from odoo import models, fields, api


class AssetRequestLine(models.Model):
    _name = 'asset.request.line'
    _description = 'Asset Request Line'

    _sql_constraints = [
        ('check_quantity_positive', 'CHECK(quantity > 0)',
         'Quantity must be strictly positive.'),
    ]

    request_id = fields.Many2one('asset.request', required=True, ondelete='cascade')
    brand_id = fields.Many2one('asset.brand', required=True)
    model_id = fields.Many2one(
        'asset.brand.model', required=True,
        domain="[('brand_id', '=', brand_id)]",
    )
    quantity = fields.Integer(required=True, default=1)

    @api.onchange('brand_id')
    def _onchange_brand_id(self):
        self.model_id = False
