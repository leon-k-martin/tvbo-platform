# Experiment Builder + thin-Odoo/LinkML — status & review items

Everything under "Done & verified" is implemented and tested. The rest is for your
review / future work.

## Done & verified

### Experiment Builder (assemble → validate → YAML)
- Renamed **Model Builder → Experiment Builder** (navbar, page title, template).
- `tvbo.utils.pydantic_loader` (in the tvbo repo) is the single trustworthy validator:
  normalizes TVBO's keyed-dict YAML (key→identifier injection), coerces Odoo's
  list/object/Text forms to the schema shape, strips file-envelope keys, and (for the
  DB export) drops platform-only fields via `drop_unknown=True`. Strict
  (`extra="forbid"`) so hand-authored input still rejects typos. Tests:
  `tvbo/tests/test_pydantic_loader.py` (222 passed).
- Backend endpoints all go through `pydantic_loader`: `/experiment/serialize`
  (assemble→validate→bare YAML), `/experiment/<id>/yaml`, `/experiment/<id>/spec`
  (validated JSON the builder hydrates from), `/instances/<class>/<id>/spec`
  (validated single building block, for KG seeding).
- Frontend assembles a schema-shaped experiment, validates/serializes server-side;
  live preview shows ✓ valid / ⚠ errors; Download YAML + Copy Python emit validated,
  tvbo-loadable output.
- **All 6 curated experiments validate** (EI Tuning, JR Peak Frequency, RWW, RateML,
  Jansen-Rit bifurcation, QIF bifurcation), plus from-scratch and **tvboptim interop**
  (`class_reference`). e2e: `tests/e2e/specs/builder.spec.ts` — **9/9 pass**.

### Knowledge Graph → Experiment Builder
- Every KG card has an **"Open in Experiment Builder"** button. Experiment cards deep
  link `?experiment=<id>` (loads the full experiment); building-block cards deep link
  `?dynamics=<id>` / `?network=<id>` / `?coupling=<id>` / `?observation=<id>` /
  `?integration=<id>` and seed a new experiment from that block (via `/instances/.../spec`).
- The builder auto-loads from those URL params; the legacy "Load Existing Experiment"
  dropdown is hidden (kept in DOM for back-compat).

### Thin Odoo layer driven by LinkML (no more divergence)
- New `scripts/linkml_odoo_generator.py` — an `OOCodeGenerator` subclass that emits
  `schema_models.py` from the tvbo LinkML schema using `SchemaView` (induced slots,
  aliases, types, enums, flattened inheritance). `scripts/generate_odoo_models.py` is
  now a thin CLI (`--check` for CI) that also regenerates `ir.model.access.csv`.
  Replaces ~2,774 lines of hand-rolled scripts (preserved at `scripts/legacy/`).
- **Root-cause of the old divergence fixed:** the old generator ignored LinkML
  `alias`. Fixed `tvbo/schema/tvbo_datamodel.yaml` so the canonical slot names are
  `lhs`/`rhs` (was `lefthandside`/`righthandside` with `alias: lhs`) and
  `experiments` (in SimulationStudy). Now SchemaView, pydantic, the data and the
  generated Odoo models all agree — the bridging glue is gone (`solver_id` inheritance
  link and `derived_observations` were old-generator artifacts, not in the schema).
- New `odoo-addons/tvbo/models/ingest.py` — **one flow, no XML**: a `post_init_hook`
  reads `tvbo/database/*.yaml` via the registry, validates each through
  `pydantic_loader`, and creates Odoo records (recursive, per-record **savepoints** so
  one bad record can't abort the install). Enums seeded from the generated pydantic
  enums. `__manifest__.py` no longer lists the `database_*.xml` / `data_*enum.xml`
  fixtures.
- Fresh install seeds **204 records**: Dynamics 77/98, Coupling 9/9, Integrator 7/7,
  Network 62/62, Observation 16/16, BrainAtlas 5/5, Continuation 2/2,
  SimulationExperiment 6 curated.
- `init-odoo.sh` made network-resilient (skip the redundant editable reinstall when
  tvbo is already importable; never hard-fail there).

## Review / follow-ups

### RESOLVED — GraphGenerator + studies now seed (schema↔data drift fixed)
The earlier "regenerate pydantic" hypothesis was wrong (pydantic was already
current). Both were genuine schema↔data drift in the tvbo repo:
- **GraphGenerator (9/9 now)**: the curated files carry a richer shape than the
  schema class (`iri`, per-backend `bindings`, a symbolic `procedure`, and
  parameter *specs* with `range`/`required`/`ifabsent`; no `type`). Extended the
  tvbo `GraphGenerator` class to match — added `iri` (reused the shared slot),
  `bindings` (→ new `Binding`, keyed by backend `name`), `procedure` (→ new
  `Procedure` + `ProcedureStep` reusing `Equation`), switched `parameters` to a
  new `ParameterSpec`, made `type` optional. (`schema/tvbo_datamodel.yaml`.)
- **studies (120/120 now)**: the `studies/*.yaml` are BibTeX-style bibliographic
  records, not `SimulationStudy` experiment containers. Added a minimal `Study`
  anchor class (`name`/`citekey`/`type`/`title`/`authors`/`year`/`doi`) and made
  `SimulationStudy is_a Study`. We do **not** replicate BibTeX: full citation
  detail stays in `references.bib` (1557 entries; 93/120 citekeys already there),
  joined by `citekey`. Ingest seeds `Study` with `drop_unknown=True` so the
  BibTeX extras (journal/volume/pages/…) are dropped, keeping the citekey-anchored
  KG node. Registry maps `Study → studies/` (kept `SimulationStudy → studies/`).
- Regenerated `tvbo/datamodel/{pydantic,schema}.py` and the platform's
  `schema_models.py` (133 models, +5) + `ir.model.access.csv`. `pydantic_loader`
  `load`/`loads` now forward `drop_unknown`.
- **Verified**: pydantic_loader validates GraphGenerator 9/9 and Study 120/120;
  222/222 loader tests pass; the Odoo registry loads the new models cleanly; a
  **clean-room install** ran `post_init_hook` end-to-end → **graph_generator 9/9,
  study 120/120, DONE: 313 records** (was 184), with bindings/parameter_spec/
  procedure_step nested records created via the real Odoo ORM.
- Dynamics 77/98: unchanged baseline — the gap is the excluded
  `database/models/neuroml/` staging import (intentional, see below). (8 of the
  21 are pre-existing `InFailedSqlTransaction` failures, not caused by this work.)

### KNOWN — in-place upgrade of an existing DB needs a stale-relation drop
On a **fresh install** everything seeds cleanly (verified). Upgrading a DB that
already had the old schema fails once: `graph_generator.parameters` changed its
comodel (`Parameter` → `ParameterSpec`) but reuses the auto-named m2m relation
`tvbo_graph_generator_parameters_rel`, whose old table still has the
`tvbo_parameter_id` column → FK error on `tvbo_parameter_spec_id`. The relation
is empty (graph_generator had 0 rows before). Fix for an in-place upgrade: drop
that stale relation table, then `TVBO_UPGRADE=1`. Cleaner long-term: a module
pre-migration script, or a fresh `RESET_DB=1` reinstall. (The running `tvbo_dev`
has the new models in code but the new tables are not yet created.)

### Study ↔ concept edges (Phase 1 — KG rendering)
The links are already in the data: dynamics/experiments/networks carry their
source papers as **citekeys** in `references:` (91 distinct; 79 match a study).
Phase 0 keeps `references` as a string slot (changing its global range to `Study`
is high blast-radius — it is shared and a few experiments use prose, not
citekeys), so the citekeys are stored as Text on each concept and the
study↔concept join is rendered in the KG browser in Phase 1. Phase 2 adds the
`Disease`/clinical metadata class + links (Epileptor → epilepsy, `Proix2017`).

### MEDIUM — NeuroML import staging excluded
- `ingest.py` skips `tvbo/database/.../neuroml/` (the "… as LEMS" experiments and exotic
  dynamics like `hhcell`/`HH_KineticScheme` with null `coupling_inputs` / a NeuroML-only
  `components` slot). Fix the NeuroML→tvbo importer if those should be offered.

### LOW — known limitations / notes
- **Addon logging during `post_init_hook` / some requests doesn't surface** in the
  install/runtime logs; `ingest.py` writes an audit trail to
  `/var/lib/odoo/tvbo_ingest.log` as a workaround. Worth understanding (Odoo log config).
- Deep-resolve uses memoization + a cycle guard so complex experiments stay fast; the
  earlier bifurcation "timeout" was actually a non-ASCII filename in the
  Content-Disposition header (em-dash / `η̄`) breaking the HTTP response — now
  ASCII-sanitized.
- `assembleExperimentSpec` preserves a loaded experiment's collection sections as-is and
  overlays only scalar/general/integration/coupling + from-scratch sections; per-member
  editing of a loaded experiment's collections via the simple row UIs isn't wired back.
- "Save to Database" still saves a Dynamics model, not a full SimulationExperiment;
  this is where it should hook into the portal save/ownership flow (below).
- Two deep resolvers remain (`building_blocks_api` vs `model_configurator`); could unify.
- Full *runtime* validation (`SimulationExperiment.from_string`) needs connectivity data
  files, so it's advisory in `tests/validate_experiment.py`; pydantic is the gate.

### Portal / session storage (your in-progress feature)
- `portal.spec.ts` + `portal_templates.xml` + the `visibility`/`owner` model fields are
  your save & share track. `pydantic_loader.validate(drop_unknown=True)` already ignores
  those platform-only fields on export. `portal.spec.ts` currently fails in the combined
  e2e run (needs admin-provisioned portal users / the feature finished); run
  `builder.spec.ts` alone for the builder suite (9/9).
