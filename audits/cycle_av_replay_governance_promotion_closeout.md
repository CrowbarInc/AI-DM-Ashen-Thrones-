# Cycle AV Replay Governance Promotion Closeout

## Summary

Cycle AV promoted replay drift governance from distributed documentation into a
contract-backed, traceable governance hierarchy. The work is governance-only.
It does not change replay execution, replay classification, diagnostics,
dashboards, reports, scorecards, thresholds, protected replay coverage, pytest
selection, or acceptance behavior.

## Completed Blocks

| Block | Deliverable | Result |
|---|---|---|
| AV1 | `audits/cycle_av_governance_registry_inventory.md` | Inventoried existing governance sources, vocabulary, record shape, mapping matrix, gaps, and recommended authority location. |
| AV2 | `tests/replay_governance_contract.py`; `tests/test_replay_governance_contract.py`; `docs/testing/replay_governance_contract.md` | Created the canonical governance decision vocabulary and governance record shape contract. |
| AV3 | `tests/replay_governance_registry.py`; `tests/test_replay_governance_registry.py`; `docs/testing/replay_governance_registry.md` | Centralized existing governance intent in a static registry with read-only lookup helpers. |
| AV4 | `tests/replay_governance_approval_contract.py`; `tests/test_replay_governance_approval_contract.py`; `docs/testing/replay_governance_approval_contract.md` | Standardized approval/review metadata shape without workflow, waiver, or override behavior. |
| AV5 | `tests/replay_governance_traceability_contract.py`; `tests/test_replay_governance_traceability_contract.py`; `docs/testing/replay_governance_traceability_contract.md` | Added canonical decision references, approval-to-decision validation, orphan detection, and audit-only traceability summaries. |
| AV6 | `docs/testing/replay_governance_authority.md`; `tests/test_replay_governance_authority.py`; this closeout | Declared and test-locked the governance authority hierarchy. |

## Governance Hierarchy

| Level | Authority | Ownership Summary |
|---:|---|---|
| 1 | `tests/replay_governance_contract.py` | Governance decision vocabulary and governance record shape. |
| 2 | `tests/replay_governance_registry.py` | Static governance decision mappings based on existing policy sources. |
| 3 | `tests/replay_governance_approval_contract.py` | Approval status vocabulary and approval metadata shape. |
| 4 | `tests/replay_governance_traceability_contract.py` | Decision reference format, approval-reference validation, and audit-only traceability summaries. |
| 5 | Audit/reporting consumers | May read governance surfaces but must not redefine or bypass Levels 1 through 4. |

Canonical decision identifier:

```text
drift_bucket:owner_bucket:category:severity
```

## Ownership Summary

Replay governance now has distinct owners:

- **Decision vocabulary:** `tests/replay_governance_contract.py`
- **Decision registry:** `tests/replay_governance_registry.py`
- **Approval metadata:** `tests/replay_governance_approval_contract.py`
- **Traceability:** `tests/replay_governance_traceability_contract.py`
- **Authority hierarchy:** `docs/testing/replay_governance_authority.md`

Existing replay systems remain the owners of their original surfaces:

- Protected replay acceptance: `docs/testing/protected_replay_manifest.md` and
  existing protected replay tests.
- Replay failure classification: `tests/failure_classification_contract.py` and
  `tests/helpers/failure_classifier.py`.
- Owner drift taxonomy: `tests/helpers/replay_drift_taxonomy.py`.
- Stability reporting schema: `tests/stability_reporting_contract.py`.
- Replay report/artifact rendering: `tests/helpers/failure_dashboard_report.py`.

## Future Extension Guidance

Allowed extensions:

- Add registry entries in `tests/replay_governance_registry.py` when they encode
  existing reviewed policy sources.
- Add approval records in future audit/documentation artifacts when they satisfy
  `tests/replay_governance_approval_contract.py`.
- Add policy sources to existing registry records when they document existing
  governance intent.
- Add audit-only synchronization tests that verify records remain contract-valid
  and traceable.
- Add read-only reporting consumers that expose governance metadata without
  changing report pass/fail behavior or replay acceptance.

Required safeguards:

- Vocabulary changes belong only in the relevant contract module.
- Registry changes must remain static declarations and must satisfy the Level 1
  governance contract.
- Approval metadata changes must satisfy the Level 3 approval contract.
- Approval references must use the Level 4 canonical decision identifier.
- No governance helper may become a replay runner, classifier, dashboard writer,
  scorecard generator, threshold engine, waiver system, override system, or
  workflow automation layer.

## Drift Prevention

`tests/test_replay_governance_authority.py` verifies:

- governance decision vocabulary remains canonical
- registry records remain valid against the governance contract
- approval status vocabulary remains canonical
- approval records can reference registry identifiers while remaining valid
- traceability identifier format remains canonical
- registry identifiers remain unique

This is an audit-only lock. It does not exercise replay execution or alter any
replay behavior.

## Deferred Items

Deferred explicitly:

- Approval workflow automation.
- Governance UI/report integration.
- Waiver systems.
- Override systems.
- Acceptance-policy automation.
- Threshold promotion or threshold enforcement.
- Replay pass/fail integration.
- Dashboard/report/scorecard output integration.

Any deferred item requires a separately reviewed future cycle. None should be
introduced through maintenance of the governance contracts, registry, approval
metadata, or traceability helpers.

## Validation

Focused validation for AV6:

```powershell
python -m pytest tests/test_replay_governance_authority.py -q
```

Recommended governance stack validation:

```powershell
python -m pytest tests/test_replay_governance_contract.py tests/test_replay_governance_registry.py tests/test_replay_governance_approval_contract.py tests/test_replay_governance_traceability_contract.py tests/test_replay_governance_authority.py -q
```

## Closeout Statement

Cycle AV is complete when the governance hierarchy document, authority
synchronization test, and closeout audit are present and focused governance tests
pass. Replay behavior, classification behavior, reporting behavior, thresholds,
and acceptance behavior remain unchanged.
