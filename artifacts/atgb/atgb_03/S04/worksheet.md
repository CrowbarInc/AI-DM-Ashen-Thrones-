# ATGB human scoring worksheet

These responses are from a live-provider execution. Enter interpretation, response, and authority separately. Uncertain is available when the evidence is insufficient. Do not collapse the three judgments into one score.

Benchmark `ATGB-02`, rubric `atgb-rubric-01`, mode `live_provider`.

Interpretation, response, and authority stay separate. Mark a judgment `uncertain` when the evidence is insufficient.

## S04 — The serjeant

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

### S04.1

- Player input: Serjeant, did the patrol's route change?
- AI-DM response: Gate Serjeant mutters, "Word is, the patrol route changed after the Ash Compact census choke worsened."
- Response origin: `live_provider`
- Relevant authoritative context: {'scenario': {'environment_id': 'frontier_gate', 'location_id': 'frontier_gate', 'shared_facts': [{'id': 'visible_notice_board', 'text': 'The notice board lists taxes, curfew rules, and a missing-patrol warning.'}, {'id': 'visible_serjeant', 'text': 'A gate serjeant manages the crowd and watches the roster board.'}, {'id': 'visible_runner_offer', 'text': 'A tavern runner trades hot stew and rumors beside the rain barrel.'}, {'id': 'visible_crowd', 'text': 'Threadbare watchers and refugees stand along the muddy line.'}, {'id': 'visible_census_choke', 'text': 'Ash Compact census delays have tightened the eastern caravan choke.'}, {'id': 'visible_banners', 'text': 'Frayed banners are in the opening description.'}, {'id': 'clue_notice_patrol_route', 'text': 'Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.'}, {'id': 'topic_watch_command', 'text': 'gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.'}, {'id': 'topic_route_change', 'text': 'gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.'}, {'id': 'topic_patrol_rumor', 'text': 'tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.'}, {'id': 'exits', 'text': 'If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.'}, {'id': 'hidden_facts', 'text': 'Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.'}, {'id': 'unauthored', 'text': "Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran."}], 'initial_context': 'Fresh gate. No interlocutor.', 'authoritative_facts': ['gate_serjeant owns the route-change sentence.', 'The eastern choke from census delays is a visible fact. The route change is a consequence of that choke worsening.', 'The catalog does not authorize the route change is why the wagons are stuck.', "Thoran's sentence is a different NPC's fact."], 'npc_knowledge': ['The serjeant may report the route change.', "The serjeant has no authored knowledge of Thoran's private awareness and does not know who gave the order."], 'unacceptable_behaviors': ['Binding gate_guard or guard_captain after the player says Gate Serjeant.', 'Inventing an order, a meeting, or a clock.', 'Answering the wagon question with only the route changed and never mentioning the choke or the wagons.']}, 'communicative_act': 'Question to gate_serjeant.', 'interpretation_pass': 'Question to gate_serjeant.', 'response_pass': 'The route changed after the Ash Compact census choke worsened.', 'authority_pass': 'No extra cause, order, or destination.', 'acceptable_variations': [], 'unacceptable_behaviors': []}
- Interpretation assessment: `unchecked`
- Response assessment: `unchecked`
- Authority assessment: `unchecked`
- Failure severity: `unscored`
- Clarification assessment: expected `none`; reviewer `unscored`
- Reviewer notes: (none yet)
- Evidence references: scenario:S04, turn:S04.1, catalog:S04.1 — primary: intent recognition

### S04.2

- Player input: I said the Gate Serjeant, not the captain and not the guard.
- AI-DM response: I can't interpret that from the current scene without using information you have not been shown.
- Response origin: `live_provider`
- Relevant authoritative context: {'scenario': {'environment_id': 'frontier_gate', 'location_id': 'frontier_gate', 'shared_facts': [{'id': 'visible_notice_board', 'text': 'The notice board lists taxes, curfew rules, and a missing-patrol warning.'}, {'id': 'visible_serjeant', 'text': 'A gate serjeant manages the crowd and watches the roster board.'}, {'id': 'visible_runner_offer', 'text': 'A tavern runner trades hot stew and rumors beside the rain barrel.'}, {'id': 'visible_crowd', 'text': 'Threadbare watchers and refugees stand along the muddy line.'}, {'id': 'visible_census_choke', 'text': 'Ash Compact census delays have tightened the eastern caravan choke.'}, {'id': 'visible_banners', 'text': 'Frayed banners are in the opening description.'}, {'id': 'clue_notice_patrol_route', 'text': 'Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.'}, {'id': 'topic_watch_command', 'text': 'gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.'}, {'id': 'topic_route_change', 'text': 'gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.'}, {'id': 'topic_patrol_rumor', 'text': 'tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.'}, {'id': 'exits', 'text': 'If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.'}, {'id': 'hidden_facts', 'text': 'Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.'}, {'id': 'unauthored', 'text': "Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran."}], 'initial_context': 'Fresh gate. No interlocutor.', 'authoritative_facts': ['gate_serjeant owns the route-change sentence.', 'The eastern choke from census delays is a visible fact. The route change is a consequence of that choke worsening.', 'The catalog does not authorize the route change is why the wagons are stuck.', "Thoran's sentence is a different NPC's fact."], 'npc_knowledge': ['The serjeant may report the route change.', "The serjeant has no authored knowledge of Thoran's private awareness and does not know who gave the order."], 'unacceptable_behaviors': ['Binding gate_guard or guard_captain after the player says Gate Serjeant.', 'Inventing an order, a meeting, or a clock.', 'Answering the wagon question with only the route changed and never mentioning the choke or the wagons.']}, 'communicative_act': 'Addressee correction.', 'interpretation_pass': 'Addressee correction.', 'response_pass': 'The serjeant is the speaker, and the route-change fact is the content if anything is repeated.', 'authority_pass': 'Thoran may be named only to set him aside. He does not become the answer.', 'acceptable_variations': ['A confirmation that restates the route-change fact passes when S04.1 already answered as the serjeant.'], 'unacceptable_behaviors': []}
- Interpretation assessment: `unchecked`
- Response assessment: `unchecked`
- Authority assessment: `unchecked`
- Failure severity: `unscored`
- Clarification assessment: expected `none`; reviewer `unscored`
- Reviewer notes: (none yet)
- Evidence references: scenario:S04, turn:S04.2, catalog:S04.2 — primary: corrections and clarifications
