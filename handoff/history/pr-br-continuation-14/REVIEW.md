# Campaign

Campaign: PR-BR Continuation 14 — Resolution-Content Preservation & Authoritative Best-Candidate Emission
Identifier: `pr-br-continuation-14`
Date: 2026-09-30
Generated: 2026-10-01T01:38:15.666203+00:00
Purpose: Require a later candidate to preserve the resolution content of the current best safe answer, and make that best answer the emitted line unless it is explicitly invalidated. Six focused live turns. No smoke. No 4x10 gate. PR-BR remains open.

# Executive Summary

Equal rank is no longer enough to replace a safe answer. Procedure, use, and confidence each keep their own resolution on the six recorded Continuation 13 replays. Deterministic band: 316 passed, 0 failed. Live turns: 6. Interpretation calls: 3. Generation calls: 6. Evaluator model calls: 0. Retries: 0. Correct contracts 5/6. Initial manual PASS 6/6. Final manual PASS 4/6. Semantic degradations 2. best_safe emission mismatches 0. Evaluator PASS 4/6 with 1 false PASS and 1 false FAIL. READY FOR INDEPENDENT 10-TURN SMOKE: NO. READY FOR FULL SYNTHETIC GATE: NO. HUMAN PLAYTEST: NOT AUTHORIZED. HEAD d31beb7d73dd4fda0f22184a6a69b947b5f470ff, uncommitted.

Objective status: `OPEN`.

# Changes Made

## Production changes

- game/resolution_contract.py compares resolution coverage, not rank alone, and emits best_safe_candidate unless that text was explicitly invalidated.
- game/interpretation_proposal.py canonicalizes dimension aliases, rejects unknown dimensions, and abstains when the fast path omits an obvious dimension.
- game/playability_eval.py fails a satisfied line that does not cover the contract dimensions.
- game/perception_grounding.py and game/narration_state_consistency.py invalidate a candidate that grounding replaced, without discarding a social answer that already resolves the contract.
- game/api_turn_support.py does not replace a referenced-surface or perception grounding line with the contract fallback.

## Validation changes

- tests/test_pr_br_continuation14_resolution_content.py replays all six Continuation 13 turns and covers equal-rank, superset, authority, and evaluator fixtures.
- Broader band: 316 passed, 0 failed.

## Tooling changes

- tools/run_pr_br_continuation14_live.py runs at most six focused live turns.

## Documentation changes

- docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md Continuation 14 section.

## Generated artifacts

- artifacts/pr_br_continuation14 live transcript, selection traces, manual review, junit, and provenance.

# What Was Tested

- **Focused tests:** Continuation 14 resolution-content tests, including all six recorded Continuation 13 replays, passed inside the 316-test band.
- **Broader relevant tests:** 316 passed, 0 failed, 0 skipped. Junit artifacts/pr_br_continuation14/junit.xml.
- **Full suite:** Not run.
- **Runtime validation:** 6 completed live turns. 3 fast-path. 3 interpretation calls. No smoke. No 4x10 gate. No repair rerun.
- **Model/runtime boundary:** 3 interpretation calls. 6 generation calls. 0 evaluator model calls. 0 generation retries. 0 aborted.
- **New regressions:** None in the final band. An intermediate grounding restoration was corrected before the live run.
- **Pre-existing failures:** None in this band.
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Do not authorize independent smoke. Two useful generated answers were still replaced after generation.
- PR-BR remains open. Do not start PR-BS. Do not run the 4x10 gate. Human playtest is not authorized.

# Known Problems / Unresolved Findings

## Campaign-specific

- Turn 5 left a content question at dimension None, so a Thoran fact replaced the traveler answer at equal rank.
- Turn 2 replaced a useful clarification with a generic time inability.
- Turn 4's use answer was emitted and then false-failed because it also says recently.

## Pre-existing baseline

- The omitted-index unscoped nominal bridge remains for callers that do not pass a catalog.

# Missing Concepts / Future Capabilities

- What travelers have been saying should carry a content dimension.
- A clarifying question should outrank a generic inability at the same nonresolution rank.

# What This Campaign Does NOT Prove

- Does not prove 10-turn smoke health.
- Does not prove 4x10 synthetic-gate health.
- Does not authorize a human playtest.

# Recommended Next Step

Give content questions a dimension, and do not let a generic inability replace a clarification at the same rank. Do not start independent smoke. Do not start PR-BS.

# Review Bundle Contents

Bundle file count: `21`
Bundle ZIP size: `000000224172` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md`.
- `support/game/resolution_contract.py`: Resolution coverage, equal-rank guard, best-safe authority, and explicit invalidation. Canonical source: `game/resolution_contract.py`.
- `support/game/interpretation_proposal.py`: Dimension aliases, unknown-dimension rejection, and fast-path abstention. Canonical source: `game/interpretation_proposal.py`.
- `support/game/playability_eval.py`: Fails a satisfied line that misses the requested resolution. Canonical source: `game/playability_eval.py`.
- `support/game/perception_grounding.py`: Grounding invalidates the replaced candidate and does not discard a keeping social answer. Canonical source: `game/perception_grounding.py`.
- `support/game/narration_state_consistency.py`: A stub destination line invalidates the invented text. Canonical source: `game/narration_state_consistency.py`.
- `support/game/api_turn_support.py`: Contract fallback does not erase a grounding line. Canonical source: `game/api_turn_support.py`.
- `support/game/social.py`: Clue-frame replacement still reports the precedence reason. Canonical source: `game/social.py`.
- `support/tests/test_pr_br_continuation14_resolution_content.py`: Six recorded replays, variants, equal-rank, superset, unsafe, and evaluator fixtures. Canonical source: `tests/test_pr_br_continuation14_resolution_content.py`.
- `support/tests/test_pr_br_continuation13_semantic_preservation.py`: Social-resolution and earlier preservation regressions. Canonical source: `tests/test_pr_br_continuation13_semantic_preservation.py`.
- `support/artifacts/pr_br_continuation14/junit.xml`: 316 passed, 0 failed. Canonical source: `artifacts/pr_br_continuation14/junit.xml`.
- `support/artifacts/pr_br_continuation14/manual_review.md`: Human-DM review of the six live turns. Canonical source: `artifacts/pr_br_continuation14/manual_review.md`.
- `support/artifacts/pr_br_continuation14/provenance.json`: HEAD and cost bounds. Canonical source: `artifacts/pr_br_continuation14/provenance.json`.
- `support/artifacts/pr_br_continuation14/20261001T013504Z/transcript.md`: Focused live transcript. Canonical source: `artifacts/pr_br_continuation14/20261001T013504Z/transcript.md`.
- `support/artifacts/pr_br_continuation14/20261001T013504Z/turns.json`: Per-turn contracts, coverage, and candidate transitions. Canonical source: `artifacts/pr_br_continuation14/20261001T013504Z/turns.json`.
- `support/artifacts/pr_br_continuation14/20261001T013504Z/summary.json`: Call counts. Canonical source: `artifacts/pr_br_continuation14/20261001T013504Z/summary.json`.
- `support/artifacts/pr_br_continuation14/20261001T013504Z/generation_calls.json`: Generated candidates before final emission. Canonical source: `artifacts/pr_br_continuation14/20261001T013504Z/generation_calls.json`.
- `support/artifacts/pr_br_continuation14/20261001T013504Z/interpretation_calls.json`: Structured interpretation outputs. Canonical source: `artifacts/pr_br_continuation14/20261001T013504Z/interpretation_calls.json`.
- `support/tools/run_pr_br_continuation14_live.py`: Six-turn cap and the live shapes. Canonical source: `tools/run_pr_br_continuation14_live.py`.

## Explicit omissions

- `docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md`: duplicate content of docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
