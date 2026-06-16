# -*- coding: utf-8 -*-
"""HTTP tests for the authenticated REST API (controllers/api.py).

These exercise the *controller* access logic — which deliberately runs as
``auth='public'`` + manual owner/visibility filters (the schema entities carry
no ownership fields), so it is NOT covered by the ORM record-rule tests. Run:

    odoo -u tvbo --test-enable --test-tags /tvbo --stop-after-init
"""
from odoo.tests import tagged
from odoo.tests.common import HttpCase, new_test_user


@tagged('post_install', '-at_install')
class TestApiHttp(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Dyn = cls.env['tvbo.dynamics']
        cls.Exp = cls.env['tvbo.simulation_experiment']
        cls.Share = cls.env['tvbo.model_share']
        cls.alice = new_test_user(cls.env, login='api_alice', groups='base.group_portal')
        cls.bob = new_test_user(cls.env, login='api_bob', groups='base.group_portal')
        _, cls.key = cls.env['tvbo.api_key'].generate('test', cls.alice)
        cls.auth = {'Authorization': 'Bearer ' + cls.key}
        cls._seq = 0  # source of unique record_id values for created experiments

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _model(self, name, owner=None, visibility='private'):
        dyn = self.Dyn.create({'name': name})
        if owner is not None:
            self.Share.create({
                'dynamics_id': dyn.id, 'owner_user_id': owner.id, 'visibility': visibility})
        return dyn

    def _exp(self, label, owner=None, visibility='private'):
        # tvbo.simulation_experiment requires an integer record_id; use high,
        # unique values to avoid clashing with seeded experiments.
        type(self)._seq += 1
        exp = self.Exp.create({'label': label, 'record_id': 900000 + type(self)._seq})
        if owner is not None:
            self.Share.create({
                'experiment_id': exp.id, 'owner_user_id': owner.id, 'visibility': visibility})
        return exp

    # Detail/push endpoints lazily cold-load the LinkML schema on first use,
    # which can take well over the default 10s url_open timeout in a fresh
    # container; allow plenty of headroom.
    _TIMEOUT = 120

    def _get(self, path, headers=None):
        self.env.flush_all()
        return self.url_open(
            path, headers=self.auth if headers is None else headers, timeout=self._TIMEOUT)

    def _post(self, path, body, ctype='application/x-yaml', headers=None):
        self.env.flush_all()
        h = dict(self.auth if headers is None else headers)
        h['Content-Type'] = ctype
        data = body if isinstance(body, bytes) else body.encode('utf-8')
        return self.url_open(path, data=data, headers=h, timeout=self._TIMEOUT)

    # ------------------------------------------------------------------ #
    # Auth
    # ------------------------------------------------------------------ #
    def test_auth_required(self):
        self.assertEqual(self._get('/api/tvbo/v1/models', headers={}).status_code, 401)
        self.assertEqual(
            self._get('/api/tvbo/v1/models', headers={'Authorization': 'Bearer tvbo_bogus'}).status_code,
            401)
        self.assertEqual(self._get('/api/tvbo/v1/models').status_code, 200)

    # ------------------------------------------------------------------ #
    # Models
    # ------------------------------------------------------------------ #
    def test_models_list_scoping(self):
        a_priv = self._model('api_a_priv', self.alice, 'private')
        a_shared = self._model('api_a_shared', self.alice, 'shared')
        b_priv = self._model('api_b_priv', self.bob, 'private')
        b_shared = self._model('api_b_shared', self.bob, 'shared')
        ids = {m['id'] for m in self._get('/api/tvbo/v1/models').json()['data']}
        self.assertIn(a_priv.id, ids, 'own private listed')
        self.assertIn(a_shared.id, ids, 'own shared listed')
        self.assertIn(b_shared.id, ids, "others' shared listed")
        self.assertNotIn(b_priv.id, ids, "others' private hidden")

    def test_model_detail_access(self):
        own = self._model('api_detail_own', self.alice, 'private')
        shared = self._model('api_detail_shared', self.bob, 'shared')
        hidden = self._model('api_detail_hidden', self.bob, 'private')
        public = self._model('api_detail_public')  # no share -> ground-truth/public
        self.assertEqual(self._get('/api/tvbo/v1/models/%d' % own.id).status_code, 200)
        self.assertEqual(self._get('/api/tvbo/v1/models/%d' % shared.id).status_code, 200)
        self.assertEqual(self._get('/api/tvbo/v1/models/%d' % hidden.id).status_code, 404,
                         "others' private -> 404")
        self.assertEqual(self._get('/api/tvbo/v1/models/%d' % public.id).status_code, 200)
        self.assertEqual(self._get('/api/tvbo/v1/models/99999999').status_code, 404,
                         'missing -> 404 (not 422)')

    def test_model_push_creates_and_replaces(self):
        r1 = self._post('/api/tvbo/v1/models', 'name: ApiPush\nlabel: One\ndescription: d\n')
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r1.json()['visibility'], 'private')
        mine = [m for m in self._get('/api/tvbo/v1/models').json()['data'] if m['name'] == 'ApiPush']
        self.assertEqual(len(mine), 1)
        self.assertTrue(mine[0]['mine'])
        # Re-push under the same name -> replace in place, not duplicate.
        r2 = self._post('/api/tvbo/v1/models', 'name: ApiPush\nlabel: Two\ndescription: d\n')
        self.assertEqual(r2.status_code, 201)
        self.assertNotEqual(r2.json()['id'], r1.json()['id'])
        again = [m for m in self._get('/api/tvbo/v1/models').json()['data'] if m['name'] == 'ApiPush']
        self.assertEqual(len(again), 1, 'replace-on-name: still exactly one')
        self.assertEqual(again[0]['label'], 'Two', 'updated in place')

    def test_push_visibility_query_param(self):
        r = self._post('/api/tvbo/v1/models?visibility=shared', 'name: ApiSharedViaQuery\nlabel: S\n')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()['visibility'], 'shared',
                         '?visibility= honored for YAML push')

    def test_push_invalid_returns_422(self):
        r = self._post('/api/tvbo/v1/models', '- not\n- a mapping\n')
        self.assertEqual(r.status_code, 422)

    # ------------------------------------------------------------------ #
    # Experiments
    # ------------------------------------------------------------------ #
    def test_experiments_list_excludes_others_private(self):
        a_exp = self._exp('api_exp_alice', self.alice, 'private')
        b_exp = self._exp('api_exp_bob', self.bob, 'private')
        pub_exp = self._exp('api_exp_public')  # no share -> public
        ids = {e['id'] for e in self._get('/api/tvbo/v1/experiments').json()['data']}
        self.assertIn(a_exp.id, ids, 'own private experiment listed')
        self.assertIn(pub_exp.id, ids, 'public experiment listed')
        self.assertNotIn(b_exp.id, ids, "others' private experiment hidden")
