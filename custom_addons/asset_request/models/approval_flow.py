from odoo import models, fields, _


class ApprovalFlow(models.Model):
    _name = 'approval.flow'
    _description = 'Approval Flow'
    _order = 'name'

    name = fields.Char(required=True, string='Flow Name',
                       help='e.g. Asset Request Approval')
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    level_ids = fields.One2many('approval.level', 'flow_id', string='Approval Levels')

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Flow name must be unique.'),
    ]

    def get_ordered_levels(self):
        """Return levels ordered by sequence."""
        self.ensure_one()
        return self.level_ids.sorted('sequence')
