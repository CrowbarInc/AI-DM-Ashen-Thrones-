# Campaign

Campaign: PR-EG — Dialogue Quality and Bounded Improvisation
Identifier: `pr_eg_dialogue_quality_20261016`
Date: 2026-10-16
Generated: 2026-10-17T00:32:45.895801+00:00
Purpose: Improve NPC dialogue relevance and bounded improvisation. Do not start PR-EH.

# Executive Summary

# 01 — Executive Summary

PR-EG adds a small dialogue-authority record on top of the PR-EF-R4 conversational authorization contract. The record names the information the player asked for, what the NPC is allowed to know, whether a harmless remark is permitted, and when the answer is already determined. It does not replace resolvers, and it does not promote NPC speech into world truth.

## Implemented changes

- A question is classified by the information it requests (a name, whether something is watched, who made an object, a personal feeling, an opinion, a hidden fact, a promise, a mystery, a relationship, or a rumor). An established sentence is used only when it actually supports that request. “The street beyond the gate is the north road” no longer counts as an answer to “is the north road watched?”
- A reply plan that claims an authoritative answer without a revealed topic is rewritten to genuine uncertainty with speech authority none. That was the contradictory plan.
- Personal and opinion questions may use the existing harmless-subjective lane. The speech is marked non-canonical.
- When the permitted answer is a closed unknown, refusal, or unestablished consequential request, narration is skipped and the NPC says a short in-character line. “Who forged the lantern?” no longer spends a strict-social narration and a retry.
- If a personal reply mixes a harmless remark with a new world claim, the harmless quoted remark can be kept and the retry is not sent.
- Conversational commitments (an opinion, a refusal, an admitted uncertainty) are stored on the session’s conversational context, capped, and saved with the session. They are not world facts.
- Validation records `internal_authority_voice`, `unauthorized_consequential_claim`, and `answer_not_relevant` when those failures occur. The old “settled here” line is not used once a dialogue-authority record exists.

## Player-facing improvements

On the fresh twelve-turn `/api/chat` conversation:

- “What is the street called?” was answered with the north road.
- “Who forged the lantern?” was “I couldn’t tell you.” in one interpretation call (1,965 input tokens), against the historical three-call, 50,784-input-token path.
- “What troubles you?” became “It’s this watch, mostly.” One narration call, no retry. The earlier run of the same question spent a narration and a retry (54,871 input tokens) and then fell back to “I couldn’t tell you.”
- The password was not disclosed. The reward was not promised. The walk through the gate used the existing movement resolver. World topics did not change on any turn.

## Critical limitations

The same conversation still fails as play in several turns:

- “Has anyone been keeping an eye on it after dark?” was answered “That has not been established in the information available to you.” That is internal authority language, and it is not Mara speaking.
- “What did you mean by that?” forgot the road name she had just given and, after a narration plus retry (52,957 input tokens), said “I couldn’t tell you.”
- “Do you prefer the morning or the evening?” still did not state a preference.
- “I meant the road, not how you feel” was treated as an undo.
- The reward request was refused as an unavailable action, in engine wording.
- After leaving the courtyard, the return to the earlier watch question asked which person was meant. It did not continue the conversation.
- A successful social narration still sends on the order of 26,000 input tokens. The skip removes the extra retry for determined questions. It does not shrink the prompt for questions that still need a model line.

Deterministic frozen holdouts pass every scored dimension. That is not the same as the live transcript passing them.

## Recommendation

**C — PR-EG REQUIRES REPAIR**

Answer relevance, natural uncertainty, and bounded improvisation are real on the paths that reach a resolved NPC with a classified request. The continuous conversation still contains an internal-voice answer, a broken follow-up, an evasive preference, and one pathological narration-plus-retry. Those are important dialogue failures. No critical authority violation was observed: hidden information stayed hidden, topics were not rewritten, and the movement turn used the existing resolver.

Do not start PR-EH. Stop for external review.


Objective status: `C — PR-EG REQUIRES REPAIR`.

# Changes Made

## Production changes

- Dialogue-authority record distinguishes the requested information, NPC posture, and non-canonical speech.
- A topic answers a question only when it supports that request.
- Determined knowledge gaps skip narration. A harmless quoted remark can be kept without a retry.

## Validation changes

- Frozen holdouts in tests/fixtures/pr_eg_dialogue_holdouts.json.
- tests/test_pr_eg_dialogue_quality.py scores dimensions separately.

## Tooling changes

- tools/validate_pr_eg.py

## Documentation changes

- Reports 01–18 under artifacts/pr_eg.

## Generated artifacts

- Fresh /api/chat twelve-turn conversation before and after quote recovery.
- Baseline and post-implementation regression junit.

# What Was Tested

- **Focused tests:** 73 passed, including frozen holdout dimensions and quote recovery. Provider not used for the holdout scorer.
- **Broader relevant tests:** Family 350 passed / 19 failed. No new failing identities. One historical failure now passes.
- **Full suite:** Not run. The established conversational family was run.
- **Runtime validation:** Fresh gpt-4.1-mini-2025-04-14 through TestClient /api/chat. Twelve turns, 16 calls, 145400 input tokens, one retry.
- **Model/runtime boundary:** Configured gpt-4.1-mini. Observed gpt-4.1-mini-2025-04-14.
- **New regressions:** None in the final family measurement.
- **Pre-existing failures:** Nineteen of the twenty PR-EF-R2 identities remain. One, the repeated-question clean refusal, now passes.
- **Self-contained bundle review:** Eighteen reports, frozen holdouts referenced from the tests, two live conversations, and the regression junit. No .env and no active campaign saves.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Accept or reject C — PR-EG requires repair.
- Do not begin PR-EH from this package.

# Known Problems / Unresolved Findings

## Campaign-specific

- A road-watch follow-up was answered with internal authority language and was not Mara's line.
- The follow-up to the road's name forgot that answer and spent a narration plus retry.
- A preference question stayed ignorance after one narration.
- A clarification was treated as an undo, and a promise request was answered as an unavailable action.

## Pre-existing baseline

- Nineteen inherited regression failures from the R2 family.

# Missing Concepts / Future Capabilities

- Using a public scene sentence, such as Mara looking concerned, as a partial spoken answer.
- A prompt small enough that one social narration is not tens of thousands of input tokens.

# What This Campaign Does NOT Prove

- That every follow-up stays with the NPC who just spoke.
- That two fresh runs of the same follow-up take the same route. Turn 3 differed between the two live runs.
- That save/load of commitments was exercised on the disposable live campaign. That campaign directory was removed. The unit test covers the session shape.
- That the nineteen remaining family failures are unchanged in their assertion text. Identities were compared. Bodies were not re-audited.

# Recommended Next Step

External review. Stop. Do not start PR-EH.

# Review Bundle Contents

Bundle file count: `28`
Bundle ZIP size: `000000091681` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg/02_BASELINE_AND_ENVIRONMENT.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/02_BASELINE_AND_ENVIRONMENT.md`.
- `support/artifacts/pr_eg/03_DIALOGUE_FAILURE_RECONSTRUCTION.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/03_DIALOGUE_FAILURE_RECONSTRUCTION.md`.
- `support/artifacts/pr_eg/04_DIALOGUE_AUTHORITY_DESIGN.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/04_DIALOGUE_AUTHORITY_DESIGN.md`.
- `support/artifacts/pr_eg/05_ANSWER_RELEVANCE.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/05_ANSWER_RELEVANCE.md`.
- `support/artifacts/pr_eg/06_BOUNDED_IMPROVISATION.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/06_BOUNDED_IMPROVISATION.md`.
- `support/artifacts/pr_eg/07_DIALOGUE_CONTINUITY.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/07_DIALOGUE_CONTINUITY.md`.
- `support/artifacts/pr_eg/08_NPC_KNOWLEDGE_AND_UNCERTAINTY.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/08_NPC_KNOWLEDGE_AND_UNCERTAINTY.md`.
- `support/artifacts/pr_eg/09_NPC_CHARACTERIZATION.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/09_NPC_CHARACTERIZATION.md`.
- `support/artifacts/pr_eg/10_RESPONSE_GENERATION_AND_VALIDATION.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/10_RESPONSE_GENERATION_AND_VALIDATION.md`.
- `support/artifacts/pr_eg/11_PROVIDER_EFFICIENCY.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/11_PROVIDER_EFFICIENCY.md`.
- `support/artifacts/pr_eg/12_FROZEN_DIALOGUE_HOLDOUTS.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/12_FROZEN_DIALOGUE_HOLDOUTS.md`.
- `support/artifacts/pr_eg/13_FRESH_LIVE_CONVERSATION.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/13_FRESH_LIVE_CONVERSATION.md`.
- `support/artifacts/pr_eg/14_STATE_INTEGRITY_AUDIT.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/14_STATE_INTEGRITY_AUDIT.md`.
- `support/artifacts/pr_eg/15_REGRESSION_COMPARISON.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/15_REGRESSION_COMPARISON.md`.
- `support/artifacts/pr_eg/16_REMAINING_ISSUES.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/16_REMAINING_ISSUES.md`.
- `support/artifacts/pr_eg/17_FINAL_RECOMMENDATION.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/17_FINAL_RECOMMENDATION.md`.
- `support/artifacts/pr_eg/18_CHANGED_FILE_INVENTORY.md`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/18_CHANGED_FILE_INVENTORY.md`.
- `support/artifacts/pr_eg/baseline_junit.xml`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/baseline_junit.xml`.
- `support/artifacts/pr_eg/baseline_output.txt`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/baseline_output.txt`.
- `support/artifacts/pr_eg/live.usage.jsonl`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/live.usage.jsonl`.
- `support/artifacts/pr_eg/live_before_quote_recovery.usage.jsonl`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/live_before_quote_recovery.usage.jsonl`.
- `support/artifacts/pr_eg/live_qualification.json`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/live_qualification.json`.
- `support/artifacts/pr_eg/live_qualification_before_quote_recovery.json`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/live_qualification_before_quote_recovery.json`.
- `support/artifacts/pr_eg/regression_junit.xml`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/regression_junit.xml`.
- `support/artifacts/pr_eg/regression_output.txt`: PR-EG report or fresh-provider evidence. Canonical source: `artifacts/pr_eg/regression_output.txt`.

## Explicit omissions

- `artifacts/pr_eg/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
