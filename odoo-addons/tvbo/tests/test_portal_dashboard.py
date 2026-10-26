# -*- coding: utf-8 -*-
"""The portal dashboard: everyone lands on /my after login, starts with the widgets for their role and can rearrange them."""
import re
from datetime import timedelta
from urllib.parse import urlsplit

from odoo import fields
from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestPortalDashboard(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal = new_test_user(cls.env, login='dash_portal', password='dash_portal_pw1', groups='base.group_portal')
        cls.reviewer = new_test_user(cls.env, login='dash_reviewer', password='dash_reviewer_pw1', groups='base.group_user,tvbo.group_tvbo_reviewer')

    def _login(self, login, password, redirect=None):
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', self.url_open('/web/login').text).group(1)
        data = {'login': login, 'password': password, 'csrf_token': csrf, **({'redirect': redirect} if redirect else {})}
        return urlsplit(self.url_open('/web/login', data=data, allow_redirects=False).headers['Location']).path

    def test_defaults_follow_the_role(self):
        self.assertEqual(self.portal._dashboard_keys(), ['models'])
        self.assertEqual(self.reviewer._dashboard_keys(), ['tasks', 'models', 'reviews'])

    def test_arrangement_keeps_each_allowed_widget_once(self):
        mine = self.portal.with_user(self.portal)
        mine._set_dashboard_keys(['api_keys', 'tasks', 'api_keys', 'unknown', 'models'])
        self.assertEqual(self.portal._dashboard_keys(), ['api_keys', 'models'])
        mine._set_dashboard_keys(None)
        self.assertEqual(self.portal._dashboard_keys(), ['models'])

    def test_login_lands_on_the_dashboard_unless_a_page_is_named(self):
        self.assertEqual(self._login('dash_reviewer', 'dash_reviewer_pw1'), '/my')
        self.url_open('/web/session/logout')
        self.assertEqual(self._login('dash_portal', 'dash_portal_pw1'), '/my')
        self.url_open('/web/session/logout')
        self.assertEqual(self._login('dash_portal', 'dash_portal_pw1', redirect='/tvbo/kg'), '/tvbo/kg')

    def test_dashboard_renders_the_widgets_in_the_saved_order(self):
        self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get_id('res.partner'), 'res_id': self.reviewer.partner_id.id,
            'user_id': self.reviewer.id, 'summary': 'Check the draft', 'date_deadline': fields.Date.today() - timedelta(days=1),
        })
        self.authenticate('dash_reviewer', 'dash_reviewer_pw1')
        page = self.url_open('/my').text
        self.assertIn('Check the draft', page)
        self.assertIn('1 overdue', page)
        result = self.make_jsonrpc_request('/my/dashboard/widgets', {'keys': ['reviews', 'models']})
        self.assertEqual(result['keys'], ['reviews', 'models'])
        page = self.url_open('/my').text
        self.assertNotIn('data-key="tasks"', page)
        self.assertLess(page.index('data-key="reviews"'), page.index('data-key="models"'))

    def test_account_pages_share_the_menu_and_mark_the_current_page(self):
        self.authenticate('dash_portal', 'dash_portal_pw1')
        page = self.url_open('/my/models').text
        self.assertRegex(page, r'href="/my/models"[^>]*aria-current="page"')
        self.assertNotIn('/odoo/action-tvbo.action_publication_review', page)
