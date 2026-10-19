# -*- coding: utf-8 -*-
"""The configurator's sudo routes reach generated schema models only and hide other people's drafts, internal users read the curated KG without editing it, and generated fields leave Odoo's record API alone.

Run: ``odoo -u tvbo --test-enable --test-tags /tvbo --stop-after-init``
"""
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import HttpCase, new_test_user

from odoo.addons.tvbo.controllers.building_blocks_api import SCHEMA_MODELS

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

    def test_create_route_needs_kg_edit_rights(self):
        new_test_user(self.env, login='scope_portal', groups='base.group_portal')
        self.authenticate('scope_portal', 'scope_portal')
        for name in PLATFORM_CLASSES:
            result = self.make_jsonrpc_request(f'/tvbo/api/configurator/instances/{name}', {'data': {'name': 'probe'}})
            self.assertIn('No DB model', result.get('error', ''), name)
        result = self.make_jsonrpc_request('/tvbo/api/configurator/instances/Dynamics', {'data': {'name': 'portal_probe'}})
        self.assertFalse(result['success'])
        self.assertFalse(self.env['tvbo.dynamics'].search([('name', '=', 'portal_probe')]))

    def test_detail_stays_inside_the_schema(self):
        dyn = self.env['tvbo.dynamics'].create({'name': 'scope_probe'})
        response = self._get(f'/tvbo/api/configurator/instances/Dynamics/{dyn.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['name'], 'scope_probe')
        self.assertFalse({'create_uid', 'write_uid'} & data.keys())

    def test_drafts_are_hidden_from_everyone_but_their_owner(self):
        owner = new_test_user(self.env, login='scope_owner', groups='base.group_portal')
        draft = self.env['tvbo.dynamics'].create({'name': 'scope_draft'})
        self.env['tvbo.model_share'].create({'dynamics_id': draft.id, 'owner_user_id': owner.id})
        paths = (
            '/tvbo/api/configurator/instances/Dynamics?q=scope_draft',
            f'/tvbo/api/configurator/instances/Dynamics/{draft.id}',
            '/tvbo/api/configurator/dynamics',
            f'/tvbo/api/configurator/dynamics/{draft.id}',
            f'/tvbo/api/kg/dynamics/{draft.id}',
        )
        for path in paths:
            self.assertNotIn(b'scope_draft', self._get(path).content, path)
        self.authenticate('scope_owner', 'scope_owner')
        for path in paths:
            self.assertIn(b'scope_draft', self._get(path).content, path)

    def test_internal_users_read_the_kg_and_reviewers_edit_it(self):
        reader = new_test_user(self.env, login='kg_reader', groups='base.group_user')
        curator = new_test_user(self.env, login='kg_curator', groups='base.group_user,tvbo.group_tvbo_reviewer')
        self.env['tvbo.dynamics'].with_user(reader).search([], limit=1)
        with self.assertRaises(AccessError):
            self.env['tvbo.dynamics'].with_user(reader).create({'name': 'reader_probe'})
        self.env['tvbo.dynamics'].with_user(curator).create({'name': 'curator_probe'})

    def test_generated_fields_leave_the_record_api_alone(self):
        """No generated field may shadow a method or attribute of Odoo's records, as a slot named ``env`` once did."""
        record_api = type(self.env['base'])
        own_fields = set(self.env['base']._fields)
        clashes = sorted(f'{model}.{name}' for model in SCHEMA_MODELS for name in self.env[model]._fields if name not in own_fields and hasattr(record_api, name))
        self.assertEqual(clashes, [])
