"""Team: the Section and TVB-O branches under Charité with their own positions, the Team list of current and former members, and student projects inside a branch."""
from datetime import date

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user
from odoo.tools import mute_logger
from odoo.tools.safe_eval import safe_eval


@tagged('post_install', '-at_install')
class TestTeam(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.section, cls.tvbo = cls.env.ref('tvbo_lab.company_section'), cls.env.ref('tvbo_lab.company_tvbo')
        in_section = {'company_id': cls.section.id, 'company_ids': [(6, 0, cls.section.ids)]}
        cls.supervisor_user, cls.student_user, cls.other_user = (new_test_user(cls.env, login=login, groups='tvbo_lab.group_lab_member', **in_section) for login in ('lab_supervisor', 'lab_student', 'lab_other'))
        cls.pi_user = new_test_user(cls.env, login='lab_pi', groups='tvbo_lab.group_lab_manager', **in_section)
        cls.student = cls.env['hr.employee'].create({'name': 'Stu Dent', 'user_id': cls.student_user.id, 'employee_type': 'student', 'company_id': cls.section.id})
        cls.project = cls.env['lab.student_project'].with_user(cls.supervisor_user).create({
            'name': 'Fitting SupHopf to resting-state FC', 'kind': 'master', 'student_id': cls.student.id,
            'date_start': date(2026, 4, 1), 'date_end': date(2026, 9, 30),
        })

    def _visible(self, user):
        return self.env['lab.student_project'].with_user(user).search([('id', '=', self.project.id)])

    def test_branches_positions_and_website(self):
        """Both branches sit under Charité with their own positions, and the website belongs to TVB-O."""
        self.assertEqual((self.section | self.tvbo).parent_id, self.env.ref('base.main_company'))
        self.assertEqual(self.env.ref('tvbo_lab.job_section_researcher').company_id, self.section)
        self.assertEqual(self.env.ref('tvbo_lab.job_tvbo_developer').company_id, self.tvbo)
        self.assertEqual(self.env.ref('website.default_website').company_id, self.tvbo)

    def test_team_lists_current_and_former_members(self):
        former = self.env['hr.employee'].create({'name': 'Fay Former', 'company_id': self.section.id})
        former.active = False
        team = self.env['hr.employee'].with_user(self.pi_user).search(safe_eval(self.env.ref('tvbo_lab.action_team').domain))
        self.assertLessEqual(former | self.student, team)

    def test_supervisor_creates_and_manages_own_project(self):
        """Whoever creates a project supervises it, it belongs to the student's branch, and other lab members do not see it."""
        self.assertEqual(self.project.supervisor_ids, self.supervisor_user)
        self.assertEqual(self.project.company_id, self.section)
        self._visible(self.supervisor_user).write({'state': 'running'})
        self.assertEqual(self.project.state, 'running')
        self.assertFalse(self._visible(self.other_user))

    def test_student_reads_but_cannot_change_own_project(self):
        mine = self._visible(self.student_user)
        self.assertEqual(mine, self.project)
        with self.assertRaises(AccessError):
            mine.write({'state': 'done'})

    def test_managers_see_the_projects_of_their_branches(self):
        tvbo_pi = new_test_user(self.env, login='tvbo_pi', groups='tvbo_lab.group_lab_manager', company_id=self.tvbo.id, company_ids=[(6, 0, self.tvbo.ids)])
        self.assertEqual(self._visible(self.pi_user), self.project)
        self.assertFalse(self._visible(tvbo_pi))

    @mute_logger('odoo.sql_db')
    def test_end_before_start_is_rejected(self):
        with self.assertRaises(IntegrityError):
            self.project.write({'date_end': date(2026, 3, 1)})
            self.env.flush_all()
