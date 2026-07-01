---
title: Export & run
access_level: public
sequence: 30
---

# Export & run

The **YAML Specification** panel shows the live, valid spec as you build. When
ready, use the buttons at the top-right of the builder:

- **Download** saves the experiment as a YAML bundle, plus a companion data file for
  the connectome matrices.
- **Copy Python** copies a ready-to-run snippet to your clipboard.

The YAML is schema-validated, so only well-formed experiments export. An untouched
example exports byte-for-byte the curated original.

## Run on the platform

You can run the experiment without leaving the browser. Open the **Run** tab, set
the duration, step size, and backend such as JAX (**1**), then click **Run
Simulation** (**2**). The platform runs it through the `tvbo` backend and returns
the result. This is the quickest way to check an experiment before you export it.

![The Run tab: settings and the Run Simulation button](img/builder-run.png)

For full control over a run, export it and use Python instead.

## Run it in Python

```bash
pip install tvbo
```

```python
from tvbo import SimulationExperiment

experiment = SimulationExperiment.from_file("demo_experiment.yaml")
result = experiment.run()
result.plot()
```

A run produces regional time series you can plot:

![Simulated regional time series](img/demo_model_ts.png)

## Watch: running an exported experiment

<video class="o_docs_video" controls preload="metadata" poster="/tvbo_platform_docs/static/img/poster-tvbo-run-in-python.jpg">
  <source src="/tvbo_platform_docs/static/video/tvbo-run-in-python.mp4" type="video/mp4"/>
  Your browser cannot play this video.
  <a href="/tvbo_platform_docs/static/video/tvbo-run-in-python.mp4">Download it</a>.
</video>

The [Python package](../python-package/index.md) section has the full API. Signed
in, you can save the experiment to your account instead of downloading it. See
[Save to your account](../account/save-to-account.md).
