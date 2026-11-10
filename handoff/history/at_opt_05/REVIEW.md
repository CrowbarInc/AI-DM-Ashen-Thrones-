# Campaign

Campaign: AT-OPT-05 Compact-Instruction Eligibility and Transition Semantics
Identifier: `at_opt_05`
Date: 2026-11-08
Generated: 2026-11-08T19:59:48.757813+00:00
Purpose: Determine whether transition.transition_required unnecessarily forces ordinary gameplay requests onto the full primary narration instruction list, without changing production selection.

# Executive Summary

Verdict A/PASS. Live provider calls: 0. Production instruction selection was not changed. On the F3 pre-continuation snapshot the attached CTIR is the notice-board examination. resolved_transition is false and state_mutations.scene.scene_id is frontier_gate, but the derived node is a required location_change with both anchors frontier_gate. must_advance_scene copies that flag, so compact stays off. Narrative mode stays action_outcome. The attached step-back rebuild is 80,403 bytes and 78 instructions, admission estimate 26,865. Forcing the existing compact path is 70,263 bytes and 18 instructions, estimate 23,485, a reduction of 10,140 bytes and 3,380 estimate. That estimate is bytes divided by 3 plus 64, not a provider bill. The recorded input remains 22,777. Compact drops visibility, first-mention, and speaker hard rules, so that reduction is not accepted. The same same-scene stamp appears on the milestone look and on the 79 and 79B session bundles. A no-resolution rebuild already selects compact because detach_ctir removes the plan. Synthetic resolved_transition and arrived_at_scene stay required and keep mode transition. Focused tests 15 passed and 3 failed. The failures are the preexisting provider_context_projection, gm_only, and social_context KeyErrors.

Objective status: `A/PASS`.

# Changes Made

## Production changes

- No production instruction selection or transition-state change. game/narrative_planning.py and game/ctir_runtime.py were not edited. game/prompt_context.py was already dirty and was left as found.

## Validation changes

- No new product tests. Existing transition-node tests passed inside the focused run. They do not cover a same-scene scene_id.

## Tooling changes

- Added artifacts/at_opt_05/analyze_compact_eligibility.py. It rebuilds the F3 request in a temp data directory, blocks OpenAI and call_gpt, and writes only under artifacts/at_opt_05/.

## Documentation changes

- Added the AT-OPT-05 reports under development/campaigns/product_realization/at_opt_05/.
- Prepended the AT-OPT-05 result to docs/NEXT_SESSION.md. Prior handoff history remains.

## Generated artifacts

- Added the eligibility analysis and the focused junit under artifacts/at_opt_05/.
- Generated this review handoff. The archive digest sidecar is written after the zip is sealed.

# What Was Tested

- **Focused tests:** 15 passed, 3 failed, 0 skipped. Transition-node tests passed. The three failures are the preexisting KeyErrors: provider_context_projection, gm_only, and social_context.
- **Broader relevant tests:** Not run. No production behavior change.
- **Full suite:** Not run.
- **Runtime validation:** Provider-free build_messages on snapshot 2026-11-08T16-50-45_8caf7aff, plus detached and forced-compact comparisons, eight utterances, and synthetic transition nodes. State was copied to a temp directory.
- **Model/runtime boundary:** Live provider calls: 0. The OpenAI constructor and call_gpt were replaced and were not entered. Byte counts are not provider tokenizer counts. No Gameplay Benchmark was run.
- **New regressions:** None. Production selection was not edited.
- **Pre-existing failures:** The worktree was already dirty. The three KeyError failures were reproduced again and were not repaired. They are public-projection mismatches, not the compact gate.
- **Self-contained bundle review:** The bundle contains the AT-OPT-05 reports, the eligibility analysis, the focused junit, and the analysis script. No live play was produced.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- No product decision is required to accept the investigation.
- AT-OPT-06 is the recommended experiment and is not authorized by this handoff.
- Do not treat the 3,380-token admission delta as a measured provider saving.

# Known Problems / Unresolved Findings

## Campaign-specific

- The captured 22,777-token prompt is still absent. The attached rebuild is not that bill.
- The false location_change label is a correctness defect. It was not repaired.
- target_scene_id and time_skip can require a transition node while narrative mode stays continuation. That mismatch was left out of scope.

## Pre-existing baseline

- Three prompt tests still fail with KeyError for provider_context_projection, gm_only, and social_context.
- The worktree was already dirty at entry. HEAD does not uniquely identify the executable source.
- game/prompt_context.py was already modified. game/narration_authorization.py was already untracked.

# Missing Concepts / Future Capabilities

- A stored copy of the original F3 provider payload, so the historical instruction list can be distinguished from the attached rebuild and the detached compact path.
- A replay of a completed different-scene transition from a saved snapshot. The negative control here is synthetic.

# What This Campaign Does NOT Prove

- It does not prove a provider-billed token saving or a latency improvement.
- It does not prove that narration quality would survive the 10,140-byte compact swap. That swap was not selected.
- It does not prove a Gameplay Benchmark result. No benchmark was run.
- It does not prove the unstored historical step-back prompt used the 78-line list.
- It does not authorize AT-OPT-06, a compact-gate bypass, or a 3,000-token production opening cap.

# Recommended Next Step

AT-OPT-06, not started here. Stop treating a same-scene scene_id as a required transition, and hold manual_play_auto compact off when a stamp-matched narrative plan is present. Roll back if the attached F3 auto instruction count moves off 78, or if a real scene signal stops setting transition_required. Do not open PR-PLAY-80. Do not cap production openings at 3,000. Do not treat the 3,380 admission delta as a measured provider saving.

# Review Bundle Contents

Bundle file count: `14`
Bundle ZIP size: `000000093572` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/at_opt_05/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/at_opt_05/SUMMARY.md`.
- `support/development/campaigns/product_realization/at_opt_05/INSTRUCTION_SELECTION_MAP.md`: Full versus compact flow, predicates, and the eligibility decision table. Canonical source: `development/campaigns/product_realization/at_opt_05/INSTRUCTION_SELECTION_MAP.md`.
- `support/development/campaigns/product_realization/at_opt_05/TRANSITION_SEMANTICS.md`: Flag lifecycle, set and clear conditions, recorded nodes, and the defect class. Canonical source: `development/campaigns/product_realization/at_opt_05/TRANSITION_SEMANTICS.md`.
- `support/development/campaigns/product_realization/at_opt_05/F3_RECONSTRUCTION.md`: Recorded examine-turn state, eligibility decision, and full versus compact sizes. Canonical source: `development/campaigns/product_realization/at_opt_05/F3_RECONSTRUCTION.md`.
- `support/development/campaigns/product_realization/at_opt_05/SEMANTIC_COMPARISON.md`: Instruction differences classified for authority, continuity, and redundancy. Canonical source: `development/campaigns/product_realization/at_opt_05/SEMANTIC_COMPARISON.md`.
- `support/development/campaigns/product_realization/at_opt_05/FEASIBILITY_RESULTS.md`: Scenario matrix, byte and estimate comparisons, and the negative control. Canonical source: `development/campaigns/product_realization/at_opt_05/FEASIBILITY_RESULTS.md`.
- `support/development/campaigns/product_realization/at_opt_05/NEXT_STEP_DECISION.md`: The single selected outcome and the rollback conditions. Canonical source: `development/campaigns/product_realization/at_opt_05/NEXT_STEP_DECISION.md`.
- `support/development/campaigns/product_realization/at_opt_05/INTEGRITY.md`: Branch, dirty-tree preservation, and the zero-provider confirmation. Canonical source: `development/campaigns/product_realization/at_opt_05/INTEGRITY.md`.
- `support/artifacts/at_opt_05/eligibility_analysis.json`: Machine-readable reconstruction, utterance matrix, synthetic nodes, and instruction lists. Canonical source: `artifacts/at_opt_05/eligibility_analysis.json`.
- `support/artifacts/at_opt_05/focused_junit.xml`: 15 passed and the three preexisting KeyError failures. Canonical source: `artifacts/at_opt_05/focused_junit.xml`.
- `support/artifacts/at_opt_05/analyze_compact_eligibility.py`: Reproducible provider-free measurement. Canonical source: `artifacts/at_opt_05/analyze_compact_eligibility.py`.
- `support/docs/NEXT_SESSION.md`: Authoritative orientation after this cycle. Prior sections are preserved. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
