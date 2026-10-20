# -*- coding: utf-8 -*-
"""The configurator's sudo routes reach generated schema models only, and internal users read the curated KG without editing it.

Run: ``odoo -u tvbo --test-enable --test-tags /tvbo --stop-after-init``
"""
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import HttpCase, new_test_user

PLATFORM_CLASSES = ('ApiKey', 'ModelShare', 'PublicationReview')


@tagged('post_install', '-at_install')
class TestSchemaScope(HttpCase):

    def _get(self, path):
        self.env.flush_all()
        return self.url_open(path, timeout=120)

    def test_public_routes_refuse_platform_models(self):
        for name in PLATFORM_CLASSES:
            for path in (f'/tvbo/api/configurator/instances/{name}', f'/tvbo/api/configurator/instances/{name}/1'):
                self.assertEqual(self._get(path).status_code, 404, path)

    def test_create_route_refuses_platform_models(self):
        new_test_user(self.env, login='scope_portal', groups='base.group_portal')
        self.authenticate('scope_portal', 'scope_portal')
        for name in PLATFORM_CLASSES:
            result = self.make_jsonrpc_request(f'/tvbo/api/configurator/instances/{name}', {'data': {'name': 'probe'}})
            self.assertIn('No DB model', result.get('error', ''), name)

    def test_detail_stays_inside_the_schema(self):
        dyn = self.env['tvbo.dynamics'].create({'name': 'scope_probe'})
        response = self._get(f'/tvbo/api/configurator/instances/Dynamics/{dyn.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['name'], 'scope_probe')
        self.assertFalse({'create_uid', 'write_uid'} & data.keys())

    def test_internal_users_read_the_kg_and_reviewers_edit_it(self):
        reader = new_test_user(self.env, login='kg_reader', groups='base.group_user')
        curator = new_test_user(self.env, login='kg_curator', groups='base.group_user,tvbo.group_tvbo_reviewer')
        self.env['tvbo.dynamics'].with_user(reader).search([], limit=1)
        with self.assertRaises(AccessError):
            self.env['tvbo.dynamics'].with_user(reader).create({'name': 'reader_probe'})
        self.env['tvbo.dynamics'].with_user(curator).create({'name': 'curator_probe'})
