"""Lab widgets for the portal dashboard: the user's agenda, and their hours this month with shortcuts into the Lab app."""
from odoo import _, fields, models
from odoo.tools import date_utils


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _dashboard_catalogue(self):
        widgets = super()._dashboard_catalogue()
        if self.has_group('tvbo_lab.group_lab_member'):
            widgets.append({'key': 'lab', 'name': _("Lab"), 'description': _("Your hours this month and shortcuts into the Lab app."), 'template': 'tvbo_lab.dashboard_lab', 'default': True})
        if self._is_internal():
            widgets.append({'key': 'agenda', 'name': _("Agenda"), 'description': _("Your next calendar events."), 'template': 'tvbo_lab.dashboard_agenda', 'default': False})
        return widgets

    def _dashboard_lab(self):
        """The first of this month and the hours the user logged on projects within it. Read as superuser, because the website runs in the TVB-O branch and the company rule would otherwise hide the user's Section timesheets."""
        first, last = date_utils.get_month(fields.Date.context_today(self))
        [[hours]] = self.env['account.analytic.line'].sudo()._read_group([('user_id', '=', self.id), ('project_id', '!=', False), ('date', '>=', first), ('date', '<=', last)], aggregates=['unit_amount:sum'])
        return {'month': first, 'hours': hours or 0.0}

    def _dashboard_agenda(self):
        """The user's next five calendar events."""
        return self.env['calendar.event'].search([('partner_ids', 'in', self.partner_id.id), ('stop', '>=', fields.Datetime.now())], order='start', limit=5)
