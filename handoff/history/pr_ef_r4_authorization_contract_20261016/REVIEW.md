# Campaign

Campaign: PR-EF-R4 — Conversational Authority Contract Consolidation
Identifier: `pr_ef_r4_authorization_contract_20261016`
Date: 2026-10-16
Generated: 2026-10-16T23:26:27.344031+00:00
Purpose: Consolidate conversational authorization. Do not start PR-EG.

# Executive Summary

# 01 — Executive Summary

PR-EF-R4 consolidates conversational authorization onto one grounding decision, `assess_addressee_grounding`, and records that decision on the resolution contract and on clarification responses. Provider-suggested NPC ids are candidates. They do not authorize an unresolved or non-unique person reference, and they do not advance the world while clarification is required.

## Implementation

The production path still interprets, then authorizes, then hands an eligible operation to the existing social, exploration, and movement resolvers. Authorization does not declare success. Final responses for an unresolved addressee use the authorization clarification. Narration is skipped only when a resolved social result has speech authority `none`, no revealed topic, no subjective allowance, and reply plan `consequential_information_request`.

## Critical findings

- The historical “I ask one of them what happened” failure does not execute and does not tick. Fresh live play with Sergeant Mara and Corporal Bren both visible asked which person was meant. Turn, clocks, and factions stayed put. The follow-up “The sergeant.” executed as Sergeant Mara.
- Explicit and uniquely grounded addresses still reach the social resolver. “I ask Sergeant Mara…”, “I ask the sergeant…”, “I ask the taller guard…” when height is actually written, and an in-conversation “What did you mean…” all executed the grounded NPC.
- A GM question about an NPC is not turned into NPC dialogue. “What does the sergeant know about the lantern?” stayed with the GM. “What did she mean by the road?” in the continuous conversation did not tick and did not open a new social exchange.
- Corrections, bare confirmation, and withdrawal do not execute a missing or already-resolved intention. The live correction after an executed ask said the action could not be undone and did not roll the turn back.
- Mixed and conditional intentions stay unexecuted until their condition or confirmation exists. The live conditional about the gate did not move. The following explicit walk through the courtyard gate did.

## Remaining defects

- One isolated live holdout, “What did you mean by the north road?” with only a session flag and no prior visible turn, was blocked as malformed communication. The same sentence succeeded as turn 3 of the continuous conversation.
- “I put the question to one of them” with one visible NPC clarified and did not mutate, but the spoken line was the provider’s clarification question rather than the authorization template.
- A knowledge-gap ask whose reply plan is `genuine_uncertainty` still calls strict-social narration and may retry. Live case B accepted “I don’t know.” after one format retry (50,784 input tokens). A clarified “what happened” ask whose plan said `authoritative_answer_available` while speech authority was `none` still spent a narration plus retry (51,910 input tokens) and then showed the safe line.
- The twenty PR-EF-R2 regression identities still fail. None were added and none were cleared.

## Recommendation

**B — PR-EF ACCEPTED WITH LIMITATIONS**

Core authorization, ambiguity, ownership, pending-intention, and resolver handoff behavior is demonstrated on fresh `/api/chat` output and on the frozen holdouts. The remaining gaps are a cold-follow-up interpretation block, clarification wording on one non-unique phrase, and narration cost when the reply plan is not the closed consequential-information plan. Do not start PR-EG from this package.


Objective status: `B — PR-EF ACCEPTED WITH LIMITATIONS`.

# Changes Made

## Production changes

- One addressee grounding decision gates execution and the world tick.
- Provider NPC ids are candidates unless the utterance uniquely grounds them.
- Narration and retry are skipped only for a closed consequential-information plan.

## Validation changes

- Frozen holdouts in tests/fixtures/pr_ef_r4_holdouts.json.
- tests/test_pr_ef_r4_authorization.py.

## Tooling changes

- tools/validate_pr_ef_r4.py

## Documentation changes

- Reports 01–18 under artifacts/pr_ef_r4.

## Generated artifacts

- Fresh /api/chat conversation, holdouts, and performance records.
- Post-implementation regression junit.

# What Was Tested

- **Focused tests:** 28/28 PR-EF-R4 authorization tests passed, including 25 frozen cases under scripted providers.
- **Broader relevant tests:** Family 349 passed / 20 failed. The 20 identities are exactly the PR-EF-R2 historical set.
- **Full suite:** Not run. The established conversational family was run.
- **Runtime validation:** Fresh gpt-4.1-mini-2025-04-14 through TestClient /api/chat. Ten-turn conversation plus 25 live holdouts. 49 requests, 494725 input tokens.
- **Model/runtime boundary:** Configured gpt-4.1-mini. Observed gpt-4.1-mini-2025-04-14.
- **New regressions:** None in the final family measurement.
- **Pre-existing failures:** The twenty PR-EF-R2 identities remain. They were not cleaned up.
- **Self-contained bundle review:** Eighteen reports, frozen holdouts, live conversation, performance cases, and the regression junit. No .env and no active campaign saves.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Accept or reject B — accepted with limitations.
- Do not begin PR-EG from this package.

# Known Problems / Unresolved Findings

## Campaign-specific

- A cold follow-up can be blocked as malformed communication before continuation.
- A non-INTERPRETED record can speak the provider clarification instead of the authorization template.
- genuine_uncertainty and authoritative_answer_available with speech authority none still pay narration and retry.

## Pre-existing baseline

- Twenty inherited regression failures from the R2 family.

# Missing Concepts / Future Capabilities

- A non-persisted incidental speech lane. Left for PR-EG. Not implemented.

# What This Campaign Does NOT Prove

- That every unknown question avoids narration.
- Interpretation-label agreement with the live model. Behavior is scored separately and is ahead of labels.
- A global token reduction against the R2 eleven-turn workload. The workloads differ.
- That the pre-edit tree would still score 321/20. That run was not repeated.

# Recommended Next Step

External review. Stop. Do not start PR-EG.

# Review Bundle Contents

Bundle file count: `25`
Bundle ZIP size: `000000080451` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_ef_r4/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_ef_r4/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_ef_r4/02_BASELINE_AND_ENVIRONMENT.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/02_BASELINE_AND_ENVIRONMENT.md`.
- `support/artifacts/pr_ef_r4/03_AUTHORIZATION_CONTRACT_DESIGN.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/03_AUTHORIZATION_CONTRACT_DESIGN.md`.
- `support/artifacts/pr_ef_r4/04_AUTHORITY_CONSOLIDATION_AUDIT.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/04_AUTHORITY_CONSOLIDATION_AUDIT.md`.
- `support/artifacts/pr_ef_r4/05_AMBIGUOUS_TARGET_INTEGRITY.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/05_AMBIGUOUS_TARGET_INTEGRITY.md`.
- `support/artifacts/pr_ef_r4/06_GM_NPC_OWNERSHIP.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/06_GM_NPC_OWNERSHIP.md`.
- `support/artifacts/pr_ef_r4/07_CORRECTIONS_AND_PENDING_INTENTIONS.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/07_CORRECTIONS_AND_PENDING_INTENTIONS.md`.
- `support/artifacts/pr_ef_r4/08_RESOLVER_HANDOFF.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/08_RESOLVER_HANDOFF.md`.
- `support/artifacts/pr_ef_r4/09_FINAL_RESPONSE_CONSISTENCY.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/09_FINAL_RESPONSE_CONSISTENCY.md`.
- `support/artifacts/pr_ef_r4/10_PROVIDER_ELIGIBILITY_AND_RETRY.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/10_PROVIDER_ELIGIBILITY_AND_RETRY.md`.
- `support/artifacts/pr_ef_r4/11_FROZEN_SEMANTIC_HOLDOUTS.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/11_FROZEN_SEMANTIC_HOLDOUTS.md`.
- `support/artifacts/pr_ef_r4/12_FRESH_LIVE_CONVERSATION.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/12_FRESH_LIVE_CONVERSATION.md`.
- `support/artifacts/pr_ef_r4/13_PERFORMANCE_COMPARISON.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/13_PERFORMANCE_COMPARISON.md`.
- `support/artifacts/pr_ef_r4/14_REGRESSION_COMPARISON.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/14_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_ef_r4/15_BOUNDED_IMPROVISATION_COMPATIBILITY.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/15_BOUNDED_IMPROVISATION_COMPATIBILITY.md`.
- `support/artifacts/pr_ef_r4/16_REMAINING_ISSUES.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/16_REMAINING_ISSUES.md`.
- `support/artifacts/pr_ef_r4/17_FINAL_RECOMMENDATION.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/17_FINAL_RECOMMENDATION.md`.
- `support/artifacts/pr_ef_r4/18_CHANGED_FILE_INVENTORY.md`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/18_CHANGED_FILE_INVENTORY.md`.
- `support/artifacts/pr_ef_r4/live.usage.jsonl`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/live.usage.jsonl`.
- `support/artifacts/pr_ef_r4/live_interpretation_disabled.usage.jsonl`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/live_interpretation_disabled.usage.jsonl`.
- `support/artifacts/pr_ef_r4/live_qualification.json`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/live_qualification.json`.
- `support/artifacts/pr_ef_r4/live_qualification_interpretation_disabled.json`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/live_qualification_interpretation_disabled.json`.
- `support/artifacts/pr_ef_r4/regression_junit.xml`: PR-EF-R4 report or fresh-provider evidence. Canonical source: `artifacts/pr_ef_r4/regression_junit.xml`.

## Explicit omissions

- `artifacts/pr_ef_r4/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_ef_r4/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
