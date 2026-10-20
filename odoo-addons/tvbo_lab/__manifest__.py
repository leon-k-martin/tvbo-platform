# -*- coding: utf-8 -*-
{
    'name': 'TVBO Lab',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Funding allocations, timesheet prefill, public-holiday import and the Charité EU timesheet export',
    'description': """
        Runs the lab's admin on Odoo's own Time Off, Timesheets, Project and Maintenance apps. The PI records which work package of which grant funds what share of each person's hours; staff prefill a month from that funding (holidays and approved leave excluded, own entries kept), correct it, and export the Charité "Time recording for EU projects" sheet filled from those records.
    """,
    'author': 'Charité Universitätsmedizin Berlin',
    'website': 'https://github.com/virtual-twin/tvbo',
    'license': 'LGPL-3',
    'depends': ['hr_timesheet', 'hr_holidays', 'project_timesheet_holidays', 'maintenance'],
    'external_dependencies': {'python': ['holidays']},
    'data': [
        'security/lab_security.xml',
        'security/ir.model.access.csv',
        'views/lab_views.xml',
    ],
    'installable': True,
    'application': False,
}
