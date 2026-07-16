# Publication workflow — architecture note

How user-generated content (models, experiments, studies) goes from a private
draft to public community content, and how the two sharing mechanisms differ.
User-facing docs live in the platform docs site
(`odoo-addons/tvbo_platform_docs/docs/account/publishing.md` and
`…/account/reviewing.md`); this note is for maintainers.

## Two orthogonal mechanisms

| | Peer-to-peer **sharing** | **Publishing** |
|---|---|---|
| Field | `shared_user_ids` (M2M `res.users`) | `publication_state` state machine |
| Audience | named collaborators | everyone (once `published`) |
| Gate | none — instant, owner-driven | automated validation **+** peer review |
| Reversible | remove a collaborator | withdraw / unpublish → `draft` |

Effective read access to an element is the **union**:

```
owner  OR  user ∈ shared_user_ids  OR  publication_state == 'published'
```

This single rule lives in `tvbo.model_share.is_accessible_to(user)` and its bulk
companion `hidden_target_ids(share_field, user)`. Every read path uses them:
the REST API (`controllers/api.py`), the configurator endpoints
(`controllers/model_configurator.py`), the Knowledge Graph
(`controllers/kg_api.py`) and the portal gallery (`controllers/portal.py`).

## Why it lives off the schema entities

Ownership/sharing/publication is a **platform** concern. Putting any of it on the
generated schema entities (`tvbo.dynamics`, `tvbo.simulation_experiment`,
`tvbo.study`) would leak non-schema fields into the strict YAML serialization the
ontology forbids. So it all lives in the platform-only `tvbo.model_share` model
(`models/model_sharing.py`); the schema entities stay field-free. One share row per
saved element, targeting exactly one of `dynamics_id` / `experiment_id` /
`study_id`.

## State machine

`publication_state` is the source of truth:

```
draft ──submit──▶ [run_technical_validation]
                      pass │            │ fail
                           ▼            ▼
                      in_review     stays draft (report saved)
                       │     │
                approve│     │reject (note required)
                       ▼     ▼
                  published   changes_requested ──resubmit──▶ …
```

Transitions (all on `tvbo.model_share`):

- `submit_for_review()` — owner; validates, then `→ in_review` on pass. Subscribes
  the owner, schedules a to-do activity for each reviewer, logs `submit`.
- `action_approve(note)` — reviewer; `→ published`, stamps `published_date` /
  `reviewer_id`, notifies owner, closes activities, logs `approve`.
- `action_reject(note)` — reviewer; `→ changes_requested`, note required, notifies
  owner, logs `reject`.
- `withdraw()` — owner; any state `→ draft`.
- Backend button wrappers: `button_submit`, `button_approve`, `button_reject`,
  `button_revalidate` (raise `UserError` so the web client shows a dialog).

### The `visibility` compatibility mirror

`visibility` (`private` / `shared`) predates this workflow and is read in many
places. It is now a **stored computed** field: `shared` iff `published`. This keeps
every legacy read working unchanged while `publication_state` drives everything. Do
**not** write `visibility` directly — set `publication_state`.

Migration `migrations/19.0.1.0.2/pre-migrate.py` backfills `publication_state` from
the old `visibility` column *before* Odoo recomputes, so previously-shared elements
stay public across the upgrade.

## Automated technical validation

`run_technical_validation()` runs four checks and persists a JSON report
(`validation_report`, rendered to `validation_html`) plus `validation_state`:

1. **Metadata completeness** (`_vcheck_metadata`) — name/label, description ≥ 20
   chars, citation for studies, owner.
2. **Schema validity** (`_vcheck_schema`) — reuses
   `controllers/building_blocks_api.validate_instance` / `validate_experiment`
   (the same pydantic/LinkML validation as the YAML export).
3. **Reference integrity** (`_vcheck_references`) — no directly-referenced building
   block is another user's non-published content.
4. **Runnable smoke-test** (`_vcheck_runnable`, experiments only) — best-effort
   short run via the tvbo package. A missing runtime → **skipped** (not failed), so
   the web tier need not carry heavy backends.

`skipped` checks do not count against the pass/fail decision.

## Security

- New group **`group_tvbo_reviewer`** (implies `base.group_user`),
  category *TVBO Platform* — `security/platform_security.xml`.
- Owners keep the existing own-and-shared read + own-only write record rules.
- Reviewers get read-all + write-on-non-draft record rules, so they can decide on
  submissions they don't own.
- `tvbo.publication_review` (append-only audit) — owners read their own rows,
  reviewers read/write all.
- App flows still go through `sudo()` controllers; the record rules are
  defense-in-depth for any non-sudo/API path.

## UI

- **Portal** (`views/portal_templates.xml`, `static/src/js/portal_models.js`):
  My Models shows the state badge, collaborator chips and reviewer feedback, with
  actions Submit / Withdraw / Unpublish / Share / Unshare. New page `/my/shared`
  ("Shared with me"). Endpoints in `controllers/portal.py`.
- **Backend** (`views/publication_review_views.xml`): *Publications → Review
  Requests* queue (reviewer-only menu), form with the validation report, approve /
  request-changes / re-validate buttons, audit history and chatter.

## Extension points

- **Enforce the runnable smoke-test**: in `_vcheck_runnable`, return a real
  `ok: False` instead of `skipped` when the runtime is absent, or gate on an
  `ir.config_parameter` flag.
- **Require N approvals**: `action_approve` currently publishes on the first
  approval. Add an approvals counter / M2M of approvers and only flip to
  `published` when the quorum is met.
- **Assign reviewers**: add a `reviewer_id` assignment step and scope the queue.
- **Async / heavy validation**: move `run_technical_validation` to a job queue and
  add a `validating` transient state if checks become expensive.
- **Publish studies**: `study_id` is already a supported target; wire a study
  submit entry point into the relevant UI when needed.
