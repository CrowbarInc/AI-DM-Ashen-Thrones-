# Replay Governance Registry

## Purpose

`tests/replay_governance_registry.py` centralizes the current governance intent
for replay drift classes. It maps existing drift buckets, owner buckets,
classifier categories, and severities to AV2 governance decisions:

- `ACCEPTED`
- `BLOCKED`
- `REVIEW_REQUIRED`

The registry makes accepted-vs-blocked intent discoverable without changing
replay execution, replay classification, reports, dashboards, scorecards,
thresholds, pytest behavior, or protected replay acceptance.

**Canonical governance inventory:** [`docs/convergence_ci_inventory.md`](../convergence_ci_inventory.md) (convergence CI seams and replay-adjacent governance navigation).

## Boundaries

The registry owns:

- static governance decision records
- read-only registry access
- read-only filtering by drift bucket
- read-only filtering by owner bucket

The registry does not own:

- replay execution
- replay assertion behavior
- replay failure classification
- drift bucket vocabulary
- owner bucket vocabulary
- classifier category or severity vocabulary
- report or dashboard rendering
- scorecard generation
- protected replay coverage
- acceptance thresholds

## Source Authority

The registry encodes existing intent from:

| Source | Role |
|---|---|
| `audits/cycle_av_governance_registry_inventory.md` | AV1 mapping matrix and gap inventory |
| `docs/testing/protected_replay_manifest.md` | Protected replay acceptance scope and advisory/report-only addenda |
| `docs/audits/cycle_k_block_k4_drift_threshold_policy_2026-05-26.md` | Existing threshold policy classes and non-threshold decisions |
| `tests/replay_governance_contract.py` | Governance decision vocabulary and record shape |
| `tests/stability_reporting_contract.py` | Stability report-only/advisory-only boundary |

The registry should not invent new policy. New blocking decisions require a
separate policy/manifest update before this registry is changed.

## Registry Records

Each record uses the AV2 governance contract shape:

| Field | Meaning |
|---|---|
| `drift_bucket` | Existing drift class or documented diagnostic drift class. |
| `owner_bucket` | Existing owner-oriented drift bucket. |
| `category` | Existing classifier category or documented advisory category. |
| `severity` | Existing classifier severity or documented severity hint. |
| `governance_decision` | One of `ACCEPTED`, `BLOCKED`, or `REVIEW_REQUIRED`. |
| `governance_reason` | Short explanation of existing governance intent. |
| `policy_source` | Source document or contract justifying the record. |

The registry identity key is:

```text
(drift_bucket, owner_bucket, category, severity)
```

Tests assert that keys are unique and records satisfy the AV2 contract.

## Difference From Classification

Replay classification answers:

```text
What kind of drift or failure is this, where is it likely owned, and how should
an operator investigate it?
```

Replay governance answers:

```text
Given the existing policy, is this drift accepted for acceptance purposes,
blocked when asserted by protected replay, or review-required?
```

The registry does not call the classifier, does not classify live drift rows,
and does not decide test pass/fail. It records governance intent only.

## Query Helpers

`replay_governance_registry()` returns the static registry in deterministic
order.

`governance_records_for_bucket(drift_bucket)` returns records matching a drift
bucket.

`governance_records_for_owner_bucket(owner_bucket)` returns records matching an
owner drift bucket.

These helpers are read-only and return copies of registry records.

## Reproduction

```powershell
python -m pytest tests/test_replay_governance_registry.py -q
```
