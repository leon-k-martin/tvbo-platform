---
title: Python package
nav_label: Python Package
nav_order: 50
access_level: public
sequence: 10
---

# The `tvbo` Python package

The platform is the front end; **`tvbo`** is the engine. Use it directly to run
experiments, script parameter sweeps, and integrate with the scientific-Python
ecosystem.

!!! note "Full API documentation"
    The complete, versioned reference and tutorials live at
    **[virtual-twin.github.io/tvbo](https://virtual-twin.github.io/tvbo/)**. This is
    just a quick start.

```bash
pip install tvbo
```

Run an experiment you exported from the
[Experiment Builder](../experiment-builder/index.md):

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
