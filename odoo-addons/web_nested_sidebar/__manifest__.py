# -*- coding: utf-8 -*-
{
    'name': 'Nested Backend Sidebar',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'A strip above the backend navbar that links back to the website, and a side menu listing every app with its menus nested',
    'description': """
        Adds a dark strip above the backend navbar with the site's name (and the company logo once one is set) linking to the website, a "Backend" badge and the backend's only account menu, which takes the place of Odoo's avatar menu; a platform that sends its own entries as account_menu in the session info gets the same menu as on its website. A side menu lists every app with its menus nested underneath; the current app is unfolded and the current page marked as you move around. On wide screens it stays open beside the page, and the menu button folds it to app icons, which each browser remembers; on narrower screens the menu button opens it as a drawer over the page. It reads Odoo's own menu data, so it shows exactly the menus each user may see. On phones Odoo's own menu is kept. A platform recolours the strip with the CSS variables --o-site-header-bg and --o-site-header-accent.
    """,
    'author': 'Charité Universitätsmedizin Berlin',
    'website': 'https://github.com/virtual-twin/tvbo',
    'license': 'LGPL-3',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'web_nested_sidebar/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
