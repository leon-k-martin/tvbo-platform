---
title: Python package
nav_label: Python Package
nav_order: 50
access_level: public
sequence: 10
summary: Run experiments in Python with the tvbo package.
thumbnail: img/demo_model_phase.png
---

# The `tvbo` Python package

Every experiment you build on the platform runs on the open-source `tvbo` package.
Use it to run experiments and script parameter sweeps in Python.

!!! note "Full API documentation"
    The complete reference and tutorials are at
    [virtual-twin.github.io/tvbo](https://virtual-twin.github.io/tvbo/). This page is
    a quick start.

```bash
pip install tvbo
```

Run an experiment you exported from the
[Experiment Builder](../experiment-builder/index.md):

```python
from tvbo import SimulationExperiment

experiment = SimulationExperiment.from_file("demo_experiment.yaml")
result = experiment.run()
result.plot()
```

![Phase portrait of the local model](img/demo_model_phase.png)

Want to pull experiments and models straight from the platform (public ones, or
**your own** private and shared work with an API key) and push new ones back? See
[Retrieve & store via the API](api.md).

## Watch: from model to a Python run

<video class="o_docs_video" controls preload="metadata" poster="/tvbo_platform_docs/static/img/poster-tvbo-run-in-python.jpg">
  <source src="/tvbo_platform_docs/static/video/tvbo-run-in-python.mp4" type="video/mp4"/>
  Your browser cannot play this video.
  <a href="/tvbo_platform_docs/static/video/tvbo-run-in-python.mp4">Download it</a>.
</video>
