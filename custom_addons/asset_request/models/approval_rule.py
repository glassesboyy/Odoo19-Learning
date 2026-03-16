from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApprovalRule(models.Model):
    _name = 'approval.rule'
    _description = 'Approval Rule'
    _order = 'level_id, priority, id'

    level_id = fields.Many2one('approval.level', required=True, ondelete='cascade',
                               string='Approval Level')
    name = fields.Char(compute='_compute_name', store=True, string='Rule Name')
    brand_id = fields.Many2one('asset.brand', string='Brand',
                               help='Leave empty for wildcard (any brand).')
    model_id = fields.Many2one('asset.brand.model', string='Model',
                               domain="[('brand_id', '=', brand_id)]",
                               help='Leave empty for wildcard (any model).')
    brand_display = fields.Char(compute='_compute_brand_display', string='Brand')
    model_display = fields.Char(compute='_compute_model_display', string='Model')
    quantity_max_display = fields.Char(compute='_compute_quantity_max_display', string='Qty Max')
    quantity_min = fields.Integer(string='Qty Min', default=0,
                                 help='Minimum quantity (inclusive). 0 = no lower bound.')
    quantity_max = fields.Integer(string='Qty Max', default=0,
                                 help='Maximum quantity (inclusive). 0 = unlimited.')
    priority = fields.Integer(string='Priority', compute='_compute_priority',
                              store=True, readonly=False,
                              help='Lower number = higher priority. Auto-computed based on specificity.')
    is_fallback = fields.Boolean(compute='_compute_is_fallback', store=True,
                                 string='Is Fallback Rule')

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------
    @api.depends('brand_id', 'model_id', 'quantity_min', 'quantity_max')
    def _compute_name(self):
        for rec in self:
            brand = rec.brand_id.name or 'Any Brand'
            model = rec.model_id.name or 'Any Model'
            if rec.quantity_max == 0:
                qty_str = f"{rec.quantity_min}+" if rec.quantity_min else 'Any Qty'
            else:
                qty_str = f"{rec.quantity_min}-{rec.quantity_max}"
            rec.name = f"{brand} / {model} / Qty {qty_str}"

    @api.depends('brand_id')
    def _compute_brand_display(self):
        for rec in self:
            rec.brand_display = rec.brand_id.name or 'Any Brand'

    @api.depends('model_id')
    def _compute_model_display(self):
        for rec in self:
            rec.model_display = rec.model_id.name or 'Any Model'

    @api.depends('quantity_max')
    def _compute_quantity_max_display(self):
        for rec in self:
            rec.quantity_max_display = '∞' if rec.quantity_max == 0 else str(rec.quantity_max)

    @api.depends('brand_id', 'model_id', 'quantity_min', 'quantity_max')
    def _compute_priority(self):
        for rec in self:
            score = 100
            if rec.brand_id:
                score -= 40
            if rec.model_id:
                score -= 30
            if rec.quantity_min > 0 or rec.quantity_max > 0:
                score -= 20
            rec.priority = max(score, 1)

    @api.depends('brand_id', 'model_id', 'quantity_min', 'quantity_max')
    def _compute_is_fallback(self):
        for rec in self:
            rec.is_fallback = (
                not rec.brand_id
                and not rec.model_id
                and rec.quantity_min == 0
                and rec.quantity_max == 0
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('quantity_min', 'quantity_max')
    def _check_quantity_range(self):
        for rec in self:
            if rec.quantity_min < 0:
                raise ValidationError(_("Quantity Min cannot be negative."))
            if rec.quantity_max < 0:
                raise ValidationError(_("Quantity Max cannot be negative."))
            if rec.quantity_max > 0 and rec.quantity_min > rec.quantity_max:
                raise ValidationError(_(
                    "Quantity Min (%s) cannot be greater than Quantity Max (%s).",
                    rec.quantity_min, rec.quantity_max))

    @api.constrains('brand_id', 'model_id', 'quantity_min', 'quantity_max', 'level_id')
    def _check_no_overlap(self):
        """Ensure no overlapping quantity ranges for the same brand+model within the same level.
        Fallback rules (all wildcards) are excluded from overlap checks."""
        for rec in self:
            # Skip overlap check for fallback rules
            if rec.is_fallback:
                continue
            domain = [
                ('id', '!=', rec.id),
                ('level_id', '=', rec.level_id.id),
                ('brand_id', '=', rec.brand_id.id if rec.brand_id else False),
                ('model_id', '=', rec.model_id.id if rec.model_id else False),
            ]
            siblings = self.search(domain)
            for sibling in siblings:
                # Also skip if sibling is a fallback rule
                if sibling.is_fallback:
                    continue
                if rec._ranges_overlap(rec.quantity_min, rec.quantity_max,
                                       sibling.quantity_min, sibling.quantity_max):
                    raise ValidationError(_(
                        "Quantity range overlap detected between rule '%s' and '%s' "
                        "at %s for the same brand/model combination.",
                        rec.name, sibling.name, rec.level_id.name))

    @staticmethod
    def _ranges_overlap(min1, max1, min2, max2):
        """Check if two quantity ranges overlap. max=0 means unlimited."""
        eff_max1 = max1 if max1 > 0 else float('inf')
        eff_max2 = max2 if max2 > 0 else float('inf')
        eff_min1 = min1 if min1 > 0 else 0
        eff_min2 = min2 if min2 > 0 else 0
        return eff_min1 <= eff_max2 and eff_min2 <= eff_max1

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange('brand_id')
    def _onchange_brand_id(self):
        self.model_id = False

    # ------------------------------------------------------------------
    # Business Logic
    # ------------------------------------------------------------------
    def matches(self, brand, model, quantity):
        """Check if this rule matches the given asset criteria.

        Args:
            brand: asset.brand recordset (or False)
            model: asset.brand.model recordset (or False)
            quantity: integer

        Returns:
            bool: True if matches
        """
        self.ensure_one()
        # Brand check: wildcard (no brand_id) matches anything
        if self.brand_id and self.brand_id != brand:
            return False
        # Model check: wildcard (no model_id) matches anything
        if self.model_id and self.model_id != model:
            return False
        # Quantity check
        if self.quantity_min > 0 and quantity < self.quantity_min:
            return False
        if self.quantity_max > 0 and quantity > self.quantity_max:
            return False
        return True
