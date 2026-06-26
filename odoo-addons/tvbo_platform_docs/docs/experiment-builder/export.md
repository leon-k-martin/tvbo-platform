---
title: Export & run
access_level: public
sequence: 30
---

# Export & run

The **YAML Specification** panel shows the live, valid spec as you build. When
ready (top-right of the builder):

- **Download** — the experiment as a YAML bundle (plus a companion data file for
  the connectome matrices).
- **Copy Python** — a ready-to-run snippet to your clipboard.

The YAML is schema-validated, so only well-formed experiments export. An untouched
example exports byte-for-byte the curated original.

## Run it in Python

```bash
pip install tvbo
```

```python
import tvbo

experiment = tvbo.load("demo_experiment.yaml")
result = experiment.run()
result.plot()
```

A run produces regional time series and connectivity you can plot:

![Simulated regional time series](img/demo_model_ts.png)

## Watch: running an exported experiment

<video class="o_docs_video" controls preload="metadata">
  <source src="/tvbo_platform_docs/static/video/tvbo-run-in-python.mp4" type="video/mp4"/>
  Your browser cannot play this video —
  <a href="/tvbo_platform_docs/static/video/tvbo-run-in-python.mp4">download it</a>.
</video>

See the [Python package](../python-package/index.md) for the full API.

!!! note "Keep your work"
    Signed in, you can **save the experiment to your account** instead of (or as
    well as) downloading — see [Save to your account](../account/save-to-account.md).
