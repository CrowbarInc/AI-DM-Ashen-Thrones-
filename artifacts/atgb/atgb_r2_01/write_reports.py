"""Write the eight offline prioritization reports and explicit review support."""
from build_review import *
import importlib.util

texts = {}
texts['01_baseline_and_evidence_inventory.md'] = '''# 01 — Baseline and Evidence Inventory

ATGB-R2-01 • 2026-10-19 • offline investigation • no implementation authority.

## Current repository and authority

The branch and HEAD are captured in `artifacts/atgb/atgb_r2_01/repository_identity.json`. The working tree was already extensively dirty, including production modules, canonical play-session data, governance, tests/evidence and current review exports. HEAD alone does not identify the running baseline. `repository_status_before.txt` and `entry_hashes.json` record this pass's entry state; `integrity_verification.json` compares protected bytes at exit. Existing changes are preserved. No commit or push.

Mandatory authorities read: `docs/DEVELOPMENT_CONSTITUTION.md`, `docs/NEXT_SESSION.md`, `docs/validation_evidence_standard.md`, `docs/product_realization_validation.md`; also `docs/review_handoff_standard.md` and `docs/state_authority_model.md`. Requested `support/docs/NEXT_SESSION.md` is absent from the checkout: `support/` is the portable review layout, not a second authority. Canonical `docs/NEXT_SESSION.md` is used. No AGENTS.md was found in the project file inventory; `.agents` contains no additional instruction file.

## Frozen historical baseline, recomputed

Authoritative assessment: `artifacts/atgb/atgb_05a/assessment/ATGB_04_review_judgments.json`, alongside its original summary. The import-verification closeout is `development/reports/atgb_05_baseline_preservation.md`. This pass recomputed the counts from the preserved judgments (`baseline_verification.json`):

| Dimension | Pass | Fail | Uncertain | Determinate fraction |
|---|---:|---:|---:|---:|
| Interpretation | 18 | 16 | 3 | 18/34 |
| Response adequacy | 10 | 25 | 2 | 10/35 |
| Authority | 35 | 0 | 2 | 35/35 |

These are historical AI-assisted judgments, not authenticated human scoring (`human_review_attestation: false`) and not current post-repair performance. Authority has two uncertain cases (S03.4/S05.4 faction flags); 35/35 is not an overall safety rate. No critical authority violation was confirmed by that bounded assessment. No historical judgment was edited.

The 37 authoritative turns are original S01–S03, continuation S04 trial 2 and S05–S10 trial 1. Partial S04 trial 1 is separate evidence. Partition counts are 25 development-visible, four related variations, eight previously exposed held-out turns; the latter are not unseen independent generalization. Missing authored openings in S07/S09 limit opening-dependent criteria. They do not make a rules fallback to an ordinary remark appropriate.

## R1-01 through R1-09 status

| Pass | Established result | What it does not establish |
|---|---|---|
| R1-01 | Historical S08.2 host revision-entry misrouting diagnosed; PR-EG bind distinct | Raw model label was not retained in that initial reconstruction; no repair |
| R1-02 | Mechanical correction routing implemented; 105 new + 28 frozen tests pass; wider 443/9 matches nine entry failures | Empty-evidence response still fails; no end-to-end adequacy |
| R1-03 | One valid live paraphrase shows redundant clarification/empty refs; original attempts fail; L4 invalid due import environment leakage | Invalid L4 cannot prove live safety; old claim guard not reached is superseded by raw-trace review |
| R1-04 | Import-safe readiness/control recovery; 167 targeted tests pass | Infrastructure result, not semantic repair |
| R1-05 | Two valid original-wording trials avoid mechanical revision; legitimate pending revision control works within tested scope | Both conversations remain inadequate; topic/recipient issues remain |
| R1-06 | Actual saved requests contain public people passages and prior reply; earliest wrong completion is disposition/selection | Prompt clause causality not proven; raw L3 guard is reached and returns null |
| R1-07 | Conversational correction contract and bounded answer receipt implemented; main slice 238 passes (209 existing, 29 new), broader 23/1 matches entry | Substituted interpretations are deterministic controls, not live acceptance |
| R1-08 | One failed dispatch, mandatory stop; no model interpretation | No live effect, regression or acceptance result |
| R1-09 | DNS failure documented; zero live admissions; DEFER | Connectivity remains unresolved; no inference about model behavior |

Mechanical correction routing is repaired and validated within tested scope. The conversational correction contract is implemented and deterministically validated. Latest live conversational acceptance remains pending. R2 does not reopen S08.2 implementation.

## Evidence inventory and precedence

1. Original `artifacts/atgb/atgb_03/S01–S03/{transcript.md,result.json,stores/.../session_log.jsonl}` and `artifacts/atgb/atgb_03c/S05,S07,S08/...`: exact inputs, outputs, raw interpretations, adapted records, routing, bounded state and telemetry. Selected exact fields with canonical path/hash are in `representative_traces.json`; full result files and selected transcripts accompany the bundle.
2. Frozen `data/validation/atgb/`: scenario intent, authorized facts and disclosure constraints, not proof of provider-message contents. S02 hours are explicitly unauthored; route clue is gated by investigation.
3. R1 reports and original R1-03/05 traces, R1-06 reconstruction, R1-07 change review and R1-08/09 verdicts: repair chronology and limits. Original error records remain historical.
4. Final `artifacts/pr_eg_r6_r5/`: baseline.jsonl, summary.json, first_failures.json, intervention reports 13–22, attribution 25, performance 30, prioritization 32 and verdict 36. Raw baseline counts verified here: 59/164; correction tag 0/25. Validation 18/54; authorized-plan intervention 44/54, expression-disabled control 45/54. These are different populations/arms, not ATGB gains or production forecasts.
5. Relevant Chapter II owner documentation: PR-EA orchestration REVIEW, PR-EB continuity REVIEW, PR-EF conversational authority contract and remaining issues, PR-EF-R4 authorization/ambiguity contract and final recommendation. Final PR-EG-R6-R4-R1 verdict still forbids integration; R5 is a diagnostic, not migration acceptance. Existing owners already cover conversation, interaction focus, grounding, evidence and emission.
6. Current source: `interaction_completion.py`, `ordinary_semantic_ownership.py`, `conversational_orchestration.py`, `live_chat_interpretation.py`, `conversational_continuity.py`; proposals remain subordinate to deterministic authority.

## Limits

No fresh gameplay execution, tests of repair effect, provider calls, DNS diagnostics or benchmark run occurred. Initial ATGB raw requests are not retained in the selected original captures; do not assume evaluation-only facts were sent. Raw model JSON and projected public evidence ARE retained in the session logs. Later R1 actual messages are available for their separate correction cases. Current-source static reconstruction and isolated unmodified regex probes explain a path; they are not a historical instruction-pointer trace or a repaired-system run. Human review remains pending; exposure estimates beyond observed examples are qualitative inferences. New reports/evidence and a concise canonical orientation update are permitted review outputs, not production changes.
'''

texts['02_failure_family_reconstruction.md'] = '''# 02 — Failure Family Reconstruction

All quoted exchanges below are exact from original captures. `representative_traces.json` embeds original raw model JSON, adapted record, host decision, prior exchanges, expected criteria, bounded state, output, telemetry, source path and hash for 19 selected turns. Original capture judgments remain intact; new causal classifications here are provisional analysis. Model fields from a single completion are co-produced: no internal temporal ordering is invented.

## F1 — Referent continuity: split addressee from topic

### S03.3 (development-visible, trial 1)

1. Input: “If I ask you again later, will you still tell me that same thing?”
2. Prior: S03.1 addresses Tavern Runner and hears the patrol rumor; S03.2 asks “Who told you that?” and hears `Tavern Runner says, "I don't know who told me that."`
3. Context: before/after snapshots retain `tavern_runner`. The saved session payload has social interaction focus and delivered exchanges. Three NPCs are available; this does not itself make an active second-person exchange ambiguous. Exact original request messages are indeterminate.
4. Authorized evidence: adapted record selects `npc_latest_reply`, the actual preceding ignorance line. A later promise is not an established world fact. Continue the same speaker and preserve uncertainty rather than inventing future commitment.
5. Model: NPC/QUESTION, ASK target `tavern_runner`, unresolved refs `[]`, subject is whether the runner will repeat the information; explicitly understands the preceding ignorance.
6. Host: `_communication_decision` calls shared `assess_addressee_grounding` before NPC ASK handoff. Stored authorization says unresolved/provider_candidate_only, candidate runner, requires clarification. Host creates pending ambiguous-addressee ASK.
7. Plan: CLARIFY, missing `interlocutor`, no resolver, no narration.
8. Final: “Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted.”
9. Expected: retain the uniquely established speaker, route through existing ASK authority; answer the continuity question with bounded knowledge. Correct routing alone cannot guarantee adequate dialogue or a warranted promise.
10. Earliest demonstrated wrong decision: host rejects the addressee despite model/interaction agreement. High confidence. More specific source diagnosis: speech extraction returns `you again later`; the grounding owner lacks a compatible second-person role branch and falls into unmatched nominal clarification. The isolated unmodified syntax probe confirms extraction; exact historical internal call sequence beyond stored authorization is inferred from matching current source, not newly observed execution.

### S05.3 (development-visible, trial 1)

1. Input: “Tell me more about that.”
2. Prior: runner tells patrol rumor; S05.2 asks about the board, receiving “I cannot provide a validated response to that request.”
3. Context: runner remains active; latest delivered line is a GM failure. Thus *topic antecedent* is genuinely less secure than S03.3. Exact provider request indeterminate.
4. Evidence: model selects `npc:tavern_runner:patrol_rumor`; public projection contains the disclosed rumor. No authorization to invent additional details or reveal the board clue.
5. Model: NPC/CLARIFICATION with ASK runner, unresolved refs empty, requests more patrol-rumor detail.
6. Host: same unresolved-addressee gate, runner as proposed candidate, pending ambiguous ASK.
7. Plan: wrong-slot CLARIFY for interlocutor; no narration.
8. Final: same three-person question as S03.3.
9. Expected: do not mistake the player recipient in “tell me” for an unknown NPC. If topic unclear after the board refusal, ask which account/detail is meant, without inventing facts. A guaranteed runner-rumor answer is not warranted.
10. Earliest definitely incorrect decision: host addressee rejection. Whether the earlier model's definite topic choice is wrong is indeterminate; preserve ambiguity. Pure extraction produces `me more`; its lexical failure explains the matching gate. High confidence in gate failure, medium in exact minimal grammatical repair.

These cases do not show memory deletion. They confirm a shared wrong-slot grounding rejection, while S05 also has a distinct topic-binding ambiguity. S09.2/S10.2 remain secondary historical symptoms, not additional confirmed instances of this precise defect.

## F2 — Question-to-evidence binding

### S02.2, S02.3, S02.4 (development-visible, trial 1)

| Stage | S02.2 | S02.3 | S02.4 |
|---|---|---|---|
| Input | “When does the curfew start?” | “I wasn't asking where the patrol went. I asked when it starts.” | “All right. What did the warning say about where they were last seen?” |
| Prior | S02.1 reads board; broad category description | Same category sentence repeated | Same non-answer twice, then subject changes to warning |
| Context | No clue discovered; curfew hours unauthored | Curfew remains antecedent of “it” | Board route clue still undiscovered |
| Evidence selected | visible:0 | reply:1 | visible:0 |
| Model | GM/QUESTION, subject curfew start time | GM/CLARIFICATION, subject “Timing of the missing patrol start” | GM/QUESTION, patrol last-seen information |
| Host | ANSWER, communication_before_execution | ANSWER despite clarification purpose because selected evidence exists | ANSWER, communication_before_execution |
| Plan/final | Broad board sentence | Same sentence via previous reply | Same sentence |
| Expected | State start time unavailable | Acknowledge corrected time question and specific unknown | Existing authorized investigation route or focused explanation of unavailable posted detail; do not disclose gated clue merely because ground truth knows it |

Exact repeated final: “The notice board lists taxes, curfew rules, and a warning about a missing patrol.” No narration request in these turns. Earliest demonstrated defect for S02.2: selection of authorized but non-answering evidence for a recognized curfew-time question. S02.3 additionally misbinds the subject to “Timing of the missing patrol start”; subject and non-answer selection are co-produced, so internal order is indeterminate. This is not merely correct curfew interpretation followed by poor expression. Host validates membership and concatenates it; no semantic adequacy check is visible. For S02.4, earliest supported boundary is the selected non-answer/answer plan; whether an investigation operation should have been inferred is less certain. Original request messages are unavailable; do not claim the model ignored the hidden clue or a supplied clock hour. Hours are **absent**, category text is **used but insufficient**; last-seen clue is **authored but gated**, not unused public evidence. Confidence high in mismatch and the S02.3 subject error, medium in smallest general repair. Prior characterization as a simple retrieval omission is too broad.

## F3 — Ordinary remarks

S01.4 input: “Fair enough. I'm just getting a sense of the place.” Prior is S01.3's unresolved stew addressee. S07.2 input: “The banners look about finished.” Prior S07.1 delivers a general rain/queue scene summary; the authored opening was not delivered. Ground truth's banner appearance cannot be treated as known to the player/provider.

Both raw interpretations say SESSION/OBSERVATION with empty evidence. S01.4 explicitly requests acknowledgment, has no action components, and its live adapter records SAFE_ABSTENTION/clarification_required; retained record is nevertheless reconsidered by orchestration. S07.2 requests acknowledgment but proposes SOCIAL_SIGNAL. Both final decisions are ANSWER, SESSION/OBSERVATION, answer_only, no resolver and no narration. Final: “I don't have an established ruling for that question. No action or roll has been made.” No gameplay mutation is shown.

Earliest demonstrated wrong decision is model communication ownership (SESSION for ordinary fictional remarks), with a downstream contract hole: empty-evidence non-question acknowledgment has no supported realization branch and SESSION selects rules fallback. This is not demonstrated execution of a misclassified physical action. Expected acknowledgment can assert no new facts; banner facts must not be invented or presumed delivered. High confidence in ownership/fallback sequence; medium confidence in a minimal acknowledgment contract, which would need to cover both interpretation and orchestration. Actual original messages remain indeterminate.

## F4 — Content selection versus expression

S03.5 input: “No, I don't want a new rumor. I want to know if those two accounts match.” Prior S03.4 repeats rumor rather than comparing accounts; S03.3 already lost addressee continuity. Available public rumor is established; full posted route is not discovered. The model selects rumor, broad board sentence, and unrelated serjeant sentence; GM/CLARIFICATION is accepted as ANSWER with selected refs. Final: “The runner heard the patrol vanished near muddy footprints northwest of the crates. The notice board lists taxes, curfew rules, and a warning about a missing patrol. A gate serjeant manages the crowd and keeps one eye on the roster board.”

Earliest supported defect is inadequate selection/answer planning, before mechanical joining. Natural paraphrase would not establish whether accounts match. A sound answer should acknowledge what can and cannot be compared from established evidence. No generation request means there is no observed model expression rewrite to repair in this turn. Raw requests indeterminate; exact model selection and host plan are visible. Confidence high for the plan/content defect, low for broad expression benefit.

Expression-specific comparison: final PR-EG-R6-R5 c06t07 has a correct UNKNOWN host line distorted by expression into a specific claim; report 32 identifies a single paired case. This is a separate mechanism from S03.5's inadequate host plan. Reports 20/22 show 44/54 authorized-plan versus 45/54 expression-disabled; they do not show that rewriting all replies would fix ATGB.

## F5 — Conversational correction comparison

Historical S08.2: “I meant the people, not the weather.” Prior S08.1 describes gate, people and weather. Final: “I don't have an unexecuted intention to revise. What do you want to change?” Context has no pending action; original raw model interpretation is recoverable from the original session log in this pass's trace extract, but R1-01's original causal argument did not retain/use it. The recovered raw completion is GM/CLARIFICATION with empty refs and correction.subject=INTENTION despite recognizing the people/weather contrast. Thus the earliest now-visible incorrect decision is already the completion's disposition/selection; the later host mechanical-revision route is an independently demonstrated additional error, entered even with CLARIFICATION because of the old regex. R1-01's narrower evidence scope and original finding remain historical, unchanged; this supplementary localization does not reopen S08.2 implementation.

Later R1-05 L1/L2 and R1-03 L3 actual requests include prior reply and authorized people facts. Those completions recognize the correction but select CLARIFICATION and no refs, so host asks redundant confirmation. Earliest later wrong runtime decision is co-produced disposition/selection, not PR-EG bind or expression. R1-06 corrects the old L3 not-reached claim: revision guard is reached and abstains. R1-07 changes the contract and receipt deterministically; R1-08/09 supply no model output to evaluate it live. Expected corrected answer remains a future live acceptance requirement. F5 is comparison only, excluded from new implementation ranking.
'''

texts['03_player_impact_assessment.md'] = '''# 03 — Player-Impact Assessment

Ratings describe consequences, not benchmark scores. Frequency beyond selected observed cases is explicitly inference; overlapping families are not summed into a failure rate.

| Family | Coherence | Agency | Immersion | Recoverability | Observed exposure / inferred ordinary-play exposure | Compounding |
|---|---|---|---|---|---|---|
| F1 addressee rejection | Appears to forget speaker while the model and interaction focus agree | Blocks a reasonable NPC follow-up before resolver | Three-person menu and “Nothing has been attempted” interrupt dialogue | Player must rename a person already addressed; S05.4 does so yet gets ignorance | Two confirmed wrong-slot cases, S03.3 and S05.3. Follow-ups likely frequent (inference); no percentage inferred | Pending ambiguous ASK is actually created. S05.4 follows with explicit runner selection; causality of later bad answer or faction flags is unproven |
| F2 question/evidence mismatch | Remembers topic words but misses requested relationship | Prevents extracting useful distinctions and learning what is unknown | Repeated board sentence sounds stuck | S02.3 rephrasing fails; S02.4 changes subject and still gets same sentence | Three selected S02 turns, plus S03.5 related planning failure. Questions likely ubiquitous (inference), mechanisms vary | Repeated non-answer loop is demonstrated across S02.2–4; future false decisions based on it are hypothetical |
| F3 remarks | Misreads conversational purpose | Makes acknowledgment/topic exit difficult | Rules/roll disclaimer breaks fiction | Can continue with an explicit question, but that workaround is inferred rather than measured | Two SESSION/OBSERVATION examples. Incidental remarks likely common (inference); S07 opening limits remain | No gameplay mutation observed; longer-term disengagement is a plausible risk, not measured |
| F4 realization | Generic joins or inappropriate expression damage flow | Could obscure an otherwise adequate answer; S03.5 has no adequate plan | Mechanical list style; expression can overstate facts | Cosmetic rephrasing cannot recover missing content; correct-plan expression cases are narrower | One selected ATGB concatenation with upstream defect; two PR-EG first-expression attributions and one paired validation case. Symptom breadth is not a frequency estimate | PR-EG c06t07 adds a specific claim in final output; historical security score still records zero restricted hits. Later consequences not shown |
| F5 correction | Player correction is misunderstood or redundantly reconfirmed | Recovery from an initial mistake fails | Mechanical intention language or confirmation loop | R1-05 repeats failure despite exact correction | Historical S08.2 plus three later completed correction trials; not a post-R1-07 rate | R1-03 invalid L4 mutated isolated state through harness leakage, a separate defect corrected in readiness infrastructure |

F2 has the broadest likely exposure, but it combines missing facts, gated facts and unused/insufficient evidence. A single safe repair for all of it has not been demonstrated. F1's narrower address-role rejection has unusually strong leverage: an already sensible model proposal is blocked at a deterministic gate. Fixing that gate removes an unnecessary obstacle to player intent without requiring better semantic sampling. Its predicted benefit is removal of wrong-person clarification, not guaranteed quality of the downstream NPC answer.

F3 strongly harms the feel of play and deserves follow-up after F1. Its minimal repair must distinguish an acknowledgment from an attempt, a rules question, a genuine withdrawal and an unsupported factual claim. Current R1-07 already says factual-free acknowledgments may have empty refs, so historical examples alone do not prove that guidance still fails now. There is no post-R1-07 fresh measurement of any candidate family.

Preserve the two historical uncertain authority cases. No causal link from these conversational failures to unauthorized faction progression is established from the bounded snapshots. No numerical projection of playability, time saved or retention is warranted.
'''

texts['04_mechanism_comparison.md'] = '''# 04 — Mechanism Comparison

Legend: **Confirmed** = direct record/source evidence of involvement; **Probable** = strong causal inference; **Possible** = plausible relation without causal identity; **Distinct** = evidence of a different mechanism; **Unknown** = unavailable. A boundary being involved does not mean it is defective.

| Boundary | F1 | F2 | F3 | F4 | F5 |
|---|---|---|---|---|---|
| Context assembly | Unknown exact original messages; model knows speaker | Unknown exact original messages; hours absent from authored world | Unknown original messages; S07 missing opening | Known selected passages, full request unknown | Confirmed adequate actual later R1 requests |
| Antecedent tracking | Confirmed preserved speaker; topic ambiguity distinct in S05 | Distinct subcases: S02.2 recognizes curfew; S02.3 misbinds to patrol start | Possible topic-exit intent | Possible incomplete account comparison | Confirmed correction subject recognized later |
| Interpretation schema | Possible contributing vocabulary | Possible insufficient answer obligation | Probable acknowledgment contract gap | Possible content obligation gap | Confirmed incomplete old contract; R1-07 implemented |
| Live interpretation | Confirmed runner proposed, not lost | Confirmed recognized question + non-answer refs | Confirmed SESSION misownership | Confirmed selected unrelated material | Confirmed later unnecessary CLARIFICATION + [] |
| Evidence selection | Confirmed public selection, irrelevant to recipient rejection | Confirmed semantic mismatch | Confirmed empty refs; permissible for pure acknowledgment | Confirmed inadequate selection before join | Confirmed omissions in pre-R1-07 live trials |
| Referent binding | Confirmed shared addressee authorization rejection | Distinct: not PR-EG bind trace | Distinct from addressee gate in selected remarks | Possible semantic antecedent issue | Distinct from PR-EG bind for S08 |
| Host orchestration | Confirmed premature wrong-slot clarification | Confirmed projects selected refs | Confirmed SESSION/no-answer fallback | Confirmed joins selected passages | Confirmed historical revision overreach, repaired |
| Authority validation | Confirmed blocks ASK; overrejects these addresses | Confirmed membership does not establish relevance | Confirmed no resolver | Confirmed authorized facts do not ensure answer | Confirmed mechanical guards preserved in tested scope |
| Response planning | Confirmed missing interlocutor instead of content handling | Confirmed non-answer becomes ANSWER | Confirmed ruling plan | Confirmed insufficient plan precedes expression | Confirmed wrong clarification disposition historically |
| Realization | Distinct: delivers host rejection | Distinct: faithfully repeats selected passage | Distinct: faithfully emits fallback | Confirmed joins; PR-EG has separate expression distortion | Distinct: zero-generation redundant question |
| Mechanical fallback | Confirmed downstream symptom | Possible generic-unknown alternative | Confirmed established-ruling string | Possible symptom; no single root | Confirmed historical intention prompt |

## Shared and distinct mechanisms

* **Confirmed:** S03.3 and S05.3 share `unresolved_addressee`, candidate runner, lexical speech nominal and existing grounding gate. Raw interpretations already select the speaker; more prompt memory would miss this demonstrated defect.
* **Probable:** Their fine-grained rejection cause is extraction/interpretation of grammatical speech participants: `you again later` and `me more` reach nominal matching. Pure AST-selected helpers reproduce those exact strings. Grounding's singular branch lists him/her/he/she, not second person; nominal-present code bypasses no-nominal active fallback. Full historical function-entry traces were not retained, so source reconstruction remains distinct evidence.
* **Distinct:** S05's “that” may refer to the prior board failure or the earlier rumor. Resolving speaker does not resolve topic. Do not persist a topic indefinitely or select the runner merely because active state exists.
* **Confirmed:** S02.2/3 and S03.5 all allow public passages to stand in for an adequate answer. Their shared projection/join is visible; semantic sufficiency failures vary. F2 and F4 symptoms overlap, so counts must not be added.
* **Confirmed:** S01.4/S07.2 share SESSION/OBSERVATION plus empty evidence and the rules fallback. S07.2 also proposes SOCIAL_SIGNAL; S01.4 does not. They are not both executed physical-action misclassifications.
* **Possible:** F2 and R1-05 empty-ref correction can benefit from clearer selection obligations. R1-07 already changes correction-specific guidance. This does not justify extending that repair wholesale to every question.

## PR-EG reconciliation

Final R5 has 105 baseline failures. Its automated first-failure attribution is operation 20, question proposition 26, source omitted 17, correspondence 5, sufficiency 15, expression 2, residual/evaluation disagreement 20. Wrong-referent code F02 is zero; this does not negate bind rejection, because attribution categories and host reasons differ. False uncertainty is often downstream (44), not 44 independent sufficiency defects. Keep those scoring limitations visible.

R5 R1 targets semantic `bind()`/witness correction deltas. c06t03 explicitly proposes correction but fails `invalid_correction_operation`. ATGB S03.3 proposes NPC ASK and fails `assess_addressee_grounding`. Relationship **Distinct** at specific rejection owners, **Possible** shared high-level conservative overrejection. No reason to merge experimental bind work into the proposed address-role repair. R5 report 20 also records post-plan unaddressed fall-throughs after authorized-plan substitution, including c08t07. This is Possible shared addressee-boundary involvement, not proof of the same grammatical defect; no local call trace establishes identity here.

R5 R2 question/source proposition pairing is **Probable** conceptual correspondence to F2, **Unknown** specific causal identity: original ATGB legacy evidence_refs do not pass through that same paired-proposition gate. Question-only I3 loses two net, source-only I5 loses three, joint arm gains eight. Those interventions do not warrant an ATGB keyword-overlap validator, a new semantic classifier or an expected eight-turn gain.

R5 expression case is **Distinct** from F1/F2/F3 and ATGB S03.5, whose wrong plans already determine final language. Plan intervention 44/54 versus expression-disabled 45/54 argues against broad realization as the first repair. It is not proof expression never matters.

Existing Chapter II ownership is adequate: PR-EB active interaction focus, PR-EF communication contract, PR-EF-R4 shared grounding/authorization, current immutable emission. These should be corrected in place. No evidence establishes a need for a parallel memory store, new router or architecture migration. R4-R1 integration ban remains in force.

Unresolved questions: exact historical provider requests for initial ATGB; minimal grammar normalization that safely separates speech recipient and addressee; downstream answer behavior after F1 gate removal; F2 sufficiency representation in legacy owner; actual model effect of existing R1-07 guidance. None prevents offline prioritization.
'''

texts['05_prioritization_matrix.md'] = '''# 05 — Prioritization Matrix

Judgment scale 1–5: severity 1 cosmetic to 5 blocks meaningful interaction; exposure 1 niche to 5 pervasive inferred play interaction; generalizability 1 isolated to 5 broad coherent mechanism; confidence 1 speculation to 5 direct records plus owning code; feasibility 1 broad redesign to 5 small existing-owner change; safety 1 high authority risk to 5 low regression risk. Exposure is an ordinal inference supported by observed examples, not measured population frequency. Feasibility and safety higher means easier/safer.

Weights: severity .25, exposure .20, generalizability .20, confidence .15, feasibility .10, safety .10. Weighted score = sum(weight × ordinal rating), maximum 5. Scores guide judgment, not empirical efficacy estimates.

| Eligible rank | Candidate boundary | Severity | Exposure | Generality | Confidence | Feasibility | Safety | Weighted |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | F1 shared host speech-role/addressee rejection | 5 | 4 | 4 | 5 | 4 | 3 | 4.30 |
| 2 | F2 legacy question/evidence sufficiency | 5 | 5 | 4 | 3 | 2 | 3 | 4.00 |
| 3 | F3 ordinary remark ownership/acknowledgment | 4 | 4 | 3 | 4 | 4 | 4 | 3.80 |
| 4 | F4 correct-plan expression/assembly quality | 3 | 5 | 3 | 3 | 3 | 4 | 3.50 |
| Excluded | F5 correction comparison, existing R1-07 | 5 | 4 | 3 | 4 | 3 | 4 | 3.95 |

Machine-readable ratings, weights and computed sums: `prioritization_scores.json` and `.csv`. F5's numerical value does not create implementation eligibility; the user explicitly excludes reopening it and latest live acceptance is pending.

## Evidence, uncertainty and expected benefit

F1: two matching host rejections after model selects runner, with persistent active social focus. Highest diagnostic confidence and a deterministic repair boundary; expected benefit is letting reasonable follow-ups reach the existing authority path. Risks: wrong-speaker execution, explicit target override, absent interlocutor, speech recipient confusion, pronoun/topic conflation. Safety is only 3 because the owner guards actual execution and world advancement. Generality 4 refers to grammatical address roles across NPCs, not all anaphora. S05 content ambiguity reduces the breadth of claimed benefit.

F2: repeated S02 non-answers and related S03.5 mismatch, supported conceptually by R5 paired proposition interventions. Highest likely exposure. However hours do not exist, clue disclosure is gated and legacy membership checking cannot prove entailment. A safe bounded semantic sufficiency repair is less specified; use a narrow investigation if chosen. Confidence/feasibility fall below F1. No new world facts should be manufactured to answer a recognized question.

F3: identical SESSION/OBSERVATION fallback in two scenarios and raw model acknowledgment intent. Small existing-owner contract work seems feasible; authority can remain non-mutating. Lower severity/general scope than meaningful NPC questions and some overlap with existing R1-07 acknowledgment guidance. Fixing only the string would mask model ownership; a new ACK speech act is not automatically justified.

F4: many poor-sounding replies, but broad symptom counts confound wrong content with expression. R5 isolates a small expression gain; ATGB S03.5 is wrong before expression. Naturalness-only repair ranks lower despite exposure. Keep correct-plan expression as a future, separately validated boundary.

## Sensitivity and decision stability

F1–F2 gap is 0.30, not decisive numerical separation. Raising F2 diagnostic confidence from 3 to 5 ties at 4.30; raising F2 feasibility by two also ties if combined with one confidence increment. Lowering F1 generality by one and confidence by one puts it at 3.95, below F2. Reducing F1 exposure by one gives 4.10, still narrowly ahead. F3 ties F2 if its generality rises one point, but evidence does not currently establish that broader mechanism.

Thus the ranking is conditional on defensible diagnostic/repair-boundary judgments, not a claim of precise utility. Direct host evidence breaks the close F1/F2 comparison: F1 can remove an established incorrect deterministic rejection without solving general semantic relevance. If owner-level reconstruction disproves the described grammatical boundary, stop and reconsider F2; do not preserve rank by weakening authority. F2's potential total benefit could be larger, but its currently credible one-pass implementation scope is weaker. No fabricated failure rate, aggregate recovery estimate or provider-cost savings is used.
'''

texts['06_repair_candidate_evaluation.md'] = '''# 06 — Repair Candidate Evaluation

Proposals only. No production, prompt or schema changes were made. At least the top three are evaluated here; all future execution requires external review/new scope.

## Candidate 1: F1 — Speech-participant grounding

Observed defect: S03.3/S05.3 raw model selects an active, present runner; shared host addressee decision rejects it using unmatched grammatical speech nominals. Earliest demonstrated failure is host grounding, before resolver; extraction detail is supported by unmodified syntax probes.

Owner: `game/ordinary_semantic_ownership.py::assess_addressee_grounding`; speech-recipient extraction helper `game/interaction_completion.py::addressed_person_nominal`. All existing callers in orchestration, interpretation bridge, ordinary contract and pre-tick gate must consume the same result. Do not repair an individual caller by bypassing the owner.

Shape: distinguish speech addressee from grammatical recipient/complement, then apply existing explicit-wording and bounded active-interlocutor precedence. Second-person “you” can use a uniquely established, present social interlocutor in an NPC exchange; first-person “me” in a tell construction denotes the player, not an unknown NPC. Preserve ambiguous topic handling separately. Explicit names/roles and genuine nonunique nominals remain authoritative inputs; arbitrary model target IDs never settle ambiguity. No phrase-specific ATGB cases or indiscriminate first-word trimming.

Required context: current scene-visible roster, existing active social target, player text and proposed ASK target, existing delivered exchange/ownership when needed to distinguish GM from NPC. No new persisted state or expanded memory window. Treat S05's recent GM refusal as a topic/ownership boundary, not permission to resume an old rumor automatically.

Authority: grounding identifies an addressee only. Existing bridge, knowledge/disclosure, pending intention, resolver and tick rules still govern ASK and effects. A corrected rejection can newly reach a legitimate social resolution, which may have existing time consequences; require the same effects as an equivalent explicit address. Never assert that every NPC ASK is non-mutating.

Performance: no new provider classification, retry or automatic follow-up call. Pure host computation has unmeasured small expected CPU impact. Prompt/context size should not grow. A turn previously stopped at clarification may now incur existing downstream resolver/expression calls; total call/token/latency effect is unknown and must be measured under the standing budget, not described as free or zero. Stop rather than add admissions when that budget is insufficient.

Offline validation: recorded-interpretation reproductions plus unrelated-name role fixtures; all grounding consumers agree; explicit conflict/nonunique/offscene/GM controls; response plan and state-effect equivalence to explicit-address control. Live acceptance: separately authorized production entry, exact raw requests/results, speaker/topic/answer adequacy independently reviewed. Regression surface medium: shared addressee owner, ASK bridge, social resolution, pre-tick eligibility. No whole-engine refactor.

## Candidate 2: F2 — Question-conditioned evidence sufficiency

Observed defect: recognized curfew time question selects category-only passage; earlier non-answer can be recycled as evidence. Earliest supported failure is interpretation evidence selection; host only checks public membership and emits joined text. S02.4 also involves gated clue access, not merely missing selection.

Owner: existing legacy interpretation contract and `_communication_decision` answer assembly/public evidence projection. R5's semantic planner already has a distinct proposition coverage owner; do not transplant it or establish a parallel classifier without evidence.

Smallest plausible scope: require selected evidence to support the requested detail; empty evidence produces specific grounded uncertainty rather than repeating nearby facts. Couple underlying question to selection in the existing call. However a deterministic general semantic sufficiency test is not identified here; bounded instruction refinement might help but R1-07 already addresses a correction subset. If chosen, first discriminate supplied non-answer, genuinely absent fact and gated clue on saved records/actual payloads before implementation. Do not promise a relevance validator from keywords.

State/context: current question, available public passages, prior delivered answer for elliptical question; source disclosure eligibility. No new world facts or state. Preserve knowledge ownership: empty GM evidence does not license loading hidden board clue or private NPC topic. Passing a public membership test is necessary but insufficient.

Benefit: more useful specific uncertainty and fewer stuck loops; larger potential exposure than F1. Complexity medium/high because question propositions and source propositions interact. Risk medium/high: rejecting valid paraphrases, inventing clock hours, promoting related nonanswers, exposing gated details. Tokens may increase for a clearer existing contract; no extra calls allowed; exact latency and model effect unknown. Offline tests can prove flow and absence/disclosure handling, not actual semantic selection improvement. Live trials must include answerable, absent, related-nonanswer and hidden-source controls with independent human judgments; original/related/held-out claims separate. Preserve PR-EG R2 as diagnostic comparison, not integration authority.

## Candidate 3: F3 — Ordinary remark acknowledgment

Observed defect: raw model expresses acknowledgment intent but labels SESSION/OBSERVATION; host returns ruling language. S01.4 has no operation, S07.2 proposes SOCIAL_SIGNAL. Earliest wrong decision is ownership; acknowledgment support is the next missing contract.

Owner: production interpretation guidance in `live_chat_interpretation.py`, existing orchestration answer branch in `conversational_orchestration.py`. R1-07 already allows empty evidence for factual-free acknowledgment, so first inspect/reuse that obligation rather than duplicating it.

Shape: bounded contract for an ordinary noncommitting remark with existing representation and a short acknowledgment carrying no new world proposition. Do not replace every SESSION response, invent facts, introduce a catch-all semantic classifier, add ACK schema automatically or turn apparent acknowledgment into withdrawal that clears pending work.

Required context: speech ownership, pending intentions, current delivered response and authorized visible content only if actually used. No persistence. Benefit: avoids mechanical interruptions in everyday remarks. Complexity moderate: both model ownership and host realization must align; changing only the fallback string is insufficient. Authority risks lower than F1 but real: remarks must not trigger actions/ticks, erase proposals or launder player premises into canon. No extra provider call; narrow prompt guidance may change tokens and live interpretation, unmeasured. Deterministic tests can prove no-op state and supported route under controlled labels; live ordinary remarks, explicit rules questions, genuine actions and mixed/pending controls needed. Regression surface is existing SESSION/GM communication and fallback behavior.

## Why F4 is not a shortcut

Only propose expression changes after a correct authorized answer plan exists. R5 c06t07 supports a small ignorance-line preservation repair; it does not justify rewriting ATGB's mistaken content. Cosmetic naturalness must not hide unanswered questions or wrong speaker selection. F5 remains the pending R1 acceptance lane, not a new repair candidate.
'''

texts['07_recommended_implementation_scope.md'] = '''# 07 — Recommended Implementation Scope

## Proposed ATGB-R2-02

**Bounded speech-role grounding for established NPC follow-ups (F1).** Earliest supported wrong runtime decision: shared host addressee rejection after a sensible NPC ASK interpretation. Primary development failure class: **implementation**, because existing PR-EB/PR-EF-R4 contracts already support active second-person follow-ups but their lexical grounding rejects the selected cases. Full semantic continuation remains unproven.

Representative reproducers: S03.3 (unambiguous current speaker) and S05.3 (same addressee defect, separately ambiguous topic). Source extraction returns `you again later` / `me more`; model target and existing active interaction both identify the runner. This is a bounded repair target, not an instruction to implement during R2-01.

## Exact permitted change boundary for a future pass

Correct grammatical speech participant handling inside the existing shared addressee owner and its nominal helper, so speaker/addressee grounding does not treat the player recipient or continuation modifiers as an unmatched NPC name. Prefer the smallest owner-local adjustment; change the extraction helper only when preserving its other callers can be demonstrated. Existing orchestration should consume the corrected authorization without a local exemption. No prompt/schema change is needed to fix the demonstrated host rejection.

Relevant modules: `game/ordinary_semantic_ownership.py` (`assess_addressee_grounding`, `_active_npc_id`, existing authorization), `game/interaction_completion.py` (`addressed_person_nominal`, complement/nominal extraction). Integration consumers to verify: `game/conversational_orchestration.py`, `game/live_chat_interpretation.py` bridge, `game/api.py` pre-tick gate and existing ordinary resolution contract. `game/conversational_continuity.py` remains owner of delivered-exchange precedence, not a new memory layer.

Use only existing current-scene roster, active social interaction, explicit text and relevant delivered ownership context. An active ID alone never proves topic, truth, disclosure or executable outcome. No unbounded persistence or new session keys.

## Deterministic acceptance criteria

1. Replay original S03.3 raw interpretation with original preceding speaker context. Host must not emit unresolved-addressee or create ambiguous-addressee pending ASK. It must retain the runner as the supported target and use existing bridge/resolver validation, without inventing a promise or new fact.
2. S05.3 must not ask which person because the grammatical recipient is “me”. Do not require a definitive rumor continuation; a genuine focused topic clarification after the GM refusal is acceptable. A patch that automatically answers the old topic fails this criterion.
3. Unrelated-name fixtures exercise second-person question and tell-to-player constructions with different verb/complement forms, multiple visible NPCs and a unique established speaker. No calibration nouns or production phrase lists. These fixtures are related variations, not independent held-out evidence.
4. Explicit new person overrides old focus; mismatched provider candidate cannot override that person. Unknown explicit addressee, either/one-of/someone, plural/unresolved reference and multiple plausible targets still clarify with no tick or resolver.
5. No active focus, departed/offscene NPC, scene transition, conversation exit, explicit GM address and third-person GM question do not inherit a stale speaker. A single visible NPC does not erase a genuinely nonunique nominal. First-person “me” alone is never an NPC target.
6. All consumers read the same authorization: conversational decision, bridge, ordinary contract and pre-tick gate. No caller bypass. Correctly grounded ASK still uses knowledge/disclosure and normal resolver/time authority; compare allowed effects to an equivalent explicit-address control, not a blanket no-mutation expectation.
7. Hidden facts remain undisclosed; unauthorized action, travel, inventory, combat and retcon remain impossible. No new facts from narration. Legitimate mechanical revisions, executed-action refusal, correction contract and genuine clarification retain their prior behavior.
8. Focused existing PR-EF-R4 authorization, PR-EB continuity, interpretation bridge, state-authority and R1-02/R1-07 regression slices must preserve entry behavior. Baseline failures are compared by identity; interrupted HTTP coverage is not a pass. No frozen ATGB edits.
9. No additional interpretation/classification/retry pathway or expanded persistent context. Capture admission counts for downstream resumed flow; stop on unexpected extra admission rather than authorizing it automatically.

## Separately authorized live acceptance criteria

Once connectivity is available, use a new bounded reviewed budget and isolated production entry with import-safe readiness from R1-04/05. Original reproductions, related variations, legitimate ambiguity and explicit speaker-switch controls remain distinct. Capture actual messages/schema, full raw model output, projected evidence, grounding authorization, routing, final accepted text, delivered history and before/after state; record all admissions, failed dispatches, tokens and latency. Existing downstream calls fit the cap or the trial stops.

Human reviewer must separately judge speaker continuity, topic binding, question adequacy, naturalness and authority. S03.3 must avoid wrong-person clarification and unsupported future commitment. S05.3 must manage the topic ambiguity coherently rather than blindly answering the old rumor. Related scenarios use unrelated characters/situations; independent generalization requires genuinely unseen fixtures chosen without tuning. No broad playability or updated ATGB score from deterministic replay, selected live trials or previously exposed held-out cases. Live R1-07 acceptance remains separately pending.

## Explicit exclusions

No S08.2 reopening, PR-EG bind/witness migration, proposition-coverage redesign, broad prompt rewrite, semantic classifier, new ACK schema, world content/curfew-hour authoring, hidden clue publication, generic expression rewrite, new conversation state, unbounded persistence, automatic provider calls, retries, frozen baseline/judgment changes, unrelated refactor or commit/push. No scenario-specific production fixes.

## Stop conditions

Stop and return for review if exact raw-record reproduction cannot demonstrate the diagnosed host rejection; if repair requires guessing a speaker without authorized context; if S05 topic ambiguity is silently converted to certainty; if caller-specific exceptions or a new owner become necessary; if explicit/ambiguous/offscene guards regress; if new unauthorized state/disclosure occurs; if provider admission expands; or if source evidence contradicts the causal boundary. Do not weaken deterministic authority to satisfy a transcript. Package the bounded result and await review before any scope expansion.
'''

texts['08_final_verdict_and_handoff.md'] = '''# 08 — Final Verdict and Handoff

**A — Implementation target established.** Evidence supports one bounded repair with credible player-facing benefit: correct speech-participant handling at the existing shared addressee-grounding boundary for established NPC follow-ups.

This is a prioritization verdict, not implementation acceptance or proof of improved gameplay. The model already proposes the runner in S03.3 and S05.3; the host rejects that proposal as an unresolved person while retaining active runner context. Current-source reconstruction and unmodified syntax probes isolate a concrete grammatical boundary. A safe repair still has to preserve explicit targets, true ambiguity, scene locality, topic uncertainty, disclosure and resolver authority.

Weighted eligible ranking: F1 4.30, F2 4.00, F3 3.80, F4 3.50. The close F1/F2 comparison is broken by repair specificity and diagnostic confidence, not a numerical claim that F1 affects more turns. F5 3.95 is comparison-only and excluded from new implementation. No recovery percentage is predicted.

Recommended **ATGB-R2-02 — Bounded speech-role grounding for established NPC follow-ups** is specified in report 07. Correct the shared host owner/nominal boundary; do not introduce prompt, schema or memory architecture changes. Expected immediate benefit: remove unnecessary wrong-person clarification and let existing authorized dialogue handling proceed. Answer adequacy downstream is a separate acceptance question, especially after S05's topic switch and GM refusal.

## Behavioral Evidence

Historical ATGB baseline: 10 scenarios, 37 authoritative captured turns, original live-enabled production API path; individual replies can be host-owned. Imported assessment is AI-assisted and unattested. This pass extracts 19 selected original turns across six scenarios, not a new benchmark run. Standard packet: `artifacts/validation_evidence/atgb_r2_01/`. `representative_traces.json` retains canonical result/log references and hashes, exact raw interpretations/decisions/exchanges. Selected historical success S03.1 demonstrates explicitly addressed runner dialogue; failures S03.3 and S02.2 demonstrate wrong-slot clarification and non-answer. S05.3's topic is ambiguous; S07's opening delivery is deficient. No authenticated human adjudication or new evaluator score was created. Historical disagreements/uncertainties remain separate and are not overwritten.

Final PR-EG-R6-R5 raw counts were recomputed (59/164, correction tag 0/25); intervention gains remain intervention results. R4-R1 experimental integration is still forbidden. R1 mechanical routing is repaired/validated within scope; R1-07 conversational contract is implemented/deterministically validated; live conversational acceptance remains pending after R1-08/09 connectivity failures. S08.2 is not the next implementation target.

## Review package and safeguards

Eight reports, architectural failure matrix, scores in JSON/CSV, representative trace references/excerpts, candidate comparison, exact next scope, repository identity/status, protected entry hashes, integrity result and standard evidence packet are included through explicit allowlists. Review exports use the existing handoff generator, with a timestamped `CURRENT_REVIEW(YYYYMMDD-HHMMSS).zip` using America/New_York time. No local configuration or credential source is packaged; selected payloads are scanned for secret-value patterns and ZIP CRC/hash verification is recorded.

Confirmed for this pass, subject to the packaged integrity verification:

* No production changes.
* No prompt or schema changes.
* No provider calls, paid probes, retries or network diagnostics.
* No experimental PR-EG candidates merged or modified.
* Frozen ATGB baseline, original transcripts and historical judgments unchanged.
* No unauthorized gameplay-state mutations; no gameplay execution.
* No secrets included in the checked explicit review payload.
* No commits or pushes; all existing repository changes preserved.

Only new reports/evidence/local review scripts, a concise canonical orientation update and generated handoff exports were written. Offline count/provenance checks and isolated pure syntax probes are not tests of repaired behavior; no product test suite or fresh live acceptance is claimed. Remaining uncertainty includes exact original provider messages, grammar-level implementation details, downstream dialogue adequacy, real provider/token/latency effect and authenticated human review.

**Stop after generating and verifying the review ZIP. Await external review before ATGB-R2-02.** No implementation or live authority carries forward from this recommendation.
'''

for name, body in texts.items():
    (REPORTS/name).write_text(body, encoding='utf-8')

weights={'severity':.25,'exposure':.20,'generality':.20,'confidence':.15,'feasibility':.10,'safety':.10}
ratings={'F1':[5,4,4,5,4,3],'F2':[5,5,4,3,2,3],'F3':[4,4,3,4,4,4],'F4':[3,5,3,3,3,4],'F5':[5,4,3,4,3,4]}
scores=[]
for family, values in ratings.items():
    row={'family':family,**dict(zip(weights,values)), 'eligible':family!='F5'}
    row['weighted_score']=round(sum(weights[k]*row[k] for k in weights),2)
    scores.append(row)
dump('prioritization_scores.json',{'weights':weights,'scale':'1–5; exposure is qualitative inference, not a frequency estimate','rows':scores})
with (OUT/'prioritization_scores.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=list(scores[0]));writer.writeheader();writer.writerows(scores)
(OUT/'failure_family_matrix.md').write_text('# Failure-family boundary matrix export\n\nCanonical analysis: development/reports/atgb_r2_01/04_mechanism_comparison.md\n\n'+texts['04_mechanism_comparison.md'].split('## Shared and distinct mechanisms')[0],encoding='utf-8')
(OUT/'candidate_repair_comparison.md').write_text('''# Candidate repair comparison export

Full evaluation: development/reports/atgb_r2_01/06_repair_candidate_evaluation.md

| Candidate | Bounded owner | Main benefit | Main risk | Calls | Offline/live distinction |
|---|---|---|---|---|---|
| F1 | Shared addressee grounding + nominal helper | Remove wrong-person clarification | Wrong-speaker execution; topic remains separate | No added classifier; resumed downstream cost unmeasured | Routing/provenance offline; adequacy live |
| F2 | Legacy interpretation evidence + answer branch | Specific relevant answers/unknowns | Semantic relevance not safely solved by membership | No extra calls allowed; wording effect unmeasured | Flow/disclosure offline; semantic selection live |
| F3 | Interpretation ownership + existing acknowledgment route | Ordinary remarks avoid rules fallback | Clearing pending intent or inventing facts | No extra call; possible bounded wording tokens | No-op route offline; naturalness/ownership live |
''',encoding='utf-8')

# Standard behavioral packet over historical evidence, never new automated judgments.
sys.path.insert(0,str(ROOT))
from tools.validation_evidence import build_packet, write_packet
traces=read('artifacts/atgb/atgb_r2_01/representative_traces.json')
examples=[]
for t in sorted(traces,key=lambda x:(x['source'],int(x['turn_id'].split('.')[1]))):
    examples.append({'example_id':t['turn_id'],'scenario_run_id':t['source']+f"/trial-{t['trial']}",
        'turn_index':int(t['turn_id'].split('.')[1]),'player_input':t['player_input'],
        'player_input_classification':['representative_player_behavior'],
        'simulated_player_rationale':'Authored ATGB fixed corpus; historical model execution, not human-captured play.',
        'prior_player_context':[x['player'] for x in t['preceding_conversation']],
        'prior_gm_context':[x['gm'] for x in t['preceding_conversation']],
        'exact_gm_output':t['final_player_facing_response'],
        'historical_result':t['historical_rubric'], 'semantic_result':None,
        'mandatory_gates':{'status':'Historical ATGB dimension rubric; no synthetic mandatory gates reconstructed.'},
        'diagnostic_result':{'scope':'Retrospective analysis; reports 02/04; not a new evaluator result'},
        'automated_evaluation':{'status':'No automated semantic score; initial judgments unchecked, imported judgments AI-assisted and unattested.'},
        'runtime_validity':{'status':t['runtime_validity'],'scope':'Historical captured live-enabled path; provider request status/telemetry in trace'},
        'final_emission_metadata':{'host_decision':t['host_decision'],'narration_invoked':t['narration_invoked']},
        'continuation_action':'Historical next authored turn or scenario end; no continuation executed in this pass.',
        'source_artifact_path':t['source'], 'raw_log_source':t['log_source'],
        'human_review':{'status':'UNREVIEWED','rationale':'Historical assessment AI-assisted, human_review_attestation false; current causal analysis also AI-assisted.'},
        'evaluator_disagreement_history':[], 'calibration_reference':None,
        'analysis_reference':'development/reports/atgb_r2_01/02_failure_family_reconstruction.md'})
packet=build_packet(campaign={'campaign_id':'ATGB-R2-01','what_was_tested':'Offline historical reconstruction and prioritization; no fresh gameplay',
    'runtime_path':'Historical production API; this pass reads saved JSON/source only', 'gm_boundary':'Raw interpretation, adapted projection, host grounding/routing, final delivered reply',
    'player_input_mode':'Authored frozen ATGB scenarios', 'run_count':6,'turn_count':19,
    'automated_conclusion':'No new automated semantic judgment; A prioritization verdict is agent analysis'},
    claim_types=['runtime_evidence','semantic_behavioral_evidence'],examples=examples,missing_concepts=[],
    limitations=['Historical AI-assisted assessment is not human-attested. No post-repair performance measurement.',
    'Original request messages unavailable for these initial captures; evaluation world facts are not proof of prompt inclusion.',
    'No semantic_result is synthesized from provisional judgments. Automatic success/failure category selectors therefore have no scored examples; selected exact historical success/failure are described separately below.',
    'S05 topic uncertainty and S07 missing opening remain. No unseen generalization or new authority guarantee.'])
packetdir=ROOT/'artifacts/validation_evidence/atgb_r2_01'
write_packet(packetdir,packet)
with (packetdir/'evidence_summary.md').open('a',encoding='utf-8') as f:
    f.write('\n## Agent-selected retrospective orientation (not human adjudication)\n\nSelected in report 02 before packaging, in addition to unchanged automatic categories. Historical success: S03.1 explicitly addresses runner and receives authorized rumor. Historical failures: S03.3 selects runner in raw model JSON but host asks which person; S02.2 repeats category-only board text for curfew time. Exact selected exchanges and judgments are embedded in the manifest. Severe/worst: no new severity ordering beyond historical major failures. Evaluator disagreement: no newly adjudicated disagreement; original S03.4/S05.4 authority uncertainties remain. Unexpected/ambiguous: S05.3 topic after board refusal; S07 missing opening. No stress probe or boundary-success claim. All human review UNREVIEWED.\n')

prior=(OUT/'NEXT_SESSION_before.md').read_text(encoding='utf-8')
addition='''## Latest prioritization — ATGB-R2-01

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

'''
updated=prior.replace('Updated 2026-10-19 / ATGB-R1-09.','Updated 2026-10-19 / ATGB-R2-01.',1)
pos=updated.index('## Latest readiness pass')
(ROOT/'docs/NEXT_SESSION.md').write_text(updated[:pos]+addition+updated[pos:],encoding='utf-8')
print('Eight reports, scores, matrix, comparison, historical evidence packet and orientation written.')
