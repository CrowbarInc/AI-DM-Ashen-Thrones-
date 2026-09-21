# Campaign

Campaign: RC-11 & RC-13 Unresolved Root-Cause Investigation
Identifier: `rc11_rc13_unresolved_root_cause_investigation_20260919`
Date: 2026-09-19
Generated: 2026-09-19T18:00:00Z
Purpose: Determine the root causes of RC-11 and RC-13 without repairing behavior or deciding RC-10/RC-21.

# Executive Summary

RC-11 and RC-13 are both classified STALE_EXPECTATION with HIGH confidence. RC-11 is a pre-attribution whole-dictionary comparator; current and legacy paths emit identical accepted text and previews, while the current helper additionally records governed mutation write-site metadata. RC-13 is a historical lineage cap that predates five correctly projected mutation events in two newer governed categories. Both reproduced identically 10/10 times, remained isolated under bounded order checks, and the full suite failure set was unchanged.

Objective status: `ACHIEVED`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No changes in this category.

## Tooling changes

- Added a read-only deterministic trace builder for RC-11 and RC-13 evidence.

## Documentation changes

- Added the canonical investigation report and case-specific root-cause narratives.

## Generated artifacts

- Added pre/post JUnit, 20 isolated-run JUnit files, four order-check JUnit files, structured traces, registry, and recommendations.

# What Was Tested

- **Focused tests:** RC-11 and RC-13 each reproduced identically in 10 of 10 isolated executions.
- **Broader relevant tests:** Four bounded module/family checks exposed only their targeted known failure.
- **Full suite:** Pre and post: 6,448 collected, 6,342 passed, 7 failed, 99 skipped; exact failure node set unchanged.
- **Runtime validation:** The existing deterministic 25-turn replay was observed without changing runtime behavior.
- **Model/runtime boundary:** No external model invocation occurred; the replay used its deterministic GPT stub.
- **New regressions:** None.
- **Pre-existing failures:** Seven remain: one unrelated governance-document failure plus RC-10, RC-11, RC-13, and three RC-21 tests.
- **Self-contained bundle review:** PASS: canonical report, structured traces, root-cause narratives, recommendations, and pre/post JUnit are bundled.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Authorize RC-11 expectation modernization in a separate task.
- Authorize RC-13 diagnostic-profile recalibration in a separate task.
- RC-10 and RC-21 remain separate policy decisions.

# Known Problems / Unresolved Findings

## Campaign-specific

- None reported.

## Pre-existing baseline

- The seven-test baseline remains deliberately unrepaired.

# Missing Concepts / Future Capabilities

- Repair implementation and policy resolution are out of scope.

# What This Campaign Does NOT Prove

- That the recommended changes are already implemented.
- Which policy RC-10 or RC-21 should adopt.
- That aggregate mutation limits outside this diagnostic should change.

# Recommended Next Step

Review and authorize separate narrow expectation-maintenance changes for RC-11 and RC-13.

# Review Bundle Contents

Bundle file count: `14`
Bundle ZIP size: `000000311898` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/rc11_rc13_unresolved_root_cause_investigation.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/rc11_rc13_unresolved_root_cause_investigation.md`.
- `support/artifacts/unresolved_root_cause_investigation/investigation_registry.json`: Records classifications, confidence, root causes, and scope boundaries. Canonical source: `artifacts/unresolved_root_cause_investigation/investigation_registry.json`.
- `support/artifacts/unresolved_root_cause_investigation/rc11_trace.json`: Shows the exact single-path metadata divergence. Canonical source: `artifacts/unresolved_root_cause_investigation/rc11_trace.json`.
- `support/artifacts/unresolved_root_cause_investigation/rc11_trace.md`: Explains candidate, emission, preview, and attribution equivalence. Canonical source: `artifacts/unresolved_root_cause_investigation/rc11_trace.md`.
- `support/artifacts/unresolved_root_cause_investigation/rc13_turn_trace.json`: Contains all 25 turns and cumulative lineage frequencies. Canonical source: `artifacts/unresolved_root_cause_investigation/rc13_turn_trace.json`.
- `support/artifacts/unresolved_root_cause_investigation/rc13_turn_trace.md`: Identifies first subtype and aggregate divergences. Canonical source: `artifacts/unresolved_root_cause_investigation/rc13_turn_trace.md`.
- `support/artifacts/unresolved_root_cause_investigation/rc13_root_cause.md`: Documents profile provenance and healthy replay evidence. Canonical source: `artifacts/unresolved_root_cause_investigation/rc13_root_cause.md`.
- `support/artifacts/unresolved_root_cause_investigation/recommended_actions.json`: Defines future narrow actions and preserved contracts. Canonical source: `artifacts/unresolved_root_cause_investigation/recommended_actions.json`.
- `support/artifacts/unresolved_root_cause_investigation/recommended_actions.md`: Readable recommendations without implementation. Canonical source: `artifacts/unresolved_root_cause_investigation/recommended_actions.md`.
- `support/artifacts/unresolved_root_cause_investigation/pre_investigation_suite.xml`: Authoritative starting baseline. Canonical source: `artifacts/unresolved_root_cause_investigation/pre_investigation_suite.xml`.
- `support/artifacts/unresolved_root_cause_investigation/post_investigation_suite.xml`: Confirms the exact failure set remained unchanged. Canonical source: `artifacts/unresolved_root_cause_investigation/post_investigation_suite.xml`.
- `support/tools/build_unresolved_root_cause_investigation.py`: Reproduces structured evidence without altering runtime behavior. Canonical source: `tools/build_unresolved_root_cause_investigation.py`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
