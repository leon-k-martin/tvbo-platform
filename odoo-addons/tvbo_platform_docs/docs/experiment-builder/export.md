---
title: Export & run
access_level: public
sequence: 30
---

# Export & run

When your experiment is complete and valid, export it as a **YAML bundle** — a
clean, validated description of the whole experiment that the `tvbo` Python package
can run directly.

## Export the bundle

As you build, the **YAML Specification** panel on the right shows the live, valid
spec for your experiment. When you are happy with it:

1. Click **Download** (top‑right of the builder) to save the experiment as a YAML
   bundle — plus, for experiments with a connectome, a companion data file for the
   network matrices.
2. Or click **Copy Python** to copy a ready‑to‑run Python snippet to your clipboard.

The YAML is **schema‑validated** — only well‑formed, runnable experiments export
cleanly.

!!! tip "Reproducible by design"
    The export contains exactly what you assembled — nothing platform‑specific. An
    untouched example exports byte‑for‑byte the curated original, so results are
    reproducible across machines.

## Run it in Python

Install the package and run your bundle:

```bash
pip install tvbo
```

```python
import tvbo

# Load the experiment you exported from the builder
experiment = tvbo.load("demo_experiment.yaml")

# Run the simulation
result = experiment.run()

# Inspect / plot the output
result.plot()
```

A typical run produces regional time series and connectivity you can plot:

![Simulated regional time series](img/demo_model_ts.png)

![Connectome used by the experiment](img/demo_connectome.png)

## Watch: running an exported experiment in Python

<video class="o_docs_video" controls preload="metadata">
  <source src="/tvbo_platform_docs/static/video/tvbo-run-in-python.mp4" type="video/mp4"/>
  Your browser cannot play this video —
  <a href="/tvbo_platform_docs/static/video/tvbo-run-in-python.mp4">download it</a>.
</video>

See the [Python package](../python-package/index.md) section for the full API.

!!! note "Keep your work"
    Logged in, you can **save the experiment to your account** instead of (or as
    well as) downloading it — see [Save to your account](../account/save-to-account.md).
