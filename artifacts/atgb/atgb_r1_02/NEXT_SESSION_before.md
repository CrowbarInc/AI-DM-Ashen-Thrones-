# NEXT_SESSION

Ashen Thrones — Product Realization. Updated 2026-10-18 / ATGB-R1-01.
Read `docs/DEVELOPMENT_CONSTITUTION.md` first, then this orientation and the
relevant authorities below.

## Current position

Reconciliation architecture is closed (AR-CA). Product Realization progressed
beyond PR-BL through PR-EF integration and PR-EG discovery. PR-EG-R6-R4-R1
remains **C — inconclusive / below acceptance; do not integrate**. Caching reuse
does not establish semantic support. No migration or PR-EH follows automatically.

PR-EG-R6-R5 is a later diagnostic, not an integration acceptance. Its verdict is
**B — diagnosis supported with limitations**
(`artifacts/pr_eg_r6_r5/36_FINAL_VERDICT.md`). Production success is 59/164,
validation 18/54, correction tag 0/25 on the full corpus. Authorized-plan
substitution reaches 44/54 on validation and 45/54 with expression disabled.
Those arms are interventions, not a production forecast. R1, R2, and R3 are
unimplemented pending review. ATGB-05A’s orientation named only R4-R1; that
omission was staleness. R5 does not replace R4-R1’s integration ban.

ATGB v1 is operationally established: adopted corpus, frozen reproducible start,
scenario isolation, provider accounting, complete 37-turn live capture, preserved
transcripts/telemetry, rubric and human-review tools. Selection is original
S01–S03; continuation S04 full trial 2 and S05–S10 trial 1. Original partial S04
trial 1 remains separate historical evidence.

The independent ChatGPT (GPT-6) provisional assessment is imported and verified:
all 37 authoritative IDs/trials match, rubric consistency and summary aggregates
agree, and original files are preserved byte-for-byte. Counts are interpretation
18/16/3, response 10/25/2, authority 35/0/2 (pass/fail/uncertain). ATGB v1 initial
operational setup is closed. AI-assisted assessment is not authenticated human
scoring; that remains pending. `human_review_attestation: false` is preserved and
the existing human-reporting guard still rejects the unattested assessment.

Conversational competence is not established. The project is not yet reliably
playable by its intended conversational standard. Response adequacy is the
greatest reported weakness. Direct questions sometimes work; natural remarks,
follow-up references, corrections, contextual NPC dialogue and distinguishing
conversation from actions frequently break down in captured replies.

## Last work and recommended next action

ATGB-R1-01 investigated S08.2 only. Report:
`development/reports/atgb_r1_01_s08_2_causal_trace.md`. Standard review:
`handoff/CURRENT_REVIEW.md` and `handoff/CURRENT_REVIEW.zip`.

S08.2’s sentence is the host `no_pending_intention` template in
`_pending_revision_decision`. The utterance matched `i meant` and no gameplay
intention was pending. Failure class: contract. Relationship to PR-EG-R6-R5:
**C — different mechanism**. R1’s `bind()` repair does not reach this turn.
The justified follow-on is a narrower entry condition that keeps the PR-EF-R4
revision holdouts. Do not implement until this review is accepted.

ATGB-05A remains the assessment-import closeout. Its review and hashes stay at
`development/reports/atgb_05_baseline_preservation.md` and
`artifacts/atgb/atgb_05a/`. No evaluator judgments changed in either pass.

Future relevant changes should distinguish original failing interactions, related
variations, existing benchmark corpus and independent generalization when
available. Deterministic PASS does not establish conversational competence.
Previously exposed held-out scenarios are not unseen generalization evidence.
Avoid another broad architectural overhaul without causal evidence of necessity.

## Remaining investigations and validation baseline

- S02.2–S02.4, S03.3/S05.3, S01.4/S07.2, S06.4, and S04.2 were compared only as
  controls. Their earliest decisions differ from S08.2. No repair is authorized
  for them.
- S03.4/S05.4 faction agenda flags: unresolved authority candidates, not confirmed
  violations. Preserve uncertain judgments; inspect full state/event provenance.
- S07/S09 opening context was not delivered before turn 1. Six observations require
  criterion-specific review; unsupported criteria stay uncertain/not evaluated.
  Missing setup is not a gameplay failure.
- ATGB-03B documented two pre-existing regression failures: routing-metadata
  dictionary expectation and missing `answer_sufficiency`. Reset-write failures
  and successful retries are separate environment evidence.
- Application admission accounting does not independently count SDK transport
  retries. Original completion-only and continuation admission scopes differ.
- Authenticated human review remains pending; provisional assessment import is
  complete. Original judgments and disagreements must remain preserved.

Validation baseline: 37 captured turns, not 37 successes. No full-suite green or
broad conversational improvement claim. ATGB-05A offline integrity results:
`artifacts/atgb/atgb_05a/assessment_import_verification.json`. No new provider requests.

## Minimum authorities and evidence

- `development/reports/atgb_r1_01_s08_2_causal_trace.md`
- `artifacts/atgb/atgb_03c/S08/transcript.md` and `result.json`
- `artifacts/pr_eg_r6_r5/36_FINAL_VERDICT.md`, `11_PRODUCTION_BASELINE.md`, and `32_REPAIR_PRIORITIZATION.md`
- `development/reports/atgb_05_baseline_preservation.md`
- `artifacts/atgb/atgb_05a/assessment/ATGB_04_review_summary.md` and `ATGB_04_review_judgments.json`
- `artifacts/pr_eg_r6_r4_r1/38_FINAL_VERDICT.md` and `04_CURRENT_SEMANTIC_PIPELINE.md`
- `docs/validation_evidence_standard.md`, `docs/product_realization_validation.md`
- `tests/fixtures/pr_ef_r4_holdouts.json` (`correction_pending`, `correction_already_executed`, `correction_nothing_pending`)

Retain state/domain owners and validation authorities. Conversational memory is
not structured-fact authority; narration cannot create a transition. Do not
reopen settled boundaries or add a second router without new evidence. Prior
history, decisions and deferred items are preserved verbatim in
`artifacts/atgb/atgb_05/NEXT_SESSION_before.md`; historical wait-for-capture or
stop-at-PR-BL instructions there do not describe current development status.

## Worktree and stop boundary

Extensive dirty/untracked work predates ATGB-05, including production, canonical
play-session data, governance and generated evidence. Preserve it. Do not revert
human play data or alter the protected latest human-playtest folder. No commit
or push requested. ATGB-05/05A change documentation/evidence/export only.
Stop for review: ATGB-R1-01 implemented no repair. No gameplay change, live
provider call, baseline edit, or authority change in this pass.
