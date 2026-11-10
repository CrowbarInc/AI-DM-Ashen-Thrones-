# Campaign

Campaign: PR-PLAY Post-NPC Conversational Handoff Repair
Identifier: `pr_play_post_npc`
Date: 2026-11-08
Generated: 2026-11-08T22:21:22.170598+00:00
Purpose: Let a player leave the previous NPC response for a visible object, a reading, an improvised action, or a grounded recall without losing travel checks or explicit repeats.

# Executive Summary

Verdict A/PASS for the targeted orchestration repair. The game is not playable. Live provider calls: 0. PR-PLAY-80 was not opened. After the Guard Captain answered, walking to the notice board was an unknown destination, reading the notice and copying it replayed the captain, and asking what the notice said was an unaddressed ask. Those four routes are repaired on the same twelve utterances. T04 declines as local contact and does not move or reveal the clue. T05 publishes the patrol-route clue. T06 declines the sleeve copy without an inventory change. T09 recalls the disclosed clue. Explicit repeats, the captain follow-up, the Old Milestone exit, and the unsupported retreat still hold. T05 still appends a stock jab sentence. T01, T07, and T08 are still non-play sentences. Focused tests: 7 passed. Holdout: 28/28. Protected files: 150/150. Twelve adjacent HTTP assertions failed and were not compared with a pre-edit run.

Objective status: `A/PASS`.

# Changes Made

## Production changes

- game/conversational_orchestration.py: a unique current-scene catalog hit declines as local contact; a grounded object question inspects that object; an unbound physical attempt declines with the existing unsupported sentence.
- game/conversational_continuity.py: overlap replay abstains for a non-question or a named scene object; an explicit repeat can recover a GM-owned delivered row.
- game/referenced_surface.py and game/intent_parser.py: a past-tense content question can name an interactable, and a multi-token interactable prefix is not replaced by a longer visible fact.

## Validation changes

- Added tests/test_pr_play_post_npc_handoff.py. Seven provider-free chat cases cover the handoff, explicit repeats, a return to the captain, travel, unknown targets, and hidden content.

## Tooling changes

- Added artifacts/pr_play_post_npc/baseline_trace.py. It replays the twelve utterances with provider calls disabled and writes a trace under artifacts/pr_play_post_npc/.

## Documentation changes

- Added the reports under development/campaigns/product_realization/pr_play_post_npc/.
- Prepended the cycle result to docs/NEXT_SESSION.md. Prior handoff history remains.

## Generated artifacts

- Added the before and after traces, the comparison, the redirected holdout, and the protected-file rehash under artifacts/pr_play_post_npc/.
- Generated this review handoff.

# What Was Tested

- **Focused tests:** 7 passed, 0 failed. Provider-free /api/chat cases.
- **Broader relevant tests:** Adjacent continuity, surface, admission, AT-OPT, transition, and efficiency tests reported 12 HTTP assertion failures. A pre-edit rerun was not obtained. Those failures are not claimed as new identities and are not claimed as baseline. The known provider_context_projection, gm_only, and social_context KeyErrors remain.
- **Full suite:** Not run.
- **Runtime validation:** The original twelve utterances were replayed before and after. T04, T05, T06, and T09 no longer use destination_not_established, repeat_delivered_statement, or ungrounded_provider_target. T11 still arrives at Old Milestone. T12 is still the unsupported retreat.
- **Model/runtime boundary:** Live provider calls: 0. call_gpt was entered 4 times and returned before dispatch. The holdout recorded 0 blocked non-local connections on the solo rerun. No Gameplay Benchmark was run.
- **New regressions:** None claimed. The 12 adjacent HTTP failures were not compared with a pre-edit run.
- **Pre-existing failures:** The worktree was already dirty. The three KeyError failures remain. T01, T08, and the tavern refusal were already non-play results. T07 was already a fallback and now uses the disabled-narration sentence.
- **Self-contained bundle review:** The bundle contains the six reports, the before and after traces, the comparison, the redirected holdout, and the protected-file rehash. No live play was produced.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- No product decision is required to accept the four route corrections.
- Do not treat A/PASS as a claim that the game is playable.
- Do not open PR-PLAY-80 from this handoff.

# Known Problems / Unresolved Findings

## Campaign-specific

- T05 publishes the authorized clue and then the existing stock sentence about someone jabbing at the board.
- T04 and T06 stop at authorized limitations. They do not perform the touch or the copy.
- T01, T07, and T08 still publish non-play sentences.
- Twelve adjacent HTTP assertions failed, and a pre-edit comparison was not obtained.

## Pre-existing baseline

- Three prompt tests still fail with KeyError for provider_context_projection, gm_only, and social_context.
- The worktree was already dirty at entry. HEAD does not uniquely identify the executable source.
- git diff HEAD on conversational_orchestration.py includes preexisting uncommitted work.

# Missing Concepts / Future Capabilities

- A pre-edit rerun of the twelve adjacent HTTP tests.
- A live narration of T01, T05, T07, and T08.
- An Ashen Thrones Gameplay Benchmark. None was run.

# What This Campaign Does NOT Prove

- It does not prove the game is playable.
- It does not prove the twelve adjacent HTTP failures are preexisting.
- The seven new tests were authored with the implementation. They are not an independent holdout. The frozen 28-case holdout is a developer holdout.
- It does not authorize PR-PLAY-80, AT-OPT-07, a writing system, or a live-play session.

# Recommended Next Step

Remove the stock diegetic sentence that follows an authorized clue publication. Do not start that repair from this handoff. Do not open PR-PLAY-80. Do not start AT-OPT-07. Do not launch live play from this result.

# Review Bundle Contents

Bundle file count: `17`
Bundle ZIP size: `000000087040` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_post_npc/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_post_npc/SUMMARY.md`.
- `support/development/campaigns/product_realization/pr_play_post_npc/ROOT_CAUSE.md`: Decision traces and the earliest wrong decision for each failure. Canonical source: `development/campaigns/product_realization/pr_play_post_npc/ROOT_CAUSE.md`.
- `support/development/campaigns/product_realization/pr_play_post_npc/ROUTING_CONTRACT.md`: Continuation, repeat, inspection, recall, travel, and authority limits. Canonical source: `development/campaigns/product_realization/pr_play_post_npc/ROUTING_CONTRACT.md`.
- `support/development/campaigns/product_realization/pr_play_post_npc/REGRESSION_RESULTS.md`: Focused, adjacent, and protected results, including the unresolved HTTP failures. Canonical source: `development/campaigns/product_realization/pr_play_post_npc/REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_post_npc/TWELVE_TURN_COMPARISON.md`: Before and after route, publication, and usefulness for all twelve turns. Canonical source: `development/campaigns/product_realization/pr_play_post_npc/TWELVE_TURN_COMPARISON.md`.
- `support/development/campaigns/product_realization/pr_play_post_npc/INTEGRITY.md`: Branch, scene-file restore, dirty-tree preservation, and zero live calls. Canonical source: `development/campaigns/product_realization/pr_play_post_npc/INTEGRITY.md`.
- `support/artifacts/pr_play_post_npc/comparison.json`: Machine-readable before and after reasons. Canonical source: `artifacts/pr_play_post_npc/comparison.json`.
- `support/artifacts/pr_play_post_npc/baseline_trace.json`: Provider-free decision trace before the repair. Canonical source: `artifacts/pr_play_post_npc/baseline_trace.json`.
- `support/artifacts/pr_play_post_npc/corrected_trace.json`: Provider-free decision trace after the solo rerun. Canonical source: `artifacts/pr_play_post_npc/corrected_trace.json`.
- `support/artifacts/pr_play_post_npc/holdout_rerun.json`: Redirected frozen holdout, 28 passed, historical results file not rewritten. Canonical source: `artifacts/pr_play_post_npc/holdout_rerun.json`.
- `support/artifacts/pr_play_post_npc/protected_rehash.json`: 150 protected files unchanged. Canonical source: `artifacts/pr_play_post_npc/protected_rehash.json`.
- `support/artifacts/pr_play_post_npc/implementation.diff`: Diff against HEAD for continuity, surface classification, and the parser. The orchestration diff is omitted because HEAD mixes preexisting dirty work. Canonical source: `artifacts/pr_play_post_npc/implementation.diff`.
- `support/tests/test_pr_play_post_npc_handoff.py`: Production chat controls for the handoff. Canonical source: `tests/test_pr_play_post_npc_handoff.py`.
- `support/artifacts/pr_play_post_npc/baseline_trace.py`: Reproducible provider-free twelve-turn replay. Canonical source: `artifacts/pr_play_post_npc/baseline_trace.py`.
- `support/docs/NEXT_SESSION.md`: Authoritative orientation after this cycle. Prior sections are preserved. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
