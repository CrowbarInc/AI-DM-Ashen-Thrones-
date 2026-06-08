# Replay Governance Authority

## Purpose

This document declares the canonical replay governance authority hierarchy
created during Cycle AV. It is governance-only. It does not change replay
execution, replay classification, diagnostics, dashboards, reports, scorecards,
thresholds, protected replay coverage, pytest behavior, or acceptance outcomes.

## Governance Architecture

Replay governance is intentionally separate from replay execution and replay
classification.

Replay execution answers:

```text
What happened during a replay?
```

Replay classification answers:

```text
What kind of drift or failure was observed, where is it likely owned, and how
should it be investigated?
```

Replay governance answers:

```text
What governance decision, approval metadata, and traceability record describe
that already-classified drift under current policy?
```

Governance modules must not become replay runners, classifiers, dashboards,
scorecard writers, threshold engines, waiver systems, or workflow automation.

## Authority Hierarchy

| Level | Authority | Owns | Does Not Own |
|---:|---|---|---|
| 1 | `tests/replay_governance_contract.py` | Governance decision vocabulary and governance decision record shape. | Drift classification, owner buckets, reports, replay pass/fail, approval metadata. |
| 2 | `tests/replay_governance_registry.py` | Static mapping records from existing drift classes to governance decisions. | New policy invention, replay classification, alternate decision vocabulary, acceptance behavior. |
| 3 | `tests/replay_governance_approval_contract.py` | Approval status vocabulary and approval metadata record shape. | Waivers, overrides, workflow automation, replay acceptance. |
| 4 | `tests/replay_governance_traceability_contract.py` | Canonical decision identifier format, approval-to-decision reference validation, and audit-only traceability summaries. | Approval workflow, enforcement, dashboard/report emission, acceptance gates. |
| 5 | Audit/reporting consumers | May read governance contracts for documentation, audits, or future reporting. | Must not redefine vocabulary, registry authority, identifiers, approval semantics, thresholds, or acceptance behavior. |

If two sources appear to disagree, the lower-numbered authority wins for its
owned surface. For example, governance decisions must use the Level 1 vocabulary;
registry entries must satisfy the Level 1 record shape; approval references must
use the Level 4 identifier format.

## Ownership Boundaries

### Level 1: Governance Contract

`tests/replay_governance_contract.py` is the sole authority for:

- `ACCEPTED`
- `BLOCKED`
- `REVIEW_REQUIRED`
- required governance decision record fields
- decision record shape validation

No other module should define alternate replay governance decision vocabulary.

### Level 2: Governance Registry

`tests/replay_governance_registry.py` is the sole authority for static
governance decision mapping records.

Registry records may summarize existing policy intent. They must not introduce
new blocking behavior, new thresholds, or alternate acceptance logic.

### Level 3: Approval Contract

`tests/replay_governance_approval_contract.py` is the sole authority for:

- `APPROVED`
- `REJECTED`
- `PENDING_REVIEW`
- approval metadata required fields
- approval metadata optional fields
- approval metadata shape validation

Approval records are documentation metadata only. Approval records do not waive
protected replay failures and do not override governance decisions.

### Level 4: Traceability Contract

`tests/replay_governance_traceability_contract.py` is the sole authority for the
canonical governance decision reference:

```text
drift_bucket:owner_bucket:category:severity
```

Traceability helpers detect unknown approval references and provide audit-only
summaries. They do not enforce workflow state or replay acceptance.

### Level 5: Audit / Reporting Consumers

Future audits, docs, or reporting consumers may read governance surfaces, but
they must preserve the hierarchy above. Consumers must not create competing
vocabularies, registries, identifiers, approval schemas, waivers, overrides, or
hidden gates.

## Extension Rules

Allowed:

- Add governance registry entries in `tests/replay_governance_registry.py` when
  they encode existing reviewed policy sources.
- Add approval records in future documentation or audit artifacts when they
  satisfy `tests/replay_governance_approval_contract.py`.
- Add policy sources to registry records when the source already documents
  existing governance intent.
- Add audit-only tests that verify governance records remain contract-valid and
  traceable.
- Add reporting consumers that read governance records without changing report
  pass/fail behavior or introducing hidden thresholds.

Disallowed:

- Alternate governance decision vocabularies.
- Alternate governance registry authorities.
- Alternate decision identifier formats.
- Approval-based replay overrides.
- Approval-based acceptance waivers.
- Workflow automation that changes replay behavior or acceptance.
- New thresholds hidden inside governance helpers.
- Imports from replay runners, runtime game modules, dashboards, or scorecard
  writers into Level 1 through Level 4 governance authorities.

## Maintenance Rules

- Keep governance authorities import-light and test-side.
- Extend vocabulary only in the Level 1 or Level 3 contract modules, with
  focused contract tests and documentation updates.
- Extend registry mappings only in the Level 2 registry, with synchronization
  tests proving each record satisfies the Level 1 contract.
- Extend approval metadata only in the Level 3 approval contract, with tests
  proving shape and status validity.
- Extend identifier or traceability rules only in the Level 4 traceability
  contract, with tests proving registry identifiers remain unique and approval
  references resolve.
- Keep replay behavior, classifier behavior, reporting output, thresholds, and
  protected replay assertions outside this governance hierarchy.

## Deferred Work

Deferred explicitly:

- Approval workflow automation.
- Governance UI or report integration.
- Waiver systems.
- Override systems.
- Acceptance-policy automation.
- Threshold promotion.
- Replay pass/fail integration.

Future work in any deferred area requires a separately reviewed block and must
not be smuggled into governance contract maintenance.
