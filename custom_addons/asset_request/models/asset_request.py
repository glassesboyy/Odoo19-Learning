from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


APPROVAL_LEVEL_MAP = {
    1: {'role': 'Manager', 'group': 'asset_request.group_approver_l1'},
    2: {'role': 'Sr. Manager', 'group': 'asset_request.group_approver_l2'},
    3: {'role': 'Director', 'group': 'asset_request.group_approver_l3'},
}


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
    line_ids = fields.One2many('asset.request.line', 'request_id', string='Request Lines')
    approval_ids = fields.One2many('asset.request.approval', 'request_id', string='Approvals')

    # === Computed Fields ===
    max_approval_level = fields.Integer(
        compute='_compute_approval_levels', store=True,
    )
    current_approval_level = fields.Integer(
        compute='_compute_current_approval_level', store=True,
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
    @api.depends('line_ids.brand_id', 'line_ids.brand_id.category', 'line_ids.quantity')
    def _compute_approval_levels(self):
        for rec in self:
            max_level = 0
            for line in rec.line_ids:
                level = self._get_line_approval_level(line)
                if level > max_level:
                    max_level = level
            rec.max_approval_level = max_level

    @api.depends('approval_ids.status', 'current_cycle')
    def _compute_current_approval_level(self):
        for rec in self:
            current_approvals = rec.approval_ids.filtered(
                lambda a: a.cycle == rec.current_cycle and a.status == 'pending'
            )
            rec.current_approval_level = min(current_approvals.mapped('level'), default=0)

    @api.depends('state', 'current_approval_level', 'approval_ids.approver_id', 'approval_ids.status', 'current_cycle')
    def _compute_is_current_approver(self):
        for rec in self:
            if rec.state != 'waiting_approval' or not rec.current_approval_level:
                rec.is_current_approver = False
                continue
            approval = rec.approval_ids.filtered(
                lambda a: a.cycle == rec.current_cycle
                    and a.level == rec.current_approval_level
                    and a.status == 'pending'
            )
            rec.is_current_approver = bool(approval and approval.approver_id == self.env.user)

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

            # Recompute max level
            rec._compute_approval_levels()
            if rec.max_approval_level == 0:
                raise UserError(_("Cannot determine approval level. Check request lines."))

            # Validate that approval configuration exists for all required levels
            for level in range(1, rec.max_approval_level + 1):
                config = self.env['asset.approval.config'].search(
                    [('level', '=', str(level))], limit=1,
                )
                if not config or not config.approver_id:
                    raise UserError(_(
                        "Approval Configuration for Level %s is not set up. "
                        "Please configure approvers in Configuration → Approval Configuration.",
                        level,
                    ))

            # Increment cycle — old approval records are kept as history
            new_cycle = rec.current_cycle + 1
            rec.current_cycle = new_cycle

            # Generate new approval records for the new cycle (sudo: system operation)
            ApprovalSudo = self.env['asset.request.approval'].sudo()
            for level in range(1, rec.max_approval_level + 1):
                info = APPROVAL_LEVEL_MAP[level]
                config = self.env['asset.approval.config'].search(
                    [('level', '=', str(level))], limit=1,
                )
                ApprovalSudo.create({
                    'request_id': rec.id,
                    'cycle': new_cycle,
                    'level': level,
                    'role': info['role'],
                    'approver_id': config.approver_id.id if config.approver_id else False,
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

            current_level = rec.current_approval_level
            if current_level == 0:
                raise UserError(_("No pending approval found."))

            rec._check_can_approve(current_level)

            # Update approval record in current cycle (sudo: system operation)
            approval = rec.approval_ids.filtered(
                lambda a: a.cycle == rec.current_cycle
                    and a.level == current_level
                    and a.status == 'pending'
            )
            approval.sudo().write({
                'status': 'approved',
                'approver_id': self.env.user.id,
                'date': fields.Datetime.now(),
            })
            rec.message_post(body=_(
                "Cycle %s — Level %s approved by %s (%s).",
                rec.current_cycle, current_level, self.env.user.name,
                APPROVAL_LEVEL_MAP[current_level]['role'],
            ))

            # Unlink activity for this approver
            rec.activity_unlink(['mail.mail_activity_data_todo'])

            # Check if all levels done in current cycle
            remaining = rec.approval_ids.filtered(
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

            current_level = rec.current_approval_level
            if current_level == 0:
                raise UserError(_("No pending approval found."))

            rec._check_can_approve(current_level)

            # Update current approval as rejected (sudo: system operation)
            approval = rec.approval_ids.filtered(
                lambda a: a.cycle == rec.current_cycle
                    and a.level == current_level
                    and a.status == 'pending'
            )
            approval.sudo().write({
                'status': 'rejected',
                'approver_id': self.env.user.id,
                'date': fields.Datetime.now(),
            })

            # Mark all remaining pending approvals in this cycle as "no_action"
            remaining_pending = rec.approval_ids.filtered(
                lambda a: a.cycle == rec.current_cycle and a.status == 'pending'
            )
            if remaining_pending:
                remaining_pending.sudo().write({
                    'status': 'no_action',
                    'date': fields.Datetime.now(),
                })

            rec.state = 'rejected'
            rec.activity_unlink(['mail.mail_activity_data_todo'])
            rec.message_post(body=_(
                "Cycle %s — Request rejected by %s (%s).",
                rec.current_cycle, self.env.user.name,
                APPROVAL_LEVEL_MAP[current_level]['role'],
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
            # Preserve approval history — do NOT unlink approval_ids
            rec.activity_unlink(['mail.mail_activity_data_todo'])
            rec.state = 'draft'
            rec.message_post(body=_(
                "Request reset to draft (was cycle %s). Ready for revision.",
                rec.current_cycle,
            ))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_line_approval_level(line):
        """Determine approval level for a single line based on brand category + quantity."""
        category = line.brand_id.category
        qty = line.quantity
        if category == 'standard' and qty <= 2:
            return 1  # Manager
        if category == 'premium' and qty <= 2:
            return 2  # Sr. Manager
        # quantity > 2 (any brand)
        return 3  # Director

    def _get_configured_approvers(self, level):
        """Return the configured approver for the given level from Approval Configuration."""
        config = self.env['asset.approval.config'].search(
            [('level', '=', str(level))], limit=1,
        )
        if config and config.approver_id:
            return config.approver_id
        return self.env['res.users']

    def _check_can_approve(self, level):
        """Validate that the current user matches the approver stored in the approval record.
        Config changes only affect new submissions — existing pending approvals
        retain the approver that was assigned at submit time.
        """
        self.ensure_one()
        approval = self.approval_ids.filtered(
            lambda a: a.cycle == self.current_cycle
                and a.level == level
                and a.status == 'pending'
        )
        if not approval:
            raise UserError(_("No pending approval found for Level %s.", level))
        stored_approver = approval.approver_id
        if not stored_approver:
            raise UserError(_(
                "No approver assigned for Level %s on this request. "
                "Please reset to draft and resubmit.",
                level,
            ))
        if self.env.user != stored_approver:
            info = APPROVAL_LEVEL_MAP.get(level, {})
            raise UserError(_(
                "You are not authorized to approve at Level %s (%s). "
                "Only %s can approve this request.",
                level, info.get('role', ''), stored_approver.name,
            ))

    def _notify_current_approvers(self):
        """Send email and schedule activity for the approver stored in the approval record."""
        self.ensure_one()
        current_level = self.current_approval_level
        if not current_level:
            return

        approval = self.approval_ids.filtered(
            lambda a: a.cycle == self.current_cycle
                and a.level == current_level
                and a.status == 'pending'
        )
        approver = approval.approver_id
        if not approver:
            return

        # Schedule activity for the assigned approver.
        # Use mail_activity_quick_update=True to suppress the automatic inbox/email
        # notification that activity_schedule() would otherwise trigger — we send
        # our own richer email via the template below, so we don't want duplicates.
        self.with_context(mail_activity_quick_update=True).activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=approver.id,
            note=_(
                "You have a pending asset request to approve: %s (Level %s - %s)",
                self.name, current_level, APPROVAL_LEVEL_MAP[current_level]['role'],
            ),
        )

        # Send email via template (force_send for external SMTP delivery)
        template = self.env.ref(
            'asset_request.mail_template_approval_request',
            raise_if_not_found=False,
        )
        if template and approver.email:
            try:
                template.send_mail(
                    self.id, force_send=True,
                    email_values={'email_to': approver.email},
                )
            except Exception:
                _logger.warning(
                    "Failed to send approval notification email for %s to %s",
                    self.name, approver.email, exc_info=True,
                )

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------
    @api.model
    def _cron_send_approval_reminder(self):
        """Daily reminder for pending approvals."""
        pending_requests = self.search([('state', '=', 'waiting_approval')])
        for rec in pending_requests:
            current_level = rec.current_approval_level
            if not current_level:
                continue

            approval = rec.approval_ids.filtered(
                lambda a: a.cycle == rec.current_cycle
                    and a.level == current_level
                    and a.status == 'pending'
            )
            approver = approval.approver_id
            if not approver:
                continue

            # Send reminder email (force_send for external SMTP delivery)
            template = self.env.ref(
                'asset_request.mail_template_approval_reminder',
                raise_if_not_found=False,
            )
            if template and approver.email:
                try:
                    template.send_mail(
                        rec.id, force_send=True,
                        email_values={'email_to': approver.email},
                    )
                except Exception:
                    _logger.warning(
                        "Failed to send reminder email for %s to %s",
                        rec.name, approver.email, exc_info=True,
                    )

            rec.message_post(body=_(
                "Reminder sent to %s for level %s approval.",
                approver.name, current_level,
            ))
