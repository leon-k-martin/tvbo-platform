---
title: What is TVB-O
nav_label: About TVB-O
nav_order: 5
access_level: public
sequence: 5
summary: One typed specification that compiles to runnable code and grounds every model in a knowledge graph.
---

# What is TVB-O

Brain-network models are hard to reproduce and compare. Equations, parameters, networks, and numerical settings are reported inconsistently, and shared code drifts from the paper it came with. TVB-O fixes this by making the whole experiment one object.

You describe a simulation experiment once, as a typed specification grounded in an ontology. From that single source, TVB-O does two things: it compiles runnable code and a methods report, and it grounds every entity in a knowledge graph.

<img src="/tvbo_platform_docs/static/fig/tvbo-overview.png" alt="One specification, two payoffs: TVB-O compiles a typed specification to code and a methods report across backends (reproducible) and grounds every entity in a knowledge graph (comparable)." style="width:100%; border:1px solid rgba(128,128,128,.2); border-radius:12px; display:block; margin:1rem 0;"/>

## One specification

A specification captures everything needed to reproduce a run: the local dynamics, the network and its coupling, the integrator, any stimuli, the observation pipeline, and the provenance. Each part is written inline, loaded from the database, or referenced by a semantic pointer into the ontology.

<img src="/tvbo_platform_docs/static/fig/tvbo-anatomy.svg" alt="Anatomy of a SimulationExperiment: Network wrapping Dynamics and Coupling, Integration, Event wrapping Stimulus, Observation, Exploration, Analysis and Environment." style="width:100%; display:block; margin:1rem 0;"/>

## Two payoffs

**Reproducible.** One compiler emits equivalent code across independent backends, plus a publication-ready methods report. A shared study re-runs without drift between what the paper says, what the code does, and what the docs claim.

**Comparable.** A four-domain ontology grounds each entity in physical units, biological process, brain anatomy, and clinical disorder. Two studies that use the same dynamics under different symbols become comparable by what their parameters mean, not by what they are called.

## See it in action

Find and compare models in the Knowledge Graph:

<video class="o_docs_video" controls preload="metadata" poster="/tvbo_platform_docs/static/img/poster-tvbo-knowledge-graph-tour.webp">
  <source src="/tvbo_platform_docs/static/video/tvbo-knowledge-graph-tour.mp4" type="video/mp4"/>
  Your browser cannot play this video.
  <a href="/tvbo_platform_docs/static/video/tvbo-knowledge-graph-tour.mp4">Download it</a>.
</video>

Assemble and export a runnable experiment in the browser:

<video class="o_docs_video" controls preload="metadata" poster="/tvbo_platform_docs/static/img/poster-tvbo-experiment-builder-workflow.webp">
  <source src="/tvbo_platform_docs/static/video/tvbo-experiment-builder-workflow.mp4" type="video/mp4"/>
  Your browser cannot play this video.
  <a href="/tvbo_platform_docs/static/video/tvbo-experiment-builder-workflow.mp4">Download it</a>.
</video>

Run the same experiment in Python:

<video class="o_docs_video" controls preload="metadata" poster="/tvbo_platform_docs/static/img/poster-tvbo-run-in-python.webp">
  <source src="/tvbo_platform_docs/static/video/tvbo-run-in-python.mp4" type="video/mp4"/>
  Your browser cannot play this video.
  <a href="/tvbo_platform_docs/static/video/tvbo-run-in-python.mp4">Download it</a>.
</video>

## The pieces

| Piece | What it is |
|---|---|
| Ontology | An OWL vocabulary and axioms for the core concepts of whole-brain simulation, aligned to Gene Ontology, UBERON, QUDT, KiSAO, and openMINDS. |
| Metadata schema | A LinkML specification of a `SimulationExperiment`, readable by humans and machines. |
| Database | Curated models, brain networks, coupling functions, atlases, and studies, versioned and grounded in the ontology. |
| Python package | `tvbo` compiles a specification to 13+ backends, runs it, and exports FAIR metadata and reports. |
| Platform | This site: browse the knowledge base, build and run experiments, and save or share your work. |

## Where to go next

- [Getting Started](../index.md) — browse, build, run, and save.
- [Knowledge Graph](../knowledge-graph/index.md) — search models, networks, couplings, and studies.
- [Experiment Builder](../experiment-builder/index.md) — assemble and run an experiment.
- [Python package](../python-package/index.md) — run experiments in Python. Full docs at [virtual-twin.github.io/tvbo](https://virtual-twin.github.io/tvbo/).
