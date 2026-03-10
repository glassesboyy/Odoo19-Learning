from odoo import models, fields


class AssetRequestApproval(models.Model):
    _name = 'asset.request.approval'
    _description = 'Asset Request Approval'
    _order = 'cycle desc, level'

    request_id = fields.Many2one('asset.request', required=True, ondelete='cascade')
    cycle = fields.Integer(string='Cycle', required=True, default=1,
                           help='Approval cycle number. Incremented on each revision.')
    level = fields.Integer(required=True)
    role = fields.Char(readonly=True)
    approver_id = fields.Many2one('res.users', string='Approver', readonly=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('no_action', 'No Action'),
    ], default='pending', readonly=True)
    date = fields.Datetime(string='Action Date', readonly=True)