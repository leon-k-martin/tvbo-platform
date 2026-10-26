# -*- coding: utf-8 -*-
"""The one account menu under the user's name, the same on the website and in the backend."""
from odoo import _, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _account_menu(self):
        """The entries of the user's account menu, in order, each with a key, label, link and Font Awesome icon. The backend opens Odoo's preferences dialog for the ``preferences`` entry instead of following its link."""
        self.ensure_one()
        entries = [
            {'key': 'website', 'label': _("Website"), 'url': '/', 'icon': 'fa-globe'},
            {'key': 'dashboard', 'label': _("Dashboard"), 'url': '/my', 'icon': 'fa-th-large'},
        ]
        if self._is_internal():
            entries.append({'key': 'backend', 'label': _("Backend"), 'url': '/odoo', 'icon': 'fa-th'})
        return entries + [
            {'key': 'preferences', 'label': _("Preferences"), 'url': '/my/account', 'icon': 'fa-sliders'},
            {'key': 'docs', 'label': _("Documentation"), 'url': '/docs', 'icon': 'fa-book'},
            {'key': 'logout', 'label': _("Log out"), 'url': '/web/session/logout?redirect=/', 'icon': 'fa-sign-out'},
        ]
