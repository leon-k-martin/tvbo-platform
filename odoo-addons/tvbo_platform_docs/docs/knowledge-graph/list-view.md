---
title: List view
access_level: public
sequence: 20
---

# Knowledge Graph — list view

The **list view** is the default. It shows every entity as a card, with the entity
name, its class, a short description, and tags. A counter above the grid tells you
how many results match (e.g. *"482 results"*).

![Card list view with the Class filter on the left](img/kg-list-view.png)

## Search

Type into the big **search box** at the top (or the one in the header). The list
filters as you type, across names, labels, and descriptions — for example
`Kuramoto`, `Desikan`, `epilepsy`, or `coupling`.

## Filter by class

The **Class** panel on the left lets you narrow to one kind of entity:
**Dynamics**, **Network**, **Integrator**, **Coupling**, **Observation**,
**Experiment**, **Study**, **Atlas**, **Graph generator**, and more. Each class
shows a count. Tick one or more boxes to filter; use **Clear All Filters** (top
right) to reset.

!!! note "Database vs. ontology"
    Results combine two sources: concrete **database** records (the building blocks
    you can actually use) and the **ontology** concepts that define and relate them.
    If you only see ontology entries and no database items, the catalogue has not
    finished loading — try again shortly.

## Sort

Use the **Sort** dropdown (top right) to order results by **Relevance** (default)
or alphabetically.

## Open a detail card

Click any card to open its **detail view**: the full description, its properties,
the governing equations (rendered as math), related entities, and — where
available — a thumbnail or report. From here you can:

- follow links to **related** entities, and
- **send the entity to the [Experiment Builder](../experiment-builder/index.md)**
  to use it in an experiment.

## Next

- [Graph view](graph-view.md) — the same results as an interactive network.
