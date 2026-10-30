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

from odoo.tests import tagged
from odoo.tests.common import HttpCase, TransactionCase

from odoo.addons.tvbo.models import bibliography, ingest
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


class TestBibliography(TransactionCase):
    """A study's details as the bib that ships with tvbo gives them."""

    def test_details_are_plain_text_without_abstract_or_file(self):
        jansen = bibliography.study('Jansen1993')
        self.assertEqual((jansen['venue'], jansen['type']), ('Biological Cybernetics', 'article'))
        self.assertEqual(bibliography.study('Montbrio2015')['authors'], 'Montbrió, Ernest\nPazó, Diego\nRoxin, Alex')
        self.assertNotIn('abstract', jansen, 'publishers hold the copyright on abstracts')
        self.assertNotIn('file', bibliography.study('Cabral2011'), 'a local path from a reference manager')

    def test_unknown_citekey_has_no_details(self):
        self.assertEqual(bibliography.study('NoSuchStudy2099'), {})
        self.assertEqual(bibliography.study(None), {})


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

    def test_reseed_writes_studies_from_the_bib(self):
        """A curated study takes the bib's values, so a corrected bib reaches it; a study someone saved keeps its own and only fills the empty ones."""
        study = self.env['tvbo.study'].search([('citekey', '=', 'Jansen1995')], limit=1)
        study.write({'title': False, 'authors': False, 'year': 1990, 'type': False})
        saved = self.env['tvbo.study'].create({'citekey': 'Jansen1993', 'year': 1990})
        self.env['tvbo.model_share'].create({'study_id': saved.id, 'owner_user_id': self.env.user.id})
        ingest.seed_database(self.env)
        self.assertEqual((study.year, study.authors, study.type), (1995, 'Jansen, Ben H.\nRit, Vincent G.', 'article'))
        self.assertTrue(study.title.startswith('Electroencephalogram and visual evoked potential'))
        self.assertEqual((saved.year, saved.type), (1990, 'article'))

    def test_reseed_refills_emptied_exploration_axis_parameters(self):
        experiment = self.env.ref(f"{ingest._INGEST_MODULE}.{_xmlid('SimulationExperiment', 'RWW_BOLD_FC_Optimization')}")
        axes = experiment.explorations.space.sorted('id')
        expected = axes.mapped('parameter')
        self.assertEqual(expected, ['ReducedWongWang.w', 'FastLinearCoupling.G'])
        # The schema reconcile left the column nullable and empty; the ORM itself would refuse to empty a required field.
        self.env.cr.execute("ALTER TABLE tvbo_exploration_axis ALTER COLUMN parameter DROP NOT NULL")
        self.env.cr.execute("UPDATE tvbo_exploration_axis SET parameter = NULL WHERE id IN %s", [tuple(axes.ids)])
        axes.invalidate_recordset(['parameter'])
        ingest.seed_database(self.env)
        self.assertEqual(axes.mapped('parameter'), expected)


@tagged('post_install', '-at_install')
class TestJsonResponseDates(HttpCase):
    """SimulationTool.date_created must not 500 the KG endpoints."""

    def test_date_serializes(self):
        tool = self.env['tvbo.simulation_tool'].create({'name': 'date_probe', 'date_created': date(2020, 1, 2)})
        self.env.flush_all()
        resp = self.url_open(f'/tvbo/api/kg/software/{tool.id}', timeout=120)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'2020-01-02', resp.content)
