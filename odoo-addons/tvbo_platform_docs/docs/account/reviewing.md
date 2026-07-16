---
title: Reviewing submissions (staff)
nav_label: Your Account
access_level: internal
sequence: 50
summary: How the review team approves or returns community publication requests.
---

# Reviewing publication requests

*This page is for internal staff in the **Publication Reviewer** group. Community
members submit content; reviewers decide whether it is published.*

## Who can review

Reviewers are internal Odoo users added to the **Publication Reviewer**
(`group_tvbo_reviewer`) group. Grant it in **Settings → Users → (user) → Other →
TVBO Platform → Publication Reviewer**, or by adding the user to the group record.
A single reviewer's approval is enough to publish.

## The queue

![The Publications → Review Requests queue in the backend](img/publications-queue.png)

Open **TVBO Database → Publications → Review Requests** in the backend. It lists
every submission that is not a private draft, defaulting to **Awaiting review**.
Rows are colour-coded: amber = awaiting review, green = published, red = validation
failed. Filter by state, validation result, element kind or owner from the search
bar, or “Decided by me” to find your own past decisions.

Only submissions that already **passed automated validation** reach *In review* —
the platform blocks anything that fails the machine checks before it ever gets to
you, so you are reviewing scientific/editorial quality, not broken data.

## Reviewing one submission

Open a request. The form shows:

- **Automated validation** — the full report: metadata, schema, reference
  integrity and the runnable smoke-test. A *skipped* smoke-test (⚠) means no
  simulation runtime was available on the node; run it yourself if in doubt.
- **The element** — owner, kind, and a link to the underlying model / experiment /
  study so you can inspect the actual content.
- **History** — the append-only audit trail of every submit / validation /
  decision, with who and when.
- **Chatter** — messages and the owner as a follower, so your decision notifies them.

### Approve

Click **Approve &amp; Publish**. The element becomes **Published** immediately: it
appears in the community gallery and the Knowledge Graph, is loadable by id through
the API, and the owner is notified. You are recorded as the deciding reviewer.

### Request changes

Put actionable feedback in **Reviewer note** (required), then click **Request
changes**. The element returns to the owner as **Changes requested** with your
note; they revise and resubmit, which re-runs validation and comes back to the
queue. Be specific — the note is the only thing the owner sees.

### Re-run validation

**Re-run validation** re-executes the automated checks on demand — useful if the
underlying data or referenced building blocks changed since submission.

## What to check as a reviewer

The machine already guaranteed the data is valid, complete and self-contained. Your
judgement covers what it can't:

- Is the science/method sound and correctly described?
- Is it a genuine, non-duplicate contribution to the community?
- Are attribution and citations appropriate?
- Does the (optional) runnable check actually produce sensible behaviour?

## How it works under the hood

- Ownership, sharing and publication state live in the platform-only
  `tvbo.model_share` model — never on the schema entities, so nothing leaks into
  the validated YAML.
- `publication_state` (`draft → in_review → changes_requested → published`) is the
  source of truth; the legacy `visibility` field is a computed mirror
  (`shared` iff `published`) that the gallery, Knowledge Graph and API read.
- Public visibility is the union of three grants: the owner, named peer-to-peer
  collaborators (`shared_user_ids`), and — once published — everyone.
- Every transition is written to `tvbo.publication_review` for audit.

See the maintainer note in the repository (`docs/publication-workflow.md`) for the
full architecture and extension points (e.g. enforcing the runnable smoke-test or
requiring multiple approvals).
