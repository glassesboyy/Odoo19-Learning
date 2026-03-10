from odoo import fields, models


class LoanAmortizationLine(models.Model):
    _name = 'loan.amortization.line'
    _description = 'Loan Amortization Schedule Line'
    _order = 'sequence, id'

    loan_id = fields.Many2one(
        'loan.amortization',
        string='Loan',
        required=True,
        ondelete='cascade',
        index=True,
    )
    currency_id = fields.Many2one(
        related='loan_id.currency_id',
        string='Currency',
        store=True,
    )
    sequence = fields.Integer(
        string='Month',
        required=True,
    )
    date = fields.Date(
        string='Date',
    )
    payment = fields.Monetary(
        string='Payment',
        currency_field='currency_id',
        digits=(16, 2),
    )
    interest_rate = fields.Float(
        string='Interest Rate',
        digits=(16, 12),
    )
    interest_amount = fields.Monetary(
        string='Interest Amount',
        currency_field='currency_id',
        digits=(16, 2),
    )
    net_deduction = fields.Monetary(
        string='Net Deduction',
        currency_field='currency_id',
        digits=(16, 2),
        help='Principal payment portion.',
    )
    remaining_balance = fields.Monetary(
        string='Remaining Balance',
        currency_field='currency_id',
        digits=(16, 2),
    )

    # === Journal Entry Link ===
    move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True,
        copy=False,
        ondelete='set null',
        help='The journal entry created for this payment period.',
    )
    move_state = fields.Selection(
        related='move_id.state',
        string='Entry Status',
        store=True,
    )
