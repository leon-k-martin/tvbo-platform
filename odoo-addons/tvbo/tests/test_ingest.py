# -*- coding: utf-8 -*-
"""Regression tests for the KG ground-truth ingestion (models/ingest.py).

Each test pins a specific bug fixed while making the KG complete, so it cannot
silently come back:

  • non-finite floats (Infinity) must not break Postgres json columns
  • the seed is idempotent (external-id markers) and never duplicates
  • a non-unique natural key (two experiments with id=1) must not collapse rows
  • a dangling marker (row gone) self-heals instead of becoming a permanent gap
  • registry categories must all be ingested (the software outage)
  • date/datetime must serialize over the API (SimulationTool.date_created)

    odoo -u tvbo --test-enable --test-tags /tvbo --stop-after-init
"""
import math
from datetime import date

from odoo.tests.common import TransactionCase

from odoo.addons.tvbo.models import ingest
from odoo.addons.tvbo.models.ingest import _json_safe, _xmlid


class TestJsonSafe(TransactionCase):
    """Pure-function guard for the Infinity-in-json fix."""

    def test_non_finite_floats_become_string_tokens(self):
        self.assertEqual(_json_safe(float('inf')), 'Infinity')
        self.assertEqual(_json_safe(float('-inf')), '-Infinity')
        self.assertEqual(_json_safe(float('nan')), 'NaN')

    def test_finite_and_non_floats_unchanged(self):
        self.assertEqual(_json_safe(1.5), 1.5)
        self.assertEqual(_json_safe(3), 3)
        self.assertEqual(_json_safe('x'), 'x')
        self.assertIsNone(_json_safe(None))

    def test_recurses_into_dicts_and_lists(self):
        out = _json_safe({'a': float('inf'), 'b': [1.0, float('-inf')], 'c': {'d': float('nan')}})
        self.assertEqual(out, {'a': 'Infinity', 'b': [1.0, '-Infinity'], 'c': {'d': 'NaN'}})

    def test_xmlid_is_deterministic_and_sanitized(self):
        self.assertEqual(_xmlid('Dynamics', 'KIonEx'), 'dynamics_kionex')
        self.assertEqual(_xmlid('SimulationTool', 'AUTO-07p'), 'simulationtool_auto_07p')
        # category-prefixed, so same entry name in two categories never collides
        self.assertNotEqual(_xmlid('Study', 'X'), _xmlid('Network', 'X'))


class TestCreateRecordResilience(TransactionCase):
    """Infinity reaches a real json column without aborting the insert."""

    def test_infinity_in_json_field_is_stored_not_fatal(self):
        # tvbo.range.hi/lo are fields.Json; raw float('inf') makes Postgres reject
        # the insert ('Token "Infinity" is invalid') and cascade. _json_safe must
        # turn it into a token so the record is created.
        rid = ingest._create_record(
            self.env, 'tvbo.range', {'hi': float('inf'), 'lo': float('-inf')}, {})
        self.assertTrue(rid, 'record with an infinite bound must still be created')
        rec = self.env['tvbo.range'].browse(rid)
        self.assertEqual(rec.hi, 'Infinity')
        self.assertEqual(rec.lo, '-Infinity')


class TestRegistryCoverage(TransactionCase):
    """Every registry category must be ingested — the software-bug guard."""

    def test_all_categories_covered(self):
        self.assertEqual(ingest.registry_coverage(), [],
                         'a registry category nothing ingests would be invisible in the KG')

    def test_dropping_a_category_is_flagged(self):
        original = ingest._INGEST
        try:
            ingest._INGEST = [p for p in original if p[1] != 'SimulationTool']
            uncovered = ingest.registry_coverage()
            self.assertTrue(any(u['category'] == 'SimulationTool' for u in uncovered),
                            'removing SimulationTool from _INGEST must be flagged')
        finally:
            ingest._INGEST = original


class TestKgCompleteness(TransactionCase):
    """The verdict the deploy banner, /kg/health and CI all rely on."""

    def test_verdict_and_shape(self):
        comp = ingest.kg_completeness(self.env)
        self.assertIn(comp['verdict'], ('KG_OK', 'KG_DEGRADED', 'KG_EMPTY', 'KG_UNKNOWN'))
        cats = comp['categories']
        for _, category in ingest._INGEST:
            self.assertIn(category, cats)
            self.assertIn('expected', cats[category])
            self.assertIn('actual', cats[category])

    def test_no_natural_key_collision(self):
        # Each ground-truth entry owns exactly one external id pointing at one row;
        # markers collapsing onto a shared row is the id=1 bug (record_id not unique).
        IMD = self.env['ir.model.data'].sudo()
        for pyd_cls, _ in ingest._INGEST:
            model = 'tvbo.' + ingest._camel_to_snake(pyd_cls)
            res_ids = IMD.search([
                ('module', '=', ingest._INGEST_MODULE), ('model', '=', model)]).mapped('res_id')
            self.assertEqual(len(res_ids), len(set(res_ids)),
                             '%s: two markers collapsed onto one row' % model)


class TestSeedIdempotency(TransactionCase):
    """Re-seeding every deploy must be a safe no-op, and self-heal gaps."""

    def test_reseed_creates_no_new_markers(self):
        IMD = self.env['ir.model.data'].sudo()
        dom = [('module', '=', ingest._INGEST_MODULE)]
        before = IMD.search_count(dom)
        ingest.seed_database(self.env)
        self.assertEqual(IMD.search_count(dom), before,
                         'an idempotent reseed must not create new markers')

    def test_dangling_marker_self_heals(self):
        IMD = self.env['ir.model.data'].sudo()
        marker = IMD.search([
            ('module', '=', ingest._INGEST_MODULE), ('model', '=', 'tvbo.dynamics')], limit=1)
        self.assertTrue(marker, 'expected seeded dynamics markers')
        name = marker.name
        # Dangle it: point the marker at a non-existent row (simulates a row removed
        # by an FK cascade that bypassed Odoo's ir.model.data cleanup).
        marker.write({'res_id': 999999999})
        ingest.seed_database(self.env)
        healed = IMD.search([('module', '=', ingest._INGEST_MODULE), ('name', '=', name)], limit=1)
        self.assertTrue(healed, 'dangling marker must be re-established, not left broken')
        self.assertTrue(self.env['tvbo.dynamics'].browse(healed.res_id).exists(),
                        'self-healed marker must point at a real row')


class TestJsonResponseDates(TransactionCase):
    """SimulationTool.date_created must not 500 the KG endpoints."""

    def test_date_serializes(self):
        from odoo.addons.tvbo.controllers.kg_api import json_response
        resp = json_response({'d': date(2020, 1, 2)})
        self.assertIn(b'2020-01-02', resp.data)
