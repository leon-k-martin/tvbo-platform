# -*- coding: utf-8 -*-
{
    'name': 'TVBO Lab',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Team branches, funding allocations, timesheet prefill, public-holiday import, the Charité EU timesheet export, student projects and an internal lab forum',
    'description': """
        Runs the lab's admin on Odoo's own Time Off, Timesheets, Project and Maintenance apps. Charité holds two branches, the Brain Simulation Section and TVB-O, each with its own team and job positions; the website belongs to TVB-O and the lab admin to the Section. The PI records which work package of which grant funds what share of each person's hours; staff prefill a month from that funding (holidays and approved leave excluded, own entries kept), correct it, and export the Charité "Time recording for EU projects" sheet filled from those records. Managers see current and former members in one Team list, and supervisors track internships, lab rotations and theses; the students themselves are employees of type Student or Trainee. Odoo's lab apps sit together under one Lab app, everyday items first and the ones only the PI or an admin can use marked "(admin)", and the portal dashboard gains a Lab widget (hours this month and shortcuts) and an Agenda widget. A private Lab forum, styled apart from the public Community forum, is open to lab members only.
    """,
    'author': 'Charité Universitätsmedizin Berlin',
    'website': 'https://github.com/virtual-twin/tvbo',
    'license': 'LGPL-3',
    'depends': ['tvbo', 'hr_timesheet', 'hr_holidays', 'hr_skills', 'project_timesheet_holidays', 'maintenance', 'website_forum'],
    'external_dependencies': {'python': ['holidays']},
    'data': [
        'security/lab_security.xml',
        'security/ir.model.access.csv',
        'data/team_data.xml',
        'data/forum_data.xml',
        'views/lab_views.xml',
        'views/team_views.xml',
        'views/menus.xml',
        'views/dashboard_templates.xml',
        'views/forum_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'tvbo_lab/static/src/css/lab_forum.css',
        ],
    },
    'installable': True,
    'application': False,
}
