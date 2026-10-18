# PR-CF Triage Report

MODE: BROAD REGRESSION FAILURE TRIAGE
LIVE CALLS: 0

PR-CE inherited decision: E - OTHER REGRESSION.

## Summary

The 202 PR-CE broad failures are best explained by multiple overlapping clusters, not by one demonstrated PR-CE subjective-classifier regression. The absent PR-CE `broad.xml` prevented direct XML extraction, but PR-CF preserved the exact 202/65 inventory shape in `lastfailed_diagnostic.xml`; the inventory marks the 161 PR-CF setup-noise records separately.

## Largest Clusters

- `tests/test_turn_pipeline_shared.py`: 33
- `tests/test_explicit_world_action_social_lock_override.py`: 9
- `tests/test_exploration_resolution.py`: 7
- `tests/test_investigation_result_provenance_non_invention.py`: 7
- `tests/test_later_turn_untargeted_observation_restacking.py`: 7
- `tests/test_golden_replay_structural_invariants.py`: 6

## Diagnosis

Root-cause clusters identified: 6.

The highest-priority finding is infrastructure: PR-CF reproduced the Windows Python 3.12 TestClient/socketpair accept hang during representative HTTP rerun. That blocks reliable diagnosis of HTTP-heavy clusters until stabilized.

Among non-noise assertion signatures, the broad failures split into response projection/fallback contract drift, social speaker/reply planning drift, governance/prompt expectation drift, exploration/investigation projection risk, and reactive-player harness drift.

Authority integrity assessment: no confirmed durable authority bypass in PR-CF, but speaker contract mismatch, refusal-vs-unknown changes, and social absence behavior are authority-adjacent and must be repaired or deliberately reconciled before live dialogue validation.

Runtime impact assessment: likely medium-high for ordinary gameplay in social dialogue and observation/investigation flows, unknown for HTTP-heavy clusters until TestClient is stable, low direct runtime impact for governance-only failures.

PR-CF decision: B - MULTIPLE INDEPENDENT REGRESSIONS.

Recommended next step: bounded repair cycle for deterministic HTTP/TestClient stability, then rerun representative turn-pipeline/social relevance/explicit-world-action tests before touching behavior.
