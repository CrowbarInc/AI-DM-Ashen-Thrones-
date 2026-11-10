# Campaign

Campaign: PR-PLAY Post-Optimization Gameplay Evaluation and Failure Triage
Identifier: `pr_play_post_opt`
Date: 2026-11-08
Generated: 2026-11-08T16:42:45-05:00
Purpose: Evaluate whether the current engine can sustain a short continuation without live provider calls, and name the single largest remaining playability obstacle.

# Executive Summary

Evaluation verdict A/PASS. The twelve-turn continuation is not a sustainable conversation. Live provider calls: 0. PR-PLAY-80 was not opened. No production code was changed. One grounded Guard Captain answer and one authored move to Old Milestone succeeded. After the captain's answer, conversational orchestration reused that sentence for a notice reading and a mud-copy improvisation, treated a walk to the visible notice board as unestablished travel, and turned a recall of the notice into an address clarification. The player never heard the notice. Three provider-disabled or retry fallback sentences were published as completed runtime responses. The retreat at Old Milestone was a correct operational refusal and did not enter primary narration. Local TestClient time was 1598.794 ms and is not live latency. A separate budget probe refused a 28000-token estimate before dispatch and admitted a 100-token estimate to a local stub. Focused AT-OPT tests passed 61. Dedup, same-scene instruction selection, and the full-instruction safeguard were not exercised by the chat turns. The next action is a targeted orchestration repair. Do not implement it from this handoff. Do not launch live play and do not open PR-PLAY-80.

Objective status: `A/PASS`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No new production tests. Existing AT-OPT focused tests were run: 61 passed.

## Tooling changes

- Added artifacts/pr_play_post_opt/run_sequence.py. It seeds an already-started frontier-gate campaign, blocks the OpenAI client and non-local connects, and writes only under artifacts/pr_play_post_opt/.

## Documentation changes

- Added the evaluation reports under development/campaigns/product_realization/pr_play_post_opt/.
- Prepended the evaluation result to docs/NEXT_SESSION.md. Prior handoff history remains.

## Generated artifacts

- Added the turn record, route index, publication events, sequence summary, and both budget probes under artifacts/pr_play_post_opt/.
- The isolated campaign store under artifacts/pr_play_post_opt/run_data/ is retained and is not packaged.
- Generated this review handoff.

# What Was Tested

- **Focused tests:** 61 passed, 0 failed. AT-OPT-02, AT-OPT-04, and AT-OPT-06 focused files. The three known baseline KeyError tests were not rerun.
- **Broader relevant tests:** Not run. No full historical 1065 suite.
- **Full suite:** Not run.
- **Runtime validation:** Twelve provider-free continuation turns on one seeded campaign. HTTP 200 on every turn. Scene moved only on the authored exit. The retreat did not move position.
- **Model/runtime boundary:** Live provider calls: 0. Provider client constructions: 0. Non-local connects: 0. call_gpt entries: 4, none dispatched. The 14-token stub completion is local. No Gameplay Benchmark was run. Disabled-provider sentences are not live prose.
- **New regressions:** No production edit, so no new source regression was introduced. The play session exposed the conversational-orchestration capture.
- **Pre-existing failures:** The worktree was already dirty. The three KeyError failures recorded by AT-OPT-06 were not rerun and were not treated as new.
- **Self-contained bundle review:** The bundle contains the seven evaluation reports, the turn record, the route index, the publication events, and both budget probes. The isolated campaign store is omitted because the turn record already carries the player text, responses, routes, and state deltas.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- No product decision is required to accept the evaluation.
- The recommended repair is not authorized by this handoff. A later cycle has to authorize the orchestration change.
- Do not treat this result as a live-model playability score.

# Known Problems / Unresolved Findings

## Campaign-specific

- After one NPC answer, repeat_delivered_statement, destination_not_established, and ungrounded_provider_target swallow notice, inspection, and recall intents.
- A resolved observation can be published as the provider-disabled sentence.
- An unresolved 'Handle it' published a mashed scene sentence and kept it as a bounded incidental.
- Two engine-response events disagree with session.last_publication.

## Pre-existing baseline

- Primary narration remains expensive when it is actually sent. This run did not send it.
- Admission estimates are bytes divided by 3 plus 64. They are not provider bills.
- Historical narration bundles can retain a stale transition flag.
- Three prompt tests still fail with KeyError for provider_context_projection, gm_only, and social_context.
- HEAD does not uniquely identify the executable source because the worktree was already dirty.

# Missing Concepts / Future Capabilities

- A live, budgeted narration of the observation and ambiguous turns. It was not authorized.
- A gameplay measurement of mixed-key dedup and of the plan-backed full instruction list.

# What This Campaign Does NOT Prove

- It does not prove live-model prose quality.
- It does not prove that the AT-OPT byte reductions changed play.
- It does not prove the three baseline KeyError tests are unchanged, because they were not rerun.
- It does not authorize PR-PLAY-80, AT-OPT-07, or a production opening cap of 3000.

# Recommended Next Step

Repair conversational orchestration so a new notice, inspection, or recall intent is not answered with the previous NPC sentence, and a visible interactable is not an unestablished destination. Keep the genuine-repeat, unknown-place, and disabled-retreat controls. Do not implement that repair from this handoff. Do not open PR-PLAY-80. Do not launch live play until that boundary is repaired.

# Review Bundle Contents

Bundle file count: `17`
Bundle ZIP size: `000000086045` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_post_opt/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_post_opt/SUMMARY.md`.
- `support/development/campaigns/product_realization/pr_play_post_opt/SCENARIO.md`: Scenario source, turns, provider mode, and budget. Canonical source: `development/campaigns/product_realization/pr_play_post_opt/SCENARIO.md`.
- `support/development/campaigns/product_realization/pr_play_post_opt/TURN_BY_TURN.md`: Every player utterance, response, route, publication, and score. Canonical source: `development/campaigns/product_realization/pr_play_post_opt/TURN_BY_TURN.md`.
- `support/development/campaigns/product_realization/pr_play_post_opt/PLAYABILITY_ASSESSMENT.md`: Separate player-experience categories. Canonical source: `development/campaigns/product_realization/pr_play_post_opt/PLAYABILITY_ASSESSMENT.md`.
- `support/development/campaigns/product_realization/pr_play_post_opt/OPTIMIZATION_IMPACT.md`: Which AT-OPT corrections the session exercised. Canonical source: `development/campaigns/product_realization/pr_play_post_opt/OPTIMIZATION_IMPACT.md`.
- `support/development/campaigns/product_realization/pr_play_post_opt/FAILURE_TRIAGE.md`: Failure inventory and the selected blocker. Canonical source: `development/campaigns/product_realization/pr_play_post_opt/FAILURE_TRIAGE.md`.
- `support/development/campaigns/product_realization/pr_play_post_opt/INTEGRITY.md`: Branch, dirty-tree preservation, and the zero-provider confirmation. Canonical source: `development/campaigns/product_realization/pr_play_post_opt/INTEGRITY.md`.
- `support/artifacts/pr_play_post_opt/turns.json`: Machine-readable turn results. Canonical source: `artifacts/pr_play_post_opt/turns.json`.
- `support/artifacts/pr_play_post_opt/route_index.json`: Resolver, conversational reason, and call_gpt count per turn. Canonical source: `artifacts/pr_play_post_opt/route_index.json`.
- `support/artifacts/pr_play_post_opt/sequence_summary.json`: Provider mode, dispatch count, and final state. Canonical source: `artifacts/pr_play_post_opt/sequence_summary.json`.
- `support/artifacts/pr_play_post_opt/publication_events.jsonl`: Publication events actually written. Canonical source: `artifacts/pr_play_post_opt/publication_events.jsonl`.
- `support/artifacts/pr_play_post_opt/preflight.json`: In-sequence admission while provider calls were disabled. Canonical source: `artifacts/pr_play_post_opt/preflight.json`.
- `support/artifacts/pr_play_post_opt/budget_probe.json`: Token-ceiling refusal and within-budget local stub. Canonical source: `artifacts/pr_play_post_opt/budget_probe.json`.
- `support/artifacts/pr_play_post_opt/run_sequence.py`: Reproducible provider-free sequence driver. Canonical source: `artifacts/pr_play_post_opt/run_sequence.py`.
- `support/docs/NEXT_SESSION.md`: Authoritative orientation after this cycle. Prior sections are preserved. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
