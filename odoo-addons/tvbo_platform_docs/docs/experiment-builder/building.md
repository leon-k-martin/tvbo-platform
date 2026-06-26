---
title: Build an experiment
access_level: public
sequence: 20
---

# Build an experiment

The builder is organised as **tabs**, one per part of the experiment. You can fill
them in any order; the builder keeps a single working specification (your
*workspace*) and validates it as you go.

![The Experiment Builder](img/builder-overview.png)

## Route 1 — Start from an example

The quickest way to a runnable experiment:

1. Open the **example / load** control and choose an example experiment.
2. The builder **prefills every tab** — network, dynamics, integrator, coupling,
   and observations.
3. Go straight to [Export](export.md), or adjust any tab first.

The exported YAML for an untouched example is **identical** to the curated source,
so examples are a reliable, reproducible starting point.

## Route 2 — Build it yourself

Work through the tabs:

1. **Network** — choose a connectome (or a graph generator), and set its options.
   The number of nodes is taken from the network; you only set it explicitly for a
   purely artificial network.
2. **Dynamics** — pick the local model (e.g. a neural mass model). You can open the
   model editor to adjust state variables, parameters, and observables. Edited
   models are tagged so your changes are preserved on export.
3. **Integrator** — choose the integration scheme and step size.
4. **Coupling** — choose the coupling function and its parameters.
5. **Observation** — add one or more observation models (you can add several
   entries), each with its source, period, and class reference.

The builder validates continuously. When the specification is complete and valid,
move on to [Export](export.md).

!!! note "Multiple entries"
    Tabs such as **observation** accept **multiple** entries — use the *add* control
    to append rows, and remove any you do not need.

## Route 3 — Bring a component from the Knowledge Graph

Start from something you found while browsing:

1. In the [Knowledge Graph](../knowledge-graph/index.md), open an entity's detail
   card and choose to **send it to the builder**.
2. The component lands in your workspace; refine it in its tab.
3. **Add further components** — repeat from the KG, or fill the remaining tabs by
   hand. After customizing one selection you can make **another** selection and add
   it to the same experiment.

This way you compose an experiment piece by piece from curated building blocks.

## Next

- [Export & run](export.md) — produce the YAML bundle and run it.
