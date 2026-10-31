# Campaign

Campaign: PR-BR Continuation 15 — Content-Dimension Coverage, Ambiguity Precedence & Final Preservation Closeout
Identifier: `pr-br-continuation-15`
Date: 2026-10-01
Generated: 2026-10-01T09:50:44.810192+00:00
Purpose: Give content questions an explicit dimension, rank necessary clarification above generic inability when the referent is ambiguous, and treat dimension coverage as inclusion. Four focused live turns. No smoke. No 4x10 gate. PR-BR remains open.

# Executive Summary

Content is the existing content dimension, kept distinct from source, confidence, time, and use. Necessary clarification outranks generic inability only when the referent is unbound. Coverage is additive. Semantic-degradation telemetry now records equal-rank requested-content loss. Deterministic band: 329 passed, 0 failed. All six Continuation 14 replays PASS. Live turns: 4. Interpretation calls: 1. Generation calls: 4. Evaluator model calls: 0. Retries: 0. Correct contracts 4/4. Initial manual PASS 4/4. Final manual PASS 4/4. Manual semantic degradations 0. Telemetry degradations 0. best_safe emission mismatches 0. Evaluator PASS 3/4 with 0 false PASS and 1 false FAIL (use paraphrase). READY FOR INDEPENDENT 10-TURN SMOKE: YES, not run. READY FOR FULL SYNTHETIC GATE: NO. HUMAN PLAYTEST: NOT AUTHORIZED. HEAD d31beb7d73dd4fda0f22184a6a69b947b5f470ff, uncommitted.

Objective status: `OPEN`.

# Changes Made

## Production changes

- game/resolution_contract.py recognizes content, ranks necessary clarification above inability, covers a requested dimension even when another dimension is also present, and records equal-rank semantic degradation.
- game/interpretation_proposal.py accepts content, canonicalizes substance and statement, and abstains when a content referent cannot be bound.
- game/semantic_interpreter.py asks the model for dimension content and distinguishes it from source, confidence, time, and use.
- game/gm_retry.py does not let scene stall replace a contract clarification.

## Validation changes

- tests/test_pr_br_continuation15_content_clarification.py covers content distinctions, the six Continuation 14 replays, degradation telemetry, and stubbed /api/chat.
- Broader band: 329 passed, 0 failed.

## Tooling changes

- tools/run_pr_br_continuation15_live.py runs at most four focused live turns and uses detect_semantic_degradation.

## Documentation changes

- docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md Continuation 15 section.

## Generated artifacts

- artifacts/pr_br_continuation15 live transcript, candidate histories, manual review, junit, and provenance.

# What Was Tested

- **Focused tests:** Continuation 15 content, clarification, additive-coverage, telemetry, and six Continuation 14 replay tests passed inside the 329-test band.
- **Broader relevant tests:** 329 passed, 0 failed, 0 skipped. Junit artifacts/pr_br_continuation15/junit.xml.
- **Full suite:** Not run.
- **Runtime validation:** 4 completed live turns. 3 fast-path. 1 abstention. 1 interpretation call. No smoke. No 4x10 gate. No repair rerun.
- **Model/runtime boundary:** 1 interpretation call. 4 generation calls. 0 evaluator model calls. 0 generation retries. 0 aborted.
- **New regressions:** None in the final band.
- **Pre-existing failures:** None in this band.
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Independent 10-turn smoke is ready and was not run. It needs separate authorization.
- Turn 4's use answer reached the player and the evaluator false-failed the paraphrase. Do not treat that as a selection regression.
- PR-BR remains open. Do not start PR-BS. Do not run the 4x10 gate. Human playtest is not authorized.

# Known Problems / Unresolved Findings

## Campaign-specific

- Use coverage misses 'folks come to that board to catch up on the latest rules and warnings', so a correct use-plus-content answer can be scored unsatisfied.

## Pre-existing baseline

- The omitted-index unscoped nominal bridge remains for callers that do not pass a catalog.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Does not prove 10-turn smoke health. The smoke was not run.
- Does not prove 4x10 synthetic-gate health.
- Does not authorize a human playtest.
- Does not prove live clarification precedence. The paid follow-up had one salient referent. The recorded Continuation 14 turn 2 replay covers the two-slot case.

# Recommended Next Step

External review may authorize the independent 10-turn smoke. Do not close PR-BR in this cycle. Do not start PR-BS. Do not repair the turn 4 use cue and rerun these four turns.

# Review Bundle Contents

Bundle file count: `19`
Bundle ZIP size: `000000187106` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md`.
- `support/game/resolution_contract.py`: Content dimension, clarification precedence, additive coverage, and degradation telemetry. Canonical source: `game/resolution_contract.py`.
- `support/game/interpretation_proposal.py`: Content validation, aliases, and content-referent abstention. Canonical source: `game/interpretation_proposal.py`.
- `support/game/semantic_interpreter.py`: Interpreter prompt distinguishes content from source, confidence, time, and use. Canonical source: `game/semantic_interpreter.py`.
- `support/game/gm_retry.py`: Scene stall does not replace a contract clarification. Canonical source: `game/gm_retry.py`.
- `support/tests/test_pr_br_continuation15_content_clarification.py`: Content variants, six Continuation 14 replays, evaluator fixtures, and stubbed chat. Canonical source: `tests/test_pr_br_continuation15_content_clarification.py`.
- `support/tests/test_pr_br_continuation14_resolution_content.py`: Equal-rank and best-safe regressions from Continuation 14. Canonical source: `tests/test_pr_br_continuation14_resolution_content.py`.
- `support/tests/test_pr_br_continuation13_semantic_preservation.py`: Social-resolution and earlier preservation regressions. Canonical source: `tests/test_pr_br_continuation13_semantic_preservation.py`.
- `support/artifacts/pr_br_continuation15/junit.xml`: 329 passed, 0 failed. Canonical source: `artifacts/pr_br_continuation15/junit.xml`.
- `support/artifacts/pr_br_continuation15/manual_review.md`: Human-DM review of the four live turns. Canonical source: `artifacts/pr_br_continuation15/manual_review.md`.
- `support/artifacts/pr_br_continuation15/provenance.json`: HEAD and cost bounds. Canonical source: `artifacts/pr_br_continuation15/provenance.json`.
- `support/artifacts/pr_br_continuation15/20261001T094739Z/transcript.md`: Focused live transcript. Canonical source: `artifacts/pr_br_continuation15/20261001T094739Z/transcript.md`.
- `support/artifacts/pr_br_continuation15/20261001T094739Z/turns.json`: Per-turn contracts, coverage, and candidate transitions. Canonical source: `artifacts/pr_br_continuation15/20261001T094739Z/turns.json`.
- `support/artifacts/pr_br_continuation15/20261001T094739Z/summary.json`: Call counts. Canonical source: `artifacts/pr_br_continuation15/20261001T094739Z/summary.json`.
- `support/artifacts/pr_br_continuation15/20261001T094739Z/generation_calls.json`: Generated candidates before final emission. Canonical source: `artifacts/pr_br_continuation15/20261001T094739Z/generation_calls.json`.
- `support/artifacts/pr_br_continuation15/20261001T094739Z/interpretation_calls.json`: Structured interpretation outputs. Canonical source: `artifacts/pr_br_continuation15/20261001T094739Z/interpretation_calls.json`.
- `support/tools/run_pr_br_continuation15_live.py`: Four-turn cap and the live shapes. Canonical source: `tools/run_pr_br_continuation15_live.py`.

## Explicit omissions

- `docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md`: duplicate content of docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
