# NEXT_SESSION

Ashen Thrones — Product Realization. Updated 2026-10-28 / PR-PLAY-06.
Read `docs/DEVELOPMENT_CONSTITUTION.md` first, then this orientation and the
relevant authorities below.

## Latest bounded opening budget repair — PR-PLAY-06

2026-10-28: **B — Conditionally ready**, pending external review. Historical
October 28 ledger confirms incomplete/max_output_tokens at 600, invalid JSON,
rejected opening and no gameplay commit. Opening-only default now 3000 output
tokens, ASHEN_OPENING_MAX_OUTPUT_TOKENS bounded 1..4096; explicit unfinished
provider status rejects even complete JSON. Ordinary controlled narration stays
600; aggregate budgets, model/schema, authority, retries and rollback unchanged.
No prompt reduction: two-scene inventory retains uncertain overlapping context.
Rich declared fixture 3726 chars/~932 estimated tokens; tokenizer unavailable.
58 focused pass; broader 361 pass / five entry-source-reproduced preexisting
failures (three rich emission, stale attestation, conversation assertion).
257 protected data/experiment files and inventory unchanged. No live/connectivity
calls, benchmark, new state structures, PR-EG integration, secrets, commit or push.
Reports/manual: development/campaigns/product_realization/pr_play_06/.
Evidence: artifacts/pr_play_06/. Review: handoff/CURRENT_REVIEW.md and timestamped
ZIP. PR_PLAY_06_LIVE_OPENING_TEST.txt supersedes PR-PLAY-05: one Start only after
external review; 3000/600 verified, six admissions, unchanged aggregate ceilings,
zero retries, bounded state snapshots, isolated data and evidence export.
Stop after package. Next action: external review; live adequacy remains unproven.

## Latest closure and diagnostics — PR-PLAY-05

2026-10-27: **B — Conditionally ready for one operator opening after external
review.** Two obsolete journal/placeholder HTTP fixtures now use valid declared
structured openings. Three rich emission cases reproduce on hash-verified pre04
source, remain failing and are excluded; no threshold/acceptance relaxation.
Opt-in ASHEN_GENERATION_DIAGNOSTICS=1 extends the existing provider usage ledger
with extraction/JSON/envelope/finish/validation and final commit observations.
No raw-response logging; SDK text segments replace response-object stringification.
39 focused checks pass, including all 18 PR-PLAY-04 checks; broader 238 pass / 5
demonstrated preexisting failures. Original live failure cause remains unknown;
600/600 is possible-truncation evidence only. Frozen attestation remains stale.
Reports and one-Start manual: development/campaigns/product_realization/pr_play_05/.
Evidence: artifacts/pr_play_05/; review: handoff/CURRENT_REVIEW.md and timestamped
ZIP. PR_PLAY_05_LIVE_OPENING_TEST.txt supersedes PR-PLAY-02 for the next trial.
Stop after review package; no live trial until external review accepts it.
No live/connectivity calls, prompt/schema/model/cap changes, extra provider
operations, normal-save/frozen/experiment changes, commit or push. Dirty entry
work retained. PR-PLAY-04 acceptance/commit-integrity repair remains valid in
its deterministic scope. No benchmark or broad gameplay-quality claim.

## Latest repair — PR-PLAY-04

2026-10-26: **B — Conditional acceptance.** A failed `scene_opening` is no longer
completed by a generic information-request fallback, and opening progression is
not committed until a valid opening is accepted. Explicit failure leaves
`campaign_started` false and restores turn, time pressure, and faction state.
Deterministic matrix: 18 passed. No live provider call. Live generation of a
valid opening remains unproven. Do not start another manual playtest until this
review is accepted. Reports:
`development/campaigns/product_realization/pr_play_04/`. Evidence:
`artifacts/pr_play_04/`. Review: `handoff/CURRENT_REVIEW.md` and the timestamped
ZIP. No commit or push.

## Prior investigation — PR-PLAY-03

2026-10-26: **C — Missing provider evidence.** Original
artifacts/pr_play_02/manual-20261026-201939.zip confirms one metered opening call,
26,593/600/27,193 tokens, zero retries; plain/missing_structured_envelope rejection.
Raw provider output and provider finish metadata were not retained; accounting
completion_status is not provider completion. Primary mechanism remains unresolved.
Recovery retains scene_opening but seals generic safe_nonresolution as complete,
then marks campaign started and commits turn/time/faction progression. Those ticks
are engine-owned; narration failure alone does not prove unauthorized mutation.
Uncaught pipeline exception rolls back turn only and permits duplicate pressure.

Six offline controls exercise actual endpoint functions/SDK stub; preserved-seed
invalid control reproduces exact fallback and state categories. Valid structured
control delivered; rich supplemental control rejected by authority. 27 assertions
and 38 existing contract tests pass. No HTTP/browser/live/benchmark/repair-effect
claim. Reports/ownership: development/campaigns/product_realization/pr_play_03/;
evidence: artifacts/pr_play_03/; packet: artifacts/validation_evidence/pr_play_03/;
review: handoff/CURRENT_REVIEW.md and timestamped ZIP. Primary cause remains unknown.

Recommend one separately authorized PR-PLAY-04 opening failure acceptance/commit
repair in existing API owner, preserving initialized state, failing explicitly,
and allowing retry without duplicate opening-only progression. No prompt/parser/cap
repair from speculation; no new durable schema/subsystem. Production, prompts,
schemas, normal saves, frozen ATGB and experiments unchanged; no live/provider
connectivity work, secrets, commit or push. Existing dirty tree preserved.
Stop for external review; no implementation or live authority carries forward.

## Latest controlled-play preparation — PR-PLAY-02

2026-10-19: **B — Conditionally ready.** Added opt-in
ASHEN_PLAYTEST_DISABLE_SDK_RETRIES=1 to all seven existing provider constructors;
reuse existing host retry suppression, process-local atomic admission limit six,
durable ledger and isolated ASHEN_DATA_DIR. Added playtest-only rejection telemetry
and nonmutating exhausted-submission gates. Normal retry defaults/payloads unchanged.
30 new checks pass; completed regression totals 354 passed / 2 preexisting failures
(stale ATGB source attestation and exact provider metadata assertion), reproduced
on saved entry source. Explicit HTTP lifespan test blocked at 15s; no repair.
445 protected normal-data/experiment/prior-handoff hashes and inventory unchanged.

Eight reports/manual artifact: development/reports/pr_play_02/; test, constructor,
admission/concurrency, entry-diff and integrity evidence: artifacts/pr_play_02/.
Review: handoff/CURRENT_REVIEW.md and timestamped ZIP. The old ATGB manifest remains
unattested for current sources; do not infer ATGB-worker readiness. Manual launch
uses the normal app, one worker/no reload, fresh disposable data and one continuous
process. No restarting to continue the six-attempt session. New Campaign then
Start Campaign are separate. No live/provider-connectivity work performed.
R1/R2 scopes, frozen baseline, PR-PLAY-01 environment-blocked status and PR-EG ban
remain unchanged. No prompt/schema/gameplay/state/model/endpoint changes; no secrets,
commit or push. Stop for external review, then separately approve operator-run
PR_PLAY_02_LIVE_PLAYTEST.txt. UI/live behavior, latency and cost remain unverified.

## Latest integrated checkpoint — PR-PLAY-01

2026-10-19: **C — Environment blocked.** Single nonbillable DNS lookup for
api.openai.com failed gaierror 11001 (6.839 ms); zero provider admissions or
live gameplay turns. Normal startup/UI/opening and integrated play remain
unvalidated. Existing reset/routing/correction/grounding/evidence tests: 204
passed (structural_only); no HTTP transport run. All 2,228 protected entry
hashes match. R2-02 deterministic acceptance, R2-04 conditional acceptance and
R1 live-pending status unchanged. No demonstrated post-repair gameplay improvement.

Eight reports and unexecuted manual handoff: development/reports/pr_play_01/.
Readiness/test/integrity evidence: artifacts/pr_play_01/; review:
handoff/CURRENT_REVIEW.md and timestamped ZIP. Normal UI host retry flag does
not explicitly disable SDK transport retries; require a reviewed zero-retry
launch control before later strictly bounded play. No new gameplay repair
justified; next action external review, then approved disposable manual test
in a provider-capable environment. No implementation, further live execution,
network repair or PR-EG integration authorized by this recommendation.
Production/prompts/schema/state/frozen/prior evidence unchanged; existing dirty
tree preserved. No secrets, commit or push. Stop for external review.

## Latest bounded implementation — ATGB-R2-04

2026-10-19: **B — Conditional.** Existing live interpretation system instruction
now distinguishes requested detail/answer-bearing evidence from related topics,
preserves unique follow-up subjects/rejected interpretations, and separates an
unavailable answer from subject ambiguity. Schema/parser/host/gameplay unchanged.
Focused 198 passed; broader non-HTTP 332 passed, 39 explicitly environment-blocked
HTTP cases; matching entry slice 314 passed/39 deselected. Four R2-03 raw controls
retain honest S02 limitations and S05 account clarification with grounded runner.
Instruction +442 characters (~111 chars/4 estimated tokens); no provider calls.
Reports: development/reports/atgb_r2_04/; evidence: artifacts/atgb/atgb_r2_04/;
review: handoff/CURRENT_REVIEW.md and timestamped ZIP. Retain for external review;
live behavioral improvement/authority and complete HTTP regression unproven.
R1-07 acceptance remains pending; R2-02 accepted scope unchanged. No frozen-data
or experimental integration changes; dirty entry tree preserved, no commit/push.
Stop for external review; no next implementation or live trial authorized.

## Latest investigation — ATGB-R2-03

2026-10-19: **C — Live interpretation dependency.** Offline only; no repair.
S02.2/.4 select public but non-answering board categories; S02.3 also misbinds
curfew timing to patrol timing. Curfew hour is unauthored; posted last-seen clue
is gated, not an omitted public answer. S05.3 keeps the repaired runner recipient
but runner-versus-board account remains ambiguous after the intervening failure.
Existing contract can emit honest limitation or targeted account clarification.
16 decision controls, four raw adapter controls, four current-request captures,
three membership controls and one valid synthetic resolver control; no live call.
Original complete requests/preturn snapshots unavailable. 1,311 protected hashes
unchanged. No production/prompt/schema/gameplay/frozen/experimental changes.
Reports: development/reports/atgb_r2_03/; evidence: artifacts/atgb/atgb_r2_03/;
packet: artifacts/validation_evidence/atgb_r2_03/; review: handoff/CURRENT_REVIEW.md
and timestamped ZIP. Recommend one separately authorized R2-04 bounded production
question-to-evidence interpretation-contract implementation/qualification, with
live acceptance required; no extra offline investigation by default. R2-02 stays
accepted in deterministic scope; R1-07 live acceptance pending; S08.2 not reopened.
Stop for external review. No commit/push; preexisting dirty tree preserved.

## Latest repair — ATGB-R2-02

2026-10-19: **A — Repair accepted** for speech-participant grounding only.
S03.3/S05.3 no longer treat "you again later" / "me more" as unidentified
people; the established runner stays the recipient. Subject of S05.3 stays
unresolved. Eight reports: development/reports/atgb_r2_02/; replay and diff:
artifacts/atgb/atgb_r2_02/; packet: artifacts/validation_evidence/atgb_r2_02/;
review: handoff/CURRENT_REVIEW.md and timestamped ZIP. Focused tests 46 passed.
Regression slice 351 passed / 2 preexisting failed. No live provider call,
prompt, schema, new persistent state, or PR-EG integration. Frozen ATGB
baseline unchanged. No commit or push. Stop for external review. Do not start
another conversational repair or a live trial from this pass. R1-07 live
acceptance remains pending. The R2-01 stop below is historical.

## Latest prioritization — ATGB-R2-01

2026-10-19: **A — Implementation target established** (prioritization only).
Offline original-log inspection identifies shared host addressee rejection in
S03.3/S05.3 despite raw model runner selection. Recommend bounded ATGB-R2-02
speech-participant grounding in existing ordinary_semantic_ownership /
interaction_completion owners. S05 topic ambiguity remains separate; no broad
referent memory, PR-EG integration or S08.2 reopening. R1 mechanical routing stays
validated within scope; R1-07 contract stays deterministically implemented and
pending live acceptance. Eight reports: development/reports/atgb_r2_01/;
traces/scores/provenance: artifacts/atgb/atgb_r2_01/; historical behavioral packet:
artifacts/validation_evidence/atgb_r2_01/; review: handoff/CURRENT_REVIEW.md and ZIP.
No production/prompt/schema/provider/gameplay/frozen-baseline changes. Existing
dirty tree preserved. No new gameplay or repair-effect test, no benchmark score.
Stop for external review before any ATGB-R2-02 implementation or live execution.
Earlier recommendations below are historical and carry no automatic authority.

## Latest readiness pass — ATGB-R1-09

2026-10-19: **D — Inconclusive; DEFER.** Phase A BLOCKED: api.openai.com DNS
resolution fails with socket.gaierror 11001; TCP/TLS cannot reach connection stages.
No live trials, provider admissions, pending setup or gameplay execution (0/4).
R1-07 reviewed owners and all 811 R1-08 protected hashes match; frozen baseline
verified. Eight reports: development/reports/atgb_r1_09/; diagnostic/ledger/integrity
evidence: artifacts/atgb/atgb_r1_09/; review: handoff/CURRENT_REVIEW.md and ZIP.
Credentials present, validity untested; model gpt-4.1-mini, retries policy 0,
timeout 45s, no proxy configured. DNS root cause and prior failures' causes unknown.
No product repair-effect, generalization, benchmark or live authority result.
R1-07 conditional implementation remains unaccepted live; no new repair justified.
External review, then environment owner to restore/verify provider-host resolution
before considering separately authorized validation. Stop: unused budget does not
authorize automatic continuation. Production/prompts/schema/data/experiments and
prior evidence unchanged. Earlier pass stop/proposal language below is historical.

## Latest validation — ATGB-R1-08

2026-10-19: **D — Inconclusive**. Reports: development/reports/atgb_r1_08/;
evidence: artifacts/atgb/atgb_r1_08/; packet: artifacts/validation_evidence/atgb_r1_08/.
R1-07 production files match reviewed ZIP; all 1,047 prior protected hashes match.
L1 fresh isolated S08 readiness passed with one-admission cap and zero SDK retries,
but its one dispatch failed with APIConnectionError. Tokens/cost/returned version
unknown. Mandatory stop: L2/L3/L4 not run; no retries or further live authority.
Actual messages include R1-07 instructions and relevant public evidence. No model
interpretation exists; no repair-effect or mechanical-control result. World, scene,
character, combat and full session unchanged; only failure transcript appended.
Durable ledger counts one admission despite response completion counters showing zero.
No production/prompt/schema/frozen corpus/experiment/gameplay-data changes.
Review: handoff/CURRENT_REVIEW.md and timestamped ZIP. Withhold live S08.2 acceptance;
external review, then separately authorize a new pass in a provider-capable environment.
Do not retry this pass automatically or implement a fix from the connection failure.
The older conditional implementation and historical stop language below is preserved.

## Current position

ATGB-R1-07 bounded contract/evidence repair is implemented; **B — Conditional**
pending external review. Eight reports: `development/reports/atgb_r1_07/`;
evidence: `artifacts/atgb/atgb_r1_07/`; current review export:
`handoff/CURRENT_REVIEW.zip` and timestamped ZIP. Existing interpretation owner
now distinguishes conversational correction, GM clarification need and mechanical
revision, and selects public evidence for the corrected underlying question.
Existing answer branch adds a receipt only for resolved REFERENT corrections with
selected evidence and no operations. Schema shape, provider dispatch and revision
guard unchanged. No experimental integration or live calls.

Main deterministic slice: 238 passed (209 existing + 29 new). Broader slice:
23 passed / 1 failed; the same provider-metadata/live-guard failure reproduces
with entry source (23/1). Two attempts stalled and were interrupted, including
HTTP TestClient coverage; neither is a completed result. Saved L1/L2/L3 replayed
offline: old interpretations still clarify; explicit substituted interpretations
answer with acknowledgment and public facts. This does not prove live selection,
semantic repair, benchmark improvement or independent generalization. Protected
data/experiments/prior ATGB artifacts match entry hashes; readiness test's generated
pending_control.json was restored byte-for-byte from the prior review ZIP.

Stop after review packaging. Await external review before separately authorized
ATGB-R1-08 live validation. Proposed scope is in report 08; no live authority
carries forward. Earlier R1-06 stop/authorization language below is historical;
the user's explicit R1-07 request authorized this bounded implementation.

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

## Latest investigation and stop boundary — ATGB-R1-06

ATGB-R1-06 offline causal investigation completed: **B — Conditional**; primary
failure class contract. Eight reports are indexed by
`development/reports/atgb_r1_06_conversational_disposition_and_evidence_selection.md`.
Evidence: `artifacts/atgb/atgb_r1_06/`; historical behavioral packet:
`artifacts/validation_evidence/atgb_r1_06/`; latest review:
`handoff/CURRENT_REVIEW.md` / ZIP and timestamped CURRENT_REVIEW ZIP.

L1/L2 (R1-05) and L3 (R1-03) recognize people versus weather but select
CLARIFICATION and no public evidence. Relevant public people passages and the
full prior reply are in the actual requests. Earliest wrong runtime decision is
the interpretation disposition/evidence result; schema wording causality remains
a hypothesis. Host and immutable emission faithfully deliver the wrong question.
**Correction to the historical L3 summary below:** raw L3 trace DOES reach
`_pending_revision_decision`, which returns null. Do not repeat the older
not-reached claim. Historical artifacts/judgments remain unchanged.

Recommend one separately authorized R1-07 contract/evidence repair in the existing
interpretation owner, with minimal existing answer-branch acknowledgment; retain
mechanical revision and genuine clarification. No empty-unresolved-reference veto,
new classifier, extra automatic call, PR-EG integration or context enlargement.
Report 07 specifies deterministic gates and separately authorized live validation.
No implementation or live-provider authority is carried forward automatically.

Only reports, evidence, review exports and this orientation changed. Production,
prompts/schema, experiments, frozen baseline and gameplay state are unchanged;
protected hashes and ZIP verification are packaged. No new tests or live calls;
no repair-effect, broad competence or full-suite claim. **Stop for external review
before ATGB-R1-07.** The R1-05 section below is historical context, not the current
next-action authorization.

## Prior R1-05 work and recommendation (historical)

ATGB-R1-05 controlled live continuation completed: **B — Partial / Outcome B**.
Report: `development/reports/atgb_r1_05_controlled_live_validation.md`; eight reports
under `development/reports/atgb_r1_05/`, raw/normalized traces and before/after state
under `artifacts/atgb/atgb_r1_05/`, behavioral packet under
`artifacts/validation_evidence/atgb_r1_05/`. Review: `handoff/CURRENT_REVIEW.zip`
and timestamped CURRENT_REVIEW(20261019-...).zip.

L1/L2 original correction now reaches the repaired revision gate, which abstains.
Both live responses still ask redundant confirmation and select no people facts;
earliest semantic failure is model clarification posture/empty evidence selection,
matching R1-03 L3. L4 valid live revision of production-created ambiguous ASK keeps
status pending and does not execute. Its model topic/recipient conflation remains
a limitation. World/character/combat/scene/time/turn/clocks unchanged in all trials.
Three responses, 3/6 admissions (1/2 each), zero retries/continuations, 6475 measured
tokens; cost unavailable. Configured gpt-4.1-mini, returned dated 2025-04-14 model.
Ten current import/mode safety tests pass; no full suite. All 3,996 predecessor
entry hashes match. Production/prompts/models/frozen baseline/experiments unchanged.
One launch approval rejection resolved by explicit user transfer approval; two local
payload previews (first fail-closed store-binding check, corrected runner passes)
made no admissions. Measured trials all preflight-ready and independently isolated.

R1-04 readiness/control remains unchanged and its 167-test deterministic result is
historical evidence. The new R1-05 runner uses its gate/control; old R1-03 runner
remains prohibited. Global source-manifest staleness and HTTP coverage limitations
persist. Judgments are provisional AI-assisted, not authenticated human scoring.

Await external review before ATGB-R1-06. Recommend only an offline causal
investigation/contract proposal for the saved L1/L2 evidence-selection and redundant
clarification defect against R1-03 L3. No semantic implementation, prompt optimization,
live calls or PR-EG integration authorized by this recommendation.

### Prior R1-03 evidence (preserved historical context)

ATGB-R1-03 controlled live validation completed on 2026-10-19 with **D — Inconclusive**.
Report: `development/reports/atgb_r1_03_controlled_live_validation.md`; eight reports
under `development/reports/atgb_r1_03/`; raw/normalized traces and accounting under
`artifacts/atgb/atgb_r1_03/`. Production R1-02 repair matches its reviewed ZIP;
3,564 protected hashes unchanged. Current non-HTTP boundary tests: 102 passed,
three API tests deselected; initial HTTP slice interrupted at environment boundary.

L1 APIConnectionError and L2 InternalServerError prevented original-wording model
results. L3 paraphrase recognized people but selected no evidence and asked
redundant confirmation; repaired gate was not reached. L4 live control INVALID:
fixture imports activated test defaults disabling interpretation; generic fallback
advanced isolated time/turn/factions and cleared pending intention. No live
authority-preservation or repair-regression conclusion from L4. Canonical player
state unchanged. Three admissions, one valid completed live trial, no retries or
continuations, failed-call usage unavailable. Production/prompts/models unchanged.

ATGB-R1-02 remains a deterministic routing repair, not demonstrated live adequacy.
No experimental integration. R1-04 recovery completed without live calls; R1-05 has now supplied the bounded
original/control live evidence above. No semantic repair is authorized.

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
Historical R1-05 stop boundary: this earlier pass changed validation-runner,
documentation and generated evidence/export files only. No production or frozen
baseline edit, experimental integration, commit or push. R1-06 was subsequently authorized and is now complete; do not begin R1-07
or make further live calls without new authority.
