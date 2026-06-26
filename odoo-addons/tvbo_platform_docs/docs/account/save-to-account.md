---
title: Save to your account
access_level: public
sequence: 30
---

# Save models & experiments to your account

When you are **signed in**, you can keep your work on the platform instead of only
downloading files — your customized models and assembled experiments live under
**My Models**, and you can issue **API keys** for programmatic access.

## Save from the Experiment Builder

1. [Sign in](create-account.md) first.
2. Build or customize your experiment in the
   [Experiment Builder](../experiment-builder/index.md).
3. Use **Save to my models** (instead of, or in addition to, exporting the YAML).
   The model/experiment is stored under your account.

## Find your saved work

Open the **user menu** (top‑right, under your name) → **My Models**, or go straight
to [`/my/models`]({{base_url}}/my/models). From here you can re‑open an item back in
the builder, or download its YAML again.

## Private vs. shared

Saved items are **private to you** by default. The curated catalogue in the
[Knowledge Graph](../knowledge-graph/index.md) stays public; your saved items do not
appear there unless you choose to share them. Sharing is tracked separately from the
catalogue, so your private work never leaks into the public ontology.

## API keys

For programmatic access (e.g. fetching your models from a script or notebook),
create a token under the user menu → **API Keys**, or at
[`/my/api-keys`]({{base_url}}/my/api-keys).

!!! warning "Treat keys like passwords"
    An API key grants access to your account. Copy it when it is shown, store it
    safely, and revoke it from the same page if it is ever exposed.

## Account & profile

Review or update your profile, and sign out, from [`/my`]({{base_url}}/my).
