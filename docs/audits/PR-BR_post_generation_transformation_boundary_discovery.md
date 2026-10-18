# PR-BR Continuation 17 — Post-Generation Transformation Necessity and Hard-Validation Boundary

Discovery only. No gameplay behavior change. No parser, contract, prompt, validator, fallback, evaluator, or state change. No live gameplay call. No interpretation call. No synthetic-player call. No evaluator-model call. No independent smoke. No full synthetic gate. No human playtest. PR-BR remains open. PR-BS was not started.

HEAD at discovery: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. Continuation 16 and the failed smoke are uncommitted work on that commit. This document is the Continuation 17 record. The campaign history in `docs/audits/PR-BR_typed_resolution_contract_and_discourse_state.md` points here.

Sources: `game/api.py`, `game/api_turn_support.py`, `game/gm_retry.py`, `game/resolution_contract.py`, `game/interaction_completion.py`, `game/live_resolution.py`, `game/social.py`, `game/perception_grounding.py`, `game/referenced_surface.py`, `game/social_exchange_fallback_catalog.py`, `game/final_emission_gate.py`, recorded sessions `artifacts/pr_br_continuation16/20261001T113214Z` and `artifacts/pr_br_independent_smoke/20261001T104551Z`, and the Continuation 13–16 manual reviews.

Offline scorecard: `artifacts/pr_br_continuation17/counterfactual_scorecard.json`.

## 1. Executive conclusion

The recent product failures are dominated by post-generation rewriting, not by failed generation.

On the sixteen recorded turns (Continuation 16's six live turns plus the failed independent smoke's ten):

| | Count |
| --- | --- |
| Initial manual PASS | 12 / 16 |
| Final manual PASS | 5 / 16 |
| Preserve-if-hard-valid counterfactual manual PASS | 12 / 16 |
| Initial candidates that are hard-invalid | 4 / 16 |
| Downstream-created failures (initial PASS, hard-valid, final FAIL) | 7 |
| Downstream-prevented failures (initial would FAIL, final PASS) | 0 |

Generation already satisfied the player on twelve turns. Deterministic machinery then destroyed seven of those twelve. It repaired none of the four turns whose initial text was actually illegal.

**Recommendation: Option C.** Replace most post-generation transformation with preserve-if-valid, one bounded regeneration when the candidate is hard-invalid, and a short deterministic nonresolution only after that retry fails. Deterministic authority over state, mechanics, permissions, and PR-BN classes stays. It stops authoring a "better" natural-language answer after a legal model answer already exists.

Option A (keep the current transformation pipeline) is not supported. The failures are the same families across Continuation 13, 14, 16, and the smoke, and they are produced by the replacement stages themselves.

Option B (a smaller rewrite set) still leaves semantic authorship after generation. The recorded damage is that authorship.

## 2. Why C17 was opened

Continuation 16's deterministic band was 350 / 350 PASS, and the ten recorded smoke replays passed their after-repair invariants. Fresh focused live validation was different: initial manual PASS 6 / 6, final manual PASS 2 / 6, manual semantic degradations 4, telemetry degradations 1.

The model had already produced a legitimate inability, a passage answer, a watcher answer, and a successful notice reading. Downstream stages replaced them with a quoted manner line, an unrelated Thoran sentence, a generic guard fallback, and "Nothing here matches that" prefixed onto the facts just read.

That split is the architectural question: validation versus rewriting.

## 3. C13–C16 quality progression

Manual reviews, not telemetry:

| Cycle | Initial manual | Final manual | What moved between them |
| --- | --- | --- | --- |
| C13 (`20261001T003832Z`) | 5 / 6 | 2 / 6 | Clue-frame replaced a clearance answer, a use answer, and a certainty answer with a stored Thoran or patrol fact. |
| C14 (`20261001T013504Z`) | 6 / 6 | 4 / 6 | A clarification and a traveler report were replaced by an inability template and the Thoran sentence. `best_safe` stored the worse line. |
| C15 focused (`20261001T094739Z`) | 4 / 4 | 4 / 4 | Identity emission on a narrow set. |
| Independent smoke (`20261001T104551Z`), C15 tree | 6 / 10 | 3 / 10 | Shells, a player-text splice, wrong-speaker collapse, a grounding closer, a scene-line substitution. Evaluator 8 / 10. |
| C16 focused (`20261001T113214Z`) | 6 / 6 | 2 / 6 | Manner quote, false "find them" rejection, wrong speaker, "Nothing here matches that." Telemetry 1 / 4. |

Continuation 15's focused identity result did not survive contact with ordinary play. Each later cycle added another selector or structural check. The live failure mode stayed: a useful generated line is replaced by a deterministic sentence that satisfaction then scores as an answer.

Recorded retries in both C16 and the smoke: 0. `MAX_TARGETED_RETRY_ATTEMPTS` in `game/gm_retry.py` is 2. The live path preferred substitution over regeneration.

## 4. Current response-pipeline diagram

Live `POST /api/chat` (`game/api.py` `api_chat` → `chat`). Stage names match `AUTHORITATIVE_TURN_STAGE_ORDER` in `game/api_turn_support.py` where that list exists. The post-model tail is longer than that list.

```text
PLAYER TEXT
    |
    v
segment_mixed_player_turn
resolve_directed_social_entry / declared actor switch
implied interaction prep
choose_interaction_route
deterministic intent parse
    |
    +-- off-scene or pending check --> engine GM text --------+
    +-- adjudication --------------> engine GM text --------+
    |                                                         |
    v                                                         |
attach_interaction_obligation                                 |
construct Resolution Contract                                 |
(optional interpret_for_contract)                             |
    |                                                         |
    v                                                         |
AUTHORITATIVE STATE MUTATION                                 |
(world, scene, clues, scene runtime)                         |
    |                                                         |
    v                                                         |
prompt context + call_gpt                                     |
    |                                                         |
    v                                                         |
guard_gm_output                                               |
bounded-improvisation attach                                  |
RETRY LOOP (detect, strategy, regenerate or                  |
            apply_deterministic_retry_fallback)              |
    |                                                         |
    v                                                         |
response-policy enforcement                                   |
authored-knowledge realization                                |
stay/leave agreement                                          |
destination-arrival realization                               |
perception non-invention                                      |
    |                                                         |
    v                                                         |
_finalize_player_facing_for_turn  <--------------------------+
    repeated-description guard
    serialized-payload strip
    sanitize (non-strict social)
    apply_final_emission_gate
        strict social: rebuild the line, else catalog fallback
        non-strict: layer stack, else sealed replace
    reconcile text with structured state
    obligation / contract preserve fallbacks
    select_preserved_answer
    commit_discourse_focus + note_emitted_npc_claim
    |
    v
SECOND PASS of authored-knowledge, stay/leave,
destination, and perception grounding
    |
    v
enforce_emitted_contract_monotonicity
    |
    v
_apply_post_gm_updates
    promote accepted bounded improvisation
    second NPC-claim note
    spoken-state refinement append
    |
    v
save session / world / log
    |
    v
PLAYER-VISIBLE TEXT
```

`game/interaction_completion.py` is not a stage of its own. `structural_assessment` and `generic_ask_completion` are called from the contract, the retry detector, and monotonicity.

## 5. Pipeline-stage table

| Stage | Source | Input | Output | Text can change | Candidate replaced | Candidate rejected | New prose | Authority / state | Semantic resolution | Necessity now | Failure risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Segmentation and route | `intent_parser.segment_mixed_player_turn`, `interaction_routing.choose_interaction_route` | Raw player text | Segments, route | No | No | No | No | Lane only | Coarse | Required | Wrong lane skips the contract |
| Deterministic intent | parse chain in `api.py` `chat` | Classification text | Normalized action or none | No | No | No | No | None yet | Intent label | Required | Missed social target |
| Contract construction | `live_resolution.attach_interaction_obligation` | Resolution, player text, scene | `resolution_contract` | No | No | Skips if a contract exists | No | Metadata | Operation, target, interlocutor, dimension | Required | Stale discourse inheritance (smoke turns 4, 6, 10) |
| Structured interpretation | `interpret_for_contract` when the fast path abstains | Player text, discourse | Proposal | No | No | Abstain | No | None | Referent | Required for ambiguous follow-ups | Smoke turn 7 accepted an ambiguous referent without clarification |
| Authoritative mutation | `_apply_authoritative_resolution_state_mutation` | Resolution | Scene, session, clues | No | No | No | No | World truth before narration | None | Required | Narration can later disagree with a mutation that already committed |
| Model generation | `gm.call_gpt` inside `_build_gpt_narration_from_authoritative_state` | Messages, contract | `player_facing_text` | Yes | No | Exception to schema fallback | Model | None | Realization | Required | Hallucinated consequential fact |
| Leak guard | `response_policy_enforcement.guard_gm_output` | Model text | Sanitized text | Yes | On leak | No | Bounded uncertainty | Hidden information | None | Required | Over-stripping is rare in these sessions |
| Retry loop | `gm_retry.detect_retry_failures`, `apply_deterministic_retry_fallback` | Candidate | Same, new model text, or fallback | Yes | Yes | Yes | Yes | Contract retention | Treats quality misses as retry causes | The loop exists; these sessions took 0 retries | Falls through to substitution |
| Policy handoff | `apply_response_policy_enforcement` | Candidate | Rewritten or appended text | Yes | Yes | No | Yes | Topic pressure, momentum | "Must answer" shaping | Historical quality pressure | Appends a beat the player did not ask for |
| Authored-knowledge realization | `social.apply_authored_knowledge_realization_to_gm` | Candidate, stored topics | Candidate or catalog line | Yes | Yes | Rank-0 lines lose | Yes | Authored clues | Swaps in a stored fact | Needed only when the model concealed a fact the question asked | C13 and C16: injected Thoran into a different question |
| Perception grounding | `perception_grounding.apply_perception_non_invention_to_gm`, `referenced_surface.render_referenced_surface_inspection_line` | Inspect prose | Grounded stock line | Yes | Yes | Via grounding lock | Yes | Visible facts | Replaces observation | The check is required; the stock sentence is not | "Nothing here matches" on a true reading |
| Final emission gate | `final_emission_gate.apply_final_emission_gate` | Candidate | Accepted or replaced text | Yes | Yes | Yes | Yes | Visibility, speaker, route | Strict-social rebuild | Packaging and leak control | Rebuilds a manner sentence into the utterance |
| Contract preserve | `select_preserved_answer`, `enforce_emitted_contract_monotonicity` | Current line, `best_safe_candidate` | Higher-ranked line | Yes | Yes | Downgrade | `generic_ask_completion` | None | Rank tournament | Intended to protect a good line | Stores the already-damaged line and emits it |
| Discourse and claims | `discourse_state.commit_discourse_focus`, `note_emitted_npc_claim` | Emitted text | Session slots | No | No | No | No | Discourse, NPC claims | None | Required, after the text is final | Today it runs before a second grounding pass |
| Bounded promotion | `bounded_improvisation.promote_accepted_bounded_improvisation` | Accepted proposals | Persisted details | Can restore text | Yes | No | No | PR-BN promotion | None | Required for accepted narration only | Must not promote a rejected candidate |
| Refinement append | `upstream_response_repairs.apply_spoken_state_refinement_cash_out` | Final text | Text plus sentence | Yes | No | No | Yes | Lead/clue cash-out | Adds a claim | Unclear on the social path | Runs after the finalized flag |

Historical reasons, where the code or the campaign record states them: stay/leave is PR-AE; destination arrival is PR-AF; narration-versus-payload reconcile is PR-AJ / RC-21; the final-emission boundary comment describes Objective C2 as packaging rather than semantic repair; response-policy orchestration is Cycles AI3–AI12; the non-strict stack is Cycle AN4; the terminal pipeline is Cycle AN6. PR-BR Continuations 5, 7, 13, 14, and 15 added preservation, rank, and `best_safe` specifically because earlier stages were destroying answers. Those guards now protect the replacement.

## 6. Post-generation mutator inventory

Thirty-five prose-capable mechanisms are on the live `/api/chat` path after the model returns. Internal helpers that only render a line for one of these mechanisms are counted with their caller. Functions that never change player-facing text are listed under observability or excluded.

The class is what the mechanism does to text today.

### Hard-invariant enforcement (5)

| Mechanism | File | What it does to text | Can change speaker / target / claims |
| --- | --- | --- | --- |
| `guard_gm_output` | `game/response_policy_enforcement.py` | Strips secret-leak patterns. May substitute a bounded uncertainty line. | Claims, by deletion |
| `apply_stay_leave_narration_agreement_to_gm` | `game/narration_state_consistency.py` | Replaces travel prose that contradicts an already resolved stay or move. | Location claim |
| `apply_visibility_enforcement` | `game/final_emission_visibility_fallback.py` | Replaces text that states a non-visible fact. | Facts |
| `hard_reject_social_exchange_text` | `game/social_exchange_emission.py` | Rejects banned social text and forces a fallback selection. | Indirect, via the fallback |
| `apply_narrative_authority_layer` | `game/final_emission_narrative_authority.py` | Flags authority violations and can repair them inside the gate. | Claims |

### Semantic repair (9)

| Mechanism | File | What it does to text |
| --- | --- | --- |
| `enforce_emitted_speaker_with_contract` | `game/speaker_contract_enforcement.py` | Rewrites attribution toward the locked speaker. |
| `retain_resolved_contract_text` | `game/resolution_contract.py` | Puts back an earlier line when a retry would drop coverage. |
| Response-policy answer shaping | `game/response_policy_enforcement.py` | `enforce_question_resolution_rule`, `enforce_forbidden_generic_phrases`, `enforce_npc_response_contract` prepend, rewrite, or append so the line looks answered. |
| `sanitize_player_facing_output` / `final_validation_pass` | `game/output_sanitizer.py` | Sentence-level heuristic rewrite before the gate on non-strict turns. |
| `select_preserved_answer` | `game/resolution_contract.py` | Chooses among the current line and stored candidates, including speaker retarget. |
| `enforce_emitted_contract_monotonicity` | `game/resolution_contract.py` | Restores a higher-ranked stored line, or calls `generic_ask_completion`. |
| `apply_social_response_structure_repair` | `game/final_emission_repairs.py` | Rebuilds dialogue shape. Continuation 16 turn 4 lost clauses here or in the strict-social rebuild. |
| `apply_spoken_state_refinement_cash_out` | `game/upstream_response_repairs.py` | Appends a refinement sentence after the finalized flag. |
| `apply_answer_shape_primacy_layer` | `game/final_emission_answer_shape_primacy.py` | Aligns the line to an answer shape the gate expects. |

Counted semantic-repair mechanisms: **9**.

### Fallback / substitute response generation (13)

| Mechanism | File | Stock effect seen or coded |
| --- | --- | --- |
| `apply_deterministic_retry_fallback` | `game/gm_retry.py` | Deterministic line when retry validation fails. Unused in these 16 turns (0 retries). |
| `ensure_minimal_social_resolution` | `game/gm_retry.py` | Fills an empty social GM. |
| Scene-pressure appenders | `game/response_policy_enforcement.py` | `enforce_scene_momentum`, `escalate_passive_scene`, `enforce_topic_pressure_escalation`. Smoke tags include `scene_momentum:*` on almost every turn. |
| `apply_authored_knowledge_realization_to_gm` | `game/social.py` | Replaces a rank-0 line with a stored topic. C16 turn 3 source `npc_topic:gate_guard:watch_command`. |
| `apply_perception_non_invention_to_gm` + `render_referenced_surface_inspection_line` | `game/perception_grounding.py`, `game/referenced_surface.py` | "Nothing here matches that. What you can actually see is …" and "Closer looking yields nothing further." |
| Strict-social rebuild and emergency pool | `game/social_exchange_emission.py`, `game/social_exchange_fallback_catalog.py` | `build_final_strict_social_response`, `apply_strict_social_terminal_dialogue_fallback_if_needed`, `minimal_social_emergency_fallback_line`. Exact C16 turn 5 string: `{speaker} shakes their head. "I have heard talk, but I cannot verify it."` |
| `obligation_preserving_fallback_line` | `game/live_resolution.py` | `I couldn't tell you {subject}; you will need another source.` Smoke turn 3 put the player's sentence in `{subject}`. |
| `run_generic_replace_exit` | `game/final_emission_generic_exit.py` | Sealed replacement when the gate has any reason. |
| `apply_first_mention_enforcement` | `game/final_emission_visibility_fallback.py` | Smoke turn 7 tag `first_mention_enforcement_replaced`. The recorded strings still match. |
| `apply_referential_clarity_enforcement` | `game/final_emission_visibility_fallback.py` | Smoke turn 10 tag `referential_clarity_violation:ambiguous_entity_reference`. Watcher answer became a scene line. |
| `generic_ask_completion` | `game/interaction_completion.py` | `I cannot answer that from what is settled here.` No new topic, no player quote. |
| `apply_destination_arrival_realization_to_gm` | `game/narration_state_consistency.py` | Replaces a destination stub with an arrival line. |
| `apply_repeated_description_guard` | `game/storage.py` | Replaces a repeated hash with "You find nothing new…" |

### Presentation-only (3)

| Mechanism | File | Effect |
| --- | --- | --- |
| Serialized-payload extract and strip | `game/output_sanitizer.py` | Pulls prose out of a JSON-shaped leak. |
| `apply_context_separation_layer`, `apply_player_facing_narration_purity_layer` | `game/final_emission_context_separation.py`, `game/final_emission_player_facing_narration_purity.py` | Strip player/GM bleed and planner residue. |
| `finalize_emission_output` | `game/final_emission_finalize.py` | Whitespace, HTML, route-illegal sentence strip. Objective C2 describes this as packaging. |

### Observability only (2)

| Mechanism | File | Effect |
| --- | --- | --- |
| `remember_satisfied_candidate` | `game/resolution_contract.py` | Stores `best_safe_candidate`. Does not itself write the sentence. The tournament that reads the store does. |
| `detect_semantic_degradation` | `game/resolution_contract.py` | Records reasons. Continuation 16 documents that the detector does not choose the emitted line. The tone layer is validate-only at the boundary and belongs with this group. |

### Legacy / redundant / unclear (3)

| Mechanism | Why it is in this class |
| --- | --- |
| Second pass of authored-knowledge, stay/leave, destination, and perception grounding after `_finalize_player_facing_for_turn` | The same four functions already ran in the narration hub. The second pass can still change text after discourse commit. |
| `best_safe` tournament | Built to stop later degradation. On these sessions it stored the damaged line (`best_safe` emission mismatches 0) and then protected that damage. |
| Satisfaction rank as a replacement chooser | A shell or a stored fact at rank 4 beats a legitimate inability at rank 2, or a rank-0 false invalidity. |

**Tally:** 5 hard-invariant, 9 semantic-repair, 13 fallback/substitute, 3 presentation, 2 observability, 3 legacy. **35** prose-adjacent mechanisms. Semantic-repair plus fallback/substitute: **22**.

Not prose mutators, and not counted: `apply_social_narration_lead_supplements` (lead state), `update_scene_momentum_runtime` (counters), `apply_social_reply_speaker_grounding` (resolution social payload).

## 7. Mutator classification

The classes above are the classification. One consequence matters more than the labels: **22 of 35 mechanisms can author or swap natural-language meaning after generation.** Five are legitimate hard stops. Three only package text. Two only record. Three are redundant with a guard that already ran, or they rank candidates the model did not need ranked.

High-risk substitutions, matched to recorded lines:

| Recorded line | Mechanism |
| --- | --- |
| `Tavern Runner says, "The tavern runner shakes their head…"` | Strict-social rebuild. The manner sentence became the quoted payload. |
| `Guard Captain says, "Word is, captain Thoran commands the gate watch tonight."` | `apply_authored_knowledge_realization_to_gm`, stage `clue_frame`, reason `npc_topic:gate_guard:watch_command`. |
| `The guard shakes their head. "I have heard talk, but I cannot verify it."` | `minimal_social_emergency_fallback_line` / `lawful_strict_social_dialogue_emergency_fallback_line`. Speaker label resolved to "The guard". |
| `Nothing here matches that. What you can actually see is…` | `render_referenced_surface_inspection_line` when authority is `AUTHORITY_UNSUPPORTED`. |
| `Closer looking yields nothing further.` | Same renderer, authored visible-feature branch. |
| `I couldn't tell you` plus the player's own words | `obligation_preserving_fallback_line`. |

## 8. Hard-invalidity taxonomy

A generated response **cannot be emitted** when any of the following is true at high confidence. The test is against canonical state, the mechanical result, permissions, and the current contract when that contract agrees with the player's explicit address.

| Category | Emit? | Evidence |
| --- | --- | --- |
| Hidden-information or secret leak | No | `guard_gm_output` exists for this. Not observed in these 16 turns. |
| Narrator asserts a consequential fact that is not in authored state and not marked as an NPC claim | No | Smoke turn 9: a dusk curfew "less than three hours away" as a posted rule. |
| Mechanical outcome contradicts the resolved roll, HP, inventory, or movement | No | Not in these social/inspect turns. The engine already mutates that state before narration. |
| Dead NPC acts as alive, or an impossible inventory/location claim | No | Not in these 16 turns. Still a hard stop. |
| Explicit wrong speaker when the contract interlocutor and the player's address agree | No | Smoke turns 4 and 5: the runner answers a question put to a guard. The contract on turn 5 had already moved to `gate_guard`. |
| Line tells the player to go find the person they are addressing | No | Smoke turn 7: "you might need to find the guard captain" after the captain was the person just questioned. High confidence because the sentence names that person as someone to locate. |
| Player utterance embedded as NPC speech | No | Smoke turn 3 final line. The initial line did not do this. The fallback did. |
| Empty, truncated-token, or attribution shell with no proposition | No | Smoke turns 1, 4, and 5 finals. The initials were complete sentences. |
| Canonical-state contradiction (the text denies a fact the engine just established, or asserts an absent object is present) | No | Not the C16 notice reading. That reading matched taxes, curfew, and the missing patrol. |

These are **not** hard-invalid by themselves:

| Situation | Why it can be emitted |
| --- | --- |
| Legitimate inability or refusal | C16 turns 1 and 2, smoke turns 1, 2, 3, and 8. The contract's expected resolution includes a real nonresolution. |
| NPC dialogue that states a policy as that NPC's words | Smoke turns 6 and 8. PR-BN records this as a claim, not as world truth. The smoke ledger stored no claims; that is a recording gap, not a reason to rewrite the line. |
| Extra scene-compatible color (rain, a glance, a bundle) | C16 turns 4 and 6. |
| Awkward or slightly mechanical wording | C16 turn 2's refusal is stiff and still a completed ask. |
| A suggestion to look at a notice board or a serjeant while speaking to the captain | C16 turn 3. "Find the specifics" is not "find the captain." |

`recommends_locating_interlocutor` in `game/interaction_completion.py` is the false-positive mechanism. `_LOCATE_RE` matches `find`. The label test then requires every significant word of the interlocutor label to appear anywhere in the line. "The guard captain replies" supplies `guard` and `captain`. "You'll find the specifics" supplies `find`. The function returns true. Continuation 16 turn 3 was marked `discourse_state_contradiction`, satisfaction rank 0, and the Thoran topic replaced it.

## 9. Quality versus invalidity

| Example | Class | What should happen |
| --- | --- | --- |
| Bland, terse, awkward, or mechanical wording | Quality | Emit |
| Imperfect atmosphere, redundant phrase | Quality | Emit |
| Weak but valid explanation | Quality | Emit |
| Extra compatible information | Quality | Emit. Do not strip it to "improve" focus. |
| Legitimate uncertainty, inability, or refusal | Valid nonresolution | Emit |
| Quoted manner with the real answer still in the line | Valid | Emit the model line. Do not rebuild. |
| Attribution shell, player-text splice, wrong speaker, invented posted hour, "go find the person in front of you" | Hard-invalid | Do not emit. Retry once under the same contract. Then the safe nonresolution. |

A response can be stylistically imperfect and still be semantically valid, state-consistent, authority-safe, and interaction-complete. On these sixteen turns, every initial manual pass was that kind of response. Deterministic machinery should have left those twelve alone.

## 10. C16 six-turn counterfactual

Session `20261001T113214Z`. Manual column is the Continuation 16 review. Hard-valid is this cycle's judgment, not the live structural flag. Turn 3's live flag was `discourse_state_contradiction`; that flag is the false positive.

| Turn | Initial manual | Hard-valid | What changed | Why it fired | Final manual | Preserve-initial | Genuine invariant in the initial | Transformation necessary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PASS | YES | Inability about stew prices became `Tavern Runner says, "The tavern runner shakes their head slightly, voice lowered amid the bustle."` | Strict-social rebuild. Satisfaction then scored the quote `inquiry_answered` at rank 4. `best_safe` is the quote. | FAIL | PASS | None. Legitimate inability, correct speaker. | NO |
| 2 | PASS | YES | None. Clue-frame and final emission compared the refusal to itself. | `resolution_content_preserved` | PASS | PASS | None. Refusal completes the ask. | NO |
| 3 | PASS | YES | Passage inability became `Word is, captain Thoran commands the gate watch tonight.` | `find` plus the words `guard captain` in the attribution. Rank 0 to 4 via `npc_topic:gate_guard:watch_command`. | FAIL | PASS | None. The redirect is to the notice board and the serjeant, not to the captain being addressed. | NO |
| 4 | PASS | YES | Quotes and some clauses dropped. The watcher still answers. | Strict-social or structure repair. Both the runner's initial view and the manual review call the final a pass. Evaluator false FAIL. | PASS | PASS | None | NO. Redundant trim. |
| 5 | PASS | YES | Watcher explanation became `The guard shakes their head. "I have heard talk, but I cannot verify it."` | Exact emergency-pool line. The transition log never saw the model sentence; replacement happened before a safe candidate was stored. Speaker label is "The guard", not the contract's `threadbare_watcher`. | FAIL | PASS | None. The model used the contract interlocutor. | NO |
| 6 | PASS | YES | Useful reading gained `Nothing here matches that.` | Referenced-surface unsupported template. Clue-frame rejected a stronger "no further reliable detail" line as `grounding_contradiction`. Final emission still applied `grounding_correction_authoritative`, so the model line was not restored. | FAIL | PASS | None. Taxes, curfew, and the missing patrol are authored. | NO |

Recommended future behavior for all six: emit the initial line. Turn 4's trim is optional packaging and is not allowed to drop clauses.

## 11. Failed-smoke ten-turn counterfactual

Session `20261001T104551Z`. Manual initial/final labels are the smoke audit. Contract errors are noted because several initials fail the player while obeying a stale contract.

| Turn | Initial manual | Hard-valid | What changed | Why it fired | Final manual | Preserve-initial | Genuine invariant in the initial | Transformation necessary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PASS | YES | Price inability became `Tavern Runner says with a tight shrug, voice low and hurried,` | Strict-social rebuild. Initial satisfaction `valid_inability`. Final satisfaction `inquiry_answered`. | FAIL | PASS | None | NO |
| 2 | PASS | YES | Market Quarter archway sentence dropped. The price hedge remains. | Grounding or quote trim. Both lines answer. | PASS | PASS | None. An off-scene place inside NPC speech is a claim, not a state write. | NO. Neutral trim. |
| 3 | PASS | YES | Real refusal became `I couldn't tell you` plus the player's sentence, cut off. | `obligation_preserving_fallback_line`. Tag `interaction_obligation_terminal_preserved`. | FAIL | PASS | None | NO |
| 4 | FAIL | NO | Runner's passage answer became a runner glance shell. | Discourse inheritance kept `tavern_runner` after the player addressed a guard. Emission then stripped the payload. | FAIL | FAIL | Wrong interlocutor relative to the player's explicit address. The contract was already wrong. | Reject the initial. The glance shell is not the repair. |
| 5 | FAIL | NO | Runner's permit speech became a runner shell that stops at `adding,` | Contract interlocutor was `gate_guard`. The model still wrote the runner. The shell kept the runner. | FAIL | FAIL | Wrong speaker against both the contract and the player. | Reject the initial. Regenerating under the guard contract is the repair. The shell is not. |
| 6 | PASS | YES | None | Identity. Tag `resolution_contract_semantic_preserved`. | PASS | PASS | None. Toll policy is the captain's claim. | NO |
| 7 | FAIL | NO | None. Tags say the gate and first-mention ran; the recorded strings match. | The model already wrote "find the guard captain." Satisfaction scored it `covered:content`. | FAIL | FAIL | Tells the player to locate the captain who just answered. | Reject. No substitute was applied, so nothing was prevented. |
| 8 | PASS | YES | None | Identity. The refusal is the resolution. | PASS | PASS | None | NO |
| 9 | FAIL | NO | Invented dusk hour and the mud-track clue became the visible-fact sentence plus `Closer looking yields nothing further.` | `referenced_surface_realization`, `passive_scene_pressure_grounded_observe`. `best_safe` invalidated with `grounding_contradiction`. The closer was still emitted. | FAIL | FAIL | Narrator states an unauthored curfew hour as a posted fact. | Reject the hour. The closer is the wrong substitute: it also drops the authored mud-track clue. |
| 10 | PASS | YES | Watcher says they are looking for a face. Emitted: `As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line.` | `referential_clarity_enforcement_replaced`. Initial scored `unrelated_fact` because the contract was still `guard_captain`. The scene line scored `inquiry_answered` at higher rank. | FAIL | PASS | None. The face is an NPC claim inside the answer the player asked for. The contract was stale. | NO |

## 12. Counterfactual scorecard

| | C16 (6) | Smoke (10) | All (16) |
| --- | --- | --- | --- |
| Initial manual PASS | 6 | 6 | 12 |
| Final manual PASS | 2 | 3 | 5 |
| Preserve-if-hard-valid manual PASS | 6 | 6 | 12 |
| Initial hard-invalid | 0 | 4 | 4 |
| Downstream-created failures | 4 | 3 | 7 |
| Downstream-prevented failures | 0 | 0 | 0 |
| Rejection of the initial was necessary | 0 | 4 | 4 |
| Rewrite was harmful | 4 | 6 | 10 |
| Rewrite was neutral or redundant | 2 | 4 | 6 |

Preserve-if-hard-valid counts a turn as a pass only when the initial was manual PASS and hard-valid. The four hard-invalid initials stay failures until a retry produces a legal line. That retry was not run. This scorecard does not assume the retry would succeed.

Smoke turn 10 is inside the 12 and outside the recorded contract. The watcher answer is hard-valid and manual PASS. The stored contract was still `guard_captain`. Requiring the recorded contract as well would reject that turn and leave 11/16, then retry under the stale captain. The recommended lifecycle corrects the contract from the current-turn addressee before validation, so the watcher line becomes the contract-satisfying line and the 12 stands.

Neutral/redundant: C16 turns 2 and 4; smoke turns 2, 6, 7, and 8. Smoke turn 7 is neutral as a diff (the text did not change) and still a failed turn.

## 13. Downstream-created failure analysis

Primary metric: initial manual PASS, hard-valid, and the downstream transformation caused the final FAIL.

**7 turns:** C16 1, 3, 5, 6 and smoke 1, 3, 10.

Shared pattern:

1. The model completes the interaction.
2. A lexical or ownership check marks the line invalid, or a rebuild extracts the wrong sentence.
3. A substitute (catalog topic, emergency pool, referenced-surface closer, obligation template, scene fact) replaces it.
4. Satisfaction scores the substitute as `inquiry_answered` or equal-rank content, so `best_safe` stores the substitute.
5. Monotonicity then protects the substitute. Emission mismatches stay 0.
6. The degradation detector compares the damaged store with the damaged final, and reports nothing. C16 turn 6 is the exception (`lower_rank`, `target_loss`) because the final satisfaction actually fell.

Telemetry caught 1 of these 7 (C16 turn 6). The smoke detector caught 0 of its 6 manual degradations, three of which are in this created-failure set.

## 14. Downstream-prevented failure analysis

**0** turns moved from an initial manual FAIL to a final manual PASS.

Smoke turn 9 is a partial block, not a prevented failure. The invented dusk hour did not reach the player. The replacement also deleted the authored mud-track clue and said closer looking yields nothing further. The player-visible result still fails. Blocking the hour is the behavior to keep. Authoring the closer is not.

No recorded turn shows a hard-invalid model line repaired into a manual pass by substitution.

## 15. Historical transformation-necessity table

| Mechanism | Introduced | Original failure | Hard-invalidity | Quality problem | Still necessary as a rewriter | Validation + one retry instead |
| --- | --- | --- | --- | --- | --- | --- |
| Perception non-invention / referenced surface | Pre-BR grounding, kept through PR-BR | Model invents inspectable detail | YES when the invention is narrator fact | The closer sentence is quality theater | The check YES. The stock sentence NO | YES. Reject the invention. Retry with the visible-fact list in the contract. |
| Authored-knowledge realization / clue frame | Social topic pressure; live damage from C13 onward | Model hides a stored fact behind fake ignorance | Sometimes, when the question asked that fact | Often. C13 turns 1, 4, 6 and C14 turn 5 and C16 turn 3 replace a different answer with Thoran or the patrol | NO as a swap | YES, and only if the stored fact is the contract's requested content. Do not swap topics. |
| Strict-social rebuild and emergency pool | Social ownership cycles | Wrong speaker, empty social, validator voice | YES for empty or wrong-speaker output | The pool invents a generic reply and can name the wrong NPC | NO | YES. Retry under the contract speaker. Last resort is `generic_ask_completion` in that speaker's mouth. |
| Obligation fallback `I couldn't tell you {subject}` | Interaction-obligation completion | Dead air on an ask | Empty output is invalid | The template manufactures an inability and has spliced player text | NO | YES. A real model inability should already have been emitted. |
| `best_safe` / monotonicity | PR-BR C5, C7, C13–C15 | Later stages destroyed a better line | NO | YES. It was a patch on the rewrite pipeline | NO once rewriters leave the critical path | The first hard-valid line does not need a tournament. |
| Satisfaction rank | C6–C16 | Could not tell an answer from a miss | NO | YES. Shells and stored facts outrank inabilities | NO as a chooser | Keep as a yes/no contract check that triggers retry, not replacement. |
| Scene-momentum and topic-pressure append | Response-policy cycles AI3–AI12 | Scenes felt static | NO | YES | NO | Put pressure in the prompt context if a future cycle wants it. Do not append it after a valid answer. |
| Stay/leave agreement | PR-AE | Narration contradicted a resolved move | YES | NO | YES, as a short factual correction when the mechanical result is already committed | A retry can do it. A one-sentence factual correction is an acceptable last resort because the fact is structured. |
| Leak guard | Response policy | Secret leak | YES | NO | YES | Retry is optional. Stripping the leak is required even if retry is skipped. |
| `generic_ask_completion` | C16 | Shells and player-text splices | The condition is invalidity | The line is deliberately non-semantic | YES as last resort only | It is the last resort after one retry, not the first repair. |

## 16. Satisfaction-system analysis

`assess_contract_satisfaction` and `resolution_rank` currently act as validator, ranker, replacement trigger, and fallback trigger.

Recorded effects:

- C16 turn 1 and smoke turn 1: a real inability (`legitimate_nonresolution` / `valid_inability`, rank-class nonresolution) loses to a manner shell scored `inquiry_answered`.
- C16 turn 3: a false structural invalidity forces rank 0, so any stored topic at rank 4 wins.
- Smoke turn 10: the useful watcher line is `unrelated_fact` because the contract is stale; the scene line is `satisfied`. Rank selects the scene line (`higher_rank`).
- C16 turn 6: the only time rank moved the right direction (`lower_rank`, `target_loss`), and the grounding lock still emitted the worse line.

Satisfaction should become one question: does this candidate sufficiently resolve the authoritative contract, including a legitimate inability or refusal when that is a legal resolution. It should not choose which reconstructed sentence replaces which other sentence.

Those responsibilities should not stay combined. Ranking reconstructed candidates is what lets a shell outrank an answer.

## 17. best_safe_candidate analysis

`remember_satisfied_candidate` stores a line at rank 2 or higher. `select_preserved_answer` and `enforce_emitted_contract_monotonicity` emit that store when the current line is not allowed to replace it.

Original use: stop a later stage from degrading a good answer. Continuation 13 turn 2 showed the opposite bug, a better line stuck in the store and not emitted. Continuations 14–16 fixed emission fidelity. `best_safe` emission mismatches are 0 in C14, C15, C16, and the smoke.

The remaining defect is the update rule. The store accepts the first line that scores as safe, and that line is often already the shell, the Thoran sentence, the emergency pool, or the closer. Fidelity to a bad best is not preservation.

Future architecture should not run a candidate tournament. The first model candidate that is hard-valid, authority-safe, state-consistent, contract-satisfying, and interaction-complete becomes the emitted text. Later candidates are not generated for rank.

## 18. Fallback inventory

| Fallback | Invoked when | Hard-invalid condition? | New semantic content | Can change target | Speaker | Operation | Claims | Contradict state | Caused recorded degradation | Class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Leak substitution inside `guard_gm_output` | Secret pattern | YES | Minimal | No | No | No | Deletes | No | Not in these 16 | REQUIRED SAFE FALLBACK |
| Stay/leave stock line | Narration contradicts resolved move | YES | The structured fact only | Location | No | No | The move | It prevents a contradiction | Not in these 16 | REQUIRED SAFE FALLBACK |
| `generic_ask_completion` | Ask structurally invalid after other attempts | YES | A content-free inability | No | Uses the contract label | No | No | No | Not observed as the damaging line | REQUIRED SAFE FALLBACK, last resort |
| Mechanical one-liner from resolution fields | Narration contradicts HP, inventory, or movement, and retry failed | YES | Only fields already resolved | No | No | No | The mechanical result | It prevents one | Not in these 16 | REQUIRED SAFE FALLBACK |
| Perception / referenced-surface closer | Unsupported or mixed inspection | The invention is invalid. A true reading is not. | YES. "Nothing matches" / "nothing further" | Can drop the object detail | No | Can collapse to observe | Can deny a visible fact | YES, by denial | C16 turn 6, smoke turn 9 | REGENERATE-FIRST |
| Strict-social emergency pool | Social ownership or terminal miss | Sometimes | YES. Generic rumor line | No | YES. Uses `speaker_label`, which was "The guard" | No | "I have heard talk" | Can name the wrong NPC | C16 turn 5, smoke 1, 4, 5 | REGENERATE-FIRST. Current pool is HARMFUL as a first repair |
| `obligation_preserving_fallback_line` | Contract or obligation unsatisfied | Sometimes empty | YES | Can | YES | No | Can quote the player | Can | Smoke turn 3 | REGENERATE-FIRST. HARMFUL when it fills `{subject}` from player text |
| Authored-knowledge / clue-frame swap | Current line rank below the stored topic | Often a false rank | YES. A different fact | YES, topic | Can | No | States the topic as the answer | Can answer the wrong question | C13, C14, C16 turn 3 | REGENERATE-FIRST. HARMFUL as a topic swap |
| Referential-clarity replacement | Ambiguous entity | Often uncertain | YES. Scene fact | YES | YES | Can collapse ask to observe | Scene facts | Smoke turn 10 | HARMFUL / REDUNDANT on these turns |
| First-mention replacement | Missing grounding on a name | Uncertain | YES | Can | Can | No | Can | Smoke turn 7 tagged it; text unchanged | UNCLEAR on that turn. Do not let it author a stall |
| `run_generic_replace_exit` | Any gate reason | Mixed | YES | YES | YES | YES | YES | Can | Gate tags on smoke 7, 9, 10 | REGENERATE-FIRST |
| Scene-momentum / topic-pressure append | Momentum due | NO | YES | No | No | No | Atmosphere or a lead | Can | Tags on most smoke turns | LEGACY |
| Repeated-description guard | Same narration hash | NO | YES. "Nothing new" | No | No | No | Denies a repeat look | Can | Not the recorded failures | LEGACY |
| Destination-arrival template | Stub destination prose | Sometimes | YES | Scene | No | No | Arrival | Can | Not in these 16 | REGENERATE-FIRST |
| Deterministic retry fallback | Retry budget exhausted inside `gm_retry` | Mixed | YES | YES | YES | Can | YES | Can | 0 uses in these sessions | LEGACY relative to a single explicit retry plus `generic_ask_completion` |

Fifteen fallbacks were audited in the table above. Four are required safe last resorts: leak strip, the stay/leave fact, `generic_ask_completion`, and the mechanical one-liner (specified for a case these sessions did not hit). The other eleven should not run before a bounded regeneration.

## 19. Retry / regeneration analysis

`game/gm_retry.py` already has a retry loop and `MAX_TARGETED_RETRY_ATTEMPTS = 2`. Both recorded sessions show `retries: 0`. Substitution ran instead. The loop's failure classes include `unresolved_question`, `scene_stall`, `forbidden_generic_phrase`, and topic pressure. Several of those are quality triggers. A quality miss should not spend a retry, and it should not spend a fallback.

Proposed use, not implemented:

```text
model candidate
    -> hard validator
    -> valid: emit unchanged
    -> invalid: one regeneration
         same Resolution Contract
         same authoritative state
         the violation named in the retry instruction
    -> hard validator
    -> valid: emit
    -> invalid: generic_ask_completion or the mechanical one-liner
```

| Concern | Assessment |
| --- | --- |
| Architecture fit | The contract and the state snapshot already exist before generation. A second call does not need a new contract. |
| Token cost | These sessions used one generation per turn. A bound of one retry adds a call only on hard-invalid turns. On this sample that is 4 of 16, about one quarter more generation calls if every illegal line is retried once. The 12 legal lines add nothing. |
| Latency | One extra model round trip on the failure path only. |
| Determinism | The validator is deterministic. The retry text is not. The last resort is deterministic. |
| Retry-loop risk | Bound is 1. Not "until success." The existing constant of 2 should not be reused as an unbounded quality loop. |
| State integrity | No world mutation from either candidate until one candidate passes. See section 22. |
| Authority | The retry sees the same permissions and the same PR-BN classes. It does not get a wider invention budget. |

Bound: **1** regeneration. Then stop.

## 20. First-valid-response analysis

Rule under test: the first model candidate that is hard-valid, authority-safe, state-consistent, contract-satisfying, and interaction-complete is immutable player-visible content. Later machinery may record state, persist accepted facts, update discourse, and log telemetry. It may not rewrite that semantic content.

On this evidence the rule is **supported**.

Benefits: the seven downstream-created failures do not happen. Continuation 16 would have finished 6 / 6. The smoke would have finished 6 / 10, which is the initial-pass count, instead of 3 / 10. Token use on the success path stays one generation.

Risks:

- Four initials were hard-invalid. Emitting them would publish a wrong speaker (smoke 4 and 5), a "find the captain" stall (smoke 7), and a fake curfew hour (smoke 9). The rule does not emit those. That is why "first valid" is not "first model string."
- Stale contracts make "contract-satisfying" disagree with the player. Smoke turn 10's watcher answer failed the stale captain contract and was the right player answer. A hard interlocutor check must not reject a line that addresses the person the current player sentence just named, only because discourse inheritance kept the previous NPC. That fix is contract construction, and it is a precondition of the rule. Until it lands, a high-confidence speaker check should prefer the explicit current-turn addressee over an inherited slot.
- Quote stripping that drops clauses (C16 turn 4) would stop. The player keeps the fuller answer. That is the point.

## 21. Immutable-boundary analysis

Text becomes immutable when the hard validator accepts it.

Nothing after that acceptance needs to change semantic content. Legal post-acceptance work is bookkeeping: discourse slots, NPC-claim notes, bounded-detail promotion from that text, logs, and telemetry.

What currently changes text after a would-be acceptance, and why it should stop:

| Later writer | Why it exists | After immutability |
| --- | --- | --- |
| Strict-social rebuild | Force a dialogue shape | Off the critical path |
| Referenced-surface closer | Stop invented inspect detail | Becomes the validator's reject reason, not a new sentence |
| Authored-knowledge swap | Force a stored fact | Off, unless the retry itself is the model stating that fact |
| `select_preserved_answer` / monotonicity | Undo an earlier downgrade | Unnecessary if nothing later downgrades |
| Second grounding pass | Same checks again | Off |
| `apply_spoken_state_refinement_cash_out` | Append a lead | Off. If the lead is authoritative, it belongs in the contract before generation |
| Presentation whitespace and HTML strip | Packaging | Allowed, if it cannot drop words |

The boundary is **before** discourse commit, not after the current gate. The current gate is itself a rewriter.

## 22. State-commit ordering

Current order:

1. World tick at the start of `chat`.
2. On the resolved path, `_apply_authoritative_resolution_state_mutation` before generation.
3. Model and rewriters.
4. End of `_finalize_player_facing_for_turn`: `commit_discourse_focus` and `note_emitted_npc_claim`.
5. Second grounding pass and `enforce_emitted_contract_monotonicity`, which can still change `player_facing_text`.
6. `_apply_post_gm_updates`: bounded promotion, another claim note, refinement append.
7. Save and log.

A preserve-if-valid path has to use this order:

1. Interpret and build the contract. Do not commit discourse from a rejected reading.
2. Apply mechanical and movement mutations that the engine has already resolved. Those are not derived from narration.
3. Generate.
4. Hard-validate. If invalid, retry once against the same pre-narration state. Do not promote facts from the rejected text.
5. On acceptance, the text is immutable.
6. Then, from that text only: discourse commit, NPC-claim notes (claims, not world truth), bounded-detail promotion for proposals that were accepted on this text.
7. Emit and persist.

Rejected text must not commit discourse, must not record a claim, and must not promote a detail. Emitted text must be the text those commits describe. Today's steps 5 and 6 can break that pairing.

## 23. PR-BN persistence implications

The recommendation keeps PR-BN.

Bounded incidental invention in an accepted narration still promotes through `promote_accepted_bounded_improvisation`, and only after the line is the immutable accepted line. A rejected candidate does not promote.

An NPC sentence remains an attributable claim through `note_emitted_npc_claim`. It does not become world truth because it was spoken. Smoke turns 6 and 8 are the pattern to preserve: the captain's toll policy stays in the captain's mouth. The smoke left `active_claim` empty; the future path should record that claim from the emitted line and still not write it as a scene fact.

Consequential narrator inventions (a posted hour, a new toll amount stated as law, a route the engine did not resolve) stay hard-invalid. They are not promoted and they are not emitted.

## 24. Mechanical-action implications

Social and inspect turns are most of the recorded damage. Mechanical turns need a tighter version of the same split.

The engine owns the result: attack roll, damage, HP, inventory transfer, movement, spell expenditure. `_apply_authoritative_resolution_state_mutation` already runs before narration on the resolved path. That order stays.

The model owns the telling of that result. Preserve the telling when it does not contradict the structured result. Reject it when it does (wrong creature wounded, item gained that was not transferred, move narrated when the resolver stayed put). One retry receives the structured result in the instruction. If the retry still contradicts, emit a short line built from the structured fields. That line states the result. It does not reconstruct motive, dialogue, or a clue.

Stay/leave agreement is this pattern already, restricted to location. It remains as the last resort for location, not as a general prose rewriter.

## 25. Generation versus resolution ownership

| Question | Owner |
| --- | --- |
| What happened? | Deterministic engine: canonical state, mechanics, permissions, authoritative action result, Resolution Contract, PR-BN class of any new detail. |
| How is it narrated? | The model: dialogue, description, connective tissue, the wording of an inability. |

The current architecture crosses that split. After a legal narration exists, `apply_authored_knowledge_realization_to_gm`, the strict-social rebuild, the referenced-surface renderer, the obligation fallback, and the emergency pool decide the words, and sometimes the speaker and the topic. Those wording decisions are the seven downstream-created failures.

## 26. Deterministic versus semantic validation boundary

Deterministic enough to reject without guessing:

- Empty response, truncated JSON, unclosed payload scaffold.
- Secret or hidden-fact pattern.
- Impossible canonical id.
- Structured mechanical mismatch (HP, inventory, location, alive/dead) against the resolution record.
- Player-utterance window embedded in the NPC line (`player_utterance_embedded`).
- Attribution shell: an attribution verb and a manner tail, and no proposition (`attribution_shell`).
- Explicit locate sentence whose object is the current addressee, when the locate verb and the addressee are in the same clause. The current `_LOCATE_RE` plus "label words appear anywhere" test is not this check.

Semantic, and not safe as a lexical reject:

- Did this NPC really answer?
- Does "find the specifics" mean "find the captain"?
- Is the narration responsive enough?
- Is the prose too thin, too rich, or off in tone?
- Is an NPC's quoted policy "true"?

Deterministic code owns the first list. The model owns the wording that the second list worries about. If a semantic doubt remains, preserve a line that already passed the deterministic list, or regenerate once. Do not resolve the doubt by writing a new sentence in Python.

## 27. Validator-confidence policy

Reject only high-confidence hard violations.

| Confidence | Examples | Action |
| --- | --- | --- |
| High | Empty, leak, mechanical mismatch, dead/alive, player-text splice, shell with no proposition, same-clause "go find {current addressee}", narrator number or clock time that is not in authored state | Reject. One retry. Then safe nonresolution. |
| Low or lexical coincidence | `find` anywhere plus the speaker's name elsewhere in the paragraph; a name that does not use the "Name says" frame; a quoted claim whose truth is unknown | Do not reject. Do not replace. |
| Contract disagrees with the current sentence's explicit addressee | Smoke turns 4, 6, and 10 | Fix the contract from the current sentence before judging the model. Do not "repair" the prose into the stale NPC. |

Uncertain semantic judgments preserve the candidate when the deterministic checks passed. They do not clarify in the player's face unless the contract itself is `ambiguous` and no interlocutor was bound. They do not call a second model to judge the first in this design.

## 28. Model-assisted validation option

A structured judge model could score "did this answer the contract?" That option is **not** recommended.

| Issue | Assessment |
| --- | --- |
| Token cost | One extra call on every turn, including the 12 that were already valid. Larger than one retry on 4 of 16. |
| Latency | Always on the success path. |
| Reliability | The local evaluator already false-passed 3 of 6 C16 finals and 5 of 10 smoke finals. A model judge has the same kind of miss available to it. |
| Circularity | The generator judging itself will prefer its own wording. A different model reintroduces an evaluator. |
| Evaluator leakage | Runtime rejection by a judge becomes another rewrite trigger. |
| State authority | A judge must not be allowed to declare a new fact legal. State legality is already a deterministic question. |
| Better encoding | Put the contract, the visible facts, and the mechanical result in the generation prompt. Validate the result with the deterministic list. Do not add a judge. |

No live call was made to test this. The recommendation does not depend on one.

## 29. Telemetry role

Degradation telemetry should be observability and QA. It should not choose the player-visible line.

C16: telemetry degradations 1, manual degradations 4. The three misses are structural: a quoted manner sentence is not classified as a shell; a line already marked invalid is not a "loss" when replaced; a speaker change without a "Name says" frame is invisible.

Smoke: telemetry 0, manual 6. The detector compared a damaged initial store with a damaged final and saw equal rank.

A detector can be useful in QA at partial coverage. It is dangerous as a runtime switch. `detect_semantic_degradation` does not currently select the line. It must stay that way. Satisfaction rank, which does select the line, should lose that authority.

## 30. Evaluator role

`evaluate_playability` is local. Evaluator-model calls in both sessions: 0.

| Session | Evaluator | Manual final |
| --- | --- | --- |
| Smoke | 8 / 10 | 3 / 10 |
| C16 | 4 / 6 (turns 1, 2, 3, 5) | 2 / 6 (turns 2 and 4) |

C16 false PASS: turns 1, 3, 5. False FAIL: turn 4. Smoke false PASS: turns 3, 4, 7, 9, 10. False FAIL: 0.

The evaluator is not trustworthy for runtime selection. Keep it as offline test assistance. This cycle does not redesign it.

## 31. Token and cost comparison

Recorded calls, no new API calls. Route noted in the C16 audit: `gpt-4.1-mini`. No dollar ledger is stored on these artifacts. Comparison is call counts.

| Architecture | Generation calls on these 16 turns | Extra calls | When the extra call happens |
| --- | --- | --- | --- |
| A. Current pipeline | 16 gameplay generations (C16: 6, smoke: 10) plus 1 opening on the smoke. Retries 0. Interpretation 2 + 3. | 0 beyond today | Rewrites are CPU, and they caused 7 failed finals |
| B. Smaller rewrite set | Same 16, plus rewrites that remain | 0 | Still pays the quality cost of whatever rewrites remain |
| C. Preserve-first + one retry | 16 on the success path, plus up to 4 retries for the hard-invalid initials | ≤ 4 generation calls on this sample (~25% more generations if all four retry) | Only after a high-confidence reject |
| D. Model-assisted judge | 16 + 16 judge calls | +16 | Every turn, including legal ones |

Option C is the cheap failure path. Option D taxes the success path. Option A is the same generation cost as today's success path and the worst final-pass rate.

## 32. Failure-containment strategy

If generation is hard-invalid and the single retry is hard-invalid, the player receives one of these, chosen from the contract operation, with no new topic and no player-text splice:

| Situation | Last resort |
| --- | --- |
| Ask or social | `generic_ask_completion`: `{Contract label} says, "I cannot answer that from what is settled here."` If no label: `No one here can answer that from what is settled here.` |
| Inspect | The authored visible-fact sentence for that object, without "Nothing here matches" and without "Closer looking yields nothing further." If there is no authored fact: `The inspection establishes no further reliable detail from the current scene.` |
| Mechanical contradiction | One sentence from the structured result (the HP, the item, the location). |
| Ambiguous referent, no bound interlocutor | One clarification question. Do not pick an NPC and answer as them. |
| Secret leak that both attempts repeat | The leak-stripped text, or the ask nonresolution if stripping leaves a shell. |

These lines do not name a different authored topic, do not quote the player, and do not change speaker away from the contract label. That is the difference between `generic_ask_completion` and the emergency pool that produced "The guard shakes their head."

## 33. Minimum trusted post-generation core

Only these mechanisms need authority over generated output:

1. Schema and non-emptiness. Reject shells and player-text splices.
2. Secret and hidden-information strip.
3. Canonical-state check against structured records (entity exists, alive/dead, location, inventory).
4. Mechanical-result check against the resolution record.
5. High-confidence interlocutor contradiction, using the current-turn addressee when the player named one.
6. High-confidence same-clause "go find the person you are talking to."
7. Narrator-voice consequential invention (a new clock time, price, or law stated as scene fact rather than as an NPC claim).
8. Contract-satisfaction check as a yes/no, including legitimate inability.
9. One bounded regeneration on failure, under the same contract.
10. The last-resort lines in section 32.
11. Emission of the accepted line unchanged.
12. Discourse, claim, and PR-BN promotion from that line only.

## 34. Mechanisms proposed for removal from the critical path

| Mechanism | Future role |
| --- | --- |
| `best_safe` tournament and `select_preserved_answer` | Delete from the emission path. A debug log of rejected candidates is enough. |
| Satisfaction rank as a chooser | Yes/no contract check, QA log |
| `detect_semantic_degradation` | QA log |
| `evaluate_playability` | Offline tests |
| Strict-social sentence rebuild and the emergency pool | Prompt constraint on speaker. Not a rewriter. |
| Authored-knowledge topic swap | Contract context before generation, when the question asked that topic |
| Referenced-surface stock closers | Reject reason, not a new paragraph |
| `obligation_preserving_fallback_line` | Replaced by `generic_ask_completion` as last resort |
| Scene-momentum, passive escalation, topic-pressure append | Prompt context if wanted later. Not an append. |
| `final_validation_pass` semantic rewrites and `_simple_diegetic_fallback` | Off the path. Packaging strip may stay. |
| Second post-finalize grounding pass | Off |
| `apply_spoken_state_refinement_cash_out` | Off. Leads belong in the contract or the log. |
| Answer-shape, tone, authenticity, and anti-railroading repairs | Offline or prompt. Not runtime replacement. |
| Repeated-description full-text replacement | Log, or a duplicate-hash note. Do not substitute "nothing new" for a legal repeat look. |

## 35. Architecture Option A — current candidate-transformation pipeline

**Description.** Generate once. Run policy repair, authored-knowledge realization, perception grounding, the final-emission gate, strict-social rebuild, obligation fallbacks, satisfaction ranking, and `best_safe`. Emit the winner.

**Strengths.** Rich regression suite (350 tests on the C16 band). Many historical hallucinations are blocked in fixtures. Preservation guards exist.

**Weaknesses.** On the 16 real turns, final manual pass is 5 / 16 against an initial 12 / 16. Zero downstream-prevented failures. Seven created failures. The guards preserve the substitute. Telemetry and the evaluator miss the damage. Retries are implemented and unused.

**Historical evidence.** C13 5→2, C14 6→4, smoke 6→3, C16 6→2. C15 focused 4→4 did not generalize.

**Complexity.** The highest. Thirty-five post-generation mechanisms, two grounding passes, rank, and a tournament.

**Token cost.** One generation per turn in these sessions, plus interpretation on abstention. The quality cost is the rewrites.

## 36. Architecture Option B — reduced transformation set

**Description.** Keep a shorter list of rewriters: grounding closers, a smaller social fallback pool, and authored-fact insertion. Remove scene-momentum append and the tournament.

**Strengths.** Less machinery. Familiar to the current tests.

**Weaknesses.** The damaging mechanisms are the ones this option is tempted to keep. C16 turns 1, 3, 5, and 6 and smoke turns 1, 3, 9, and 10 are exactly grounding, social fallback, and authored-fact insertion. A smaller rewrite set that still writes sentences will keep the failure mode. The false-positive locate check still feeds them.

**Historical evidence.** Each continuation that added a narrower repair (C14 preservation, C15 coverage, C16 structural completion) left the same live families in place.

**Complexity.** Still a rewrite pipeline, with a shorter registry.

**Token cost.** Same as A. No retry.

## 37. Architecture Option C — preserve-first, hard validation, one retry

**Description.**

```text
PLAYER INPUT
    |
    v
SEMANTIC INTERPRETATION
    |
    v
AUTHORITATIVE RESOLUTION CONTRACT
(current-turn addressee overrides a stale inherited interlocutor)
    |
    v
STATE / AUTHORITY / MECHANICAL CONTEXT
    |
    v
MODEL GENERATION
    |
    v
HARD VALIDATION
    |
    +---- VALID ----------------------+
    |                                 |
    |                                 v
    |                         IMMUTABLE RESPONSE
    |                                 |
    |                                 v
    |                    DISCOURSE / CLAIM / PR-BN COMMIT
    |                                 |
    |                                 v
    |                              EMISSION
    |
    +---- INVALID (high confidence only)
                  |
                  v
             ONE RETRY, SAME CONTRACT,
             VIOLATION NAMED
                  |
                  v
             HARD VALIDATION
                  |
          +-------+-------+
          |               |
        VALID           INVALID
          |               |
          v               v
       EMIT        SAFE NONRESOLUTION
                  (section 32)
                  then commit and emit
```

**Strengths.** Matches the scorecard: 12 / 16 preserved, 4 / 16 rejected instead of published, 0 reliance on a rewriter to invent the repair. PR-BN promotion and NPC claims attach to the accepted line only. Mechanical results stay engine-owned. Token cost rises only on the failure path.

**Weaknesses.** The four hard-invalid turns do not become passes unless the retry succeeds. That is unknown without a future live run, and this cycle does not run one. Stale discourse must be fixed in contract construction or the validator will judge the model against the wrong NPC. Existing tests encode stock sentences ("Closer looking yields nothing further", Thoran realization, emergency pool lines). Those tests will need to expect rejection-or-retry rather than the stock sentence. That is an implementation-cycle cost, not a reason to keep the stock sentence on the success path.

**Historical evidence.** The seven created failures are cases the model had already solved. The four hard-invalid initials are the cases a validator must still catch, and the current substitutes did not turn them into passes. Smoke turn 9 shows the one real save (the fake hour was not shown) and shows that the save can be a reject without a closer.

**Complexity.** Lower on the success path: generate, validate, commit, emit. The retry and the four last-resort templates are the whole failure path.

**Token cost.** 16 generations plus at most 4 retries on this sample. No judge model.

## 38. Evidence-backed recommendation

**Option C.**

| Piece | Choice |
| --- | --- |
| Response lifecycle | Interpret → contract → state context → generate → hard-validate → emit if valid, else one retry, else section-32 nonresolution. |
| Hard validators | Section 33 items 1–7. |
| Soft validators | Tone, richness, atmosphere, "could be more specific," equal-rank topic preference. Log only. Never replace. |
| Retry | One. Same contract. Violation named. Not until success. |
| Fallback | Section 32 only, after the retry fails. No topic swap, no emergency rumor pool, no player-text subject. |
| Immutable boundary | The moment hard validation accepts the text. Before discourse commit. |
| State-commit ordering | Section 22. |
| Telemetry | QA only. |
| Evaluator | Offline only. |

This is not "trust the LLM." The engine still owns entities, world state, HP, inventory, location, death, discovered facts, hidden information, permissions, PR-BN classes, consequential inventions, the claim/truth split, persistence, promotion, mechanics, action legality, and state mutation. It stops owning the wording of a response that already respects those constraints.

## 39. Proposed next implementation cycle

PR-BR Continuation 18, still inside open PR-BR. Do not open PR-BS.

Implement the immutability boundary:

- Hard-valid model text is emitted unchanged.
- The locate check requires the locate verb and the addressee in the same clause.
- Current-turn explicit addressee overrides inherited discourse before the model is judged.
- Authored-knowledge swap, strict-social rebuild, referenced-surface closers, obligation-subject fallback, scene-pressure append, and `best_safe` selection leave the emission path.
- One retry, then `generic_ask_completion` or the mechanical one-liner.
- Discourse, claims, and PR-BN promotion run on the accepted line only.
- Update the deterministic tests that currently require the stock closer or the emergency pool as the emitted line. Assert rejection or the last-resort line instead.

Do not run an independent smoke, the six live turns, or the 4×10 gate in that cycle until the deterministic band shows a hard-valid fixture emitted byte-for-byte. Human playtest stays unauthorized until a later validation cycle says otherwise.

## 40. PR-BR status

PR-BR: **STILL OPEN.**

No completion commit. No push. No PR-BS. No gameplay behavior change. Gameplay-generation calls: 0. Interpretation calls: 0. Synthetic-player calls: 0. Evaluator-model calls: 0. Independent smoke: not run. Full synthetic gate: not run. Human playtest: **NOT AUTHORIZED.**

READY FOR IMPLEMENTATION OF OPTION C: YES, as Continuation 18. This document does not implement it.

# PR-BR Continuation 18 — Immutable Valid Response Boundary & Bounded Regeneration

HEAD remains `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. Continuation 18 is uncommitted work on that commit. Live session `artifacts/pr_br_continuation18/20261001T225126Z`.

## 1. C17 implementation basis

C17 measured 16 recorded turns. Initial manual PASS was 12/16. Final manual PASS was 5/16. Preserve-if-hard-valid would have kept 12/16. Four initials were genuinely hard-invalid. Seven failures were created downstream. Zero failures were prevented downstream. Continuation 18 implements that recommendation: hard-validate, preserve a valid response, regenerate once if it is hard-invalid, otherwise emit a minimal safe nonresolution.

## 2. Previous vs new response lifecycle

Previously, generation was followed by a candidate tournament. Satisfaction rank, `best_safe_candidate`, closers, and scene-pressure lines could replace a valid answer.

The contract-bearing narration path is now:

generate → hard-validate → if valid, seal the text → commit effects from that text → emit it.

If hard-invalid: one regeneration under the same contract → hard-validate → seal and emit, or emit the safe line. Scene openings and turns with no contract operation stay on the legacy path. A zero retry budget (`MAX_TARGETED_RETRY_ATTEMPTS == 0`) skips regeneration and goes to the safe line.

## 3. Hard-validation implementation

`game/immutable_valid_response.py` `validate_generated_response` rejects, with high confidence only: malformed or truncated output, secret leaks, the player-splice template, an ASK attribution shell, a passive observation standing in for an ASK, a smell/wear/sound/taste question that neither names the sense nor states an inability, meta validator voice (`based on what's established`, `we can determine`, model identity), a confidently wrong speaker, same-clause locate of the current addressee, an unauthored clock outside quotes, a mechanical success/failure contradiction, a dead actor speaking, and scene-backed unsupported perception invention.

## 4. Hard vs soft validation

Soft flags do not replace text. Bland or awkward prose, a partial echo of the player, a valid inability, and the old anywhere-match locate cue (`low_confidence_locate`, including C16 turn 3) stay soft. "I do not know" is a valid inability, not meta voice.

## 5. Accepted-response representation

A sealed turn stores `gm.metadata.accepted_response`: contract id, player input, text, speaker, addressee, target, operation, hard-validation result, interaction completion, attempt number, and provenance (`initial_generation`, `regeneration`, or `safe_nonresolution`). `immutable` is true.

## 6. Immutable boundary

After the seal, policy enforcement, authored-knowledge realization, stay/leave and destination realization, perception non-invention, the repeated-description substitute, the final emission gate, contract monotonicity, and spoken-state refinement return the accepted text. `restore_accepted_text` runs again before discourse and claim commit and records an equality report.

## 7. Post-acceptance allowed transformations

`normalize_presentation` collapses whitespace and strips simple `b/i/em/strong/br/p` tags. JSON transport escaping is unchanged. Any other difference is written back to the accepted sentence and marked `mutation_blocked`.

## 8. best_safe migration

`enforce_emitted_contract_monotonicity` may still compute `legacy_would_emit` for diagnostics. It does not assign that text when the response is immutable.

## 9. Satisfaction migration

Satisfaction is not a search for a better sentence. Hard validation answers whether the line may be emitted. `assess_contract_satisfaction` is not a reject: on the 16 recorded initials it marks preserve-cases unsatisfied (smoke 2, 6, and 10). Using it as a hard gate would have destroyed valid lines.

## 10. Old mutator migration

Forty mechanisms are classified. None are ambiguous.

| Status | Count |
| --- | --- |
| REMOVED FROM CRITICAL PATH | 20 |
| RETAINED AS OBSERVABILITY | 7 |
| RETAINED AS PRESENTATION-ONLY | 4 |
| STILL REQUIRED FOR STATE/MECHANICS | 4 |
| RETAINED AS HARD VALIDATOR | 3 |
| RETAINED AS LAST-RESORT SAFE NONRESOLUTION | 2 |

`guard_gm_output` still runs before the seal. That is containment, not a post-acceptance rewrite.

## 11. Initial-valid path

Attempt 1 hard-valid → seal `initial_generation` → skip the quality retry loop → emit the same string. Stub case C asserts one generation call.

## 12. One-retry path

`MAX_GENERATION_ATTEMPTS` is 2. A hard-invalid attempt 1 is marked rejected and is not the commit source. Attempt 2 uses the same contract, state, mechanic, operation, and interlocutor. Stub case A emits attempt 2 unchanged.

## 13. Retry feedback

The retry user message names reason codes only. It does not include the rejected sentence or a replacement sentence. Live feedback on turns 4 and 6 was `consequential_invention`.

## 14. Double-invalid path

If attempt 2 is also hard-invalid, provenance is `safe_nonresolution`, `retry_exhausted` is set, and there is no third gameplay generation. Stub case B covers this.

## 15. Safe nonresolution design

The line is one of: a dimension-specific inspection limit, the mechanical failure sentence, an authored visible fact, an action-incomplete sentence, one clarification question, or `generic_ask_completion`. If that line would repeat the player's utterance, it falls back to "No one here can answer that from what is settled here." It does not invent a posted fact, a clue, or a new speaker.

## 16. State-commit ordering

Engine mechanics still resolve before narration. Rejected candidates do not promote bounded proposals. `effects_allowed` is false for provenance `rejected` and for a text mismatch. Safe provenance strips improvisation proposals before the seal.

## 17. Discourse-commit ordering

`commit_discourse_focus` and `note_emitted_npc_claim` use `commit_text`, which is the accepted sentence.

## 18. Bounded invention persistence

Stub: attempt 1's incidental detail is rejected and does not persist. Attempt 2's different detail does.

## 19. NPC-claim persistence

Stub: a rejected attempt-1 rumor does not become an active claim. Only the accepted attempt is recorded.

## 20. Mechanical authority

Narration that says success when the mechanic says failure is hard-invalid and regenerates. The mechanic is not edited to match the prose. The matching failure narration is accepted unchanged.

## 21. Validator-confidence handling

Low-confidence locate is a soft flag. C16 turn 3 stays hard-valid. An unexpectedly phrased but valid line is not replaced.

## 22. 16-turn replay

`test_sixteen_turn_counterfactual_classifies_c17_boundary` loads the six C16 turns and the ten failed-smoke turns.

| Result | Count |
| --- | --- |
| Recorded turns | 16 |
| Initial hard-valid, preserved unchanged | 12 / 12 eligible |
| Hard-invalid, sent to regeneration | 4 / 4 |
| Downstream-created failures remaining | 0 |
| Accepted-response mutations | 0 |
| Regeneration of a hard-valid line | 0 |

## 23. Seven downstream-created failures

C16 turns 1, 3, 5, and 6, and smoke turns 1, 3, and 10, are hard-valid. Their recorded finals differ from the initials. The new path seals the initial and keeps it through monotonicity, authored-knowledge realization, perception non-invention, and the final emission gate. 7 / 7 eliminated.

## 24. Four hard-invalid initial responses

Smoke 4, 5, 7, and 9 stay blocked. Smoke 7 uses same-clause locate, not the old anywhere-match. Smoke 9's unauthored clock stays `consequential_invention`. 4 / 4 blocked.

## 25. Historical hard-invalid regressions

Authority leak, a dead actor speaking, malformed truncation, mechanical contradiction, and unauthored clock phrasing stay blocked.

## 26. Stub integration

Cases A, B, and C pass. The raw `/api/chat` stub preserves a valid runner price line and does not emit a wrong-speaker guard answer, the closer, or the emergency pool.

## 27. Focused deterministic results

Continuation 18's own file passed. A later combined run of Continuations 14–16 and 18, the resolution-contract suite, bounded improvisation, perception audible non-invention, transcript regression, and empty-social retry passed: 183 passed, 0 failed.

## 28. Broader regression result

Continuations 12–16, outcome precedence, bounded improvisation, the resolution contract, transcript regression, and empty-social retry passed together: 189 passed, 0 failed. The full repository suite was not run. Two product-path tests that required a hard-valid atmosphere line to be rewritten into "the tattered man" now expect that line to be preserved. Direct gate calls without an observe contract also no longer invent that approach. `question_resolution_rule_check` no longer treats a cinematic interruption as satisfied just because a loose contract assessment returned partial.

## 29. Focused live transcript

One isolated session, six completed turns, stamp `20261001T225126Z`. Natural wording, not the Continuation 16 strings. No repair and no rerun.

| Turn | Player | Provenance | Exact |
| --- | --- | --- | --- |
| 1 | Ask the tavern runner whether east-lane carts are still coming through. | initial | yes |
| 2 | Who told him that? | initial | yes |
| 3 | Leave the runner and ask the nearest guard about passage. | initial | yes |
| 4 | Read the newest notice-board posting. | regeneration | yes |
| 5 | Return to the runner with a coin and ask about the patrol. | initial | yes |
| 6 | Stay and watch the road. | regeneration | yes |

Turn 4 attempt 1 posted an unauthored "indoors by the third bell" and was rejected for `consequential_invention`. Attempt 2 states taxes, curfew rules, and the missing patrol, and was sealed. Turn 6 attempt 1 invented scent and footprints and was rejected for the same reason. Attempt 2 was sealed. Neither rejection was emitted.

## 30. Accepted-vs-emitted equality

6 / 6 exact matches. Presentation-only differences: 0. Accepted-response semantic mutations: 0. Generation attempts above two: 0.

## 31. Retry observations

Regenerations invoked: 2. Both succeeded on attempt 2. Double-invalid safe nonresolutions: 0. No third generation.

## 32. Initial vs final manual quality

Manual reading of the six finals:

| Turn | Initial manual | Final manual | Note |
| --- | --- | --- | --- |
| 1 | PASS | PASS | Inability plus an NPC-attributed rumor. |
| 2 | PASS | PASS | Inability to name a source. |
| 3 | FAIL | FAIL | Guard states an unauthored "third bell" closing as fact. Hard validation did not catch a clock inside dialogue. |
| 4 | FAIL | PASS | Posted "third bell" was rejected; the retry stays on the authored board. |
| 5 | PASS | PASS | Hedged NPC rumor about the muddy northwest track. |
| 6 | FAIL | PASS | Invented scent was rejected; the retry is a watch with no new patrol sign. |

Initial manual PASS 3 / 6. Final manual PASS 5 / 6. Correct contracts 4 / 6: turns 2 and 3 are the misses. Turn 2's canonical target is a slice of the previous answer. Turn 3's operation is `act` for a question, though the interlocutor correctly became the gate guard.

## 33. Evaluator vs manual

`evaluate_playability` is local. Evaluator model calls: 0. Evaluator PASS 2 / 6 (turns 2 and 4). False PASS: 0. False FAIL: 3 (turns 1, 5, and 6), against the manual reading above. Turn 3 is a true FAIL.

## 34. Legacy diagnostic comparison

Where recorded, `legacy_would_emit` matches the accepted line. No legacy mutator replaced an accepted response. Skipped mutators on every live turn include policy enforcement, authored-knowledge realization, perception non-invention, the final emission gate, and contract monotonicity.

## 35. Model and API cost

Gameplay-generation calls: 8 (six initials plus two regenerations). Interpretation calls: 2. Evaluator model calls: 0. Retry calls: 2. Aborted turns: 0. Independent smoke: not run. Full synthetic gate: not run.

## 36. Residual failure families

- A clock inside NPC dialogue ("third bell") is not the narrator-outside-quotes check, so turn 3 reached the player.
- Follow-up contract targets can become the previous sentence instead of the interlocutor.
- An accepted NPC rumor can name an unauthored institution ("ash compact census") or role ("gate serjeant") without becoming hard-invalid.
- The local evaluator still fails hedged but usable answers.

## 37. State-integrity findings

Rejected attempt text did not become the emitted line. Turn 4's "third bell" does not appear after the retry. Turn 6's invented scent does not appear in the sealed line. No rejected-response world or discourse commit was observed on the emitted path. No state-integrity failure stopped the session.

## 38. Readiness recommendation

READY FOR ANOTHER INDEPENDENT 10-TURN SMOKE: **YES.** The 16-turn replay preserves the 12 hard-valid lines, the seven downstream failures stay eliminated, the four hard-invalid initials stay blocked, immutability held on all six live turns, commit ordering held in the stubs, the retry cap held, and no accepted line was rewritten. The smoke should watch the residual families in section 36. It was not run in this cycle.

READY FOR FULL SYNTHETIC GATE: **NO.**

## 39. PR-BR status

PR-BR: **STILL OPEN.**

No completion commit. No push. PR-BS was not started. Human playtest: **NOT AUTHORIZED.** Semantic repair/rerun: no.

# PR-BR Continuation 19 — Hard-Authority Boundary & Contract Canonicalization Closeout

HEAD `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`, uncommitted. C18's lifecycle is unchanged: generate, hard-validate, seal and emit when valid, one bounded regeneration when hard-invalid, then a minimal safe nonresolution. No post-generation rewrite, candidate tournament, best-safe emission authority, or deterministic answer reconstruction was restored.

## 1. C18 residual findings

C18 sealed an unauthored gate schedule inside guard dialogue ("the watch changes at the third bell") because the narrator clock check ignores quoted speech and does not treat an ordinal bell as a clock. The source follow-up "Who told him that?" stored a slice of the previous response as the target text. Two social questions were accepted as `act` after the model interpreter proposed `act`.

## 2. C18 immutable architecture retained

Yes. `run_preserve_if_valid` still seals a hard-valid response, retries once, and emits the safe line only after both attempts fail. Accepted text is restored before emission. The Continuation 18 regressions passed inside the 267-test band below.

## 3. PR-BN authority integration

`game/proposition_authority.py` reuses PR-BN kinds from `game/bounded_improvisation.py`: `incidental_fact`, `npc_claim`, and `consequential_proposal`, plus `authoritative_fact` when an operational sentence is already in the authored corpus. Epistemic frames are world-truth, grounded, hearsay, rumor, and uncertain. Official levies proposed as incidental facts are rejected by `content:official_levy`.

## 4. Proposition authority design

Sentences are classified by family and by how the sentence presents them. A hedge, a hearing, or a rumor is an NPC claim. A bare operational assertion is world-truth. World-truth that the authored corpus does not already establish is `consequential_proposal` and hard-invalid (`ungrounded_authoritative_rule`). The response is rejected whole. It is not edited into a rumor.

## 5. Authoritative operational-rule handling

The family is structural: a closing, barring, watch change, or "be indoors" together with a definite time; a deontic credential; an official levy with an amount; or a standing legal mandate. "Curfew rules" on a posted notice, without a closing verb or an indoors-by-time clause, is not itself a new schedule. Retry feedback names `ungrounded_authoritative_rule` and tells the model to answer again without establishing unsupported authoritative facts. It does not prescribe a replacement fact.

## 6. Grounded-rule handling

If the authored corpus already contains the schedule anchor and an institutional closing or curfew, the same assertion is `authoritative_fact` and can be hard-valid. A coarse "until morning" in the same response is grounded when a specific anchor in that response is already in the corpus.

## 7. NPC-claim handling

"I heard they may close the gate around the third bell tonight" is hearsay or rumor, kind `npc_claim`, and is not an unauthorized world rule. Permission wording ("only guild members may enter") is not treated as uncertainty. Bare "may" is not a hedge. "May be" is.

## 8. Bounded-incidental handling

Food, clothing, weather, and ordinary gesture stay `incidental_fact` when they do not state an operational rule. A vendor bowl price stays improvisable. The C13 inspection that reports posted taxes and curfew rules without a new closing time remains acceptable.

## 9. Consequential-fact handling

Ungrounded world-truth schedules, access credentials, official levy amounts, and standing legal mandates are `consequential_proposal`. Mechanical results, including a referential "place your foot on the worn step" outcome, stay hard-invalid as consequential invention. Social `ask` turns are not rejected as unsupported perception.

## 10. Price authority

Official toll, tax, duty, or levy amounts are `official`. A tavern bowl, an estimated street price, and a hedged merchant figure without an official levy word are mundane. "The toll is not fixed" is not an official levy. "The toll is two silver" is.

## 11. Temporal authority

"In a few minutes" is incidental. An institutional close, watch change, or indoors requirement tied to a bell, a clock, dusk, dawn, sunset, or "until morning" is a schedule. A posted "curfew rules" line without that pairing is not.

## 12. Access authority

"You need papers," "only guild members may enter," and the same shape with a credential are access rules. They are hard-valid only when that credential is already in the authored corpus. Otherwise they are unauthorized world-truth.

## 13. Rejection and regeneration

Unauthorized propositions reject the whole response. `MAX_GENERATION_ATTEMPTS` remains 2. The retry note is the ungrounded-rule feedback. No sentence is deleted or rewritten in place.

## 14. Rejected-proposition persistence

A rejected schedule is not `commit_text`. The stub path asserts the rejected third-bell sentence is absent from the committed text and from later visible facts.

## 15. Accepted-claim persistence

An accepted rumor persists as an NPC claim with hearsay, rumor, or uncertain status. It is not copied into visible facts as world truth. Inability lines and bare "told me" source replies are not new claims.

## 16. Source-follow-up canonicalization

With an active claim present, "Who told you that?", "Where did she hear that?", "What's your source?", "Did the guard tell him that?", and "Who says?" bind dimension `source` and the claim id. The live turn 2 had no active claim, because turn 1 was an inability, and the stored dimension stayed `content`. See section 31.

## 17. Claim-reference representation

A short claim label stays readable. A clause-sized label is stored as the claim id (`claim_target_identity`). The previous response string is not the entity target when a claim id exists.

## 18. ASK/ACT classification repair

A model proposal of `act` on a clear question is canonicalized to `ask` when the terminal operation is ask and an interlocutor is bound. "Open" counts as an act only in "open the/a/an/it/that/this/up". "Pay," "hand," "push," and "give" are acts only when the utterance is not a question.

## 19. Fast-path competence

The fast path still canonicalizes or abstains. A genuine physical act whose object is not a catalog entity stays `act` instead of collapsing to unresolved. A named person the catalog does not contain is not invented.

## 20. Structured-interpreter behavior

The interpreter may propose. Deterministic validation still canonicalizes. On the live source follow-up the interpreter returned dimensions `content` and `source` with `referenced_claim_id` null. The stored contract kept `content`.

## 21. C18 six-turn replay

All six Continuation 18 live turns were replayed offline. Turn 3's initial third-bell schedule is hard-invalid (`ungrounded_authoritative_rule`). Turns 1, 2, and 5 stay hard-valid. Turn 4's initial "indoors by the third bell" posting stays hard-invalid. Turn 2's target is the claim id `emitted_85a7ac5156`, not the long census sentence. The model `act` proposal on turn 3's question canonicalizes to `ask`.

## 22. Third-bell regression

PASS. The unauthored "watch changes at third bell / gates close until morning" response is hard-invalid, retries once, and the feedback does not contain "third bell" or the rejected sentence.

## 23. Grounded control

PASS. The same closing is hard-valid when the corpus establishes that the gate closes at the third bell, and it is emitted unchanged.

## 24. Rumor control

PASS. The hedged hearing is a valid NPC claim and is not written into visible facts.

## 25. Bounded-detail controls

PASS. A stew, cloak, and gesture response stays hard-valid.

## 26. Authority variant results

PASS in `test_price_temporal_and_access_families_follow_pr_bn`: grounded versus ungrounded schedule, access, and levy; rumor versus world-truth; mundane bowl price versus official toll; incidental duration versus official schedule.

## 27. Source-follow-up variants

PASS offline for the five source wordings when an active claim exists. The live follow-up is the exception in section 31.

## 28. ASK/ACT variants

PASS offline. Approach-and-ask samples stay `ask`. "I hand him the papers," "I push the door," "I follow the tracks," and "I pay the toll" stay `act`. A question that mentions paying stays `ask`.

## 29. C18 historical replay status

Healthy. The Continuation 18 suite passed in this band: 12/12 hard-valid historical responses preserved, 4/4 hard-invalid initials blocked, 7/7 downstream-created failures still eliminated.

## 30. Broader regression result

267 passed, 0 failed. Files: Continuations 12, 13, 14, 15, 16, 18, and 19; outcome precedence; bounded improvisation; resolution contract; transcript regression; empty-social retry; model interpretation; interpretation proposal; perception narration authority. Full suite was not run.

## 31. Focused live transcript

One isolated session, `artifacts/pr_br_continuation19/20261002T002239Z`. Four completed turns. No repair rerun. The scene's addressable people are the guard captain, tavern runner, ragged stranger, and threadbare watcher. The third turn named a cloth merchant, who is not in that scene.

| Turn | Player | Contract | Provenance | Exact |
| --- | --- | --- | --- | --- |
| 1 | Ask the tavern runner what travelers are saying about the gate tonight. | ask / tavern_runner / content | initial_generation | yes |
| 2 | Who told you that? | ask / Tavern Runner / content | initial_generation | yes |
| 3 | Walk over to the cloth merchant and ask whether anyone has come through from the north road today. | ask / no interlocutor | safe_nonresolution | yes |
| 4 | Look over the notice board and read what is posted. | inspect / Notice board | regeneration | yes |

Turn 1 is an inability. No operational rule. No active claim, which is correct for an inability. Turn 2 keeps the tavern runner and does not use the previous response as a target. Dimension stayed `content` because no claim was stored and the interpreter's source dimension was not selected. Turn 3's fast path returned `ask` with a null interlocutor. Both generations answered as the tavern runner, were rejected for `wrong_interlocutor`, and the sealed line is "No one here can answer that from what is settled here." Turn 4's first posting invented an immediate stricter curfew and a specific last-seen track, rejected as `consequential_invention`. The retry stays on the authored taxes, curfew rules, and missing patrol, plus rain and crowd.

## 32. Live authority review

No emitted sentence was an unauthorized authoritative rule. Turn 1 and turn 2 carry no operational proposition. Turn 3's emitted safe line carries none. Turn 4's accepted atmosphere sentence is `incidental_fact`, ungrounded, not consequential. The rejected first posting did not become the emitted line.

## 33. Accepted versus emitted

4 / 4 exact matches. Accepted-response semantic mutations: 0. Immutable on all four turns.

## 34. Model and API cost

Gameplay-generation calls: 6. Interpretation calls: 1. Regeneration calls: 2. Evaluator model calls: 0. Generation attempts over two: 0. Independent smoke: not run. Full synthetic gate: not run.

## 35. Residual failure families

- A source follow-up with no stored claim stayed on dimension `content`. The target was the NPC, not the previous sentence, and the answer was a usable inability.
- A fast-path `ask` with a null interlocutor was returned for a named person who is not in the scene catalog. Both generations stayed on the previous NPC and the safe line was sealed. That is a malformed contract rather than an `act` misclassification.
- The local evaluator marked that safe line PASS.

The third-bell dialogue hole from C18 is closed in the deterministic replay. This live session did not emit a new unauthored schedule.

## 36. Readiness recommendation

READY FOR ANOTHER INDEPENDENT 10-TURN SMOKE: **NO.** Hard-authority blocking, grounded exceptions, rumor-as-claim, bounded detail, immutability, and the historical replay held. Live contract canonicalization did not: 2 / 4 contracts were correct, and turn 3 sealed a non-answer after an unbound ask. Do not open another repair implementation from this cycle. The failure family is in section 35.

READY FOR FULL SYNTHETIC GATE: **NO.**

## 37. PR-BR status

PR-BR: **STILL OPEN.**

No completion commit. No push. PR-BS was not started. Human playtest: **NOT AUTHORIZED.** Semantic repair/rerun: no. The four-turn budget was not reset.

# PR-BR Continuation 20 — Incidental Entity Binding & Intent-Preserving Abstention

HEAD `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`, uncommitted. C18's generate, hard-validate, seal, one regeneration, then safe-line lifecycle is unchanged. C19's ungrounded-rule rejection is unchanged. This cycle adds a PR-BN path for an ordinary person the player addresses, and it keeps the player's operation and inquiry dimension when that binding does not succeed.

## 1. C19 residual basis

C19's deterministic band was 267 / 267. The 16-turn historical replay stayed healthy, 7 / 7 downstream-created failures stayed eliminated, and 4 / 4 historical hard-invalid responses stayed blocked. Fresh live contract quality was 2 / 4. "Who told you that?" with no active claim stored dimension `content` after the interpreter returned `content` and `source`. "I walk over to the cloth merchant..." became `ask` with no interlocutor, both generations answered as the tavern runner, and the safe line was sealed.

## 2. C18 lifecycle unchanged

Yes. `run_preserve_if_valid` still seals a hard-valid response, retries once, and emits the safe line only after both attempts fail. Accepted text is still restored before emission. Continuation 18 passed inside the 281-test band.

## 3. C19 authority boundary unchanged

Yes. An ungrounded operational schedule is still `ungrounded_authoritative_rule`, still rejects the whole response, and still retries once. The third-bell, grounded-corpus, and rumor controls in Continuation 19 passed again. Incidental status does not waive that check.

## 4. Incidental entity authority model

`game/incidental_entity.py` reuses `validate_bounded_improvisation_proposal` with kind `incidental_fact` and category `background_npc_detail`. Player language is a proposed interaction target. A canonical catalog match binds first. Otherwise the proposal is a person-shaped reference in a populated scene, free of a plot assertion, an authority office, and PR-BN consequential or hidden terms. There is no occupation whitelist and no location-to-noun list.

## 5. Canonical, incidental, consequential, and ambiguous binding

Binding status is `bound_canonical`, `bound_incidental`, `unresolved`, `ambiguous`, or `rejected_consequential`. Entity class is `canonical_established`, `permitted_bounded_incidental`, `unsupported_consequential`, or `ambiguous_unresolved`. An implausible scene stays `unresolved` with reason `scene:isolated`, `scene:mixed`, or `scene:unknown`. A plot clause such as "who killed the duke" is rejected even when a word overlaps a canonical role. An in-catalog captain still binds canonically.

## 6. Scene plausibility

Population is read from public scene text: crowd, traffic, travelers, market, square, street, tavern, and dock versus sealed, abandoned, deserted, empty, or an isolated shrine, crypt, or ruin. Hidden facts are ignored. Incidental people are permitted only when population is `populated`. A cloth merchant, porter, traveler, stable hand, or sweeper can bind in a crowded gate. The same shapes do not bind in a sealed crypt, an isolated shrine, or an abandoned ruin.

## 7. Minimal incidental representation

An accepted record stores entity id, label, role, scene id, provenance `bounded_incidental`, authority `bounded_improvisation`, kind, category, truth status `runtime_incidental`, and consequence `incidental`. It does not store a proper name, faction, family, secret, inventory, quest role, biography, or combat stats.

## 8. Stable identity and promotion

The id is `inc_` plus a hash of the scene and the stemmed content words. A later role reference with the same stem reuses that id. Pronoun follow-up inherits it. The ledger entry is written `promoted`, so the entity remains available for continuity after acceptance.

## 9. Rejected incidental proposals

`rejected_consequential` and implausible `unresolved` proposals are not written to `incidental_entities`. They do not become the active interlocutor and do not become world truth. The previous interlocutor is cleared for that request instead of being restored.

## 10. Incidental NPC epistemology

Instantiation does not add quest knowledge or an official rule. The generation constraint names the bound person and forbids answering as someone else. A rejected or unresolved explicit addressee still supplies the proposed label to the speaker check, so a tavern-runner answer remains `wrong_interlocutor`.

## 11. Incidental NPC claims

Hearsay, rumor, and uncertain framing on a sentence that is not an operational family is now `npc_claim`. "I heard patrols have been delayed." persists through `note_emitted_npc_claim` with hearsay, rumor, or uncertain status and is not copied into visible facts.

## 12. C19 authority interaction

"The gate officially closes at third bell," spoken by an incidental porter, is hard-invalid and regenerates once. The incidental id is not removed because the response text failed. Extra invented detail about the person, such as a secret allegiance, remains subject to PR-BN and C19.

## 13. Operation and binding

A clear question stays `ask` when the interlocutor is unresolved, ambiguous, or rejected, including when the fast path would otherwise abstain. A genuine operation conflict still becomes `unresolved`. "Fine," is an interjection, not a proposed person, so a referential action stays on the fast path.

## 14. Dimension and binding

If the utterance's obvious dimension is a claim dimension, it stays first. "Who told you that?" drops a model-proposed `content` dimension unless the utterance is also a content request. Source is not replaced because claim binding failed.

## 15. Binding-status representation

The contract construction carries `entity_binding`: status, entity class, proposed label, bound id, explicit-new flag, authority reasons, and claim binding (`bound`, `unresolved`, or `none`). Those fields are not encoded by emptying the operation or swapping the dimension.

## 16. Explicit-interlocutor precedence

An explicit current-turn addressee is resolved before inherited discourse. A selected canonical or incidental person replaces the previous interlocutor in the contract, the social target, and the discourse slot.

## 17. Stale-interlocutor prevention

When the named person cannot be bound, the contract interlocutor is cleared, social `npc_id` is not used as a fallback, and an emitted speaker is not adopted as the rejected addressee. The tavern runner does not answer a failed cloth-merchant request.

## 18. Source without an active claim

"Who told you that?" with no eligible claim stays `ask` and `source`, with claim binding `unresolved`. The live interpreter returned dimensions `content` and `source` with a null claim id. The stored dimension stayed `source`.

## 19. Fast path

The fast path still canonicalizes or abstains. It binds an obvious canonical person and an already-established incidental person. A new incidental proposal is authority-checked and only then inserted into the referent index. The fast path does not mint a consequential entity.

## 20. Structured interpreter

The interpreter remains non-authoritative. A model interlocutor id that is not already bound cannot replace a deterministic `bound_canonical` or `bound_incidental` interlocutor. A model `content` dimension cannot replace an obvious source inquiry.

## 21. C19 four-turn replay

All four Continuation 19 live inputs were replayed offline against the frontier-gate scene.

| Turn | Player | Old contract | New contract |
| --- | --- | --- | --- |
| 1 | Ask the tavern runner what travelers are saying about the gate tonight. | ask / tavern_runner / content | ask / tavern_runner / bound_canonical |
| 2 | Who told you that? | ask / Tavern Runner / content | ask / tavern_runner / source, claim unresolved |
| 3 | Walk over to the cloth merchant and ask whether anyone has come through from the north road today. | ask / no interlocutor | ask / cloth merchant / bound_incidental |
| 4 | Look over the notice board and read what is posted. | inspect / Notice board | inspect / Notice board, not the runner |

## 22. Cloth-merchant regression

PASS. Operation `ask`, proposed interlocutor `cloth merchant`, binding `bound_incidental`, authority `pr_bn:accepted`, and the tavern runner is not the interlocutor. The minimal record is persisted.

## 23. Follow-up regression

PASS. "Who told you that?" keeps the same incidental id, operation `ask`, dimension `source`, and does not return to the tavern runner. With no eligible claim, claim binding stays `unresolved`.

## 24. Incidental variants

PASS. Porter, passing traveler, stable hand, woman sweeping the steps, and nearby merchant bind as incidental people in a populated scene. "Stable hand" stays `ask`. "Tavern patron" does not partially match Tavern Runner.

## 25. Implausible controls

PASS. A merchant in a sealed empty crypt, a dockworker in an isolated shrine, and a tavern patron in an abandoned ruin are not persisted. Operation stays `ask` and the previous interlocutor is cleared.

## 26. Consequential and authority-role controls

PASS. The assassin who killed the duke, the spy working for the Ash Compact, the officer who ordered the patrol murdered, the wizard who knows the secret entrance, the king's secret adviser, the commander of the hidden rebel cell, and the magistrate who secretly takes bribes are `rejected_consequential` and are not persisted.

## 27. Stable-identity regression

PASS. A permitted porter, a later "him," and a later role reference share one `inc_` id.

## 28. Minimality regression

PASS. The stored record has no name, faction, family, secret, quest role, inventory, or biography fields.

## 29. Incidental claim and authority regressions

PASS. The delayed-patrol hearing is an NPC claim and is absent from visible facts. The third-bell schedule from an incidental speaker is hard-invalid and retries once. The C19 grounded control and rumor control remain PASS.

## 30. C18 and C19 regression status

Continuation 18 passed: the 16-turn historical replay is healthy, 7 / 7 downstream-created failures remain eliminated, and 4 / 4 historical hard-invalid responses remain blocked. Continuation 19's third-bell, grounded, rumor, and immutability regressions passed. PR-BN authority regressions passed.

## 31. Broader regression

281 passed, 0 failed. The Continuation 19 band of 267, plus 14 Continuation 20 tests. Full suite was not run. Two mid-band failures were repaired before any live call: a leading "Fine," is not a proposed person, and a real operation conflict still abstains as `unresolved`.

## 32. Focused live transcript

One isolated session, `artifacts/pr_br_continuation20/20261002T010416Z`. Four completed turns. No repair rerun. The incidental person was a porter in the gate crowd, not the cloth-merchant fixture sentence.

| Turn | Player | Contract | Provenance | Exact | Manual |
| --- | --- | --- | --- | --- | --- |
| 1 | Catch the tavern runner's eye and ask what people around the gate have been saying tonight. | ask / tavern_runner / bound_canonical / content | initial_generation | yes | PASS |
| 2 | Step away from him and ask a porter hauling crates whether anyone came down from the north today. | ask / inc_23a2c479b9 / bound_incidental / proposed "porter hauling crates" | initial_generation | yes | PASS |
| 3 | Ask him who he heard that from. | ask / same id / bound_incidental / source / claim unresolved | initial_generation | yes | PASS |
| 4 | Leave him and look over the notice board. | inspect / no interlocutor | initial_generation | yes | PASS |

Turn 1 is the runner declining to spread rumors and pointing at the guard captain. No operational rule and no active claim. Turn 2 answers as the porter, from what he has seen, and does not restore the runner. Authority review marks the observation as incidental or an uncertain NPC claim, not an unauthorized rule. Turn 3 keeps the same porter. The interpreter proposed dimensions `content` and `source` with a null claim; the stored dimension is `source`, and the reply says he cannot name who. Turn 4 leaves the porter and describes the authored taxes, curfew rules, and missing patrol on the northwest mud track. The object target is empty, which is the same result as "I look over the notice board." without "read what is posted." The C19 sentence that includes the posted reading still binds the notice board offline.

## 33. Incidental entity lifecycle evidence

Turn 2 created `inc_23a2c479b9`, class `permitted_bounded_incidental`, reasons `scene:populated` and `pr_bn:accepted`. Turn 3 inherited that id by pronoun, reason `identity:discourse`, and did not mint a second entity. No consequential entity was created. Rejected proposals were not part of this live session; the deterministic controls cover them.

## 34. Accepted versus emitted

4 / 4 exact matches. Accepted-response semantic mutations: 0. Immutable on all four turns. Rejected-response state commits: 0, because no generation was rejected.

## 35. Model and API cost

Gameplay-generation calls: 4. Interpretation calls: 1. Regeneration calls: 0. Evaluator model calls: 0. Attempts over two: 0. Independent smoke: not run. Full synthetic gate: not run.

## 36. Residual failure families

No architecture-level failure in this cycle. The live inspect "look over the notice board" did not fill an object target unless the utterance also says what is posted. That shape already behaved this way offline and did not redirect to the porter. The porter's firsthand observation was not stored as the active claim, so the source follow-up correctly stayed unresolved rather than inventing a claim. Local evaluator: 4 / 4 PASS, no false PASS and no false FAIL.

## 37. Readiness recommendation

READY FOR ANOTHER INDEPENDENT 10-TURN SMOKE: **YES.** Deterministic incidental binding, intent preservation, C18 immutability, and C19 authority held, and the four live turns met the contract, interlocutor, and dimension targets. Do not open Continuation 21 for fixture cleanup. Do not run the smoke in this cycle.

READY FOR FULL SYNTHETIC GATE: **NO.**

## 38. PR-BR status

PR-BR: **STILL OPEN**, pending an independent smoke.

No completion commit. No push. PR-BS was not started. Human playtest: **NOT AUTHORIZED.** Semantic repair/rerun: no. The four-turn budget was not reset.

# PR-BR — Independent 10-Turn Synthetic Smoke After Continuation 20

Validation only. No gameplay behavior change. No repair. No rerun of the scored session. No 4×10 gate. No human playtest. No completion commit. No push. PR-BR remains open. PR-BS was not started.

## 1. Purpose

The question was whether the accumulated PR-BR architecture produces coherent multi-turn play when a fresh player interacts naturally with the product as it exists. The smoke was not designed to prove Continuation 18, 19, or 20. It was not a repair cycle, a scripted capability test, or the full synthetic gate.

The integrated behavior under observation is PR-BN bounded improvisational authority, the typed Resolution Contract, lightweight discourse state, hybrid semantic interpretation, the canonical-or-abstain fast path, structured model interpretation, interaction completion, the C18 immutable valid-response boundary and one bounded regeneration, C19 hard-authority validation, and C20 incidental entity binding with intent-preserving abstention.

## 2. Code provenance

- HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
- Subject: `PR-BN bounded DM improvisational authority` (2026-09-26)
- Working tree: uncommitted PR-BR, including Continuations 18–20 (`game/immutable_valid_response.py`, `game/proposition_authority.py`, `game/incidental_entity.py`, `game/resolution_contract.py`, `game/discourse_state.py`, `game/semantic_interpreter.py`, `game/interaction_completion.py`)
- Scored session: `artifacts/pr_br_independent_smoke/20261002T012905Z`
- Product path: `POST /api/start_campaign`, then `POST /api/chat`
- Live interpretation left enabled. `evaluate_playability` is local. No model evaluator.

## 3. Behavior changes

NO. No game, prompt, config, validator, or fixture edit before or during the scored run.

The only added file is the validation harness `artifacts/pr_br_independent_smoke/run_post_c20_session.py`. A first process, stamp `20261002T012819Z`, died before any gameplay turn because PowerShell wrote a UTF-8 BOM into the inbox and the harness reader rejected it. That process is not a scored session and not a rerun. The reader was switched to `utf-8-sig` before Turn 1 of the scored session. The scored session then ran to ten turns without further harness or product edits.

## 4. Session isolation

YES. Storage root: `artifacts/pr_br_independent_smoke/20261002T012905Z/isolated_data`. The player's saved campaign was not used.

Before opening, and again after opening before Turn 1:

- `active_claim`: null
- `active_interlocutor`: null
- `active_inspected`: null
- `last_attempted_action`: null
- `incidental_entities`: []
- session log empty before opening
- character: Galinor
- extra test-only facts injected: no

The scene is the ordinary frontier-gate bootstrap used by the product's isolated campaign start (`seed_frontier_gate_world` after default campaign-start scenes). It was not rewritten to exercise C18, C19, or C20.

Authoritative opening state: scene `frontier_gate`, NPCs `gate_guard`, `gate_serjeant`, `tavern_runner`, discoverable clue `notice_patrol_route` still unrevealed to the player until play. The scene catalog already lists `threadbare_watcher` as an interlocutor. No incidental entity record existed.

## 5. Persona

Galinor, a level-1 wandering wizard just arrived at a rainy frontier gate. He tries to understand what is in front of him, get useful information, and make ordinary progress. He talks to people who are present, follows what they say, and changes approach when someone stops helping.

He was operated by the validation agent from player-visible text only. No player model was called. He was not given C18, C19, or C20 findings, prior failure transcripts, regression strings, contract shapes, authority categories, or a coverage checklist. The ten actions were not written before the opening. Each line was chosen after that turn's visible reply. Instructions: `persona.md`. Motivations recorded in `inbox.jsonl` are the player's reasons, not an evaluator rubric.

## 6. Opening

Player-visible opening:

Rain spatters against the soot-dark stone of Cinderwatch's eastern gate, where frayed banners shudder in the chilly wind. The muddy approach to the gate is congested with foot traffic, refugees, and wagons, all pressing forward under the watchful eyes of guards who hold the choke point firm. Nearby, a tavern runner calls out energetically, hawking hot stew and tidbits of rumor to the waiting crowd. A notice board catches your eye; it prominently displays new taxes and curfew rules alongside a troubling warning about a missing patrol. Among the crowd, a lone figure dressed in threadbare clothes remains unnervingly still, their gaze darting more toward the passing faces and packs than the gate itself.

Opening generation calls: 1 (`primary_turn`). Not counted as one of the ten gameplay turns.

## 7. Model-call accounting

| Call | Count |
| --- | --- |
| Opening generation | 1 |
| Gameplay response generations | 12 |
| of which initial attempts | 10 |
| of which C18 regenerations | 2 |
| Interpretation calls | 8 |
| Synthetic-player model calls | 0 |
| Evaluator model calls | 0 |
| Adjudication, semantic repair, or hidden second opinion | 0 |

Cap: at most one regeneration per gameplay turn, and at most 20 gameplay response generations across 10 turns. Actual gameplay generations: 12. No turn exceeded two attempts.

## 8. Player-visible transcript

Turn 1. He is selling stew in the rain. Intended: a price, and somewhere dry.

Player: I push through the wet crowd to the tavern runner and ask him what a bowl of that stew costs, and whether I can eat it somewhere out of this rain.

GM: "A bowl of stew?" The tavern runner glances around anxiously before shaking their head. "Can't say what it costs right now, and there’s no dry spot to eat out here. Best head inside the market quarter if you want shelter from the rain."

Turn 2. He named the market quarter and refused a price. Intended: how to get inside, and whether the guards allow it for a meal.

Player: I nod at the crush of people. If the dry place is inside the market quarter, how do I get through this line, and will the guards let a stranger in just to eat?

GM: The tavern runner shakes their head again, their eyes darting briefly toward the guards managing the crowded line. "I can't say how you’d manage to get through the crowd, and I don’t know if they’d allow a stranger inside just to eat. You might have better luck asking one of the gate guards over there, but right now, things are tense and they're quite strict about who passes."

Turn 3. He told me to ask a guard. Intended: what a traveler must show or pay.

Player: I leave the runner and step up to the nearest gate guard. I ask, plainly, what a traveler has to show or pay to get through this gate.

GM: "I'm afraid I can't give you a simple answer," the gate guard says, eyes flicking toward the crowded line and the notice board listing curfews and taxes. "The rules for passage vary, and travelers might be required to show permits, pay certain fees, or prove they're not a threat. These days, with the Ash Compact census and tightened checks, things can change on short notice. Your best bet is to prepare for paperwork and coin, but exactly what depends on who’s watching and what happens to be in force when you reach the front."

Turn 4. He said it depends on who is watching. Intended: the papers and fee in force from this guard, now.

Player: I keep my eyes on the guard. You are the one watching me right now. What papers, and what fee, are actually in force for a lone traveler at this moment?

GM: "What papers and fees apply for a lone traveler right now?" the gate guard says, their tone measured. "I can't give you a straight answer—the requirements shift often. Your best bet is to check the notice board there; it lists the current taxes, curfew rules, and what’s expected for anyone seeking passage." The guard's gaze flicks to the crowded board plastered with notices.

Turn 5. He sent me to the board. Intended: read the taxes, the curfew, and any passage rule.

Player: I step away from the guard and go to the notice board he indicated. I read the postings for the taxes, the curfew, and anything that says what a traveler needs in order to pass.

GM: The notice board before you is densely packed with papers under a thin layer of grime from the rain. You make out several postings: a list of new taxes imposed recently, a curfew ordinance restricting movement after dark, and a cautionary note about a patrol reported missing to the northwest. While there is no direct statement detailing traveler-specific papers or fees here, the implication of frequent changes and the posted warnings suggest that travelers might face variable requirements. Nearby guards keep a watchful eye on the board and the crowd, but do not intervene as you read.

Turn 6. The board named taxes and a night curfew, not a fee or papers. Intended: a yes or no from the same guard.

Player: I leave the board and walk back to the same gate guard. The postings name new taxes and a curfew after dark, but no fee and no papers. Will you let me through tonight, or am I staying outside?

GM: The gate guard eyes you with a guarded expression. "The new postings list taxes and a curfew after dark, but there is no set fee or mandatory papers required for passage at this moment," they say. "Whether I'll let you through tonight depends on other factors—the crowd, the mood of the guards, and orders from above. No guarantees, but you won't be stopped just for lack of papers or fees right now." They glance back toward the notice board and the line pressing forward.

Turn 7. He said lack of papers will not stop me. Intended: try to pass.

Player: I step into the line and move toward the gate. I tell the guard I have no papers and nothing set aside for a fee, and that I am going through now.

GM: You step into the line toward the gate, stating plainly to the guard that you have no papers or fees set aside and that you intend to pass through now. The guard assesses you with a hard, unreadable gaze but offers no immediate promise of passage. His expression remains guarded, and without explicit orders or concessions, the crowded line ahead does not shift. It seems your movement forward depends heavily on factors beyond your control—the mood among the guards, the orders they are enforcing, and the pressure of the gathering crowd.

Turn 8. He will not decide. The still figure from the opening is still there. Intended: ask what they are waiting for.

Player: I step back out of the line. This guard will not give me a yes or a no. I walk over to the threadbare figure who has been standing still, watching packs and faces, and I ask quietly what they are waiting for.

GM: The player-visible reply is a raw JSON object, including `player_facing_text`, tags, an improvisation proposal, and `debug_notes`. Inside the JSON string, the watcher says they are waiting for a sign, that folks say the missing patrol might bring one or trouble, and looks toward boarded-up crates beyond the gate where the patrol was last seen.

Turn 9. They looked at crates and mentioned the patrol. Intended: which crates, and whether they saw it.

Player: I follow their glance. Which crates do you mean, and did you see the patrol there yourself, or is that only what people have been saying?

GM: You turn your gaze to follow where the watchful figures—gate guards and refugees alike—are looking. Their eyes trace a path toward a clutter of weather-beaten crates piled near the northwestern edge of the muddy approach to the gate. This aligns with the recent warnings posted about a missing patrol that was last seen moving past this muddy track northwest of here. The gate serjeant’s gaze lingers briefly on that area before flicking back to the restless crowd, his posture taut with vigilance amid the persistent rain and tension.

Turn 10. The figure did not answer. The reply put a serjeant on those crates. Intended: ask him what he is watching for.

Player: They did not answer me. I leave the threadbare figure and walk up to the gate serjeant who was looking at those crates. I ask him what he is watching for out there.

GM: "The gate serjeant follows your gaze toward the weather-beaten crates near the northern edge of the gate district. "Those crates," they say quietly, "have been a focal point for the patrol’s last known movements. We’re watching for any sign of that missing unit or unusual activity along that muddy northwest track. Quiet as it is, our eyes and ears need to stay sharp out there." Their expression tightens slightly. "The patrol was tasked with checking the route beyond those crates, but they've vanished without a trace. We’re on edge, waiting for any hint—something to break this silence."

Completed turns: 10 / 10. Early stop: no.

## 9. Turn-by-turn Resolution Contracts

| Turn | Operation | Target | Interlocutor | Dimension | Binding | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ask | tavern_runner | tavern_runner | content | bound_canonical | CORRECT |
| 2 | ask | Gate Guard | tavern_runner | content | bound_canonical | PARTIAL |
| 3 | ask | Gate Guard | gate_guard | content | bound_canonical | CORRECT |
| 4 | ask | Gate Guard | gate_guard | content | bound_canonical | CORRECT |
| 5 | unresolved | none | gate_guard | none | bound_canonical | INCORRECT |
| 6 | ask | none | gate_guard | none | bound_canonical | PARTIAL |
| 7 | act | Gate Guard | none | content | unresolved | PARTIAL |
| 8 | ask | Threadbare watcher | threadbare_watcher | content | bound_canonical | CORRECT |
| 9 | act | none | none | none | unresolved | INCORRECT |
| 10 | ask | Gate Serjeant | gate_serjeant | content | bound_canonical | CORRECT |

Correct 5 / 10. Partial 3 / 10. Incorrect 2 / 10.

Turn 2 keeps the runner as the person being asked, which matches the utterance, and moves the target onto the gate guard because the question is about them. That weakens the contract without making the runner stop being the addressee. Turn 6 asks the same guard for a yes or no and leaves the target empty. Turn 7 correctly treats the attempt to pass as an act, then fails to bind the guard and proposes the gate as a person (`proposal:not_a_person`), so the interlocutor is empty. Turn 5 is an inspection of the notice board. The contract is an ambiguous clarification still pinned to the guard. Turn 9 asks the watcher two questions. The contract is only the leading clause, `I follow their glance.`, stored as an act. The questions were segmented into `adjudication_question_text` and were not the contract.

## 10. Fast-path and interpreter routing

Fast-path contracts: 3 (turns 5, 6, 9). Structured-interpreter contracts: 7 (turns 1, 2, 3, 4, 7, 8, 10).

Turn 5 abstained from the fast path with `ambiguous_referent`, invoked the interpreter once, and still kept the abstaining deterministic contract (`validation_status: abstained`). That call is counted in the 8 interpretation calls and is not counted as a structured-interpreter contract.

| Turn | Route | Abstention | Interpreter calls | Proposal |
| --- | --- | --- | --- | --- |
| 1 | interpreter | unresolved_compound_intent | 1 | accepted, ask / runner |
| 2 | interpreter | target_not_canonical | 1 | accepted, ask / runner, target Gate Guard |
| 3 | interpreter | ambiguous_referent | 1 | accepted, ask / gate_guard |
| 4 | interpreter | ambiguous_referent | 1 | accepted, ask / gate_guard |
| 5 | fast-path abstention | ambiguous_referent | 1, not adopted | unresolved / gate_guard |
| 6 | fast path |  | 0 | ask / gate_guard |
| 7 | interpreter | ambiguous_referent | 1 | act, binding unresolved |
| 8 | interpreter | ambiguous_referent | 1 | ask / threadbare_watcher |
| 9 | fast path |  | 0 | act, leading clause only |
| 10 | interpreter | target_not_canonical | 1 | ask / gate_serjeant |

## 11. Incidental entity bindings

No incidental entity was created. `incidental_entities` stayed empty. World NPC ids stayed `gate_guard`, `gate_serjeant`, `tavern_runner`.

The threadbare figure was already a catalog interlocutor (`threadbare_watcher`). Turn 8 bound that id as `bound_canonical` / `canonical_established` / `identity:established`. A runtime attitude slot was created. No biography, role, or faction record was written.

Explicit new-interlocutor attempts: 3 (the gate guard on turn 3, the threadbare figure on turn 8, the gate serjeant on turn 10). Canonical bindings of the person being addressed: 7 (turns 1, 2, 3, 4, 6, 8, 10). Turn 5 also reports `bound_canonical` for the guard while the player is reading the board. Incidental bindings: 0. Unresolved bindings: 2 (turns 7 and 9). Stale-interlocutor fallbacks, meaning the previous NPC answers a question aimed at someone else: 0. Unsupported consequential entities instantiated: 0. Incidental identity continuity failures: 0.

## 12. Discourse-state evolution

| Turn | active_interlocutor | active_claim | active_inspected | previous_action |
| --- | --- | --- | --- | --- |
| 1 | tavern_runner | empty | empty | empty |
| 2 | tavern_runner | empty | empty | empty |
| 3 | gate_guard | empty | empty | empty |
| 4 | gate_guard | empty | empty | empty |
| 5 | gate_guard | empty | empty | empty |
| 6 | gate_guard | empty | empty | empty |
| 7 | empty | empty | empty | the pass attempt |
| 8 | threadbare_watcher | hearsay fragment `They say in a low, hesitant voice, \` | empty | the pass attempt |
| 9 | threadbare_watcher | same fragment | empty | `I follow their glance.` |
| 10 | id `gate_serjeant`, label `Threadbare watcher` | hearsay fragment `they say quietly,` | empty | `I follow their glance.` |

Integrity: `active_claim` FAIL. `active_interlocutor` FAIL. `active_inspected` FAIL. `previous_action` FAIL.

The claim slots store broken slices of emitted speech, marked hearsay, not world truth. The turn 10 interlocutor id updates to the serjeant and the label does not. The notice-board reading never becomes `active_inspected`. Turn 9 stores only the leading clause as the previous action.

## 13. Initial generation candidates

Turn 1. The runner cannot name a price, says there is no dry spot outside, and points to the market quarter.

Turn 2. The runner says the guards are strict, do not usually make exceptions, and suggests finding someone from the inner districts to vouch.

Turn 3. The guard says passage rules vary: permits, fees, or proof the traveler is not a threat, with the Ash Compact census and whoever is watching.

Turn 4. The guard repeats the question as his opening line, refuses a fixed fee, and points at the notice board.

Turn 5. The board is given specific new content: tax rates imposed by the city magistrate, a dusk curfew that forbids movement past the gates without explicit guard permission, and a warning to report unusual sights. The northwest route past the crates is also stated as posted.

Turn 6. The guard says there is no set fee or mandatory papers at this moment, and that lack of papers will not by itself stop the traveler tonight.

Turn 7. The player steps into the line. The guard does not promise passage. The line does not move.

Turn 8. The model returns a JSON object whose `player_facing_text` has the watcher answer, plus tags, an improvisation proposal, and debug notes.

Turn 9. Narration follows other people's eyes to crates at the northwestern edge and restates the missing patrol on the muddy northwest track. The watcher is not asked the two questions.

Turn 10. The serjeant says the crates mark the patrol's last known movements and that the patrol was tasked with checking the route beyond them.

## 14. Hard-validation decisions

Initial hard-valid: 8 / 10 (turns 1, 3, 4, 6, 7, 8, 9, 10).

Turn 2 initial: hard-invalid, reason `wrong_interlocutor`. The prose is the tavern runner speaking. The contract interlocutor is also the runner. The rejection did not match the visible speaker.

Turn 5 initial: hard-invalid, reason `ungrounded_authoritative_rule`. That matches the magistrate tax, the dusk permission rule, and the classifier's consequential access sentence about fees and permits in flux.

Turn 8 initial: hard-valid, even though the candidate is a JSON document. C18 then sealed it.

## 15. Regeneration evidence

Regenerations invoked: 2. Successful regenerations: 2. Double-invalid safe nonresolutions: 0.

Turn 2 feedback named `wrong_interlocutor` and required the same contract and interlocutor. The second candidate is the runner, hard-valid, and was accepted.

Turn 5 feedback named `ungrounded_authoritative_rule` and forbade a replacement invented fact. The second candidate drops the magistrate, the dusk permission rule, and the reporting instruction. It keeps taxes, a curfew after dark, and a patrol missing to the northwest. Hard-valid, accepted.

No turn generated a third gameplay response.

## 16. Accepted candidates

| Turn | Provenance | Accepted response |
| --- | --- | --- |
| 1 | initial_generation | runner, no price, no dry spot, market quarter |
| 2 | regeneration | runner, cannot say, ask a gate guard |
| 3 | initial_generation | guard, variable permits and fees |
| 4 | initial_generation | guard, no straight answer, read the board |
| 5 | regeneration | board reading without the invented dusk rule |
| 6 | initial_generation | guard, no set fee or papers right now |
| 7 | initial_generation | line does not yield |
| 8 | initial_generation | the JSON object |
| 9 | initial_generation | observation of the northwest crates |
| 10 | initial_generation | serjeant on the crates and the track |

All ten accepted records are marked immutable.

## 17. Accepted versus emitted

Accepted/emitted exact match: 10 / 10. Semantic mismatches: 0. C18 immutability regressions: 0. Downstream destruction of an accepted answer: 0.

The turn 5 rejection removed an invalid candidate before acceptance. The accepted regeneration was emitted unchanged. That is the boundary working, not a mutation after it.

## 18. Final manual review

Standard: would a competent human DM give this without the player having to correct the DM's understanding of target, speaker, action, question, or the established situation.

| Turn | Initial manual | Final manual | Why |
| --- | --- | --- | --- |
| 1 | PASS | PASS | The runner answers both the price and the dry place by refusing each and naming an existing district. |
| 2 | PASS | PASS | The runner answers both questions and points at the guards. The first candidate was also a usable runner answer. |
| 3 | PASS | PASS | The guard is the right speaker and gives a variable requirement instead of a number the scene does not post. |
| 4 | PASS | PASS | He refuses a fixed fee and sends the player to the board. The opening sentence echoes the question and is clumsy. It does not replace the answer. |
| 5 | FAIL | PASS | The first candidate invents a magistrate tax and a dusk permission rule. The accepted reading reports taxes, a night curfew, a patrol missing to the northwest, and no posted fee or papers. |
| 6 | PASS | PASS | The same guard gives a conditional answer: no papers are required at this moment, and that alone will not stop the traveler. |
| 7 | PASS | PASS | The attempt is acknowledged and does not succeed. The line stays put and the guard makes no promise. |
| 8 | FAIL | FAIL | The player is shown a JSON document with debug notes. The watcher's answer is trapped inside that document. |
| 9 | FAIL | FAIL | The two questions are not put to the watcher. The reply is an observation of where the crowd and the serjeant are looking. |
| 10 | PASS | PASS | The serjeant answers what he is watching for. The quotation marks are broken. The answer is still usable. |

Initial manual PASS: 7 / 10. Final manual PASS: 8 / 10.

## 19. Evaluator comparison

Local `evaluate_playability` only. No model evaluator.

Evaluator PASS: 3 / 10 (turns 1, 4, 6). Evaluator FAIL: 7 / 10.

False PASS (manual FAIL, evaluator PASS): 0.

False FAIL (manual PASS, evaluator FAIL): 5 (turns 2, 3, 5, 7, 10). Each of those failures is `player_intent_addressed`, and turn 10 also flags `malformed_output` for the broken quotes. Turns 8 and 9 fail both reviews. Turn 8 flags `malformed_output` and `player_intent_addressed`.

Manual review is authoritative for this validation.

## 20. Authority proposition review

Gameplay-relevant propositions only.

| Turn | Proposition | Grounded | Runtime class | Framing | Consequential | Reviewer agrees | Emitted | Persisted as |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Go to the market quarter for shelter | The district exists | incidental_fact | world_truth | no | yes | yes | not persisted as a new place |
| 2 initial | Inner-district voucher | no | npc_claim | uncertain | no | yes | no | not persisted |
| 2 emitted | Guards are strict about who passes | partial, choke is authored | npc_claim | uncertain | no | yes | yes | not persisted |
| 3 | Permits, fees, or proof one is not a threat | no | npc_claim | uncertain | yes, access | yes | yes | NPC claim, not world truth; active_claim stayed empty |
| 5 initial | Magistrate imposed new tax rates | no | not separately unauthorized | authoritative | yes | yes, this is an unsupported rule | no | not persisted |
| 5 initial | Dusk curfew forbids passage without explicit guard permission | no | hard-invalid as ungrounded authoritative rule | authoritative | yes | yes | no | not persisted |
| 5 initial | Fees and permits are in constant flux | no | consequential_proposal | world_truth | yes | yes | no | not persisted |
| 5 emitted | Taxes, curfew after dark, patrol missing to the northwest, no posted fee | taxes, curfew, and the northwest clue are authored; the "no fee posted" reading is a negative observation | npc_claim on the variable-requirements sentence | uncertain | no | yes | yes | not a new clue id |
| 6 | No set fee or mandatory papers at this moment | no | npc_claim | hearsay | yes, access | yes | yes | not stored as world truth |
| 8 | Boarded-up crates beyond the gate are where the patrol was last seen | the authored clue is the northwest mud track past the crates; "beyond the gate" and "boarded-up" are extra | chopped into incidental JSON fragments | world_truth on fragments | classifier no | no | yes, inside JSON | a visible-figure key from the gaze sentence, not a route fact |
| 9 | Patrol last seen moving past the muddy track northwest | yes, authored clue `notice_patrol_route` | not extracted as an ungrounded row | narrator | the clue is already canonical | yes, this is not an invention | yes | clue id unchanged |
| 10 | Patrol was tasked with checking the route beyond those crates and vanished | no | npc_claim on the last-known-movements sentence | hearsay | classifier no | no on the consequential flag | yes | hearsay claim fragment, not world truth |

Unsupported authoritative propositions generated: 3, all in the rejected turn 5 candidate (magistrate tax, dusk permission rule, fees-in-flux as world truth). Rejected: 3. Emitted: 0.

## 21. Incidental versus consequential

Not every useful detail is consequential. Gestures, rain, grime on the board, and the runner's anxious glance stay inside bounded color.

The review question is whether an invention materially changes the world in a way that needs stronger authority.

Turn 1's market quarter is an existing district used as shelter advice. Turn 3 and turn 6 state access conditions as uncertain NPC speech. They were not written as world truth. Turn 9 restates the authored northwest clue. Those are not incidental-bucket mistakes.

Two classifications are questionable:

- Turn 8's last-seen crates "beyond the gate" are strategic, and the JSON segmentation never marked that clause consequential.
- Turn 10's "tasked with checking the route beyond those crates" is a mission and a destination. It is correctly framed as something the serjeant says. The consequential flag is still false.

## 22. C20 incidental-entity review

The player referred to one ordinary person who is easy to mistake for an incidental creation: the threadbare figure. The catalog already had `threadbare_watcher`. Binding was canonical, not incidental. The initial representation is an attitude slot with empty topics. Later turns kept that id until turn 10's interlocutor id moved to `gate_serjeant` while the label stayed `Threadbare watcher`. No extra model-generated biography was persisted. The watcher's patrol sentence remained inside the emitted JSON and was not stored as a world fact. The stored claim is a broken hearsay fragment.

No porter, merchant, or other new person was proposed. No consequential unsupported entity was instantiated.

## 23. Persistence review

Accepted bounded inventions did not become new world records. The improvisation ledger stayed empty, including rejected entries.

Accepted NPC statements that were stored are marked hearsay. They did not become world truth. Most earlier NPC statements, including the guard's access hedge, were not stored at all.

Rejected turn 5 facts are absent from scene clues, visible facts, and the ledger. Search of the isolated JSON for `magistrate`, `dusk`, `boarded-up`, and `explicit guard permission` found no matches.

Rejected entities persisted: 0. Rejected-response state commits: 0.

The accepted turn 8 JSON left a visible-figure key derived from the gaze sentence. That is residue of the accepted emission, not of a rejected candidate.

## 24. Failure clustering

Two manual failures, two mechanisms. They are not one family, and neither mechanism repeated as a manual failure.

1. Hard validation sealed non-prose. Turn 8. The model emitted a JSON document. Hard validation marked it valid. C18 then preserved it byte for byte, which is what C18 is for. The defect is that the candidate was eligible to be sealed. The stored claim label is a slice of that JSON.

2. Leading-clause segmentation dropped the question. Turn 9. The fast path committed `I follow their glance.` as an act and parked the two questions in `adjudication_question_text`. The watcher never answered. Turn 5 is related only in outcome quality of the contract: an inspection became an unresolved clarification pinned to the previous guard. The accepted prose still read the board, so it is not the same manual failure.

Turns 2 and 5 show the regeneration boundary doing the job it was given. Turn 2's `wrong_interlocutor` rejection looks undeserved because the runner was already the speaker, and the replacement was also a runner answer. It did not become a player-visible failure.

Evaluator disagreements are a separate cluster: five false FAILs, zero false PASSes. They are not manual failures.

## 25. Authority-watchlist conclusion

NO.

The smoke did not provide repeated evidence that materially consequential invented information is classified as bounded incidental detail.

The authored northwest clue does appear in player-visible text on turns 5, 9, and 10. Turn 9's wording matches the clue. Turn 10 puts a mission on that route in the serjeant's mouth and classifies the speech as an NPC claim, not as incidental color. Turn 8 adds "boarded-up" and "beyond the gate" inside a JSON dump, and the segmenter does not classify that clause cleanly. That is one malformed turn, not a repeated incidental-bucket family.

Isolated mistakes are recorded above. No repair was implemented.

## 26. Readiness decision

READY FOR FULL 4×10 SYNTHETIC GATE.

Final manual PASS is 8 / 10. The critical counters in the strong-evidence list are zero: accepted/emitted semantic mismatches, downstream-created failures, unsupported authoritative facts emitted, stale-interlocutor fallbacks, consequential unsupported entities, rejected-response state commits, and player-visible systemic continuity collapse.

The contract bar for strong evidence was not met: 5 correct, 3 partial, 2 incorrect. The two manual failures are different mechanisms and each happened once. Opening another focused continuation to chase those two turns would ignore the instruction that an 8 / 10 smoke without a critical architectural failure should not become another repair cycle. The 4×10 gate is the measurement that can show whether either mechanism recurs. It was not run.

## 27. PR-BR status

PR-BR: STILL OPEN.

No completion commit. No push. PR-BS was not started. Human playtest: NOT AUTHORIZED. Full 4×10 synthetic gate: NOT RUN. Semantic repair or rerun: NO.

### C18, C19, and C20 baselines used only for this review

C18: a hard-valid generated response should reach the player unchanged, with at most one regeneration. That held on all ten turns, including the unfortunate preservation of turn 8.

C19: an unsupported authoritative operational rule should not cross the hard-validity boundary. The turn 5 candidate that stated a dusk permission rule was rejected and was not emitted. Emitted unsupported authoritative facts: 0.

C20: an ordinary plausible incidental person may be instantiated under PR-BN, and an unsupported consequential entity may not. This session did not need a new incidental person. The threadbare figure was already canonical. No consequential entity was created, and no stale interlocutor answered in place of a new addressee.

# PR-BR — Full 4×10 Synthetic Playability Gate

Validation only. No gameplay behavior change before or during the gate. No repair. No rerun. No fifth persona. No extra smoke. No human playtest. No completion commit. No push. PR-BR remains open. PR-BS was not started.

## 1. Purpose

Determine whether remaining defects recur across four independent natural 10-turn sessions, or stay isolated. The integrated stack under validation is PR-BN bounded improvisation, the typed Resolution Contract, lightweight discourse state, hybrid semantic interpretation, the canonical-or-abstain fast path, structured model interpretation, interaction obligations, the C18 immutable valid-response boundary and one regeneration, C19 hard-authority validation, and C20 incidental binding with intent-preserving abstention.

## 2. Authorization basis

The independent smoke after Continuation 20 finished 10/10 turns with final manual PASS 8/10 and zero accepted/emitted mismatches, downstream-created post-seal failures, emitted unsupported authoritative facts, stale-interlocutor fallbacks, unsupported consequential entities, and rejected-response commits. That smoke did not authorize Continuation 21. This gate was the authorized next measurement.

## 3. Provenance

- HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
- Subject: PR-BN bounded DM improvisational authority
- Date: 2026-09-26 15:18:20 -0400
- Gate stamp: `20261002T021950Z`
- Working tree at freeze: uncommitted PR-BR game, tests, tools, and docs, recorded in `freeze.json`. No `game/` file hash changed between sessions. A later session would have stopped with `FREEZE_MISMATCH`.
- Harness: `artifacts/pr_br_full_gate/run_gate_session.py`. It drives `POST /api/start_campaign` and `POST /api/chat` through the product app. It does not change product behavior.

## 4. Behavior freeze

Confirmed. No product code, prompt, or configuration edit after Session A opened. Personas and the harness were written before Session A and were hash-checked on Sessions B, C, and D.

## 5. Configuration and model

All routes used `gpt-4.1-mini`: `MODEL_NAME`, `DEFAULT_MODEL_NAME`, `HIGH_PRECISION_MODEL_NAME`, and `RETRY_ESCALATION_MODEL_NAME`. `ENABLE_MODEL_ROUTING` was true. Live interpretation was left enabled. Evaluator model calls: 0. Product synthetic-player model calls: 0.

Player lines were chosen one turn at a time by a fresh or resumed player who saw only that persona and that session's player-visible transcript. Those operator decisions are not product synthetic-player calls. There were 40 of them.

## 6. Isolation

Each session used its own storage root, a new session id, an empty discourse focus before Turn 1, no incidental entities, an empty improvisation ledger, an empty session log before opening, and only the authored frontier-gate NPCs `gate_guard`, `gate_serjeant`, and `tavern_runner`. Character name remained the product default, Galinor. Scene content was not hand-edited. Openings differ because the product generates them from the same authored baseline.

| Persona | Session id | Discourse before Turn 1 | Incidentals before Turn 1 |
| --- | --- | --- | --- |
| A | `6c8d3781fdeb8d0cf7f9835f` | all null | none |
| B | `a2a06862f50a60c63d84b2bd` | all null | none |
| C | `cbdc8395077b740060237d56` | all null | none |
| D | `73cbeca12beac54fe0ae3c5a` | all null | none |

Isolation confirmed: YES.

## 7. Personas

Behavioral tendencies only. No scripted NPCs, questions, objects, or routes.

- A, direct and practical. Wants something usable and then acts on it.
- B, social and curious. Talks to people, follows up, and may change interlocutors.
- C, exploratory and observant. Looks first, then sometimes asks or moves.
- D, independent and action-oriented. Prefers doing, and talks when it helps.

Texts: `artifacts/pr_br_full_gate/personas/persona_a.md` through `persona_d.md`.

## 8. Opening scenes

Product openings, not hand-written variants. Full text is in each session's `visible.md`.

- A: Rain at Cinderwatch's eastern gate, guards, serjeant, notice board, townhouse, tavern runner, threadbare figure.
- B: Same gate, notice board, townhouse, threadbare figure, runner selling news for a coin.
- C: Same gate, serjeant and roster, runner, threadbare figure, bright townhouse.
- D: Same gate, guards, townhouse, ragged threadbare stranger, runner, notice board.

## 9. Player-visible transcripts

Verbatim transcripts are the four `visible.md` files packaged with this audit. They were the only scene text the players used.

## 10–16. Contracts, routing, candidates, validation, emission

Per-turn records are in each session's `review_index.json` and `turns/turn_NN.json`. Manual contract class is below. Accepted text equaled emitted text on every turn, including the six hard-valid retries. Initial model text differed from the emission only when a retry or the safe line was what the runtime accepted.

| Turn | Contract | Routing | Initial hard | Final provenance | Final manual |
| --- | --- | --- | --- | --- | --- |
| A1 | PARTIAL inspect board, binding unresolved | fast | valid | initial | PASS |
| A2 | PARTIAL ask, serjeant, no target | fast | valid | initial | PASS |
| A3 | PARTIAL act, unresolved | fast | valid | initial | PASS |
| A4 | PARTIAL act toward serjeant, ambiguous | interpreter | invalid: ungrounded rule (3 copper) | retry | PASS |
| A5 | INCORRECT phrase bound as a person | fast | invalid: wrong interlocutor | retry | PASS |
| A6 | CORRECT act, serjeant | interpreter | valid | initial | PASS |
| A7 | PARTIAL ask, unresolved | fast | valid | initial | PASS |
| A8 | INCORRECT inherited junk target | fast, discourse inheritance | valid | initial | PASS |
| A9 | PARTIAL ask, chopped "first local" | fast | valid | initial | PASS |
| A10 | INCORRECT perceive board/wear while the player entered the tavern | fast, discourse inheritance | valid | initial | PASS |
| B1 | PARTIAL ask, runner right, target skewed to the board | fast | valid | initial | PASS |
| B2 | CORRECT ask, runner | interpreter | invalid: wrong interlocutor | retry, still the captain | FAIL |
| B3 | CORRECT ask, captain the player then addressed | interpreter | valid | initial | PASS |
| B4 | PARTIAL ask, captain, unresolved | fast | valid | initial | PASS |
| B5 | INCORRECT "i lean in" bound as a person | fast | valid | initial | PASS |
| B6 | PARTIAL ask, captain id, junk label | interpreter | valid | initial | PASS |
| B7 | CORRECT ask, runner | fast | valid | initial | PASS |
| B8 | PARTIAL ask, runner, junk target | interpreter | invalid: wrong interlocutor | retry | PASS |
| B9 | INCORRECT ask, ragged stranger instead of the runner | fast | valid on the catalog line | initial, catalog grimace | FAIL |
| B10 | PARTIAL ask, unresolved | fast | valid | initial | PASS |
| C1 | PARTIAL inspect board, time, unresolved | interpreter | valid | initial | PASS |
| C2 | INCORRECT yard phrase bound as a person, dimension wear | fast | invalid: interaction incomplete | retry | PASS |
| C3 | PARTIAL act, inherited junk target | fast, discourse inheritance | valid | initial | PASS |
| C4 | INCORRECT perceive junk target; look-plus-question lost in the contract | interpreter | valid | initial | PASS |
| C5 | CORRECT follow the guard's glance | interpreter | valid | initial | PASS |
| C6 | PARTIAL inspect the watcher, unresolved | interpreter | valid | initial | PASS |
| C7 | PARTIAL ask the watcher, unresolved | interpreter | valid | initial | PASS |
| C8 | INCORRECT ask, clause bound as a person; player was looking | fast | invalid: wrong interlocutor | retry, still speech | FAIL |
| C9 | PARTIAL inspect, target widened to the district | interpreter | valid | initial | PASS |
| C10 | INCORRECT perceive district/wear | fast | invalid: interaction incomplete | safe nonresolution | FAIL |
| D1 | CORRECT inspect board, time | fast | valid | initial | FAIL |
| D2 | INCORRECT inspect board; player looked for the track | fast, discourse inheritance | valid | initial | PASS |
| D3 | INCORRECT perceive board/wear; junk interlocutor | fast | invalid: interaction incomplete | safe nonresolution | FAIL |
| D4 | PARTIAL inspect the brush | fast | valid | initial | PASS |
| D5 | INCORRECT perceive board | interpreter | valid | initial | PASS |
| D6 | INCORRECT ask, board target, junk interlocutor | fast, discourse inheritance | valid | initial | PASS |
| D7 | INCORRECT ask, brush phrase as a person | fast | valid | initial | FAIL |
| D8 | INCORRECT act, board target | interpreter | valid | initial | FAIL |
| D9 | INCORRECT inspect board; prose did inspect the figure | interpreter | valid | initial | PASS |
| D10 | PARTIAL act, unresolved | fast | valid | initial | PASS |

## 17. Manual turn review

A competent human DM standard. Runtime labels are evidence, not the verdict.

Persona A, final 10/10. The player read the board, asked the serjeant the toll, presented for inspection, paid three silver, was cleared, walked through, asked for a bed, and entered the Rusty Tankard. Turn 4's first candidate stated a three-copper toll and was rejected. Turn 5's first candidate had the guard name two silver and was rejected; the retry had the serjeant name three silver. Both retries were playable. Turn 9 casts the tavern runner as "the first local." That is a substitution, and the bed-and-meal question was still answered. Turn 10's contract still pointed at the notice board; the prose entered the tavern.

Persona B, final 8/10. Turn 2: the player was still questioning the runner. The first candidate and the accepted retry are both the guard captain. The first was rejected for the wrong interlocutor. The retry was sealed anyway. Turn 9: the player asked the runner to point at someone. The model wrote a longer answer in the ragged stranger's mouth, naming houses. The player received the catalog line `Ragged stranger grimaces. "Not something I can say here."` That line was what hard validation sealed. The generated answer did not reach the player. The other eight turns are playable, including vague but usable refusals.

Persona C, final 8/10. Looking at the board, the yards, the guard, the road, the watcher, and the townhouse was answered in ordinary prose. Turn 8: the player looked at faces and did not ask. Both candidates are the ragged stranger speaking. The retry was sealed. Turn 10: both candidates described the windows and a crest. Both were rejected as interaction-incomplete. The player received `The inspection establishes no further reliable detail about the wear.`

Persona D, final 6/10. Turn 1 answers the request for a name by putting "Eldrin Voss" on the roster. That name is not in the authored patrol clue, and it is stated as a posted fact. Turn 3: both candidates described boot prints and something moving. Both were rejected. The player received the same wear sentence as C10. Turns 7 and 8 keep the figure in the brush unresolvable after the player asked for a plain look. Turn 9 finally gives negatives (no face, clothes, weapon, or badge). Turn 10 walks on and is playable. Turns 2, 4, 5, and 6 are playable even where the contract still names the notice board.

No session stopped early. A bad answer never made the next choice impossible.

## 18. Authority propositions

Classifier unauthorized-authoritative rows that were emitted: 0.

Material propositions the reviewer treated separately:

- A4 initial, three copper pieces as the wizard's toll. Classifier: ungrounded authoritative rule. Hard-invalid. Not emitted.
- A5 retry, three silver, spoken by the serjeant after the player asked the exact coin. Classifier did not flag it. Emitted. Questionable. A price the player requested, framed as NPC speech, is not scored as an emitted authored-rule break.
- B8 initial, families Durain and Velmark. Not emitted. Rejected as wrong interlocutor, not as an authority rule.
- B9 model text, House Verevin and the Ash Cowl. Not emitted.
- C10 candidates, a hawk crest tied to House Verevin, then a dragon-and-tree crest. Not emitted.
- D1, roster name Eldrin Voss, posted as the patrol leader, this morning. Classifier did not flag it. Emitted. The player then searched for that person's gear. Reviewer: one unsupported official identity. Not repeated.

Unsupported authoritative facts generated, reviewer count of these material items: 6. Rejected before emission: 4 (A4, B8, B9, C10). Emitted: 1 (D1), plus 1 questionable NPC price (A5) that is not counted in the emitted-rule total.

## 19. Incidental entities

No supported new person stayed stable under a real name. The ledger promoted sentence fragments as incidental people:

- A: "exact coin modest fee so i"; "first local i pass"
- B: "i lean in"
- C: "for crate yards"; "they lingered on"
- D: "underbrush for whatever is moving out there"; "still patch brush at steady pace"

B and C also show canonical `refugee` / "Ragged stranger," which matches the authored threadbare figure, not a new consequential person. D's brush figure was not stored as an NPC. Unsupported consequential entities instantiated: 0.

The "first local" in A9 was not kept as its own person in the prose. The runner answered. That is one incidental identity break in the player-visible scene. Binding status itself was `bound_incidental`, not a stale canonical fallback flag.

Explicit new-interlocutor attempts: A9 (first local), B3 (the captain the previous reply had introduced, then the player addressed), D6 (the figure on the track). Canonical bindings: 10. Incidental bindings: 11. Unresolved bindings: 18. Ambiguous: 1. Stale-interlocutor binding fallbacks: 0.

## 20. Discourse

`active_claim`: usually empty. A9–A10 stored the fragment "they say, voice low and hurried." Cosmetic. It did not steer A10.

`active_interlocutor`: ids often moved to a real NPC while the label stayed a fragment ("exact coin modest fee so i" on the serjeant; "i lean in" on the captain and the runner; "for crate yards" across C2–C5). Wrong answers were not caused by those labels alone.

`active_inspected`: A kept the notice board after the player had left it, which matched A10's wrong contract, not A10's prose. D kept a notice-board label on an incidental id. C moved from the board to the junk yard phrase, then to the watcher, then to the district.

`previous_action`: often stuck on an earlier sentence for several turns (A8's departure through A10; C3's yard search through C10; D8's branch pull through D9).

## 21. Persistence

Accepted bounded fragments persisted as incidental ledger rows. They did not become scene clues or visible facts. Rejected ledger lists are empty in all four sessions. Rejected copper toll, family names, house names, and crests are absent from final facts, clues, and NPC ids. Eldrin Voss was not written into the persisted clue list; it exists in the transcript only. Three silver was not written into world truth. Rejected-response state commits: 0.

## 22. Structured output

No JSON, schema, or tool payload was shown to a player. A6, A9, and B6 have a stray opening quotation mark in otherwise ordinary prose. Those three stayed manual passes. Structured-output leaks: 0. The smoke's JSON leak did not recur.

## 23. Compound intent

Naturally combined clauses were not manufactured.

- A2, two questions to the serjeant. Both answered.
- A5, open the pack and ask the price. The price was answered. Inspection was deferred until payment. Playable.
- C4, look at the guard and ask who passed. The prose did both. The contract did not. Not a gameplay loss.
- C10, windows and crest. Both were in the rejected candidates and absent from the safe line.
- D3, prints and listening. Both were in the rejected candidates and absent from the safe line.

Compound-intent gameplay losses: 2, both from the safe nonresolution, not from the smoke's leading-clause fast path. That fast-path pattern did not recur.

## 24. Per-persona metrics

| | A | B | C | D |
| --- | --- | --- | --- | --- |
| Completed | 10 | 10 | 10 | 10 |
| Initial manual PASS | 8 | 8 | 9 | 7 |
| Final manual PASS | 10 | 8 | 8 | 6 |
| Correct / partial / incorrect | 1 / 6 / 3 | 3 / 5 / 2 | 1 / 5 / 4 | 1 / 2 / 7 |
| Fast / interpreter | 8 / 2 | 6 / 4 | 4 / 6 | 7 / 3 |
| Regenerations | 2 | 2 | 3 | 1 |
| Safe nonresolutions | 0 | 0 | 1 | 1 |
| Accepted/emitted mismatches | 0 | 0 | 0 | 0 |
| Authority violations emitted | 0 | 0 | 0 | 1 |
| Stale binding fallbacks | 0 | 0 | 0 | 0 |
| Structured leaks | 0 | 0 | 0 | 0 |
| Discourse-caused later failure | NO | NO | YES | YES |
| Incidental bindings | 2 | 1 | 3 | 5 |

A failures: none final. B: turns 2 and 9. C: turns 8 and 10. D: turns 1, 3, 7, and 8.

## 25. Aggregate

- Completed: 40/40
- Initial manual PASS: 32/40
- Final manual PASS: 32/40
- Correct / partial / incorrect: 6 / 18 / 16
- Partial with successful play: 18
- Partial with failed play: 0
- Incorrect with successful play: 10
- Incorrect with failed play: 6
- Fast-path turns: 25
- Interpreter turns: 15
- Initial hard-valid: 32
- Regenerations: 8
- Successful hard-valid retries: 6
- Double-invalid safe nonresolutions: 2
- Accepted/emitted mismatches: 0
- Downstream post-seal alterations: 0
- Pre-seal catalog replacement of a generated answer: 1 (B9)
- Unsupported authoritative facts generated: 6 material items
- Rejected before emission: 4
- Emitted unsupported official identity: 1 (D1)
- Questionable price classification: 1 (A5)
- Explicit new-interlocutor attempts: 3
- Canonical / incidental / unresolved bindings: 10 / 11 / 18
- Stale-interlocutor binding fallbacks: 0
- Unsupported consequential entities instantiated: 0
- Incidental identity breaks: 1 (A9)
- Structured-output leaks: 0
- Compound-intent gameplay losses: 2
- Discourse-caused gameplay failures: 2
- Rejected-response state commits: 0

## 26. Failure clustering

1. Inspection false invalid, then one canned sentence. C10 and D3. Same player-visible sentence. Same hard-invalid reason, `interaction_incomplete`. The candidates had already described what the player looked at.
2. Wrong speaker or catalog shell. B2 (captain answers the runner; the retry was sealed), B9 (catalog grimace replaces the generation before the seal), C8 (a look is answered as stranger speech). Three turns, personas B and C.
3. Sentence fragments bound as incidental people. All four personas. Eighteen partial contracts still played. Ten incorrect contracts still played. Six incorrect contracts did not. The fragment bind is the common contract defect under those mixed outcomes.
4. Evasive figure. D7 and D8 only. The player asked for a plain look and got a shadow that is neither person nor animal. D9 then answered with negatives. One persona.
5. One invented roster name. D1 only.
6. Evaluator disagreement. Not a gameplay family.

No JSON-leak family. No leading-clause fast-path family of the kind in the post-C20 smoke.

## 27. Recurrence

The wear-sentence failure is the same mechanism twice, in C and D. Play continued after both. The wrong-speaker family is three turns in two personas. Play continued; B's player even addressed the captain the reply had invented. Fragment binding is the widest pattern and is usually benign. A single invented name and a two-turn vague figure are not cross-persona systems. Nothing required the player to correct the GM on every turn, and no session became unplayable.

## 28. Evaluator

Deterministic `evaluate_playability` only. No evaluator model.

- Evaluator PASS: 21/40
- False PASS against this manual review: 5 (B2, B9, C8, D1, D7)
- False FAIL: 16

The local evaluator is not the verdict. It missed the wrong-speaker turns and the invented roster name, and it failed many playable looks and questions.

## 29. Model-call accounting

- Opening generations: 4
- Gameplay initial generations: 40
- Gameplay retry generations: 8
- Interpretation calls: 15
- Product synthetic-player calls: 0
- Evaluator model calls: 0
- Product total: 67
- Operator player-selection calls, outside the product: 40
- Known total including those operator calls: 107

## 30. Gate decision

PR-BR SYNTHETIC GATE FAILED — MULTIPLE SYSTEMIC DEFECTS REMAIN.

Final manual pass is 32/40, which meets the approximate strong-pass count, and the post-seal equality, consequential-entity, and rejected-commit counters are zero. The gate's question was recurrence. Two failure mechanisms recurred across personas: completed inspections replaced by one wear sentence, and replies whose speaker is not the person addressed, including one catalog line substituted for the generation before the immutable seal. A third pattern, binding a slice of the player's sentence as an incidental person, is in every persona. It is often harmless and sometimes underneath the other two. That is more than one narrow defect, and it is not an infrastructure failure.

The post-C20 watch items did not recur: no JSON leak, no leading-clause fast path that drops a trailing question, and no repeated incidental-bucket miss of the smoke's kind. D1 is one missed official name.

## 31. Human playtest

NOT AUTHORIZED. Do not start a human playtest from this result.

## 32. PR-BR status

PR-BR remains OPEN. No repair was implemented. No rerun was performed. PR-BS was not started. Wait for external review.

Smallest recurrent mechanisms, without a proposed patch:

- An ordinary look is marked interaction-incomplete, and the only sealed line is about "the wear."
- The sealed speaker is not the person the player is talking to. Once, that seal is a catalog grimace rather than the generated answer.
- Fast-path binding stores a clause fragment as an incidental person and sometimes keeps that fragment in discourse.

### C18, C19, and C20 baselines

C18: every text the runtime marked accepted was the text emitted, including six retries and two safe lines. The B9 grimace was sealed as the initial generation and then left unchanged. The longer model answer never became the accepted text. Post-seal mismatches: 0.

C19: the three-copper toll was rejected and not emitted. The Eldrin Voss roster line was emitted and not flagged. No second official identity of that kind appeared.

C20: no unsupported consequential entity was stored. No binding-status stale fallback to the previous NPC was recorded. Fragment incidental binds were common. One player-visible case, A9, answered a new "first local" with the tavern runner.

# PR-BR Continuation 21 — Resolution Subject Integrity & Incidental-Binding Hardening

Bounded post-gate repair. Deterministic replay and stubbed `/api/chat` first. One isolated focused live session afterward. No full synthetic gate. No human playtest. No commit. No push. PR-BR remains open. PR-BS was not started.

HEAD remains `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (PR-BN bounded DM improvisational authority, 2026-09-26). C21 is uncommitted work on top of Continuations 18–20.

## 1. Gate failure basis

The 4×10 gate at `artifacts/pr_br_full_gate/20261002T021950Z` completed 40/40 turns. Final manual pass was 32/40. Eight player-visible failures: B2, B9, C8, C10, D1, D3, D7, D8. Contract labels were CORRECT 6, PARTIAL 18, INCORRECT 16. All 18 partial contracts still played. Only 6 of the 16 incorrect contracts caused a failed turn. The metric kept here is player-visible resolution, not contract-label perfection.

## 2. C18 / C19 / C20 architecture preservation

C18 immutable emission, C19 hard-authority validation, and C20 bounded incidental entities stay in place. This continuation does not restore post-seal rewriting, best-safe tournaments, or a new authority taxonomy. It tightens inspection completion, speaker checks, candidate shape, and role-identity classification inside those boundaries.

## 3. C10 forensic trace

Player text looks past townhouse windows for a lamp, a face, or movement, and reads whatever mark or crest is on the door. The fast path classified it as perceive with dimension wear, because `_WEAR_RE` treated bare “mark/marks” as wear. Both generations described the windows and a crest. Both were marked interaction-incomplete, because the dimension lexicon required wear/worn/fray/scuff and ignored the observation. The sealed line was the wear safe-template. Provenance was safe nonresolution. Manual FAIL.

Corrected contract: perceive, no sensory dimension, no incidental bind. A window-and-crest observation is hard-valid. The old wear template is incomplete against this player text. The safe line is the generic scene line, not wear.

## 4. D3 forensic trace

Player text checks ruts for boot prints or drag marks, then listens toward the underbrush. “Drag marks” matched wear before “listen”, so the primary dimension was wear. The address pattern also bound “underbrush for whatever is moving out there” as an incidental person. Both generations mentioned prints and sound and were rejected as incomplete. The sealed line was the same wear sentence. Manual FAIL.

Corrected contract: perceive, dimension sound, no incidental person. A response with rustling is complete. A wear-only response is incomplete. The safe line names sound.

## 5. Wear-fallback root cause

The shared sentence was not a stale scene fact and not a phrase the model preferred. `_WEAR_RE` owned “mark/marks”. The contract stored that as the single dimension. Completion required a tiny wear lexicon. `safe_nonresolution` then echoed `contract.dimension`. Any failed inspection whose false dimension was wear produced the same sentence. Ownership is fixed: bare marks are not wear, player-requested senses outrank a stale contract tag, and the safe line names a sense only when the current utterance asked for exactly one.

## 6. Inspection completion repair

Completion is evidence against the requested sense. Dimensionless inspection is complete when the response observes the target. Sound, smell, wear, use, and markings are checked against what the player asked, including ordinary inflections (rustles, scratches). A wear sentence does not satisfy a listen. Retry feedback keeps the same contract, target, and dimension. One regeneration, then a target-aware safe line.

## 7. B2 forensic trace

Player kept the coin and asked who saw the footprints, still with the tavern runner. Contract was ask, interlocutor tavern runner, and was labeled CORRECT. Generation 1 (“the guard captain says”) was rejected as the wrong interlocutor. Generation 2 (“The guard captain narrows their eyes… they say”) was sealed. The speaker pattern only matched a name immediately before says/replies/answers. “Narrows” plus a later “they say” produced no conflicting speaker. Manual FAIL.

Corrected: the communicative subject of narrows/shrugs/shakes is the speaker, and a following “they” resolves to that name. The captain line is `wrong_interlocutor`. Both attempts rejected, so the sealed text is safe nonresolution and does not contain the captain. The name is not rewritten in place.

## 8. B9 forensic trace

The model named a noble house and the Ash Cowl. `guard_gm_output` ran before `run_preserve_if_valid`. The existing keyword list matched “noble house” and, on a strict social route, substituted the catalog grimace. C18 then sealed that grimace as the initial generation. C18 did not rewrite after the seal. The culprit is pre-seal catalog replacement.

Corrected: when the C18 lifecycle applies, the original candidate is kept and the leak reasons are attached. `run_preserve_if_valid` rejects it as hidden information and allows one regeneration. The grimace is not substituted. Non-lifecycle callers still get the old sanitizer behavior.

## 9. C8 forensic trace

The player looked into a knot of guards and refugees. The contract became ask because “face” and “who” were treated as an address, “they lingered on” was stored as a person, and “look into” was not perception. Generation 1 was the wrong interlocutor. Generation 2 attributed a shrug-and-quote to the ragged stranger without matching the says-pattern, so it sealed. Manual FAIL. The contract was wrong, the span was not a person, and the speaker check missed the shrug.

Corrected contract: perceive. “They lingered on” is not proposed. Quoted stranger speech on a look is `unsolicited_npc_speech`.

## 10. Speaker / addressee root causes

Three mechanisms, not one. B2: speaker extraction missed the person who narrows/shrugs and then says “they”. B9: a content leak was replaced by a catalog line before the immutable boundary. C8: a look was classified as an ask and a clause was bound as the addressee, so a stranger quote could seal. An ask whose discourse pointer was empty also failed to constrain a canonically bound interlocutor; the bound label is now the speaker constraint for asks.

## 11. Speaker integrity repair

Player, target, and speaker stay distinct. An ask with a bound interlocutor rejects a different person as the one who says, replies, narrows, shrugs, or shakes and then speaks. Identity uses catalog ids when both sides resolve, so “the guard” and “guard captain” are not a false conflict. A head-shake without a quote stays valid. Inspect, perceive, look, and ordinary act reject quoted or verb-attributed NPC speech unless the contract itself is an ask. The whole candidate is rejected. One regeneration under the same contract. No post-seal name rewrite.

## 12. Malformed incidental-person examples

Collected from the gate turns:

| Turn | Span | Persisted | Player-visible effect |
| --- | --- | --- | --- |
| A5 | exact coin modest fee so i | yes | pass; generation compensated |
| A9 | first local i pass | yes | runner answered a new local |
| B5 | i lean in | yes | pass; label stuck in later discourse |
| C2 | for crate yards | yes | pass after retry |
| C8 | they lingered on | yes | look became stranger speech |
| D3 | underbrush for whatever is moving out there | yes | inspection collapsed |
| D7 | still patch brush at steady pace | yes | evasive-figure failure |

All were fast-path address captures. The validator accepted them because a capture existed and the head was not on a short inanimate list. They were not written into scene clues. Unsupported consequential entities remained 0.

## 13. Incidental extraction root cause

A regex nominal was treated as a person whenever `person_shaped` did not reject the head. Clause tails, pronouns, preposition starts, and abstract nouns all passed. The interpreter label was not required to be a referential nominal.

## 14. Incidental candidate validation repair

`referential_person_nominal` runs before scene plausibility, consequence, and PR-BN. It keeps a determiner-led person phrase (porter, cloth merchant, tired porter, woman, travelers, stable hand) and rejects clause cuts, pronouns, preposition starts, finite verbs, abstract heads, and participial tails. A rejected span does not restore the previous interlocutor, does not persist, and does not change operation or dimension. Inspect and perceive survive a bad target span. Consequential roles such as “the spy working for the Ash Compact” still reach the C20 rejection instead of being dropped as non-entities.

## 15. D1 forensic trace

The player read the notice board for names, places, and how recent the ink was. The contract was a correct inspect. The generation stated that the roster lists the patrol leader as Eldrin Voss, posted this morning. Hard validation accepted it. The name is not in the authored patrol clue. It was not written into the clue list. It was in the transcript only. Manual FAIL. The classifier had no role-identity family, so a proper name plus a consequential office was ordinary color.

## 16. Consequential identity authority repair

A proper name is consequential when the same span identifies that name with a consequential role (missing patrol leader, murderer, Ash Compact spy, faction leader, an official who issued an order) using an identification verb. Ungrounded world-truth assertions use the existing C19 consequential path: hard-invalid, one regeneration, no in-place name strip and no rewrite into a rumor.

## 17. Grounded, rumor, and bounded-name controls

Hearsay (“I heard the patrol leader was called Voss”) stays an NPC claim and is not an unauthorized rule. “I’m Mara” from an incidental person, with no consequential role, is not this family. The same identity is allowed when the authored corpus contains both the role and the name. “The patrol leader is late” is not an identity assertion.

## 18. Incorrect-contract outcome map

Sixteen incorrect contracts: A5, A8, A10, B5, B9, C2, C4, C8, C10, D2, D3, D5, D6, D7, D8, D9. See `incorrect_contract_map.json`.

## 19. Six failure-producing contracts

B9, C8, C10, D3, D7, D8. B9, C8, C10, and D3 are families A, B, and C above. B2 and D1 failed gameplay with CORRECT contracts, so they are not in this six. They are the speaker check and the identity check.

## 20. Deliberately unfixed contract debt

Ten incorrect contracts still played and did not violate an invariant: A5, A8, A10, B5, C2, C4, D2, D5, D6, D9. Left as debt. D7 and D8 are one persona’s evasive figure (a shadow that is neither person nor animal). That pattern is not shared by a second persona. No fifth workstream.

No separate recurrent causal contract mechanism beyond A–D. Broad contract-perfection rewrite: not performed.

## 21. Mandatory replay results

C10, D3, B2, B9, C8, and D1 are covered by `tests/test_pr_br_continuation21_subject_integrity.py`, plus the malformed spans from A, B, C, and D. C18 accepted/emitted equality holds on those paths. Replaying the 32 previously successful gate emissions under the stored contracts newly rejects only B8, and only because that stored discourse label is the old fragment “i lean in”. Under a reconstructed contract the runner’s answer is valid. Count of previously successful turns newly broken by the repair: 0. B9’s historical grimace still matches the old, wrongly bound stranger contract; the repair stops the substitution before the seal rather than rejecting the grimace after the fact. C10’s historical wear sentence is now incomplete under the corrected contract.

## 22. Inspection regressions

I1 door condition complete. I2 wear complete. I3 sound complete, and wear-only is incomplete. I4 use complete. I5 markings complete. I6 dimensionless safe line does not invent wear. Sound safe line names sound.

## 23. Speaker regressions

S1 other NPC answers: hard-invalid, retry under the same contract. S2 head-shake: valid. S3 courtyard look plus stranger quote: hard-invalid. S4 the bound addressee remains the constraint when another NPC is nearby. S5 an incidental porter may answer.

## 24. Incidental-extraction regressions

E1 porter binds. E2 “tired porter carrying two crates” stays the porter. E3 a trailing question is cut. E4 no person invented from a bare action clause. E5 “him” inherits and is not a new entity. E6 patrol, rumor, and price are not people.

## 25. Identity-authority regressions

A1/A6 mundane self-name is not an unauthorized rule. A2 ungrounded patrol-leader identity is hard-invalid. A3 grounded identity is allowed. A4 hearsay stays a claim. A5 “Mara is the Ash Compact spy” is hard-invalid.

## 26. C18 regression status

`tests/test_pr_br_continuation18_immutable_boundary.py` passed. Accepted text remains the emitted text. Speaker feedback names `wrong_interlocutor` and does not rewrite the sentence.

## 27. C19 regression status

`tests/test_pr_br_continuation19_hard_authority.py` passed. Unsupported rules stay blocked. Grounded rules, rumors-as-claims, and bounded detail stay available. The new identity family uses that same path.

## 28. C20 regression status

`tests/test_pr_br_continuation20_incidental_entity.py` passed. Plausible incidentals bind. Pronouns inherit. Consequential roles are rejected. A malformed bind does not restore the previous NPC.

## 29. Broader regression status

Also passed: resolution contract, interaction completion, interpretation proposal, model interpretation, and continuations 13–16. Focused band: 127 passed, 0 failed. Full suite was not run.

## 30. Raw `/api/chat` stub results

PASS. Ten cases through `TestClient` with `call_gpt` stubbed: valid door inspection accepted unchanged; listen answered with wear retried into a sound answer; captain speech while the runner was addressed rejected and retried; a head-shake accepted; a courtyard look with stranger speech not emitted; a porter bound and allowed to answer; an underbrush clause not instantiated; an ungrounded roster identity not emitted; a rumored name kept as a claim.

## 31. Focused live transcript

Stamp `20261002T101405Z`. One isolated session. Six completed turns. No repair and no rerun. Player model saw only the opening and later player-visible replies. Transcript: `live/20261002T101405Z/visible.md`.

The player asked the ragged stranger, then the gate serjeant, then the tavern runner twice, walked into the market, and asked after an innkeeper. The innkeeper was absent and no substitute speaker answered.

## 32. Live manual review

Player-visible manual pass: 6/6. Turns 1–4 are answered by the person addressed. Turn 5 resolves the walk into the market. Turn 6 does not invent an innkeeper. Offline evaluator marked turns 4–6 FAIL; that scorer is not the manual metric.

## 33. Accepted / emitted equality

6/6 semantic matches. All six provenance values are initial generation. No post-seal rewrite.

## 34. Authority review

Unauthorized authoritative rules on emitted text: 0. The patrol rumor stayed in the runner’s mouth as talk, and the authored muddy-footprints clue was the clue that surfaced. No roster identity was invented.

## 35. Incidental entity review

Turns 1–4 bound canonical NPCs. Turn 6 did not instantiate the innkeeper. Turn 5 bound the span “the inn to see” as incidental person `inc_ec1197ac5e`, label “inn to see”. That is a place plus an infinitive, not a person. It did not speak, and it did not change the market narration, but it persisted. This is the same extraction family as the gate fragments, on a shape the fixtures did not cover: a purpose infinitive whose head is not on the inanimate list.

## 36. Discourse review

Interlocutors moved from the stranger to the serjeant to the runner and stayed with the runner across the follow-up. Turn 5’s explicit new span suppressed that interlocutor by storing the inn fragment. Turn 6 is unresolved rather than a return to the runner. No stale-interlocutor fallback flag fired.

## 37. Model / API cost accounting

Opening generation calls: 1. Gameplay generation calls: 6. Interpretation calls: 1. Retry generation calls: 0. Player-model calls (transcript only, `gpt-4.1-mini`): 6. Evaluator-model calls: 0. Gameplay route: `gpt-4.1-mini`. A first preflight attempt found no cached probe and spent no gameplay calls. The recorded session ran after a healthy probe.

## 38. Residual failure families

One narrow residual: infinitive or place spans such as “the inn to see” can still pass the referential check and persist as an incidental person. D7/D8 evasive-figure generation remains deferred. Ten incorrect contracts that still played remain debt.

## 39. Readiness decision

C21 REPAIR INCOMPLETE — NARROW DEFECT REMAINS.

The inspection collapse, the wear fallback, the three speaker paths, the gate’s clause fragments, and the ungrounded patrol-leader identity are repaired under deterministic tests and the stubbed request path. The focused live session did not reopen C18, did not emit a wrong speaker, and did not emit an unsupported identity. It did instantiate one non-person incidental. That misses the live success target. Another 4×10 gate is not authorized from this result. No further repair or rerun was performed inside C21.

## 40. PR-BR status

PR-BR remains OPEN. Controlled human playtest: NOT AUTHORIZED. Full synthetic gate: NOT RUN. Semantic repair or rerun of the live session: NO. PR-BS was not started.

# PR-BR C21 Continuation 2 — Incidental Referential-Nominal Closure

## 1. Purpose

Close only the residual where a non-person span can still pass `referential_person_nominal` and persist as an incidental person. Incidental people stay generative. No occupation whitelist. No second 4×10 gate, no smoke, no human playtest, no PR-BS.

## 2. C21 authorization basis

C21 focused live validation was 6/6 manual pass, with 0 wrong-speaker accepts, 0 unsupported consequential identities, 0 accepted/emitted mismatches, and 0 retries. C18, C19, and C20 stayed healthy. Turn 5 still persisted “the inn to see” as incidental person `inc_ec1197ac5e`. That blocked a second 4×10 gate.

## 3. C21 live Turn 5 forensic trace

Interpretation was not invoked. `_ADDRESS_RE` treated `find` as an address verb. `_complement_cut` stopped at `if`, leaving span `the inn to see`. `referential_person_nominal` returned `inn to see`. Scene population was populated. PR-BN accepted. The entity was stored and became the discourse interlocutor. It did not speak. Full trace: `artifacts/pr_br_continuation21b/FORENSICS.md`.

## 4. Historical malformed candidates

Eight persisted person records: `exact coin modest fee so i`, `first local i pass`, `i lean in`, `for crate yards`, `they lingered on`, `underbrush for whatever is moving out there`, `still patch brush at steady pace`, `the inn to see`. Five further captures were not stored as incidental people: `the gate`, `the crowded gate`, `the quieter fringe of the square`, `the crowd`, `here at Cinderwa`.

## 5. Mechanism clustering

One family. Address capture keeps a tail through a purpose infinitive or a clause. The old head was the last content word, so `to` vanished and `see` became the head. Personhood was a negative list: a head absent from a short inanimate list was a person. `inn`, `market`, `room`, and `tavern` were not on that list. Clause, pronoun, and preposition fragments were the same family and were already rejected by the C21 check.

## 6. Referential nominal versus personhood

`referential_nominal` may return a place or object (`inn`, `gate`, `board`). `referential_person_nominal` returns a phrase only when the semantic head denotes a person. A model span is rechecked by the same function. Saying “person” does not bypass it.

## 7. Semantic-head implementation

Infinitives (`to see`, `to speak with`), participles (`carrying`, `sweeping`, `waiting`), locative tails (`by the gate`, `near the wagon`), and `of` complements that leave a noun (`commander of the hidden rebel cell`) are removed before the head is read. A player-pronoun finite clause (`I pass`) abstains. A `who` relative is cut. Known place, object, route, abstract, and action heads are not people. An unknown common-noun head can still be a person. That is not an occupation whitelist.

## 8. Infinitive handling

`the merchant to ask` stays `merchant`. `the inn to see`, `the gate to inspect`, `the market to find`, `the board to read`, `the road to follow`, `the crate to examine`, `the room to search`, and `the tavern to visit` are not people. The place nominal remains available.

## 9. Participial modifier handling

`the tired porter carrying crates` stays `tired porter`. `the woman sweeping the steps` stays `woman`. `the traveler waiting by the wall` stays `traveler`.

## 10. Prepositional modifier handling

`the porter by the gate`, `the guard near the wagon`, `the innkeeper behind the counter`, and `the traveler from the north road` stay people. `for crate yards` and the underbrush clause do not.

## 11. Pronoun handling

`him` is not an entity. `I ask him` after a bound porter keeps that porter.

## 12. Clause-fragment rejection

`i lean in`, `they lingered on`, `for crate yards`, `underbrush for whatever is moving out there`, `exact coin modest fee so i`, `first local i pass`, and `still patch brush at steady pace` are not people.

## 13. Valid incidental controls

Simple people, modified people, person-plus-infinitive, and an unknown role (`a cooper`, `the sentry beside the wagon`) pass. Consequential roles such as the spy working for the Ash Compact still reach rejection rather than being dropped as non-entities.

## 14. Invalid non-person controls

Bare places and objects, and those same heads plus an infinitive, fail as people and remain nominals. `I read the notice board` stays an inspection, not an incidental person.

## 15. Historical replay

15/15 recorded malformed strings are not person candidates. 8/8 historical player turns do not persist those labels. The C21 Turn 5 sentence does not persist `inn to see`.

## 16. C18 regression

`tests/test_pr_br_continuation18_immutable_boundary.py` passed. Accepted text remains the emitted text.

## 17. C19 regression

`tests/test_pr_br_continuation19_hard_authority.py` passed.

## 18. C20 regression

`tests/test_pr_br_continuation20_incidental_entity.py` passed. Plausible incidentals bind. Pronouns inherit. Consequential roles are rejected.

## 19. C21 regression

`tests/test_pr_br_continuation21_subject_integrity.py` passed: inspection, speaker integrity, and consequential identity.

## 20. Raw `/api/chat` stub

PASS. Head-to-inn does not create `the inn to see`. Innkeeper and tired porter bind. Gate, road, and board do not become people. A new porter replaces the runner. A following underbrush span does not restore that porter and does not persist.

## 21. Fresh 3-turn transcript

Stamp `20261002T111028Z`. One isolated session. Three completed turns. No repair and no rerun. Transcript: `artifacts/pr_br_continuation21b/live/20261002T111028Z/visible.md`.

The player asked the tavern runner about the missing patrol, asked a follow-up, then turned toward the muddy lane to inspect the footprints. Turns 1 and 2 were answered by the runner. Turn 3 described the milestone and the mud.

## 22. Live candidate and binding review

Turns 1 and 2 bound the canonical tavern runner. No incidental person was proposed. Turn 3 bound incidental `inc_d06766ba95`, label `muddy lane northwest`, span `the muddy lane northwest of the crates`, head `northwest`, reasons `scene:populated` and `pr_bn:accepted`. That is a route, not a person. It was stored and became the discourse interlocutor on `old_milestone`.

## 23. Live manual review

Player-visible manual pass: 2/3. Turns 1 and 2 answer the person who was asked, and the footprint clue stays in the runner’s mouth. Turn 3 fails. The player was inspecting footprints before deciding whether to go to the milestone. The reply places them at the milestone, and the stored interlocutor is the lane.

## 24. State and discourse review

The runner held turns 1 and 2. Turn 3 replaced that pointer with the lane entity. This was not a stale-interlocutor fallback after a rejection. The span was accepted. No rejected candidate was stored. Accepted text matched emitted text on all three turns. Unauthorized authoritative rules on emitted text: 0.

## 25. Model and API cost

Opening generation calls: 1. Gameplay initial-generation calls: 3. Gameplay retry-generation calls: 0. Interpretation calls: 0. Player-model calls: 3. Evaluator-model calls: 0. Preflight used the cached healthy probe and spent no new gameplay call. Route: `gpt-4.1-mini`.

## 26. Residual defects

The head is still the last remaining content word. In `the muddy lane northwest of the crates`, stripping `of the crates` leaves `northwest` as the head. `northwest` is not classified as a place, so the route is a person. Direction or other postnominal modifiers can still hide the noun. The early stop did not fire, because it uses the same check that accepted the span.

## 27. Readiness decision

CLOSURE INCOMPLETE — MALFORMED INCIDENTAL-PERSON BOUNDARY STILL LEAKS.

The deterministic matrix, the historical replays, and the stubbed request path reject `the inn to see` and the recorded gate fragments. The fresh live session instantiated one new non-person, `muddy lane northwest`. A second 4×10 gate is not authorized. No further repair or rerun was performed.

## 28. PR-BR status

PR-BR remains OPEN. Human playtest: NOT AUTHORIZED. Second full 4×10 gate: NOT RUN. PR-BS was not started.

# PR-BR C21 Continuation 3 — Referential Head Resolution

## 1. Purpose

Stop treating the last remaining content word as the thing a noun phrase denotes. The referential head is the noun at the right edge of the prenominal cluster. Personhood is judged on that noun. This is not C22, not a parser rewrite, and not another 4×10 gate.

## 2. Authorization basis

Continuation 2 rejected `the inn to see` and the recorded gate fragments, and the broader band was 180/180. A fresh three-turn session then stored `muddy lane northwest` as an incidental person because the head was `northwest`. That session is not closed. A second 4×10 was not authorized.

## 3. Continuation 2 failure forensic trace

Full trace: `artifacts/pr_br_continuation21c/FORENSICS.md`.

Raw input asked to inspect footprints on the muddy lane and only then decide whether to follow the road. The address capture kept `the muddy lane northwest of the crates`. Stripping `of the crates` left `northwest` as the last content word. It was not on the non-person list, so personhood passed. Entity `inc_d06766ba95`, label `muddy lane northwest`, was stored and became the discourse interlocutor on `old_milestone`. It did not speak.

## 4. Last-content-word root cause

`_raw_head` was `words[-1]` after modifier stripping. A postnominal locative that is not a preposition survived the strip and became the head. The assumption “last remaining content word = referential head” is removed.

## 5. Referential-head design

The cluster stops at the first postnominal boundary: preposition, relative, infinitive, participle with a complement, locative adjunct after a noun, or a second determined conjunct. The head is the right-edge noun of what remains. Compounds stay head-final. `stable hand` keeps both words because `hand` alone is not a person.

## 6. Implementation

`game/incidental_entity.py` (`referential_head`, `personhood_of_span`). `game/interaction_completion.py` recovers a person in `to see if the innkeeper` without treating `the inn to see` as a person. Summary: `artifacts/pr_br_continuation21c/IMPLEMENTATION.md`.

## 7. Compound-noun handling

`gate guard` denotes `guard`. `cloth merchant`, `caravan master`, and `tavern keeper` stay people. `stable hand` is kept as a compound. `notice board` denotes `board` and is not a person. `hand` alone is not a person.

## 8. Prepositional-modifier handling

`the porter by the gate` denotes `porter`. `the innkeeper behind the counter` denotes `innkeeper`. `the wagon beside the wall` denotes `wagon`. `the lane northwest of the crates` denotes `lane`.

## 9. Participial-modifier handling

`carrying`, `sweeping`, `waiting`, and `blocking` do not become the head. `the woman sweeping the steps` denotes `woman`. `the wagon blocking the road` denotes `wagon`.

## 10. Infinitive-modifier handling

`the merchant to ask` denotes `merchant`. `the inn to see`, `the gate to inspect`, and `the road to follow` are not people.

## 11. Relative-clause handling

`the porter who carried the crates` denotes `porter`. `the wagon that blocked the road` denotes `wagon`. A leading `that porter` stays a determiner, not a relative cut.

## 12. Directional-modifier handling

`northwest` and `upstairs` are locative adjuncts after the noun. They are not selected as the head. They were not added to the non-person list.

## 13. Unknown-personhood behavior

An identifiable head whose personhood cannot be told abstains (`proposal:personhood_unresolved`). It is not stored. It does not restore the previous interlocutor. `the beadle` abstains. `the lamplighter` is accepted by agentive shape, not by an occupation list. `lane` is unknown and is not a person. `northwest` never becomes the head.

## 14. Structured-interpreter boundary

A proposed person span is rechecked by `referential_person_nominal`. A model label does not override a non-person or unknown head. The live Turn 3 interpretation call did not create an entity.

## 15. Vocabulary additions

Non-person list additions: 0. `lane` and `northwest` were not added. Social-category forms, for roles with no agentive ending: 18 (`woman`, `man`, `guard`, `merchant`, `sentry`, `spy`, `wizard`, `assassin`, `patron`, `magistrate`, `child`, `boy`, `girl`, `person`, `captain`, `stranger`, plus the plurals `women` and `men`). That set is not how the lane phrase was fixed.

## 16. Historical malformed replay

22/22 recorded malformed strings are not people. 9/9 historical player turns do not persist them.

## 17. Valid-person controls

15/15.

## 18. Non-person controls

13/13. Each remains a nominal. None is a person.

## 19. Structural variation

Pass. Covered stacked adjectives, compound person and object, preposition, participle, infinitive, relative, direction, possessive, demonstrative, indefinite article, and coordination. `the inn and the porter` has no single head.

## 20. Player-input integration

J1–J8 pass. The lane, road, wagon, and underbrush do not become people. The porter, innkeeper, woman, and merchant do. `the inn to see` is not a person beside the innkeeper.

## 21. Turn-3 action-resolution replay

With the head repair, the original sentence does not bind a person. Head `lane`. Reason `proposal:personhood_unresolved`. The runner is not restored. The world-action parser still returns `scene_transition` to `old_milestone` on lane `authored_exit_resolution`.

The same sentence without `before deciding whether to follow the road toward the old milestone` is an inspection of the footprints. That conditional clause alone resolves to `old_milestone`. The move is not caused by the lane binding. It is a separate exit binder treating an uncommitted `whether to follow` as current travel. This continuation does not change that binder.

## 22. C18 regression

`tests/test_pr_br_continuation18_immutable_boundary.py` passed inside the 270. Live accepted text matched emitted text on all three turns.

## 23. C19 regression

`tests/test_pr_br_continuation19_hard_authority.py` passed. Live Turn 1 rejected an invented curfew tightening and did not emit it.

## 24. C20 regression

`tests/test_pr_br_continuation20_incidental_entity.py` passed. Plausible incidentals still bind. A rejected lane does not restore the previous interlocutor.

## 25. C21 regression

`tests/test_pr_br_continuation21_subject_integrity.py` passed: inspection, speaker integrity, and consequential identity.

## 26. Continuation 2 regression

`tests/test_pr_br_continuation21b_referential_personhood.py` passed. `the inn to see` stays rejected.

## 27. Raw `/api/chat` stub

Pass. Lane is not a person and does not restore the porter. Porter, woman, merchant, and innkeeper bind. The inn is not `inn to see`. Wagon and road are not people. Accepted text matched emitted text on the lane turn.

## 28. Fresh 3-turn transcript

Stamp `20261003T110414Z`. Transcript: `artifacts/pr_br_continuation21c/live/20261003T110414Z/visible.md`.

The player asked the tavern runner for stew and rumors, asked again, then turned to the guard serjeant. No repair and no rerun.

## 29. Live referential-head telemetry

Turn 1: head `runner`, person, canonical. Turn 2: head `runner`, person, canonical. Turn 3: span `the guard serjeant near the roster to ask`, head `serjeant`, personhood unknown, binding `ambiguous`, no entity stored.

## 30. Live entity and binding review

Incidental entities instantiated: 0. Non-person stored as a person: 0. Stale-interlocutor fallback: 0. The runner was cleared on the ambiguous serjeant address and was not put back. Rejected-candidate commits: 0.

## 31. Live manual review

1/3. Turn 1 fails: both drafts were rejected for consequential invention, and the sealed line is the sound-inspection fallback. Turn 2 passes: the runner answers and points at the serjeant. Turn 3 fails: the captain speaks, while the address stayed ambiguous and no person was created. Detail: `artifacts/pr_br_continuation21c/MANUAL_REVIEW.md`.

## 32. Discourse and state review

The runner held turns 1 and 2. Turn 3 left the interlocutor empty. Scene stayed `frontier_gate`. Accepted text matched emitted text on every turn. Unauthorized authoritative rules on emitted text: 0.

## 33. Model and API cost

Opening generation calls: 1. Gameplay initial-generation calls: 3. Gameplay retry-generation calls: 2. Interpretation calls: 1. Player-model calls: 3. Evaluator-model calls: 0. Route: `gpt-4.1-mini`. Turns 1 and 2 used the two-attempt ceiling. Turn 3 used one attempt. Preflight used the cached healthy probe.

## 34. Residual defects

The conditional-travel defect remains. `before deciding whether to follow the road toward the old milestone` is enough for the authored-exit binder to move the player to `old_milestone`. It is not coupled to referential-head extraction.

Live Turn 3 still captured `near the roster to ask` inside the address span. The head of that span is `serjeant`, and no person was stored, but catalog matching stayed ambiguous and the captain spoke.

`serjeant` is an unknown head. A unique catalog match can still bind it. This session did not get a unique match.

## 35. Readiness decision

The Continuation 2 leak did not recur. Manual gameplay is 1/3, below the 2/3 bar, for reasons outside that leak. A second full 4×10 is not authorized.

## 36. PR-BR status

PR-BR remains OPEN. Human playtest: NOT AUTHORIZED. Second full 4×10 gate: NOT RUN. PR-BS was not started. No completion commit. No push.


