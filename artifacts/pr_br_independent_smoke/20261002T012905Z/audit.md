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
