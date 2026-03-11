from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApprovalApprover(models.Model):
    _name = 'approval.approver'
    _description = 'Approval Approver'
    _order = 'level_id, role_type desc, id'

    level_id = fields.Many2one('approval.level', required=True, ondelete='cascade',
                               string='Approval Level')
    user_id = fields.Many2one('res.users', required=True, string='User')
    role_type = fields.Selection([
        ('primary', 'Primary Approver'),
        ('delegation', 'Delegation Approver'),
    ], required=True, default='delegation', string='Approver Type')

    # Related fields for display
    flow_id = fields.Many2one(related='level_id.flow_id', store=True, string='Flow')
    level_sequence = fields.Integer(related='level_id.sequence', store=True, string='Level')
    level_role = fields.Char(related='level_id.role', store=True, string='Role')
    group_id = fields.Many2one(related='level_id.group_id', string='Required Group')

    _sql_constraints = [
        ('unique_level_user', 'UNIQUE(level_id, user_id)',
         'A user can only be assigned once per approval level.'),
    ]

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('role_type', 'level_id')
    def _check_single_primary(self):
        """Ensure only one primary approver per level."""
        for rec in self:
            if rec.role_type == 'primary':
                others = self.search([
                    ('level_id', '=', rec.level_id.id),
                    ('role_type', '=', 'primary'),
                    ('id', '!=', rec.id),
                ])
                if others:
                    raise ValidationError(_(
                        "Level '%s' already has a primary approver (%s). "
                        "Each level can only have one primary approver.",
                        rec.level_id.name, others[0].user_id.name))

    @api.constrains('user_id', 'level_id')
    def _check_user_in_group(self):
        """Validate that the user belongs to the required security group for this level."""
        for rec in self:
            if not rec.level_id.group_id or not rec.user_id:
                continue
            if rec.level_id.group_id not in rec.user_id.group_ids:
                raise ValidationError(_(
                    "User '%s' does not belong to the required security group '%s' "
                    "for %s. Please assign the user to the correct group first.",
                    rec.user_id.name, rec.level_id.group_id.full_name,
                    rec.level_id.name))
