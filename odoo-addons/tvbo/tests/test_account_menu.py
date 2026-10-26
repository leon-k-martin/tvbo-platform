# -*- coding: utf-8 -*-
"""The one account menu: the same entries on the website and in the backend, with the backend link for staff only; the portal's left menu does not repeat them, and visitors are asked to log in."""
from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestAccountMenu(HttpCase):

    def test_website_and_backend_show_the_same_entries(self):
        staff = new_test_user(self.env, login='menu_staff', password='menu_staff_pw1', groups='base.group_user')
        portal = new_test_user(self.env, login='menu_portal', groups='base.group_portal')
        self.assertIn('backend', [entry['key'] for entry in staff._account_menu()])
        self.assertNotIn('backend', [entry['key'] for entry in portal._account_menu()])
        self.assertIn('Log in</a>', self.url_open('/').text)
        self.authenticate('menu_staff', 'menu_staff_pw1')
        self.assertEqual(self.make_jsonrpc_request('/web/session/get_session_info')['account_menu'], staff._account_menu())
        page = self.url_open('/my').text
        for entry in staff._account_menu():
            self.assertIn(f'href="{entry["url"]}"', page)
        self.assertEqual(page.count('/web/session/logout'), 1, 'the left menu leaves logging out to the account menu')
        self.assertEqual(page.count('href="/odoo"'), 1, 'the left menu leaves the backend link to the account menu')
