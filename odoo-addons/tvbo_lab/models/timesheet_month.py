import base64
from collections import defaultdict
from datetime import datetime, time
from urllib.parse import quote

import pytz
from dateutil.relativedelta import relativedelta

from odoo import fields, models
from odoo.exceptions import AccessError, UserError

from .. import eu_timesheet


class TimesheetMonth(models.TransientModel):
    """One employee's month: prefill it from their funding, or export it as the Charité EU timesheet."""

    _name = 'lab.timesheet_month'
    _description = 'Monthly timesheet'

    employee_id = fields.Many2one('hr.employee', required=True, default=lambda self: self.env.user.employee_id)
    month = fields.Date(required=True, default=fields.Date.context_today, help='Any day of the month.')
    project_id = fields.Many2one('project.project', string='Grant', domain=[('allow_timesheets', '=', True)])
    eu_file = fields.Binary(readonly=True)

    def _check_employee(self):
        """Staff handle their own month; lab managers anyone's."""
        self.ensure_one()
        if self.employee_id != self.env.user.employee_id and not self.env.user.has_group('tvbo_lab.group_lab_manager'):
            raise AccessError(self.env._('You can only handle your own timesheets.'))

    def _bounds(self):
        start = self.month.replace(day=1)
        return start, start + relativedelta(months=1, days=-1)

    def _work_hours(self, domain=None):
        """Scheduled hours per day of the month, minus the absences ``domain`` matches (Odoo's default: all of them)."""
        start, end = self._bounds()
        employee = self.employee_id.sudo()
        tz = pytz.timezone(employee.tz or 'UTC')
        span = (tz.localize(datetime.combine(start, time.min)), tz.localize(datetime.combine(end, time.max)))
        return dict(employee._list_work_time_per_day(*span, domain=domain)[employee.id])

    def action_prefill(self):
        """Book every scheduled, non-absent day that has no own entry yet on the funding work packages, split by their percentages."""
        self._check_employee()
        start, end = self._bounds()
        this_month = fields.Date.context_today(self).replace(day=1)
        if not this_month - relativedelta(months=1) <= start <= this_month:
            raise UserError(self.env._('Only the current or the previous month can be prefilled.'))
        Line = self.env['account.analytic.line']
        month = [('employee_id', '=', self.employee_id.id), ('date', '>=', start), ('date', '<=', end)]
        booked = set(Line.search(month + [('holiday_id', '=', False), ('global_leave_id', '=', False)]).mapped('date'))
        allocations = self.env['lab.funding_allocation'].search([('employee_id', '=', self.employee_id.id)])
        Line.create([{
            'employee_id': self.employee_id.id,
            'project_id': alloc.project_id.id,
            'task_id': alloc.task_id.id,
            'date': day,
            'unit_amount': round(hours * alloc.percentage / 100, 2),
            'name': alloc.name or '/',
        } for day, hours in self._work_hours().items() if day not in booked for alloc in allocations._active_on(day)])
        action = self.env['ir.actions.act_window']._for_xml_id('hr_timesheet.act_hr_timesheet_line')
        action.update(domain=month, context={'is_timesheet': 1})
        return action

    def _absence_rows(self):
        """Template row of each validated absence day the employee was scheduled to work (public holidays excluded)."""
        start, end = self._bounds()
        scheduled = self._work_hours(domain=[('time_type', '=', 'leave'), ('resource_id', '=', False)])
        row_of_type = {
            self.env.ref('hr_holidays.leave_type_sick_time_off'): eu_timesheet.SICK_ROW,
            self.env.ref('hr_holidays.leave_type_paid_time_off'): eu_timesheet.VACATION_ROW,
        }
        leaves = self.env['hr.leave'].sudo().search([
            ('employee_id', '=', self.employee_id.id), ('state', '=', 'validate'),
            ('request_date_from', '<=', end), ('request_date_to', '>=', start),
        ])
        return {
            day: row_of_type.get(leave.holiday_status_id, eu_timesheet.SPECIAL_ROW)
            for leave in leaves for day in scheduled
            if leave.request_date_from <= day <= leave.request_date_to
        }

    def action_export_eu_sheet(self):
        """Fill the company's EU timesheet template with this month's hours on the grant and the absences, and download it."""
        self._check_employee()
        template = self.env.company.lab_eu_timesheet_template
        if not template:
            raise UserError(self.env._('Upload the EU timesheet template on the company first.'))
        template = base64.b64decode(template)
        grant = self.project_id
        if not grant or grant.name not in eu_timesheet.acronyms(template):
            raise UserError(self.env._('Pick a grant whose name is an acronym from the template, e.g. "eBRAIN-Health".'))
        start, end = self._bounds()
        employee = self.employee_id.sudo()
        lines = self.env['account.analytic.line'].search([('employee_id', '=', employee.id), ('project_id', '=', grant.id), ('date', '>=', start), ('date', '<=', end)])
        hours = defaultdict(lambda: defaultdict(float))
        for line in lines:
            hours[line.task_id.name or grant.name][line.date.day] += line.unit_amount
        if len(hours) > len(eu_timesheet.WP_ROWS):
            raise UserError(self.env._('The template has room for %s work packages per grant and month.', len(eu_timesheet.WP_ROWS)))
        cells = {
            'E4': eu_timesheet.MONTH_LABELS[start.month],
            'M4': start.year,
            'J7': employee.name,
            'J8': 'A.1 ',
            'J11': grant.name,
            'J14': employee._get_version(start).resource_calendar_id.hours_per_week,
            'B31': '; '.join(dict.fromkeys(n for n in lines.mapped('name') if n and n != '/')),
            'H37': employee.name.upper(),
        }
        if employee.parent_id:
            cells['Z37'] = employee.parent_id.name.upper()
        for row, (wp, per_day) in zip(eu_timesheet.WP_ROWS, sorted(hours.items())):
            cells[f'B{row}'] = wp
            cells.update({f'{eu_timesheet.day_column(day)}{row}': round(per_day[day], 2) for day in range(1, end.day + 1)})
        cells.update({f'{eu_timesheet.day_column(day.day)}{row}': 'X' for day, row in self._absence_rows().items()})
        self.eu_file = base64.b64encode(eu_timesheet.fill(template, cells))
        filename = f'Timesheet_{start:%Y_%m}_{grant.name}_{employee.name}.xlsm'.replace(' ', '_')
        return {'type': 'ir.actions.act_url', 'url': f'/web/content/{self._name}/{self.id}/eu_file/{quote(filename)}?download=true', 'target': 'self'}
