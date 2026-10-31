# PR-BR Second Limited Live Validation — Fresh Generalization

Measurement only. No production edits after the probes started. No failed-turn reruns. No 4×10 gate. No continuous playtest. No PR-BS. No commit. No push.

Run stamp: `20261003T190253Z`
Workspace HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
The run executed the current workspace, including the uncommitted decision-layer repair already present. This cycle did not change those modules.

Evidence directory: `artifacts/pr_br_second_live_validation/20261003T190253Z/`

Domains are Ashford, a hill town of mills, cisterns, yards, and a ferry slip. The probes do not reuse the kiln, the Violet Compact, the dye vat, the chapel bell, Pell, or the reed drying loft.

Probe 7 starts with Mirelle already engaged, because the known scene-transition failures are mixed social-and-travel lines under an existing social engagement. The names, the warning, and the courtyard are new. The fixture wording from `test_scene_transition_authority.py` was not copied.

## 1. Executive conclusion

The attachment repair holds on this fresh population. Every turn had a Resolution Contract and a `GMResolutionDecision`, and every `decision.contract_id` matched `contract.contract_id`. That includes the prebuilt social turns and both movement turns, which were the routes that skipped the decision in the first live validation.

The old sentence-local negation failure did not recur. A polar “not locked” answer kept the authorized “full” cistern. A multi-sentence wagon inspection distributed missing spokes, a torn cover, and a coil of rope across sentences and was accepted. The one retry note carried the contract, the decision, and the validation failure. The generic line “No one here can answer that from what is settled here” was not emitted.

Three localized defects remain:

1. On the sluice, the model said the cause, the time, and the actor remain unseen. Validation rejected that sentence as `unauthorized_qualifier:location` because “when it happened” sits within 48 characters of “here.” Bounded preservation deleted that sentence and kept a hedged lead about a missing patrol’s notice.

2. Both movement decisions record `permitted_state_mutations: []` and `consequentially_unresolved`, while the travel resolver commits the destination. On the sail loft, narration arrives correctly and then restates the departure stair as a route that still leads upward.

3. The mixed thanks-and-courtyard line became a travel contract. Movement occurred, so the known “social resolver blocks travel” pattern did not reproduce. The thanks itself was dropped with the social clause.

Manual result: **5 PASS / 3 FAIL.**

## 2. Eight-turn PASS/FAIL table

| Turn | Probe | Resolver | Decision | Player-facing result | Manual |
| --- | --- | --- | --- | --- | --- |
| 1 | Jammed sluice, unknown cause | social | Present. `established_or_retrieved`. Qualifier `cause`. Ids match. | Jam and spilling water kept. Unknown-cause sentence removed. Missing-patrol lead kept. | FAIL |
| 2 | Sedge and the Harbor Guild | social | Present. `epistemically_qualified`. Ids match. | Rumor frame. Guild not committed. | PASS |
| 3 | Full cistern, asked if locked | social | Present. `derived_denial` for `locked`. Ids match. | “Not locked,” and still full. | PASS |
| 4 | Timber wagon inspection | exploration | Present. `established_or_retrieved`. Ids match. | Spokes, torn cover, and rope across sentences. | PASS |
| 5 | Osric, lantern-tender | social | Present. `epistemically_qualified`. Ids match. | Ordinary evening mood. No new institution. | PASS |
| 6 | Go to the sail loft | travel | Present. `consequentially_unresolved`. Ids match. Mutations empty. | Arrives in `sail_loft`. Stair still “leads upward.” | FAIL |
| 7 | Thank Mirelle, then the eastern courtyard | travel | Present. `consequentially_unresolved`. Ids match. Mutations empty. | Arrives in `eastern_courtyard`. Thanks omitted. | FAIL |
| 8 | Empty ink pot and the scribes’ college | social | Present. `established_or_retrieved`. Ids match. | Pot is empty. College purchase denied. | PASS |

## 3. Exact PASS count

**5 PASS, 3 FAIL.**

PASS: turns 2, 3, 4, 5, 8.
FAIL: turns 1, 6, 7.

## 4. Exact API/model call count

| Kind | Count |
| --- | --- |
| Gameplay turns | 8 |
| Initial generation calls | 8 |
| Retry generation calls | 1 |
| Interpretation calls | 1 |
| Preflight calls | 1 |
| Total model/API calls | 11 |

The retry is turn 1, purpose `retry_escalation`, reason `hard_invalid`. The interpretation call is turn 8. The preflight is the startup check, `health_class=healthy`. No evaluator-model calls. No reruns. Logged route model: `gpt-4.1-mini`.

## 5. Decision-presence matrix

Invariant for every ordinary generated-resolution probe: contract present, decision present, `decision.contract_id` equals `contract.contract_id`.

| Turn | Contract id | Decision | Id match | Outcome |
| --- | --- | --- | --- | --- |
| 1 | `rc_8252c9bea2b9` | Present | Yes | `established_or_retrieved` |
| 2 | `rc_983ea52adf7e` | Present | Yes | `epistemically_qualified` |
| 3 | `rc_0fde9c4bb196` | Present | Yes | `established_or_retrieved` |
| 4 | `rc_3f7f479d7d62` | Present | Yes | `established_or_retrieved` |
| 5 | `rc_78f77f7a769b` | Present | Yes | `epistemically_qualified` |
| 6 | `rc_2a0365ba3ddf` | Present | Yes | `consequentially_unresolved` |
| 7 | `rc_6ff0fda95ff8` | Present | Yes | `consequentially_unresolved` |
| 8 | `rc_60b5c3e0c0a5` | Present | Yes | `established_or_retrieved` |

**8 / 8 satisfy the invariant.** No turn fails on a missing decision.

Prompt flags match that matrix. Every initial generation payload contained `resolution_contract` and `gm_resolution_decision`. The turn 1 retry note contained both, plus `AUTHORITATIVE RETRY CONTEXT` and `validation_failure`.

## 6. Resolver-selection matrix

| Turn | Operation | Subject | Selected resolver | Resolution kind | Scene after |
| --- | --- | --- | --- | --- | --- |
| 1 | `ask` | social | social | none | `mill_race` |
| 2 | `ask` | social | social | `question` | `cooper_yard` |
| 3 | `ask` | social | social | none | `orchard_cistern` |
| 4 | `inspect` | perception | exploration | `investigate` | `timber_yard` |
| 5 | `ask` | social | social | `question` | `ferry_slip` |
| 6 | `act` | travel | travel | `scene_transition` | `sail_loft` |
| 7 | `act` | travel | travel | `scene_transition` | `eastern_courtyard` |
| 8 | `ask` | social | social | none | `ink_stall` |

Turns 1 and 3 are physical questions contracted as social asks. The answers were still governed by the attached decision. Turn 4 is the inspection, and exploration owned it. Turns 6 and 7 are travel. `select_ordinary_resolver` followed the contract subject in every case.

## 7. Per-turn pipeline traces

### Turn 1 — Established condition, unknown cause — FAIL

- Initial state: `mill_race`. Structured fact: the oak sluice gate is jammed halfway open and water pours over the lower boards. Identity: subject `sluice_gate`, relation `condition`, value `jammed`, polarity `positive`. No cause, actor, or time.
- Player: “What happened to the sluice gate?”
- Contract `rc_8252c9bea2b9`: operation `ask`, subject `social`, expected `answer`, construction `deterministic`, commitment `executed_now`. Obligation kind `question`, mode `clarification_target_failure`, subject the sluice question, no interlocutor. Live mode `grounded_information_request`.
- Resolver: `social`.
- Decision: present, same contract id. Outcome `established_or_retrieved`. Unresolved qualifier `cause`. Answer relations empty. Permitted mutations empty. Constraints include “Cause, actor, and time may be called unknown.”
- Proposed facts: the jammed-gate sentence (`world_truth`, `authored_world_fact`) and the unstructured water sentence (`world_truth`).
- Generation 1 (`primary_turn`, retry 0, prompt 103,940 characters, contract and decision present): the gate is jammed halfway open; water spills over the lower boards; “What caused it to jam, when it happened, and who might be responsible remain unseen here.” Then a lead: compare the disruption with “the missing patrol’s notice,” or seek witnesses who noticed the condition “earlier today.”
- Validation attempt 1: `hard_valid` false, reason `unauthorized_resolution_decision_fact`. The only violation is the “remain unseen here” sentence, code `unauthorized_qualifier:location`. The patrol sentence was labeled `npc_claim` / `claim_only` / `epistemically_qualified` and was not a violation.
- Retry: purpose `retry_escalation`, reason `hard_invalid`, prompt 2,675 characters. The note contains the contract, the decision, the unresolved `cause` qualifier, and the violating sentence. Generation 2 `player_facing_text` is empty. Attempt 2 reasons: `malformed_or_truncated`. Decision audit on that empty text is vacuously `hard_valid` with no violations.
- Bounded preservation then dropped the flagged sentence from attempt 1 and sealed the remainder as `initial_generation`, acceptance why `bounded_sentence_preservation`.
- Emitted: the jam and the spilling water, then the missing-patrol lead. The unknown-cause sentence is gone.
- Commit: scene stayed `mill_race`. Factions, flags, event log, and improvisation ledger empty. Discourse claim null.
- Manual: FAIL. A competent GM would report the jam and say the cause, the actor, and the time are unknown. The model did that, then added an unrelated patrol notice. The player heard the jam and the patrol lead, and did not hear that the cause is unknown.
- First incorrect layer: **G. Semantic-fidelity validation.** The decision already authorized an unknown cause. The event-site pattern treats “when it happened … here” as a filled location. Secondary: **I** (preservation removed the valid sentence and kept the patrol lead) and **H** (the retry call returned no text). The patrol lead itself begins in generation (**F**), and validation did not flag it.

### Turn 2 — Prebuilt social contract, unsupported world fact — PASS

- Initial state: `cooper_yard`. Sedge fits hoops on barrels. No Harbor Guild, no quay order, no factions.
- Player: “I ask Sedge whether the Harbor Guild has closed the lower quay to outsiders.”
- Contract `rc_983ea52adf7e`: `ask` / social / answer, interlocutor path binds Sedge. Social kind `question`, `reply_kind` `answer`.
- Resolver: `social`.
- Decision: present and matched. Outcome `epistemically_qualified`. Proposed facts are the staves, the hoop work, and “Sedge exists as cooper.” No guild fact.
- Generation 1, accepted immediately, `strict_social`: Sedge cannot say for sure about the lower quay. “Rumors have been drifting that the Harbor Guild is tightening control down there.” No clear word on who is allowed. Ask someone who works the docks.
- Audit: the rumor sentences are `npc_claim` / `claim_only` / `explicit_testimony_nonassertion` or `epistemically_qualified`. Violations empty.
- Commit: scene `cooper_yard`. Factions, flags, and event log empty. Discourse interlocutor is Sedge. Active claim null. Ledger empty.
- Manual: PASS. The guild stays inside a rumor Sedge does not confirm. It does not become world truth. The answer is usable. “Someone who works the docks” is extra local color, the same class of soft blemish as the first validation’s dockworker redirect.

### Turn 3 — Negated unrelated predicate — PASS

- Initial state: `orchard_cistern`. Structured fact: the cistern is full to the rim. The lid rests beside it. Lock state is not authored.
- Player: “Is the cistern locked?”
- Contract `rc_0fde9c4bb196`: `ask` / social / answer. Resolver `social`.
- Decision: present and matched. Outcome `established_or_retrieved`. Answer relation: subject cistern, asked predicate `locked`, authorized values `full` / `full to the rim`, permitted polarity `negative`, kind `derived_denial`. Constraint: the asked predicate may be denied and may not be asserted.
- Generation 1, accepted: “The cistern is not locked; its lid rests on the ground beside the rim, and the cistern itself is full to the rim.”
- Audit: the sentence matches the authored full-cistern identity. Violations empty. `hard_valid` true.
- Commit unchanged. Ledger empty.
- Manual: PASS. Negation lands on locked. Full remains. The validator did not treat “not locked” as a contradiction of `full`.

### Turn 4 — Multi-sentence observation — PASS

- Initial state: `timber_yard`. Near wheel missing two spokes. Canvas cover torn along one seam. A coil of spare rope on the bed. No cause.
- Player: “I look over the timber wagon.”
- Contract `rc_3f7f479d7d62`: operation `inspect`, subject `perception`, expected answer. Resolver `exploration`. Kind `investigate`.
- Decision: present and matched. Outcome `established_or_retrieved`. Both structured conditions are `world_truth`. The rope is an unstructured `world_truth` fact.
- Generation 1, accepted, three sentences: the wheel is damaged with two spokes missing and looks unsteady; the cover has a tear along one seam, ragged and worn from use; a coil of spare rope sits on the bed.
- Audit: the wheel sentence matches the missing-spokes identity. The tear sentence is `bounded_incidental`. Violations empty.
- Commit: scene unchanged. Ledger empty, so “worn from use” was not written into scene canon.
- Manual: PASS. Observations are split across sentences. Naming the wagon is not treated as a new proposition. “Worn from use” is texture, classified incidental, and not a committed cause. No actor and no crime.

### Turn 5 — Background NPC and bounded improvisation — PASS

- Initial state: `ferry_slip`. Osric keeps the post lantern. No importance tag. No mood, no river condition, no institution.
- Player: “I ask the lantern-tender how the evening is treating him.”
- Contract `rc_78f77f7a769b`: `ask` / social, interlocutor `osric`, subject “how the evening is treating him.” Social `reply_kind` on the resolution is `refusal`, with a hint to narrate uncertainty without inventing facts. Resolver `social`.
- Decision: present and matched. Outcome `epistemically_qualified`. Facts are the lantern, Osric beside it, and “Osric exists as lantern-tender.”
- Generation 1, accepted, `strict_social`: a reserved line that the evening has seen better days, the work is steady, the river has been restless, and folks keep an uneasy eye on it. He shifts beside the lantern.
- Audit: the gesture sentence is `bounded_incidental`. Violations empty. No `[IMPORTANT]` marker.
- Commit: scene unchanged. Ledger empty. Factions empty. Discourse interlocutor is Osric. Claim null.
- Manual: PASS. He has a manner and a limit. Restless water and uneasy neighbors stay atmospheric. No guild, crime, shrine, or civic order is founded to make him interesting.

### Turn 6 — Clean authorized movement — FAIL

- Initial state: `rope_walk`, exit “Go to the sail loft” → `sail_loft`. Destination facts: cut canvas on pegs, swept floor, waxed-thread air.
- Player: “I go to the sail loft.”
- Contract `rc_2a0365ba3ddf`: operation `act`, subject `travel`, expected `action_outcome`. Resolver `travel`. Engine log: “Scene transition -> sail_loft.” Kind `scene_transition`, `resolved_transition` true, target `sail_loft`.
- Decision: present and matched. Outcome `consequentially_unresolved`. `permitted_state_mutations` is `[]`. Authorized facts are only the departure scene: coils of rope, and “A stair at the far end climbs to the sail loft.” Constraint: do not narrate a location change unless a location mutation is permitted, and the requested result remains unresolved unless the resolver or state authorizes it.
- Generation 1, accepted: arrival in the sail loft, canvas on pegs, swept floor, waxed thread. Then high windows, coils of rope along the adjacent covered walk, and “a sturdy stair leads upward, beckoning further exploration.”
- Audit: the rope-walk sentence is labeled `authored_world_fact` / `world_truth` with an empty semantic identity. Violations empty. The upward-stair sentence is not a violation.
- Commit: `active_scene_id` `sail_loft`, visited `rope_walk` then `sail_loft`. Ledger empty.
- Manual: FAIL. The resolver and the commit are right, and the loft’s canvas and floor are right. The stair that climbs to the loft is then told as a stair that still leads upward toward further exploration. That is an unauthored onward route. A competent GM would describe the loft the player has entered.
- First incorrect layer: **D. GMResolutionDecision content.** The decision does not record the location mutation the travel resolver committed, and the only authorized place-facts are the departure walk and its stair. Generation (**F**) then carries that stair into the loft as a new upward route. Validation (**G**) accepts it.

### Turn 7 — Mixed social and declared movement — FAIL

- Initial state: `cistern_steps`. Mirelle is engaged (`interaction_mode` social, `engagement_level` engaged). Authored warning: the steps are slick. Exit “Go to the eastern courtyard” → `eastern_courtyard`, with a dry stone trough against the mill wall.
- Player: “I thank Mirelle for the warning, then head for the eastern courtyard.”
- Contract `rc_6ff0fda95ff8`: operation `act`, subject `travel`, expected `action_outcome`. Obligation kind `action_request`, subject the whole utterance, interlocutor null. Resolver `travel`. Engine log: “Scene transition -> eastern_courtyard.” Kind `scene_transition`, target `eastern_courtyard`, `resolved_transition` true.
- Decision: present and matched. Outcome `consequentially_unresolved`. `permitted_state_mutations` is `[]`. Facts: the slick-step warning, the arch onto the courtyard, and “Mirelle exists as cistern keeper.”
- Generation 1, accepted: the player steps through the arch into the eastern courtyard. Paved yard, cistern house, mill wall, dry trough, dust, breeze, muffled mill sounds. No thanks to Mirelle.
- Audit: the courtyard sentences are `bounded_incidental`. Violations empty.
- Commit: `eastern_courtyard`. Visited `cistern_steps` then `eastern_courtyard`. Discourse interlocutor null. Ledger empty. Factions empty.
- Manual: FAIL. Travel was actionable and it happened. The thanks was not spoken and was not an obligation on the contract. A competent GM would acknowledge Mirelle and then arrive. This is not the social-resolver failure. Social content did not suppress the move. The contract kept only the move.
- First incorrect layer: **A. Resolution Contract / intent interpretation.** The mixed utterance was reduced to `act` / `travel` before resolver selection. The travel resolver then did what that contract says. Secondary: **F**, because the narration follows that single operation and omits the thanks. Family **B** does not apply: the selected resolver is `travel`, and the travel stage ran.

### Turn 8 — Mostly valid answer, consequential temptation — PASS

- Initial state: `ink_stall`. Structured fact: the ink pot is empty. A trimmed quill lies beside it. No buyer.
- Player: “Is there any ink left in the pot, and did the scribes’ college buy the last of it?”
- One interpretation call. The model proposed `ask`, subject “ink availability and purchase history,” expected information about remaining ink and a purchase by the college, `ambiguous` false. The stored contract is `ask` / social / answer, construction source `structured_interpretation`, contract `rc_60b5c3e0c0a5`.
- Resolver: `social`.
- Decision: present and matched. Outcome `established_or_retrieved`. Facts: empty pot (`ink_pot` / `empty` / positive) and the quill. No college fact. No derived-denial row, because the utterance is not a single polar predicate match.
- Generation 1, accepted: the pot is empty and the quill is beside it. No clear sign of who took the last of the ink. No visible indication that the scribes’ college was involved. A closer look at the quill might show recent use.
- Audit: the empty-pot sentence matches the authored identity. The quill suggestion is `claim_only`. Violations empty.
- Commit: scene unchanged. Factions, flags, event log, ledger, and discourse claim empty.
- Manual: PASS, path A. The initial narration answers from the empty pot and refuses the college purchase. The college stays inside the player’s question. Nothing consequential was committed.

## 8. Authority and provenance analysis

Authored structured rows became `authored_world_fact` / `world_truth` with the source identity intact when the decision ran: sluice `jammed`, cistern `full`, wagon `missing spokes`, ink `empty`.

NPC existence rows use kind `entity` (Sedge, Osric, Mirelle).

No turn wrote a faction, a world flag, or an event-log truth. Turn 2’s Harbor Guild and turn 8’s scribes’ college were not persisted. Turn 1’s patrol notice was not persisted. It was player-facing only, and the audit called it `claim_only`.

Turn 4’s “worn from use” and turn 5’s lantern gesture were audited as `bounded_incidental` / `runtime_incidental` and did not enter the improvisation ledger or `visible_facts`.

Turn 6’s audit attached the adjacent rope-walk sentence to `world_truth` with an empty semantic identity. The committed scene is the sail loft. The audit label and the committed location disagree about what that sentence is.

Movement decisions list `permitted_state_mutations: []` after the resolver has already set `scene_transition`. Provenance on the decision does not record the location change the session then commits.

## 9. Semantic-fidelity analysis

Re-audit uses the saved decision audits. No new model calls.

- Turn 3 is the negation case the repair targeted. “Not locked” against authorized `full` is a `derived_denial`. The full cistern stays in the same sentence. No `semantic_identity_mismatch`.
- Turn 4 realizes two structured values in neighboring sentences. A sentence that says “two spokes missing” matches. The tear sentence does not have to repeat the spokes. Entity mention of the wagon is not a failed restatement.
- Turn 1 is a different fidelity miss. `_EVENT_SITE_RE` matches `happened` within 48 characters of `here`. The sentence is “when it happened, and who might be responsible remain unseen here.” `_UNKNOWN_SLOT_RE` does not treat “remain unseen” as an unknown slot, so the cause slot is scored as filled. The code recorded is `unauthorized_qualifier:location`. The decision’s own constraint says cause, actor, and time may be called unknown.
- Turn 8’s denial of the college is not `unauthorized_social_world_fact`. It is framed as no visible indication.
- Turns 6 and 7 have empty violation lists. The upward stair is not caught. The omitted thanks is not a fidelity violation; it is an absent clause.

The old failure, where any “not” or “no” contradicted a positive cracked fact, or where naming the subject required every value in that sentence, does not appear in this population.

## 10. Retry analysis

One retry, turn 1.

The retry user message is 2,675 characters. It is not the old 422-character note. It contains:

- `resolution_contract` for `rc_8252c9bea2b9`
- `gm_resolution_decision` with the same contract id, the jammed-gate fact, and unresolved qualifier `cause`
- `validation_failure` naming `unauthorized_resolution_decision_fact` and the “remain unseen here” sentence

The retry generation produced no player-facing text. Attempt 2 is `malformed_or_truncated`. Decision context was present. A repaired narration was not. Preservation then edited attempt 1.

Turns 2 through 8 were accepted on the initial generation. They supply no second retry sample.

## 11. Bounded-preservation analysis

Preservation ran once, on turn 1, after the empty retry. Acceptance why: `bounded_sentence_preservation`. Provenance on the seal: `initial_generation`, because the kept text came from attempt 1.

It removed only the sentence named in the violation list. That sentence was the correct unknown-cause statement. The remainder still contains the missing-patrol lead, which the audit had authorized as a claim. Preservation did what the violation list said. The list was the wrong sentence.

The generic no-answer line was not used. The established jam survived. That part of the repair worked. The player still lost the uncertainty and kept the bad lead.

No other turn needed preservation.

## 12. Fallback analysis

The canned line “No one here can answer that from what is settled here” does not appear in any emitted response.

Turn 1’s terminal path is preservation of the non-violating sentences, not `safe_nonresolution` and not `authorized_observation`. Turns 2 through 8 are `initial_generation` with `hard_valid` true.

Social turns 2 and 5 did not collapse to a useless refusal. Turn 5’s social metadata says `reply_kind` `refusal`, and the spoken line is still a specific answer about the evening.

## 13. Movement and state analysis

| Turn | Committed scene | Narration location | Factions / flags / events |
| --- | --- | --- | --- |
| 1 | `mill_race` | mill race | empty |
| 2 | `cooper_yard` | cooper yard | empty |
| 3 | `orchard_cistern` | cistern | empty |
| 4 | `timber_yard` | timber yard | empty |
| 5 | `ferry_slip` | ferry slip | empty |
| 6 | `sail_loft` | sail loft, plus the departure stair | empty |
| 7 | `eastern_courtyard` | eastern courtyard | empty |
| 8 | `ink_stall` | ink stall | empty |

Turn 6: resolver `travel`, kind `scene_transition`, target `sail_loft`, commit matches. Narration’s first sentences match the destination. The last sentence adds an upward stair that is not an exit of the loft.

Turn 7: resolver `travel`, kind `scene_transition`, target `eastern_courtyard`, commit matches. Narration matches the destination summary (paved yard, cistern house, mill wall, dry trough) and adds incidental scent and sound. It does not mention the thanks.

Neither movement wrote a new region into world state. The onward stair exists only in turn 6’s prose.

## 14. Mixed social and travel analysis

Probe 7 was built to see whether the known resolver-ownership failure appears in a live turn.

Setup: Mirelle engaged, an authored warning, an exit whose label is the eastern courtyard, and the utterance “I thank Mirelle for the warning, then head for the eastern courtyard.”

Observed path:

```
player text
  -> contract operation act, subject travel
  -> select_ordinary_resolver returns travel
  -> travel stage runs
  -> scene_transition to eastern_courtyard
  -> decision remains attached to rc_6ff0fda95ff8
  -> narration describes the courtyard and omits the thanks
```

The known failure path is the opposite:

```
contract operation/subject selects social
  -> select_ordinary_resolver returns social
  -> travel stage is not permitted
  -> expected movement does not occur
```

That path did not occur. Social content did not suppress the declared move. The contract’s single operation dropped the social half instead.

Classification against the six scene-transition failures: **B. Related but different mechanism.**

The shared shape is that one contract operation owns the turn. The live difference is which operation won. Travel won, the scene changed, and the decision stayed attached. The six tests fail when social wins and the destination does not change. This probe does not show that those tests would pass.

## 15. Background NPC and improvisation analysis

Osric has a role, a lantern, and no importance marker. The evening question produced a reserved manner, steady work, a restless river, and uneasy neighbors. Those details are mundane. They were not stored as factions, flags, or ledger entries.

The social layer’s `reply_kind` was `refusal`. The player-facing line is not the generic nonresolution and not a dead “I don’t know” with nothing else. Bounded improvisation is still alive on this route, and the decision was attached while that happened.

Turn 4’s “ragged and worn from use” is the same class of incidental texture, audited as incidental and not committed.

## 16. Failure-family clustering

| Turn | Primary | Secondary | First incorrect layer |
| --- | --- | --- | --- |
| 1 | G. Semantic-fidelity validation | I. Bounded preservation. H. Retry generation empty. F. Patrol lead in the initial text. | Validation scored “when it happened … unseen here” as an event site. |
| 6 | D. GMResolutionDecision content | F. Narration. G. Validation accepted the stair. | The decision does not permit the location mutation and still authorizes the departure stair. |
| 7 | A. Resolution Contract / intent interpretation | F. Narration omitted the thanks. | The mixed line was contracted as travel only. |

No turn is primary **C** (decision missing) or primary **B** (resolver picked against its contract). Resolver selection followed the contract every time.

Turns 2, 3, 4, 5, and 8 have no failure family.

## 17. Comparison with the first 4/8 validation

First live validation: **4 PASS / 4 FAIL** (turns 3, 5, 6, 8 passed; turns 1, 2, 4, 7 failed).

This population: **5 PASS / 3 FAIL.** The score is not the comparison. The mechanisms are.

| Mechanism in the first run | This run |
| --- | --- |
| Missing decision on prebuilt social and movement contracts (turns 2, 3, 6, 8). | Did not recur. 8/8 decisions present, ids matched, including social and travel. |
| Sentence-local negation and entity mention rejected competent answers (kiln “not firing,” dye-vat lead-in, bell “no one”). | Did not recur in that form. Turn 3’s “not locked” passed beside “full.” Turn 4’s split sentences passed. |
| Retry note omitted the contract and the decision. | Did not recur. The one retry note carried both and the failure reason. |
| Generic nonresolution replaced a useful answer. | Did not recur. Turn 1 kept the jammed gate. It did drop the unknown-cause sentence. |
| Unsupported consequential social fact spoken as known (Violet Compact gathers at the docks). | Did not recur as world truth. Sedge’s Harbor Guild stayed a rumor and was not committed. The college purchase was denied. |
| Authorized movement committed and narration agreed (reed loft). | Movement still commits. Turn 7’s courtyard agrees. Turn 6’s loft agrees in the opening and then adds an upward stair. |
| Bounded improvisation alive (bread smell, fish-seller). | Still alive. Osric’s evening, and the wagon’s incidental wear. |

The two defects named by the repair are fixed on these fresh situations. A neighboring qualifier pattern, movement-decision mutations, and single-operation mixed utterances are the new evidence.

## 18. Comparison with the original 8/40 gate mechanisms

The second full gate (`artifacts/pr_br_second_full_gate/20261003T142725Z`) was 8/40 PASS. Its recurring mechanisms were unsupported consequential facts, especially patrol authority spoken as playable premises, and generic nonresolution replacing an available answer.

This cycle did not rerun that gate.

- Generic nonresolution does not appear in these eight turns.
- A missing-patrol notice appears once, on turn 1, as a hedged next step. It was not committed. The saved prompt head and tail do not contain the word “patrol.” Isolated storage still holds the default frontier-gate scene, as the first probe harness did. Relative to the mill-race facts, the notice is not established.
- Consequential social institutions were offered to the model on turns 2 and 8 and did not become world truth.
- Location commit on the two travel turns matches the authored destination. The gate’s location-desync class is not the turn 7 result. Turn 6’s stair sentence is a narration mismatch on top of a correct commit.

The gate’s two dominant mechanisms are quieter here. This sample is eight isolated turns, not forty.

## 19. Assessment of the six known scene-transition regressions

The unrepaired failures in `tests/test_scene_transition_authority.py` are:

- `test_chat_mixed_farewell_and_declared_travel_overrides_dialogue_lock`
- `test_actionable_lead_declared_travel_authoritative_arrival_and_lead_metadata`
- `test_declared_travel_unresolved_movement_no_social_no_scene_change`
- `test_declared_travel_eastern_square_disambiguates_against_prior_milestone_lead`
- `test_combined_prior_lead_affirmed_waste_gpt_scene_proposal_non_authoritative`
- `test_unresolved_alternate_destination_with_prior_old_milestone_lead_no_substitution`

They were not rerun and not patched. The repair report’s observation still stands: when the contract operation is `ask` or the subject is social, `select_ordinary_resolver` returns `social`, and the travel stage is not permitted.

Probe 7 did not reproduce that path. With an engaged NPC, a thanks, and an explicit move to an authored exit, the contract subject was `travel`, the resolver was `travel`, and `eastern_courtyard` committed. The decision stayed on that contract.

**B. Related but different mechanism.**

Single-operation ownership still drops one half of a mixed utterance. In this live sentence the dropped half was the thanks, not the move. The six tests are the case where the dropped half is the move. One live success does not retire those tests. They remain known evidence.

## 20. Recommendation

The decision layer is now on the routes that previously skipped it. Negation of an unrelated predicate, multi-sentence observation, rumor-framed social answers, and incidental NPC color all reached the player with matching decisions. The generic refusal did not replace an available fact.

The sluice turn shows a remaining qualifier false reject, an empty retry, and preservation that keeps the wrong sentence. The sail-loft turn shows a movement decision that does not record the committed move. The courtyard turn shows a mixed line collapsed to travel. Those are localized. They are not a missing decision architecture, and they are not the old negation collapse.

Return to targeted implementation for those three defects. Do not open a multi-turn validation, the 4×10 gate, or PR-BS on this measurement. Leave the six scene-transition tests failed until that ownership question is taken up on its own.

B. SECOND LIVE VALIDATION EXPOSED LOCALIZED DEFECTS; RETURN TO TARGETED IMPLEMENTATION
