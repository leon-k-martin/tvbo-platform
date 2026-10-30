# -*- coding: utf-8 -*-
"""Links and layout of the knowledge graph: relations between ontology entities and between database records, link cleanup, and the force layout behind the front-page cloud."""
from collections import defaultdict

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from odoo.models import LOG_ACCESS_COLUMNS

TAXONOMY = frozenset({'is_a', 'instance_of'})
TVBO = 'https://w3id.org/tvbo/'
PERMISSIBLE_VALUES = 'SELECT ?enum ?value ?label WHERE { ?enum <https://w3id.org/linkml/permissible_values> ?value . OPTIONAL { ?value <http://www.w3.org/2000/01/rdf-schema#label> ?label } }'


def link(source, target, kind):
    return {'source': source, 'target': target, 'type': kind, 'label': kind.replace('_', ' ')}


def ontology_links(api, nodes):
    """Object-property links between the drawn ontology entities, and each sub-entity's link from its owner, read from IRIs of the form ``<owner>/<slot>/<name>`` (a model's parameters, state variables and derived variables)."""
    drawn = {node['storid'] for node in nodes}
    links = [
        link(subject.storid, value.storid, prop.name)
        for prop in api.world.object_properties()
        for subject, value in prop.get_relations()
        if subject.storid in drawn and getattr(value, 'storid', None) in drawn
    ]
    by_iri = {node['iri']: node['storid'] for node in nodes if node.get('iri')}
    for node in nodes:
        owner, _sep, slot = (node.get('iri') or '').rpartition('/')[0].rpartition('/')
        if owner in by_iri:
            links.append(link(by_iri[owner], node['storid'], slot))
    return links


def relation_paths(env, model, kinds):
    """Field paths from ``model`` to knowledge-graph models: its relational fields to one, and its many2one fields to another model followed by that model's many2one fields to one (a network's parcellation to its atlas)."""
    for fname, field in model._fields.items():
        if not field.relational or fname in LOG_ACCESS_COLUMNS:
            continue
        if field.comodel_name in kinds:
            yield fname, kinds[field.comodel_name]
        elif field.type == 'many2one':
            for sub, subfield in env[field.comodel_name]._fields.items():
                if subfield.type == 'many2one' and subfield.comodel_name in kinds:
                    yield f'{fname}.{sub}', kinds[subfield.comodel_name]


def read_models(env, kg_models):
    """The models the graph reads records from: ``kg_models`` and every model one relation away from them, which holds the enum values records pick and the in-between records of two-step relations (a network's parcellation)."""
    return set(kg_models) | {field.comodel_name for name in kg_models for fname, field in env[name]._fields.items() if field.relational and fname not in LOG_ACCESS_COLUMNS}


def enum_values(api):
    """Every enum value of the ontology as ``{(enum class name, value name): storid}``; a value goes by its IRI name and by its label, because one with an outside IRI (Wikidata, QUDT) is named only by its label."""
    values = {}
    for enum, value, label in api.world.sparql(PERMISSIBLE_VALUES):
        for name in {value.name, label} - {None}:
            values[(enum.name, name)] = value.storid
    return values


def cites(model):
    """Whether *model*'s records list the study citekeys they cite in a ``references`` text field."""
    field = model._fields.get('references')
    return bool(field) and field.type in ('char', 'text')


def cited(record):
    """The study citekeys *record* lists in its ``references``, for a model that ``cites``."""
    return (record.references or '').split()


def record_links(env, kinds, record_node, values):
    """Links from drawn records: their relations (see ``relation_paths``), the study citekeys a record lists in ``references``, and each enum value a record picks (a tool's scales, roles and languages), matched through ``values`` from ``enum_values``.

    ``kinds`` maps each knowledge-graph model to its entity type and ``record_node`` maps (entity type, record id) to the node that draws the record; relations to records without a node are skipped.
    """
    ids = defaultdict(list)
    for kind, rec_id in record_node:
        ids[kind].append(rec_id)
    studies = env['tvbo.study'].sudo().browse(ids['study'])
    citekeys = {study.citekey: record_node[('study', study.id)] for study in studies if study.citekey}
    enums = {enum for enum, _ in values}
    links = []
    for model_name, kind in kinds.items():
        model = env[model_name].sudo()
        records = model.browse(ids[kind])
        for path, target_kind in relation_paths(env, model, kinds):
            for rec in records:
                for target in rec.mapped(path):
                    target_node = record_node.get((target_kind, target.id))
                    if target_node:
                        links.append(link(record_node[(kind, rec.id)], target_node, path.rpartition('.')[2]))
        for fname, field in model._fields.items():
            enum = field.relational and env[field.comodel_name]._description
            if enum in enums:
                for rec in records:
                    for choice in rec[fname]:
                        if (enum, choice.name) in values:
                            links.append(link(record_node[(kind, rec.id)], values[(enum, choice.name)], fname))
        if cites(model):
            for rec in records:
                for key in cited(rec):
                    if key in citekeys:
                        links.append(link(record_node[(kind, rec.id)], citekeys[key], 'references'))
    return links


def drawn_classes(nodes, links, classes, values):
    """Storids of the ontology classes the front-page cloud draws: TVB-O's own named classes, each enum value in ``values`` that a record picks, and each class from another vocabulary that links to one of those or to a record."""
    records = {node['storid'] for node in nodes if 'db_type' in node}
    terms = classes - values
    own = {node['storid'] for node in nodes if node['storid'] in terms and node.get('iri', '').startswith(TVBO)}
    picked = {item['target'] for item in links if item['source'] in records and item['target'] in values}
    imported = terms - own
    core = records | own | picked
    linked = {a for item in links for a, b in ((item['source'], item['target']), (item['target'], item['source'])) if a in imported and b in core}
    return own | picked | linked


def clean_links(links, moved, drawn):
    """``links`` re-pointed from merged nodes to the node they ``moved`` to, without duplicates, self-links or links to nodes that are not ``drawn``."""
    seen, kept = set(), []
    for item in links:
        source, target = moved.get(item['source'], item['source']), moved.get(item['target'], item['target'])
        key = (source, target, item['type'])
        if source != target and source in drawn and target in drawn and key not in seen:
            seen.add(key)
            kept.append({**item, 'source': source, 'target': target})
    return kept


def force_layout(count, edges, groups, iterations=300, link_distance=30.0, charge=-30.0, charge_range=60.0, gravity=0.08, decay=0.4, cohesion=0.2, collide=4.0, hub=0.25):
    """Positions (``count`` × 2, centred on 0) for one connected part, nodes joined by ``edges`` (pairs of node indices), from a d3-force style simulation.

    Springs pull linked nodes together, more weakly at well-connected nodes; nodes closer than ``charge_range`` repel, well-connected ones harder, so hubs spread their neighbours; each node is pulled toward the centre of its group in ``groups`` (one label per node), so groups form regions that the links arrange; nodes keep at least ``collide`` apart, more around well-connected ones; and a pull to the centre holds the part together. The start is a seeded random disc, so the same graph in the same node order always gets the same layout.
    """
    edges = np.asarray(edges, dtype=int).reshape(-1, 2)
    rng = np.random.default_rng(0)
    radius, angle = 10 * np.sqrt(count * rng.random(count)), 2 * np.pi * rng.random(count)
    pos = np.stack([radius * np.cos(angle), radius * np.sin(angle)], 1)
    if not len(edges):
        return np.zeros((count, 2))
    vel = np.zeros_like(pos)
    src, dst = edges[:, 0], edges[:, 1]
    degree = np.bincount(edges.ravel(), minlength=count).astype(float)
    strength = 1 / np.minimum(degree[src], degree[dst])
    bias = degree[src] / (degree[src] + degree[dst])
    weight = 1 + 0.35 * np.sqrt(degree)
    group = np.unique(np.asarray(groups), return_inverse=True)[1]
    group_size = np.bincount(group).astype(float)[:, None]
    reach = collide * (1 + hub * np.sqrt(degree))
    alpha, alpha_decay = 1.0, 1 - 0.001 ** (1 / iterations)
    for _ in range(iterations):
        alpha -= alpha * alpha_decay
        delta = pos[dst] + vel[dst] - pos[src] - vel[src]
        length = np.linalg.norm(delta, axis=1) + 1e-6
        pull = delta * ((length - link_distance) / length * alpha * strength)[:, None]
        np.add.at(vel, dst, -pull * bias[:, None])
        np.add.at(vel, src, pull * (1 - bias)[:, None])
        pairs = cKDTree(pos).query_pairs(charge_range, output_type='ndarray')
        near = pos[pairs[:, 1]] - pos[pairs[:, 0]]
        push = near * (charge * alpha * weight[pairs[:, 0]] * weight[pairs[:, 1]] / np.maximum((near * near).sum(1), 1.0))[:, None]
        np.add.at(vel, pairs[:, 0], push)
        np.add.at(vel, pairs[:, 1], -push)
        centre = np.stack([np.bincount(group, pos[:, 0]), np.bincount(group, pos[:, 1])], 1) / group_size
        vel += (centre[group] - pos) * cohesion * alpha
        vel -= (pos - pos.mean(0)) * gravity * alpha
        vel *= 1 - decay
        ahead = pos + vel
        pairs = cKDTree(ahead).query_pairs(2 * reach.max(), output_type='ndarray')
        gap = ahead[pairs[:, 1]] - ahead[pairs[:, 0]]
        dist = np.linalg.norm(gap, axis=1) + 1e-6
        shove = gap * (np.maximum(reach[pairs[:, 0]] + reach[pairs[:, 1]] - dist, 0) / dist * 0.35)[:, None]
        np.add.at(vel, pairs[:, 0], -shove)
        np.add.at(vel, pairs[:, 1], shove)
        pos += vel
    return pos - pos.mean(0)


def pack(radii, aspect=1.6, margin=3.0, step=1.5):
    """Centres for circles of the given ``radii``: the largest at 0, then each next-largest at the first spot on a spiral, ``aspect`` times wider than tall, where it overlaps none placed before.

    A spot blocked for one radius stays blocked for that radius as more circles are placed, so a circle as large as the one before resumes the search where that one landed instead of rescanning the spiral.
    """
    order = np.argsort(-radii)
    turns = np.arange(0, 2 * (radii.sum() + margin * len(radii)) / step, 0.02)
    spiral = step * turns[:, None] * np.stack([aspect * np.cos(turns), np.sin(turns)], 1)
    centres = np.zeros((len(radii), 2))
    first = 0
    for n, i in enumerate(order[1:], 1):
        placed = order[:n]
        if radii[i] != radii[order[n - 1]]:
            first = 0
        for start in range(first, len(spiral), 2048):
            spots = spiral[start:start + 2048]
            clear = (np.linalg.norm(spots[:, None] - centres[placed], axis=2) >= radii[placed] + radii[i] + margin).all(1)
            if clear.any():
                first = start + clear.argmax()
                centres[i] = spiral[first]
                break
    return centres


def layout(count, edges, groups):
    """Positions for the whole graph: each connected part laid out on its own by ``force_layout``, then the parts packed around the largest, so parts without a link to the rest sit close by instead of drifting to the edge."""
    edges = np.asarray(edges, dtype=int).reshape(-1, 2)
    part = connected_components(coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(count, count)), directed=False)[1]
    groups = np.asarray(groups)
    pos = np.zeros((count, 2))
    for p in range(part.max() + 1):
        members = np.flatnonzero(part == p)
        local = np.full(count, -1)
        local[members] = np.arange(len(members))
        inside = edges[part[edges[:, 0]] == p]
        pos[members] = force_layout(len(members), local[inside], groups[members])
    radii = np.array([np.linalg.norm(pos[part == p], axis=1).max() for p in range(part.max() + 1)]) + 4.0
    return pos + pack(radii)[part]


def cloud(graph):
    """Compact laid-out form of ``graph`` for the front page.

    ``kinds`` names the node kinds (a record's entity type, ``ontology`` otherwise); each node row is [x, y, kind index, label, record id or ontology storid] on a 0–1000 grid, and each link row is [source index, target index, 1 when the link is taxonomic (``is_a``, ``instance_of``) and 0 otherwise].
    """
    nodes = graph['nodes']
    index = {node['storid']: i for i, node in enumerate(nodes)}
    pairs = [(index[item['source']], index[item['target']]) for item in graph['links']]
    node_kinds = [node.get('db_type') or 'ontology' for node in nodes]
    kinds = sorted(set(node_kinds))
    groups = [kinds.index(kind) for kind in node_kinds]
    pos = layout(len(nodes), pairs, groups)
    pos -= pos.min(0)
    pos *= 1000 / max(pos.max(), 1e-6)
    return {
        'kinds': kinds,
        'nodes': [
            [round(x), round(y), group, node.get('label') or '', int(str(node['storid']).rpartition('_')[2])]
            for node, group, (x, y) in zip(nodes, groups, pos.tolist())
        ],
        'links': [[s, t, int(item['type'] in TAXONOMY)] for (s, t), item in zip(pairs, graph['links'])],
    }
