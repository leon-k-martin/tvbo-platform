# -*- coding: utf-8 -*-
"""The portal dashboard on /my: the widgets a user may place there, the arrangement they chose and the data each widget shows."""
from collections import Counter

from odoo import _, fields, models

_SAVED_MODELS = [('dynamics_id', '!=', False)]  # shares of a model saved from the configurator


def _placeable(keys, catalogue):
    """The keys in ``keys`` that ``catalogue`` offers, each once and in order; anything but a list counts as no keys."""
    available = {widget['key'] for widget in catalogue}
    return list(dict.fromkeys(key for key in keys if isinstance(key, str) and key in available)) if isinstance(keys, list) else []


class ResUsers(models.Model):
    _inherit = 'res.users'

    dashboard_widgets = fields.Json(help="Keys of the widgets on this user's portal dashboard, in order; empty shows the defaults.")

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['dashboard_widgets']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['dashboard_widgets']

    def _dashboard_catalogue(self):
        """The widgets this user may place on the dashboard, in default order. Each names its template, which loads its own data, and whether a new dashboard shows it."""
        self.ensure_one()
        widgets = []
        if self._is_internal():
            widgets.append({'key': 'tasks', 'name': _("My tasks"), 'description': _("Activities assigned to you, overdue ones first."), 'template': 'tvbo.dashboard_tasks', 'default': True})
        widgets.append({'key': 'models', 'name': _("My models"), 'description': _("The models you saved, by publication state."), 'template': 'tvbo.dashboard_models', 'default': True})
        if self.has_group('tvbo.group_tvbo_reviewer'):
            widgets.append({'key': 'reviews', 'name': _("Reviews"), 'description': _("Models waiting for a reviewer, oldest first."), 'template': 'tvbo.dashboard_reviews', 'default': True})
        widgets.append({'key': 'shared', 'name': _("Shared with me"), 'description': _("Models colleagues shared with you."), 'template': 'tvbo.dashboard_shared', 'default': False})
        widgets.append({'key': 'api_keys', 'name': _("API keys"), 'description': _("Keys for the tvbo Python client."), 'template': 'tvbo.dashboard_api_keys', 'default': False})
        return widgets

    def _dashboard_layout(self):
        """The widgets on this user's dashboard in order, and the ones they may still add. The dashboard shows their own arrangement, or the defaults while it holds no widget they may still place."""
        catalogue = self._dashboard_catalogue()
        keys = _placeable(self.dashboard_widgets, catalogue) or [widget['key'] for widget in catalogue if widget['default']]
        by_key = {widget['key']: widget for widget in catalogue}
        return [by_key[key] for key in keys], [widget for widget in catalogue if widget['key'] not in keys]

    def _dashboard_keys(self):
        """The keys of the widgets on this user's dashboard, in order."""
        return [widget['key'] for widget in self._dashboard_layout()[0]]

    def _set_dashboard_keys(self, keys):
        """Store the user's arrangement, keeping each widget they may place once; an empty arrangement, like None, goes back to the defaults."""
        self.dashboard_widgets = _placeable(keys, self._dashboard_catalogue())

    def _dashboard_tasks(self):
        """The user's next open activities, soonest deadline first, and how many are overdue."""
        Activity = self.env['mail.activity']
        domain = [('user_id', '=', self.id)]
        return {
            'activities': Activity.search(domain, order='date_deadline, id', limit=6),
            'overdue': Activity.search_count(domain + [('date_deadline', '<', fields.Date.context_today(self))]),
        }

    def _shares_summary(self, domain, order, limit):
        """How many shares of saved models match ``domain``, and the first ``limit`` of them in ``order``."""
        Share = self.env['tvbo.model_share'].sudo()
        domain = _SAVED_MODELS + domain
        return {'count': Share.search_count(domain), 'records': Share.search(domain, order=order, limit=limit)}

    def _dashboard_models(self):
        """How many of the user's saved models are in each publication state, and the three changed last."""
        Share = self.env['tvbo.model_share'].sudo()
        domain = _SAVED_MODELS + [('owner_user_id', '=', self.id)]
        return {'counts': Counter(dict(Share._read_group(domain, ['publication_state'], ['__count']))), 'latest': Share.search(domain, order='write_date desc', limit=3)}

    def _dashboard_reviews(self):
        """How many models wait for a reviewer, and the three waiting longest."""
        return self._shares_summary([('publication_state', '=', 'in_review')], 'submitted_date, id', 3)

    def _dashboard_shared(self):
        """How many models colleagues shared with the user, and the four changed last."""
        return self._shares_summary([('shared_user_ids', 'in', self.id)], 'write_date desc', 4)

    def _dashboard_api_keys(self):
        return self.env['tvbo.api_key'].sudo().search([('user_id', '=', self.id)], order='create_date desc')
