# Aligning the TVBO Platform and the tvb-ext-ontology JupyterLab extension

**Status:** proposal · **Audience:** TVBO platform + tvb-ext-ontology maintainers

## 1. Two products, one engine

Both front-ends sit on the **same tvbo core** — the LinkML schema, the
ontology / clinical KG (`tvb-o-clinical*.ttl`), the registry of curated
building blocks, and the `SimulationExperiment` runtime (+ tvboptim). They
differ only in *role* and *host*:

| | **TVBO Platform** (`tvbo-platform`, Odoo) | **tvb-ext-ontology** (JupyterLab) |
|---|---|---|
| Purpose | **Explore & author**; **save** specs/experiments to **user accounts** | **Run** simulations next to the user's notebooks/data |
| Host | Web app (Odoo QWeb + vanilla JS) | JupyterLab extension (React/TS + a Jupyter server ext) |
| Explorer | `/tvbo/kg` force graph + card browser | `GraphView` + `InfoBox` + `TreeView` |
| Workspace | Experiment Builder → **full `SimulationExperiment` YAML** (+ connectome bundle) | `Workspace` → reduced `{model, parcellation, tractogram, coupling}` |
| Persistence | per-user (`tvbo.model_share`) | none (local files / BIDS output) |
| Run | no (exports a runnable bundle) | yes (`onto_api.experiment.run` → BIDS) |
| KG source | Odoo DB seeded from the tvbo schema, served by `building_blocks_api` | rdflib/SPARQL over the `.ttl`, served by `tvb_ext_ontology/handlers.py` |

## 2. North star

Keep the two **purposes** distinct, but make them feel like **one product**:

> A user **explores** the knowledge graph and **authors** a
> `SimulationExperiment` in the platform (saved to their account), then opens
> that exact spec in JupyterLab to **run** it beside their data — and can save
> a refined spec back. Same graph+card explorer, same workspace, same spec.

Three convergence targets, in priority order:

1. **The `SimulationExperiment` YAML is the single contract.** Both sides
   produce/consume the *same* full spec. The platform already does this (the
   download bundle is `experiment.yaml` + `connectome.h5`); the extension's
   `Workspace` must be **upgraded from the reduced object to the full spec**.
2. **One explorer + workspace UI**, shared by both hosts.
3. **The same UI, all the way down to single components.** The atomic unit is
   a **schema-driven editor for one tvbo class** (a `Dynamics`, a `Network`, a
   `Coupling`, …). The full Experiment Builder / Workspace is just a
   *composition* of these. The same editors should also be usable **standalone
   in a notebook cell** — `DynamicsEditor()`, `NetworkEditor()` — so "specify a
   component" looks identical in the platform, the JupyterLab panel, and inline
   in a notebook. **Harmonized UI everywhere.**

## 3. What's actually shared vs forked today

**Genuinely shared (the asset):** the tvbo schema, the clinical KG, the
registry of curated blocks, and `SimulationExperiment` semantics. Both UIs are
*views* of this.

**Forked (the cost):**

- **The spec model.** Platform = full `SimulationExperiment` (dynamics,
  network, coupling, observations, integration, events, …, + `transforms`,
  coordinates). Extension = a flat 4-field workspace. *These are not the same
  artifact*, so a platform experiment can't round-trip through the extension.
- **The KG API.** Two backends answer "give me nodes / links / search /
  node-detail" with different shapes (`building_blocks_api` JSON vs
  `handlers.py` SPARQL results). A shared explorer can't target both as-is.
- **The explorer UI.** Two independent implementations of the same force-graph
  + card/info concepts (Odoo JS vs React).
- **Curated option lists.** The extension *hardcodes* `parcellationOptions` /
  `tractogramOptions` in `Workspace.tsx`; the platform reads them from the tvbo
  registry. They will drift.

## 4. Convergence architecture

Layered and decoupled, so each can be aligned independently. The shared UI is
**component-granular** — schema-driven editors for single tvbo classes — which
is what lets the same UI reach a notebook cell, not just the two apps.

```
        ┌──────────────────────────────────────────────┐
        │  tvbo core: schema · ontology/KG · registry ·  │   (shared today)
        │  SimulationExperiment runtime · tvboptim       │
        └──────────────────────────────────────────────┘
              ▲                                   ▲
   ┌──────────┴───────────┐          ┌────────────┴───────────┐
   │  KG API contract     │  (align) │  Experiment-spec API   │ (align)
   │  nodes/links/search/ │          │  build · validate ·    │
   │  detail — ONE shape  │          │  bundle (yaml + h5)    │
   └──────────┬───────────┘          └────────────┬───────────┘
              ▲                                    ▲
        ┌─────┴────────────────────────────────────┴─────┐
        │  Shared UI = schema-driven COMPONENT EDITORS     │ (align)
        │  (one per tvbo class) → composed into Explorer   │
        │  + Workspace                                     │
        └──┬───────────────────┬──────────────────────┬───┘
    embeds │            embeds │              wraps    │ (anywidget)
  ┌────────┴───────┐ ┌─────────┴────────┐ ┌────────────┴───────┐
  │ Platform (Odoo)│ │ JupyterLab ext   │ │ Notebook cell      │
  │ explore + SAVE │ │ explore + RUN +  │ │ DynamicsEditor() · │
  │ + accounts     │ │ BIDS results     │ │ NetworkEditor() …  │
  └────────────────┘ └──────────────────┘ └────────────────────┘
```

### 4.1 The spec contract (highest value, lowest risk)
Make the extension's `Workspace` hold a **full `SimulationExperiment`**, not
the 4-field object. Concretely: its `runSimulation`/`exportWorkspace` already
post `nodeData` to the server, where `construct_metadata` assembles a tvbo
experiment — change that assembly to emit/round-trip the **canonical YAML**
(reuse `tvbo`'s experiment assembly so it's identical to the platform's
`pydantic_loader.dump`). Then:
- the platform's **download bundle** (`experiment.yaml` + `connectome.h5`) is
  directly **`SimulationExperiment.from_file`-loadable in the extension** — the
  handoff already works (we built/verified it this session);
- the extension can **show/edit the YAML** as its workspace, not a lossy form.

### 4.2 The KG API contract
Define one HTTP contract — `search`, `node`, `neighbors`, `detail` — returning
one node/link shape (the schema's IRIs + labels + types). Best path: both
backends **delegate to a single tvbo KG service** (e.g. `tvbo.api.ontology_api`
as source of truth) so the platform's `building_blocks_api` and the extension's
`handlers.py` are thin adapters over identical data. Kill the hardcoded
parcellation/tractogram lists in `Workspace.tsx` — serve them from the tvbo
registry like the platform does.

### 4.3 The shared UI: schema-driven component editors
The atomic unit is **a schema-driven editor for one tvbo class**, not a
monolithic explorer. The platform already has the prototype:
`schema_driven_editor.js` (the "SDE") fetches the LinkML schema
(`/tvbo/api/configurator/schema`) and renders an editor for *any* class — with
enum handling and bounded recursion for the cyclic schema. (It's currently
disabled in the platform because it competes with the hand-built Experiment
Builder tabs — see the `configurator-builder-vs-sde` note — but it is the right
primitive.) Because it's schema-driven, you get an editor for **every** tvbo
class for free: `Dynamics`, `Network`, `Coupling`, `Observation`, `Integrator`,
… The Experiment Builder and the extension Workspace are then just
*compositions* of these editors.

Package the SDE (+ the explorer's force-graph/card view) once as a
framework-neutral unit, embedded by every host. Options, cheapest → deepest:
- **(a) Contract-only:** keep both UIs, align them to the same KG API + spec
  contract + visual language. Lowest effort; they *look* aligned and
  interoperate, but code stays duplicated.
- **(b) Shared web component:** build the SDE + explorer once as framework-
  neutral **web components** (custom elements). The extension imports them; the
  platform mounts them as islands in QWeb; the notebook wraps them (see §4.5).
  One implementation, three hosts. **Recommended target.**
- **(c) Single SPA embedded twice:** the explorer becomes a standalone app
  embedded via iframe. Strong isolation, weaker host integration, and harder to
  expose as per-component notebook widgets.

### 4.4 Component editors in the notebook (anywidget)
"Specify a component directly in a cell" is the same SDE web component wrapped
as an **[anywidget](https://anywidget.dev)** (the modern ipywidgets path:
one ES-module front-end + a small Python model, works in classic Notebook,
JupyterLab and Colab). The value is the tvbo object / its YAML:

```python
from tvbo.widgets import DynamicsEditor, NetworkEditor

dyn = DynamicsEditor()          # schema-driven form for a Dynamics
dyn                             # renders inline; edit parameters / state vars / equations
dyn.value                       # -> a tvbo Dynamics (or its YAML)

net = NetworkEditor()           # pick parcellation + tractogram from the registry;
net                             # preview the connectome (matrix + brain surface)
exp = SimulationExperiment(dynamics=dyn.value, network=net.value)
```

`anywidget` is not yet installed (`ipywidgets` is); adding it + a thin
`tvbo.widgets` module that wraps the shared web component is the whole bridge.
A generic `edit(SomeTvboClass)` falls out of the schema-driven design — no
per-class hand-coding. This is what makes the UI **harmonized everywhere**: the
exact editor a user sees in the platform is the one in the JupyterLab panel and
the one in their notebook cell.

### 4.5 Round-trip between the hosts
With 4.1–4.2 in place:
- **Platform → JupyterLab:** "Open in JupyterLab to run" — hands over the spec
  (deep link by saved-experiment IRI, or the downloaded bundle). The extension
  loads it into the shared Workspace and runs.
- **JupyterLab → Platform:** "Save to my TVBO account" — POSTs the workspace
  spec to the platform's save endpoint (the `tvbo.model_share`-backed flow).

## 5. Phased plan

| Phase | Deliverable | Touches | Effort |
|------|-------------|---------|--------|
| **0** | One demo pipeline (done) — shared cinematic toolkit, both videos consistent | workshop | ✅ done |
| **1** | Extension `Workspace` ⇒ full `SimulationExperiment` YAML; consume the platform bundle | `tvb-ext-ontology` (Workspace.tsx, handlers.py) + tvbo assembly | M |
| **2** | One KG API contract + retire hardcoded option lists; both backends adapt to `tvbo.api.ontology_api` | both backends + tvbo | M |
| **3** | Extract the SDE (+ explorer) as framework-neutral **web components** (the per-class editors) | new shared UI pkg; re-enable/port `schema_driven_editor.js`; embed in both hosts | L |
| **4** | **Notebook widgets**: `tvbo.widgets` wraps the SDE web component as `anywidget` (`DynamicsEditor`, `NetworkEditor`, generic `edit(cls)`) | add `anywidget` + `tvbo/widgets/` | S–M (after 3) |
| **5** | Round-trip: "Open in JupyterLab" / "Save to account" | both hosts | M |

Phases 1–2 deliver most of the *felt* alignment (same spec, same data, same
options, working handoff) without merging UI stacks. **Phase 3 is the pivot** —
once the per-class editors are framework-neutral web components, Phase 4
(notebook widgets) is a thin `anywidget` wrapper and the same editors light up
in all three hosts. A useful early spike: ship a single `DynamicsEditor`
notebook widget against the *existing* SDE to prove the round-trip before the
full extraction.

## 6. Decisions to make

- **Source of truth for the KG API** — promote `tvbo.api.ontology_api` to the
  one service both hosts call? (Recommended.)
- **Shared-UI strategy** — web component (4.3b) vs iframe SPA (4.3c)? Only the
  web-component path cleanly yields per-component notebook widgets, so it ties
  into the harmonized-UI goal. Drives whether the platform's Experiment Builder
  is rewritten or wraps the shared components.
- **Build the per-class editors on the existing SDE** (`schema_driven_editor.js`,
  schema-driven, already covers every class) vs a fresh component library?
  Reusing the SDE keeps a single schema-driven editor; the cost is the recursion/
  cycle handling it already wrestles with.
- **Widget tech** — `anywidget` (recommended; reuses the web component, one
  codebase) vs hand-built `ipywidgets` (already installed, but a separate UI to
  maintain — defeats harmonization).
- **Do the products *merge* or just *align*?** This proposal assumes **align**
  (two hosts, shared core + UI). A full merge (one app that is both authoring
  and run host) is a larger product decision and not required to get the
  shared explorer + spec.

## 7. Non-goals
- Replacing JupyterLab-side execution with the platform (the platform stays
  authoring/exploring; running stays where the user's data is).
- Changing the tvbo schema or `SimulationExperiment` semantics — the whole
  point is that both already speak it.
