from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    lab_eu_timesheet_template = fields.Binary('EU timesheet template', help='The Charité "Time recording for EU projects" .xlsm that the monthly sheet export fills.')
