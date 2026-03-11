from odoo import models, fields, api


class ApprovalLevel(models.Model):
    _name = 'approval.level'
    _description = 'Approval Level'
    _order = 'flow_id, sequence'

    flow_id = fields.Many2one('approval.flow', required=True, ondelete='cascade',
                              string='Approval Flow')
    name = fields.Char(compute='_compute_name', store=True, readonly=False,
                       string='Level Name')
    sequence = fields.Integer(required=True, default=10,
                              help='Order of this level in the approval flow.')
    role = fields.Char(required=True, string='Role',
                       help='Role name, e.g. Manager, Sr. Manager, Director')
    group_id = fields.Many2one('res.groups', required=True, string='Security Group',
                               help='Users in this group are eligible for this level.')
    rule_ids = fields.One2many('approval.rule', 'level_id', string='Approval Rules')
    approver_ids = fields.One2many('approval.approver', 'level_id', string='Approvers')

    _sql_constraints = [
        ('unique_flow_sequence', 'UNIQUE(flow_id, sequence)',
         'Each level sequence must be unique within a flow.'),
    ]

    @api.depends('sequence', 'role')
    def _compute_name(self):
        for rec in self:
            if rec.sequence and rec.role:
                rec.name = f"Level {rec.sequence} - {rec.role}"
            elif rec.sequence:
                rec.name = f"Level {rec.sequence}"
            else:
                rec.name = rec.role or ''

    def get_primary_approver(self):
        """Return the primary approver user for this level."""
        self.ensure_one()
        primary = self.approver_ids.filtered(lambda a: a.role_type == 'primary')
        return primary[:1].user_id if primary else self.env['res.users']

    def get_all_approvers(self):
        """Return all eligible approver users (primary + delegation) for this level."""
        self.ensure_one()
        return self.approver_ids.mapped('user_id')

    def get_delegation_approvers(self):
        """Return delegation approver users for this level."""
        self.ensure_one()
        delegation = self.approver_ids.filtered(lambda a: a.role_type == 'delegation')
        return delegation.mapped('user_id')
