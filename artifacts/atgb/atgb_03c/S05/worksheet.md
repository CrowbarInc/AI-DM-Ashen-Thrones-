# ATGB human scoring worksheet

These responses are from a live-provider execution. Enter interpretation, response, and authority separately. Uncertain is available when the evidence is insufficient. Do not collapse the three judgments into one score.

Benchmark `ATGB-02`, rubric `atgb-rubric-01`, mode `live_provider`.

Interpretation, response, and authority stay separate. Mark a judgment `uncertain` when the evidence is insufficient.

## S05 — Two accounts

Partition: `development_visible`. Evidence status: `development_visible`.

### Conversation quality

Not a score. A conversation may be technically successful and still feel unnatural.

- [ ] repetitive responses
- [ ] unnatural phrasing
- [ ] excessive clarification
- [ ] poor conversational pacing
- [ ] failure to sustain initiative
- [ ] mechanical or validation-like dialogue

Reviewer observations:

(none yet)

### S05.1

- Player input: Runner, what did you hear about the patrol?
- AI-DM response: Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."
- Response origin: `live_provider`
- Relevant authoritative context: {'scenario': {'environment_id': 'frontier_gate', 'location_id': 'frontier_gate', 'shared_facts': [{'id': 'visible_notice_board', 'text': 'The notice board lists taxes, curfew rules, and a missing-patrol warning.'}, {'id': 'visible_serjeant', 'text': 'A gate serjeant manages the crowd and watches the roster board.'}, {'id': 'visible_runner_offer', 'text': 'A tavern runner trades hot stew and rumors beside the rain barrel.'}, {'id': 'visible_crowd', 'text': 'Threadbare watchers and refugees stand along the muddy line.'}, {'id': 'visible_census_choke', 'text': 'Ash Compact census delays have tightened the eastern caravan choke.'}, {'id': 'visible_banners', 'text': 'Frayed banners are in the opening description.'}, {'id': 'clue_notice_patrol_route', 'text': 'Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.'}, {'id': 'topic_watch_command', 'text': 'gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.'}, {'id': 'topic_route_change', 'text': 'gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.'}, {'id': 'topic_patrol_rumor', 'text': 'tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.'}, {'id': 'exits', 'text': 'If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.'}, {'id': 'hidden_facts', 'text': 'Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.'}, {'id': 'unauthored', 'text': "Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran."}], 'initial_context': 'Fresh gate.', 'authoritative_facts': ["The runner's rumor and, once the board is read, notice_patrol_route both point near the crates and the northwest approach.", 'They are different sentences and different sources.'], 'npc_knowledge': ["The runner knows the rumor as hearsay. The board holds the posted warning. Neither may absorb the other's wording."], 'unacceptable_behaviors': ['The same paragraph presented as both the notice and the rumor.', 'A third story.', 'The guard answering S05.4.']}, 'communicative_act': 'Question to tavern_runner.', 'interpretation_pass': 'tavern_runner is the addressee.', 'response_pass': 'The footprint rumor as hearsay.', 'authority_pass': 'No notice wording presented as what the runner heard.', 'acceptable_variations': [], 'unacceptable_behaviors': []}
- Interpretation assessment: `unchecked`
- Response assessment: `unchecked`
- Authority assessment: `unchecked`
- Failure severity: `unscored`
- Clarification assessment: expected `none`; reviewer `unscored`
- Reviewer notes: (none yet)
- Evidence references: scenario:S05, turn:S05.1, catalog:S05.1 — primary: NPC dialogue coherence

### S05.2

- Player input: And the board, what does it say about the same patrol?
- AI-DM response: I cannot provide a validated response to that request.
- Response origin: `live_provider`
- Relevant authoritative context: {'scenario': {'environment_id': 'frontier_gate', 'location_id': 'frontier_gate', 'shared_facts': [{'id': 'visible_notice_board', 'text': 'The notice board lists taxes, curfew rules, and a missing-patrol warning.'}, {'id': 'visible_serjeant', 'text': 'A gate serjeant manages the crowd and watches the roster board.'}, {'id': 'visible_runner_offer', 'text': 'A tavern runner trades hot stew and rumors beside the rain barrel.'}, {'id': 'visible_crowd', 'text': 'Threadbare watchers and refugees stand along the muddy line.'}, {'id': 'visible_census_choke', 'text': 'Ash Compact census delays have tightened the eastern caravan choke.'}, {'id': 'visible_banners', 'text': 'Frayed banners are in the opening description.'}, {'id': 'clue_notice_patrol_route', 'text': 'Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.'}, {'id': 'topic_watch_command', 'text': 'gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.'}, {'id': 'topic_route_change', 'text': 'gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.'}, {'id': 'topic_patrol_rumor', 'text': 'tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.'}, {'id': 'exits', 'text': 'If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.'}, {'id': 'hidden_facts', 'text': 'Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.'}, {'id': 'unauthored', 'text': "Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran."}], 'initial_context': 'Fresh gate.', 'authoritative_facts': ["The runner's rumor and, once the board is read, notice_patrol_route both point near the crates and the northwest approach.", 'They are different sentences and different sources.'], 'npc_knowledge': ["The runner knows the rumor as hearsay. The board holds the posted warning. Neither may absorb the other's wording."], 'unacceptable_behaviors': ['The same paragraph presented as both the notice and the rumor.', 'A third story.', 'The guard answering S05.4.']}, 'communicative_act': 'A shift from the runner to the notice board, same patrol topic.', 'interpretation_pass': 'A shift from the runner to the notice board, same patrol topic.', 'response_pass': 'The posted warning, including the northwest track once the board is investigated.', 'authority_pass': 'The runner is not quoted as the board.', 'acceptable_variations': [], 'unacceptable_behaviors': []}
- Interpretation assessment: `unchecked`
- Response assessment: `unchecked`
- Authority assessment: `unchecked`
- Failure severity: `unscored`
- Clarification assessment: expected `none`; reviewer `unscored`
- Reviewer notes: (none yet)
- Evidence references: scenario:S05, turn:S05.2, catalog:S05.2 — primary: conversational continuity

### S05.3

- Player input: Tell me more about that.
- AI-DM response: Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted.
- Response origin: `live_provider`
- Relevant authoritative context: {'scenario': {'environment_id': 'frontier_gate', 'location_id': 'frontier_gate', 'shared_facts': [{'id': 'visible_notice_board', 'text': 'The notice board lists taxes, curfew rules, and a missing-patrol warning.'}, {'id': 'visible_serjeant', 'text': 'A gate serjeant manages the crowd and watches the roster board.'}, {'id': 'visible_runner_offer', 'text': 'A tavern runner trades hot stew and rumors beside the rain barrel.'}, {'id': 'visible_crowd', 'text': 'Threadbare watchers and refugees stand along the muddy line.'}, {'id': 'visible_census_choke', 'text': 'Ash Compact census delays have tightened the eastern caravan choke.'}, {'id': 'visible_banners', 'text': 'Frayed banners are in the opening description.'}, {'id': 'clue_notice_patrol_route', 'text': 'Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.'}, {'id': 'topic_watch_command', 'text': 'gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.'}, {'id': 'topic_route_change', 'text': 'gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.'}, {'id': 'topic_patrol_rumor', 'text': 'tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.'}, {'id': 'exits', 'text': 'If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.'}, {'id': 'hidden_facts', 'text': 'Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.'}, {'id': 'unauthored', 'text': "Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran."}], 'initial_context': 'Fresh gate.', 'authoritative_facts': ["The runner's rumor and, once the board is read, notice_patrol_route both point near the crates and the northwest approach.", 'They are different sentences and different sources.'], 'npc_knowledge': ["The runner knows the rumor as hearsay. The board holds the posted warning. Neither may absorb the other's wording."], 'unacceptable_behaviors': ['The same paragraph presented as both the notice and the rumor.', 'A third story.', 'The guard answering S05.4.']}, 'communicative_act': 'The referent is unresolved between the rumor and the notice.', 'interpretation_pass': 'The referent is unresolved between the rumor and the notice.', 'response_pass': 'One question that names both, or otherwise distinguishes them. No new facts. This is a successful turn when the clarification is necessary and focused. Guessing is a major failure.', 'authority_pass': 'No additional detail about either account.', 'acceptable_variations': ['The clarification may pick neither account and ask.'], 'unacceptable_behaviors': ['Picking one account and calling the choice obvious.']}
- Interpretation assessment: `unchecked`
- Response assessment: `unchecked`
- Authority assessment: `unchecked`
- Failure severity: `unscored`
- Clarification assessment: expected `necessary_pass`; reviewer `unscored`
- Reviewer notes: (none yet)
- Evidence references: scenario:S05, turn:S05.3, catalog:S05.3 — primary: ambiguity handling

### S05.4

- Player input: The runner's version, not the notice.
- AI-DM response: Tavern Runner says, "I couldn't tell you."
- Response origin: `live_provider`
- Relevant authoritative context: {'scenario': {'environment_id': 'frontier_gate', 'location_id': 'frontier_gate', 'shared_facts': [{'id': 'visible_notice_board', 'text': 'The notice board lists taxes, curfew rules, and a missing-patrol warning.'}, {'id': 'visible_serjeant', 'text': 'A gate serjeant manages the crowd and watches the roster board.'}, {'id': 'visible_runner_offer', 'text': 'A tavern runner trades hot stew and rumors beside the rain barrel.'}, {'id': 'visible_crowd', 'text': 'Threadbare watchers and refugees stand along the muddy line.'}, {'id': 'visible_census_choke', 'text': 'Ash Compact census delays have tightened the eastern caravan choke.'}, {'id': 'visible_banners', 'text': 'Frayed banners are in the opening description.'}, {'id': 'clue_notice_patrol_route', 'text': 'Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.'}, {'id': 'topic_watch_command', 'text': 'gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.'}, {'id': 'topic_route_change', 'text': 'gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.'}, {'id': 'topic_patrol_rumor', 'text': 'tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.'}, {'id': 'exits', 'text': 'If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.'}, {'id': 'hidden_facts', 'text': 'Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.'}, {'id': 'unauthored', 'text': "Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran."}], 'initial_context': 'Fresh gate.', 'authoritative_facts': ["The runner's rumor and, once the board is read, notice_patrol_route both point near the crates and the northwest approach.", 'They are different sentences and different sources.'], 'npc_knowledge': ["The runner knows the rumor as hearsay. The board holds the posted warning. Neither may absorb the other's wording."], 'unacceptable_behaviors': ['The same paragraph presented as both the notice and the rumor.', 'A third story.', 'The guard answering S05.4.']}, 'communicative_act': 'The player resolved S05.3 in favor of the runner.', 'interpretation_pass': 'The player resolved S05.3 in favor of the runner.', 'response_pass': 'The footprint rumor only, still hearsay.', 'authority_pass': 'The track-past-the-crates sentence is not substituted.', 'acceptable_variations': [], 'unacceptable_behaviors': ['The guard answering this turn.']}
- Interpretation assessment: `unchecked`
- Response assessment: `unchecked`
- Authority assessment: `unchecked`
- Failure severity: `unscored`
- Clarification assessment: expected `none`; reviewer `unscored`
- Reviewer notes: (none yet)
- Evidence references: scenario:S05, turn:S05.4, catalog:S05.4 — primary: corrections and clarifications
