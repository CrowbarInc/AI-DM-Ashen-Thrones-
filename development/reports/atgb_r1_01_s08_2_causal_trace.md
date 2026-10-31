# ATGB-R1-01 — S08.2 Causal Trace and PR-EG Reconciliation

Date: 2026-10-18
Campaign: ATGB-R1
Pass: ATGB-R1-01
Mode: read-only investigation
Failure class: contract
Implementation: none

This pass reconstructs why ATGB S08.2 answered “I meant the people, not the weather.” with a pending-intention prompt, and whether PR-EG-R6-R5 explains that failure. No production code, test expectation, frozen baseline, or authority boundary was changed. No live provider call was made.

## Path note

The task listed `support/docs/` and `support/artifacts/` paths. Those prefixes are the review-bundle layout. Repository authorities are `docs/NEXT_SESSION.md`, `development/reports/`, and `artifacts/`. This report uses the repository paths. `docs/NEXT_SESSION.md` remains the orientation authority. Detailed verdicts remain in the artifacts it names, plus the later PR-EG-R6-R5 packet, which the orientation file had not yet absorbed.

# 01 — Baseline Reconciliation

## Orientation conflict

`docs/NEXT_SESSION.md` and `development/reports/atgb_05_baseline_preservation.md`, both updated for ATGB-05A on 2026-10-18, name PR-EG-R6-R4-R1 as the latest repository verdict: **C — inconclusive / below acceptance; do not integrate**. That verdict is in `artifacts/pr_eg_r6_r4_r1/38_FINAL_VERDICT.md`. It is an integration verdict about caching and semantic support. It does not diagnose S08.2.

PR-EG-R6-R5 is a later diagnostic packet, campaign id `pr_eg_r6_r5_pipeline_reliability_20261018`, also dated 2026-10-18. Its verdict in `artifacts/pr_eg_r6_r5/36_FINAL_VERDICT.md` is **B — diagnosis supported with limitations**. That grade is about the information-planning diagnosis. The same file says it is not a playability grade, and `artifacts/pr_eg_r6_r5/35_RECOMMENDED_NEXT_CYCLE.md` forbids implementing R1, R2, or R3 until review accepts the ranking. R5 does not supersede R4-R1’s integration ban. NEXT_SESSION’s silence on R5 is staleness, not a finding that R5 is absent.

Authorities used here:

- R4-R1 `38_FINAL_VERDICT.md` for the integration decision.
- R5 `36_FINAL_VERDICT.md`, `01_EXECUTIVE_SUMMARY.md`, `11_PRODUCTION_BASELINE.md`, `32_REPAIR_PRIORITIZATION.md`, `33_ARCHITECTURE_DECISION.md`, and `34_REMAINING_UNKNOWNS.md` for the diagnostic numbers and the proposed repair.
- ATGB-05A judgments and the ATGB-03C S08 capture for the player-facing failure.

## PR-EG-R6-R5 measurements

Source: `artifacts/pr_eg_r6_r5/summary.json` and `baseline.jsonl`, reconciled with `11_PRODUCTION_BASELINE.md`. The run used `gpt-4.1-mini` (`gpt-4.1-mini-2025-04-14`), unified semantic planning on, expression on, SDK retries off. Success means `score.player_facing_success`.

| Claim | Population | Result | Kind |
| --- | --- | --- | --- |
| Production conversational success 59/164 | Full frozen corpus: development c01–c04 20/55, validation c05–c08 18/54, holdout c09–c12 21/55 | 59/164 (36.0%) | Production observation |
| Validation success 18/54 | Validation partition only | 18/54 (33.3%) | Production observation on the validation slice |
| Correction success 0/25 | Correction tag on the full 164-turn corpus, not the validation slice alone | 0/25 | Production observation |
| Validation corrections | Same tag, validation partition only | 0/8 | Production observation, subset of the 25 |
| Development / holdout corrections | Same tag | 0/8 and 0/9 | Production observation |
| I8 authorized-plan substitution | Validation interventions | 44/54 (net +26) | Controlled intervention |
| I10B same plan, expression disabled | Validation expression-control arm | 45/54 (net +27) | Controlled intervention |
| I10C speaker asked only to say the authorized sentence | Not the production path | 53/54 | Controlled intervention, explicitly not production |
| I9 gold upstream inputs, authorization still on | Validation | 32/54 (net +14) | Controlled intervention |
| Restricted disclosures | Baseline, interventions, and expression control | 0 hits | Production and intervention observation |

The 25 correction turns are NPC information corrections such as “No, I meant when the harbor gate opens.” Every one called `semantic_plan` once. None succeeded. Host lines were “I can't reliably answer that revision just now.” (22) and “Which earlier question or argument do you mean?” (3). Reasons were `unlisted_role_change` 7, `invalid_correction_operation` 6, `invalid_referent_target` 6, `ambiguous_historical_target` 3, `empty_correction` 2, `unlisted_correction_change` 1. Zero baseline rows contain the sentence “unexecuted intention.”

Class counts on the full corpus, for orientation only: DIRECT 23/62, PARTIAL 2/15, UNKNOWN 13/47, CLARIFICATION_REQUIRED 7/15, RESTRICTED 14/22, RELATED_NONANSWER 0/3. Follow-ups 9/35. Six turns never entered the planner. R5 artifact 34 says the live-interpretation path is outside that causal map.

## What R5 established, and what it proposed

Production observation: a correct, authorized, sufficient reply occurs on 59/164 turns. On the correction tag, bind and witness checks in `game/conversational_referents.py` `bind()` reject the plan before source retrieval. The player hears the revision-reliability line above.

Controlled intervention: substituting a host-authorized plan (I8) lifts validation to 44/54. Leaving expression in place is almost the same as turning it off (I10B 45/54). Supplying gold semantic inputs and still running authorization (I9) reaches only 32/54, and the remaining misses include bind and witness errors. Question-only and source-only substitutions lose baseline successes. Both together gain. Candidate-id filtering changes nothing.

Hypothesis, stated as such by R5: a local bind/witness change could recover a large share of the I8-versus-I9 gap. Confidence is high that the gate is causal for those turns, and medium on the exact gain. R5 says the gold delta is still rejected, so a one-line predicate change is not identified. I8 and I10B are not production forecasts.

Proposed repair R1, not implemented: accept a witnessed correction or follow-up through `bind()` and the witness call in `authorize_information_turn`. R2 is joint question-and-source correspondence. R3 is one expression case. R5’s architecture decision is targeted repairs inside the existing pipeline, not a new stage.

Unresolved: human review pending; F18 covers 20 of 105 baseline failures; two validation turns never entered the planner; one PARTIAL label has no eligible source; holdout was baselined and not used to choose repairs.

R1’s causal support is intervention evidence on the semantic-plan correction population. It is direct for that population’s bind rejections. It is not a measurement of ATGB S08.2.

## ATGB status used as the scene baseline

ATGB v1 capture remains the frozen 37-turn baseline. Provisional assessment counts stay interpretation 18/16/3, response 10/25/2, authority 35/0/2. Authenticated human scoring is still pending. S08.2/trial-1 is a related variation, not held-out evidence. The provisional judgment is interpretation fail, response fail, authority pass, severity major, continuity preserved, with the explanation that the people-correction was routed to pending-intention revision. That judgment is AI-assisted assessment, not attested human scoring.

# 02 — S08.2 Execution Trace

## Reconstructed conversation

Scenario `data/validation/atgb/visible/S08.json`, partition `related_variation`, fresh `frontier_gate`. Authoritative visible facts include the notice board, the gate serjeant managing the crowd, the tavern runner, threadbare watchers and refugees, and the census choke. Who ordered the route change is unauthored. No opening was omitted: S08.1’s reply is the scene presentation. S07/S09’s missing-opening caveat does not apply.

S08.1 player: “What's in front of me right now?”

S08.1 AI-DM: the public gate description, beginning with rain and choke traffic, and also naming the notice board, the gate serjeant, the tavern runner, watchers, and refugees. Resolution `conversational_answer`. Reason `communication_before_execution`. Purpose `QUESTION`. Interlocutor remained null. No clue, flag, or scene change. Authorization source on the stored exchange: `conversational_decision:communication_before_execution`. The stored exchange has no `unified_semantic_plan`.

S08.2 player: “I meant the people, not the weather.”

S08.2 AI-DM: “I don't have an unexecuted intention to revise. What do you want to change?”

Resolution `conversational_clarify`. Reason `no_pending_intention`. Communication purpose on the decision `CORRECTION`. Context update null. Interlocutor null before and after. Transcript entries 1 → 2. No world mutation. One interpretation request, zero narration requests, zero retries. Model `gpt-4.1-mini-2025-04-14`. Input 2004, output 210. Request id `resp_0ffffc99ed67ac1d006ad548fcc5e887d2af53b020d7776c33`. Elapsed 1850 ms.

A contextually appropriate reading is a correction of S08.1’s description, away from the weather lead and toward the people already named in that reply: serjeant, runner, watchers, refugees, and the guards implied by the gate watch. The catalog’s pass line is those visible people. Weather may be dropped. No named traveler is to be invented. No scene change and no pending action are required.

S08.3 later asked who handles the crowd and received the serjeant sentence. That later success does not repair S08.2.

## Pipeline trace

Observed execution is the ATGB-03C S08 capture: `artifacts/atgb/atgb_03c/S08/transcript.md`, `result.json`, `stores/.../session.json`, and `session_log.jsonl`. Code locations are the current tree. The captured reason and sentence match the current function, so the host branch below is the branch that ran.

| Stage | Evidence | Decision | Status |
| --- | --- | --- | --- |
| Player input | Exact text stored | Subject correction of the previous description | Correct input |
| Context assembly | One prior GM exchange stored; interlocutor null; no `pending_intention`, no `pending_clarification`, no `last_executed_intention`, no `unified_semantic_plan` | Antecedent description is available; no gameplay intention is pending | Correct. The description was not dropped from storage |
| Migrated information planner | `is_migrated_information_turn` requires a prior semantic plan, or a question-shaped utterance with a named addressee. This utterance has neither. Accounting owner is `live_chat_interpretation.request_interpretation`, not `semantic_plan` | Planner not entered | Correct abstention. `bind()` was not reached |
| Model interpretation | One live interpretation call. The raw communication object was not retained | Unknown label | Indeterminate |
| Host routing | `decision_from_interpretation_record` → `_communication_decision` → `_pending_revision_decision` | Text contains “i meant”, which `_REVISION_RE` matches | Incorrect classification |
| Authority check | No pending or executed intention | `no_pending_intention` | The check correctly finds no intention. Invoking it for this utterance is the mistake |
| Response plan | Host template, narration count 0 | Ask what gameplay change is wanted | Incorrect, and a consequence of the routing |
| Final response | Captured sentence; `authoritative_mutation` false | Player hears an intention prompt | Incorrect |

`response_origin: live_provider` is the harness mode in `tools/atgb/chat_worker.py`. It records that the live API path ran. The sentence itself is the host string in `_pending_revision_decision`.

## Code that made the decision

`game/conversational_orchestration.py` defines:

```python
_REVISION_RE = re.compile(
    r"\b(?:instead|make that|change that|i meant|revise)\b",
    re.IGNORECASE,
)
```

`_pending_revision_decision` returns immediately only for `WITHDRAWAL`, or when the purpose is not `CORRECTION` and the regex does not match. Otherwise it looks for `pending_intention`, then `pending_clarification`, then `last_executed_intention`. With none of those present it returns reason `no_pending_intention` and the captured sentence, and it sets `communication_purpose` to `CORRECTION` on the way out.

That overwrite matters. The stored purpose `CORRECTION` is the host return value. It does not prove the model chose `CORRECTION`.

The regex match is sufficient by itself. Any communication record that reaches this call with a purpose other than `WITHDRAWAL` produces this sentence for “I meant…”, because no intention was pending. The call sits after addressee clarification and after the NPC-action early return. The captured reason shows those earlier returns did not fire.

The prompt in `interpret_production_turn` tells the model that cancellation, revision, and assent control pending intent, and that revising a proposed attempt is `GM/CORRECTION`. That instruction can bias the label. The label was not stored, and the regex does not need it. The prompt is a contributing bias, not the demonstrated cause.

Later stages could not recover. `_pending_revision_decision` returns before public-evidence answering. `bind()`, witness checks, correspondence, and expression never ran.

## Earliest incorrect decision

The earliest demonstrated incorrect decision is the host classification in `_pending_revision_decision`: “I meant the people, not the weather.” was handled as a request to revise an unexecuted gameplay intention.

The pending-action check then correctly reported that no such intention existed. The player-facing prompt is that report. It is a consequence, not a second cause. Lost antecedent, witness rejection, and bad narration are not what the trace shows. The prior description was stored. The witness gate was not entered. Narration was not called.

Competing explanation that the evidence does not decide: the model may also have labeled the turn `CORRECTION`. That label is a second sufficient entry condition and was not persisted. If it occurred, it would be an earlier model decision only if the label meant “revise a pending action” rather than “correct the last description.” The stored purpose cannot separate those readings. The host regex still makes the model label unnecessary for this outcome.

# 03 — Mechanical Revision Counterexample

Representative case: `tests/fixtures/pr_ef_r4_holdouts.json`, exercised by `tests/test_pr_ef_r4_authorization.py`.

| Case | State | Player | Required result |
| --- | --- | --- | --- |
| `correction_pending` | Pending ambiguous ask, status pending, scene-local | “Instead, make that a question about the lamp.” | Revise, do not execute, keep the intention pending |
| `correction_already_executed` | `last_executed_intention` status executed | Same sentence | Refuse to undo |
| `correction_nothing_pending` | No pending intention | Same sentence | “What do you want to change?”, no social resolution, no world mutation |

Those sentences match `_REVISION_RE` through “instead” and “make that”. The pending case is a real revision of an unexecuted ask. The empty case is the safeguard: an action-revision request with nothing pending must not invent an action or answer as if a lamp question had been established. The executed case must not roll back a resolved ask.

S08.2 differs in both intent and state. The player contrasts two parts of a delivered description. The session has no pending or executed intention. The antecedent is the S08.1 scene reply. The holdout player is changing a proposed ask.

Recognition belongs to the entry condition of `_pending_revision_decision`. Enforcement of “do not execute, do not undo, do not invent a pending action” belongs to the body of that function and to the holdout expectations. The current function does both jobs. `_REVISION_RE` includes `i meant`, so a description correction with no intention is enforced as a failed action revision.

A repair that deletes the no-pending safeguard, or that lets S08.2 succeed by skipping pending-action checks, would break `correction_nothing_pending` and `correction_already_executed`. That is out of scope.

# 04 — PR-EG Causal Comparison

Classification: **C — different mechanism.**

PR-EG corrections enter `authorize_information_turn`, call `semantic_plan`, and die in `bind()` with `unlisted_role_change`, `invalid_correction_operation`, `invalid_referent_target`, and the neighboring witness reasons. The player hears “I can't reliably answer that revision just now.” or a question about which earlier argument. R5 artifact 34 states that the live-interpretation path is outside that map.

S08.2 entered live interpretation, stored reason `no_pending_intention`, and spoke the orchestration template. `bind()` was not called. The R5 baseline contains zero copies of S08.2’s sentence. S08.1 left no semantic plan for a later correction to bind.

R1 would change witness acceptance inside `bind()` for turns that already have a referent operation. S08.2 is not such a turn. Implementing R1 would leave this host branch in place. R1 is irrelevant to this failure, not a downstream patch for it. R2 and R3 are likewise about source correspondence and expression on the planning path.

R5’s intervention results remain valid for their own population. They are not evidence that S08.2 failed in `bind()`.

# 05 — Cross-Scenario Findings

These are diagnostic controls. They are not one shared root cause.

## S03.3 and S05.3 — referent loss

S03.3, “If I ask you again later, will you still tell me that same thing?”, and S05.3, “Tell me more about that.”, both resolved `conversational_clarify` with reason `unresolved_addressee`. The player-facing line is “Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted.” Interlocutor was already `tavern_runner` before and after. S05.3’s catalog expects a topic clarification between the rumor and the notice, not a person list.

The line is built by `assess_addressee_grounding` in `game/ordinary_semantic_ownership.py`, called from `_communication_decision` before the revision gate. That is a different owner and an earlier branch than S08.2. Related problem: an available conversational referent was not used. Distinct mechanism: person-addressee grounding, not pending-intention revision.

## S02.2–S02.4 — question specificity

S02.2 “When does the curfew start?”, S02.3 “I wasn't asking where the patrol went. I asked when it starts.”, and S02.4 “All right. What did the warning say about where they were last seen?” each received “The notice board lists taxes, curfew rules, and a warning about a missing patrol.” Reason on each is `communication_before_execution`. Purposes are `QUESTION`, `CLARIFICATION`, and `QUESTION`. Context references are public-evidence ids such as `visible:0` and `reply:1`.

S02.3 is a correction and does not match `_REVISION_RE` (`i meant` is absent). It did not enter the pending-intention gate. The host emitted the selected notice-category passage. The raw evidence selection was not retained, so model selection versus host emission of that passage stays unresolved. The failure is a related non-answer on the ordinary GM evidence path. It is distinct from S08.2. It also is not the R5 `bind()` population: the stored reason is the orchestration answer path.

## S01.4 and S07.2 — ordinary remarks

S01.4 “Fair enough. I'm just getting a sense of the place.” and S07.2 “The banners look about finished.” both received “I don't have an established ruling for that question. No action or roll has been made.” Reason `communication_before_execution`. Owner `SESSION`. Purpose `OBSERVATION`. Context references empty.

That sentence is the empty-answer fallback in `_communication_decision` when the owner is `SESSION` or the purpose is `RULES`. S07’s opening was not delivered before turn 1; the remark itself does not depend on that opening, and the provisional judgment already treats the ruling line as nonresponsive. This is another mechanical-control sentence applied to ordinary speech. The branch is the session-ruling fallback, not `_pending_revision_decision`.

## Nearby corrections, not used as the primary controls

S06.4, “Back in character. Runner, I'll hear the rumor, not buy the stew.”, received “I've set aside the unexecuted intention. Anything already resolved still stands.” Purpose `WITHDRAWAL`, reason `communication_before_execution`. `WITHDRAWAL` skips `_pending_revision_decision` and hits the later set-aside sentence. Same family of intention-control text, different purpose and different branch. Out of the S08.2 repair.

S04.2, “I said the Gate Serjeant, not the captain and not the guard.”, was `interpretation_rejected` with a context-leak block. Different mechanism.

# 06 — Minimal Repair Recommendation

## Boundary

Owner: conversational orchestration, the entry condition that decides an utterance is mechanical intention control.

Locations:

- `game/conversational_orchestration.py`, `_REVISION_RE` and `_pending_revision_decision`
- the `CORRECTION` arm immediately after that call inside `_communication_decision`, which currently says an unexecuted intention was set aside

Contract to record before code changes:

- An unexecuted pending intention, or a pending clarification used as that intention, may be revised and must not be executed.
- An executed intention must not be undone.
- An explicit action-revision request with nothing pending must still ask what to change and must not mutate the world. The holdout sentence is “Instead, make that a question about the lamp.” The cues that select this safeguard are `instead`, `make that`, `change that`, and `revise`.
- `i meant`, and a `CORRECTION` purpose, do not by themselves select that safeguard when no pending or executed intention exists.
- With no intention record, a description correction stays on the ordinary GM communication path. It does not clear or create an intention.

State required: `conversational_context.pending_intention`, `pending_clarification`, and `last_executed_intention`, plus the already stored prior exchange if the ordinary path answers. No new persistent referent.

Reuse: the existing three holdout outcomes; public evidence and delivered exchanges for whatever answer the ordinary path can already give. Do not add a phrase table, a scenario id, a second router, or a new planner. Do not change `bind()`, world-state ownership, or disclosure rules.

## Expected effect and risks

S08.2 would leave the intention prompt. Whether the ordinary path then names the visible people is unproven, because the model’s evidence refs were not stored. An empty evidence record can still produce a weak GM answer after the gate is fixed. That would be a second, later defect, investigated only if a stub shows it.

Related scenarios: S02, S03.3, S05.3, S01.4, and S07.2 use other branches and should not move because of this entry-condition change. S06.4 uses `WITHDRAWAL` and stays out of this repair.

Regression risk: medium on the revision entry condition, low on world authority if the holdouts stay intact. Residual risk: “I meant…” while a real pending intention exists would still revise that intention. That preserves the safeguard and can still misread a description correction spoken during a pending ask. A second case can cover that later; it is not required to explain S08.2, where nothing was pending.

## Alternatives set aside

- PR-EG R1. S08.2 never reaches `bind()`.
- Deleting the no-pending prompt for every revision-shaped sentence. That disables `correction_nothing_pending`.
- A new correction classifier or an “I meant” special case. The existing regex already over-matches; the contract is to narrow when that match is intention control.
- Prompt-only changes. The host regex determines the captured sentence without the model label.
- Routing S08.2 into unified semantic planning. The turn is not an addressed information question, and S08.1 stored no plan to correct.

No smaller experiment is required to justify the entry-condition change. A stub replay is required before claiming the people are then named. See section 07.

# 07 — Validation Proposal

Deterministic tests and preserved transcripts only. Do not rerun ATGB live. Do not edit `data/validation/atgb/` expectations. Do not fit to PR-EG holdout. Deterministic absence of the intention prompt is not conversational adequacy.

## Original failure

Stub `decision_from_interpretation_record` with S08.1’s stored description as session context, no pending intention, and S08.2’s text. The player-facing text must not be the unexecuted-intention prompt. Run at least two stubs that reach `_communication_decision`: one `GM`/`DESCRIPTION` and one `GM`/`CORRECTION`, both with empty action components. Both currently can hit the regex. Both must leave the intention gate after the repair.

## Nearby paraphrases

Same state, wordings that correct the description without `instead`, `make that`, `change that`, or `revise`: “I mean the people, not the weather.” and “The people, not the weather.” Record whether each still depends on the model label. Do not add those strings as production phrase lists. They are tests of the contract.

## Mechanical counterexamples

Keep, unchanged:

- `correction_pending` revises and does not execute.
- `correction_already_executed` refuses undo.
- `correction_nothing_pending` still asks what to change.

Add one ambiguous control: a correction whose excluded subject is not in the prior reply. The reply may ask which part of the description was meant. It must not ask which gameplay intention to revise, and it must not invent a person.

## Conversational continuity

- S03.3-shaped follow-up to an established interlocutor stays out of this change; existing addressee tests remain the guard.
- S02.3-shaped correction (“I wasn't asking…”) stays on the evidence path and must not start entering the intention gate.
- A subject correction must not write world flags, clues, scene id, or inventory.

## Authority

Assert no world mutation, no restricted disclosure, no bridge execution, and no clearing of an absent intention. `bind()` unit results and the PR-EG diagnostic tests stay as they are. This repair does not claim a change in the 0/25 correction tag.

## Broader regression

Focused: `tests/test_pr_ef_r4_authorization.py` holdouts for the three correction cases, plus the new S08.2 stubs.

Do not treat a green stub as an ATGB performance result. S08 is a related variation already visible in the corpus. A later live rerun, if separately authorized, would be a new trial, not a rewrite of trial 1. Previously exposed held-out scenarios are not unseen generalization. PR-EG validation 18/54 and correction 0/25 stay historical measurements until a planning-path change is actually made and measured.

## Performance

The repair adds no provider call, no context enlargement, no retry, no classification stage, and no persistent state. S08.2 already spent one interpretation call and zero narration calls. Token and latency effect is unmeasured and is not claimed.

# 08 — Final Verdict

The root cause of the captured sentence is established. S08.2 was classified as mechanical intention revision by `_pending_revision_decision` because the utterance matched `i meant` and no intention was pending. The model’s own purpose label was not stored and is not required to explain the sentence.

PR-EG-R6-R5 does not explain S08.2. Relationship **C**. R1 addresses `bind()` on semantic-plan corrections. That proposal is inapplicable here.

Implementation of the orchestration entry-condition contract is justified as ATGB-R1-02, after review of this packet. Implementation of R1 is not justified by S08.2. This pass does not implement either.

ATGB-R1-02 scope, if accepted:

- Record the contract in section 06, then change only the revision entry condition and the `CORRECTION` set-aside arm so intention-control text requires an intention or an explicit action-revision cue.
- Preserve the three PR-EF-R4 correction holdouts.
- Add the S08.2 stubs.
- Do not change `bind()`, prompts, world authority, ATGB expectations, or the frozen baseline.
- Do not claim the people are named until a stub shows the follow-on answer.
- No live provider call in that pass unless a later authorization says otherwise.

Failure class: **contract**. The revision function’s tested contract is action control. Its entry condition also claims ordinary “I meant…” corrections. The product requires those to remain conversational. The ordinary GM path already exists; this is not a missing owner and not a reason for a new architecture.
