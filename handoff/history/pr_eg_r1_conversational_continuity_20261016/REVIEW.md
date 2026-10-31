# Campaign

Campaign: PR-EG-R1 — Conversational Continuity and Response Ownership
Identifier: `pr_eg_r1_conversational_continuity_20261016`
Date: 2026-10-16
Generated: 2026-10-17T01:16:27.298687+00:00
Purpose: Repair conversational continuity and response ownership. Do not start PR-EH.

# Executive Summary

# 01 — Executive Summary

PR-EG-R1 repairs conversational continuity and response ownership without replacing the PR-EF-R4 authorization contract.

## Implemented repairs

- The line actually delivered to the player is stored as a bounded exchange. Rejected narration and discarded provider candidates are not stored.
- A follow-up can ground "that," a paraphrase, a possessive ("the road's name"), or an earlier topic in that delivered statement.
- If the player is still speaking to that NPC, the reply stays in the NPC's voice. A GM question about what the NPC said quotes the earlier line and does not start a new NPC turn.
- A conversational correction updates the topic. It does not emit an undo refusal for a completed social action.
- A harmless preference that comes back as ignorance or a one-word refusal is replaced with a stable non-canonical preference. A later question reuses it.
- A request for a promise or reward is declined in the NPC's voice. No quest, payment, or inventory change is created.
- An earlier statement can be recalled after the character leaves. The absent NPC is not spoken to from the new scene.
- Scene descriptions are dropped from the exchange window before an NPC statement, so a short move-and-inspect sequence does not erase the last useful answer.
- Follow-ups that the engine can already answer do not start a narration or a retry.

## Player-facing improvement

Fresh `/api/chat` play, model route `gpt-4.1-mini`, two disposable campaigns, frozen checks written before the run:

- Fifteen-turn conversation: 0 frozen failures. 6 provider calls, 2 narration calls, 0 retries, 56,440 input tokens.
- Independent twelve-turn conversation: 0 frozen failures. 4 provider calls, 2 narration calls, 0 retries, 53,374 input tokens.

"What did you mean by that?" now repeats the north-road sentence with no provider call. The historical failure of that turn spent about 52,957 input tokens and answered "I couldn't tell you."

## Remaining limitations

- "Say that again in plainer words" repeats the sentence under "I meant this:" rather than restating it in new words.
- The first street-name question and a preference question still each send one strict-social narration of about 24,000–26,000 input tokens. There is no retry. The prompt itself was not rewritten.
- The preference the player hears is a stable "I prefer the evening," not a longer characterization.
- Nineteen inherited regression identities remain. No new failing identity was introduced.

## Recommendation

**B — PR-EG ACCEPTED WITH LIMITATIONS**

Ordinary conversation now keeps the previous delivered meaning, the speaker, and the authority boundary. The remaining gaps are phrasing stiffness and the size of the first social narration, not lost context or internal software language.


Objective status: `B — PR-EG ACCEPTED WITH LIMITATIONS`.

# Changes Made

## Production changes

- Delivered NPC lines are the grounding source for the next turn.
- Ordinary NPC replies stay in the NPC's voice. GM recalls quote earlier speech.
- Topic corrections, harmless preferences, and reward requests no longer surface internal templates.

## Validation changes

- Frozen holdouts in tests/fixtures/pr_eg_r1_continuity_holdouts.json.
- Frozen live checks in tests/fixtures/pr_eg_r1_live_expectations.json.

## Tooling changes

- tools/validate_pr_eg_r1.py

## Documentation changes

- Reports 01–19 under artifacts/pr_eg_r1.

## Generated artifacts

- Fresh /api/chat fifteen-turn conversation and an independent twelve-turn conversation.
- Baseline and post-implementation regression junit.

# What Was Tested

- **Focused tests:** Continuity holdouts, PR-EG dialogue quality, and PR-EF-R4 authorization pass. Provider not used for the holdout scorer.
- **Broader relevant tests:** Family 393 passed / 19 failed, including 22 new continuity tests. Pre-change family was 371 passed / 19 failed. No new failing identities.
- **Full suite:** Not run. The established conversational family was run.
- **Runtime validation:** Fresh gpt-4.1-mini through TestClient /api/chat. Fifteen turns, 6 calls, 56440 input tokens, 0 retries. Second conversation, 12 turns, 4 calls, 53374 input tokens, 0 retries. Frozen failures 0 and 0.
- **Model/runtime boundary:** Configured gpt-4.1-mini. Observed route gpt-4.1-mini strict_social.
- **New regressions:** None in the final family measurement.
- **Pre-existing failures:** The same nineteen identities as the pre-change baseline.
- **Self-contained bundle review:** Nineteen reports, frozen holdouts, two fresh /api/chat conversations, and the regression junit. No .env and no active campaign saves.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Accept or reject B — PR-EG accepted with limitations.
- Do not begin PR-EH from this package.

# Known Problems / Unresolved Findings

## Campaign-specific

- A paraphrase repeats the sentence under 'I meant this:' rather than restating it.
- The first street-name narration and the preference narration are still about 24k–26k input tokens each. They do not retry.

## Pre-existing baseline

- Nineteen inherited regression failures from the shared turn pipeline and exploration routing.

# Missing Concepts / Future Capabilities

- A real paraphrase of a delivered sentence.
- A smaller strict-social prompt for the first answer of a known fact.

# What This Campaign Does NOT Prove

- That every unseen phrasing will ground. Novel wording that matches neither a cue nor the supplied sentence still falls through to interpretation.
- That the first social narration can be cheap. Only follow-up retries were removed.
- That the nineteen remaining family failures are unchanged in their assertion text. Identities were compared.

# Recommended Next Step

External review. Stop. Do not start PR-EH.

# Review Bundle Contents

Bundle file count: `25`
Bundle ZIP size: `000000073311` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r1/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r1/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r1/02_BASELINE_AND_ENVIRONMENT.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/02_BASELINE_AND_ENVIRONMENT.md`.
- `support/artifacts/pr_eg_r1/03_HISTORICAL_FAILURE_RECONSTRUCTION.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/03_HISTORICAL_FAILURE_RECONSTRUCTION.md`.
- `support/artifacts/pr_eg_r1/04_CONVERSATIONAL_CONTINUITY_DESIGN.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/04_CONVERSATIONAL_CONTINUITY_DESIGN.md`.
- `support/artifacts/pr_eg_r1/05_RESPONSE_OWNERSHIP_AUDIT.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/05_RESPONSE_OWNERSHIP_AUDIT.md`.
- `support/artifacts/pr_eg_r1/06_CONVERSATIONAL_CORRECTION.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/06_CONVERSATIONAL_CORRECTION.md`.
- `support/artifacts/pr_eg_r1/07_BOUNDED_PERSONAL_CONVERSATION.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/07_BOUNDED_PERSONAL_CONVERSATION.md`.
- `support/artifacts/pr_eg_r1/08_NPC_REQUESTS_AND_NEGOTIATION.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/08_NPC_REQUESTS_AND_NEGOTIATION.md`.
- `support/artifacts/pr_eg_r1/09_DISTANT_CONVERSATIONAL_REFERENCES.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/09_DISTANT_CONVERSATIONAL_REFERENCES.md`.
- `support/artifacts/pr_eg_r1/10_COMMITMENT_RETENTION.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/10_COMMITMENT_RETENTION.md`.
- `support/artifacts/pr_eg_r1/11_PROVIDER_EFFICIENCY.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/11_PROVIDER_EFFICIENCY.md`.
- `support/artifacts/pr_eg_r1/12_FROZEN_INDEPENDENT_HOLDOUTS.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/12_FROZEN_INDEPENDENT_HOLDOUTS.md`.
- `support/artifacts/pr_eg_r1/13_FRESH_FIFTEEN_TURN_CONVERSATION.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/13_FRESH_FIFTEEN_TURN_CONVERSATION.md`.
- `support/artifacts/pr_eg_r1/14_SECOND_LIVE_QUALIFICATION.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/14_SECOND_LIVE_QUALIFICATION.md`.
- `support/artifacts/pr_eg_r1/15_STATE_INTEGRITY_AUDIT.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/15_STATE_INTEGRITY_AUDIT.md`.
- `support/artifacts/pr_eg_r1/16_REGRESSION_COMPARISON.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/16_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_eg_r1/17_REMAINING_ISSUES.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/17_REMAINING_ISSUES.md`.
- `support/artifacts/pr_eg_r1/18_FINAL_RECOMMENDATION.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/18_FINAL_RECOMMENDATION.md`.
- `support/artifacts/pr_eg_r1/19_CHANGED_FILE_INVENTORY.md`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/19_CHANGED_FILE_INVENTORY.md`.
- `support/artifacts/pr_eg_r1/baseline_junit.xml`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/baseline_junit.xml`.
- `support/artifacts/pr_eg_r1/live.usage.jsonl`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/live.usage.jsonl`.
- `support/artifacts/pr_eg_r1/live_qualification.json`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/live_qualification.json`.
- `support/artifacts/pr_eg_r1/regression_junit.xml`: PR-EG-R1 report or fresh-provider evidence. Canonical source: `artifacts/pr_eg_r1/regression_junit.xml`.

## Explicit omissions

- `artifacts/pr_eg_r1/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r1/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
