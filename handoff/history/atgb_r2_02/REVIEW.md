# Campaign

Campaign: ATGB-R2-02 Bounded Speech-Participant Grounding Repair
Identifier: `atgb_r2_02`
Date: 2026-10-19
Generated: 2026-10-19T12:00:00+00:00
Purpose: Repair ordinary first- and second-person addressee grounding without live provider calls.

# Executive Summary

S03.3 and S05.3 no longer treat grammatical speech as an unidentified NPC. The established runner remains the recipient. S05.3's subject stays unresolved, and the existing resolver returns uncertainty rather than a new rumor. Related variations keep real ambiguity, explicit addressee changes, and off-scene rejection. Slice: 351 passed / 2 preexisting failed. No new relevant regression. Stop for external review.

Objective status: `A — Repair accepted`.

# Changes Made

## Production changes

- game/interaction_completion.py: speech_participant_head applied inside addressed_person_nominal.
- game/ordinary_semantic_ownership.py: first- and second-person roles use the existing present-interlocutor branch.

## Validation changes

- tests/test_atgb_r2_02_speech_participant_grounding.py: 46 deterministic tests. Frozen holdouts unchanged.

## Tooling changes

- No reusable tool or production framework changed.

## Documentation changes

- Eight reports in development/reports/atgb_r2_02/ and a short docs/NEXT_SESSION.md orientation update.

## Generated artifacts

- Baseline reproduction, after replay, source diff, regression count, evidence packet, and review ZIP.

# What Was Tested

- **Focused tests:** 46 passed, 0 failed. Historical S03.3 and S05.3 replays included.
- **Broader relevant tests:** 353 collected in the relevant slice: 351 passed / 2 failed. Both failures reproduce on the pre-repair production files.
- **Full suite:** Not run.
- **Runtime validation:** Offline replay of captured interpretations through grounding, the interpretation decision, and the existing social resolver. Resolver result is genuine_uncertainty with no topic revealed.
- **Model/runtime boundary:** No live provider calls, no prompt or schema edits, no retries.
- **New regressions:** None in the stable slice.
- **Pre-existing failures:** test_raw_chat_stub_covers_commitment_and_addressee and test_chat_hailing_runner_with_can_you_question_routes_social. Both fail on b012c3d copies of the two production files.
- **Self-contained bundle review:** Bundle contains the eight reports, production diff, modified sources, new tests, before/after replay, generalization and authority reports, regression count, repository status, verdict, and next action.

# Behavioral Evidence

## Evidence Packet: atgb_r2_02

Runs / turns: `1` / `2`
Runtime/model boundary: Offline host grounding and existing resolver. No live model narration.

### Representative success

Example: `S03.3-after`
Player classification: `representative_player_behavior, human_captured`
Player: If I ask you again later, will you still tell me that same thing?
GM: Host decision text is empty. Resolver hint: Player spoke with Tavern Runner. No authored answer was available. Narrate honest uncertainty or a bounded conversational reply without inventing facts the speaker does not have.
Automated result: `grounding_pass_recipient_tavern_runner`
Human review: `UNREVIEWED` - Repair-effect replay awaits external review.
Source: `artifacts/atgb/atgb_r2_02/historical_replay_after.json`

### Representative failure

No example observed in this campaign.

### Evaluator disagreement

No example observed in this campaign.

### Ambiguous/unexpected

No example observed in this campaign.

### Stress probe

No example observed in this campaign.

### All evaluator disagreements

No example observed in this campaign.


# Decisions Requiring Human Review

- Accept or reject verdict A before any further conversational implementation.
- Do not treat this package as authorization for a live provider trial or a subject-binding repair.

# Known Problems / Unresolved Findings

## Campaign-specific

- S05.3 recipient is grounded, but the host still does not ask which account 'that' means. The resolver reports authored uncertainty.
- Related variations were written with this repair. They are not independent held-out evidence.

## Pre-existing baseline

- Two slice failures named above.
- Full suite not run.
- R1-07 live acceptance remains pending.
- Preexisting dirty worktree was preserved. No commit or push.

# Missing Concepts / Future Capabilities

- No new subsystem. Question-subject binding stays with its existing owner and was not repaired.

# What This Campaign Does NOT Prove

- Improved natural dialogue, a correct answer to the S03.3 promise question, a focused S05.3 topic clarification, independent generalization, a gameplay-benchmark score, or full-suite green.

# Recommended Next Step

Stop for external review. Do not implement a follow-on repair or live trial from this pass.

# Review Bundle Contents

Bundle file count: `21`
Bundle ZIP size: `000000072306` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_r2_02/08_final_verdict_and_handoff.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_r2_02/08_final_verdict_and_handoff.md`.
- `support/artifacts/validation_evidence/atgb_r2_02/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/atgb_r2_02/evidence_summary.md`.
- `support/artifacts/validation_evidence/atgb_r2_02/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/atgb_r2_02/evidence_manifest.json`.
- `support/development/reports/atgb_r2_02/01_baseline_and_reproduction.md`: Baseline and historical reproduction. Canonical source: `development/reports/atgb_r2_02/01_baseline_and_reproduction.md`.
- `support/development/reports/atgb_r2_02/02_root_cause_and_repair.md`: Root cause and repair rationale. Canonical source: `development/reports/atgb_r2_02/02_root_cause_and_repair.md`.
- `support/development/reports/atgb_r2_02/03_implementation_diff.md`: Implementation summary. Canonical source: `development/reports/atgb_r2_02/03_implementation_diff.md`.
- `support/development/reports/atgb_r2_02/04_historical_replay_results.md`: Before and after historical replay. Canonical source: `development/reports/atgb_r2_02/04_historical_replay_results.md`.
- `support/development/reports/atgb_r2_02/05_generalization_and_ambiguity.md`: Speech-role and ambiguity results. Canonical source: `development/reports/atgb_r2_02/05_generalization_and_ambiguity.md`.
- `support/development/reports/atgb_r2_02/06_authority_validation.md`: Authority and state-integrity results. Canonical source: `development/reports/atgb_r2_02/06_authority_validation.md`.
- `support/development/reports/atgb_r2_02/07_regression_and_performance.md`: Regression counts and performance limits. Canonical source: `development/reports/atgb_r2_02/07_regression_and_performance.md`.
- `support/game/interaction_completion.py`: Nominal extraction after the repair. Canonical source: `game/interaction_completion.py`.
- `support/game/ordinary_semantic_ownership.py`: Addressee grounding after the repair. Canonical source: `game/ordinary_semantic_ownership.py`.
- `support/tests/test_atgb_r2_02_speech_participant_grounding.py`: New and historical grounding tests. Canonical source: `tests/test_atgb_r2_02_speech_participant_grounding.py`.
- `support/artifacts/atgb/atgb_r2_02/source.diff`: Production source diff. Canonical source: `artifacts/atgb/atgb_r2_02/source.diff`.
- `support/artifacts/atgb/atgb_r2_02/baseline_reproduction.json`: Pre-repair S03.3 and S05.3 host decisions. Canonical source: `artifacts/atgb/atgb_r2_02/baseline_reproduction.json`.
- `support/artifacts/atgb/atgb_r2_02/historical_replay_after.json`: Post-repair grounding, decision, and resolver results. Canonical source: `artifacts/atgb/atgb_r2_02/historical_replay_after.json`.
- `support/artifacts/atgb/atgb_r2_02/regression_slice.txt`: Slice command and counts. Canonical source: `artifacts/atgb/atgb_r2_02/regression_slice.txt`.
- `support/artifacts/atgb/atgb_r2_02/repository_status.txt`: Branch, commit refusal, and file scope. Canonical source: `artifacts/atgb/atgb_r2_02/repository_status.txt`.
- `support/docs/NEXT_SESSION.md`: Updated session orientation. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
