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
from datetime import timedelta

from odoo import fields, http
from odoo.exceptions import ValidationError
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
            [('owner_user_id', '=', request.env.user.id), ('dynamics_id', '!=', False)],
            order='write_date desc')
        return request.render('tvbo.portal_my_models', {
            'shares': shares,
            'page_name': 'my_models',
        })

    @http.route('/tvbo/models/shared', type='http', auth='public', website=True)
    def shared_models(self, **kw):
        """Community gallery: models that have been *published* (own ones badged)."""
        if request.env.user._is_public():
            return request.redirect('/web/login?redirect=/tvbo/models/shared')
        shares = self._shares().search(
            [('publication_state', '=', 'published'), ('dynamics_id', '!=', False)],
            order='published_date desc, write_date desc')
        return request.render('tvbo.portal_shared_models', {
            'shares': shares,
            'current_uid': request.env.user.id,
            'page_name': 'shared_models',
        })

    @http.route('/my/shared', type='http', auth='public', website=True)
    def shared_with_me(self, **kw):
        """Elements other users have peer-to-peer shared directly with me."""
        if request.env.user._is_public():
            return request.redirect('/web/login?redirect=/my/shared')
        shares = self._shares().search(
            [('shared_user_ids', 'in', request.env.user.id),
             ('dynamics_id', '!=', False)],
            order='write_date desc')
        return request.render('tvbo.portal_shared_with_me', {
            'shares': shares,
            'page_name': 'shared_with_me',
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

    @http.route('/my/models/<int:model_id>/submit', type='jsonrpc',
                auth='user', csrf=False)
    def submit_for_review(self, model_id, **kw):
        """Publish request: run automated validation, then queue for peer review.

        Returns the validation report so the UI can show actionable issues if it
        did not pass. This does NOT make the model public — a reviewer does.
        """
        share = self._owned_share(model_id)
        if share is None:
            return {'success': False, 'error': 'not found or not owner'}
        result = share.submit_for_review()
        return {
            'success': result.get('success', False),
            'state': result.get('state'),
            'message': result.get('message'),
            'report': result.get('report'),
        }

    @http.route('/my/models/<int:model_id>/withdraw', type='jsonrpc',
                auth='user', csrf=False)
    def withdraw(self, model_id, **kw):
        """Pull a submission or a published model back to a private draft (owner)."""
        share = self._owned_share(model_id)
        if share is None:
            return {'success': False, 'error': 'not found or not owner'}
        share.withdraw()
        return {'success': True, 'state': share.publication_state}

    @http.route('/my/models/<int:model_id>/share', type='jsonrpc',
                auth='user', csrf=False)
    def share_with(self, model_id, login=None, **kw):
        """Peer-to-peer share this model with one person by login/email (owner)."""
        share = self._owned_share(model_id)
        if share is None:
            return {'success': False, 'error': 'not found or not owner'}
        target = share._resolve_user(login)
        if not target:
            return {'success': False, 'error': 'no user with that login or email'}
        if target.id == request.env.user.id:
            return {'success': False, 'error': 'you already own this model'}
        share.share_with_users(target)
        return {'success': True, 'user': target.name,
                'count': share.shared_user_count}

    @http.route('/my/models/<int:model_id>/unshare', type='jsonrpc',
                auth='user', csrf=False)
    def unshare(self, model_id, user_id=None, **kw):
        """Revoke a collaborator's peer-to-peer access (owner)."""
        share = self._owned_share(model_id)
        if share is None:
            return {'success': False, 'error': 'not found or not owner'}
        user = request.env['res.users'].sudo().browse(int(user_id)) if user_id else None
        if not user or not user.exists():
            return {'success': False, 'error': 'unknown user'}
        share.unshare_user(user)
        return {'success': True, 'count': share.shared_user_count}

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

    # ------------------------------------------------------------------ #
    # API keys (self-service) — for the Python REST client
    # ------------------------------------------------------------------ #
    @http.route('/my/api-keys', type='http', auth='public', website=True)
    def api_keys(self, **kw):
        """Manage personal API keys used by the tvbo Python client."""
        if request.env.user._is_public():
            return request.redirect('/web/login?redirect=/my/api-keys')
        keys = request.env['tvbo.api_key'].sudo().search(
            [('user_id', '=', request.env.user.id)], order='create_date desc')
        return request.render('tvbo.portal_api_keys', {
            'keys': keys,
            'page_name': 'api_keys',
        })

    @http.route('/my/api-keys/create', type='jsonrpc', auth='user', csrf=False)
    def api_key_create(self, name=None, expires_days=None, **kw):
        """Mint a key for the caller; returns the raw token once.

        ``expires_days`` (optional, int) sets an expiry that many days out; 0 or
        empty means the key never expires.
        """
        try:
            days = int(expires_days) if expires_days else 0
        except (TypeError, ValueError):
            days = 0
        expires = fields.Datetime.now() + timedelta(days=days) if days > 0 else False
        try:
            record, raw = request.env['tvbo.api_key'].sudo().generate(
                name, user=request.env.user, expires=expires)
        except ValidationError as exc:
            return {'success': False, 'error': exc.args[0] if exc.args else str(exc)}
        return {'success': True, 'id': record.id, 'name': record.name, 'key': raw}

    @http.route('/my/api-keys/<int:key_id>/revoke', type='jsonrpc', auth='user', csrf=False)
    def api_key_revoke(self, key_id, **kw):
        """Revoke (delete) one of the caller's own keys."""
        key = request.env['tvbo.api_key'].sudo().browse(key_id)
        if not key.exists() or key.user_id.id != request.env.user.id:
            return {'success': False, 'error': 'not found or not owner'}
        key.unlink()
        return {'success': True}
