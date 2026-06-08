# Cycle AU Golden Replay Ownership Compression Closeout

## Executive Summary

Cycle AU compressed `tests/test_golden_replay.py` from a broad replay/golden hotspot into a thinner protected replay orchestrator. Synthetic projection, fallback/final-emission, diagnostics/report, and helper-contract assertions now live in narrower owner files. The golden replay file still owns protected end-to-end replay scenarios, live bridge assertions, and long-session acceptance/stability coverage.

No protected replay scenario was moved. No replay behavior, expected diagnostics/report text, protected replay observations, manifest semantics, long-session thresholds, or runtime/game code changed.

## Final Ownership Split

| Owner bucket | Current owner file(s) | Ownership after AU |
| --- | --- | --- |
| Golden replay orchestration | `tests/test_golden_replay.py` | Protected E2E replay scenarios, live replay/gate bridge checks, long-session acceptance and stability thresholds, protected diagnostic bridge. |
| Replay projection/schema/manifest | `tests/test_golden_replay_projection.py` | Synthetic projection contracts, protected observation registry/path representation, extraction registry parity, manifest parity, read-side fallback-family precedence, response-delta projection, sanitizer-lineage projection. |
| Fallback/final-emission projection | `tests/test_golden_replay_fallback_projection.py` | Synthetic fallback owner-bucket, final-emission metadata, runtime lineage, sealed/strict-social/visibility fallback, prepared-emission telemetry, and sanitizer/fallback split projection proofs. |
| Diagnostics/report ownership | `tests/test_failure_dashboard_report.py`, existing failure-classification tests | Synthetic protected failure report, drift bucket/report scorecard rendering and writer checks. Golden replay keeps only a thin protected failure bridge. |
| Helper contracts | `tests/test_golden_replay_helper_contracts.py` | Route/source/social structural expectation helper shapes, markdown report helper rendering, and golden assertion helper dotted-path/debug-message behavior. |
| Inventory/recon documentation | `cycle_au_golden_replay_ownership_compression_recon.md`, `audits/cycle_au_replay_assertion_family_inventory.md`, `audits/cycle_au_golden_replay_owner_mapping.md`, this file | Durable ownership map and AU closeout record. |

## Files Created During AU

- `cycle_au_golden_replay_ownership_compression_recon.md`
- `audits/cycle_au_replay_assertion_family_inventory.md`
- `audits/cycle_au_golden_replay_owner_mapping.md`
- `audits/cycle_au_golden_replay_ownership_compression_closeout.md`
- `tests/test_golden_replay_helper_contracts.py`
- `tests/test_golden_replay_fallback_projection.py`
- `tests/test_failure_dashboard_report.py`
- `tests/test_golden_replay_projection.py`

## What Remains In `tests/test_golden_replay.py`

- Protected golden replay scenarios:
  - directed NPC question
  - vocative override after prior continuity
  - wrong-speaker strict-social emission
  - thin answer/action outcome final-emission
  - sanitizer scaffold leakage
  - canonical opening fallback
  - lead follow-up with dialogue lock
  - frontier gate social-inquiry 25-turn structural stability
  - frontier gate social-inquiry resume persistence
  - frontier gate direct-intrusion diagnostic stability
  - scenario spine three-branch structural smoke
- Live replay bridge assertions:
  - protected diagnostic failure bridge
  - declared-alias dialogue-plan direct seam
  - canonical opening fallback direct seam
  - canonical opening fallback replay bridge
  - sanitizer lineage fields surviving protected replay paths
- Long-session summary, stability scorecard, rerun-drift, and continuity acceptance checks that still support protected replay orchestration and thresholds.

## What Moved To Owner Files

- Route/speaker helper output-shape contracts moved to `tests/test_golden_replay_helper_contracts.py`.
- The remaining golden assertion helper dotted-path/debug-message contract moved to `tests/test_golden_replay_helper_contracts.py` during AU7.
- Synthetic fallback/final-emission projection proofs moved to `tests/test_golden_replay_fallback_projection.py`.
- Synthetic diagnostics/report assertions moved to `tests/test_failure_dashboard_report.py`.
- Synthetic projection/schema/manifest assertions moved to `tests/test_golden_replay_projection.py`.

## Final Thinning In AU7

AU7 moved `test_golden_expectation_helper_supports_dotted_paths_and_debug_messages` from `tests/test_golden_replay.py` to `tests/test_golden_replay_helper_contracts.py`. This was helper-level assertion construction coverage, not a protected E2E replay scenario.

No other test movement was made in AU7. Remaining inline expectations in `tests/test_golden_replay.py` are scenario-specific protected replay expectations or bridge assertions where locality is useful.

## Validation Results

- `python -m pytest tests/test_golden_replay.py -q --tb=short`
  - Passed: 32 tests.
- `python -m pytest tests/test_golden_replay_projection.py tests/test_golden_replay_fallback_projection.py tests/test_failure_dashboard_report.py tests/test_golden_replay_helper_contracts.py -q --tb=short`
  - Passed: 54 tests.
- `python -m pytest -m golden_replay -q --tb=short`
  - Passed: 32 tests.
- `python tools/test_audit.py --check`
  - Failed with known `tests/test_inventory_governance.json` drift.
  - Reported `Test files: +0 added, -0 removed`.
  - Reported nodeid/file sets match; drift is in other generated inventory fields.
  - Governance inventory was not regenerated because AU7 did not intentionally update audited inventory.

## Guardrails Preserved

- Protected E2E replay tests stayed in `tests/test_golden_replay.py`.
- Long-session thresholds were not changed.
- Diagnostics/report text was not changed.
- Manifest/projection semantics were not changed.
- Runtime/game code was not changed.
- Expected replay observations were not changed.

## Remaining Notes

- `tests/test_golden_replay.py` still contains long-session summary and scorecard helper checks because those are coupled to golden replay acceptance thresholds and operator-facing stability reporting. They may be candidates for a future dedicated long-session/stability owner pass, but AU did not move them to avoid weakening the protected replay acceptance surface.
- The known `tools/test_audit.py --check` drift remains a separate governance inventory issue.
