"""The Lab app: Odoo's lab apps under one menu, everyday items first and the ones only the PI or an admin can use marked "(admin)"."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestLabMenus(TransactionCase):

    def _lab_apps(self, user):
        """Map each app under Lab to the names of its items, in the order the user's menu shows them."""
        menus = self.env['ir.ui.menu'].with_user(user).load_menus(debug=False)
        lab = menus[self.env.ref('tvbo_lab.menu_lab_root').id]
        return {menus[app]['name']: [menus[item]['name'] for item in menus[app]['children']] for app in lab['children']}

    def test_member_sees_everyday_items_only(self):
        apps = self._lab_apps(new_test_user(self.env, login='lab_menu_member', groups='tvbo_lab.group_lab_member'))
        self.assertEqual(apps['Timesheets'], ['My Timesheets', 'Monthly Sheet', 'Funding'])
        self.assertEqual(apps['Time Off'][:3], ['Dashboard', 'My Time Off', 'My Allocations'])
        self.assertFalse([item for items in apps.values() for item in items if item.endswith('(admin)')])

    def test_pi_sees_admin_items_after_everyday_ones(self):
        apps = self._lab_apps(new_test_user(self.env, login='lab_menu_pi', groups='tvbo_lab.group_lab_manager'))
        self.assertEqual(list(apps), ['Timesheets', 'Time Off', 'Project', 'Employees', 'Maintenance'])
        self.assertEqual(apps['Timesheets'], ['My Timesheets', 'Monthly Sheet', 'Funding', 'All Timesheets (admin)', 'Reporting (admin)'])
        self.assertEqual(apps['Employees'][-5:], ['Employees (admin)', 'Team (admin)', 'Learning (admin)', 'Reporting (admin)', 'Configuration (admin)'])
