---
title: Save to your account
access_level: public
sequence: 30
---

# Save models & experiments to your account

Signed in, your customized models and assembled experiments live under **My
Models**, and you can issue API keys for scripts.

## Save and find your models

In the [Experiment Builder](../experiment-builder/index.md), use **Save to my
models** instead of (or alongside) downloading the YAML. Your saved models appear
under the user menu at **My Models** ([`/my/models`]({{base_url}}/my/models)). Each
model (**1**) can be re-opened in the builder or downloaded again.

![My Models, with a saved model and its Share button marked](img/my-models.png)

## Share with the community

Saved items stay **private** to you. Click **Share** (**2**) to publish a model.
Shared models appear in the community gallery at
[`/tvbo/models/shared`]({{base_url}}/tvbo/models/shared), where anyone signed in can
browse and load them. The same button switches it back to private.

## API keys

Name a key (**1**) and click **Create key** (**2**) at
[`/my/api-keys`]({{base_url}}/my/api-keys). Use it as a bearer token to load and
push models from Python.

![Creating an API key](img/api-keys.png)

!!! warning "Treat keys like passwords"
    An API key grants access to your account. Copy it when shown, store it safely,
    and revoke it if exposed.
