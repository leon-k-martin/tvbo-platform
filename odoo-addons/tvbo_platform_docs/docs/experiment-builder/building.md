---
title: Build an experiment
access_level: public
sequence: 20
---

# Build an experiment

The builder is a row of **tabs**, one per part of the experiment. Fill them in any
order — the builder keeps one working spec and validates it live (the **YAML
Specification** panel on the right). Three ways to start, and you can mix them:

## 1 — Start from an example

Open the load control, pick an example, and every tab is prefilled. Export
straight away, or tweak first. An untouched example exports **identical** to the
curated original.

## 2 — Build it yourself, tab by tab

![General tab](img/builder-general.png)

- **General** — name, label, description.
- **Dynamics** — *Add Dynamics Model*, then pick the local model; open the editor to
  adjust state variables, parameters, and observables. Edited models are tagged so
  your changes survive export.

  ![Dynamics tab](img/builder-dynamics.png)

- **Network** — choose a connectome or graph generator. Node count comes from the
  network (set it by hand only for a purely artificial one).

  ![Network tab](img/builder-network.png)

- **Integration** — scheme and step size.
- **Observations** — add one or more observation models, each with source, period,
  and class reference.

  ![Observations tab](img/builder-observations.png)

## 3 — Bring a component from the Knowledge Graph

From a [KG](../knowledge-graph/index.md) detail card, **send it to the builder**;
it lands in your workspace to refine. Add more the same way, or fill the remaining
tabs by hand — after customizing one selection you can add **another**.

## Next

[Export & run](export.md) — produce the YAML bundle and run it.
