# NEXT_SESSION

Ashen Thrones — Product Realization. Updated 2026-10-18 / ATGB-05.
Read `docs/DEVELOPMENT_CONSTITUTION.md` first, then this orientation and the
relevant authorities below.

## Current position

Reconciliation architecture is closed (AR-CA). Product Realization progressed
beyond PR-BL through PR-EF integration and PR-EG discovery. The latest repository
verdict, PR-EG-R6-R4-R1, is **C — inconclusive / below acceptance; do not integrate**.
Caching reuse does not establish semantic support. No migration or PR-EH follows
automatically.

ATGB v1 is operationally established: adopted corpus, frozen reproducible start,
scenario isolation, provider accounting, complete 37-turn live capture, preserved
transcripts/telemetry, rubric and human-review tools. Selection is original
S01–S03; continuation S04 full trial 2 and S05–S10 trial 1. Original partial S04
trial 1 remains separate historical evidence.

The user reports a completed independent ChatGPT (GPT-6) provisional assessment.
**Its two source files are missing: import and per-turn verification are pending.**
Request-reported counts are interpretation 18/16/3, response 10/25/2, authority
35/0/2 (pass/fail/uncertain), not verified aggregates. AI-assisted assessment is
not authenticated human scoring. Human review remains pending;
`human_review_attestation: false` must stay false for the AI assessment.

Conversational competence is not established. The project is not yet reliably
playable by its intended conversational standard. Response adequacy is the
greatest reported weakness. Direct questions sometimes work; natural remarks,
follow-up references, corrections, contextual NPC dialogue and distinguishing
conversation from actions frequently break down in captured replies.

## Last work and recommended next action

ATGB-05 reconciled orientation and preserved baseline evidence; assessment import
is incomplete. Review `handoff/CURRENT_REVIEW.md` and `handoff/CURRENT_REVIEW.zip`.
Full status, limitations and investigation recommendations:
`development/reports/atgb_05_baseline_preservation.md`.

Locate original `ATGB_04_review_judgments.json` and `ATGB_04_review_summary.md`.
Repository, attachments, common user folders, parent AI Dungeon Master directory
and its ZIP-member search found neither. Preserve originals; verify 37 exact
turn/trial IDs, rubric consistency, summary/count agreement and setup caveats.
Record discrepancies and request clarification; do not recreate evaluator labels
from totals or route AI judgments through human-attested reporting.

Next Product Realization investigation: corrections vs mechanical revisions
(S08.2/S06.4/S04.2), related nonanswers/reference loss (S02.2–4/S05.2/S03.5), then
ordinary social remarks/needless clarification (S01.4/S03.3). Establish the earliest
demonstrable wrong pipeline decision before selecting repairs. The report lists
subsystem candidates, evidence needed, diagnostic approaches and validation.
These recommendations do not authorize repairs during this handoff pass.

Future relevant changes should distinguish original failing interactions, related
variations, existing benchmark corpus and independent generalization when
available. Deterministic PASS does not establish conversational competence.
Previously exposed held-out scenarios are not unseen generalization evidence.
Avoid another broad architectural overhaul without causal evidence of necessity.

## Remaining investigations and validation baseline

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
- Authenticated human review and AI-assessment import remain pending; existing
  transcripts can still scope the next investigation.

Validation baseline: 37 captured turns, not 37 successes. No full-suite green or
broad conversational improvement claim. ATGB-05 offline integrity results:
`artifacts/atgb/atgb_05/validation_results.json`. No new provider requests.

## Minimum authorities and evidence

- `development/reports/atgb_05_baseline_preservation.md`
- `artifacts/atgb/atgb_04/review_index.json` and `conversational_review.md`
- `artifacts/atgb/atgb_04/scenario_qualifications.md` and `evidence_provenance.md`
- `development/reports/atgb_02_benchmark_specification.md`
- `development/reports/atgb_03b_provider_accounting_integrity.md`
- `development/reports/atgb_03c_live_baseline_continuation.md`
- `artifacts/pr_eg_r6_r4_r1/04_CURRENT_SEMANTIC_PIPELINE.md` and `38_FINAL_VERDICT.md`
- `docs/validation_evidence_standard.md`, `docs/product_realization_validation.md`
- `development/campaigns/reconciliation/AR-CA_campaign6_chassis_strategy_closeout.md`

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
or push requested. ATGB-05 changes documentation/evidence/export only.
Stop for review: no gameplay repairs, live-provider requests or new benchmark
infrastructure campaign in this pass.
