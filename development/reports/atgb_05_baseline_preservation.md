# ATGB-05 — Baseline preservation and session reconciliation

2026-10-18 / ATGB-05A. **Complete: provisional assessment imported and verified; initial ATGB v1 operational setup closed.**
Documentation/evidence only; no gameplay repair, provider request, benchmark
rerun, expectation change, or reporting-tool change.

## ATGB v1 status

| Milestone | Repository-supported status |
| --- | --- |
| Operational benchmark readiness | Complete: adopted corpus, frozen starting state, isolated scenarios, request-accounting safeguards, rubric and human-review tools |
| Initial live evidence capture | Complete: 37 authoritative turns, transcripts and telemetry preserved |
| Provisional independent assessment | Complete: original AI-assisted assessment imported byte-for-byte and verified against all 37 authoritative turns |
| Authenticated human scoring | Pending; existing self-attestation is not identity authentication |
| Conversational gameplay competence | Not established |

Operational readiness is not criterion eligibility or evidence that the game is
playable. S07/S09 opening delivery is limited. Previously exposed held-out
scenarios are not independent unseen generalization. No composite score exists.

## Imported provisional assessment and provenance

ATGB-05A located the supplied originals in the workspace root:
`ATGB_04_review_judgments.json` and `ATGB_04_review_summary.md`. Both remain
unchanged there; byte-identical evidence copies are preserved under
`artifacts/atgb/atgb_05a/assessment/`. `source_manifest.json` records their original
paths, preserved paths, byte sizes and SHA-256 hashes.

The assessment was produced by ChatGPT (GPT-6), independently of Cursor's
implementation process (supplied provenance). It is AI-assisted transcript
assessment, not authenticated human scoring. Original metadata remains
`human_review_attestation: false`. No labels, explanations, timestamps or summary
contents were altered. The human reporting tool rejects the exact original
assessment for lack of explicit human attestation; that rejection is expected
and preserved, not bypassed. No official human report was generated.

### Verification outcome

`artifacts/atgb/atgb_05a/assessment_import_verification.json` records no
identified discrepancies: 37 unique authoritative review IDs exactly once;
scenario, turn, conversation and trial identities match; baseline text and state
match original results; rubric labels, explanations and severity/clarification
constraints conform. All aggregate claims in the supplied summary agree with
individual entries, including determinate denominators and rounded percentages,
evidence classes, severity, clarification and continuity. This verifies artifact
consistency, not evaluator infallibility or human adjudication.

| Dimension | Pass | Fail | Uncertain |
| --- | ---: | ---: | ---: |
| Interpretation | 18 | 16 | 3 |
| Response adequacy | 10 | 25 | 2 |
| Authority compliance | 35 | 0 | 2 |

Response adequacy is the greatest demonstrated provisional weakness. Uncertain
is not success. The 35/35 determinate authority figure is not an overall safety
rate; S03.4/S05.4 remain unresolved and bounded state is incomplete evidence.
No composite score is calculated. The original summary surfaces authority
uncertainty and major failure families before aggregates.

The summary also matches 25 major, 3 minor and no confirmed critical defects;
1 necessary, 5 unnecessary and 1 missing focused clarification; 11 preserved,
11 lost and 15 not-applicable continuity labels. Response counts remain split:
development-visible 7 pass / 18 fail; related 2 / 2; previously exposed held-out
1 pass / 5 fail / 2 uncertain. None is independently unseen evidence.

All six S07/S09 entries retain explanations of undelivered opening/shout/posture
limits. S07.1/S07.3 retain uncertain interpretation and response; S07.4 retains
uncertain interpretation. Other judgments concern independently supported
criteria and do not presume opening delivery. S03.4/S05.4 retain authority
`uncertain`, major response failure, and faction-flag investigation explanations;
neither is relabeled a confirmed violation.

ATGB-05's missing-file search and unverified request metadata remain historical
in its original artifacts and `artifacts/atgb/atgb_05a/ATGB_05_report_before_05a.md`.
Its old `validation_results.json` describes the earlier blocked pass, not current
import status. The original files and ATGB-05A verification supersede that blocker.

## Baseline and development position

ATGB-04 selects original ATGB-03 S01–S03 (13 turns), ATGB-03C S04 full trial 2
(4), and S05–S10 trial 1 (20). Original S04 trial 1's two observations remain
separate historical evidence: 39 observations, 37 selected baseline turns.
No trials are spliced or overwritten. Original completion-only and continuation
admission ledgers retain different scopes; SDK transport retries are not counted
independently. Versions remain ATGB-02 / ATGB-01 / atgb-rubric-01 /
ATGB-02-s07-held-out: 25 development-visible, 4 related, 8 exposed held-out turns.

Authorities reviewed: Development Constitution, Validation Evidence Standard,
Product Realization Validation, Review Handoff Standard; ATGB-01 design/catalog/
feasibility; ATGB-02 specification/implementation/execution; ATGB-02A readiness;
ATGB-03/03B/03C execution and ATGB-04 authoritative review package/reporting tools.
Historical blank forms remain preparation artifacts, not provisional judgments.

AR-CA closed Reconciliation architecture. Product Realization progressed beyond
PR-BL. PR-EF's bounded authority integration remained below full acceptance
(`artifacts/pr_ef_gm_authority/12_FINAL_RECOMMENDATION.md`). Later
PR-EG-R6-R4-R1's `38_FINAL_VERDICT.md` is C, inconclusive/below acceptance: caching
reuse works, semantic support and human ground truth are unresolved; do not
integrate. Its `04_CURRENT_SEMANTIC_PIPELINE.md` identifies current unified
planning, host eligibility, correspondence, sufficiency, authorization and sealed
emission stages. No migration or PR-EH follows from those experiments.

The game is not yet reliably playable by its intended conversational standard.
Architectural closure and deterministic checks do not establish that standard.
The provisional assessment documents conversational intent misclassification, corrections treated
as mechanical revisions, related nonanswers, lost references, needless
clarification, exposed mechanical fallbacks and weak ordinary social remarks.
Captured replies provide direct examples; the recommendations below do not
alter the evaluator's per-turn scores.

## Recommended investigations — no repairs authorized here

1. **Corrections mistaken for mechanical revisions.** S08.2 responds to “I meant
   the people, not the weather” with an unexecuted-intention revision message;
   S06.4 sets aside an intention when returning to character/requesting a rumor;
   S04.2 rejects an addressee correction. Candidate stages: live/contract
   interpretation (`game/live_chat_interpretation.py`, `semantic_interpreter.py`),
   API communication mode/revision precedence and conversational orchestration.
   Needed evidence: captured act/recipient classification, pending intention,
   decision metadata and final-response provenance. Trace the earliest incorrect
   selection before choosing a repair. Validate a future repair on originals in
   full context, varied meaning corrections and legitimate action revisions,
   corpus regression, and separately labeled independent unseen evidence.
2. **Related nonanswers and reference loss.** S02.2–4 repeat board stock instead
   of handling curfew timing/correction/follow-up; S05.2 exposes “I cannot provide
   a validated response”; S03.5 lists facts instead of comparing accounts.
   Candidates: `game/conversational_continuity.py`, unified semantic planning,
   information authorization/sufficiency and final realization. Needed evidence:
   actual delivered history, requested relation/role, selected sources and
   propositions, coverage/sufficiency rejection and fallback provenance. Compare
   the requested relation with the selected proposition to locate the earliest
   unsupported/discarded decision. S03.4/S08.4 reference material not delivered
   earlier in their actual trials; do not replace actual context with the script.
   Validate originals, source/recipient variations, grounded unknowns, the corpus
   and unseen source families when available. Do not invent curfew hours or facts.
3. **Social remarks and avoidable clarification.** S01.4 gives a ruling/no-roll
   fallback to “Fair enough”; S03.3 asks which person despite preceding runner
   dialogue; S01.3 loses an implied addressee. Candidates: orchestration,
   continuity/recipient binding, interpretation and expressive dialogue eligibility.
   Needed evidence: active interlocutor, pending clarification, act classification,
   owner eligibility and response origin. Determine whether context is unavailable
   or an existing owner never receives it. A future separately authorized
   diagnostic can use saved telemetry and offline stubs, which cannot establish
   naturalness. Validate full-context originals, varied remarks, genuinely
   ambiguous controls, corpus regression and independent evidence when available.
   S07 examples retain opening-context caveats.

Root cause remains unresolved until pipeline evidence establishes it. No
diagnostic gameplay execution begins here. Prefer a bounded investigation over
another architectural overhaul; distinguish original reproduction, related
variations, corpus regression and independent generalization in future claims.

## Known limitations and remaining investigations

- S03.4/S05.4: the assessment records unrelated faction agenda flags after
  conversational turns. Preserve as unresolved authority-investigation
  candidates, not confirmed violations. Inspect full before/after flag values and
  domain commit/event provenance; bounded flag-name projections cannot establish
  causation or authorization. Evaluator uncertainty is preserved in the imported original.
- S07/S09: six observations need criterion-specific review. Opening facts were
  authored but not delivered before turn 1; unsupported criteria stay uncertain/
  not evaluated. Missing setup is not automatically a gameplay failure.
- ATGB-03B's two pre-existing regression failures concern a routing-metadata
  dictionary expectation and missing `answer_sufficiency`; both reproduced before
  repair. Windows reset-write failures and successful retries are separate
  environment evidence. No full-suite green claim here.
- SDK retries, single environment/selected trials, uncontrolled sampling,
  API-only capture, bounded state projections and exposed held-out material limit
  claims. Authenticated human scoring remains pending after provisional import.

## Change summary and validation (ATGB-05 and ATGB-05A)

Replaced contradictory session orientation with current status and evidence-led
next work. Archived its exact previous bytes at
`artifacts/atgb/atgb_05/NEXT_SESSION_before.md`, preserving historical decisions
and deferred work. Added this report, request-reported metadata, preservation and
integrity evidence, and an explicit standard review-handoff configuration.
Generated standard review Markdown/manifest/ZIP. No production, tests, corpus,
rubric, frozen baseline, governance authority or reporting implementation edited.

`artifacts/atgb/atgb_05/validation_results.json` records actual checks and scope.
Protected hashes cover gameplay/UI, canonical session data, corpus/frozen state,
harness and ATGB-03/03C/04 evidence. Existing offline review tests verify exact
selection, source text/state, trial boundaries, setup caveats and reporting
rejection behavior. The earlier blocked-pass records remain historical; current verification is in
`artifacts/atgb/atgb_05a/assessment_import_verification.json`.
No provider calls, gameplay reruns, broad regression or semantic improvement claim.

ATGB-05A adds byte-identical assessment copies and source hashes, verifies all
judgments and summary counts offline, updates this report and NEXT_SESSION, and
regenerates the standard review handoff. All 21 existing offline human-review and
handoff tests passed. All 1,620 entry-protected files and the
609 original ATGB-05 protected files remain unchanged. Original evaluator files
remain unchanged. Existing human-review/handoff tests and isolated ZIP checks
are recorded under `artifacts/atgb/atgb_05a/`; no formal human performance result
is claimed. No gameplay, test expectations, reporting implementation or benchmark
framework changed.

ATGB v1 initial operational setup is closed: evidence capture and provisional
independent assessment are complete; authenticated human scoring is pending;
conversational competence is not established. Stop and await review before any
Product Realization investigation. No repair, live request or new ATGB campaign
is initiated.
