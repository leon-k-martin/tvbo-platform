# -*- coding: utf-8 -*-
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        """Add ``site_header``, the strip above the navbar: the current website's name when the website app is installed and the company's name otherwise, plus the company logo once it is no longer Odoo's default."""
        info = super().session_info()
        company = self.env.company
        site = self.env['website'].get_current_website() if 'website' in self.env else company
        info['site_header'] = {
            'name': site.name,
            'logo': not company.uses_default_logo and f'/web/binary/company_logo?company={company.id}',
        }
        return info
