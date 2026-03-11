from odoo import models, fields, api


class ApprovalHistory(models.Model):
    _name = 'approval.history'
    _description = 'Approval History'
    _order = 'cycle desc, level_sequence'

    request_id = fields.Many2one('asset.request', required=True, ondelete='cascade',
                                 string='Asset Request')
    cycle = fields.Integer(string='Cycle', required=True, default=1,
                           help='Approval cycle number. Incremented on each revision.')
    level_sequence = fields.Integer(string='Level', required=True,
                                    help='Approval level sequence number.')
    role = fields.Char(string='Role', readonly=True)
    assigned_approver_id = fields.Many2one('res.users', string='Assigned Approver',
                                           readonly=True,
                                           help='The primary approver assigned from configuration.')
    actual_approver_id = fields.Many2one('res.users', string='Actual Approver',
                                         readonly=True,
                                         help='The user who actually performed the approval action.')
    is_delegation = fields.Boolean(compute='_compute_is_delegation', store=True,
                                   string='Delegated',
                                   help='True if the action was performed by a delegation approver.')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('no_action', 'No Action'),
    ], default='pending', readonly=True)
    date = fields.Datetime(string='Action Date', readonly=True)
    note = fields.Text(string='Note')

    @api.depends('assigned_approver_id', 'actual_approver_id')
    def _compute_is_delegation(self):
        for rec in self:
            rec.is_delegation = bool(
                rec.actual_approver_id
                and rec.assigned_approver_id
                and rec.actual_approver_id != rec.assigned_approver_id
            )
