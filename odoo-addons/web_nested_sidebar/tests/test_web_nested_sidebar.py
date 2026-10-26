# -*- coding: utf-8 -*-
import base64

from odoo.tests import HttpCase, tagged
from odoo.tools.misc import file_open


@tagged('post_install', '-at_install')
class TestNestedSidebar(HttpCase):

    def test_backend_bundle_ships_the_addon(self):
        """The backend bundle carries the addon's scripts, templates and styles, and its styles compile."""
        bundle = self.env['ir.qweb']._get_asset_bundle('web.assets_backend')
        urls = {asset.url for asset in bundle.javascripts + bundle.templates + bundle.stylesheets}
        expected = {f'/web_nested_sidebar/static/src/{name}' for name in (
            'side_menu.js', 'side_menu.xml', 'side_menu.scss',
            'site_header.js', 'site_header.xml', 'site_header.scss',
        )}
        self.assertLessEqual(expected, urls)
        bundle.css()
        self.assertFalse(bundle.css_errors)

    def test_session_info_describes_the_site_header(self):
        """The strip is named after the website when the website app is installed and after the company otherwise, and shows the company logo only once it is not Odoo's default."""
        company = self.env.ref('base.main_company')
        company.name = 'Example Company'
        expected = 'Example Company'
        if 'website' in self.env:
            self.env['website'].search([]).write({'name': 'Example Website'})
            expected = 'Example Website'
        self.authenticate('admin', 'admin')
        info = self.make_jsonrpc_request('/web/session/get_session_info')
        self.assertEqual(info['site_header'], {'name': expected, 'logo': False})

        with file_open('web/static/img/logo2.png', 'rb') as logo:
            company.logo = base64.b64encode(logo.read())
        info = self.make_jsonrpc_request('/web/session/get_session_info')
        self.assertEqual(info['site_header']['logo'], f'/web/binary/company_logo?company={company.id}')
