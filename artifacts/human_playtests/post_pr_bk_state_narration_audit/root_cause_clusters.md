# Root Cause Clusters

Session `735ebd1cfb4567c4f97df6dc`. Four clusters. Turns 07–09 are not separate causes.

---

## CLUSTER 1 — Unparsed movement narrates and commits a journey

FIRST AFFECTED TURN: 06

FIRST INCORRECT DECISION: `parse_freeform_to_action` returned `None` for `I proceed North-West, as the runner directed.` No travel or transition owner ran. The documented fallthrough is generative narration. That narration asserted arrival, and `game/api.py` adopted the model's `scene_update` because the payload had a legal shape.

OWNER: intent parsing, then generative realization, then legacy scene-update adoption.

FUNCTION / FILE:

- `game/intent_parser.py` `parse_freeform_to_action` — `proceed` is not a travel verb; the legacy follow/pursue matcher never runs without `follow` or `pursue`
- `game/narration_state_consistency.py` `apply_stay_leave_narration_agreement_to_gm` — rewrites false arrival only when kind is `travel` or `scene_transition`
- `game/api.py` `_validate_gm_scene_update_for_legacy_adoption` and the `apply_gm_scene_update_layers` block — shape check only; comment says it does not make a gameplay-policy decision

AFFECTED TURNS: 06, 07, 08, 09

PLAYER-FACING SYMPTOMS: a northwest journey past crates, sheds, lanterns, and broken banners while the scene id stays `frontier_gate`. Then a crate question, a banner question, and "continue the path" cannot find those things.

DOWNSTREAM DEPENDENCIES: 07 (passing crates), 08 (broken banners), 09 (the path). Empty `The guard says` on 08 and 09 is an amplifier, not the cause.

EXISTING CAPABILITY OR MISSING CAPABILITY?: Existing. The rumor exit already transitions for `I follow the missing patrol rumor`, `I follow the northwest mud track`, `I pursue the missing patrol rumor northwest`, `I go to the old milestone`, and `I'll head toward the old milestone`. Bare `I'll head northwest` is already unresolved `travel`, which is the PR-BF path. This utterance never entered that path.

GENERALITY: Any unparsed directional or continuation utterance can be narrated as success, and any shape-valid `scene_update` can add visible facts, clues, hidden facts, and mode. Not specific to northwest, crates, or this scene.

SEVERITY: High. The player acted inside a place the simulation did not enter, and the overlay then stored that place.

SMALLEST GENERAL REPAIR: Do not emit spatial-success narration, and do not adopt model `scene_update` arrival or new clue/hidden/mode facts, unless `resolved_transition` or an equivalent owner flag is true. Recognize `proceed` as the existing travel verb family only if destination binding stays the current exit/clue matcher. Unresolved `northwest` must stay unresolved.

ARCHITECTURE EXPANSION REQUIRED?: No second travel router, geography database, or noun promotion.

SHOULD ADDRESS NOW?: Yes. This is the coherence break.

---

## CLUSTER 2 — One board payload answers every board question

FIRST AFFECTED TURN: 01

FIRST INCORRECT DECISION: On turn 01, a failed no-target `social_probe` (`canonical_entry_reason` `no_addressable_target`) emitted `generated_candidate` board prose, including a curfew-hour schedule and the still-undiscovered route. The resolution hint was to narrate that there was no social target. Narrative authority did not fail.

On turn 02 the inspect owner did the right bind (`notice_board`, target surface `curfew`) and then revealed its only payload, `notice_patrol_route`, because `skip_unrelated_clue_discovery` is false. Hours, districts, penalties, and reasons are not authored.

OWNER: realization on turn 01; referenced-surface discovery on turn 02 (`game` referenced-surface metadata on the resolution). Content gap is the missing hour/district text.

FUNCTION / FILE: social entry that classified the approach as `social_probe`; `generated_candidate` emission; notice-board `reveals_clue` single payload; `apply_authored_knowledge_realization_to_gm` note `resolution:authored_discovery` appending the clue onto passive scene pressure.

AFFECTED TURNS: 01, 02

PLAYER-FACING SYMPTOMS: the board appears to publish a curfew schedule; examining the curfew section returns the patrol route.

DOWNSTREAM DEPENDENCIES: turn 02's question is motivated by the schedule sentence. The route itself becomes authoritative on turn 02, so the later journey does not depend on the leak alone. Opening seeds already mention curfews, so a player can ask about curfew without turn 01.

EXISTING CAPABILITY OR MISSING CAPABILITY?: Both. Emitting an undiscovered clue and a nonexistent schedule on a failed social probe is an existing realization defect. An inspectable surface with several advertised subjects and one reveal payload cannot say "the hours are not on the board" instead of the other subject. That absence behavior is missing. Authoring the hours would be new content, not a fix for the substitution.

GENERALITY: Any interactable whose label or alias names subject A while `reveals_clue` is subject B. Not specific to the word curfew. `What do the notices say about the curfew?` still parses as `None` (known leading-question residue) and is a different miss; this session's examine-sentence did bind the board.

SEVERITY: Medium. It mis-answers a real question and leaks a clue early. It does not move the player.

SMALLEST GENERAL REPAIR: If the asked detail is not the reveal payload, do not emit that payload as the answer. Say the surface does not state it. Do not author curfew rules in this repair.

ARCHITECTURE EXPANSION REQUIRED?: A document reader is not required for ordinary play. The board can keep one clue. The missing piece is refusing to present that clue as the answer to a different advertised subject.

SHOULD ADDRESS NOW?: No. Record it. The journey integrity bug is the higher lever.

---

## CLUSTER 3 — A general question is answered with whichever fact is available

FIRST AFFECTED TURN: 03

FIRST INCORRECT DECISION: Dimension `general` makes `authored_answer_sufficient_for_question` return true without the fact answering the question. `realize_authored_knowledge_answer` / `apply_authored_knowledge_realization_to_gm` then replaces an ignorance line (`Not something I can say here`, which is treated as concealment) with the discovered patrol sentence. The runner was the correct NPC. `reply_kind` was `refusal`. `topic_revealed` was null. The spoken line is the board clue, not runner topic `patrol_rumor`.

OWNER: authored-knowledge realization. `game/social.py` `authored_answer_sufficient_for_question`, `apply_authored_knowledge_realization_to_gm`.

AFFECTED TURNS: 03. Turn 07 repeats the mechanism: anti-reset's guard line is replaced from `topic_pressure:last_answer`, and the emitted text is the clue payload. Turn 07's reason for asking is cluster 1.

PLAYER-FACING SYMPTOMS: "What should a stranger know to get around?" receives the patrol route inside `Word is`.

DOWNSTREAM DEPENDENCIES: turn 06's phrase `as the runner directed` uses this line. The same direction is already in the discovered clue, so the travel attempt does not exist only because of this answer.

EXISTING CAPABILITY OR MISSING CAPABILITY?: Existing social owner, wrong fact. A grounded refusal was computed and then overwritten. Missing city-guide content is not the defect. A refusal would have been the honest result.

GENERALITY: Any general or weakly subject-tokenized question to an NPC who has, or who just heard, some other true fact. Not specific to Tavern Runner.

SEVERITY: Medium. Authoritative and irrelevant. It aims the player at a real lead for the wrong reason.

SMALLEST GENERAL REPAIR: A known fact must not replace a grounded refusal unless it is sufficient for the asked subject. Dimension `general` is not sufficiency.

ARCHITECTURE EXPANSION REQUIRED?: No knowledge graph and no new city facts.

SHOULD ADDRESS NOW?: Not before cluster 1. It is a real, separate owner defect.

---

## CLUSTER 4 — `to the watch` rebinds the interlocutor

FIRST AFFECTED TURN: 05

FIRST INCORRECT DECISION: `to the watch` matched alias token `watch` on `gate_guard` through directed-prep binding (`_residual_directed_prep_npc_should_bind` / `find_world_npc_reference_id_in_text`). That explicit target beat the active interlocutor. `declared_switch_detected` and `spoken_vocative_detected` are both false. Grounding reason: `authoritative_speaker_eligible_topic_salience_ignored`.

OWNER: NPC reference resolution in `game/interaction_context.py`.

AFFECTED TURNS: 05

PLAYER-FACING SYMPTOMS: Gate Guard shrugs at a reward question the player was asking in the runner conversation.

DOWNSTREAM DEPENDENCIES: none of the geography. The shrug does not invent a reward. Turns 08–09's `The guard says` come from an empty `speaker_label`, not from this NPC id.

EXISTING CAPABILITY OR MISSING CAPABILITY?: Existing identity owner. Alias `watch` is authored. The miss is treating an institutional prepositional phrase as a new addressee while a conversation is open. Probe contrasts: `to the watch` and `to the watch?` bind `gate_guard`; `to the city watch` does not; a reward question with no `to the watch` binds nobody; `to the tavern runner` binds the runner.

GENERALITY: Any short alias that is also an institution, office, or place, inside `to/toward/at the <alias>`, during another NPC's conversation. Not specific to this sentence's other words.

SEVERITY: Medium. Wrong speaker, honest absence of a reward.

SMALLEST GENERAL REPAIR: A prepositional institution mention must not beat an active interlocutor unless the phrase is a vocative, a declared switch, or an ask/address directed at that NPC as a person. Do not delete the alias `watch`.

ARCHITECTURE EXPANSION REQUIRED?: No second NPC router and no rank list.

SHOULD ADDRESS NOW?: No. New evidence, not a reopen of PR-BH's title-token bug. PR-BH still holds for leftover title fragments. This is a different pattern: a full alias inside `to the X`.

---

## Not clusters

- Turn 00 opening. Authorized seeds.
- Turn 04 quantity refusal. Correct. The word `No.` is awkward. Stored generative count stayed `generative_reply` and was not emitted.
- `The guard says` on turns 08–09. Display-only empty `speaker_label`. Known latent helper. It did not store a guard id. It appears because those turns had no owner. Do not reopen PR-BJ to rename it.
- Compound execution. Turn 08 segmented a detail question and executed only `custom`. Already deferred. It amplified the banner turn; it did not create the banner.
- Diegetic clock. Date stayed Day 1. Not this session's break.
- Comprehensive N-action execution. Not required to explain the journey.
