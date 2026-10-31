# ATGB human scoring worksheet

These responses are from a live-provider execution. Enter interpretation, response, and authority separately. Uncertain is available when the evidence is insufficient. Do not collapse the three judgments into one score.

Benchmark `ATGB-02`, rubric `atgb-rubric-01`, mode `live_provider`.

Interpretation, response, and authority stay separate. Mark a judgment `uncertain` when the evidence is insufficient.

## S02 — The notices

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

### S02.1

- Player input: I read the notices.
- AI-DM response: The notice board lists taxes, curfew rules, and a warning about a missing patrol.
- Response origin: `live_provider`
- Relevant authoritative context: {'scenario': {'environment_id': 'frontier_gate', 'location_id': 'frontier_gate', 'shared_facts': [{'id': 'visible_notice_board', 'text': 'The notice board lists taxes, curfew rules, and a missing-patrol warning.'}, {'id': 'visible_serjeant', 'text': 'A gate serjeant manages the crowd and watches the roster board.'}, {'id': 'visible_runner_offer', 'text': 'A tavern runner trades hot stew and rumors beside the rain barrel.'}, {'id': 'visible_crowd', 'text': 'Threadbare watchers and refugees stand along the muddy line.'}, {'id': 'visible_census_choke', 'text': 'Ash Compact census delays have tightened the eastern caravan choke.'}, {'id': 'visible_banners', 'text': 'Frayed banners are in the opening description.'}, {'id': 'clue_notice_patrol_route', 'text': 'Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.'}, {'id': 'topic_watch_command', 'text': 'gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.'}, {'id': 'topic_route_change', 'text': 'gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.'}, {'id': 'topic_patrol_rumor', 'text': 'tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.'}, {'id': 'exits', 'text': 'If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.'}, {'id': 'hidden_facts', 'text': 'Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.'}, {'id': 'unauthored', 'text': "Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran."}], 'initial_context': 'Fresh gate. The board has not been read.', 'authoritative_facts': ['The board lists taxes, curfew rules, and a missing-patrol warning. Hours are not authored.', 'Investigating the notice board may reveal notice_patrol_route.', 'S02.2 is the distinction between a true nearby fact and an answer.'], 'npc_knowledge': ['The board is an object. An NPC who has not been given the clue does not gain it by standing nearby.', "The runner's rumor is a different sentence and is not a substitute for the posted warning."], 'unacceptable_behaviors': ['Dusk-until-dawn, a fine, bandits, a statute number, or answering S02.2 or S02.3 with the crate track.']}, 'communicative_act': 'Investigate or read the notice board, not a social question to the runner.', 'interpretation_pass': 'Investigate or read the notice board, not a social question to the runner.', 'response_pass': 'Taxes, curfew rules, and a missing-patrol warning, or the revealed route clue plus those categories.', 'authority_pass': 'No hours, fines, or causes that are not in the clue text. Revealing notice_patrol_route on this investigation is authorized. Revealing a hidden fact is not.', 'acceptable_variations': [], 'unacceptable_behaviors': []}
- Interpretation assessment: `unchecked`
- Response assessment: `unchecked`
- Authority assessment: `unchecked`
- Failure severity: `unscored`
- Clarification assessment: expected `none`; reviewer `unscored`
- Reviewer notes: (none yet)
- Evidence references: scenario:S02, turn:S02.1, catalog:S02.1 — primary: intent recognition

### S02.2

- Player input: When does the curfew start?
- AI-DM response: The notice board lists taxes, curfew rules, and a warning about a missing patrol.
- Response origin: `live_provider`
- Relevant authoritative context: {'scenario': {'environment_id': 'frontier_gate', 'location_id': 'frontier_gate', 'shared_facts': [{'id': 'visible_notice_board', 'text': 'The notice board lists taxes, curfew rules, and a missing-patrol warning.'}, {'id': 'visible_serjeant', 'text': 'A gate serjeant manages the crowd and watches the roster board.'}, {'id': 'visible_runner_offer', 'text': 'A tavern runner trades hot stew and rumors beside the rain barrel.'}, {'id': 'visible_crowd', 'text': 'Threadbare watchers and refugees stand along the muddy line.'}, {'id': 'visible_census_choke', 'text': 'Ash Compact census delays have tightened the eastern caravan choke.'}, {'id': 'visible_banners', 'text': 'Frayed banners are in the opening description.'}, {'id': 'clue_notice_patrol_route', 'text': 'Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.'}, {'id': 'topic_watch_command', 'text': 'gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.'}, {'id': 'topic_route_change', 'text': 'gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.'}, {'id': 'topic_patrol_rumor', 'text': 'tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.'}, {'id': 'exits', 'text': 'If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.'}, {'id': 'hidden_facts', 'text': 'Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.'}, {'id': 'unauthored', 'text': "Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran."}], 'initial_context': 'Fresh gate. The board has not been read.', 'authoritative_facts': ['The board lists taxes, curfew rules, and a missing-patrol warning. Hours are not authored.', 'Investigating the notice board may reveal notice_patrol_route.', 'S02.2 is the distinction between a true nearby fact and an answer.'], 'npc_knowledge': ['The board is an object. An NPC who has not been given the clue does not gain it by standing nearby.', "The runner's rumor is a different sentence and is not a substitute for the posted warning."], 'unacceptable_behaviors': ['Dusk-until-dawn, a fine, bandits, a statute number, or answering S02.2 or S02.3 with the crate track.']}, 'communicative_act': 'A time question about the curfew.', 'interpretation_pass': 'A time question about the curfew.', 'response_pass': 'The start time is not known or not posted. The player is not handed a different fact in its place. An accurate patrol sentence on this turn fails response, and if it is presented as the curfew answer it stays a response failure even when the sentence itself is owned.', 'authority_pass': 'No clock hour and no penalty.', 'acceptable_variations': [], 'unacceptable_behaviors': ['Dusk-until-dawn, a fine, or the crate track as the curfew answer.']}
- Interpretation assessment: `unchecked`
- Response assessment: `unchecked`
- Authority assessment: `unchecked`
- Failure severity: `unscored`
- Clarification assessment: expected `none`; reviewer `unscored`
- Reviewer notes: (none yet)
- Evidence references: scenario:S02, turn:S02.2, catalog:S02.2 — primary: response relevance

### S02.3

- Player input: I wasn't asking where the patrol went. I asked when it starts.
- AI-DM response: The notice board lists taxes, curfew rules, and a warning about a missing patrol.
- Response origin: `live_provider`
- Relevant authoritative context: {'scenario': {'environment_id': 'frontier_gate', 'location_id': 'frontier_gate', 'shared_facts': [{'id': 'visible_notice_board', 'text': 'The notice board lists taxes, curfew rules, and a missing-patrol warning.'}, {'id': 'visible_serjeant', 'text': 'A gate serjeant manages the crowd and watches the roster board.'}, {'id': 'visible_runner_offer', 'text': 'A tavern runner trades hot stew and rumors beside the rain barrel.'}, {'id': 'visible_crowd', 'text': 'Threadbare watchers and refugees stand along the muddy line.'}, {'id': 'visible_census_choke', 'text': 'Ash Compact census delays have tightened the eastern caravan choke.'}, {'id': 'visible_banners', 'text': 'Frayed banners are in the opening description.'}, {'id': 'clue_notice_patrol_route', 'text': 'Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.'}, {'id': 'topic_watch_command', 'text': 'gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.'}, {'id': 'topic_route_change', 'text': 'gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.'}, {'id': 'topic_patrol_rumor', 'text': 'tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.'}, {'id': 'exits', 'text': 'If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.'}, {'id': 'hidden_facts', 'text': 'Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.'}, {'id': 'unauthored', 'text': "Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran."}], 'initial_context': 'Fresh gate. The board has not been read.', 'authoritative_facts': ['The board lists taxes, curfew rules, and a missing-patrol warning. Hours are not authored.', 'Investigating the notice board may reveal notice_patrol_route.', 'S02.2 is the distinction between a true nearby fact and an answer.'], 'npc_knowledge': ['The board is an object. An NPC who has not been given the clue does not gain it by standing nearby.', "The runner's rumor is a different sentence and is not a substitute for the posted warning."], 'unacceptable_behaviors': ['Dusk-until-dawn, a fine, bandits, a statute number, or answering S02.2 or S02.3 with the crate track.']}, 'communicative_act': 'Correction of S02.2.', 'interpretation_pass': 'Correction of S02.2.', 'response_pass': 'Returns to the start time and keeps the uncertainty. It does not repeat the route as the answer.', 'authority_pass': 'Still no invented hour.', 'acceptable_variations': [], 'unacceptable_behaviors': ['Repeating the route as the answer.']}
- Interpretation assessment: `unchecked`
- Response assessment: `unchecked`
- Authority assessment: `unchecked`
- Failure severity: `unscored`
- Clarification assessment: expected `none`; reviewer `unscored`
- Reviewer notes: (none yet)
- Evidence references: scenario:S02, turn:S02.3, catalog:S02.3 — primary: corrections and clarifications

### S02.4

- Player input: All right. What did the warning say about where they were last seen?
- AI-DM response: The notice board lists taxes, curfew rules, and a warning about a missing patrol.
- Response origin: `live_provider`
- Relevant authoritative context: {'scenario': {'environment_id': 'frontier_gate', 'location_id': 'frontier_gate', 'shared_facts': [{'id': 'visible_notice_board', 'text': 'The notice board lists taxes, curfew rules, and a missing-patrol warning.'}, {'id': 'visible_serjeant', 'text': 'A gate serjeant manages the crowd and watches the roster board.'}, {'id': 'visible_runner_offer', 'text': 'A tavern runner trades hot stew and rumors beside the rain barrel.'}, {'id': 'visible_crowd', 'text': 'Threadbare watchers and refugees stand along the muddy line.'}, {'id': 'visible_census_choke', 'text': 'Ash Compact census delays have tightened the eastern caravan choke.'}, {'id': 'visible_banners', 'text': 'Frayed banners are in the opening description.'}, {'id': 'clue_notice_patrol_route', 'text': 'Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.'}, {'id': 'topic_watch_command', 'text': 'gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.'}, {'id': 'topic_route_change', 'text': 'gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.'}, {'id': 'topic_patrol_rumor', 'text': 'tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.'}, {'id': 'exits', 'text': 'If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.'}, {'id': 'hidden_facts', 'text': 'Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.'}, {'id': 'unauthored', 'text': "Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran."}], 'initial_context': 'Fresh gate. The board has not been read.', 'authoritative_facts': ['The board lists taxes, curfew rules, and a missing-patrol warning. Hours are not authored.', 'Investigating the notice board may reveal notice_patrol_route.', 'S02.2 is the distinction between a true nearby fact and an answer.'], 'npc_knowledge': ['The board is an object. An NPC who has not been given the clue does not gain it by standing nearby.', "The runner's rumor is a different sentence and is not a substitute for the posted warning."], 'unacceptable_behaviors': ['Dusk-until-dawn, a fine, bandits, a statute number, or answering S02.2 or S02.3 with the crate track.']}, 'communicative_act': 'Recall of the posted warning from S02.1, after the curfew detour, not a new rumor request.', 'interpretation_pass': 'Recall of the posted warning, not a new rumor request.', 'response_pass': 'The northwest mud track past the crates, if that clue was revealed in S02.1. If S02.1 never revealed it, the reply says the warning names a missing patrol and does not add a place, or it investigates now and then reports the clue.', 'authority_pass': "The place comes from notice_patrol_route or is withheld. The runner's footprint sentence is not quoted as the notice.", 'acceptable_variations': [], 'unacceptable_behaviors': ["Quoting the runner's footprint sentence as the notice."]}
- Interpretation assessment: `unchecked`
- Response assessment: `unchecked`
- Authority assessment: `unchecked`
- Failure severity: `unscored`
- Clarification assessment: expected `none`; reviewer `unscored`
- Reviewer notes: (none yet)
- Evidence references: scenario:S02, turn:S02.4, catalog:S02.4 — primary: conversational continuity
