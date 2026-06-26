---
title: Python package
nav_label: Python Package
nav_order: 50
access_level: public
sequence: 10
---

# The `tvbo` Python package

Everything you build on the platform runs on the open‑source **`tvbo`** Python
package. The platform is the friendly front end; `tvbo` is the engine — use it
directly to run experiments, script large parameter sweeps, and integrate with the
wider TVB / scientific‑Python ecosystem.

!!! note "Full API documentation"
    The complete, versioned package documentation lives at
    **[virtual-twin.github.io/tvbo](https://virtual-twin.github.io/tvbo/)** — API
    reference, tutorials, and the data model. This page is just a quick start.

## Install

```bash
pip install tvbo
```

## Run an experiment you exported

Export an experiment from the [Experiment Builder](../experiment-builder/index.md),
then:

```python
import tvbo

experiment = tvbo.load("demo_experiment.yaml")
result = experiment.run()
result.plot()
```

![Phase portrait of the local model](img/demo_model_phase.png)

## Watch: from model to a Python run

<video class="o_docs_video" controls preload="metadata">
  <source src="/tvbo_platform_docs/static/video/tvbo-run-in-python.mp4" type="video/mp4"/>
  Your browser cannot play this video —
  <a href="/tvbo_platform_docs/static/video/tvbo-run-in-python.mp4">download it</a>.
</video>

## Where to go next

- **[Package documentation](https://virtual-twin.github.io/tvbo/)** — the full
  reference and tutorials.
- **[Experiment Builder](../experiment-builder/index.md)** — assemble experiments
  visually, then export and run them here.
- **[Knowledge Graph](../knowledge-graph/index.md)** — find models, networks, and
  studies to build from.
