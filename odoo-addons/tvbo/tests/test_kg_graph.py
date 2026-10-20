# -*- coding: utf-8 -*-
"""HTTP tests for the knowledge-graph view (controllers/kg_api.py, kg_graph.py): links between records, and the public cloud on the front page."""
from odoo.tests import tagged
from odoo.tests.common import HttpCase, TransactionCase, new_test_user

from odoo.addons.tvbo.controllers import kg_graph
from odoo.addons.tvbo.controllers.kg_api import get_ontology_api


@tagged('post_install', '-at_install')
class TestKnowledgeGraph(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Dyn, Exp = cls.env['tvbo.dynamics'], cls.env['tvbo.simulation_experiment']
        cls.model = Dyn.create({'name': 'KgTestOscillator', 'references': 'KgTest2026'})
        cls.inline_copy = Dyn.create({'name': 'KgTestOscillator'})
        cls.study = cls.env['tvbo.study'].create({'citekey': 'KgTest2026'})
        cls.experiment = Exp.create({'label': 'KgTest experiment', 'record_id': 990001, 'dynamics': cls.inline_copy.id})
        cls.owner = new_test_user(cls.env, login='kg_owner', groups='base.group_portal')
        cls.draft = Exp.create({'label': 'KgTest draft', 'record_id': 990002, 'dynamics': cls.model.id})
        cls.env['tvbo.model_share'].create({'experiment_id': cls.draft.id, 'owner_user_id': cls.owner.id})
        Scale = cls.env['tvbo.simulation_scale']
        scale = Scale.search([('name', '=', 'network_system')], limit=1) or Scale.create({'name': 'network_system', 'technical_name': 'network_system'})
        cls.env['tvbo.simulation_tool'].create({'name': 'KgTestTool', 'scale': [(6, 0, scale.ids)]})

    def _json(self, path):
        self.env.flush_all()
        response = self.url_open(path, timeout=300)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_graph_links_records_and_drops_dangling_links(self):
        """An experiment's inline copy of a model is drawn as the library model and the experiment links to it, a model links to the study it cites, and every link ends at a drawn node."""
        graph = self._json('/tvbo/api/kg/graph?db_only=true')
        ids = {node['id'] for node in graph['nodes']}
        links = {(link['source'], link['target'], link['type']) for link in graph['links']}
        model = f'db_dynamics_{self.model.id}'
        self.assertNotIn(f'db_dynamics_{self.inline_copy.id}', ids)
        self.assertIn((f'db_experiment_{self.experiment.id}', model, 'dynamics'), links)
        self.assertIn((model, f'db_study_{self.study.id}', 'references'), links)
        self.assertTrue(all(link['source'] in ids and link['target'] in ids for link in graph['links']))

    def test_cloud_is_public_and_hides_drafts(self):
        """The front-page cloud is the same for every visitor, so a draft is left out even when its owner asks, its ontology points are classes rather than individuals, and every link row points at a node row."""
        self.authenticate('kg_owner', 'kg_owner')
        cloud = self._json('/tvbo/api/kg/graph/cloud')
        labels = {node[3] for node in cloud['nodes']}
        self.assertIn('KgTest experiment', labels)
        self.assertNotIn('KgTest draft', labels)
        ontology = cloud['kinds'].index('ontology')
        self.assertLessEqual(sum(node[2] == ontology for node in cloud['nodes']), len(list(get_ontology_api().onto.classes())))
        self.assertTrue(all(0 <= source < len(cloud['nodes']) and 0 <= target < len(cloud['nodes']) for source, target, _ in cloud['links']))
        tool = next(i for i, node in enumerate(cloud['nodes']) if node[3] == 'KgTestTool')
        picked = [s if t == tool else t for s, t, taxonomic in cloud['links'] if tool in (s, t) and not taxonomic]
        self.assertTrue(any(cloud['nodes'][i][2] == ontology for i in picked), "a tool's chosen scale is drawn and linked to the tool")


class TestDrawnClasses(TransactionCase):

    def test_named_classes_picked_values_and_linked_imports(self):
        """The cloud keeps TVB-O's named classes, the enum values a record picks and the outside classes linked to either, and drops unpicked values and unlinked outside classes."""
        tvbo = 'https://w3id.org/tvbo/'
        nodes = [{'storid': 'db_software_1', 'db_type': 'software'}] + [{'storid': storid, 'iri': iri} for storid, iri in (
            (1, tvbo + 'Dynamics'), (2, tvbo + 'SimulationScale#cellular'), (3, tvbo + 'SimulationScale#network'),
            (4, 'http://schema.org/ScholarlyArticle'), (5, 'http://schema.org/Book'))]
        links = [kg_graph.link('db_software_1', 3, 'scale'), kg_graph.link(4, 1, 'is_a')]
        self.assertEqual(kg_graph.drawn_classes(nodes, links, {1, 2, 3, 4, 5}, {2, 3}), {1, 3, 4})
