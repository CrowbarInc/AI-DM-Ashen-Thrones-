# Replay Governance Contract

## Purpose

`tests/replay_governance_contract.py` is the contract-backed governance surface
for replay drift decision vocabulary and governance record shape.

It makes accepted-vs-blocked governance language explicit without changing
replay execution, replay classification, owner attribution, reports, dashboards,
scorecards, thresholds, pytest behavior, or protected replay acceptance.

**Canonical governance inventory:** [`docs/convergence_ci_inventory.md`](../convergence_ci_inventory.md) (convergence CI seams and replay-adjacent governance navigation).

## Boundaries

The contract owns:

- governance decision vocabulary
- governance record required fields
- lightweight shape validation helpers

The contract does not own:

- replay execution
- protected replay assertions
- drift classification behavior
- drift bucket or owner bucket vocabularies
- classifier categories or severities
- dashboard/report rendering
- scorecard generation
- acceptance thresholds
- runtime gameplay behavior

## Ownership

| Surface | Owner |
|---|---|
| Governance vocabulary | `tests/replay_governance_contract.py` |
| Governance record shape | `tests/replay_governance_contract.py` |
| Protected replay acceptance set | `docs/testing/protected_replay_manifest.md` |
| Replay failure classifier taxonomy | `tests/failure_classification_contract.py` |
| Owner drift bucket taxonomy | `tests/helpers/replay_drift_taxonomy.py` |
| Stability reporting schema | `tests/stability_reporting_contract.py` |
| Replay reports and artifacts | `tests/helpers/failure_dashboard_report.py` |

## Non-Goals

- Do not infer pass/fail behavior from governance records.
- Do not promote advisory or report-only drift into blocking drift.
- Do not add new thresholds.
- Do not add new protected replay scenarios or protected observation fields.
- Do not change existing report, dashboard, or scorecard output.
- Do not replace existing classifier, taxonomy, or stability contracts.

## Vocabulary

| Decision | Meaning |
|---|---|
| `ACCEPTED` | Current policy permits the drift condition for acceptance purposes. This does not mean the drift is desirable. |
| `BLOCKED` | Current policy treats the drift condition as acceptance-blocking when it violates an existing protected replay invariant. |
| `REVIEW_REQUIRED` | Current policy says the drift condition should be investigated or monitored before any future promotion to blocking policy. |

Authoritative constant:

```text
ALLOWED_REPLAY_GOVERNANCE_DECISIONS = {
    "ACCEPTED",
    "BLOCKED",
    "REVIEW_REQUIRED",
}
```

## Record Shape

Required governance record fields:

| Field | Meaning |
|---|---|
| `drift_bucket` | Existing measurement drift bucket, such as `structural_drift`, `semantic_drift`, or `exact_drift`. |
| `owner_bucket` | Existing owner drift bucket, such as `route_drift`, `speaker_drift`, or `replay_drift_unclassified`. |
| `category` | Existing classifier category, such as `route`, `speaker`, `fallback`, `emission`, or `projection`. |
| `severity` | Existing classifier severity, such as `critical`, `high`, `medium`, or `low`. |
| `governance_decision` | One of `ACCEPTED`, `BLOCKED`, or `REVIEW_REQUIRED`. |
| `governance_reason` | Short explanation of the governance decision. |
| `policy_source` | Document or contract that supports the decision. |

Authoritative constant:

```text
REQUIRED_REPLAY_GOVERNANCE_RECORD_FIELDS = {
    "drift_bucket",
    "owner_bucket",
    "category",
    "severity",
    "governance_decision",
    "governance_reason",
    "policy_source",
}
```

## Validation Helpers

`is_valid_governance_decision(value)` validates only whether a value belongs to
the governance decision vocabulary.

`governance_record_shape_errors(record)` validates only:

- the record is a mapping
- all required governance fields are present
- `governance_decision` is canonical
- `governance_reason` and `policy_source` are non-empty strings when present

The helper intentionally does not validate drift bucket values, owner bucket
values, classifier categories, severities, policy semantics, or acceptance
outcomes.

## Reproduction

```powershell
python -m pytest tests/test_replay_governance_contract.py -q
```
