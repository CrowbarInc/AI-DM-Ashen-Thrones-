# Replay Governance Approval Contract

## Purpose

`tests/replay_governance_approval_contract.py` defines the contract-backed shape
for replay governance approval and review metadata.

The contract makes approval records representable and standardized. It does not
create an approval workflow, waiver behavior, override behavior, replay behavior
change, acceptance change, threshold change, reporting change, or dashboard
change.

## Boundaries

The approval contract owns:

- approval status vocabulary
- approval record required fields
- approval record optional fields
- lightweight approval metadata validation helpers

The approval contract does not own:

- replay execution
- replay classification
- drift bucket or owner bucket vocabularies
- governance decision mappings
- protected replay assertions
- dashboards, reports, or scorecards
- acceptance thresholds
- waiver or override semantics
- automated review workflow

## Ownership

| Surface | Owner |
|---|---|
| Approval status vocabulary | `tests/replay_governance_approval_contract.py` |
| Approval metadata shape | `tests/replay_governance_approval_contract.py` |
| Governance decision vocabulary | `tests/replay_governance_contract.py` |
| Governance decision registry | `tests/replay_governance_registry.py` |
| Protected replay acceptance scope | `docs/testing/protected_replay_manifest.md` |
| Replay failure classification | `tests/failure_classification_contract.py` |

## Non-Goals

- Do not treat `APPROVED` as a replay pass.
- Do not treat `REJECTED` as a replay failure.
- Do not treat `PENDING_REVIEW` as a pytest state.
- Do not use approval records to waive protected replay failures.
- Do not use approval records to override governance decisions.
- Do not emit approval records from replay helpers, dashboards, reports, or scorecards in this contract block.

## Vocabulary

| Status | Meaning |
|---|---|
| `APPROVED` | A reviewer has approved the referenced governance decision or record for documentary purposes. |
| `REJECTED` | A reviewer has rejected the referenced governance decision or record for documentary purposes. |
| `PENDING_REVIEW` | The referenced governance decision or record has not completed review. |

Authoritative constant:

```text
ALLOWED_REPLAY_GOVERNANCE_APPROVAL_STATUSES = {
    "APPROVED",
    "REJECTED",
    "PENDING_REVIEW",
}
```

## Approval Record Schema

Required fields:

| Field | Meaning |
|---|---|
| `approval_status` | One of `APPROVED`, `REJECTED`, or `PENDING_REVIEW`. |
| `decision_reference` | String reference to the governance decision or registry record under review. |
| `approval_reason` | Short explanation of the approval status. |
| `reviewed_by` | Reviewer identifier or governance group label. |
| `review_date` | Review date string. The contract does not enforce a date parser. |
| `approval_source` | Document, audit, issue, or other source backing the review metadata. |

Optional fields:

| Field | Meaning |
|---|---|
| `notes` | Free-form string notes. |

Authoritative constants:

```text
REQUIRED_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS = {
    "approval_status",
    "decision_reference",
    "approval_reason",
    "reviewed_by",
    "review_date",
    "approval_source",
}

OPTIONAL_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS = {
    "notes",
}
```

## Validation Helpers

`is_valid_approval_status(value)` validates only whether a value belongs to the
approval status vocabulary.

`approval_record_shape_errors(record)` validates only:

- the record is a mapping
- all required approval fields are present
- `approval_status` is canonical
- required text fields are non-empty strings when present
- `notes` is a string when present
- no unknown approval fields are present

The helper intentionally does not validate workflow state, reviewer identity,
date format, policy correctness, waiver eligibility, override eligibility,
replay acceptance, or governance decision semantics.

## Reproduction

```powershell
python -m pytest tests/test_replay_governance_approval_contract.py -q
```
