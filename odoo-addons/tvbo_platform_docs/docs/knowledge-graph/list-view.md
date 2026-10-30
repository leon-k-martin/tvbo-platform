---
title: List view
access_level: public
sequence: 20
---

# Knowledge Graph: list view

The default view shows one card per entity, with a result counter above the grid. The numbered markers below match the controls in the screenshot.

![The list view: search, Class filter, view toggle, and a result card marked](img/kg-list-view.webp)

1. **Search** filters live across names, descriptions and the other text of each entity, such as a study's authors and journal, as you type. Try `Kuramoto`, `Desikan`, or `epilepsy`.
2. The **Class** filter narrows results to Dynamics, Network, Coupling, Study, Brain atlas, and the rest; each row shows a count. **Clear All Filters** resets it, and **Sort** orders by relevance or alphabetically.
3. The **view toggle** switches between this list and the [graph view](graph-view.md).
4. Each **card** is one entity: its class, title and description, then its key facts. A study shows its authors, year, journal, DOI and the models that cite it; an experiment its model, network and integrator; a model its state variables, parameters and the experiments that use it. An experiment carries its own copy of the library model or integrator it runs; that copy has no card of its own, so the library entity's card lists the experiment, and the experiment's card shows what its copy changes, such as a step size or a parameter value next to the library's. Click a card to open the detail.

## Open a detail card

The detail shows the full entity: description, parameters, state variables and governing equations, then under **Metadata** every other field it holds, its links to other entities and the entities that link to it. A linked entity opens in place.

![Entity detail](img/kg-detail.webp)

Follow the links to related entities, or send the entity to the [Experiment Builder](../experiment-builder/index.md).
