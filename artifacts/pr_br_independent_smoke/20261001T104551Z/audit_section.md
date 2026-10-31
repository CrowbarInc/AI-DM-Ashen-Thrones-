
## PR-BR — Independent 10-Turn Synthetic Smoke Validation

PR-BR remains open. This cycle is validation only. No semantic repair. No prompt change. No rerun. No 4×10 gate. No human playtest. No completion commit. No push.

### 1. Validation purpose

The question was whether the accumulated PR-BR architecture produces a coherent, responsive 10-turn interaction when the player behaves like an ordinary tabletop player. This was a product validation, not a parser test, dimension checklist, evaluator benchmark, or curated regression sequence.

### 2. Independence controls

The player was operated by the validation agent from player-visible text only. Each next action was chosen after that turn's reply. The ten inputs were not written in advance.

The player was not given failure families, regression phrases, contract dimensions, evaluator rubrics, parser branches, or authority branches. The existing synthetic-gate personas and the reactive/adversarial scenarios were not used. Those scripts target the patrol, the notice, watch command, and source/confidence follow-ups.

No separate player model was called. Synthetic-player model calls: 0.

### 3. Clean-session confirmation

YES. Isolated storage under `artifacts/pr_br_independent_smoke/20261001T104551Z/isolated_data`. The player's saved campaign was not reset.

- HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (`PR-BN bounded DM improvisational authority`). PR-BR Continuation 15 is the uncommitted working tree this session ran. No further product edit was applied before or during the run.
- C15 modules present: `game/resolution_contract.py`, `game/discourse_state.py`, `game/semantic_interpreter.py`, `game/interpretation_proposal.py`.
- Session after isolate: campaign/session `9119df19bfba65f7c3a4b830`, scene `frontier_gate`, character Galinor, transcript empty, upstream preflight ok.
- Product path: `POST /api/start_campaign` for the opening, then ten `POST /api/chat` turns.
- Live interpretation left enabled. `evaluate_playability` is local and was the only evaluator.

### 4. Persona

Galinor, a level-1 wandering wizard just arrived at a rainy frontier gate. He looks for food and shelter, talks to people who are actually in front of him, follows a glance or a refusal, and changes approach when an NPC stops helping. Instructions: `artifacts/pr_br_independent_smoke/persona.md`.

### 5. Completed turn count

10 / 10 gameplay turns. The opening narration is not one of the ten. No early stop. The session stayed runnable. It did not stay coherently answered.

### 6. Full player-visible transcript

Opening:

Rain spatters the soot-dark stones above the eastern gate of Cinderwatch, where frayed banners shudder in the chill wind. A well-appointed townhouse overlooks the bustling square, its noble colors standing in quiet contrast to the mud and clamoring masses below. Refugees, laden wagons, and travelers clog the muddy approach, pressed tightly by guards who maintain a determined choke point amid the push. Near a rain barrel, a tavern runner calls out offers of hot stew and paid rumors, hoping to turn the uneasy crowd’s attention into coin. A figure clad in threadbare clothing stands oddly still apart from the line, their gaze flicking with keen scrutiny among packs and faces, betraying a watchfulness at odds with the rest. A notice board near the gate lists new taxes and curfew rules, though the most eye-catching entry is a somber warning about a missing patrol, casting a shadow over the crowded scene.

Turn 1. Motivation: the runner is selling stew in the rain. Intended: price, and a dry place to eat it.

Player: I shoulder through the crowd toward the tavern runner and ask what the stew costs, and whether there is somewhere dry to eat it.

GM: Tavern Runner says with a tight shrug, voice low and hurried,

Turn 2. Motivation: the sentence stopped. Intended: the price and a dry place.

Player: I lean closer so I can hear him over the rain. You started to answer and stopped. How much for a bowl, and where can I eat it out of this weather?

GM: Tavern Runner says, "Look, it's hard to be sure just now, Prices shift with the rumors and the guards' moods, and dry spots to eat? If you want sure warmth, you might need to pay a bit more or know the right people."

Turn 3. Motivation: he named shifting prices and "the right people." Intended: a number, and who those people are.

Player: I keep my voice down. A number, then. What are you charging for one bowl right now, and who are these right people?

GM: Tavern Runner says, "I couldn't tell you I keep my voice down. A number, then. What are you charging for one bowl right n; you will need another source."

Turn 4. Motivation: the runner quoted the player and gave up. Intended: ask a guard how to pass.

Player: I leave the runner and step up to the nearest guard holding the line. I ask, calmly, what a traveler has to do to pass this gate.

GM: The tavern runner replies, voice low and wary, eyes flicking to the guards holding the line.

Turn 5. Motivation: the runner answered a question put to the guard. Intended: ask the guard, not the runner.

Player: I ignore the stew seller. I face the guard holding the line and say it again: I am not asking him. What do I need to show or pay to pass this gate?

GM: Tavern Runner says, voice low and careful. The runner glances past you toward the stern figure managing the crowd, adding,

Turn 6. Motivation: the glance named someone managing the crowd. Intended: ask that person how to get through.

Player: I follow his glance to the stern figure managing the crowd. I walk over and ask that person, directly, what it takes for a traveler to get through this gate.

GM: You approach the stern figure managing the crowd, a guard captain who keeps a sharp eye on the scene. When you ask directly what it takes for a traveler to get through the gate, the guard captain's gaze sharpens. "These days," they say, "it's more than just coin or papers. With the patrol missing and tensions high, we need solid reasons, sometimes proof of connections, or a willingness to pay the proper toll. Each day’s conditions change with the rumors and orders from above. If you have the right allies or can make your case convincingly, you might get through—otherwise, patience and persistence are your best options."

Turn 7. Motivation: the captain offered a toll or a case. Intended: today's toll, and whether paying it is enough.

Player: I nod. I do not have local allies to name. What is the proper toll today, and if I pay it, will you let me through?

GM: No one steps forward to directly answer your question here, and the guards maintain a tight grip on the line without acknowledging any posted toll or passage terms. The notice board nearby lists taxes and curfew rules but does not specify a fixed toll for passage today. The tavern runner’s earlier words hinted that prices and requirements fluctuate with rumors and the moods of the guards. If you want certainty on the proper toll and whether payment now guarantees passage, you might need to find the guard captain managing the crowd—he’s the one who makes the calls and can say what’s needed right now.

Turn 8. Motivation: the reply told the player to find the captain already being addressed. Intended: a toll, or a refusal.

Player: Captain, I am standing in front of you. I asked you, not the crowd. Either name today's toll, or tell me you will not let me through.

GM: "I cannot name a fixed toll today," the guard captain says, his gaze steady but unyielding. "The prices shift with the mood of the guards and what passes through here. Paying does not always guarantee passage. You'll need to prove your business or gain favor by other means." He straightens, signaling that he will not offer more. "If that is unacceptable, then you will not be allowed through."

Turn 9. Motivation: the captain closed the toll. Intended: read the posted curfew.

Player: He is done with me. I step back from the captain and read the notice board, starting with the curfew, so I know whether I can even wait out here.

GM: On closer inspection, the notice board lists taxes, curfew rules, and a warning about a missing patrol. Closer looking yields nothing further.

Turn 10. Motivation: the board did not give a rule, and the still figure from the opening is still unaddressed. Intended: ask whether they are waiting or watching for someone.

Player: The board will not give me the rule. I leave it and walk over to the threadbare figure who has been standing still, watching packs and faces. I ask, quietly, whether they are waiting to get in or watching for someone.

GM: As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line.

### 7. Per-turn contract table

| Turn | Operation | Target | Interlocutor | Dimension | Expected | Contract |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ask | tavern_runner | tavern_runner | none | answer | YES |
| 2 | ask | Tavern Runner | tavern_runner | content | answer | PARTIAL |
| 3 | ask | none | tavern_runner | none | answer | YES |
| 4 | ask | Tavern Runner | tavern_runner | none | answer | NO |
| 5 | ask | Gate Guard | gate_guard | content | answer | PARTIAL |
| 6 | ask | Tavern Runner | none | none | answer | NO |
| 7 | ask | Tavern Runner | gate_guard | content | answer | PARTIAL |
| 8 | ask | none | guard_captain | none | answer | YES |
| 9 | inspect | Notice board | none | none | answer | YES |
| 10 | ask | Guard Captain | guard_captain | none | answer | NO |

Correct 4 / 10. Partial 3 / 10. Incorrect 3 / 10.

Turn 2 asks for a price and a dry place. Operation, target, and interlocutor match. Dimension `content` is the interpreter's label for the substance of a report, and this question is not that. Turn 5 binds the guard, which matches the address, and again labels a practical requirement as `content`. Turn 7 keeps the runner as target, sets interlocutor `gate_guard`, and the player was speaking to the captain. Turns 4, 6, and 10 keep the previous NPC through discourse inheritance after the player changed addressee.

### 8. Per-turn initial-versus-final quality

| Turn | Initial | Final | Evaluator |
| --- | --- | --- | --- |
| 1 | PASS | FAIL | FAIL |
| 2 | PASS | PASS | PASS |
| 3 | PASS | FAIL | PASS |
| 4 | FAIL | FAIL | PASS |
| 5 | FAIL | FAIL | FAIL |
| 6 | PASS | PASS | PASS |
| 7 | FAIL | FAIL | PASS |
| 8 | PASS | PASS | PASS |
| 9 | FAIL | FAIL | PASS |
| 10 | PASS | FAIL | PASS |

Initial candidate manual PASS: 6 / 10. Final player-visible manual PASS: 3 / 10.

The three final passes are the runner's price hedge (turn 2), the captain's passage answer (turn 6), and the captain's refusal of a fixed toll (turn 8).

### 9. Per-turn candidate preservation

Turn 1. Generated: the runner cannot name a price and points to the serjeant by the roster board for shelter. Emitted: an attribution shell that ends on a comma. The answer is gone.

Turn 2. Generated: prices shift, dry spots are scarce, Market Quarter through an archway, or pay more / know people. Emitted: the hedge without the archway. The hedge still answers. The dropped place was not in the scene.

Turn 3. Generated: no solid number, and he will not name the people in this crowd. Emitted: `I couldn't tell you` plus the player's own sentence, cut off, plus `you will need another source.`

Turn 4. Generated: the runner says he cannot state the rule and points at the serjeant or captain. Emitted: the runner glances at the guards. The player had addressed a guard. Both lines use the runner.

Turn 5. Generated: the runner describes permits, tokens, faction ties, or coin, and points at the serjeant. Emitted: the runner starts to add something and stops. The contract had already moved to the gate guard. The model still wrote the runner.

Turn 6. Generated and emitted are the same captain answer. Preserved.

Turn 7. Generated and emitted are the same "no one steps forward / find the captain" stall. Preserved, and already the wrong resolution.

Turn 8. Generated and emitted are the same refusal. Preserved.

Turn 9. Generated: a dusk curfew "less than three hours away," shifting taxes, and the northwest mud-track warning. Emitted: the visible-fact sentence plus `Closer looking yields nothing further.` The dusk hour is not authored. The mud-track line is the scene's inspect clue, and it was removed with the invention.

Turn 10. Generated: the threadbare watcher says they are looking for a particular face and will not say more. Emitted: the visible-fact line about threadbare watchers and refugees. The question is gone.

### 10. Interpretation routing

Deterministic fast-path turns: 7 (1, 3, 4, 6, 8, 9, 10). Fast-path abstentions: 3. Structured interpretation calls: 3. Accepted proposals: 3. Rejected proposals: 0. Clarification outcomes: 0.

| Turn | Fast path | Abstention reason | Interpreter | Proposal result |
| --- | --- | --- | --- | --- |
| 1 | used |  | no | discourse inheritance, runner |
| 2 | abstained | insufficient_discourse_context | yes | accepted, ask / runner / content |
| 3 | used |  | no | deterministic, runner |
| 4 | used |  | no | discourse inheritance, runner |
| 5 | abstained | insufficient_discourse_context | yes | accepted, ask / gate_guard / content |
| 6 | used |  | no | discourse inheritance, target runner |
| 7 | abstained | ambiguous_referent | yes | accepted, not a clarification; gate_guard / content |
| 8 | used |  | no | deterministic, guard_captain |
| 9 | used |  | no | deterministic inspect, notice board |
| 10 | used |  | no | discourse inheritance, guard_captain |

Turn 7's abstention reason was `ambiguous_referent`. The accepted proposal set `ambiguous` false and did not request clarification. The player was not asked which person they meant.

### 11. Discourse-state observations

Active interlocutor stayed `tavern_runner` through turn 5, including turns 4 and 5 where the player said they were leaving him and facing a guard. Turn 6's reply introduced the guard captain in prose, but the slot stayed on the runner with no interlocutor on the contract. Turn 7 set `gate_guard`. Turn 8 set `guard_captain` and kept it through turn 10, after the player had walked to the threadbare figure.

Active claim stayed empty on every turn. The runner's hedge and the captain's toll policy were never stored as claims.

Active inspected object was empty until turn 9, then `notice_board`, and it correctly remained on turn 10.

`last_attempted_action` stayed empty on every turn. Actionable lead stayed empty.

### 12. Authority observations

The bounded-improvisation ledger recorded no proposals on any turn.

Bounded incidental uses: 0. NPC-claim ledger uses: 0. Consequential proposals in the ledger: 0. Authority rejections in the ledger: 0.

Observable grounding outside that ledger:

- Turn 9 tags include `referenced_surface_realization` and `final_emission_gate:passive_scene_pressure_grounded_observe`. `best_safe` was invalidated with `grounding_contradiction`. The invented dusk hour was not emitted. The replacement was the passive "nothing further" line, which also dropped the authored mud-track clue.
- Turn 7 tags include `first_mention_violation:first_mention_missing_grounding` and `anti_reset_continuation_fallback`. The stored model text already matched the emitted stall.
- Turn 10 tags include `referential_clarity_violation:ambiguous_entity_reference`. The watcher's reply was replaced by a scene fact.

NPC speech on turns 6 and 8 stayed in the captain's mouth. It was not restated as narrator fact. The turn 10 invention (a face they are waiting for) was also dialogue, and it never reached the player.

### 13. Semantic-degradation analysis

Manual degradations after generation: 6 (turns 1, 3, 4, 5, 9, 10).

Telemetry degradations: 0. Turn 9 stored no telemetry flag (`null`). The other nine stored false.

Disagreements: 6. On each manual degradation the detector compared the raw model line with the emitted line and did not call it degraded.

Why telemetry missed them:

- Turns 1 and 5: the attribution shell scored `satisfied` / `inquiry_answered` or `covered:content`, at equal or higher rank than the real answer, with `replacement_reason` `resolution_content_preserved`.
- Turn 3: both lines scored `legitimate_nonresolution` at rank 2. The parroted player sentence was treated as the same kind of inability as the real refusal.
- Turns 4 and 9: both lines scored `satisfied` at rank 4.
- Turn 10: the real reply scored `unsatisfied` / `unrelated_fact` because the contract was still the captain. The scene line scored `satisfied` at rank 4. Emission then kept the scene line as a rank improvement (`downgrade_rejected`, `recovery_source: candidate`).

### 14. Best-safe emission analysis

`best_safe_candidate` emission mismatches: 0.

On the damaged turns, the stored best was already the shell, the parrot, the "nothing further" line, or the scene fact. Emission matched that stored best. Turn 9 stored an empty best after the grounding invalidation, so there was no competing best left to emit. The useful model lines were never the stored best at emission time.

### 15. Evaluator and manual comparison

Evaluator PASS: 8 / 10 (turns 2, 3, 4, 6, 7, 8, 9, 10). Evaluator FAIL: 2 / 10 (turns 1 and 5), both `malformed_output` and `player_intent_addressed`. Those two agree with manual review. They are dangling speech attributions.

False PASS: 5 (turns 3, 4, 7, 9, 10). False FAIL: 0.

Turn 4 is the same family as turns 1 and 5, and the evaluator passed it. The shell still has a complete glance sentence, so it is not classified as a dangling attribution.

### 16. Repetition and fallback analysis

YES. A repeated nonresolution family is present.

The same loss shows up four times in social turns: a full spoken answer is reduced to an attribution lead-in. Turns 1, 4, and 5 end before the utterance. Turn 3 fills the inability template in `game/live_resolution.py` (`I couldn't tell you {subject}; you will need another source.`) with the player's own words as the subject.

A second repeated replacement is the grounded scene sentence standing in for the action. Turn 9 uses `Closer looking yields nothing further.` from the referenced-surface inspect line. Turn 10 emits the authored visible fact about threadbare watchers and refugees instead of the conversation.

This is not stylistic repetition. Different requests (price, passage, curfew, the watcher) collapsed into a shell or a scene sentence.

### 17. Cross-turn continuity review

The player's choices were one session: stew, then a number, then the guards, then the person the runner looked at, then the toll, then the curfew, then the still figure.

Referent continuity: NO. The stern figure was resolved in prose on turn 6 and then denied on turn 7. The threadbare figure was never bound.

Interlocutor continuity: NO. The runner remained the addressee after the player left him. The captain remained the addressee after the player left him.

Active-claim continuity: NO. No claim slot was filled, so later turns could not follow a stored claim. They also did not inherit a wrong claim.

Inspected-object continuity: YES. The notice board became the inspected object on turn 9 and was still the inspected object on turn 10.

Previous-action continuity: NO. The previous-action slot stayed empty.

NPC claim versus world truth: YES in the emitted text. The dusk curfew was not published as fact. Captain policy stayed dialogue. No NPC claim was promoted into a narrator fact.

Contradictory detail: turn 6 establishes a conversation with the captain. Turn 7 says no one answered and tells the player to go find that captain.

### 18. Playability review

1. The player side is one coherent session. The DM side often is not. Several replies do not finish, and two later replies deny the person the player is already addressing.
2. The player can understand turns 2, 6, and 8. Turns 1, 3, 4, and 5 do not say what the NPC answered. Turn 7 contradicts turn 6. Turn 9 does not give the curfew. Turn 10 does not show the approach.
3. The DM resolved the immediate attempt on 3 of 10 turns.
4. The world did not stay internally coherent once the captain both spoke and then was described as absent.
5. Prior text mattered on turns 2, 3, 6, and 8, because the player used it and the DM sometimes answered. It did not control interlocutor binding.
6. The player had freedom. The missing-patrol warning was visible in the opening and was not pursued. The player chose stew, passage, the curfew, and the watcher.
7. Ordinary play was derailed by attribution shells, a stuck interlocutor, and scene lines substituted for the action.

Session remained coherently playable: NO.

### 19. Model and API cost accounting

| Call | Count |
| --- | --- |
| Opening narration (`primary_turn` via `/api/start_campaign`) | 1 |
| Gameplay generation | 10 |
| Interpretation | 3 |
| Synthetic player | 0 |
| Evaluator model | 0 |
| Retries | 0 |

Generation purposes on the ten gameplay turns: `strict_social` on turns 1, 2, 3, 4, 5, and 8; `primary_turn` on turns 6, 7, 9, and 10. No `retry_attempt` above 0. No second smoke, no evaluator rerun, no response regeneration.

### 20. Failure-family clustering

Family A, final emission. Useful social answers become attribution shells (turns 1, 4, 5) or the live-resolution inability line with the player utterance inserted as the subject (turn 3). Layer: `final_emission` and `fallback`.

Family B, discourse typing. Fast-path discourse inheritance keeps the previous interlocutor after the player names a new one (turns 4, 6, 10, and the stale target on turn 7). Layer: `discourse_typing`.

Family C, generation against the bound addressee. Turn 5's contract is the gate guard and the model still writes the runner. Turn 7's model says nobody is there and points back at the captain. Layer: `generation`.

Family D, grounded scene replacement. Referenced-surface "nothing further" (turn 9, `speaker_grounding`) and the referential-clarity scene fact (turn 10, `final_emission`) replace a more specific result. Layer: `speaker_grounding` and `final_emission`.

Family E, satisfaction. Shells and scene lines score as answers, so degradation telemetry stays at 0 and `best_safe_candidate` stores the damaged line. Layer: `satisfaction`. The evaluator misses five of the seven manual final failures.

Turn 9's invented dusk hour is a generation fault. Removing it was appropriate. Replacing the whole inspection with "nothing further" was not, because the scene has an inspectable patrol warning.

### 21. Residual defects

- Social answers that the model did produce are being cut down to attribution shells before the player sees them.
- The inability fallback can quote the player inside the NPC's mouth.
- Discourse inheritance does not move when the player changes person.
- A correct reply to the new person can be scored unrelated against the stale contract, and a scene sentence can then outrank it.
- Degradation telemetry does not see those losses.
- The evaluator catches dangling attributions and misses the same loss when the shell still forms a sentence, and it passes scene-line substitutions.
- Previous-action and active-claim slots did not record this session's actions or NPC statements.

These are recurring. They are not one model-quality miss.

### 22. Readiness recommendation

READY FOR FULL SYNTHETIC GATE: NO.

Final manual PASS is 3 / 10, under the recommended 8 / 10. The attribution-shell family and the stale-interlocutor family both recur. Manual semantic degradation is 6 and systemic, not isolated. Best-safe emission mismatches are 0 only because the stored best was already the weaker line. There was no state-integrity crash. The session was not coherently playable through the answers.

Do not treat the 0 emission-mismatch count or the 8 / 10 evaluator PASS as readiness. Manual review is authoritative.

### 23. PR-BR status

PR-BR: STILL OPEN.

No completion commit. No push. No PR-BS. Human playtest is not authorized. A further continuation is warranted before any full synthetic gate. This cycle does not specify that repair and does not rerun the smoke.
