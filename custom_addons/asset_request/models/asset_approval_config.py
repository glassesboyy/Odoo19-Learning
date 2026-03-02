from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

LEVEL_GROUP_MAP = {
    '1': 'asset_request.group_approver_l1',
    '2': 'asset_request.group_approver_l2',
    '3': 'asset_request.group_approver_l3',
}

LEVEL_ROLE_MAP = {
    '1': 'Manager',
    '2': 'Sr. Manager',
    '3': 'Director',
}


class AssetApprovalConfig(models.Model):
    _name = 'asset.approval.config'
    _description = 'Approval Configuration'
    _order = 'level'

    name = fields.Char(compute='_compute_name', store=True)
    level = fields.Selection([
        ('1', 'Level 1 - Manager'),
        ('2', 'Level 2 - Sr. Manager'),
        ('3', 'Level 3 - Director'),
    ], required=True, string='Approval Level')
    role = fields.Char(compute='_compute_role', store=True, readonly=True)
    approver_id = fields.Many2one(
        'res.users',
        string='Approver',
    )

    _sql_constraints = [
        ('unique_level', 'UNIQUE(level)',
         'Each approval level can only have one configuration record.'),
    ]

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------
    @api.depends('level')
    def _compute_name(self):
        level_labels = dict(self._fields['level'].selection)
        for rec in self:
            rec.name = level_labels.get(rec.level, _('New'))

    @api.depends('level')
    def _compute_role(self):
        for rec in self:
            rec.role = LEVEL_ROLE_MAP.get(rec.level, '')

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange('level')
    def _onchange_level(self):
        """Reset approver and set domain filtered to exact-level users."""
        self.approver_id = False
        if self.level:
            level_int = int(self.level)
            group_xmlid = LEVEL_GROUP_MAP.get(self.level)
            group = self.env.ref(group_xmlid, raise_if_not_found=False)
            if not group:
                return {'domain': {'approver_id': [('id', '=', False)]}}

            user_ids = set(group.user_ids.ids)

            # Exclude users from higher-level groups so only exact-level users show
            if level_int < 3:
                higher_xmlid = LEVEL_GROUP_MAP.get(str(level_int + 1))
                higher_group = self.env.ref(higher_xmlid, raise_if_not_found=False)
                if higher_group:
                    user_ids -= set(higher_group.user_ids.ids)

            return {'domain': {'approver_id': [('id', 'in', list(user_ids))]}}
        return {'domain': {'approver_id': [('id', '=', False)]}}

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('approver_id', 'level')
    def _check_approvers_in_group(self):
        """Ensure the selected approver belongs to the required security group."""
        for rec in self:
            if not rec.level or not rec.approver_id:
                continue
            group_xmlid = LEVEL_GROUP_MAP.get(rec.level)
            group = self.env.ref(group_xmlid, raise_if_not_found=False)
            if group and group not in rec.approver_id.group_ids:
                raise ValidationError(_(
                    "User '%s' does not belong to the required group for %s.",
                    rec.approver_id.name, rec.name,
                ))
