# -*- coding: utf-8 -*-
"""Portal pages for user-saved models.

- ``/my/models``            owner's own saved models (the portal dashboard)
- ``/tvbo/models/shared``   community gallery of models other users have shared
- visibility / delete       owner-only mutations on a saved model

Ownership and private/shared state live in the platform-only ``tvbo.model_share``
table (see models/model_sharing.py); the schema entity ``tvbo.dynamics`` carries
none of it. Reads use ``sudo()`` to reach the shared/ground-truth records, but
every query is scoped by owner/visibility and mutations verify ownership first.
"""
from odoo import http
from odoo.http import request


class TVBOPortal(http.Controller):

    def _shares(self):
        return request.env['tvbo.model_share'].sudo()

    # ------------------------------------------------------------------ #
    # Pages
    # ------------------------------------------------------------------ #
    @http.route('/my/models', type='http', auth='public', website=True)
    def my_models(self, **kw):
        """Portal dashboard: the logged-in user's own saved models."""
        if request.env.user._is_public():
            return request.redirect('/web/login?redirect=/my/models')
        shares = self._shares().search(
            [('owner_user_id', '=', request.env.user.id)], order='write_date desc')
        return request.render('tvbo.portal_my_models', {
            'shares': shares,
            'page_name': 'my_models',
        })

    @http.route('/tvbo/models/shared', type='http', auth='public', website=True)
    def shared_models(self, **kw):
        """Community gallery: models other users have shared (own ones badged)."""
        if request.env.user._is_public():
            return request.redirect('/web/login?redirect=/tvbo/models/shared')
        shares = self._shares().search(
            [('visibility', '=', 'shared')], order='write_date desc')
        return request.render('tvbo.portal_shared_models', {
            'shares': shares,
            'current_uid': request.env.user.id,
            'page_name': 'shared_models',
        })

    # ------------------------------------------------------------------ #
    # Owner-only mutations (model_id is the tvbo.dynamics id)
    # ------------------------------------------------------------------ #
    def _owned_share(self, model_id):
        """Return the share row only if it exists and the caller owns it."""
        share = self._shares().search([('dynamics_id', '=', model_id)], limit=1)
        if not share or share.owner_user_id.id != request.env.user.id:
            return None
        return share

    @http.route('/my/models/<int:model_id>/visibility', type='jsonrpc',
                auth='user', csrf=False)
    def set_visibility(self, model_id, visibility=None, **kw):
        """Flip a model between private and shared (owner only)."""
        if visibility not in ('private', 'shared'):
            return {'success': False, 'error': 'invalid visibility'}
        share = self._owned_share(model_id)
        if share is None:
            return {'success': False, 'error': 'not found or not owner'}
        share.write({'visibility': visibility})
        return {'success': True, 'visibility': visibility}

    @http.route('/my/models/<int:model_id>/delete', type='jsonrpc',
                auth='user', csrf=False)
    def delete_model(self, model_id, **kw):
        """Delete one of the caller's own saved models (owner only)."""
        share = self._owned_share(model_id)
        if share is None:
            return {'success': False, 'error': 'not found or not owner'}
        # Deletes the model and its exclusive child records; removing the model
        # cascades to its share row (ondelete='cascade').
        share.purge_model()
        return {'success': True}
