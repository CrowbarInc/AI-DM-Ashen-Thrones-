# High-Confidence Validation Rationalization

Date: 2026-09-18

## Executive Summary

This campaign implements only high-confidence, low-risk authority corrections approved by the
Validation Portfolio Rationalization audit. It preserves execution, scoring, thresholds, mandatory
semantic gates, calibration, behavioral evidence, protected replay invariants, and historical truth.

## Approved Scope and Implementation Plan

| Family | Current -> target authority | Audit | Action | Expected test/baseline effect | Risk | Rollback |
|---|---|---|---|---|---|---|
| Historical BW/BZ closeout assertions | RELEASE_GATE -> HISTORICAL_ONLY | RETIRE, HIGH | Replace 16 obsolete root-path/prose assertions with two canonical provenance checks; ledger every retired node | 14 fewer collected nodes; 13 known failures removed as rationalization, not product repair | LOW: provenance path could be incomplete | Restore the two test modules from the retirement ledger/history |
| Automated playability | CAMPAIGN_GATE -> SUPPORTING_EVIDENCE | RECLASSIFY, HIGH | Correct current docs and registry authority; retain runner/evaluator output and all scoring/gates | No test-count or failure change | LOW: consumers may still overread raw `overall.passed` | Revert docs/registry/ledger only |
| Protected replay | RELEASE_GATE -> RELEASE_GATE with narrower claim | RECLASSIFY, HIGH | Rename CI presentation and correct current claim language to controlled structural replay | No execution, selection, test-count, or failure change | LOW: terminology-only | Revert labels/docs/registry notes |
| Behavioral gauntlet | SUPPORTING_EVIDENCE -> DIAGNOSTIC | CONSOLIDATE, HIGH | Clarify diagnostic authority beneath semantic calibration; preserve evaluator and all cases | No execution, test-count, or failure change | LOW: claim-only | Revert docs/registry/ledger only |

No additional portfolio item qualifies. Synthetic-session reclassification is high-confidence but not
needed to satisfy the approved areas and would broaden the campaign. Content lint and final-emission
modernization are implementation changes, not low-risk claim corrections. They remain deferred.

## Deferred Scope

- Ownership/import governance remains quarantined and unchanged.
- Replay projection, recurrence, drift, and diagnostic consolidation remains deferred.
- Suspected product and architecture regressions remain unfixed.
- Medium/low-confidence recommendations remain unimplemented.
- Content-lint, final-emission, and general architecture-governance modernization remain future work.
- No calibration round, state/narration validator, long-session validator, player/character parser,
  ambiguity repair, generative player, or browser validation was started.

## Before Baseline

`PRE_RATIONALIZATION_BASELINE` used `python -m pytest -q --tb=short`:

| Metric | Before |
|---|---:|
| Collected | 6,444 |
| Passed | 6,296 |
| Failed | 49 |
| Skipped | 99 |
| Warnings | 1 existing Starlette TestClient deprecation |
| Runtime | Not retained; not inferred |

All 49 failures matched the portfolio audit mapping, including 13 BW/BZ documentation-drift
failures. The run completed before executable validation edits. Its retained console output truncated
the duration; pass/skip counts reconcile from the stable post-run because all removed and added nodes
are deterministic and non-skipped. The machine-readable comparison records this limitation.

## Implemented Changes

### Historical BW/BZ closeout assertions

Sixteen historical test nodes were retired. They locked obsolete root-level paths, historical prose,
command examples, artifact names, and CLI help. Two narrow replacement checks now establish only that
the canonical closeouts exist under `docs/audits/closeouts/` and remain listed in the audit manifest.

The test modules remain at their existing paths for repository continuity. Their stale entries were
removed from `tests/test_inventory_governance.json` because they no longer own active governance
contracts. This updates inventory data, not ownership/import policy.

### Automated playability authority

Current documentation and registry metadata now classify playability as `SUPPORTING_EVIDENCE`.
`evaluate_playability`, the runner, semantic result states, mandatory gates, diagnostic scores,
thresholds, artifacts, calibration corpus, and reactive-player integration were not changed. FAIL
signals remain intact; PASS no longer independently establishes player-facing acceptance.

### Controlled structural replay

The CI presentation and current manifest now call this a controlled structural replay acceptance lane.
Its `RELEASE_GATE` authority, marker command, seven selected nodes, six ordinary invariant checks, one
opt-in skipped node, assertions, projections, and failure artifact remain unchanged. PASS explicitly
does not prove production-model semantics, narrative quality, live AI-GM behavior, or human
playability.

### Behavioral gauntlet authority

The registry and current test guidance classify the offline gauntlet as `DIAGNOSTIC` beneath semantic
calibration. All four axes, cases, reason codes, result schema, manual-report attachment, and failure
detection remain intact. Destructive consolidation was not performed.

## Evidence Preservation

- BW/BZ canonical closeouts, discoveries, audit-manifest entries, and trend-window artifacts remain.
- Playability still executes and emits semantic results, mandatory gates, diagnostic quality, axes,
  transcripts, evaluations, metadata, and state snapshots.
- Semantic calibration cases and thresholds are unchanged.
- Reactive/adversarial behavior and evidence are unchanged.
- Controlled structural replay still hard-fails on its protected invariant set.
- Behavioral gauntlet still detects its enumerated anti-patterns and emits the same axes/reason codes.
- No historical result or artifact was rewritten.

No unique evidence was lost. Active authority became narrower where evidence was already narrow.

## Authority Changes

The machine-readable authority ledger is
`artifacts/validation_rationalization/authority_changes.json`.

## Retired Tests

The machine-readable retirement ledger is
`artifacts/validation_rationalization/retired_tests.json`.

## After Baseline

`POST_RATIONALIZATION_BASELINE` used the same suite with JUnit accounting:

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| Collected | 6,444 | 6,440 | -4 |
| Passed | 6,296 | 6,305 | +9 |
| Failed | 49 | 36 | -13 |
| Skipped | 99 | 99 | 0 |
| Warnings | 1 | 1 | 0 |
| Runtime seconds | not retained | 470.510 | n/a |

The node delta is fully explained: 16 retired nodes, two provenance replacements, and ten campaign
tests. The 13 removed failures are exactly the retired documentation-drift failures. No new failure
appeared.

## Baseline Interpretation

The red baseline is more meaningful because it no longer mixes 13 missing historical-root-document
assertions with current validation. The remaining 36 failures preserve the previous classifications:

- 7 likely current product regressions
- 9 likely current architecture regressions
- 9 registry/governance drift failures
- 9 stale expectations
- 1 stale fixture
- 1 uncertain long-session diagnostic failure

No actual product or architecture defect was fixed. Ownership/import failures, replay projection and
recurrence failures, final-emission failures, social-lead failures, scene fallback, and validation-layer
separation remain visible. A smaller count is useful here only because every removed failure has a
documented authority reason.

## Unexpected Findings

- Canonical BW/BZ closeouts were already preserved under `docs/audits/closeouts/`; the obsolete tests
  referred to former root-level paths.
- Retiring the nodes made their old governance-inventory entries stale. Removing those two rows was a
  necessary inventory reconciliation, not a change to ownership/import policy.
- A second attempted pre-baseline accounting run overlapped documentation/artifact creation and was
  rejected as mixed-state evidence. It is not used in the comparison.

## Human Decisions Needed

None for the implemented scope. Review is still required before selecting any deferred campaign,
especially ownership/import governance or replay-diagnostic consolidation.

## Recommended Next Step

Review this baseline and authority ledger. Select a separate, explicitly approved campaign only after
that review. Do not begin ownership/import investigation, broader validation cleanup, Calibration
Round 2, or State-to-Narration Consistency automatically.

## Verification

- Focused authority/provenance/inventory/evaluator/calibration/portfolio tests: **128 passed**.
- Controlled structural replay: **6 passed, 1 skipped**; one existing Starlette warning.
- Full suite: **6,305 passed, 36 failed, 99 skipped** from **6,440** collected; one existing warning.
- No new full-suite failure appeared.
- No gameplay or model run was performed.

## Commands Executed

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'
& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m pytest -q --tb=short

& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  tools\build_validation_portfolio.py

& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m pytest tests\test_bw_protected_replay_trend_window_closeout.py `
  tests\test_bz_protected_replay_trend_window_2_closeout.py `
  tests\test_high_confidence_validation_rationalization.py tests\test_inventory_governance.py `
  tests\test_ownership_registry.py tests\test_playability_eval.py `
  tests\test_run_playability_validation_tool.py tests\test_behavioral_gauntlet_eval.py `
  tests\test_behavioral_gauntlet_smoke.py tests\test_semantic_calibration_corpus.py `
  tests\test_validation_portfolio.py -q --tb=short

& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m pytest -m golden_replay -q --tb=short

& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m pytest -q --tb=no `
  --junitxml=artifacts\validation_rationalization\post_suite.xml
```

Repository searches used `rg` across active docs, tests, tools, CI, prior audits, and portfolio
artifacts. `git status --short` was used for final worktree accounting.

## Files Changed

- Historical test modules: narrowed to canonical provenance checks.
- `.github/workflows/convergence-checks.yml`: presentation label only.
- `docs/playability_validation.md`, `docs/testing/protected_replay_manifest.md`, and
  `tests/README_TESTS.md`: active claim boundaries.
- `data/validation/validation_family_registry.json`: implemented authority/migration state only.
- `tests/test_inventory_governance.json`: removed two retired governance-owner rows.
- Added this report, authority ledger, retirement ledger, baseline comparison, focused regression tests,
  JUnit output, and campaign handoff configuration.
- Regenerated the family registry view, current failure summary, and review handoff.

## Limitations

- The pre-change runtime was not retained after console truncation and is not guessed.
- Failure classifications remain audit-level triage, not final root-cause proof.
- Documentation can correct declared authority but cannot prevent every downstream reader from
  overinterpreting raw evaluator fields.
- No runtime/model gameplay was rerun because no evaluator or gameplay behavior changed.
