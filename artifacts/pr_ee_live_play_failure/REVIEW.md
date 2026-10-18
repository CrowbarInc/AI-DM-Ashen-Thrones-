# PR-EE — Live-Play Failure Investigation


# 01 — PR-EE Executive Summary

Investigation only. Severity: **Critical playability failure**. Recommendation: **Option B — conversational routing rework**, bounded to message authority, lifecycle dispatch, continuation, and confirmation contracts. Preserve simulation/resolver authority and downstream narration systems.

The original six-turn production record was available in `data/session_log.jsonl`: raw provider interpretation strings, adapted records, orchestration decisions, bridge rejection, final replies, timestamps, and provider usage. This is stronger evidence than the supplied paraphrased transcript. The captured log is `original_session_log.json`. Its wording contains double periods and “Player addresses” where the supplied transcript normalized punctuation/wording; all six raw logged replies were reproduced byte for byte through the current HTTP route with the five recorded provider outputs injected at the provider-request seam. This proves current downstream behavior for those outputs, not present-day provider determinism or deployed source identity.

Primary findings:

1. **Communication authority is narrower than the conversation it serves.** The provider schema has in-world action, correction, rules question, clarification, and OTHER; no ordinary player-to-GM, narrative request, or session-control domain. The interpreter understood readiness and campaign-start intent in turns 1/2, but empty action lists became generic requests for intention. Turn 3 also contains a real provider classification error: campaign start was labeled INVENTORY_GRANT. Turn 6 explicitly understood the GM addressee, but OTHER + SOCIAL_SIGNAL entered unsupported operation handling.
2. **Unsupported does not mean compound.** `decision_from_interpretation_record` uses `len(connected) > 1 or unsupported` (game/conversational_orchestration.py:1673). Any unsupported singleton creates a compound confirmation. `_compound_clarification` asks for confirmation even with zero supported steps. `Yes.` correctly restores the known unsupported step and declines it. This is a proposal eligibility defect, not lost confirmation state.
3. **Continuity preserves text but lacks GM discourse ownership.** `Why not?` reaches a new interpreter call with the last two visible exchanges (reconstructed from current code), including the rejection. Pending-resume deliberately skips questions; no GM interlocutor/rejection subject is retained as typed context. The provider classifies it as in-scene ASK without a target; bridge rejection produces “Who are you asking?” before the social resolver runs.
4. **Campaign opening already exists but is misintegrated.** Authored first-scene state exists before opening narration. The first failed chat entry closes the transcript-empty start gates while the campaign-started latch stays false. Additionally, even a recognized fresh chat start cue still hits live interpretation before the later scene-opening branch. A separate replay on empty transcript confirms that earlier filter can block the opening.
5. **Final emission is exonerated for these six turns.** All return through the early deterministic conversational response function. No resolver, narration completion, final-emission gate, or narration retry ran. Interpreter results were overridden by orchestration; no useful generated narration was discarded because none was requested.

Confidence: **High** in the observed causal chain and current-source replay; **medium** in historical attribution to individual cycles and deployed configuration identity; **unmeasured** fresh live-provider generalization to semantic alternatives. Existing reports identify PR-EC compound machinery, but the dirty worktree has no clean EA/EB/EC commit sequence to prove exact introduction time.

No production gameplay source was edited. Active data, game source, and static assets passed before/after hash checks. The prior PR-ED handoff was archived before replacing CURRENT_REVIEW. Fresh live-provider probes were blocked by automatic approval review; no new external provider requests were sent. Six alternatives were inspected at the deterministic routing boundary, explicitly not passed off as completed live API tests.


---

# 02 — Six-Turn Reconstruction

Evidence labels: **O** = original logged runtime; **R** = isolated current HTTP replay of recorded provider output; **S** = static code inference. All turns used Player UI and AUTO communication mode (O). UI sends `{text, ui_mode}` to `/api/chat?ui_mode=player` at static/app.js:585; game/api.py:6157 dispatches to chat. Current worktree production seam `_stored_interpretation_for_player_text` returns None; the replay leaves it unset.

Original initial-state snapshot is unavailable. The current saved post-turn-six session (O) has frontier_gate, turn_counter=0, campaign_started=false, and no active NPC interlocutor. The log marks all six authoritative_mutation=false, resolver_invoked=false, gameplay_parser_invoked=false, narration_invoked=false. Therefore no world-operation turn advancement occurred according to the runtime evidence. Exact per-turn original on-disk persistence diffs cannot be recovered. R uses a fresh factory session and copied current campaign/world/scene/character/combat data, not an asserted original snapshot.

Shared execution detail for all six: no authoritative resolver selected or called, no resolver result, no narration request or provider narration response, no final-emission validation, no narration retry. “Validation” below distinguishes interpreter structural/eligibility processing and bridge validation from final emission. Final response owner is `_nonmutating_conversational_decision_response` (game/api.py:731–815); it logs and returns decision text verbatim and persists only bounded context updates when present. HTTP 200 / ok=true means request completion, not playable success.

Interpretation request reconstruction: game/live_chat_interpretation.py:237–248 constructs active public scene summary, visible ids gate_guard/gate_serjeant/notice_board/tavern_runner, schema/mode instructions, and up to two visible player/GM rows, 240 characters per field. Original request messages were not stored; the replay saves reconstructed messages. Raw original provider responses ARE retained. The following context rows refer to this reconstructed current request contract, not recovered original wire payloads.


## Turn 1

- Raw input (O): `I'm ready to begin play!`
- Logged UTC time (O): 2026-10-16T20:12:25.130642Z (October 16, 2026, 4 p.m. hour America/New_York).
- State/conversation context (O/S/R): No previous transcript rows (six-row log begins here). No pending clarification is evidenced.
- Interpretation request/result and validation (O): Readiness understood; IN_WORLD_ACTION, INTERPRETED, zero action_components. Eligibility SAFE_ABSTENTION; live wrapper blocked/clarification_required.
- Orchestration/category (O): **CLARIFY**, family `clarification`, reason `clarification_required`. No deterministic rule claims the input. Record-to-decision sees no executable component and uses the generic intention fallback, ignoring the understood player_intent.
- Final emitted response (O): What are you trying to accomplish?
- State effects (O/R/S): Transcript row appended. No conversational_context update. Fresh structured-start availability becomes false because the transcript is now nonempty.
- Provider calls/latency (O): 1 interpretation; 0 narration; 0 narration retries; total turn 3247 ms. Provider 3204.669 ms, input/output 736/154 tokens, gpt-4.1-mini-2025-04-14.
- Controlled replay (R): HTTP 200; exact response match `True`; 26.476 ms excluding real provider latency; changed session keys `[]`. World content unchanged.


## Turn 2

- Raw input (O): `I'd like you to start the campaign.`
- Logged UTC time (O): 2026-10-16T20:12:40.669145Z (October 16, 2026, 4 p.m. hour America/New_York).
- State/conversation context (O/S/R): One previous visible player/GM exchange. Campaign-start cue text matches, but the nonempty recent_log makes campaign_start false (S/R).
- Interpretation request/result and validation (O): Campaign/session start understood; OTHER, INTERPRETED, zero components. SAFE_ABSTENTION, blocked/clarification_required.
- Orchestration/category (O): **CLARIFY**, family `clarification`, reason `clarification_required`. OTHER has no GM/session answer path; no executable component again becomes generic intention clarification.
- Final emitted response (O): What are you trying to accomplish?
- State effects (O/R/S): Second transcript row appended; no bounded context update. No successful opening.
- Provider calls/latency (O): 1 interpretation; 0 narration; 0 narration retries; total turn 2683 ms. Provider 2677.942 ms, input/output 764/120 tokens, gpt-4.1-mini-2025-04-14.
- Controlled replay (R): HTTP 200; exact response match `True`; 10.613 ms excluding real provider latency; changed session keys `[]`. World content unchanged.


## Turn 3

- Raw input (O): `Begin.`
- Logged UTC time (O): 2026-10-16T20:12:50.048696Z (October 16, 2026, 4 p.m. hour America/New_York).
- State/conversation context (O/S/R): Previous two exchanges are repeated clarifications. No pending sequence before this turn in R.
- Interpretation request/result and validation (O): IN_WORLD_ACTION, INTERPRETED, one INVENTORY_GRANT component describing campaign start. Eligibility UNSUPPORTED_OPERATION; live wrapper blocked/interpretation_rejected.
- Orchestration/category (O): **CLARIFY**, family `multi_action`, reason `compound_intention_needs_confirmation`. Blocked-record path reprocesses the record. Unsupported singleton triggers compound helper. Stored step is operation OTHER, supported=false, consequential=true; pending scene_id is empty because helper passes scene=None.
- Final emitted response (O): You asked to Start the campaign or scene at Cinderwatch Gate District.. I can resolve one supported action at a time, and I have not done any of them yet. Should I start with the first one?
- State effects (O/R/S): Transcript appended; pending_clarification replaced with one known unsupported campaign-start step. No world mutation.
- Provider calls/latency (O): 1 interpretation; 0 narration; 0 narration retries; total turn 2648 ms. Provider 2643.207 ms, input/output 782/190 tokens, gpt-4.1-mini-2025-04-14.
- Controlled replay (R): HTTP 200; exact response match `True`; 10.249 ms excluding real provider latency; changed session keys `['last_saved_at', 'conversational_context']`. World content unchanged.


## Turn 4

- Raw input (O): `Yes.`
- Logged UTC time (O): 2026-10-16T20:12:59.066206Z (October 16, 2026, 4 p.m. hour America/New_York).
- State/conversation context (O/S/R): Pending one-step sequence from turn three. Deterministic pending resume has priority; no interpretation request.
- Interpretation request/result and validation (O): No new provider output or adapted record. Yes selects the first stored step.
- Orchestration/category (O): **DECLINE**, family `multi_action`, reason `unsupported_compound_step`. Restoration succeeds. supported=false immediately produces DECLINE/unsupported_compound_step before bridge or resolver. The proposal should never have requested approval.
- Final emitted response (O): I have not done this: Start the campaign or scene at Cinderwatch Gate District.. It is not a supported action I can resolve safely yet.
- State effects (O/R/S): Transcript appended; identical pending sequence retained, still pending. R also changes persistence timestamp; no simulation effects.
- Provider calls/latency (O): 0 interpretation; 0 narration; 0 narration retries; total turn 4 ms. No provider latency or tokens.
- Controlled replay (R): HTTP 200; exact response match `True`; 9.604 ms excluding real provider latency; changed session keys `['last_saved_at']`. World content unchanged.


## Turn 5

- Raw input (O): `Why not?`
- Logged UTC time (O): 2026-10-16T20:13:12.503872Z (October 16, 2026, 4 p.m. hour America/New_York).
- State/conversation context (O/S/R): Reconstructed two visible rows are Begin + proposal and Yes + rejection; the prior rejection is in the interpreter context. Pending campaign-start sequence still exists.
- Interpretation request/result and validation (O): IN_WORLD_ACTION, INTERPRETED, one ASK with target_ref=null. Runtime accepted/eligible_for_bridge (eligibility does not require a target).
- Orchestration/category (O): **CLARIFY**, family `world_operation`, reason `missing_target`. Question bypasses bounded pending restoration; no active NPC follow-up or general rejection explanation rule. Orchestration selects EXECUTE for ASK, then bridge rejects missing_target; focused clarification emits Who are you asking?
- Final emitted response (O): Who are you asking?
- State effects (O/R/S): Transcript appended. No context_update is created for this bridge clarification; old campaign-start pending sequence survives. In particular, no new missing-interlocutor question/GM addressee slot is saved.
- Provider calls/latency (O): 1 interpretation; 0 narration; 0 narration retries; total turn 2250 ms. Provider 2245.36 ms, input/output 832/202 tokens, gpt-4.1-mini-2025-04-14.
- Controlled replay (R): HTTP 200; exact response match `True`; 8.197 ms excluding real provider latency; changed session keys `[]`. World content unchanged.


## Turn 6

- Raw input (O): `You, in the capacity of game-master.`
- Logged UTC time (O): 2026-10-16T20:13:33.411883Z (October 16, 2026, 4 p.m. hour America/New_York).
- State/conversation context (O/S/R): Reconstructed prior rows are Yes + rejection and Why not + Who are you asking?; pending still describes campaign start rather than the question just asked.
- Interpretation request/result and validation (O): OTHER, INTERPRETED, SOCIAL_SIGNAL. Summary explicitly identifies the game-master. SAFE_ABSTENTION; provider clarification asks what specific action/information is requested.
- Orchestration/category (O): **CLARIFY**, family `multi_action`, reason `compound_intention_needs_confirmation`. OTHER is not routed as GM communication. SOCIAL_SIGNAL is allowed by upstream schema but absent from connected/incidental orchestration sets; it becomes unsupported singleton, then false compound confirmation. Provider clarification_question is not used for status INTERPRETED.
- Final emitted response (O): You asked to Player addresses the game-master directly, invoking their role as game-master.. I can resolve one supported action at a time, and I have not done any of them yet. Should I start with the first one?
- State effects (O/R/S): Transcript appended; previous pending sequence overwritten with one unsupported GM-address step, operation OTHER, empty scene_id. Saved post-test session confirms this pending state.
- Provider calls/latency (O): 1 interpretation; 0 narration; 0 narration retries; total turn 3706 ms. Provider 3701.401 ms, input/output 801/184 tokens, gpt-4.1-mini-2025-04-14.
- Controlled replay (R): HTTP 200; exact response match `True`; 9.594 ms excluding real provider latency; changed session keys `['last_saved_at', 'conversational_context']`. World content unchanged.


Original aggregate: 5 provider requests, 3915 input + 850 output = 4765 tokens; summed provider latency 14472.579 ms; summed turn elapsed 14538 ms. These sums are processing time, not the wall interval between human submissions. Original token totals are recoverable in nested interpretation usage even though top-level PR-ED performance token fields are null.

Full records: `original_session_log.json`, `original_session.json`, `recorded_output_http_replay.json`, `original_provider_totals.json`. R result contains every input, before/after session, previous log, reconstructed interpretation request, injected raw output, API response, and changed keys. It does not manufacture original provider outputs: the injected strings come directly from the original runtime log.


---


# 03 — Campaign Lifecycle Analysis

Campaign creation/configuration, runtime reset, and first playable narration are separate operations.

| Concern | Current owner / behavior | Evidence |
|---|---|---|
| Campaign premise/tone | campaign.json persists authored configuration; load_campaign seeds defaults if absent, save_campaign updates; /api/campaign edits it | game/storage.py:204; game/api.py:4779 |
| Player character | character.json sheet loaded independently; current sheet Galinor, level 1 Wizard; compose_state synchronizes character_name | game/storage.py:214; game/api.py:4643 |
| Initial world/scene | startup ensures data, scene templates; fresh session chooses frontier_gate; authored summary, entities, suggested actions, opening seed facts exist before narration | game/storage.py:181; game/campaign_state.py:41,73; data/scenes/frontier_gate.json |
| New Campaign | /api/new_campaign hard reset replaces session/combat, clears world playthrough residue and transcript; keeps campaign/character/templates | game/campaign_reset.py:35; game/api.py:4890 |
| Opening narration | /api/start_campaign creates internal scene_opening intent; shared resolved-turn stack constructs prompt, asks narration provider, validates, persists output | game/api.py:4497,4532,5920,6069,6119 |
| Started latch | campaign_started=true only at successful opening persistence | game/api.py:5832 |
| Player UI | /api/state displays existing scene/affordances regardless of started latch; separate campaign_can_start controls Start Campaign button | game/api.py:4590,4633; static/app.js:647 |

Thus an initialized scene is not evidence of a successful opening. The original final session has campaign_started=false and turn_counter=0; the six-row original transcript contains no opening. The initial screenshot alone cannot prove why Start Campaign was not used or its prior enabled state.

Two integration faults matter:

1. The text cue gate at game/api.py:4474 rejects any nonempty transcript. The structured start gate at :4565 similarly requires no transcript, zero turns and false started latch. Turn one's non-mutating clarification appends a transcript row; it does not set campaign_started, but it prevents both gates. An explicit “I'd like you to start the campaign” on turn two therefore misses the opening path even though its text matches a cue. `lifecycle_gate_probes.json` evaluates this directly. A read or failed conversational turn must not be equivalent to an opening having completed.
2. A true campaign_start flag at :6198 only skips stored/deterministic interpretation. The live interpretation branch at :6287 still runs before the opening branch at :6508. On an empty transcript the exact turn-two sentence returns true from the cue predicate; replaying its recorded provider output through HTTP STILL returns generic clarification. `recognized_fresh_start_replay.json` confirms this separate ordering defect. Simply relaxing the transcript gate is insufficient with live interpretation enabled.

This is primarily initialized-versus-started lifecycle confusion plus misrouting of GM/session requests (C/D in the task's campaign-start alternatives). Opening narration is missing from this run as a consequence. Campaign-start functionality is not absent. The prose is generated from authored/stored opening facts and scene context when the dedicated opening path is reached, with downstream deterministic opening fallback support; the scene summary visible in the UI is authored state and is not itself a generated opening exchange. This investigation did not call /api/start_campaign on the active campaign, did not validate fresh opening provider quality, and does not establish that its full downstream path always succeeds.


---


# 04 — Conversational Authority Analysis

| Requested distinction | Representation and gap |
|---|---|
| Player-to-GM communication | Caller mode AUTO/IC/OOC and interpreter OTHER/rules/correction are partial proxies; no general GM recipient/message purpose. OTHER can still be interpreted as executable components. |
| Player-character actions | IN_WORLD_ACTION + components/visible ids; bridge connects PERCEIVE/INSPECT/ASK/MOVE and existing resolvers retain authority. |
| NPC dialogue | ASK targets must be visible NPCs; active_interaction_target_id defaults NPC follow-ups. There is no equivalent active GM participant. |
| Session/campaign controls | Separate endpoints exist; chat lifecycle matching is lexical and gated on transcript emptiness, then encountered too late behind live interpretation. |
| Rules/interface questions | Deterministic question+keyword patterns and OOC mode. Schema uses RULES_QUESTION, eligibility recognizes it, but record decision checks OUT_OF_CHARACTER/OUT_OF_CHARACTER_CORRECTION, not RULES_QUESTION. |
| Clarification responses | Persisted pending operation, choices, scene, bounded compound steps. Bridge missing-target replies do not necessarily create a corresponding pending slot. |
| Narrative requests | Selected public-context patterns answer from scene; no general narrative-request intent. “Describe the opening scene” falls through to interpretation. |
| Consequential operations | Execution gate and resolvers exist, but unsupported descriptive components are automatically marked consequential and offered as compound steps. |

Source: game/conversational_orchestration.py:16–106,216–263,323–449,1442–1690; game/api.py:375–495,818–840; experiments/pr_do/schema.py:9–48 and eligibility.py:23; experiments/pr_dr/prompt.py:18–29,75–102.

The previous GM reply is retained in session_log and reconstructed into the last two visible interpreter turns, capped at 240 characters per line. The turn-four rejection is short enough to be included in full. Therefore “Why not?” is not explained by wholesale transcript loss or context truncation. The original wire request was not archived; this is current-code reconstruction supported by the replay's captured request, not direct proof of its historical bytes.

Missing typed discourse: no persistent GM-facing rejection reason, subject, recipient, or conversational response obligation is written by `_nonmutating_conversational_decision_response`. It writes the full decision to the transcript, but interpreter projection excludes resolution metadata. Pending sequence state survives; `_resume_bounded_pending` returns None for question-start utterances. Active-follow-up logic requires an NPC id and supplies ASK; with no active NPC it cannot interpret GM follow-ups. `_recent_visible_answer` only uses a small lexical trigger set; “Why not?” has none. The provider consequently makes a wrong recipient inference (ASK without target). The bridge correctly refuses an ungrounded NPC operation, and its “Who are you asking?” is a focused action-slot question in the wrong conversation domain.

Turn six is the clearest ownership failure: the provider summary and premise identify direct game-master address, yet mode OTHER + SOCIAL_SIGNAL becomes an unsupported world step. A new recipient clarification is not restored because turn five stored no pending ASK clarification; the older start sequence remains until turn six overwrites it. This combines incomplete GM discourse state with misrouting, rather than a universally broken memory subsystem.

Even explicit OOC avoids mutation but currently returns a fixed acknowledgement (game/api.py:461), not an answer to arbitrary GM/rules requests. Merely prefixing all inputs with OOC is not a coherent product repair. The latent RULES_QUESTION mode-name mismatch is a source finding outside the original six inputs; it must not be presented as their cause.


---


# 05 — Multi-Action and Confirmation Analysis

The exact sentence comes from deterministic `_compound_clarification`, game/conversational_orchestration.py:1146–1188, specifically :1172–1173. It is neither provider narration, final-emission repair, nor the social fallback catalog. The API returns it verbatim.

```text
decision_from_interpretation_record
  classify each component into connected / incidental / unsupported
  if len(connected) > 1 OR unsupported:
      _compound_from_record_parts(...)
        unsupported description -> OTHER, supported=false, consequential=true
        _compound_clarification(..., scene=None)
          persist compound_sequence, ask to start with first step
```

The `or unsupported` condition makes cardinality irrelevant. “Begin.” has one INVENTORY_GRANT (a provider class error). Direct GM address has one SOCIAL_SIGNAL (provider explicitly understands recipient). Both become one unsupported step; no actual multiple consequential operations were described. SOCIAL_SIGNAL is allowed by PR-DO's validation schema but is absent from orchestration's connected and incidental sets and absent from the production bridge's four connected operations.

The helper computes supported/unsupported lists before composing its message. With zero supported steps it still uses the generic confirmation wording. It therefore asks approval of a step the proposal already marks non-executable. Even connected compound steps call a nonempty target sufficient for `supported`; this is not the bridge's full visible-kind/destination validation. This latter coarse support criterion is a static risk, not an additional observed six-turn failure.

Pending representation after turn three (original logged context_update):

```json
{"kind":"compound_sequence","operation":"OTHER",
 "original_text":"The player intends to start the campaign or scene at the Cinderwatch Gate District.",
 "steps":[{"text":"Start the campaign or scene at Cinderwatch Gate District.",
 "label":"Start the campaign or scene at Cinderwatch Gate District.",
 "operation":"OTHER","target_id":"","supported":false,
 "consequential":true,"dependency":"sequence","status":"pending"}],"scene_id":""}
```

`Yes.` is selected by `_select_compound_step` (:1342). Resume checks selected.supported (:1367) and immediately returns DECLINE/unsupported_compound_step (:1373), preserving the entire pending object unchanged. There is no resolver rejection: bridge and resolver were never asked. Confirmation restoration is correct for the stored step, but the stored step should not have been proposed for confirmation. Operation identity is also degraded from INVENTORY_GRANT or SOCIAL_SIGNAL to OTHER, and scene scope is erased by passing scene=None. The empty scene id prevents the usual pending scene-expiry guard from having its intended boundary; scene-change leakage is a source risk, not exercised here.

PR-EC's report and changed-file list explicitly claim introduction/extension of named compound steps, support flags and pending sequences; the current defect resides in that machinery. PR-EA already routed unsupported/multiple-component records into orchestration. Without preserved pre-EC source or a clean commit boundary, exact historical introduction of the overbroad predicate cannot be assigned conclusively. PR-EC demonstrably supplies the current harmful confirmation behavior and extends its persistence/resumption surface; its targeted tests cannot establish general provider integration correctness.

Repair boundary: classify communication purpose first, separate unsupported singleton handling from genuine compound sequencing, and validate offerability before asking for confirmation. Preserve original operation/mode and scene scope in pending state. Approval must authorize an eligible operation; it must not be used to discover an already known unsupported step. No phrase-specific start/DM handlers are proposed.


---


# 06 — PR-EA / EB / EC / ED Effectiveness Audit

Participation is established by original metadata plus exact current replay; cycle intent is sourced from the archived prior reports in `prior_cycle_reports/`. Historical reports are context, not independent runtime proof.

| Cycle / mechanism | Intended behavior | Participation and actual result | Decision respected / override | Contribution / preservation |
|---|---|---|---|---|
| EA early ANSWER/CLARIFY/DECLINE/EXECUTE/PLAN envelope | Decide conversational response before time/resolution | All six end here; turns 1/2 understand intent yet choose generic clarification | Envelope respected all six; however API reprocesses blocked interpreter records, replacing wrapper responses; interpreter eligibility is not preserved as conversation policy | Primary routing mismatch; preserve early non-mutating boundary and inspectable decision, replace purpose/execution conflation |
| EA bridge validation | Keep execution grounded, reject unexecutable actions | Turn five ASK reaches bridge and fails missing_target | Bridge rejection respected; no world action occurs | Correct gate operating in wrong domain; preserve validation |
| EB pending clarification/context persistence | Resume original intent from short reply | Turn-three pending saved; Yes restores it; turn-four preserves it; turn-six overwrites it | Stored unsupported flag respected; no loss of step on confirmation | Persistence works; missing GM rejection subject, recipient, and pending ASK slot make continuity incomplete; preserve store with stronger contract |
| EB active NPC follow-up and recent context | Resolve NPC addressee and prior references | Deterministic decision consulted; no active NPC for turn five; recent answer lexical trigger misses Why not | No successful NPC/GM decision is later overridden | Scope too narrow for GM conversation; preserve NPC logic under correct recipient routing |
| EC movement/partial modality | Ground movement; hold tentative/question intent | Deterministic stage consulted; none of original inputs is movement; no movement resolver participates | Not a movement failure | Useful existing capability; preserve |
| EC compound scheduling/confirmation | Name multiple consequential steps, execute one confirmed step safely | Turns three/six single unsupported components enter compound helper; turn four uses pending resume | False proposal is honored until supported=false decline; no resolver override | Direct contributor; replace compound eligibility/cardinality and offer validation, preserve bounded sequencing |
| ED provider efficiency | Skip discarded narration, constrain retry, measure provider cost | Five interpreter calls recorded; Yes zero; early returns never request narration | Skip/duplicate-policy/retry-stop mechanisms are not reached; not evidence they failed | Preserve optimizations; not root cause of these failures |
| ED observability | Expose calls/tokens/latency | Nested interpreter usage contains original model/request ids/tokens/timing; early performance marks every response successful=true | Top-level token/stage fields null; DECLINE's performance successful=true despite resolution.success=false | Secondary observability defect; distinguish response delivery from player-goal success and aggregate interpreter usage |

No evidence that social.py, noncombat_resolution.py, ordinary_semantic_ownership.py, gm.py narration, or final_emission_gate.py executes these turns. They are imports/dependencies and potential later owners, not the owners of the observed replies. API pre-routing returns before their resolver/narration paths. PR-ED's timeout helper is consulted by original interpreter requests in the current implementation; archived provider latency is not proof of an exact historical timeout setting.

Existing inherited social/final-emission failures remain relevant to later implementation validation, but rerunning their known narrow suites does not establish this conversation works. No new acceptance suite was added and no baseline failure was repaired in PR-EE.


---


# 07 — Final-Emission and Fallback Analysis

Response ownership for the original six turns:

| Stage | Responsibility / observed effect |
|---|---|
| Browser | Sends input without a communication override, renders returned gm_output.player_facing_text |
| Interpreter provider | Supplies structured descriptions, modes, components, sometimes clarification_question; not player-facing narration |
| PR-DO adapter/eligibility | Structure, allowed ids/enums and eligible/unsupported/OOC/abstain classification |
| Live wrapper | Creates blocked/accepted outcomes and candidate fallback/question text |
| API + orchestration | For blocked outcomes WITH a record, builds a new decision; can replace wrapper text. For accepted output, decides whether bridge is needed. |
| Bridge | On turn five only, rejects ASK without an NPC target. Correctly prevents invalid execution. |
| Early response function | Emits deterministic decision text, appends transcript, optionally saves context. Owns all six final replies. |
| Domain resolver / gm narration / final emission / retry | Not reached on any of these six; invocation flags zero, original logs contain no narration response. |

Exact fallback owners: generic “What are you trying to accomplish?” is `_focused_bridge_clarification`'s default at game/conversational_orchestration.py:472; “Who are you asking?” is its missing_target/ASK branch at :457; proposal template :1172; unsupported confirmation :1376–1377. These are early deterministic fallbacks, not final-emission fallbacks.

Turn one's provider understood session readiness, and turn two understood campaign start. The failure then arises when no operation is equated with insufficient intention. Turn three adds an interpreter error (INVENTORY_GRANT); orchestration further transforms an unsupported classification into an offer. Turn six has a provider-written clarification question, but status INTERPRETED means the record decision's not-interpreted branch does not select it. The wrapper's SAFE_ABSTENTION question is also superseded by record-to-compound processing. The existence of that question does not prove it would fully solve the conversation, but it proves a response-owner override occurs upstream of final emission.

No useful provider-generated narrative answer was rejected by validation in these turns: no such answer was requested. No retry loop repeated an invalid narrative premise: retries are zero. Unsupported handling dominates turns three/four/six, while turns one/two are empty-component fallbacks and turn five is a missing-target bridge fallback. It would be incorrect to blame every turn on the interpreter, or every fallback on final_emission_gate.

Current downstream finalization is wired from game/api_turn_support.py:734,747,1411,1426 through final_emission_runtime. The early function game/api.py:731–815 does not call it. Persistent social validation issues documented in PR-ED are separate evidence and were not reclassified as causes here.


---


# 08 — Reproduction Evidence and Limits

## Original production evidence

`original_session_log.json` preserves all six existing log rows. They span 2026-10-16 20:12:25–20:13:33 UTC (4:12–4:13 p.m. America/New_York). Original nested provider records identify five gpt-4.1-mini requests, actual returned model gpt-4.1-mini-2025-04-14, real request ids, tokens and latency; turn four has no provider call. These were available before investigation; they are not newly generated completions. `original_session.json` is the post-interaction persisted envelope, not the original initial state. No original raw HTTP capture, screenshot, exact provider prompts, process build fingerprint, startup flags, or per-turn prestate snapshots were available.

## Controlled current production-entry reproduction

Command: `.venv/Scripts/python.exe artifacts/pr_ee_live_play_failure/investigate.py`.

The runner copies campaign/character/world/combat/conditions/scene files to a disposable directory, sets ASHEN_DATA_DIR before game imports, seeds `create_fresh_session_document`, clears only the copied transcript, and posts the exact UI-shaped bodies to actual FastAPI `/api/chat?ui_mode=player` via TestClient. It does not replace `chat`, interpretation records, orchestrator, bridge, resolvers, storage, or rendering text. At `request_interpretation` only, it returns the ORIGINAL raw provider JSON for that turn. Thus the real production adapter/eligibility and blocked/accepted routing are exercised. It records reconstructed prompts before injection, before/after sessions and prior logs. It sends no external requests in this mode. Lifespan/preflight is not run. No real browser automation or remote deployment is claimed.

Result: six HTTP 200 responses, six byte-for-byte matches of the original logged player-facing strings. World documents unchanged; pending sequence updates and persistence timestamps are recorded. The seven-turn diagnostic including the separate recognized-fresh-start replay is a reproduction exercise, not an acceptance suite.

The extra fresh-start probe uses the exact turn-two sentence and recorded output on an empty transcript. Cue detection is true and structured start is available before posting, yet live interpretation intercepts before scene_opening. See `recognized_fresh_start_replay.json` and `lifecycle_gate_probes.json`.

Windows sandbox limitations: initial temp-file replacement failed with WinError 5 outside the workspace; disposable state was moved inside the artifact directory. Sandboxed TestClient also hung creating asyncio's socketpair before entering the endpoint. The no-network diagnostic then succeeded outside the sandbox after automatic review. These harness failures were not product-turn failures and were not repaired in production code.

## Six semantic alternatives

Fresh live-provider run command was prepared (`investigate.py --live`) but automatic approval review rejected execution before process launch: the requested run might transmit private campaign/world context to an external provider without payload-specific authorization. No fresh calls or alternative provider outputs exist. The rejection was not bypassed. `live_probe_access_limit.json` records this limitation.

All six requested alternatives were evaluated at the real deterministic decision function, in fresh context and in reconstructed post-turn-four rejection context (`semantic_alternatives_static_probes.json`):

| Input | Fresh deterministic result | After original rejection |
|---|---|---|
| Can we start playing? | No deterministic decision | Same; requires unmeasured provider interpretation |
| Describe the opening scene. | No deterministic decision | Same |
| What is happening around me? | No deterministic decision | Same |
| I'm speaking to you, the DM. | No deterministic decision | Same |
| Why can't you do that? | No deterministic decision | ANSWER/recent_visible_context_answer; repeats the previous refusal with a “From what has already been established” prefix, rather than explaining why |
| What should my character do next? | No deterministic decision | Same; narrower planning regex does not recognize this wording |

“No decision” is not a completed failing API response. It establishes lack of deterministic ownership, not the answer a new provider completion would give. Semantic robustness across fresh provider outputs remains unmeasured. The generality of the confirmed singleton/unsupported bug follows from the branch predicate and two different original component classes, not a guessed model completion for each phrase.

## Configuration and version

Current checkout HEAD is d31beb7d73dd4fda0f22184a6a69b947b5f470ff (“PR-BN bounded DM improvisational authority”), with extensive later modified/untracked files. Therefore HEAD alone cannot identify PR-EA–ED code. `git_status_at_review.txt`, `source_hashes.json`, and source_snapshot preserve the inspected implementation. Current effective default/high-precision/interpreter model is gpt-4.1-mini and model routing is enabled. The original returned model matches that configured family. All original responses and decision reasons match current source/replay. This supports current implementation compatibility; it does not prove the production process loaded these exact bytes, used identical flags, or was freshly reloaded. Process inspection was unavailable (CIM denied), and no deployment/source fingerprint exists in the six log entries. No evidence warrants claiming a stale deployment as the cause, nor certifying intended deployment configuration.

Original provider call accounting is preserved separately from replay timing. Top-level performance stage/token fields are null on early exits; nested original usage contains the missing tokens and actual interpreter latencies. No raw credentials or .env file are packaged.


---

# 09 — Root-Cause Register

Task classification letters are used verbatim (A lifecycle; B interpretation; C orchestration; D context; E confirmation; F resolver contract; I fallback; J prompt/schema; K integration/configuration; L architectural deficiency). No G narration or H final-emission defect is established for this interaction.

## EE-01 — Message-purpose/authority contract excludes ordinary GM/session/narrative requests

- Role / categories: primary; C, J, L.
- Evidence: Original turns 1,2,6; orchestration:1616–1674; schema modes; prompt mode line.
- Trigger: Understood readiness/start/GM address with no connected world operation.
- Responsible component: PR-DR prompt / PR-DO schema / record decision / API mode routing.
- Downstream consequence: Understood intention becomes clarification or unsupported executable proposal.
- Severity / confidence: Critical; High.
- Recommended repair boundary: Typed recipient and purpose independent of executable components; non-mutating GM answer path with grounded context.

## EE-02 — Unsupported singleton becomes compound confirmation, including zero executable steps

- Role / categories: primary; C, E, F, I.
- Evidence: Original turns 3,6 and exact HTTP replay; stored supported=false.
- Trigger: Any unsupported component, even when component count is one.
- Responsible component: conversational_orchestration.py:1442–1477,1673;1146–1188.
- Downstream consequence: False multi-action language, approval of known impossible action, misleading promise.
- Severity / confidence: Critical; High.
- Recommended repair boundary: Separate unsupported/single/compound routes; validate each offer before confirmation; preserve operation identity and scope.

## EE-03 — GM rejection/recipient absent from typed continuation; questions bypass pending; bridge clarification not stored

- Role / categories: primary; D, C, E, B.
- Evidence: Original turns 4–6, original post-session; captured reconstructed context includes prior refusal.
- Trigger: Why not? after engine-owned rejection; subsequent explicit GM recipient.
- Responsible component: orchestration:323–449,1352–1360; API early-response/context updater.
- Downstream consequence: Question becomes NPC ASK; missing_target emits Who are you asking; next reply cannot fill unstored question slot.
- Severity / confidence: Critical; High.
- Recommended repair boundary: Persist rejection subject/reason/recipient and actual pending conversational obligation; dispatch GM follow-ups before NPC action routing.

## EE-04 — Lifecycle availability tied to empty transcript; recognized chat opening still filtered before lifecycle dispatch

- Role / categories: primary; A, C, L.
- Evidence: Original turn 2 follows logged clarification; lifecycle_gate_probes; recognized_fresh_start_replay.
- Trigger: Any non-opening chat before start; or fresh matching start cue with live interpretation enabled.
- Responsible component: api.py:4474–4494,4565–4578,6198–6290,6508.
- Downstream consequence: Started=false yet start UI disabled; existing opening implementation unreachable for these requests.
- Severity / confidence: Critical; High for current implementation; historical UI before turn one unknown.
- Recommended repair boundary: Route lifecycle intent before world interpretation; gate start on authoritative lifecycle completion rather than arbitrary transcript content.

## EE-05 — Provider assigns campaign start to INVENTORY_GRANT; Why not to in-world ASK

- Role / categories: contributor; B, J.
- Evidence: Original raw_interpretation turns 3 and 5, not inferred from replies.
- Trigger: Begin; Why not under restricted mode/operation prompt.
- Responsible component: Original interpreter completions / prompt-schema authority categories.
- Downstream consequence: Unsupported/missing-target processing; downstream routing amplifies classifier errors.
- Severity / confidence: High; High occurrence; frequency unmeasured.
- Recommended repair boundary: Correct semantic contract and context projection; retain validation against unintended operations, avoid phrase handlers.

## EE-06 — Mode and operation vocabularies disagree across schema, eligibility and orchestration

- Role / categories: secondary integration defect; C, F, J.
- Evidence: Original turn 6; static schema/routing inspection for RULES_QUESTION.
- Trigger: OTHER+SOCIAL_SIGNAL observed; RULES_QUESTION mismatch latent.
- Responsible component: schema.py:9,35; eligibility.py:23; orchestration.py:91–108,1619.
- Downstream consequence: Describable social signal becomes unsupported; some OOC modes miss answer handling.
- Severity / confidence: High; High current source; RULES_QUESTION not observed here.
- Recommended repair boundary: One shared, explicit mapping from message domain and class to conversation/execution disposition.

## EE-07 — Early-path telemetry calls every completed conversational response successful; tokens/stages missing at summary

- Role / categories: secondary observability; K.
- Evidence: Original turn 4 resolution.success=false but performance.successful=true; nested usage vs null summary.
- Trigger: Non-mutating clarify/decline early return with interpreter usage.
- Responsible component: api.py:785–791,1002–1033.
- Downstream consequence: Responsiveness instrumentation cannot measure playability or summarize interpreter cost reliably.
- Severity / confidence: Medium; High.
- Recommended repair boundary: Separate transport/delivery, decision validity, opening/gameplay success; aggregate interpreter usage.

---


# 10 — Architectural Recommendation

**Select Option B — conversational routing rework.** The current system has useful separation between a non-mutating decision envelope and authoritative resolvers. It demonstrably preserves world state and pending confirmation. Yet message purpose is repeatedly inferred from whether an executable operation exists, and ordinary GM communication has no complete contract. Patching only the compound predicate (Option A) would stop a particularly harmful prompt but leave understood start requests, rejection follow-ups, and narrative requests unowned. The evidence does not justify a simulation or narration rewrite (Option C): these systems were not reached.

Smallest coherent intervention for a proposed next implementation cycle (not begun in PR-EE):

1. **Classify communication purpose and recipient independently of execution.** Define GM communication, lifecycle/control, rules/interface, narrative/context request, NPC dialogue, character action, and clarification/confirmation reply. Keep world operations as optional proposed effects, not a required representation for every message. Use one schema-to-orchestration vocabulary with explicit handling for OTHER and unknown/unsupported classes. An intention understood but requiring no operation must be answerable.
2. **Give lifecycle dispatch first ownership.** Use existing scene_opening/start_campaign services. Route recognized lifecycle purposes before operation eligibility. Derive startability from authoritative opening state and explicit lifecycle rules, not an empty transcript. Preserve the distinction between configured campaign, initialized scene, and delivered opening. Do not add another “start campaign” simulation operation or erase history to recover startability.
3. **Make conversational continuation a real obligation.** Persist current recipient, subject, prior rejection/decline reason and pending reply type, with scene/session scope. Pass bounded public projections to interpretation. A GM follow-up should explain the prior engine decision without pretending an NPC was asked. A clarification reply must resume the question actually posed, not stale earlier pending work. Preserve existing NPC context and pending operation machinery under this owner.
4. **Make proposals offerable before confirmation.** Separate no-op, unsupported singleton, true compound, and ambiguous execution. Check capability/target/route before promising a first step; never ask approval of supported=false. Preserve original operation identity, validated support reasons and scene scope. Confirmation resumes an eligible proposal and revalidates changing world facts; it does not discover a static unsupported contract.
5. **Distinguish delivery from success.** Record conversational owner, message domain, interpreter disposition, why a candidate response was superseded, lifecycle status, and user-visible outcome. Aggregate interpreter timing/tokens with narration timing while retaining unavailable values honestly.

Preserve: authoritative storage and snapshot semantics; scene/world/character bootstrap; visible-id grounding and bridge safety; semantic resolution contracts and ordinary_semantic_ownership; noncombat/social/exploration/combat resolvers; downstream narration/final-emission validation; PR-ED provider budget, timeout and skip logic; bounded pending state/NPC context where valid. Do not loosen authoritative execution validation to make GM chat work. Put GM answers before world execution selection and still ground factual claims in player-visible state.

Replace or revise: the mandatory world-operation bias of the interpretation contract, mismatched mode/class vocabularies, unsupported-as-compound dispatch, approval eligibility, transcript-empty lifecycle gating, and continuation ownership. These changes fit the existing early orchestration seam; no second simulation engine or unrestricted provider authority is needed.

Review criteria for that future cycle should evaluate coherent multi-turn behavior across held-out purposes/recipients and changed contexts, not six hardcoded successful phrases. Show who owns every response, that answers and clarifications do not advance simulation, that eligible actions still reach the same resolvers, that unsupported offers never request approval, and that failure before opening does not close opening availability. Use production HTTP and fresh-provider evidence when approved. Retain inherited social/finalization failures as explicit limits; assess those after execution/narration is actually reached. PR-EE makes no claim that these recommendations alone prove sustainable full-campaign play.

No repairs, new phrase handlers, gameplay expansion, production instrumentation, or new acceptance tests were implemented. Stop after this package.


---


# 11 — Changed-File Inventory

PR-EE changed only investigation artifacts under `artifacts/pr_ee_live_play_failure/` and the established handoff files `handoff/CURRENT_REVIEW.md`, `handoff/REVIEW_MANIFEST.json`, `handoff/CURRENT_REVIEW.zip`. `package_inventory.json` lists every package member with byte count and SHA-256 (except the inventory itself, whose hash appears in REVIEW_MANIFEST). `source_hashes.json` fingerprints the copied current sources; source_snapshot contains copies, not production edits.

- Documents: 01–11 reports and combined REVIEW.md.
- Original evidence: original_session_log.json, original_session.json, original_provider_totals.json; original data is read/copied only.
- Diagnostic evidence: recorded_output_http_replay.json, recognized_fresh_start_replay.json, lifecycle_gate_probes.json, semantic_alternatives_static_probes.json, replay_environment.json, replay_preservation_check.json, production_hashes_before.json, final_preservation_check.json, live_probe_access_limit.json, validation_results.json, root_cause_register.json.
- Runners: investigate.py and build_review.py. Temporary instrumentation is process-local wrapping of request_interpretation to inject recorded raw outputs and capture reconstructed requests; no instrumentation edits in production modules. Optional --live mode remains unexecuted and requires explicit approval of payload/destination.
- Context: git_status_at_review.txt, git_revision.txt, prior_cycle_reports/, predecessor_handoff/ (PR-ED's prior CURRENT_REVIEW files preserved), source_snapshot/, source_hashes.json.
- Generated packaging: package_inventory.json; handoff manifest and zip.

Disposable copied state directories named pr_ee_* inside this artifact directory are diagnostic runtime copies, excluded from CURRENT_REVIEW.zip. Failed sandbox attempts also used temporary state; no live campaign was targeted. Runtime copies may be removed after review; reproducibility comes from runner plus current source snapshot and captured before/after records. No sensitive environment file or credentials are copied into the review package.

Before/after SHA-256 checks cover every game Python file, static asset, top-level data JSON/JSONL and scene JSON. The replay check and final check require zero changes in those paths. The repository already had extensive unrelated dirty/untracked work (including game and data changes from earlier cycles). PR-EE neither reverts nor claims those changes. The new CURRENT_REVIEW intentionally supersedes PR-ED's handoff, whose prior files remain archived in predecessor_handoff.
