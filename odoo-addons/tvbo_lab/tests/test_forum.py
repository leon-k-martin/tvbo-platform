"""The private Lab forum: only lab members see it, it looks internal, and the Lab widget and the Lab menu lead to it."""
from odoo.tests import tagged
from odoo.tests.common import HttpCase, new_test_user


@tagged('post_install', '-at_install')
class TestLabForum(HttpCase):

    def test_only_lab_members_see_the_lab_forum_and_it_looks_internal(self):
        forum = self.env.ref('tvbo_lab.forum_lab')
        member = new_test_user(self.env, login='forum_member', groups='tvbo_lab.group_lab_member')
        outsider = new_test_user(self.env, login='forum_outsider', groups='base.group_user')
        self.assertFalse(self.env['forum.forum'].with_user(outsider).search([('id', '=', forum.id)]))
        self.env['forum.post'].with_user(member).create({'forum_id': forum.id, 'name': 'Journal club on Friday', 'content': '<p>Room 2.04</p>'})
        url = self.env.ref('tvbo_lab.action_lab_forum').url
        self.assertNotIn(b'Journal club', self.url_open(url).content, 'hidden from visitors')
        self.authenticate('forum_member', 'forum_member')
        page = self.url_open(url)
        self.assertEqual(page.status_code, 200)
        for marker in (b'data-forum-privacy="private"', b'o_lab_forum_banner', b'Journal club'):
            self.assertIn(marker, page.content)
        self.assertIn(f'href="{url}"'.encode(), self.url_open('/my').content, 'the Lab widget links to the forum')
        self.assertEqual(self.make_jsonrpc_request('/web/action/load', {'action_id': 'tvbo_lab.action_lab_forum'})['url'], url, 'the Lab menu opens the forum')
