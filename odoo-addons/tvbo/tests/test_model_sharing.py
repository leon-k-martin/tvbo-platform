# -*- coding: utf-8 -*-
"""Backend tests for platform-only model ownership & sharing.

These run against the ORM (no live HTTP stack needed):

    odoo -u tvbo --test-enable --test-tags /tvbo --stop-after-init
"""
import psycopg2

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user
from odoo.tools import mute_logger


class TestModelSharing(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Dyn = cls.env['tvbo.dynamics']
        cls.Share = cls.env['tvbo.model_share']
        cls.alice = new_test_user(cls.env, login='tvbo_alice', groups='base.group_portal')
        cls.bob = new_test_user(cls.env, login='tvbo_bob', groups='base.group_portal')

    def _make_model(self, name, owner, visibility='private'):
        dyn = self.Dyn.create({'name': name})
        share = self.Share.create({
            'dynamics_id': dyn.id,
            'owner_user_id': owner.id,
            'visibility': visibility,
        })
        return dyn, share

    def test_default_visibility_is_private(self):
        dyn = self.Dyn.create({'name': 'share_default'})
        share = self.Share.create({'dynamics_id': dyn.id, 'owner_user_id': self.alice.id})
        self.assertEqual(share.visibility, 'private')

    def test_one_share_per_model(self):
        dyn, _ = self._make_model('share_unique', self.alice)
        with self.assertRaises(psycopg2.IntegrityError), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self.Share.create({'dynamics_id': dyn.id, 'owner_user_id': self.bob.id})
                self.env.flush_all()

    def test_delete_model_cascades_share(self):
        dyn, share = self._make_model('share_cascade', self.alice)
        dyn.unlink()
        self.assertFalse(share.exists())

    def test_purge_removes_exclusive_children(self):
        rng = self.env['tvbo.range'].create({'lo': 0.0, 'hi': 1.0})
        param = self.env['tvbo.parameter'].create({'name': 'a', 'value': 1.0, 'domain': rng.id})
        dyn = self.Dyn.create({'name': 'share_purge', 'parameters': [(6, 0, param.ids)]})
        _, share = (dyn, self.Share.create({'dynamics_id': dyn.id, 'owner_user_id': self.alice.id}))

        share.purge_model()

        self.assertFalse(dyn.exists(), 'model deleted')
        self.assertFalse(share.exists(), 'share cascaded')
        self.assertFalse(param.exists(), 'exclusive parameter removed')
        self.assertFalse(rng.exists(), 'nested range removed')

    def test_record_rule_read_own_and_shared(self):
        _, a_priv = self._make_model('rr_a_priv', self.alice, 'private')
        _, a_shared = self._make_model('rr_a_shared', self.alice, 'shared')
        _, b_priv = self._make_model('rr_b_priv', self.bob, 'private')
        _, b_shared = self._make_model('rr_b_shared', self.bob, 'shared')

        visible = self.Share.with_user(self.alice).search([])
        self.assertIn(a_priv, visible, "own private visible")
        self.assertIn(a_shared, visible, "own shared visible")
        self.assertIn(b_shared, visible, "others' shared visible")
        self.assertNotIn(b_priv, visible, "others' private hidden")

    def test_record_rule_modify_own_only(self):
        _, b_shared = self._make_model('rr_write_shared', self.bob, 'shared')
        # Alice can read Bob's shared row but must not be able to change it.
        with self.assertRaises(AccessError):
            b_shared.with_user(self.alice).write({'visibility': 'private'})
