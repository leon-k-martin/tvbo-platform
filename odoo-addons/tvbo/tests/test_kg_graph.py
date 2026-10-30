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
        cls.model = Dyn.create({'name': 'KgTestOscillator', 'references': 'KgTest2026', 'parameters': [(0, 0, {'name': 'k', 'value': 1.0}), (0, 0, {'name': 'c', 'value': 0.0}), (0, 0, {'name': 'z', 'value': 0.0})]})
        cls.inline_copy = Dyn.create({'name': 'kgtestoscillator', 'parameters': [(0, 0, {'name': 'k', 'value': 2.0}), (0, 0, {'name': 'c', 'value': 0.5}), (0, 0, {'name': 'z', 'value': 0.0})]})
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

    def test_list_items_carry_their_links_and_back_links(self):
        """A card reads an item's links and the records linking to it from the list: an experiment names its model and what its copy changes, the library model stands for the experiment's copy, whatever its case, and names the experiment, a study the models citing it, and a draft only its owner sees is left out."""
        Integrator = self.env['tvbo.integrator']
        library = Integrator.create({'method': 'KgTestHeun', 'step_size': 0.1})
        self.experiment.integration = Integrator.create({'method': 'kgtestheun', 'step_size': 4.0})
        lonely = Integrator.create({'method': 'KgTestEuler'})
        self.env['tvbo.simulation_experiment'].create({'label': 'KgTest second', 'record_id': 990003, 'integration': lonely.id})
        items = {(item['type'], item['id']): item for item in self._json('/tvbo/api/kg/data?include_ontology=false')}
        experiment, model = items['experiment', self.experiment.id], items['dynamics', self.model.id]
        self.assertEqual(experiment['related']['dynamics'], {'count': 1, 'names': ['kgtestoscillator'], 'ids': [self.inline_copy.id], 'type': 'dynamics', 'changes': [['k', 2.0, 1.0], ['c', 0.5, 0]]}, 'a zero the library sets is a value, not a missing one')
        self.assertEqual(experiment['related']['integration']['names'], ['kgtestheun'], 'a record without a name field is named by its method')
        self.assertEqual(experiment['related']['integration']['changes'], [['step size', 4.0, 0.1]])
        self.assertNotIn(('dynamics', self.inline_copy.id), items)
        self.assertEqual((model['copies'], model['used_by']['experiment']['names']), ([self.inline_copy.id], ['KgTest experiment']), 'the draft using it is private to its owner')
        self.assertEqual(items['integrator', library.id]['copies'], [self.experiment.integration.id])
        self.assertIn(('integrator', lonely.id), items, 'a copy without a library record stays its own')
        self.assertEqual(items['study', self.study.id]['used_by']['dynamics']['names'], ['KgTestOscillator'])

    def test_study_is_named_by_citekey_and_described_by_the_bib(self):
        study = self.env['tvbo.study'].create({'citekey': 'Jansen1995'})
        item = next(item for item in self._json('/tvbo/api/kg/data?entity=study') if item['id'] == study.id)
        self.assertEqual(item['name'], 'Jansen1995')
        self.assertTrue(item['title'].startswith('Electroencephalogram and visual evoked potential'))
        self.assertEqual((item['venue'], item['kind'], item['type']), ('Biological Cybernetics', 'article', 'study'))

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

    def test_cloud_cache_watches_enum_values_and_in_between_records(self):
        """Renaming a tool's scale or re-pointing a network's parcellation changes the drawn graph, so the cloud cache watches those models too."""
        watched = kg_graph.read_models(self.env, ['tvbo.simulation_tool', 'tvbo.network'])
        self.assertLessEqual({'tvbo.simulation_tool', 'tvbo.network', 'tvbo.simulation_scale', 'tvbo.parcellation'}, watched)
        self.assertNotIn('res.users', watched, 'who last wrote a record does not change the graph')
