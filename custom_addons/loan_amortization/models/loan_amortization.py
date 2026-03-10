from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class LoanAmortization(models.Model):
    _name = 'loan.amortization'
    _description = 'Loan Amortization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    _sql_constraints = [
        ('check_principal_positive', 'CHECK(principal > 0)',
         'Principal amount must be greater than zero.'),
        ('check_term_years_positive', 'CHECK(term_years > 0)',
         'Term in years must be greater than zero.'),
        ('check_annual_rate_positive', 'CHECK(annual_rate_display > 0)',
         'Annual rate must be greater than zero.'),
    ]

    # === Identity & Status ===
    name = fields.Char(
        string='Reference',
        default=lambda self: _('New'),
        readonly=True,
        copy=False,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Internal Company',
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
    )

    # === Loan Parameters (User Input) ===
    partner_id = fields.Many2one(
        'res.partner',
        string='Company',
        required=True,
        tracking=True,
    )
    principal = fields.Monetary(
        string='Principal ($)',
        required=True,
        tracking=True,
        currency_field='currency_id',
        help='The total loan amount.',
    )
    term_years = fields.Integer(
        string='Term (Years)',
        required=True,
        tracking=True,
        help='Loan term in years.',
    )
    annual_rate_display = fields.Float(
        string='Annual Rate (%)',
        required=True,
        digits=(16, 4),
        tracking=True,
        help='Annual interest rate in percentage (e.g. 7 for 7%).',
    )
    annual_rate = fields.Float(
        string='Annual Rate (Decimal)',
        compute='_compute_annual_rate',
        store=True,
        digits=(16, 12),
        help='Annual interest rate as decimal (e.g. 0.07 for 7%).',
    )
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )

    # === Computed Loan Metrics ===
    number_of_months = fields.Integer(
        string='Number of Months (n)',
        compute='_compute_number_of_months',
        store=True,
    )
    monthly_rate = fields.Float(
        string='Monthly Rate (i)',
        compute='_compute_monthly_rate',
        store=True,
        digits=(16, 12),
    )
    monthly_payment = fields.Monetary(
        string='Monthly Payment ($)',
        compute='_compute_monthly_payment',
        store=True,
        currency_field='currency_id',
    )
    total_payment = fields.Monetary(
        string='Total Payment ($)',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )
    total_interest = fields.Monetary(
        string='Total Interest ($)',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )

    # === Schedule Lines ===
    line_ids = fields.One2many(
        'loan.amortization.line',
        'loan_id',
        string='Amortization Schedule',
        copy=False,
    )
    line_count = fields.Integer(
        string='Schedule Lines',
        compute='_compute_line_count',
    )

    # === Accounting Configuration ===
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        help='Miscellaneous journal used for lease payment entries.',
        tracking=True,
    )
    leasing_payable_account_id = fields.Many2one(
        'account.account',
        string='Leasing Payable Account',
        domain="[('company_ids', 'in', company_id)]",
        help='Debit account for the principal (leasing payable) portion.',
        tracking=True,
    )
    interest_expense_account_id = fields.Many2one(
        'account.account',
        string='Interest Expense Account',
        domain="[('company_ids', 'in', company_id)]",
        help='Debit account for the interest expense portion.',
        tracking=True,
    )
    accounts_payable_account_id = fields.Many2one(
        'account.account',
        string='Accounts Payable for Lease',
        domain="[('company_ids', 'in', company_id)]",
        help='Credit account for the total lease payment (accounts payable).',
        tracking=True,
    )
    move_count = fields.Integer(
        string='Journal Entries',
        compute='_compute_move_count',
    )

    # === Compute Methods ===

    @api.depends('annual_rate_display')
    def _compute_annual_rate(self):
        for loan in self:
            loan.annual_rate = (loan.annual_rate_display or 0.0) / 100.0

    @api.depends('term_years')
    def _compute_number_of_months(self):
        for loan in self:
            loan.number_of_months = (loan.term_years or 0) * 12

    @api.depends('annual_rate')
    def _compute_monthly_rate(self):
        for loan in self:
            loan.monthly_rate = (loan.annual_rate or 0.0) / 12.0

    @api.depends('principal', 'monthly_rate', 'number_of_months')
    def _compute_monthly_payment(self):
        """
        PMT Formula:
            Monthly Payment = P * ((i * (1 + i)^n) / ((1 + i)^n - 1))

        Where:
            P = Principal
            i = Monthly interest rate
            n = Number of months
            Z = (1 + i)^n
            A = i * Z
            B = Z - 1
            C = A / B
            D = C * P  (Monthly Payment)
        """
        for loan in self:
            P = loan.principal or 0.0
            i = loan.monthly_rate or 0.0
            n = loan.number_of_months or 0

            if P <= 0 or n <= 0:
                loan.monthly_payment = 0.0
                continue

            if i == 0:
                # Zero interest: simple division
                loan.monthly_payment = round(P / n, 2)
                continue

            Z = (1 + i) ** n        # (1 + i)^n
            A = i * Z               # i * Z
            B = Z - 1               # Z - 1
            C = A / B               # A / B
            D = C * P               # Monthly Payment

            loan.monthly_payment = round(D, 2)

    @api.depends('monthly_payment', 'number_of_months', 'principal')
    def _compute_totals(self):
        for loan in self:
            loan.total_payment = round(
                (loan.monthly_payment or 0.0) * (loan.number_of_months or 0), 2
            )
            loan.total_interest = round(
                loan.total_payment - (loan.principal or 0.0), 2
            )

    @api.depends('line_ids')
    def _compute_line_count(self):
        for loan in self:
            loan.line_count = len(loan.line_ids)

    @api.depends('line_ids.move_id')
    def _compute_move_count(self):
        for loan in self:
            loan.move_count = len(loan.line_ids.mapped('move_id'))

    # === Constraints ===

    @api.constrains('principal')
    def _check_principal(self):
        for loan in self:
            if loan.principal <= 0:
                raise ValidationError(_('Principal amount must be greater than zero.'))

    @api.constrains('term_years')
    def _check_term_years(self):
        for loan in self:
            if loan.term_years <= 0:
                raise ValidationError(_('Term in years must be greater than zero.'))

    @api.constrains('annual_rate_display')
    def _check_annual_rate(self):
        for loan in self:
            if loan.annual_rate_display <= 0:
                raise ValidationError(_('Annual rate must be greater than zero.'))

    # === CRUD ===

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'loan.amortization'
                ) or _('New')
        return super().create(vals_list)

    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = _('New')
        return super().copy(default)

    # === Action Methods ===

    def action_generate_schedule(self):
        """Generate the amortization schedule lines based on loan parameters."""
        for loan in self:
            if loan.state != 'draft':
                raise UserError(_(
                    'You can only generate the schedule for loans in Draft state.'
                ))

            P = loan.principal
            i = loan.monthly_rate
            n = loan.number_of_months

            if P <= 0 or n <= 0:
                raise UserError(_(
                    'Please fill in valid Principal and Term before generating.'
                ))

            # Clear existing schedule lines
            loan.line_ids.unlink()

            # Calculate monthly payment using PMT formula
            if i == 0:
                monthly = round(P / n, 2)
            else:
                Z = (1 + i) ** n
                A = i * Z
                B = Z - 1
                C = A / B
                monthly = round(C * P, 2)

            remaining = P
            lines_vals = []

            for month in range(1, n + 1):
                date = loan.start_date + relativedelta(months=month - 1)
                interest = round(remaining * i, 2)

                if month == n:
                    # Last month: adjust so remaining balance is exactly 0
                    principal_pay = round(remaining, 2)
                    payment = round(principal_pay + interest, 2)
                else:
                    payment = monthly
                    principal_pay = round(payment - interest, 2)

                remaining = round(remaining - principal_pay, 2)

                lines_vals.append({
                    'loan_id': loan.id,
                    'sequence': month,
                    'date': date,
                    'payment': payment,
                    'interest_rate': i,
                    'interest_amount': interest,
                    'net_deduction': principal_pay,
                    'remaining_balance': max(remaining, 0.0),
                })

            self.env['loan.amortization.line'].create(lines_vals)

            loan.message_post(
                body=_('Amortization schedule generated: %d payment lines.', n),
            )

    def action_confirm(self):
        """Confirm the loan — locks parameters and schedule."""
        for loan in self:
            if loan.state != 'draft':
                raise UserError(_('Only draft loans can be confirmed.'))
            if not loan.line_ids:
                raise UserError(_(
                    'Please generate the amortization schedule before confirming.'
                ))

            loan.write({'state': 'confirmed'})
            loan.message_post(body=_('Loan confirmed.'))

    def action_done(self):
        """Mark the loan as done."""
        for loan in self:
            if loan.state != 'confirmed':
                raise UserError(_('Only confirmed loans can be marked as done.'))

            loan.write({'state': 'done'})
            loan.message_post(body=_('Loan marked as done.'))

    def action_reset_to_draft(self):
        """Reset loan back to draft state — clears the schedule."""
        for loan in self:
            if loan.state not in ('confirmed', 'done'):
                raise UserError(_('Only confirmed or done loans can be reset.'))

            # Cancel and unlink related journal entries that are still in draft
            moves = loan.line_ids.mapped('move_id')
            draft_moves = moves.filtered(lambda m: m.state == 'draft')
            posted_moves = moves.filtered(lambda m: m.state == 'posted')

            if posted_moves:
                raise UserError(_(
                    'Cannot reset to draft: %d journal entries have already been posted. '
                    'Please cancel or reverse them first.',
                    len(posted_moves),
                ))

            if draft_moves:
                # Unlink the move reference from lines first
                loan.line_ids.filtered(
                    lambda l: l.move_id in draft_moves
                ).write({'move_id': False})
                draft_moves.unlink()

            loan.line_ids.unlink()
            loan.write({'state': 'draft'})
            loan.message_post(body=_('Loan reset to draft. Schedule cleared.'))

    # === Journal Entry Methods ===

    def action_create_journal_entries(self):
        """Create journal entries for all schedule lines that don't have one yet."""
        for loan in self:
            if loan.state not in ('confirmed', 'done'):
                raise UserError(_(
                    'Journal entries can only be created for confirmed or done loans.'
                ))
            if not loan.line_ids:
                raise UserError(_('No amortization schedule lines found.'))

            # Validate accounting configuration
            if not loan.journal_id:
                raise UserError(_(
                    'Please configure the Journal in the Accounting tab before '
                    'generating journal entries.'
                ))
            if not loan.leasing_payable_account_id:
                raise UserError(_(
                    'Please configure the Leasing Payable Account in the Accounting tab.'
                ))
            if not loan.interest_expense_account_id:
                raise UserError(_(
                    'Please configure the Interest Expense Account in the Accounting tab.'
                ))
            if not loan.accounts_payable_account_id:
                raise UserError(_(
                    'Please configure the Accounts Payable for Lease in the Accounting tab.'
                ))

            # Filter lines that don't have a journal entry yet
            lines_to_process = loan.line_ids.filtered(lambda l: not l.move_id)
            if not lines_to_process:
                raise UserError(_(
                    'All schedule lines already have journal entries.'
                ))

            created_moves = self.env['account.move']
            for line in lines_to_process:
                move_vals = loan._prepare_move_values(line)
                move = self.env['account.move'].create(move_vals)
                line.write({'move_id': move.id})
                created_moves |= move

            loan.message_post(
                body=_(
                    'Created %d journal entries for amortization schedule.',
                    len(created_moves),
                ),
            )

        return True

    def _prepare_move_values(self, line):
        """Prepare the values for creating a journal entry from a schedule line.

        Journal entry structure:
            - Debit: Leasing Payable (principal / net_deduction)
            - Debit: Interest Expense (interest_amount)
            - Credit: Accounts Payable for Lease (payment = principal + interest)
        """
        self.ensure_one()
        return {
            'move_type': 'entry',
            'journal_id': self.journal_id.id,
            'date': line.date,
            'ref': _('%(loan)s - Payment %(month)d/%(total)d',
                     loan=self.name, month=line.sequence, total=self.number_of_months),
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'line_ids': [
                # Debit: Leasing Payable (principal portion)
                Command.create({
                    'name': _('Leasing Payable - %(loan)s Month %(month)d',
                             loan=self.name, month=line.sequence),
                    'account_id': self.leasing_payable_account_id.id,
                    'partner_id': self.partner_id.id,
                    'debit': line.net_deduction,
                    'credit': 0.0,
                    'currency_id': self.currency_id.id,
                }),
                # Debit: Interest Expense
                Command.create({
                    'name': _('Interest Expense - %(loan)s Month %(month)d',
                             loan=self.name, month=line.sequence),
                    'account_id': self.interest_expense_account_id.id,
                    'partner_id': self.partner_id.id,
                    'debit': line.interest_amount,
                    'credit': 0.0,
                    'currency_id': self.currency_id.id,
                }),
                # Credit: Accounts Payable for Lease
                Command.create({
                    'name': _('Accounts Payable - %(loan)s Month %(month)d',
                             loan=self.name, month=line.sequence),
                    'account_id': self.accounts_payable_account_id.id,
                    'partner_id': self.partner_id.id,
                    'debit': 0.0,
                    'credit': line.payment,
                    'currency_id': self.currency_id.id,
                }),
            ],
        }

    def action_post_journal_entries(self):
        """Post all draft journal entries linked to this loan's schedule."""
        for loan in self:
            if loan.state not in ('confirmed', 'done'):
                raise UserError(_(
                    'Journal entries can only be posted for confirmed or done loans.'
                ))

            draft_moves = loan.line_ids.mapped('move_id').filtered(
                lambda m: m.state == 'draft'
            )
            if not draft_moves:
                raise UserError(_('No draft journal entries to post.'))

            draft_moves.action_post()
            loan.message_post(
                body=_('Posted %d journal entries.', len(draft_moves)),
            )

    def action_view_journal_entries(self):
        """Open the list of journal entries linked to this loan."""
        self.ensure_one()
        moves = self.line_ids.mapped('move_id')
        action = {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', moves.ids)],
            'context': {'default_move_type': 'entry'},
        }
        if len(moves) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': moves.id,
            })
        return action
