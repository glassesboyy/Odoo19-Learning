from odoo import models, fields


class AssetBrand(models.Model):
    _name = 'asset.brand'
    _description = 'Asset Brand'
    _order = 'name'

    _sql_constraints = [
        ('unique_brand_name', 'UNIQUE(name)', 'Brand name must be unique.'),
    ]

    name = fields.Char(required=True)
    category = fields.Selection([
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ], required=True, default='standard',
        help="Standard: Honda, Toyota, Mitsubishi, Mazda. Premium: BMW, Mercedes.")
    model_ids = fields.One2many('asset.brand.model', 'brand_id', string='Models')
