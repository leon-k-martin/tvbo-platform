"""The portal dashboard's lab widgets: lab members start with the Lab widget, which shows the hours they logged this month."""
from odoo import fields
from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user
from odoo.tools import date_utils


@tagged('post_install', '-at_install')
class TestLabDashboard(HttpCase):

    def test_member_starts_with_the_lab_widget_showing_this_months_hours(self):
        member = new_test_user(self.env, login='lab_dash_member', password='lab_dash_member1', groups='tvbo_lab.group_lab_member')
        employee = self.env['hr.employee'].create({'name': 'Dee Ashboard', 'user_id': member.id})
        project = self.env['project.project'].create({'name': 'Dashboard check', 'allow_timesheets': True})
        today = fields.Date.today()
        self.env['account.analytic.line'].create([
            {'name': 'Fitting', 'project_id': project.id, 'employee_id': employee.id, 'unit_amount': 2.5, 'date': today},
            {'name': 'Next month', 'project_id': project.id, 'employee_id': employee.id, 'unit_amount': 4, 'date': date_utils.add(today, months=1)},
        ])
        self.assertEqual(member._dashboard_keys(), ['tasks', 'models', 'lab'])
        self.assertEqual(member._dashboard_lab()['hours'], 2.5)
        self.authenticate('lab_dash_member', 'lab_dash_member1')
        page = self.url_open('/my').text
        self.assertIn('data-key="lab"', page)
        self.assertIn('02:30', page)
