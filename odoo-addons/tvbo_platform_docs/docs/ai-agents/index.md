---
title: Overview
nav_label: AI Agents
nav_order: 60
access_level: public
sequence: 10
summary: Build and run experiments with an AI coding assistant and the tvbo package.
thumbnail: img/agents.png
---

# AI Agents

Your AI coding assistant (Claude, Cursor, Copilot, or a local model) does not know
what TVBO is until you tell it. TVBO ships a bundle of focused **skills** that teach
an assistant the model spec format, the backend choices, and the platform, so it can
find models in the Knowledge Graph, assemble a `SimulationExperiment`, run it, and
iterate in code.

[**Open the full guide →**]({{base_url}}/tvbo/agents)

![Agentic Coding with TVBO](img/agents.png)

Install the skills once with the **Quick install** on the full guide, and your
assistant carries that context into every session. The guide goes from beginner to
expert: run a curated model, describe an experiment in plain language and let the
assistant write and run it, then scale up to parameter sweeps and push results back
to your account with the [API](../python-package/api.md).

Everything an agent needs is the [`tvbo` package](../python-package/index.md) and its
[reference docs](https://virtual-twin.github.io/tvbo/).
