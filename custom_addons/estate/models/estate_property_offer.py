from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta

class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Real Estate Property Offer'
    _order = 'price desc'
    
    _sql_constraints = [
        ('check_offer_price_positive', 'CHECK(price > 0)', 'Offer price must be strictly positive.'),
    ]

    price = fields.Float()
    status = fields.Selection([
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),
    ], copy=False)
    partner_id = fields.Many2one('res.partner', required=True)
    property_id = fields.Many2one('estate.property', required=True)
    
    # Related Field
    property_type_id = fields.Many2one(
        'estate.property.type',
        related='property_id.property_type_id',
        string='Property Type',
        store=True
    )
    
    # Computed Field with Inverse
    validity = fields.Integer(default=7)
    date_deadline = fields.Date(
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline',
        string='Deadline'
    )
    
    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        for record in self:
            # Fallback to today if create_date is not set (at creation time)
            base_date = record.create_date.date() if record.create_date else fields.Date.today()
            record.date_deadline = base_date + timedelta(days=record.validity)
    
    def _inverse_date_deadline(self):
        for record in self:
            # Compute validity from date_deadline
            base_date = record.create_date.date() if record.create_date else fields.Date.today()
            if record.date_deadline:
                delta = record.date_deadline - base_date
                record.validity = delta.days
    
    # Action Methods
    def action_accept(self):
        for record in self:
            # Check if another offer is already accepted
            if record.property_id.offer_ids.filtered(lambda o: o.status == 'accepted' and o.id != record.id):
                raise UserError("Another offer has already been accepted for this property.")
            record.status = 'accepted'
            # Set buyer and selling price on property
            record.property_id.buyer_id = record.partner_id
            record.property_id.selling_price = record.price
    
    def action_refuse(self):
        for record in self:
            record.status = 'refused'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            property_id = vals.get('property_id')
            if property_id:
                property_obj = self.env['estate.property'].browse(property_id)
                # Raise error if the new offer is lower than an existing offer
                if property_obj.offer_ids:
                    max_existing = max(property_obj.offer_ids.mapped('price'))
                    if vals.get('price', 0) < max_existing:
                        raise UserError(
                            f"Cannot create an offer lower than the existing best offer of {max_existing}."
                        )
                # Set the property state to 'Offer Received'
                property_obj.state = 'offer_received'
        return super().create(vals_list)
