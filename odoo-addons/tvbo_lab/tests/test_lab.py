"""Funding allocations, month prefill, public-holiday import and the EU sheet export.

Run: ``odoo -i tvbo_lab --test-enable --test-tags /tvbo_lab --stop-after-init``. The real Charité template is not in the repo, so the export runs against a minimal workbook that has the same cells.
"""
import base64
import io
import re
import zipfile
from collections import defaultdict
from datetime import date, datetime

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, freeze_time, new_test_user

from odoo.addons.tvbo_lab import eu_timesheet

ACRONYM = 'eBRAIN-Health'


def _template():
    """Smallest workbook carrying every cell the export writes, as empty styled cells."""
    refs = ['E4', 'M4', 'J7', 'J8', 'J11', 'J14', 'B31', 'H37', 'Z37', 'H38', 'Z38']
    refs += [f'B{row}' for row in eu_timesheet.WP_ROWS]
    refs += [f'{eu_timesheet.day_column(day)}{row}' for row in range(eu_timesheet.WP_ROWS.start, eu_timesheet.SPECIAL_ROW + 1) for day in range(1, 32)]
    files = {
        '[Content_Types].xml': '<Types><Override PartName="/xl/calcChain.xml" ContentType="x"/></Types>',
        'xl/workbook.xml': '<workbook><calcPr calcId="1"/></workbook>',
        'xl/_rels/workbook.xml.rels': '<Relationships><Relationship Id="rId9" Target="calcChain.xml"/></Relationships>',
        'xl/sharedStrings.xml': f'<sst><si><t>{ACRONYM}</t></si></sst>',
        eu_timesheet.SHEET_XML: '<worksheet><sheetData><row>%s</row></sheetData></worksheet>' % ''.join(f'<c r="{r}" s="1"/>' for r in refs),
        eu_timesheet.CALC_CHAIN: '<calcChain/>',
    }
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        for name, text in files.items():
            z.writestr(name, text)
    return out.getvalue()


def _cell(sheet, ref):
    match = re.search(r'<c r="%s"[^>]*>(?:<v>([^<]*)</v>|<is><t[^>]*>([^<]*)</t></is>)</c>' % ref, sheet)
    return match and (match.group(1) or match.group(2))


@tagged('post_install', '-at_install')
@freeze_time('2026-10-19')
class TestLab(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        calendar = cls.env['resource.calendar'].create({'name': 'Lab 40h', 'tz': 'Europe/Berlin'})
        cls.staff = new_test_user(cls.env, login='lab_staff', groups='tvbo_lab.group_lab_member')
        cls.pi = cls.env['hr.employee'].create({'name': 'Petra Pi', 'resource_calendar_id': calendar.id, 'tz': 'Europe/Berlin'})
        cls.ada = cls.env['hr.employee'].create({
            'name': 'Ada Lovelace', 'user_id': cls.staff.id, 'parent_id': cls.pi.id,
            'resource_calendar_id': calendar.id, 'tz': 'Europe/Berlin',
        })
        cls.grant = cls.env['project.project'].create({'name': ACRONYM, 'allow_timesheets': True, 'privacy_visibility': 'employees'})
        cls.wp1, cls.wp2 = cls.env['project.task'].create([{'name': 'WP1', 'project_id': cls.grant.id}, {'name': 'WP2', 'project_id': cls.grant.id}])
        cls.env['lab.funding_allocation'].create([
            {'employee_id': cls.ada.id, 'task_id': cls.wp1.id, 'percentage': 60, 'date_from': date(2026, 1, 1), 'name': 'Platform development'},
            {'employee_id': cls.ada.id, 'task_id': cls.wp2.id, 'percentage': 40, 'date_from': date(2026, 1, 1)},
        ])
        # Monday 7 Sep 2026 is a public holiday (Berlin midnight = 22:00 UTC).
        cls.env['resource.calendar.leaves'].create({'name': 'Holiday', 'company_id': cls.env.company.id, 'date_from': datetime(2026, 9, 6, 22), 'date_to': datetime(2026, 9, 7, 21, 59, 59)})
        sick = cls.env['hr.leave'].create({
            'employee_id': cls.ada.id, 'holiday_status_id': cls.env.ref('hr_holidays.leave_type_sick_time_off').id,
            'request_date_from': date(2026, 9, 10), 'request_date_to': date(2026, 9, 11),
        })
        sick.action_approve(check_state=False)
        cls.env['account.analytic.line'].with_user(cls.staff).create({'employee_id': cls.ada.id, 'project_id': cls.grant.id, 'task_id': cls.wp2.id, 'date': date(2026, 9, 14), 'unit_amount': 8, 'name': 'Own entry'})
        cls.env.company.lab_eu_timesheet_template = base64.b64encode(_template())

    def _month(self, day, employee=None, user=None):
        return self.env['lab.timesheet_month'].with_user(user or self.staff).create({'month': day, 'employee_id': (employee or self.ada).id, 'project_id': self.grant.id})

    def _booked(self):
        lines = self.env['account.analytic.line'].search([('employee_id', '=', self.ada.id), ('holiday_id', '=', False), ('global_leave_id', '=', False)])
        by_day = defaultdict(dict)
        for line in lines:
            by_day[line.date][line.task_id] = line.unit_amount
        return by_day

    def test_prefill_splits_funding_and_skips_absences_and_own_days(self):
        self._month(date(2026, 9, 15)).action_prefill()
        booked = self._booked()
        self.assertEqual(booked[date(2026, 9, 1)], {self.wp1: 4.8, self.wp2: 3.2})
        self.assertNotIn(date(2026, 9, 7), booked, 'public holiday')
        self.assertNotIn(date(2026, 9, 10), booked, 'sick leave')
        self.assertEqual(booked[date(2026, 9, 14)], {self.wp2: 8.0}, 'own entry kept, nothing added')
        self.assertEqual(len(booked), 19, '22 weekdays minus holiday and two sick days')

    def test_prefill_is_limited_to_recent_months(self):
        with self.assertRaises(UserError):
            self._month(date(2026, 8, 31)).action_prefill()

    def test_staff_cannot_handle_someone_else(self):
        with self.assertRaises(AccessError):
            self._month(date(2026, 10, 1), employee=self.pi).action_prefill()

    def test_funding_above_100_percent_is_refused(self):
        with self.assertRaises(ValidationError):
            self.env['lab.funding_allocation'].create({'employee_id': self.ada.id, 'task_id': self.wp1.id, 'percentage': 10, 'date_from': date(2026, 6, 1), 'date_to': date(2026, 6, 30)})

    def test_staff_see_only_their_own_funding(self):
        self.env['lab.funding_allocation'].create({'employee_id': self.pi.id, 'task_id': self.wp1.id, 'percentage': 50, 'date_from': date(2026, 1, 1)})
        seen = self.env['lab.funding_allocation'].with_user(self.staff).search([])
        self.assertEqual(seen.employee_id, self.ada)

    def test_export_fills_the_template_from_records(self):
        month = self._month(date(2026, 9, 1))
        month.action_prefill()
        action = month.action_export_eu_sheet()
        self.assertIn('/eu_file/Timesheet_2026_09_eBRAIN-Health_Ada_Lovelace.xlsm', action['url'])
        workbook = zipfile.ZipFile(io.BytesIO(base64.b64decode(month.eu_file)))
        self.assertNotIn(eu_timesheet.CALC_CHAIN, workbook.namelist())
        sheet = workbook.read(eu_timesheet.SHEET_XML).decode()
        expected = {
            'E4': 'September', 'M4': '2026', 'J7': 'Ada Lovelace', 'J11': ACRONYM, 'J14': '40',
            'B19': 'WP1', 'B20': 'WP2', 'C19': '4.8', 'C20': '3.2', 'P20': '8', 'I19': '0',
            'L26': 'X', 'M26': 'X', 'H37': 'ADA LOVELACE', 'Z37': 'PETRA PI', 'H38': None, 'B21': None,
        }
        self.assertEqual({ref: _cell(sheet, ref) for ref in expected}, expected)
        self.assertEqual(_cell(sheet, 'B31'), 'Platform development; Own entry')

    def test_export_refuses_a_grant_missing_from_the_template(self):
        self.grant.name = 'Not-A-Grant'
        with self.assertRaises(UserError):
            self._month(date(2026, 9, 1)).action_export_eu_sheet()

    def test_export_refuses_a_file_that_is_not_the_template(self):
        self.env.company.lab_eu_timesheet_template = base64.b64encode(b'not a workbook')
        with self.assertRaisesRegex(UserError, 'Time recording for EU projects'):
            self._month(date(2026, 9, 1)).action_export_eu_sheet()

    def _locate_company_in_berlin(self):
        germany = self.env.ref('base.de')
        self.env.company.write({'country_id': germany.id, 'state_id': self.env['res.country.state'].search([('country_id', '=', germany.id), ('code', '=', 'BE')]).id})
        self.env.company.resource_calendar_id.tz = 'Europe/Berlin'

    def test_public_holiday_import_is_idempotent(self):
        self._locate_company_in_berlin()
        Leaves = self.env['resource.calendar.leaves']
        Leaves.action_import_public_holidays()
        count = Leaves.search_count([('resource_id', '=', False)])
        unity_day = Leaves.search([('resource_id', '=', False), ('date_from', '=', datetime(2026, 10, 2, 22))])
        self.assertEqual(len(unity_day), 1, 'Tag der Deutschen Einheit, 3 Oct 2026')
        Leaves.action_import_public_holidays()
        self.assertEqual(Leaves.search_count([('resource_id', '=', False)]), count)

    def test_public_holiday_import_skips_days_a_closure_covers(self):
        self._locate_company_in_berlin()
        Leaves = self.env['resource.calendar.leaves']
        Leaves.create({'name': 'Winter closure', 'company_id': self.env.company.id, 'date_from': datetime(2026, 12, 23, 23), 'date_to': datetime(2026, 12, 31, 22, 59, 59)})
        Leaves.action_import_public_holidays()
        starts = set(Leaves.search([('resource_id', '=', False)]).mapped('date_from'))
        self.assertNotIn(datetime(2026, 12, 24, 23), starts, 'Christmas Day lies inside the closure')
        self.assertIn(datetime(2026, 12, 31, 23), starts, "New Year's Day follows the closure")

    def test_public_holiday_import_explains_an_unknown_state(self):
        germany = self.env.ref('base.de')
        nowhere = self.env['res.country.state'].create({'name': 'Nowhere', 'code': 'XX', 'country_id': germany.id})
        self.env.company.write({'country_id': germany.id, 'state_id': nowhere.id})
        with self.assertRaises(UserError):
            self.env['resource.calendar.leaves'].action_import_public_holidays()
