from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FundingAllocation(models.Model):
    """Share of an employee's contract hours that one work package of a grant funds over a period."""

    _name = 'lab.funding_allocation'
    _description = 'Funding allocation'
    _order = 'employee_id, date_from desc'

    employee_id = fields.Many2one('hr.employee', required=True, index=True, ondelete='cascade')
    task_id = fields.Many2one('project.task', string='Work package', required=True, ondelete='restrict')
    project_id = fields.Many2one(related='task_id.project_id', store=True, string='Grant')
    percentage = fields.Float(required=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(help='Leave empty while the funding runs.')
    name = fields.Char('Activity', help='What the person does on this work package; prefilled timesheet lines carry it as their description.')

    _percentage_range = models.Constraint('CHECK(percentage > 0 AND percentage <= 100)', 'The percentage must be above 0 and at most 100.')
    _date_order = models.Constraint('CHECK(date_to IS NULL OR date_to >= date_from)', 'The end date must not be before the start date.')

    def _active_on(self, day):
        """The allocations in ``self`` that cover ``day``."""
        return self.filtered(lambda a: a.date_from <= day and (not a.date_to or day <= a.date_to))

    @api.constrains('employee_id', 'percentage', 'date_from', 'date_to')
    def _check_total_percentage(self):
        """No day may be funded above 100 %; the total only changes where an allocation starts, so those days are the ones to check."""
        for alloc in self:
            mine = self.search([('employee_id', '=', alloc.employee_id.id)])
            for day in {d for d in mine.mapped('date_from') if alloc._active_on(d)}:
                if round(sum(mine._active_on(day).mapped('percentage')), 2) > 100:
                    raise ValidationError(self.env._('%(employee)s would be funded above 100%% on %(day)s.', employee=alloc.employee_id.name, day=day))
