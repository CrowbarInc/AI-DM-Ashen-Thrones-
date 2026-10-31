# ATGB-01 Scenario Catalog

Date: 2026-10-18
Status: historical proposal. Scenario wording below is the source for the ATGB-02 fixtures. The index still lists S07 as development-visible. ATGB-02 moves that scenario, unchanged, to held-out. See `development/reports/atgb_02_benchmark_specification.md`.
Corpus id: `ATGB-01`

This catalog defines ten conversations and 37 scored player turns. It is the proposal reviewed by `development/reports/atgb_01_conversational_benchmark_design.md`. Nothing here has been run.

Shared rules for every scenario:

- Initial state is a fresh `frontier_gate` in an isolated data directory. No scenario inherits another scenario's transcript.
- The engine opening, if shown, is unscored context.
- Exact prose is not required. A reply passes when it does the communicative job and stays inside the fact list below.
- Hearsay must stay hearsay. The runner "heard" a rumor. The notice and the serjeant report a posted or stated fact. Merging those into one witness is an authority failure.
- Hidden facts must not appear: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.
- Unauthored, so grounded uncertainty is success: curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran.
- Owned sentences, which a paraphrase may carry:
  - `gate_guard` / `watch_command`: Captain Thoran commands the gate watch tonight.
  - `gate_serjeant` / `route_change`: the patrol route changed after the Ash Compact census choke worsened.
  - `tavern_runner` / `patrol_rumor`: the runner heard the patrol vanished near muddy footprints northwest of the crates.
  - Notice clue `notice_patrol_route`, only after the board is actually investigated: the missing patrol was last seen taking the northwest mud track past the crates.
- Visible without investigation: taxes, curfew rules, and a missing-patrol warning on the board; the serjeant managing the crowd and watching the roster board; hot stew and rumors at the rain barrel; watchers and refugees on the muddy line; census delays tightening the eastern caravan choke; frayed banners in the opening description.
- Exits, if travel is actually resolved: Enter Cinderwatch → `market_quarter`; Follow the missing patrol rumor → `old_milestone`. None of these player lines is an instruction to take an exit.
- Cross-cutting evidence for every turn: player line, player-facing reply, communication mode, conversational decision if present, resolution kind, addressee, scene id before and after, clue and world-flag delta, performance record with nulls preserved, and the three results plus severity, clarification tag, and continuity tag.
- Determinism: mixed, unless a turn note says a host fast path is likely. Live interpretation defaults on. Naturalness is judged on the live lane only.

Scoring shorthand used in each turn:

- Interpretation, response, and authority are separate.
- Acceptable means response pass and authority pass.
- Clarification tags: `none`, `necessary_pass`, `unnecessary_fail`, `missing_when_needed_fail`.
- Continuity tags: `not_applicable`, `preserved`, `lost`.

## Index

| Scenario | Class | Primary capability | Turns | Shape |
| --- | --- | --- | ---: | --- |
| S01 Gate small talk | development-visible | Intent recognition | 4 | Ordinary arrival |
| S02 The notices | development-visible | Response relevance | 4 | Read, correct, recall |
| S03 The runner's account | development-visible | NPC dialogue coherence | 5 | Rumor, source, commitment, comparison |
| S04 The serjeant | development-visible | Corrections | 4 | Addressee and relevance |
| S05 Two accounts | development-visible | Ambiguity handling | 4 | Notice versus rumor |
| S06 Beside the table | development-visible | IC/OOC boundaries | 4 | Mode switches |
| S07 In the queue | development-visible | Initiative and naturalness | 4 | Small talk into a question |
| S08 Same gate, other words | related variation | Intent recognition | 4 | Paraphrase of visible requirements |
| S09 The quiet pair | held-out | Ambiguity handling | 2 | Two bystanders |
| S10 The barrel | held-out | Ambiguity handling | 2 | Thing versus offer |

Primary-capability counts: intent 5, continuity 5, corrections 5, relevance 5, NPC dialogue 5, IC/OOC 4, ambiguity 4, initiative 4.

## S01 — Gate small talk

1. Identifier: `S01`
2. Primary capability: intent recognition
3. Secondary: response relevance, initiative, authority
4. Initial context: fresh gate. No interlocutor selected. No clue discovered.
5. Authoritative facts: the shared visible list. Thoran's sentence belongs to `gate_guard`. Stew quality and price are unauthored. The offer of hot stew and rumor is visible.
6. NPC knowledge: nobody has spoken. Hidden facts stay hidden. A speaker who does not own `watch_command` does not know a commander beyond what the visible watch presence supports, and does not invent a name.
7. Player inputs: four, below.
8. Expected outcomes: a look is treated as looking; a watch question is treated as a question; a stew remark is not answered with the patrol; a "just looking" line ends the pressure.
9. Acceptable variation: GM narration or an NPC remark, as long as the job and the facts hold. One sensory detail already in the opening is enough for the look.
10. Unacceptable: a journey, a new location, a hidden fact, a price, a commander other than Thoran stated as fact, or a command menu in place of a reply.
11. Scoring: per turn below. Scene remains `frontier_gate`. No new clue is required; discovering `notice_patrol_route` on the look, without a board investigation, is an authority failure.
12. Evidence: the shared turn packet. State diff must show no scene change.
13. Setup dependency: `guard_captain` and `gate_guard` are different ids. S01.2 must not be failed solely because the host asks which watch member the player means.
14. Determinism: mixed. S01.2 and S01.3 are provider-dependent if the host does not already hold a grounded answer.

### S01.1 — primary: intent recognition

Player: `I look around the gate.`

This is an action, not a question.

- Interpretation pass: observation of the current scene.
- Response pass: at least two visible public facts, in place.
- Authority pass: no exit, no hidden fact, no invented building the player then occupies.
- Clarification: `none`. Asking the player what they want to look at is `unnecessary_fail`.
- Continuity: `not_applicable`.

### S01.2 — primary: intent recognition

Player: `Who's running the watch tonight?`

This is a question in ordinary speech.

- Interpretation pass: information question, not travel and not combat.
- Response pass: either the owning speaker reports that Captain Thoran commands the gate watch tonight, or one focused clarification asks whom to address, or a speaker without that fact says they cannot name the commander.
- Authority pass: no other personal name is introduced as the commander. No new post, order, or biography.
- Clarification: `necessary_pass` only if no addressee can own the fact yet. `unnecessary_fail` if the owning speaker is already bound and the reply still asks.
- Continuity: `not_applicable`.

### S01.3 — primary: response relevance

Player: `Is the stew any good, or are you just shouting?`

- Interpretation pass: a question about the visible stew offer, addressed to the runner if an addressee is chosen.
- Response pass: stays on stew or on the fact that the runner is hawking stew and rumor. Quality may be unknown.
- Authority pass: no price, no serving, no coin. The patrol route is not the answer.
- A reply that only restates the missing-patrol warning fails response even if that warning is true.
- Clarification: `none` expected. `unnecessary_fail` if the player is asked whether they meant stew or the weather.
- Continuity: `not_applicable`.

### S01.4 — primary: initiative and naturalness

Player: `Fair enough. I'm just getting a sense of the place.`

- Interpretation pass: withdrawal from the previous topic, not a new investigation order.
- Response pass: a short in-character acknowledgement. The patrol briefing does not restart. The player is not told to type a command.
- Authority pass: no scene change and no new clue.
- Clarification: `none`. A menu of "ask questions / investigate further" is `unnecessary_fail` and a major response failure.
- Continuity: `preserved` if the reply does not resurrect a topic the player just set down. `lost` if it resumes the stew pitch or the watch question as though the player asked again.

## S02 — The notices

1. Identifier: `S02`
2. Primary capability: response relevance
3. Secondary: intent recognition, corrections, continuity, authority
4. Initial context: fresh gate. The board has not been read.
5. Authoritative facts: the board lists taxes, curfew rules, and a missing-patrol warning. Hours are not authored. Investigating `notice_board` may reveal `notice_patrol_route`.
6. NPC knowledge: the board is an object. An NPC who has not been given the clue does not gain it by standing nearby. The runner's rumor is a different sentence and is not a substitute for the posted warning.
7. Player inputs: four, below.
8. Expected outcomes: the read reports the posted categories; the hour question does not become the patrol answer; the correction keeps the hour question; the later question recalls the posted last-seen line.
9. Acceptable variation: if the investigation reveals the northwest track, the read may include it. If it only lists the three posted categories, that is also a successful read. The hour question is successful only as uncertainty or as a statement that the hours are not posted.
10. Unacceptable: dusk-until-dawn, a fine, bandits, a statute number, or answering S02.2 or S02.3 with the crate track.
11. Scoring: per turn. S02.2 is the distinction between a true nearby fact and an answer.
12. Evidence: shared packet, plus whether `notice_patrol_route` entered discovered clues, and on which turn.
13. Setup dependency: content questions about the board have historically missed investigation and been narrated freely. The benchmark records that outcome. It does not require a new board owner in order to score.
14. Determinism: mixed.

### S02.1 — primary: intent recognition

Player: `I read the notices.`

- Interpretation pass: investigate or read the notice board, not a social question to the runner.
- Response pass: taxes, curfew rules, and a missing-patrol warning, or the revealed route clue plus those categories.
- Authority pass: no hours, fines, or causes that are not in the clue text. Revealing `notice_patrol_route` on this investigation is authorized. Revealing a hidden fact is not.
- Clarification: `none`.
- Continuity: `not_applicable`.

### S02.2 — primary: response relevance

Player: `When does the curfew start?`

- Interpretation pass: a time question about the curfew.
- Response pass: the start time is not known or not posted. The player is not handed a different fact in its place.
- Authority pass: no clock hour and no penalty.
- An accurate patrol sentence on this turn fails response and, if it is presented as the curfew answer, stays a response failure even when the sentence itself is owned.
- Clarification: `none`.
- Continuity: `preserved` if the reply still knows the player is asking about the board they just read. `lost` if it switches speaker and topic without reason.

### S02.3 — primary: corrections and clarifications

Player: `I wasn't asking where the patrol went. I asked when it starts.`

- Interpretation pass: correction of S02.2.
- Response pass: returns to the start time and keeps the uncertainty. It does not repeat the route as the answer.
- Authority pass: still no invented hour.
- Clarification: `none`. The player has already clarified.
- Continuity: `preserved` when the hour question survives. `lost` when the route replaces it again.

### S02.4 — primary: conversational continuity

Player: `All right. What did the warning say about where they were last seen?`

This refers to the board from S02.1, after the curfew detour.

- Interpretation pass: recall of the posted warning, not a new rumor request.
- Response pass: the northwest mud track past the crates, if that clue was revealed in S02.1. If S02.1 never revealed it, the reply says the warning names a missing patrol and does not add a place, or it investigates now and then reports the clue.
- Authority pass: the place comes from `notice_patrol_route` or is withheld. The runner's footprint sentence is not quoted as the notice.
- Clarification: `none`, unless S02.1 produced no warning at all, in which case one question ("the notice, or someone in the crowd?") is `necessary_pass`.
- Continuity: `preserved` only if the notice from S02.1 is the referent. `lost` if the referent becomes the runner or an empty "I don't know" after the clue was already delivered.

## S03 — The runner's account

1. Identifier: `S03`
2. Primary capability: NPC dialogue coherence
3. Secondary: continuity, corrections, authority
4. Initial context: fresh gate. No active interlocutor.
5. Authoritative facts: the runner's only owned topic is the footprint rumor, as hearsay. The notice's track sentence is not this NPC's topic unless the player introduces it, as S03.4 does.
6. NPC knowledge: Tavern Runner may say the heard rumor. The runner does not have an authored source, an authored price, or an authored promise of a second rumor. A commitment to repeat this same rumor is compatible with `current_agenda: sell_rumors`. A commitment to a new secret is not.
7. Player inputs: five, below.
8. Expected outcomes: the runner is the speaker; the rumor stays hearsay; the source is unknown; the same rumor can be repeated later; the notice comparison does not weld the two accounts into one witness.
9. Acceptable variation: the runner may mention that stew is also on offer, then answer the rumor. Another speaker describing what the runner is hawking can pass S03.1 only if the player is not left talking to the wrong person on S03.2.
10. Unacceptable: Gate Guard or Gate Serjeant delivering this rumor as their own knowledge; a named informant; a coin price; a new faction; the Thoran sentence; the route-change sentence spoken as the runner's rumor.
11. Scoring: per turn. S03.4 is a continuity turn whose facts are similar on purpose.
12. Evidence: shared packet plus speaker id on each turn.
13. Setup dependency: question-only lines can collapse to the sole world NPC in some older paths. Here the player names the runner. Binding anyone else is an interpretation failure, not an excuse.
14. Determinism: provider-dependent for wording; the addressee and the owned sentence are host-checkable when the social path binds `tavern_runner`.

### S03.1 — primary: NPC dialogue coherence

Player: `Tavern runner, what's the rumor you're selling?`

- Interpretation pass: social question to `tavern_runner`.
- Response pass: the footprint rumor, marked as heard or sold rumor, not as a confirmed sighting by the player.
- Authority pass: no extra witness, place, or time.
- Clarification: `none`.
- Continuity: `not_applicable`.

### S03.2 — primary: NPC dialogue coherence

Player: `Who told you that?`

- Interpretation pass: source question about the rumor just given.
- Response pass: the runner does not name a source. Uncertainty or a refusal to invent one.
- Authority pass: no new proper noun.
- Clarification: `none`.
- Continuity: `preserved` if "that" is the rumor from S03.1. `lost` if the runner answers about Thoran, the curfew, or a different story.

### S03.3 — primary: NPC dialogue coherence

Player: `If I ask you again later, will you still tell me that same thing?`

- Interpretation pass: a commitment question, not a purchase and not a request for a new rumor.
- Response pass: the runner can repeat this rumor, or says they only have this one. The answer is about the same claim.
- Authority pass: no price, no second secret, no quest.
- Clarification: `none`.
- Continuity: `preserved` when the commitment refers to the footprint rumor. `lost` when the runner commits to a story that was never told.

### S03.4 — primary: conversational continuity

Player: `Earlier the notice said they took a track past the crates. Is that the same story you heard?`

The player brings the notice content into this conversation. The scenario does not depend on S02.

- Interpretation pass: comparison of two accounts.
- Response pass: they are similar and not identical. The runner heard footprints northwest of the crates. The notice line, as the player stated it, is the track past the crates. The reply may say the runner cannot confirm the notice.
- Authority pass: no claim that one person saw both, and no denial that the runner just told the footprint rumor.
- Clarification: `none`.
- Continuity: `preserved` for the S03.1 rumor. The notice clause is in the player's current line, so forgetting the rumor is the continuity failure that matters.

### S03.5 — primary: corrections and clarifications

Player: `No, I don't want a new rumor. I want to know if those two accounts match.`

- Interpretation pass: correction that rejects a new story and repeats the comparison.
- Response pass: the match question is answered as in S03.4, briefly.
- Authority pass: still no welded witness and no new rumor.
- Clarification: `none`.
- Continuity: `preserved` if both accounts remain the footprint rumor and the track-past-the-crates line. `lost` if either account is replaced.

## S04 — The serjeant

1. Identifier: `S04`
2. Primary capability: corrections and clarifications
3. Secondary: intent recognition, relevance, NPC dialogue, authority
4. Initial context: fresh gate. No interlocutor.
5. Authoritative facts: `gate_serjeant` owns the route-change sentence. The eastern choke from census delays is a visible fact. The route change is a consequence of that choke worsening. The catalog does not authorize "the route change is why the wagons are stuck." Thoran's sentence is a different NPC's fact.
6. NPC knowledge: the serjeant may report the route change. The serjeant has no authored knowledge of Thoran's private awareness. The serjeant does not know who gave the order.
7. Player inputs: four, below.
8. Expected outcomes: `gate_serjeant` is bound when named; a wrong speaker is corrected by the second line; the wagon question is answered from the census choke, not by repeating the route sentence alone; the last line stays inside the owned sentence.
9. Acceptable variation: on S04.1 a correct serjeant answer means S04.2 may simply confirm the serjeant and restate the fact. That confirmation passes.
10. Unacceptable: binding `gate_guard` or `guard_captain` after the player says Gate Serjeant; inventing an order, a meeting, or a clock; answering the wagon question with only "the route changed" and never mentioning the choke or the wagons.
11. Scoring: per turn. S04.3 fails response if the owned route sentence is delivered and the wagon question is ignored.
12. Evidence: shared packet plus speaker id. S04.2 records whether the speaker changed after the correction.
13. Setup dependency: alias coverage for "serjeant" and "gate serjeant" is already authored. The scenario uses that ordinary address. It is not a request for a rank ontology.
14. Determinism: mixed.

### S04.1 — primary: intent recognition

Player: `Serjeant, did the patrol's route change?`

- Interpretation pass: question to `gate_serjeant`.
- Response pass: the route changed after the Ash Compact census choke worsened.
- Authority pass: no extra cause, order, or destination.
- Clarification: `none`.
- Continuity: `not_applicable`.

### S04.2 — primary: corrections and clarifications

Player: `I said the Gate Serjeant, not the captain and not the guard.`

- Interpretation pass: addressee correction.
- Response pass: the serjeant is the speaker, and the route-change fact is the content if anything is repeated.
- Authority pass: Thoran may be named only to set him aside. He does not become the answer.
- Clarification: `none`.
- Continuity: `preserved` if the route question remains. `lost` if the correction starts a new topic.

### S04.3 — primary: response relevance

Player: `Is that why the eastern wagons are stuck?`

- Interpretation pass: a cause question about the wagons, using the census choke already in play.
- Response pass: the census delays are why the eastern choke is tight. The route change is another result of that choke, not the cause of the jam, unless the reply explicitly says it does not know which caused which and states only the two owned pieces.
- Authority pass: no blockade, no count of wagons, no hour of delay.
- A reply that only repeats the route-change sentence fails response.
- Clarification: `none`.
- Continuity: `preserved` if "that" can still be the route change or the choke from S04.1. `lost` if "that" becomes Thoran or the stew.

### S04.4 — primary: NPC dialogue coherence

Player: `Say that again, but only what you actually know.`

- Interpretation pass: a request to restate the serjeant's own limited knowledge.
- Response pass: the route-change sentence, and nothing past it. Uncertainty on the wagon cause may remain one clause.
- Authority pass: no new personnel and no new order.
- Clarification: `none`.
- Continuity: `preserved` for the serjeant and the route sentence.

## S05 — Two accounts

1. Identifier: `S05`
2. Primary capability: ambiguity handling
3. Secondary: NPC dialogue, continuity, corrections
4. Initial context: fresh gate.
5. Authoritative facts: the runner's rumor and, once the board is read, `notice_patrol_route`. Both point near the crates and the northwest approach. They are different sentences and different sources.
6. NPC knowledge: the runner knows the rumor as hearsay. The board holds the posted warning. Neither may absorb the other's wording.
7. Player inputs: four, below.
8. Expected outcomes: the runner answers first; the board is consulted second; "that" is then ambiguous; the player's choice of the runner is honored.
9. Acceptable variation: S05.3 may pick neither account and ask. It may not pick one and call the choice obvious.
10. Unacceptable: the same paragraph presented as both the notice and the rumor; a third story; the guard answering S05.4.
11. Scoring: S05.3 is a successful turn when the clarification is necessary and focused. Guessing is a major failure.
12. Evidence: shared packet, including the clarification text and the player's S05.4 choice.
13. Setup dependency: pronoun follow-up is not last-answer authority for `they` / `it`. "That" after two delivered accounts is supposed to be ambiguous. A host that continues only the latest account has lost the earlier one; score continuity `lost` and clarification `missing_when_needed_fail`.
14. Determinism: mixed. The ambiguity decision is host-checkable when both accounts are in the delivered transcript and the reply asks.

### S05.1 — primary: NPC dialogue coherence

Player: `Runner, what did you hear about the patrol?`

- Interpretation pass: `tavern_runner`.
- Response pass: the footprint rumor as hearsay.
- Authority pass: no notice wording presented as what the runner heard.
- Clarification: `none`.
- Continuity: `not_applicable`.

### S05.2 — primary: conversational continuity

Player: `And the board, what does it say about the same patrol?`

- Interpretation pass: a shift from the runner to the notice board, same patrol topic.
- Response pass: the posted warning, including the northwest track once the board is investigated.
- Authority pass: the runner is not quoted as the board.
- Clarification: `none`.
- Continuity: `preserved` if "the same patrol" is the patrol from S05.1. `lost` if the board answer changes the subject to taxes only, or if the runner's sentence is repeated unchanged and called the notice.

### S05.3 — primary: ambiguity handling

Player: `Tell me more about that.`

- Interpretation pass: the referent is unresolved between the rumor and the notice.
- Response pass: one question that names both, or otherwise distinguishes them. No new facts.
- Authority pass: no additional detail about either account.
- Clarification: `necessary_pass`. Continuing only the latest line without acknowledging the other is `missing_when_needed_fail`.
- Continuity: `preserved` if both accounts are still available to name. `lost` if one has vanished.

### S05.4 — primary: corrections and clarifications

Player: `The runner's version, not the notice.`

- Interpretation pass: the player resolved S05.3 in favor of the runner.
- Response pass: the footprint rumor only, still hearsay.
- Authority pass: the track-past-the-crates sentence is not substituted.
- Clarification: `none`. Asking again is `unnecessary_fail`.
- Continuity: `preserved` for the runner's account from S05.1.

## S06 — Beside the table

1. Identifier: `S06`
2. Primary capability: IC/OOC boundaries
3. Secondary: intent recognition, authority, NPC dialogue
4. Initial context: fresh gate. No purchase system is in play.
5. Authoritative facts: talking does not itself change scene or discover the route clue. Hot stew is a visible offer. The rumor is the runner's owned hearsay. There is no price and no inventory transaction.
6. NPC knowledge: OOC turns are answered by the GM or session voice. They are not answered by the runner. IC turns return to the runner when the player addresses the runner.
7. Player inputs: four, below.
8. Expected outcomes: the OOC questions do not execute play; the IC question is in character; the disclaimer prevents a purchase; the last line delivers the rumor and not a bowl of stew.
9. Acceptable variation: an OOC reply may be short. It does not have to use a particular stock sentence. It does have to answer the question that was asked.
10. Unacceptable: validator phrases such as "based on what's established" are a response defect under the AI GM contract, scored minor if the answer is otherwise present and major if they replace the answer. A narrated purchase, a coin change, or a scene move is critical. An OOC lecture that continues after the player has said `IC:` fails the IC turn.
11. Scoring: interpretation can pass on a recognized OOC turn while response fails if the reply is only a generic invitation to ask rules questions.
12. Evidence: shared packet plus `authoritative_mutation`, scene id, clues, and any inventory or world-flag delta. A host path that skips narration records provider calls as zero when that is what the response says.
13. Setup dependency: explicit `OOC:` and `IC:` prefixes are recognized by the current communication-mode parser. Some OOC bodies also hit a non-mutating acknowledgement that does not answer the specific question. That acknowledgement is interpretable as OOC and still has to meet the response criterion.
14. Determinism: S06.1 and S06.3 are often host-deterministic. S06.2 and S06.4 are mixed. Naturalness of the IC lines is live-lane only.

### S06.1 — primary: IC/OOC boundaries

Player: `OOC: if I talk to people here, does that spend game time or change the scene?`

- Interpretation pass: OOC, non-mutating.
- Response pass: a direct OOC answer. Talk at this gate does not travel and does not resolve an exit. The reply may say that a chat turn exists without claiming that hours passed.
- Authority pass: scene stays `frontier_gate`, no clue is added, no NPC is forced into a conversation by this line.
- A stock sentence that only says "ask your rules questions normally," and never addresses time or scene, fails response and can pass interpretation.
- Clarification: `none`.
- Continuity: `not_applicable`.

### S06.2 — primary: IC/OOC boundaries

Player: `IC: I ask the runner whether the stew is hot.`

- Interpretation pass: in-character question to `tavern_runner`.
- Response pass: in character, about the stew. The visible offer is hot stew. A one-line yes grounded in that offer passes. A quality review or a price does not.
- Authority pass: no serving and no coin.
- Clarification: `none`.
- Continuity: `preserved` if the OOC policy talk has stopped. `lost` if the reply continues S06.1.

### S06.3 — primary: IC/OOC boundaries

Player: `OOC: that was only a question. I am not buying anything.`

- Interpretation pass: OOC correction. No transaction.
- Response pass: confirms that nothing was bought and that the scene is unchanged.
- Authority pass: no inventory delta and no price.
- Clarification: `none`.
- Continuity: `preserved` for "that" = the stew question.

### S06.4 — primary: IC/OOC boundaries

Player: `Back in character. Runner, I'll hear the rumor, not buy the stew.`

- Interpretation pass: IC request to `tavern_runner` for the rumor, refusing the stew.
- Response pass: the footprint rumor as hearsay. Stew is not served.
- Authority pass: no purchase, no coin, no second rumor.
- Clarification: `none`.
- Continuity: `preserved` if the refusal of the stew is honored.

## S07 — In the queue

> Partition supersession: ATGB-02 moves S07 to held-out. The original designation
> is retained below as historical design evidence. The current machine-readable
> corpus is authoritative for execution; scenario wording is unchanged.

1. Identifier: `S07`
2. Primary capability: conversational initiative and naturalness
3. Secondary: relevance, authority
4. Initial context: fresh gate, opening description available, including rain and frayed banners. The runner is visibly hawking.
5. Authoritative facts: rain, queue, frayed banners, stew, and rumor. No patrol question has been asked.
6. NPC knowledge: no one is required to volunteer the route clue, Thoran, or the route change.
7. Player inputs: four, below.
8. Expected outcomes: small talk stays small; the banner remark does not become a dossier; the shout is identified as stew and rumor; the correction drops the rumor.
9. Acceptable variation: one grounded hook, such as the crush or the runner's shout, may appear inside S07.1. It is an offer, not a briefing.
10. Unacceptable: an unprompted patrol report, a three-item command menu, anti-echo that consumes the whole reply, invented crowd dialogue about why refugees fled.
11. Scoring: minor stiffness can leave a turn acceptable. A menu or a dossier is major.
12. Evidence: shared packet. Narration-quality notes sit in the severity field.
13. Setup dependency: local small talk has no separate mechanical owner. Success is a non-mutating conversational reply. The scenario does not require a mood system.
14. Determinism: provider-dependent for naturalness. Host lane may show non-mutation and must leave naturalness unchecked.

### S07.1 — primary: initiative and naturalness

Player: `Miserable rain for a queue this long.`

- Interpretation pass: in-character remark, not an investigation command.
- Response pass: a human-scale reply about the rain or the queue. At most one grounded hook.
- Authority pass: no travel and no new fact.
- Clarification: `none`.
- Continuity: `not_applicable`.

### S07.2 — primary: initiative and naturalness

Player: `The banners look about finished.`

- Interpretation pass: continuation of the observation. Frayed banners are already in the opening.
- Response pass: stays with that observation for a beat. Does not open the missing-patrol briefing.
- Authority pass: no new heraldry and no noble house.
- Clarification: `none`. `unnecessary_fail` if the player is asked to choose a mechanical action.
- Continuity: `preserved` if the queue conversation is still the conversation.

### S07.3 — primary: initiative and naturalness

Player: `The one shouting — what's he offering?`

- Interpretation pass: a shift to the runner's visible offer. Binding `tavern_runner` is appropriate. A GM description of the shout also passes if the offer is right.
- Response pass: hot stew and rumor.
- Authority pass: no price and no patrol destination beyond the fact that a rumor is on offer.
- Clarification: `none`, unless several people are shouting, which the visible scene does not support. Inventing a second hawker is an authority failure.
- Continuity: `preserved` for the gate. The player did not ask to leave.

### S07.4 — primary: response relevance

Player: `Leave the rumor. I only wanted to know what he's selling.`

The visible offer includes both stew and rumor, and the player now narrows it.

- Interpretation pass: correction toward the food offer.
- Response pass: stew, without the patrol story.
- Authority pass: no price and no bowl placed in inventory.
- Clarification: `none`.
- Continuity: `preserved` if the shouting runner from S07.3 is still the seller.

## S08 — Same gate, other words

1. Identifier: `S08`
2. Primary capability: intent recognition
3. Secondary: corrections, relevance, continuity
4. Initial context: fresh gate. This is a related variation, not a held-out scenario. The requirements match S01, S02, and S04. The words do not.
5. Authoritative facts: the same visible list and the serjeant's route-change sentence. Who issued the change is unauthored.
6. NPC knowledge: the serjeant, once addressed by the conversation, knows the route change and the census choke as the setting of that change. The serjeant does not know the official who ordered it.
7. Player inputs: four, below.
8. Expected outcomes: a question-shaped look still looks; a correction toward people is honored; the crowd-handler is the serjeant from the visible fact; the follow-up recalls the choke and withholds the official.
9. Acceptable variation: any grounded description, any wording of the route-change fact.
10. Unacceptable: treating S08.1 as travel; describing only the rain after the player asks for the people; naming an official; answering "who handles the crowd?" with the runner.
11. Scoring: these turns are reported in the related-variation column. They are not independent generalization.
12. Evidence: shared packet, labeled `related_variation`.
13. Setup dependency: none beyond the fresh gate. Do not chain this scenario after S04.
14. Determinism: mixed.

### S08.1 — primary: intent recognition

Player: `What's in front of me right now?`

Variation of a look, in question form.

- Interpretation pass: current-scene observation.
- Response pass: present public facts, not a history of the patrol.
- Authority pass: no hidden fact and no scene change.
- Clarification: `none`.
- Continuity: `not_applicable`.

### S08.2 — primary: corrections and clarifications

Player: `I meant the people, not the weather.`

- Interpretation pass: correction of S08.1 toward the people present.
- Response pass: names people who are actually there, from the visible set: serjeant, runner, watchers, refugees, guards. Weather may be dropped.
- Authority pass: no invented traveler with a name and a story.
- Clarification: `none`.
- Continuity: `preserved` for the look the player is correcting.

### S08.3 — primary: response relevance

Player: `Which person looks like they handle the crowd?`

- Interpretation pass: a question about the visible crowd-handler.
- Response pass: the gate serjeant, who is described as managing the crowd. The roster board may be mentioned because the same visible sentence includes it.
- Authority pass: no rank promotion and no claim that the serjeant commands the watch. That command sentence belongs to Thoran's topic.
- Clarification: `none`.
- Continuity: `preserved` if the people from S08.2 are the set being narrowed.

### S08.4 — primary: conversational continuity

Player: `You just said the route changed because the choke got worse. Who changed it?`

The player attributes a route statement to the reply. If S08.3's reply never said that, the line is still a question about who changed the route, and the serjeant fact may be stated once before the gap.

- Interpretation pass: a who-question about the agent of the change.
- Response pass: the choke worsened and the route changed; the person who ordered it is not known.
- Authority pass: no name, no office, no "the captain ordered it."
- Clarification: `none`.
- Continuity: `preserved` if a route or choke statement was made and is still the topic. If no such statement was made, continuity is `not_applicable` and the turn is only the unauthored who-question. Inventing the missing statement in order to agree with the player is an authority failure.

## S09 — The quiet pair

1. Identifier: `S09`
2. Primary capability: ambiguity handling
3. Secondary: NPC dialogue, authority
4. Initial context: fresh gate. Held-out. Not a tuning set.
5. Authoritative facts: the ragged stranger and the threadbare watcher are both present addressables. Neither has an owned topic in `world.json`. The stranger hangs back and watches the crowd. The watcher stands still, gaze moving to packs and faces. Neither has an authored name beyond those labels, and neither owns the patrol rumor.
6. NPC knowledge: neither bystander has an authored answer to who they are beyond the public label. Delivering the runner's rumor in either voice is an authority failure. Delivering a hidden fact is critical.
7. Player inputs: two, below.
8. Expected outcomes: the first line is ambiguous between two people and is clarified; the second line selects the watcher; no patrol story is borrowed.
9. Acceptable variation: the clarification may be in character or a single concise OC line. Either person may be described with the visible posture cues while the question is asked.
10. Unacceptable: answering as the tavern runner; inventing personal names; stating how long either has stood there; revealing the signal, the face list, the noble agent, or the Ash Cowl contact.
11. Scoring: reported only in the held-out column.
12. Evidence: shared packet, labeled `held_out`.
13. Setup dependency: the engine is not required to role-play two NPCs in one reply. One clarifying question is the successful path. A crowd conversation system is unsupported and is not a pass condition.
14. Determinism: mixed. A host clarification that names both people is host-checkable. What the chosen NPC then says, if anything, is live-lane.

### S09.1 — primary: ambiguity handling

Player: `I ask either the ragged stranger or the threadbare watcher who they are.`

- Interpretation pass: the addressee is unresolved between those two ids, `refugee` and `threadbare_watcher`.
- Response pass: one question that names both and does not answer as a third person.
- Authority pass: no biography.
- Clarification: `necessary_pass`.
- Continuity: `not_applicable`.

### S09.2 — primary: ambiguity handling

Player: `The threadbare watcher.`

- Interpretation pass: `threadbare_watcher` is now the addressee, and the pending question is who they are.
- Response pass: the public label is the available identity. The reply does not invent a personal name or a secret role.
- Authority pass: no hidden fact. The runner's rumor is not moved into this mouth.
- Clarification: `none`. Asking the same choice again is `unnecessary_fail`.
- Continuity: `preserved` if the who-question from S09.1 is what gets answered.

## S10 — The barrel

1. Identifier: `S10`
2. Primary capability: ambiguity handling
3. Secondary: continuity, relevance, authority
4. Initial context: fresh gate. Held-out. The rain barrel and the runner's offer are visible. Nothing has been said yet.
5. Authoritative facts: the runner trades hot stew and rumors beside the rain barrel. The non-food half of that offer is the rumor, whose content is the footprint hearsay once the runner is actually asked. The barrel is not an interactable with a clue.
6. NPC knowledge: the runner knows the owned rumor when the rumor is requested. The barrel has no knowledge.
7. Player inputs: two, below.
8. Expected outcomes: "the thing by the barrel" is not quietly resolved into travel, a purchase, or a single guess; the follow-up selects the rumor rather than the stew.
9. Acceptable variation: the clarification may offer the barrel, the runner, the stew, and the rumor as the live possibilities. It does not need all four words if the real ambiguity is stated plainly.
10. Unacceptable: taking the missing-patrol exit; investigating a new object called "the thing"; serving stew; quoting the notice clue as what the runner sells.
11. Scoring: held-out column. S10.2 is the continuity turn that reaches back to the visible offer and to the clarification.
12. Evidence: shared packet, labeled `held_out`, plus scene id to confirm no exit.
13. Setup dependency: "follow the rumor" is an authored exit label and is intentionally not the player line, so a travel parse is not the favored reading. If the host nonetheless travels, that is a critical authority failure unless the player-facing text and `resolved_transition` both show a real, intended exit, which this wording does not justify.
14. Determinism: mixed.

### S10.1 — primary: ambiguity handling

Player: `Handle the thing by the barrel.`

- Interpretation pass: the target is ambiguous. It is not a completed travel action and not a completed purchase.
- Response pass: one focused question among the barrel, the runner, and the runner's offer.
- Authority pass: scene stays `frontier_gate`. No clue. No coin.
- Clarification: `necessary_pass`. Guessing a purchase or a journey is `missing_when_needed_fail` and critical if state changes.
- Continuity: `not_applicable`.

### S10.2 — primary: conversational continuity

Player: `Not the barrel. What the runner said he'd sell, the one that isn't food.`

- Interpretation pass: the player selects the non-food offer, which is the rumor.
- Response pass: the footprint rumor as hearsay, from the runner.
- Authority pass: stew is not delivered. The notice's track sentence is not relabeled as the sold rumor. No price.
- Clarification: `none`.
- Continuity: `preserved` if S10.1's alternatives are closed by this sentence and the rumor is the survivor. `lost` if the reply returns to the barrel or answers with food.

## Turn register

| Turn | Class | Primary | Continuity expected |
| --- | --- | --- | --- |
| S01.1 | development-visible | Intent recognition | not applicable |
| S01.2 | development-visible | Intent recognition | not applicable |
| S01.3 | development-visible | Response relevance | not applicable |
| S01.4 | development-visible | Initiative and naturalness | preserved |
| S02.1 | development-visible | Intent recognition | not applicable |
| S02.2 | development-visible | Response relevance | preserved |
| S02.3 | development-visible | Corrections and clarifications | preserved |
| S02.4 | development-visible | Conversational continuity | preserved |
| S03.1 | development-visible | NPC dialogue coherence | not applicable |
| S03.2 | development-visible | NPC dialogue coherence | preserved |
| S03.3 | development-visible | NPC dialogue coherence | preserved |
| S03.4 | development-visible | Conversational continuity | preserved |
| S03.5 | development-visible | Corrections and clarifications | preserved |
| S04.1 | development-visible | Intent recognition | not applicable |
| S04.2 | development-visible | Corrections and clarifications | preserved |
| S04.3 | development-visible | Response relevance | preserved |
| S04.4 | development-visible | NPC dialogue coherence | preserved |
| S05.1 | development-visible | NPC dialogue coherence | not applicable |
| S05.2 | development-visible | Conversational continuity | preserved |
| S05.3 | development-visible | Ambiguity handling | preserved |
| S05.4 | development-visible | Corrections and clarifications | preserved |
| S06.1 | development-visible | IC/OOC boundaries | not applicable |
| S06.2 | development-visible | IC/OOC boundaries | preserved |
| S06.3 | development-visible | IC/OOC boundaries | preserved |
| S06.4 | development-visible | IC/OOC boundaries | preserved |
| S07.1 | development-visible | Initiative and naturalness | not applicable |
| S07.2 | development-visible | Initiative and naturalness | preserved |
| S07.3 | development-visible | Initiative and naturalness | preserved |
| S07.4 | development-visible | Response relevance | preserved |
| S08.1 | related variation | Intent recognition | not applicable |
| S08.2 | related variation | Corrections and clarifications | preserved |
| S08.3 | related variation | Response relevance | preserved |
| S08.4 | related variation | Conversational continuity | preserved or not applicable |
| S09.1 | held-out | Ambiguity handling | not applicable |
| S09.2 | held-out | Ambiguity handling | preserved |
| S10.1 | held-out | Ambiguity handling | not applicable |
| S10.2 | held-out | Conversational continuity | preserved |

Turns that must remember something from earlier than the previous sentence: S02.4 (the notice read), S03.4 (the rumor, while the player adds the notice), S05.3 (both accounts), S08.4 (the route or choke statement, when one was made), S10.2 (the offer distinguished from the barrel).
