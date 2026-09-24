# Human Playtest Audit — Natural Mixed-Action Ownership and Compound-Turn Capability

Date: 2026-09-23
Era: Product Realization
Primary lane: Gameplay
Secondary lane: AI Experience

This audit is not PR-BK. No next cycle identifier is assigned.

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Human evidence: `artifacts/human_playtests/20260923_cinderwatch_crowd_observation_failure/`

Probe evidence: `artifacts/human_playtests/mixed_action_ownership_audit/`

---

## 1. Executive summary

The human turn was a mixed perception attempt: move through the gate crowd, look, listen, and ask what that looking and listening could show. The architecture already recognized a listen attempt inside the utterance. It then discarded that attempt because the utterance also contained a question, routed the whole turn as open social solicitation on the word `anyone`, and filled the unset open bid with the sole world NPC, Tavern Runner.

That is ownership collapse, not a failure to understand one sentence, and not a missing answer about refugee origins. Authored state has no refugee origin, regional composition, dialect, heraldry, wounds, or overheard reason for flight. A correct listen may realize the authored runner shout about stew and rumor. It may not invent demographics.

Production change: a player listen / eavesdrop / overhear attempt remains the existing perception owner when a question shares the utterance. `Does anyone know` and `Anyone listening?` stay social. Explicit `I ask the warden` stays social. Movement and the peeled visual question still do not execute. That remaining gap is deferred compound-turn capability, not another parser exception.

The `Word is` line was not the root defect. Integrity replaced the model paragraph because the pronoun `their` was ambiguous, then `topic_pressure.last_answer` re-emitted a fragment of the same invented paragraph. That path is downstream of the wrong owner.

PR-AS through PR-BJ are not reopened. They converged single-owner families. This playtest is the next abstraction: ordinary turns that contain more than one operation.

---

## 2. What the captured turn actually did

Player text:

```text
Galinor eyes the crowd as he steadily moves into Cinderwatch, eavesdropping where he can. Is anyone talking about what have these people had to flee from? Do the refugees all seem to be from the same region, or is it a hodge-podge?
```

Player-facing result:

```text
Tavern Runner mutters, "Word is, best way to find out lies beyond this gate, if you've the wit and will."
```

Verified routing fields from `persisted_data/session_log.jsonl` and the chat debug trace:

| Field | Captured value |
| --- | --- |
| `kind` | `question` |
| `action_id` | `question_tavern_runner` |
| `social_intent_class` on the action | `open_call` |
| `social_intent_class` after resolution | `social_exchange` |
| `route` | `dialogue` |
| `routed_to` | `social_exchange` |
| `route_reason` | `open_social_solicitation` |
| `addressed_actor_id` | `tavern_runner` |
| `addressed_actor_source` | `scene_open_bid` |
| `canonical_entry.target_actor_id` | `null` |
| `canonical_entry.target_source` | `scene_open_bid` |
| `broad_address_phrase_matched` | `anyone` |
| `broad_address_reason` | `broad_lexical_and_framing_ok` |
| `reply_kind` | `refusal` |
| `social_question_dimension` | `location` |
| `source_route` | `mixed` |
| `state_changes` | `{}` |
| `topic_revealed` | `null` |
| `resolved_transition` | `false` |

The prompt's `route: social_exchange` is the `routed_to` / intent class, not `metadata.route`. `metadata.route` is `dialogue`.

### Evidence table

| Stage | Observed result | Authoritative? | Notes |
| --- | --- | --- | --- |
| Raw player input | The mixed move / look / listen / two-question text above | Yes | `session_log.jsonl` entry 2, `2026-09-23T09:31:34Z` |
| Segmentation | Declared action keeps movement, eavesdropping, and the first question. The region question is `adjudication_question_text` | Yes | One trailing question is peeled. The earlier question stays on the action |
| Intent parse | `question` / `question_tavern_runner` via dialogue-first | Yes | Listen family was detectable and was not the selected action |
| Addressed NPC | `tavern_runner` | Yes | Open bid left the target unset. Dialogue lock then supplied the sole world NPC |
| Action owner | Social exchange, open solicitation collapsed to a directed question | Yes | `reply_kind: refusal`. Hint: no new information |
| Adjudication | Region question stored, not resolved | Yes | No `embedded_adjudication` on the resolution |
| State mutation | No scene change, no clue, no topic reveal | Yes | `topic_pressure.last_answer` was written from model prose |
| Model realization | Tavern Runner hedge plus invented refugee origins and a "beyond this gate" hint | Partial | Full text stored as `last_answer`. Raw wire payload was not captured |
| Integrity validation | Referential clarity replaced the paragraph on ambiguous `their`. Narrative-authority invented-fact flags stayed false | Yes | Speaker binding also mismatched because the quote was parsed as the speaker name |
| Final emission | `Word is` around the invented "beyond this gate" sentence | Yes | Post-gate mutation from `topic_pressure:last_answer` after the grimace emergency line |

---

## 3. First incorrect decision

Trace forward:

1. `segment_mixed_player_turn` peels only the last question. The declared clause still contains `eavesdropping` and `Is anyone talking…?`. That segmenter is conservative by design. It is not the first wrong owner.
2. `classify_human_adjacent_intent_family` / `looks_like_listen_perception_intent` already treat `eavesdropping` as listen. `_has_information_seeking_question` then returns true because of `?`.
3. That question guard makes `looks_like_explicit_physical_or_perception_action` false and skips the human-adjacent observe block in `parse_freeform_to_action`. `recover_actionable_explicit_world_action` therefore returns nothing.
4. `detect_broad_address_social_bid` matches `\banyone\b` plus a question mark. `resolve_directed_social_entry` sets `open_social_solicitation`, `target_source: scene_open_bid`, `target_actor_id: null`. Candidates, in rank order, are `guard_captain`, `tavern_runner`, `refugee`, `threadbare_watcher`. Tavern Runner is not the winning candidate.
5. `_build_dialogue_first_action` fills the empty target with `resolve_dialogue_lock_action_target_id`. Persisted `data/world.json` has one NPC at `frontier_gate`. The lock's final branch assigns that sole scene NPC with no information-seeking check. The action becomes `question_tavern_runner`.
6. `resolve_social_action` sees an explicit target, so the open-call branch that would have left `npc_id` unset does not run. Resolution says the player spoke with Tavern Runner and revealed nothing.

The first incorrect decision is step 3: `game/intent_parser.py`, the question guard around the existing human-adjacent listen owner (`looks_like_explicit_physical_or_perception_action` and the `0c` block in `parse_freeform_to_action`). An already recognized player listen attempt was discarded because a question shared the utterance. Open social and the sole-NPC fill then interpreted the discarded turn.

Step 5 explains why the addressee was Tavern Runner rather than Guard Captain. It is the second decision, and it only runs because step 3 already dropped listen. `scene_open_bid` itself did not choose Tavern Runner. Presence was not treated as enough inside the bid. The bid left the target empty. Dialogue lock's sole-world-NPC fallback created the address.

PR-BH is not reopened. This turn has no explicit addressee. The settled sole-NPC behavior for a genuine undirected question remains. It was applied here only after listen had been discarded.

---

## 4. Semantic components, tested apart

Persisted-world probe, before the repair:

| Utterance | Selected owner | Executes? | Authority |
| --- | --- | --- | --- |
| `I move farther into Cinderwatch.` | Unparsed (`kind` none) | No | Exit label is `Enter Cinderwatch`. This wording is not local `custom` and not a resolved scene transition |
| `I look over the refugees.` | `investigate` | Yes, untargeted | Fail-closed: no discoverable target. Does not invent a find |
| `I listen to the crowd.` | `observe` / listen | Yes | Grounded audible cue only |
| `I eavesdrop on the crowd.` | `observe` / listen | Yes | Same listen owner. `eavesdrop` was already a listen cue |
| `Is anyone talking about why the refugees fled?` | `question` to `refugee` | Yes, refusal | The noun matches the addressable role. No listen verb, so this stays social |
| `Do the refugees seem to come from the same place?` | `question` to `refugee` | Yes, refusal | Visual inference is addressed to the ragged stranger. No authored origin |
| `Does anyone know why the road is closed?` | Open solicitation, then sole NPC `tavern_runner` | Yes | Legitimate open social. Preserved |
| `I listen to see whether anyone is talking about why the road is closed.` | `observe` / listen | Yes | No question mark, so the old guard already allowed listen |
| `I look around the gate.` | `observe` | Yes | Ordinary look |
| `I examine the notice board.` | `investigate` `notice_board` | Yes | Ordinary investigation |
| `I walk a few steps along the gate.` | `custom` local movement | Yes | PR-AQ local movement |
| `I ask the runner whether he's heard anything about the missing patrol.` | Social, declared switch to `tavern_runner` | Yes | Explicit dialogue preserved |

Ashen Thrones already sees more than one slice of text. It does not already understand that more than one operation was asked. The second question is a syntactic slot. It is executed only when adjudication recognizes it. The region question was not a procedural adjudication, so it was dropped. The listen attempt and the first question were one string, and the question won.

---

## 5. `open_social_solicitation` and `scene_open_bid`

`detect_broad_address_social_bid` is a lexical crowd-address detector. `\banyone\b` plus `?` is enough. The intended positive set in `tests/test_broad_address_social_bid.py` is solicitation: `Anyone up for a chat?`, `Who here knows about the patrol?`, `Can somebody tell me what happened?`, `I call out for anyone willing to talk.`

`Does anyone know why the road is closed?` belongs there.

`I listen to see whether anyone is talking about why the road is closed.` does not. Before this audit, the no-question-mark form already reached listen, while the open-bid flag was still computed and then ignored because recover ran first. Adding `?` used to flip the executed owner to social.

`Is anyone here I can ask about the road?` is still an open bid. The social parser then mis-binds a target slug from the tail of the sentence. That residue is separate from the listen repair.

`scene_open_bid` may select a candidate list when the broad-address detector fires and no explicit addressee resolved. It does not require a named vocative. Scene presence supplies candidates. It does not, by itself, pick Tavern Runner. The live `addressed_actor_source: scene_open_bid` is the route reason copied onto the debug record after dialogue lock had already filled `tavern_runner` as `resolved_target_id`.

---

## 6. Settled owners, applied and not reopened

PR-AR: listen is perception. The runner's shout is authored speech. Refugee small-talk is not. After the repair the human turn's hint is the stew-and-rumor shout, with an explicit ban on extra speakers and topics. Empty audible absence remains valid when no such cue exists.

PR-AQ: `I walk a few steps along the gate` stays `custom`. `I move farther into Cinderwatch` stays unparsed. Local movement was not reopened. The movement clause in the human turn is an unsupported component beside the listen owner, not a travel success.

PR-AY / PR-BB: `I look over the refugees` reaches investigate and fail-closes. `Do the refugees seem to come from the same place?` does not. It binds the refugee addressable. That is accepted residue of this audit, not a new observation paraphrase cycle. No demographic facts were added.

PR-BH: no explicit identity was offered, so identity resolution was not the failing owner. The sole world NPC was applied only after listen was dropped.

PR-BI: `Word is` / `mutters` on the final line is the existing structured-fact envelope. The sentence inside it was not an owned fact. PR-BI is not reopened to delete the envelope.

---

## 7. World authority

Frontier Gate authored material (`data/scenes/frontier_gate.json`, persisted `data/world.json`) supports:

- Refugees are present in the crowd.
- A tavern runner shouts offers of hot stew and paid rumor.
- Threadbare clothes on one still figure.
- Notice board: taxes, curfew, missing patrol.
- Runner topic: the patrol never came back from the old milestone.
- Hidden facts about a noble watcher, an Ash Cowl spotter, and a signal. Those are not player-visible.

It does not support refugee origin, shared region, dialect, heraldry, origin clothing, wounds, group composition, reasons for flight, overheard refugee speech, or a rumor about why people fled.

| Asked dimension | Class |
| --- | --- |
| People are present and crowded | A. Authoritatively observable |
| Runner is hawking stew and rumor | A. Authoritatively audible |
| Why they fled | D. Knowledge absent |
| Same region or mixed origins | D. Knowledge absent |
| Clothing, dialect, heraldry, wounds as origin evidence | C/D. Not authored as observable origin cues. `threadbare clothes` is one figure's description, not a demographic |
| Overheard refugee dialogue | E. Would need new authored speech or ambient content. Not invented here |

Correct routing must not force an origin answer.

---

## 8. Model paragraph and the final line

Full model text, stored as `topic_pressure['topic:anyone_cinderwatch_crowd'].last_answer`:

```text
"I can't say for certain," the tavern runner shrugs, wiping rain from their brow. "People here keep their mouths shut tight around such matters—fear and watchful eyes make for quiet lips. Refugees come from all directions, some fleeing across borders, others from the wilderland strife, but no one talks freely about the true causes. Best way to find out lies beyond this gate, if you've the wit and will."
```

| Assertion | Class |
| --- | --- |
| Uncertainty / cannot say for certain | Harmless hedge, then contradicted by later specifics |
| Mouths shut, fear, watchful eyes | Unsupported |
| Refugees come from all directions | Unsupported |
| Fleeing across borders | Unsupported |
| Wilderland strife | Unsupported |
| No one talks about the true causes | Unsupported |
| Best way to find out lies beyond this gate | Unsupported. Not the patrol-milestone topic |

`narrative_authority` flags `invented_hidden_fact: false`. The paragraph was not rejected as unauthorized knowledge.

Replacement path:

1. Referential clarity: token `their` in `their brow`, kind `ambiguous_entity_reference`.
2. Speaker contract: the quote prefix was parsed as the speaker name (`speaker_binding_mismatch`).
3. Sealed fallback `minimal_social_emergency_fallback`: `Tavern Runner grimaces. "Not something I can say here."`
4. Post-gate `authored_knowledge_realization` source `topic_pressure:last_answer`. Dimension `location` picked the shortest stored sentence that looked locative: `Best way to find out lies beyond this gate…`
5. `format_structured_fact_social_line` wrapped it as `Word is` because that sentence did not already contain the envelope.

Given `question_tavern_runner`, a refusal would have matched `reply_kind: refusal`. The emitted line is not that refusal. It is a fragment of the model paragraph treated as a structured fact. PR-BI's cutoff exclusion did not apply, because this text is a complete answer. The envelope itself is the existing formatter.

The final `Word is` line is not the root defect. It is how the wrong social owner was realized after a pronoun check, using contaminated `last_answer`. This audit does not weaken validators and does not change that formatter. The listen repair keeps this turn off that path.

---

## 9. Generalization probe

Persisted-world matrix. Before / after refers to the listen-question repair. Cases that did not contain a player listen attempt are unchanged.

| Case | Before | After |
| --- | --- | --- |
| Human playtest turn | `question` Tavern Runner, open social | `observe` listen, no NPC, no state change |
| Study guards while listening to merchants | `observe` listen | unchanged |
| Walk toward the notice board and watch the stranger. Does he react? | `travel` (`notice board` / move pattern) | unchanged |
| Examine wagon tracks while listening for the patrol | `investigate`, listen not executed | unchanged |
| Keep walking and look at refugees. Do any look wounded? | `investigate`, question not executed | unchanged |
| Watch the guards, then ask the serjeant | Social question, serjeant unbound | unchanged |
| Listen, then ask the runner about the patrol | `observe` listen. The ask is not executed | unchanged |
| What are the guards watching, and does the road look passable? | `question` Tavern Runner via sole NPC | unchanged |
| `Does anyone know why the road is closed?` | Open social, sole NPC Tavern Runner | unchanged |
| `Anyone listening?` | Social solicitation, not player listen | unchanged |
| Atomic listen, look, investigate, local walk, explicit runner ask | Existing single owners | unchanged |
| `I move farther into Cinderwatch.` | Unparsed | unchanged |

The failure reproduces where a player listen attempt shares a string with a question, and where a question-only turn has no better owner than the sole world NPC. It does not reproduce for atomic listen, atomic look, explicit asks, or mixed turns whose surviving clause is already investigate / listen / travel.

Listen-plus-explicit-ask already executes listen and leaves the ask unresolved. That is the existing single-owner limit. This repair puts listen-plus-question on that same limit instead of reinterpreting the question as the whole turn.

---

## 10. Classification

Outcome F, with a primary and two leftovers.

Primary: **ownership collapse.** A recognized listen attempt was discarded, then open social plus the sole world NPC interpreted the turn.

Also present, and not repaired:

- **Missing decomposition capability.** A turn cannot execute listen and also answer, defer, or fail a second visual question. Segmentation stores one peeled question and does not run it unless adjudication claims it. Movement beside listen does not run.
- **World-content insufficiency.** Even a perfect listen cannot honestly answer origin or regional mix.
- **Local routing residue.** Question-only lines with no listen attempt still become a directed question to the sole world NPC (`What are the guards watching, and does the road beyond the gate look passable?`). `Is anyone talking about why the refugees fled?` binds `refugee` by role substring. Those are not the captured turn's first decision.

Not a safe single-owner limit before the repair: the other clauses were not left unresolved. They were answered through Tavern Runner.

After the repair, this captured turn is a safe single-owner result: listen executes; movement and the region question stay unresolved; no invented origin is spoken by the social resolver.

---

## 11. Compound-intent capability

1. A turn can contain multiple parsed slots: declared action, one adjudication question, spoken text, observation, contingency. That is not N semantic operations.
2. More than one component does not execute.
3. One component can execute while another is dropped with no player-facing "unresolved" marker. Dropped is not the same as an explicit safe failure.
4. There is no primary/secondary intent model. There is a single winning action, plus an optional adjudication slot.
5. Secondary questions are not retained as questions after an action executes, except as inert segmentation metadata. `source_route: mixed` means a peeled question existed. It does not mean the question was answered.
6. Perception and social action do not both execute. Listen currently wins over a later explicit ask in the same string.
7. Movement and perception do not both execute.
8. Investigation and listen do not both execute. `examine` wins and listen is dropped.
9. Realization knows the winning action and its hint. It does not receive a list of unexecuted clauses.
10. Final narration does not systematically distinguish attempted, executed, unresolved, and unanswered. The listen hint can constrain audible invention. It does not say that the region question was left open.

Comprehensive N-action execution remains deferred.

---

## 12. Repair

Invariant: a player listen, eavesdrop, or overhear attempt stays the existing human-adjacent perception owner when a question shares the utterance. A solicitation whose only listen-word is `anyone listening` / `who's listening` stays social. Local movement stays blocked by questions. `Does anyone know` stays open social. Explicit asks that do not themselves declare a player listen stay social.

The repair does not add phrase recognition for the human sentence, refugee origins, or a Tavern Runner exception. `eavesdrop` was already inside `_RE_LISTEN_PERCEPTION` and `classify_human_adjacent_intent_family`.

Files:

- `game/intent_parser.py` — `_player_listen_attempt`, and the two question guards that feed human-adjacent observe.
- `tests/test_listen_question_not_social_capture.py`

After the repair, the captured turn classifies as `observe` / `listen`. Resolution hint realizes only: `A tavern runner shouts offers of hot stew and paid rumor.` No NPC is addressed. `npc_runtime` does not change. The region question remains segmented and unanswered.

---

## 13. Anti-overfitting

1. Would the repair still make sense if the original human sentence had never existed? **Yes.** Any player listen attempt was being discarded by a shared question mark, then available for social capture.
2. Does the repair improve at least three semantically different mixed turns? **Yes.** `I listen to see whether anyone is talking about why the span is shut?`; `I eavesdrop on the porters` plus two questions; `While I overhear the porters, is the cracked pier still dripping?`; plus the captured gate turn.
3. Literal dependency on `eavesdrop`, `refugee`, `region`, `hodge-podge`, `Tavern Runner`, or `Cinderwatch` in the repair? **No.** `eavesdrop` remains an existing listen cue in the perception regex. The new test uses cistern / porter / span wording for the engine contract, and the captured sentence only as a calibration regression.
4. Is the failure fundamentally lexical? **No.**
5. Is the failure fundamentally ownership/capability related? **Ownership.** A recognized listen owner was replaced by social. Compound execution and missing origin content are separate.
6. Did any previously settled atomic owner prove incorrect? **No.**
7. Did the playtest reveal a new semantic class? **Yes.** Ordinary multi-part turns, where one recognized component must not be reinterpreted through whichever later single owner wins. Prior probes were atomic or single-owner.

---

## 14. PR-AS through PR-BJ

1. Those cycles converged the atomic and single-owner families they named. This turn does not show `"The guard says"`, a bad Gate Serjeant bind, a lost `Why is that?`, or an interruption cutoff stored as `last_answer`.
2. This playtest is a higher abstraction: mixed natural turns and which single owner is allowed to consume them.
3. No evidence here says the prior repairs were phrase-specific. Atomic listen, look, investigate, local walk, explicit runner dialogue, and `Does anyone know` still behave as those cycles left them.
4. They generalized inside those domains on this probe.
5. Nothing here justifies reopening a settled cycle.
6. It justified one small existing-owner repair, already made, plus a still-deferred compound-turn capability. It does not justify another authority or paraphrase sibling.

---

## 15. Closeout answers

A. The player asked to move into the crowd, look at the refugees, listen for talk about why they fled, and judge whether the crowd looks like one region or many.

B. Segmentation recognized a declared clause (move, eyes, eavesdrop, first question) and one adjudication question (same region or mix). The listen family was recognized on that declared clause and then discarded. No movement owner and no observation owner were selected.

C. Social exchange captured the turn: `open_social_solicitation` executed as `question_tavern_runner`.

D. `anyone` opened a scene bid with no chosen NPC. `resolve_dialogue_lock_action_target_id` then assigned the only world NPC at the gate, `tavern_runner`. Guard Captain ranked first among addressable candidates and was not the lock's input.

E. First incorrect decision: `game/intent_parser.py` question guard that skips human-adjacent listen when the same utterance contains `?`.

F. Was `Word is` the root defect? **No.** It wrapped a fragment of invented model prose after the wrong owner was already selected.

G. Did integrity reject unsupported refugee information? **Partially.** The full paragraph did not reach the player. The rejection reason was ambiguous `their`, not missing authority. A fragment of the invention was then emitted as `last_answer`.

H. Authoritative information: refugees are present; a runner shouts stew and rumor; one threadbare figure; the patrol notice and the runner's milestone topic. Not origins, region mix, dialect, wounds, or overheard flight reasons.

I. Does it reproduce across different mixed turns? **Partially.** Listen-plus-question collapsed. Several other mixes already kept a single non-social owner. Question-only mixes can still collapse to the sole world NPC.

J. Classification: ownership collapse, plus leftover missing decomposition and world-content insufficiency. A local sole-NPC question residue remains for turns that are not listen attempts.

K. Production code changed? **Yes.**

L. Invariant repaired: a player listen attempt is not discarded because the same utterance also asks a question, and that attempt is not retold as solicitation to the sole NPC.

M. Anti-overfitting: **Yes.**

N. Did this invalidate the PR-AS through PR-BJ convergence claim? **No.** The boundary is single-owner semantic integrity versus mixed-turn ownership. Convergence inside the first boundary still holds.

O. Next Product Realization work: **resume human playtest.** The small owner repair is in this audit. Do not open a paraphrase cycle. Do not assign PR-BK. Compound-turn execution, origin content, and question-only sole-NPC collapse stay deferred until a later playtest shows which of those the player actually hits next.

---

## 16. Validation

Focused pytest, not a new full-suite baseline: 145 passed, 0 failed.

`tests/test_listen_question_not_social_capture.py`, `tests/test_human_adjacent_focus.py`, `tests/test_human_adjacent_nearby_group_continuity.py`, `tests/test_broad_address_social_bid.py`, `tests/test_perception_narration_authority_audible_non_invention.py`, `tests/test_local_observation_classifier_boundary.py`, `tests/test_local_observation_routing.py`, `tests/test_local_presence_question_adjudication.py`, `tests/test_question_form_observe_realization_retry_ownership.py`, `tests/test_physical_action_typing_compound_perception_realization.py`.

Authoritative full suite remains the pre-later-cycle record: 6,450 collected, 6,351 passed, 0 failed, 99 skipped (`artifacts/policy_implementation/post_implementation_suite.xml`). This focused run does not replace it.

Known validation residue from the prior handoff was not absorbed.

---

## 17. Deferred residue

- Compound execution of movement plus perception, investigation plus listen, or listen plus a later explicit ask.
- A player-facing distinction among attempted, executed, unresolved, and unanswered.
- `I move farther into Cinderwatch` remaining unparsed.
- Question-only turns collapsing to the sole world NPC.
- `Is anyone talking about why the refugees fled?` and `Do the refugees seem to come from the same place?` binding `refugee`.
- Same-turn model prose stored as `topic_pressure.last_answer` and later selected as a structured fact. Not reached by this turn after the listen repair. Not a `Word is` wording cycle.
- Authored refugee origins, ambient crowd speech, and a five-senses simulation. Not added.
