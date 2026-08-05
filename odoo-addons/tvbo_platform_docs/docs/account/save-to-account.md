---
title: Save to your account
access_level: public
sequence: 30
---

# Save models & experiments to your account

Once you sign in, your customized models and assembled experiments live under **My
Models**, and you can issue API keys for scripts.

## Save and find your models

In the [Experiment Builder](../experiment-builder/index.md), use **Save to my
models** instead of (or alongside) downloading the YAML. Your saved models appear
under the user menu at **My Models** ([`/my/models`]({{base_url}}/my/models)). Each
model (**1**) can be re-opened in the builder or downloaded again.

Whole **experiments** you assemble can be stored to your account too. Push them
from Python with the REST API (`POST /api/tvbo/v1/experiments`), so a collaborator
can reproduce your run by id rather than by emailing a YAML file. See
[Retrieve & store via the API](../python-package/api.md).

![My Models, with a saved model and its Share button marked](img/my-models.webp)

## Share or publish

Saved items stay **private** to you. There are two separate ways to let others in:

- **Share with a colleague** (**2**) — grant a specific person access instantly.
  It does not become public.
- **Submit for review** — request **publication** to the whole community. It goes
  through automated validation and a human reviewer before it appears in the
  community gallery at [`/tvbo/models/shared`]({{base_url}}/tvbo/models/shared) and
  the Knowledge Graph.

The two are independent and both are managed from **My Models**. See
[Share &amp; publish](publishing.md) for the full workflow, the validation checks,
and how to do the same from Python.

## API keys

Name a key (**1**) and click **Create key** (**2**) at
[`/my/api-keys`]({{base_url}}/my/api-keys). The raw key is shown **once**, so copy
it then. Use it as a bearer token to pull and push your models **and experiments**
from Python: see [Retrieve & store via the API](../python-package/api.md) for the
endpoints and ready-to-run code.

![Creating an API key](img/api-keys.webp)

!!! warning "Treat keys like passwords"
    An API key grants access to your account. Copy it when shown, store it safely,
    and revoke it if exposed.
