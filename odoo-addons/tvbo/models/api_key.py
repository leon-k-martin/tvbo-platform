# -*- coding: utf-8 -*-
"""Personal API keys for the TVBO platform REST API.

Users mint keys from the portal (/my/api-keys) and use them as a bearer token to
read and push their saved/shared models and experiments from Python. Keys are
stored hashed (SHA-256) — the raw token is shown exactly once, at creation.
"""
import hashlib
import secrets
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

KEY_PREFIX = 'tvbo_'
# Cap keys per user so a runaway script (or abuse) can't mint unbounded rows.
MAX_KEYS_PER_USER = 25
# Rewriting last_used on every call would turn every authenticated read into a
# write; once per window is enough to show "recently used".
_LAST_USED_THROTTLE = timedelta(hours=1)


class TvboApiKey(models.Model):
    _name = 'tvbo.api_key'
    _description = 'Personal API key for the TVBO platform REST API'
    _order = 'create_date desc'

    name = fields.Char(required=True, help='Human-friendly label, e.g. "laptop".')
    user_id = fields.Many2one(
        'res.users', string='User', required=True, ondelete='cascade', index=True,
        default=lambda self: self.env.user,
    )
    # Only system may read the hash over the ORM; portal users never see it.
    key_hash = fields.Char(required=True, index=True, groups='base.group_system')
    key_prefix = fields.Char(help='First characters of the key, shown so users can tell keys apart.')
    last_used = fields.Datetime(readonly=True)
    expires = fields.Datetime(
        help='Optional expiry. After this moment the key is rejected. Empty = never expires.')
    active = fields.Boolean(default=True)

    @api.model
    def _hash(self, raw):
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    @api.model
    def generate(self, name, user=None, expires=False):
        """Create a key for ``user`` and return ``(record, raw_token)``.

        The raw token is returned only here — it is never recoverable later.
        Raises ``ValidationError`` if the user is already at the key cap.
        """
        user = user or self.env.user
        if self.sudo().search_count(
                [('user_id', '=', user.id), ('active', '=', True)]) >= MAX_KEYS_PER_USER:
            raise ValidationError(
                'You already have %d active API keys. Revoke one before creating another.'
                % MAX_KEYS_PER_USER)
        raw = KEY_PREFIX + secrets.token_urlsafe(32)
        record = self.sudo().create({
            'name': name or 'API key',
            'user_id': user.id,
            'key_hash': self._hash(raw),
            'key_prefix': raw[:12],
            'expires': expires or False,
        })
        return record, raw

    @api.model
    def verify(self, raw):
        """Return the ``res.users`` owning an active, unexpired key matching ``raw``
        (empty recordset if none)."""
        empty = self.env['res.users']
        if not raw:
            return empty
        now = fields.Datetime.now()
        record = self.sudo().search([
            ('key_hash', '=', self._hash(raw)),
            ('active', '=', True),
            '|', ('expires', '=', False), ('expires', '>', now),
        ], limit=1)
        if not record:
            return empty
        # Throttle the write so authenticated reads stay (mostly) read-only.
        if not record.last_used or now - record.last_used >= _LAST_USED_THROTTLE:
            record.last_used = now
        return record.user_id
