from odoo import models, fields

class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Real Estate Property Type'
    _order = 'sequence desc, name'
    
    _sql_constraints = [
        ('unique_type_name', 'UNIQUE(name)', 'Type name must be unique.'),
    ]

    sequence = fields.Integer(default=1)
    name = fields.Char(required=True)
    property_ids = fields.One2many('estate.property', 'property_type_id', string='Properties')
