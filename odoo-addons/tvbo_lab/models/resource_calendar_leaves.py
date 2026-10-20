from datetime import datetime, time

import holidays
import pytz

from odoo import api, fields, models
from odoo.exceptions import UserError


class ResourceCalendarLeaves(models.Model):
    _inherit = 'resource.calendar.leaves'

    @api.model
    def action_import_public_holidays(self):
        """Create this and next year's public holidays of the company's country and state, skipping days that already have one, then show the list for manual curation."""
        company = self.env.company
        if not company.country_id:
            raise UserError(self.env._('Set the country (and state) of %s first.', company.name))
        tz = pytz.timezone(company.resource_calendar_id.tz or 'UTC')

        def utc(day, clock):
            return tz.localize(datetime.combine(day, clock)).astimezone(pytz.utc).replace(tzinfo=None)

        existing = {pytz.utc.localize(leave.date_from).astimezone(tz).date() for leave in self.search([('company_id', '=', company.id), ('resource_id', '=', False)])}
        year = fields.Date.today().year
        found = holidays.country_holidays(company.country_id.code, subdiv=company.state_id.code or None, years=[year, year + 1])
        self.create([{
            'name': name,
            'company_id': company.id,
            'date_from': utc(day, time.min),
            'date_to': utc(day, time(23, 59, 59)),
        } for day, name in sorted(found.items()) if day not in existing])
        return self.env['ir.actions.act_window']._for_xml_id('hr_holidays.open_view_public_holiday')
