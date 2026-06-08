# Replay Drift Governance Registry Inventory

Cycle AV scope: governance inventory only. This document does not change replay
execution, protected replay coverage, drift classification, owner buckets,
thresholds, reports, diagnostics, or acceptance behavior.

## Existing Governance Sources

| Source | Responsibility | Governance Type | Notes |
|---|---|---|---|
| `docs/testing/protected_replay_manifest.md` | Declares the canonical protected replay set, protected observation field paths, scenario status, and replay reporting addenda. | Acceptance and documentation authority | Defines `PROTECTED`, `SUPPORTING`, `ADVISORY`, and `DEPRECATED`; states that protected replay pass/fail is owned by existing golden replay tests and structural/semantic invariants. |
| `docs/audits/cycle_k_block_k4_drift_threshold_policy_2026-05-26.md` | Defines the current replay drift threshold policy and non-threshold policy classes. | Policy memo / acceptance intent | Defines `ACCEPTANCE_BLOCKING`, `WARNING`, `REPORT_ONLY`, and `FUTURE_MONITORING`; explicitly avoids new numeric thresholds. |
| `tests/failure_classification_contract.py` | Locks replay failure categories, owners, severities, tags, classification row fields, and dashboard evidence fields. | Schema and taxonomy contract | Governs classifier/dashboard row validity; does not decide replay pass/fail. |
| `tests/helpers/replay_drift_taxonomy.py` | Defines owner drift buckets and maps failure/rerun/stability signals to owner-oriented drift buckets. | Owner drift taxonomy | Adds attribution and reporting vocabulary only; owner drift buckets are not acceptance-blocking by themselves. |
| `tests/helpers/golden_replay_projection.py` | Defines protected observation fields, protected field drift buckets, and observed-turn projection. | Acceptance observation registry | Current field-level source for `structural_drift` and `semantic_drift`; runtime lineage remains diagnostic/read-side. |
| `tests/helpers/golden_replay.py` | Runs replay helpers, evaluates golden expectations, raises protected assertion failures, classifies exact/structural/semantic drift, and builds report-only scorecards. | Assertion and helper orchestration | Protected assertion failures already block through pytest; rerun scorecards are `report_only`. |
| `tests/helpers/failure_classifier.py` | Converts captured drift rows into classified failure rows with category, severity, owners, investigation target, evidence, and owner drift bucket. | Diagnostic classification | Explains failure locality after a drift row exists; classifier severity does not independently gate acceptance. |
| `tests/helpers/failure_dashboard_report.py` | Renders and writes protected replay failure reports, failure dashboards, rerun scorecards, owner drift trend/hotspot/risk artifacts, and stability artifacts. | Diagnostic reporting | Report artifacts expose owner drift and evidence; report generation must not become hidden acceptance logic. |
| `tests/stability_reporting_contract.py` | Locks long-session stability reporting schema, advisory/report-only flags, and stability reporting ownership boundaries. | Stability reporting governance | Defines `STABILITY_REPORTING_ADVISORY_ONLY = True` and `STABILITY_REPORTING_REPORT_ONLY = True`; no protected replay threshold ownership. |
| `docs/cycles/cycle_ar_replay_drift_classification_recon.md` | Describes Cycle AR classification promotion plan and guardrails. | Replay governance documentation | Confirms owner drift reporting can proceed without replay expansion or pass/fail changes. |
| `audits/cycle_au_golden_replay_owner_mapping.md` | Maps golden replay ownership across hard-fail orchestration, projection, diagnostics/reporting, and drift taxonomy. | Ownership documentation | Useful source for future single-authority placement; not executable policy. |

## Governance Vocabulary

`ACCEPTED`

A drift condition that current policy permits for acceptance purposes. This
includes diagnostic or report-only drift that does not correspond to an existing
protected assertion failure. `ACCEPTED` does not mean desirable; it means the
current governance sources do not make it acceptance-blocking.

`BLOCKED`

A drift condition that violates an existing declared protected replay invariant.
Current behavior already blocks these through protected replay pytest assertions.
This vocabulary does not add new blocking cases.

`REVIEW_REQUIRED`

A drift condition that current policy says should be surfaced for investigation
or future monitoring, but which is not safe to promote into acceptance blocking
without more evidence, explicit review, and manifest/policy updates.

## Governance Decision Record

Proposed documentation/schema shape only. No runtime or test code consumes this
record today.

| Field | Meaning |
|---|---|
| `drift_bucket` | Existing measurement bucket, such as `structural_drift`, `semantic_drift`, or `exact_drift`. |
| `owner_bucket` | Existing owner-oriented bucket, such as `route_drift`, `speaker_drift`, `fallback_drift`, or `replay_drift_unclassified`. |
| `category` | Existing classifier category, such as `route`, `speaker`, `fallback`, `emission`, `projection`, or `sanitizer`. |
| `severity` | Existing classifier severity, such as `critical`, `high`, `medium`, or `low`. |
| `governance_decision` | One of `ACCEPTED`, `BLOCKED`, or `REVIEW_REQUIRED`. |
| `governance_reason` | Short prose explaining why the current policy assigns that decision. |
| `policy_source` | Source document or contract that justifies the decision. |

Example shape:

```text
drift_bucket: structural_drift
owner_bucket: speaker_drift
category: speaker
severity: critical
governance_decision: BLOCKED
governance_reason: Existing protected speaker invariant mismatch blocks when asserted by a protected replay scenario.
policy_source: docs/testing/protected_replay_manifest.md; docs/audits/cycle_k_block_k4_drift_threshold_policy_2026-05-26.md
```

## Governance Mapping Matrix

| Classification | Current Policy Source | Acceptance Status | Review Status | Notes |
|---|---|---|---|---|
| `structural_drift` | `docs/testing/protected_replay_manifest.md`; `docs/audits/cycle_k_block_k4_drift_threshold_policy_2026-05-26.md`; `tests/helpers/golden_replay_projection.py` | `BLOCKED` only when it violates an existing protected assertion; otherwise `ACCEPTED` for acceptance purposes. | `REVIEW_REQUIRED` when structural evidence is diagnostic-only or unasserted. | Existing protected route, speaker, fallback, response-type, final-source, and ownership invariants already hard-fail through pytest. |
| `semantic_drift` | `docs/testing/protected_replay_manifest.md`; `docs/audits/cycle_k_block_k4_drift_threshold_policy_2026-05-26.md`; `tests/helpers/golden_replay_projection.py` | `BLOCKED` when it violates protected player-facing semantic invariants such as scaffold leakage or required useful output. | `REVIEW_REQUIRED` for semantic signals not tied to a protected assertion. | Protected semantic checks are predicate-level, not broad semantic similarity thresholds. |
| `exact_drift` | `docs/testing/protected_replay_manifest.md`; `docs/audits/cycle_k_block_k4_drift_threshold_policy_2026-05-26.md`; `tests/helpers/golden_replay.py` | `ACCEPTED` by default for protected acceptance; exact text comparison is opt-in. | `REVIEW_REQUIRED` only if future policy wants to promote a curated exact-text expectation. | Exact prose identity is report-only unless explicitly curated. |
| `route_drift` | `tests/helpers/replay_drift_taxonomy.py`; `docs/testing/protected_replay_manifest.md`; K4 policy memo | `BLOCKED` when the route field is an asserted protected invariant; otherwise `ACCEPTED`. | `REVIEW_REQUIRED` for unasserted route frequency or diagnostic route shifts. | Owner bucket attribution does not independently block. |
| `speaker_drift` | `tests/helpers/replay_drift_taxonomy.py`; protected replay manifest; K4 policy memo | `BLOCKED` when protected speaker ownership is asserted and violated; otherwise `ACCEPTED`. | `REVIEW_REQUIRED` for supporting speaker diagnostics outside protected scenarios. | Speaker failures are often high/critical diagnostically, but severity alone is not the gate. |
| `fallback_drift` | `tests/helpers/replay_drift_taxonomy.py`; protected replay manifest; K4 policy memo | `BLOCKED` for existing protected fallback source/family/timeframe constraints; otherwise `ACCEPTED`. | `REVIEW_REQUIRED` for non-asserted fallback telemetry shifts. | Fallback is legitimate in some canonical paths, so broad fallback occurrence is not blocked. |
| `ownership_drift` | `tests/helpers/replay_drift_taxonomy.py`; protected replay manifest; `tests/failure_classification_contract.py` | `BLOCKED` for declared protected ownership/source invariants such as canonical opening fallback ownership; otherwise `ACCEPTED`. | `REVIEW_REQUIRED` for owner bucket shifts that are reported but not protected. | Current owner buckets improve attribution without changing acceptance. |
| `emission_drift` | `tests/helpers/replay_drift_taxonomy.py`; K4 policy memo; protected replay manifest | `BLOCKED` when an existing protected final-emission, response-type, or final-source invariant is violated; otherwise `ACCEPTED`. | `REVIEW_REQUIRED` for standalone mutation or post-gate lineage evidence. | Mutation and repair evidence is diagnostic unless attached to a protected invariant. |
| `projection_drift` | `tests/helpers/replay_drift_taxonomy.py`; `tests/helpers/golden_replay_projection.py`; K4 policy memo | `BLOCKED` when a required protected observation cannot support an asserted protected field; otherwise `ACCEPTED`. | `REVIEW_REQUIRED` when projection health obscures diagnosis but no protected assertion is violated. | Projection health matters for diagnostics but should not silently expand acceptance behavior. |
| `lineage_drift` | `docs/testing/protected_replay_manifest.md`; `tests/helpers/replay_drift_taxonomy.py`; `tests/stability_reporting_contract.py` | `ACCEPTED` for protected acceptance today. | `REVIEW_REQUIRED` / future monitoring for repeated or worsening lineage signals. | Runtime lineage is diagnostic/read-side and explicitly excluded from protected drift unless promoted later. |
| `semantic_drift` owner bucket | `tests/helpers/replay_drift_taxonomy.py`; K4 policy memo | `BLOCKED` only for protected semantic/player-facing assertions; otherwise `ACCEPTED`. | `REVIEW_REQUIRED` for broader semantic degradation indicators. | Owner-bucket `semantic_drift` and measurement bucket `semantic_drift` can overlap but are separate surfaces. |
| `replay_drift_unclassified` | `tests/helpers/replay_drift_taxonomy.py`; K4 policy memo | `ACCEPTED` by default unless tied to an existing protected assertion. | `REVIEW_REQUIRED` when repeated unclassified drift reduces diagnostic confidence. | Catch-all bucket for exact text fingerprint and unknown drift. |
| Stability `stable` / `watch` / `degraded` | `tests/stability_reporting_contract.py`; `docs/testing/protected_replay_manifest.md` Cycle AT addendum | `ACCEPTED` for protected replay acceptance because stability artifacts are advisory/report-only. | `REVIEW_REQUIRED` for `watch` or `degraded` scorecards during operator review. | Stability reporting does not own acceptance thresholds. |

## Gaps

- There is no single executable or documentation-only registry that maps
  drift bucket, owner bucket, category, and severity to governance intent.
- Current governance vocabulary uses several nearby terms across sources:
  `PROTECTED`, `SUPPORTING`, `ADVISORY`, `ACCEPTANCE_BLOCKING`, `WARNING`,
  `REPORT_ONLY`, `FUTURE_MONITORING`, `report_only`, and `advisory_only`.
- Classifier severity is intentionally separate from acceptance behavior, but
  no central record shape makes that separation visible next to each drift row.
- Runtime lineage, stability status, and owner drift buckets are clearly
  advisory in docs, but the accepted-vs-review-required distinction is
  distributed across manifest addenda and contracts.
- Exact drift is supported by helper code but governed procedurally as opt-in
  and report-only; that intent is not represented in a registry.
- There is no drift waiver or approval metadata contract. This is acceptable for
  AV1 because the requested scope is visibility only, not approval workflow.

## Recommended Authority Location

Recommended future authority: `tests/replay_governance_contract.py`.

Rationale:

- It matches the existing pattern of `tests/failure_classification_contract.py`
  and `tests/stability_reporting_contract.py`.
- It can remain test-only and governance-only, avoiding production/runtime
  imports and preserving replay behavior.
- It can expose constants for the governance vocabulary and an allowed record
  field set without changing classifier output, dashboard rendering, or golden
  replay execution.
- It can later be paired with a prose companion section in
  `docs/testing/protected_replay_manifest.md` if policy needs human-readable
  publication.

Recommended future shape, if implemented in a later block:

- `ALLOWED_REPLAY_GOVERNANCE_DECISIONS = {"ACCEPTED", "BLOCKED", "REVIEW_REQUIRED"}`
- `REQUIRED_REPLAY_GOVERNANCE_RECORD_FIELDS`
- `replay_governance_registry_manifest()`
- Contract tests that verify vocabulary only, without importing replay runners
  or modifying classification/report artifacts.

Do not implement this authority in AV1. This inventory is the deliverable for
the current block.
