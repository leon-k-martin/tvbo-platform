# -*- coding: utf-8 -*-
{
    'name': 'TVBO - The Virtual Brain Ontology',
    'version': '19.0.1.0.1',
    'category': 'Research/Neuroscience',
    'summary': 'Data models for brain simulation, DBS, and neuroanatomical atlases',
    'description': '\n            Complete TVBO data models including:\n            - Brain simulation dynamics and experiments\n            - Deep Brain Stimulation (DBS) protocols\n            - Neuroanatomical atlases and parcellations\n        ',
    'author': 'Charité Universitätsmedizin Berlin',
    'website': 'https://github.com/virtual-twin/tvbo',
    'license': 'LGPL-3',
    'depends': ['base', 'website', 'survey', 'mass_mailing', 'tvbo_platform_docs'],
    # Building-block records and enum lookups are seeded from the tvbo
    # ground-truth database by post_init_hook (see models/ingest.py) — one flow
    # from tvbo/database/*.yaml through pydantic_loader into the Odoo DB. Only
    # security, static config, surveys and views are declarative data files.
    'data': [
        'security/ir.model.access.csv',
        'security/platform_security.xml',
        'data/survey_workshop_preworkshop.xml',
        'data/survey_workshop_feedback.xml',
        'data/website_config.xml',
        'views/website_templates.xml',
        'views/survey_customizations.xml',
        'views/portal_templates.xml',
        'views/configurator_templates.xml',
        'views/database_views.xml',
        'views/menus.xml',
        'views/literature_views.xml',
        'views/document_parser_templates.xml'
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False
}
