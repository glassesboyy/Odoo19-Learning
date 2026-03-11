from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AssetRequest(models.Model):
    _name = 'asset.request'
    _description = 'Asset Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # === Header Fields ===
    name = fields.Char(
        default=lambda self: _('New'),
        readonly=True, copy=False, tracking=True,
    )
    description = fields.Text(
        string='Description',
        help='Description or purpose of this asset request.',
        tracking=True,
    )
    date = fields.Date(
        default=fields.Date.today, required=True, tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner', string='Requestor', required=True, tracking=True,
    )
    request_type = fields.Selection([
        ('replacement_car_temporary', 'Replacement Car (Temporary)'),
        ('replacement_car_new', 'Replacement Car (New)'),
    ], required=True, tracking=True)
    required_date = fields.Date(required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', required=True, copy=False, tracking=True)

    # === Additional Fields ===
    attachment = fields.Binary(string='Attachment', attachment=True)
    attachment_filename = fields.Char(string='Attachment Filename')
    notes = fields.Text(string='Notes')
    current_cycle = fields.Integer(
        string='Current Cycle', default=0, copy=False,
        help='Tracks the current approval cycle number.',
    )

    # === Relational Fields ===
    flow_id = fields.Many2one(
        'approval.flow', string='Approval Flow',
        default=lambda self: self.env['approval.flow'].search([('active', '=', True)], limit=1),
        tracking=True,
        help='The approval workflow used for this request.',
    )
    line_ids = fields.One2many('asset.request.line', 'request_id', string='Request Lines')
    approval_history_ids = fields.One2many('approval.history', 'request_id', string='Approval History')

    # === Computed Fields ===
    max_approval_level = fields.Integer(
        compute='_compute_approval_levels', store=True,
        string='Required Approval Level',
    )
    current_approval_level = fields.Integer(
        compute='_compute_current_approval_level', store=True,
        string='Current Pending Level',
    )
    is_current_approver = fields.Boolean(
        compute='_compute_is_current_approver',
    )
    can_reset_to_draft = fields.Boolean(
        compute='_compute_can_reset_to_draft',
    )

    # ------------------------------------------------------------------
    # CRUD overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        # Backend validation: only Admin can create Asset Requests
        if not self.env.su and not self.env.user.has_group('asset_request.group_asset_request_admin'):
            raise UserError(_("Only Admin users can create Asset Requests."))
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('asset.request') or _('New')
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------
    @api.depends('line_ids.brand_id', 'line_ids.model_id', 'line_ids.quantity', 'flow_id')
    def _compute_approval_levels(self):
        for rec in self:
            if not rec.flow_id or not rec.line_ids:
                rec.max_approval_level = 0
                continue
            # Aggregate quantities by (brand, model) before matching rules
            aggregated = rec._aggregate_line_quantities()
            max_seq = 0
            for (brand, model), qty in aggregated.items():
                level = rec._find_matching_level(brand, model, qty)
                if level and level.sequence > max_seq:
                    max_seq = level.sequence
            rec.max_approval_level = max_seq

    @api.depends('approval_history_ids.status', 'current_cycle')
    def _compute_current_approval_level(self):
        for rec in self:
            current_pending = rec.approval_history_ids.filtered(
                lambda a: a.cycle == rec.current_cycle and a.status == 'pending'
            )
            rec.current_approval_level = min(
                current_pending.mapped('level_sequence'), default=0
            )

    @api.depends('state', 'current_approval_level', 'approval_history_ids.status',
                 'approval_history_ids.assigned_approver_id', 'current_cycle', 'flow_id')
    def _compute_is_current_approver(self):
        for rec in self:
            if rec.state != 'waiting_approval' or not rec.current_approval_level:
                rec.is_current_approver = False
                continue
            # Find the approval level config to get all eligible approvers
            level = rec._get_level_by_sequence(rec.current_approval_level)
            if not level:
                rec.is_current_approver = False
                continue
            all_approvers = level.get_all_approvers()
            rec.is_current_approver = self.env.user in all_approvers

    @api.depends('state')
    def _compute_can_reset_to_draft(self):
        is_privileged = (
            self.env.su
            or self.env.user.has_group('asset_request.group_asset_request_admin')
            or self.env.user.has_group('base.group_system')
        )
        for rec in self:
            rec.can_reset_to_draft = rec.state == 'rejected' and is_privileged

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only draft requests can be submitted."))
            if not rec.line_ids:
                raise UserError(_("Please add at least one request line before submitting."))
            if not rec.flow_id:
                raise UserError(_("No Approval Flow is configured. Please select an Approval Flow."))

            # Recompute max level from rules
            rec._compute_approval_levels()
            if rec.max_approval_level == 0:
                raise UserError(_(
                    "Cannot determine approval level. "
                    "No matching approval rules found for the request lines. "
                    "Check Approval Flow configuration."))

            # Determine which levels are required (1..max_approval_level)
            ordered_levels = rec.flow_id.get_ordered_levels().filtered(
                lambda l: l.sequence <= rec.max_approval_level
            )
            if not ordered_levels:
                raise UserError(_("No approval levels found in the configured flow."))

            # Validate that each required level has a primary approver
            for level in ordered_levels:
                primary = level.get_primary_approver()
                if not primary:
                    raise UserError(_(
                        "Approval Level '%s' does not have a primary approver. "
                        "Please configure approvers in Configuration → Approval Flows.",
                        level.name))

            # Increment cycle — old approval records are kept as history
            new_cycle = rec.current_cycle + 1
            rec.current_cycle = new_cycle

            # Generate new approval history records for the new cycle
            HistorySudo = self.env['approval.history'].sudo()
            for level in ordered_levels:
                primary = level.get_primary_approver()
                HistorySudo.create({
                    'request_id': rec.id,
                    'cycle': new_cycle,
                    'level_sequence': level.sequence,
                    'role': level.role,
                    'assigned_approver_id': primary.id if primary else False,
                    'status': 'pending',
                })

            rec.state = 'waiting_approval'
            rec.message_post(body=_(
                "Request submitted for approval (Cycle %s). Required level: %s",
                new_cycle, rec.max_approval_level,
            ))

            # Notify approvers for the first level
            rec._notify_current_approvers()

    def action_approve(self):
        for rec in self:
            if rec.state != 'waiting_approval':
                raise UserError(_("Only requests in 'Waiting Approval' state can be approved."))

            current_level_seq = rec.current_approval_level
            if current_level_seq == 0:
                raise UserError(_("No pending approval found."))

            rec._check_can_approve(current_level_seq)

            # Get the level config for role name
            level = rec._get_level_by_sequence(current_level_seq)
            role_name = level.role if level else ''

            # Update approval history record in current cycle
            history = rec.approval_history_ids.filtered(
                lambda a: a.cycle == rec.current_cycle
                    and a.level_sequence == current_level_seq
                    and a.status == 'pending'
            )
            history.sudo().write({
                'status': 'approved',
                'actual_approver_id': self.env.user.id,
                'date': fields.Datetime.now(),
            })

            # Build message indicating delegation if applicable
            delegation_note = ""
            if history.is_delegation:
                delegation_note = _(" (delegation for %s)", history.assigned_approver_id.name)

            rec.message_post(body=_(
                "Cycle %s — Level %s approved by %s%s (%s).",
                rec.current_cycle, current_level_seq, self.env.user.name,
                delegation_note, role_name,
            ))

            # Unlink activity for this approver
            rec.activity_unlink(['mail.mail_activity_data_todo'])

            # Check if all levels done in current cycle
            remaining = rec.approval_history_ids.filtered(
                lambda a: a.cycle == rec.current_cycle and a.status == 'pending'
            )
            if not remaining:
                rec.state = 'approved'
                rec.message_post(body=_("Request fully approved (Cycle %s).", rec.current_cycle))
            else:
                # Notify next level approvers
                rec._notify_current_approvers()

    def action_reject(self):
        for rec in self:
            if rec.state != 'waiting_approval':
                raise UserError(_("Only requests in 'Waiting Approval' state can be rejected."))

            current_level_seq = rec.current_approval_level
            if current_level_seq == 0:
                raise UserError(_("No pending approval found."))

            rec._check_can_approve(current_level_seq)

            # Get the level config for role name
            level = rec._get_level_by_sequence(current_level_seq)
            role_name = level.role if level else ''

            # Update current approval as rejected
            history = rec.approval_history_ids.filtered(
                lambda a: a.cycle == rec.current_cycle
                    and a.level_sequence == current_level_seq
                    and a.status == 'pending'
            )
            history.sudo().write({
                'status': 'rejected',
                'actual_approver_id': self.env.user.id,
                'date': fields.Datetime.now(),
            })

            # Mark all remaining pending approvals in this cycle as "no_action"
            remaining_pending = rec.approval_history_ids.filtered(
                lambda a: a.cycle == rec.current_cycle and a.status == 'pending'
            )
            if remaining_pending:
                remaining_pending.sudo().write({
                    'status': 'no_action',
                    'date': fields.Datetime.now(),
                })

            # Build message indicating delegation if applicable
            delegation_note = ""
            if history.is_delegation:
                delegation_note = _(" (delegation for %s)", history.assigned_approver_id.name)

            rec.state = 'rejected'
            rec.activity_unlink(['mail.mail_activity_data_todo'])
            rec.message_post(body=_(
                "Cycle %s — Request rejected by %s%s (%s).",
                rec.current_cycle, self.env.user.name,
                delegation_note, role_name,
            ))

    def action_reset_to_draft(self):
        for rec in self:
            # Backend validation: only 'rejected' state allowed
            if rec.state != 'rejected':
                raise UserError(_("Only rejected requests can be reset to draft."))
            # Backend validation: only Admin or System can reset
            is_admin = self.env.user.has_group('asset_request.group_asset_request_admin')
            is_system = self.env.user.has_group('base.group_system')
            if not is_admin and not is_system:
                raise UserError(_("Only Admin users can reset requests to draft."))
            # Preserve approval history — do NOT unlink records
            rec.activity_unlink(['mail.mail_activity_data_todo'])
            rec.state = 'draft'
            rec.message_post(body=_(
                "Request reset to draft (was cycle %s). Ready for revision.",
                rec.current_cycle,
            ))

    # ------------------------------------------------------------------
    # Rule Matching / Level Resolution
    # ------------------------------------------------------------------
    def _aggregate_line_quantities(self):
        """Aggregate quantities by (brand_id, model_id) across all request lines.

        Returns:
            dict: {(brand recordset, model recordset): total_quantity}
        """
        self.ensure_one()
        aggregated = {}
        for line in self.line_ids:
            key = (line.brand_id, line.model_id)
            aggregated[key] = aggregated.get(key, 0) + line.quantity
        return aggregated

    def _find_matching_level(self, brand, model, quantity):
        """Find the highest-priority matching approval level for given criteria.

        Iterates all levels in the flow, checks each level's rules against the
        brand, model, and aggregated quantity. Returns the level whose matching
        rule has the highest priority (lowest number). Falls back to the level
        with a fallback rule if no specific rule matches.

        Args:
            brand: asset.brand recordset
            model: asset.brand.model recordset
            quantity: integer (aggregated total)

        Returns:
            approval.level record or empty recordset
        """
        self.ensure_one()
        if not self.flow_id:
            return self.env['approval.level']

        best_level = self.env['approval.level']
        best_priority = float('inf')
        fallback_level = self.env['approval.level']

        for level in self.flow_id.get_ordered_levels():
            for rule in level.rule_ids:
                if rule.is_fallback:
                    # Track the fallback level (use the first/lowest one found)
                    if not fallback_level:
                        fallback_level = level
                    continue
                if rule.matches(brand, model, quantity):
                    if rule.priority < best_priority:
                        best_priority = rule.priority
                        best_level = level

        return best_level or fallback_level

    def _get_level_by_sequence(self, sequence):
        """Return the approval.level record for the given sequence in this request's flow."""
        self.ensure_one()
        if not self.flow_id:
            return self.env['approval.level']
        return self.flow_id.level_ids.filtered(lambda l: l.sequence == sequence)[:1]

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------
    def _check_can_approve(self, level_sequence):
        """Validate that the current user is an eligible approver for the given level.

        Eligible = primary approver OR any delegation approver configured for this level.
        The user must also belong to the required security group.
        """
        self.ensure_one()
        history = self.approval_history_ids.filtered(
            lambda a: a.cycle == self.current_cycle
                and a.level_sequence == level_sequence
                and a.status == 'pending'
        )
        if not history:
            raise UserError(_("No pending approval found for Level %s.", level_sequence))

        level = self._get_level_by_sequence(level_sequence)
        if not level:
            raise UserError(_(
                "Approval Level %s not found in the configured flow.", level_sequence))

        all_approvers = level.get_all_approvers()
        if not all_approvers:
            raise UserError(_(
                "No approvers configured for %s. "
                "Please reset to draft and resubmit after configuring approvers.",
                level.name))

        if self.env.user not in all_approvers:
            primary = level.get_primary_approver()
            raise UserError(_(
                "You are not authorized to approve at %s (%s). "
                "Authorized approvers: %s",
                level.name, level.role,
                ', '.join(all_approvers.mapped('name'))))

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------
    def _notify_current_approvers(self):
        """Send email and schedule activity for all eligible approvers at the current level."""
        self.ensure_one()
        current_level_seq = self.current_approval_level
        if not current_level_seq:
            return

        level = self._get_level_by_sequence(current_level_seq)
        if not level:
            return

        all_approvers = level.get_all_approvers()
        if not all_approvers:
            return

        # Schedule activity for each eligible approver (primary + delegation)
        for approver in all_approvers:
            self.with_context(mail_activity_quick_update=True).activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=approver.id,
                note=_(
                    "You have a pending asset request to approve: %s (%s - %s)",
                    self.name, level.name, level.role,
                ),
            )

        # Send email via template to the primary approver
        primary = level.get_primary_approver()
        template = self.env.ref(
            'asset_request.mail_template_approval_request',
            raise_if_not_found=False,
        )
        if template and primary and primary.email:
            try:
                template.send_mail(
                    self.id, force_send=True,
                    email_values={'email_to': primary.email},
                )
            except Exception:
                _logger.warning(
                    "Failed to send approval notification email for %s to %s",
                    self.name, primary.email, exc_info=True,
                )

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------
    @api.model
    def _cron_send_approval_reminder(self):
        """Daily reminder for pending approvals."""
        pending_requests = self.search([('state', '=', 'waiting_approval')])
        for rec in pending_requests:
            current_level_seq = rec.current_approval_level
            if not current_level_seq:
                continue

            level = rec._get_level_by_sequence(current_level_seq)
            if not level:
                continue

            all_approvers = level.get_all_approvers()
            if not all_approvers:
                continue

            # Send reminder email to the primary approver
            primary = level.get_primary_approver()
            template = self.env.ref(
                'asset_request.mail_template_approval_reminder',
                raise_if_not_found=False,
            )
            if template and primary and primary.email:
                try:
                    template.send_mail(
                        rec.id, force_send=True,
                        email_values={'email_to': primary.email},
                    )
                except Exception:
                    _logger.warning(
                        "Failed to send reminder email for %s to %s",
                        rec.name, primary.email, exc_info=True,
                    )

            approver_names = ', '.join(all_approvers.mapped('name'))
            rec.message_post(body=_(
                "Reminder sent for %s approval. Eligible approvers: %s",
                level.name, approver_names,
            ))
