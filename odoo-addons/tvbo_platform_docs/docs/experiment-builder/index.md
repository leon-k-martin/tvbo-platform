---
title: Overview
nav_label: Experiment Builder
nav_order: 30
access_level: public
sequence: 10
---

# The Experiment Builder

The **Experiment Builder** assembles a complete, **runnable** brain‑simulation
experiment — a network, the local **dynamics**, an **integrator**, a **coupling**,
and one or more **observation models** — and exports it as a clean, validated YAML
bundle you can run with the `tvbo` Python package.

Open it at [`/tvbo/configurator`]({{base_url}}/tvbo/configurator). No account is
required to build and export.

## Watch: the full workflow

<video class="o_docs_video" controls preload="metadata">
  <source src="/tvbo_platform_docs/static/video/tvbo-experiment-builder-workflow.mp4" type="video/mp4"/>
  Your browser cannot play this video —
  <a href="/tvbo_platform_docs/static/video/tvbo-experiment-builder-workflow.mp4">download it</a>.
</video>

## Three ways to start

You can build an experiment in whichever way suits you — and you can mix them:

1. **Start from an example.** Pick a ready‑made experiment and the builder fills in
   every tab. Export immediately, or tweak first. The YAML you get is identical to
   the curated example.
2. **Build it yourself.** Go tab by tab — network, dynamics, integrator, coupling,
   observation — filling in the forms (you can add multiple entries) until you have
   a valid, runnable experiment.
3. **Bring a single component from the Knowledge Graph.** Send one entity (say a
   particular model or connectome) from the [KG](../knowledge-graph/index.md) into
   the builder, refine it, and add further components around it.

See [Build an experiment](building.md) for each route in detail, then
[Export & run](export.md).

## In this section

- [Build an experiment](building.md) — the three routes, tab by tab.
- [Export & run](export.md) — produce the YAML bundle and run it in Python.
