from odoo import models, fields


class AssetBrandModel(models.Model):
    _name = 'asset.brand.model'
    _description = 'Asset Brand Model'
    _order = 'name'

    _sql_constraints = [
        ('unique_model_per_brand', 'UNIQUE(name, brand_id)',
         'Model name must be unique per brand.'),
    ]

    name = fields.Char(required=True)
    brand_id = fields.Many2one('asset.brand', required=True, ondelete='cascade')
