"""Doc pages render ``{{base_url}}`` with the public address in force when the docs are imported."""
from odoo.tests.common import TransactionCase


class TestDocPage(TransactionCase):

    def test_reimport_renders_the_current_public_address(self):
        self.env['ir.config_parameter'].set_param('web.base.url', 'https://docs.example.org')
        self.env['tvbo.doc.page'].import_docs()
        page = self.env['tvbo.doc.page'].search([('source_path', '=', 'docs/account/index.md')])
        self.assertIn('href="https://docs.example.org/web/login"', page.content_html)
