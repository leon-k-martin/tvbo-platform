# -*- coding: utf-8 -*-
"""Model-level tests for personal API keys (no HTTP stack needed).

    odoo -u tvbo --test-enable --test-tags /tvbo --stop-after-init
"""
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, new_test_user

from odoo.addons.tvbo.models.api_key import KEY_PREFIX, MAX_KEYS_PER_USER


class TestApiKey(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Key = cls.env['tvbo.api_key']
        cls.alice = new_test_user(cls.env, login='apikey_alice', groups='base.group_portal')

    def test_generate_returns_raw_and_stores_only_hash(self):
        rec, raw = self.Key.generate('laptop', self.alice)
        self.assertTrue(raw.startswith(KEY_PREFIX))
        self.assertNotEqual(rec.key_hash, raw, 'raw token must not be stored')
        self.assertEqual(rec.key_hash, self.Key._hash(raw))
        self.assertEqual(rec.key_prefix, raw[:12])
        self.assertEqual(rec.user_id, self.alice)

    def test_verify_matches_and_rejects_wrong(self):
        _, raw = self.Key.generate('k', self.alice)
        self.assertEqual(self.Key.verify(raw), self.alice)
        self.assertFalse(self.Key.verify('tvbo_wrong'))
        self.assertFalse(self.Key.verify(''))

    def test_verify_rejects_inactive(self):
        rec, raw = self.Key.generate('k', self.alice)
        rec.active = False
        self.assertFalse(self.Key.verify(raw))

    def test_verify_rejects_expired_accepts_unexpired(self):
        now = fields.Datetime.now()
        _, past = self.Key.generate('expired', self.alice, expires=now - timedelta(days=1))
        _, future = self.Key.generate('valid', self.alice, expires=now + timedelta(days=1))
        self.assertFalse(self.Key.verify(past), 'expired key rejected')
        self.assertEqual(self.Key.verify(future), self.alice, 'unexpired key accepted')

    def test_last_used_is_throttled(self):
        rec, raw = self.Key.generate('throttle', self.alice)
        self.Key.verify(raw)
        first = rec.last_used
        self.assertTrue(first, 'last_used set on first use')
        self.Key.verify(raw)
        self.assertEqual(rec.last_used, first, 'within window: not rewritten')
        stale = fields.Datetime.now() - timedelta(hours=2)
        rec.last_used = stale
        self.Key.verify(raw)
        self.assertGreater(rec.last_used, stale, 'past window: refreshed')

    def test_key_cap_enforced(self):
        capuser = new_test_user(self.env, login='apikey_cap', groups='base.group_portal')
        for i in range(MAX_KEYS_PER_USER):
            self.Key.generate('k%d' % i, capuser)
        with self.assertRaises(ValidationError):
            self.Key.generate('over the cap', capuser)

    def test_revoked_key_frees_a_cap_slot(self):
        capuser = new_test_user(self.env, login='apikey_cap2', groups='base.group_portal')
        keys = [self.Key.generate('k%d' % i, capuser)[0] for i in range(MAX_KEYS_PER_USER)]
        keys[0].active = False  # inactive keys don't count toward the cap
        # Now under the cap again -> generate succeeds.
        rec, _ = self.Key.generate('replacement', capuser)
        self.assertTrue(rec.id)
