# Replay Governance Traceability Contract

## Purpose

`tests/replay_governance_traceability_contract.py` defines the contract-backed
link between replay governance decision records and replay governance approval
records.

The contract makes governance approvals attributable to known governance
decisions. It also makes orphan approvals detectable. It does not introduce
workflow automation, waiver behavior, override behavior, replay behavior
changes, acceptance changes, report changes, dashboard changes, scorecard
changes, or threshold changes.

## Boundaries

The traceability contract owns:

- canonical governance decision reference format
- decision reference validation against the governance registry
- approval-to-decision linkage validation
- audit-only traceability summaries

The traceability contract does not own:

- replay execution
- replay classification
- drift bucket or owner bucket vocabularies
- governance decision policy
- approval status policy
- protected replay assertions
- dashboards, reports, or scorecards
- waiver or override semantics
- automated approval workflow
- acceptance thresholds

## Identifier Format

The canonical governance decision identifier is built from the AV3 registry key:

```text
drift_bucket:owner_bucket:category:severity
```

The field order is authoritative:

```text
(
    "drift_bucket",
    "owner_bucket",
    "category",
    "severity",
)
```

Example:

```text
structural_drift:speaker_drift:speaker:critical
```

This identifier is a traceability key only. It does not execute policy or decide
test outcomes.

## Linkage Model

An approval record links to a governance decision through:

```text
approval_record["decision_reference"]
```

A reference is valid when it exactly matches one canonical identifier from
`tests/replay_governance_registry.py::replay_governance_registry()`.

Unknown references are considered orphan approvals for audit purposes. They are
not waivers, overrides, test failures, or workflow states.

## Helpers

`governance_decision_reference(record)` returns the canonical identifier for one
registry record.

`governance_decision_reference_set(registry=None)` returns all canonical
identifiers for a registry.

`is_valid_governance_decision_reference(decision_reference, registry=None)`
validates whether a reference resolves to a known governance decision.

`approval_references_unknown_decision(approval_record, registry=None)` returns
whether a valid approval record references an unknown governance decision.
Invalid approval records return `False` here because shape errors are owned by
the approval contract.

## Audit Model

`replay_governance_traceability_audit(approval_records, registry=None)` returns
an audit-only payload:

| Field | Meaning |
|---|---|
| `governed_decisions` | Sorted list of all decision references in the registry. |
| `approved_decisions` | Sorted list of governed decisions with `APPROVED` approval records. |
| `pending_decisions` | Sorted list of governed decisions with `PENDING_REVIEW` approval records. |
| `orphan_approvals` | Approval records with valid approval shape but unknown decision references. |
| `invalid_approvals` | Approval records that fail the AV4 approval shape contract. |

Rejected approvals are valid approval metadata, but they are not counted as
approved or pending decisions in the audit summary.

The audit payload is informational only. It does not enforce coverage, block
acceptance, alter governance decisions, or trigger any workflow.

## Reproduction

```powershell
python -m pytest tests/test_replay_governance_traceability_contract.py -q
```
