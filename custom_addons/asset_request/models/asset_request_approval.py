from odoo import models, fields


class AssetRequestApproval(models.Model):
    _name = 'asset.request.approval'
    _description = 'Asset Request Approval'
    _order = 'level'

    request_id = fields.Many2one('asset.request', required=True, ondelete='cascade')
    level = fields.Integer(required=True)
    role = fields.Char(readonly=True)
    approver_id = fields.Many2one('res.users', string='Approver', readonly=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending', readonly=True)
    date = fields.Datetime(string='Action Date', readonly=True)
    remarks = fields.Text()
