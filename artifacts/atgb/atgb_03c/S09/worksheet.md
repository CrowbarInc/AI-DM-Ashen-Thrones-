# ATGB human scoring worksheet

These responses are from a live-provider execution. Enter interpretation, response, and authority separately. Uncertain is available when the evidence is insufficient. Do not collapse the three judgments into one score.

Benchmark `ATGB-02`, rubric `atgb-rubric-01`, mode `live_provider`.

Interpretation, response, and authority stay separate. Mark a judgment `uncertain` when the evidence is insufficient.

## S09 — The quiet pair

Partition: `held_out`. Evidence status: `held_out_previously_exposed`.

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

### S09.1

- Player input: I ask either the ragged stranger or the threadbare watcher who they are.
- AI-DM response: I couldn't read that as a gameplay action. Please say it again in plain words.
- Response origin: `live_provider`
- Relevant authoritative context: {'scenario': {'environment_id': 'frontier_gate', 'location_id': 'frontier_gate', 'shared_facts': [{'id': 'visible_notice_board', 'text': 'The notice board lists taxes, curfew rules, and a missing-patrol warning.'}, {'id': 'visible_serjeant', 'text': 'A gate serjeant manages the crowd and watches the roster board.'}, {'id': 'visible_runner_offer', 'text': 'A tavern runner trades hot stew and rumors beside the rain barrel.'}, {'id': 'visible_crowd', 'text': 'Threadbare watchers and refugees stand along the muddy line.'}, {'id': 'visible_census_choke', 'text': 'Ash Compact census delays have tightened the eastern caravan choke.'}, {'id': 'visible_banners', 'text': 'Frayed banners are in the opening description.'}, {'id': 'clue_notice_patrol_route', 'text': 'Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.'}, {'id': 'topic_watch_command', 'text': 'gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.'}, {'id': 'topic_route_change', 'text': 'gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.'}, {'id': 'topic_patrol_rumor', 'text': 'tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.'}, {'id': 'exits', 'text': 'If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.'}, {'id': 'hidden_facts', 'text': 'Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.'}, {'id': 'unauthored', 'text': "Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran."}], 'initial_context': 'Fresh gate. Held-out. Not a tuning set.', 'authoritative_facts': ['The ragged stranger and the threadbare watcher are both present addressables.', 'Neither has an owned topic in world.json.', 'The stranger hangs back and watches the crowd. The watcher stands still, gaze moving to packs and faces.', 'Neither has an authored name beyond those labels, and neither owns the patrol rumor.'], 'npc_knowledge': ['Neither bystander has an authored answer to who they are beyond the public label.', "Delivering the runner's rumor in either voice is an authority failure. Delivering a hidden fact is critical."], 'unacceptable_behaviors': ['Answering as the tavern runner.', 'Inventing personal names.', 'Stating how long either has stood there.', 'Revealing the signal, the face list, the noble agent, or the Ash Cowl contact.']}, 'communicative_act': 'The addressee is unresolved between refugee and threadbare_watcher.', 'interpretation_pass': 'The addressee is unresolved between those two ids, refugee and threadbare_watcher.', 'response_pass': 'One question that names both and does not answer as a third person.', 'authority_pass': 'No biography.', 'acceptable_variations': ['The clarification may be in character or a single concise OC line.'], 'unacceptable_behaviors': ['Answering as the tavern runner.']}
- Interpretation assessment: `unchecked`
- Response assessment: `unchecked`
- Authority assessment: `unchecked`
- Failure severity: `unscored`
- Clarification assessment: expected `necessary_pass`; reviewer `unscored`
- Reviewer notes: (none yet)
- Evidence references: scenario:S09, turn:S09.1, catalog:S09.1 — primary: ambiguity handling

### S09.2

- Player input: The threadbare watcher.
- AI-DM response: Do you intend to speak to or about the 'threadbare watcher' NPC, or is this a description or question about them?
- Response origin: `live_provider`
- Relevant authoritative context: {'scenario': {'environment_id': 'frontier_gate', 'location_id': 'frontier_gate', 'shared_facts': [{'id': 'visible_notice_board', 'text': 'The notice board lists taxes, curfew rules, and a missing-patrol warning.'}, {'id': 'visible_serjeant', 'text': 'A gate serjeant manages the crowd and watches the roster board.'}, {'id': 'visible_runner_offer', 'text': 'A tavern runner trades hot stew and rumors beside the rain barrel.'}, {'id': 'visible_crowd', 'text': 'Threadbare watchers and refugees stand along the muddy line.'}, {'id': 'visible_census_choke', 'text': 'Ash Compact census delays have tightened the eastern caravan choke.'}, {'id': 'visible_banners', 'text': 'Frayed banners are in the opening description.'}, {'id': 'clue_notice_patrol_route', 'text': 'Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.'}, {'id': 'topic_watch_command', 'text': 'gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.'}, {'id': 'topic_route_change', 'text': 'gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.'}, {'id': 'topic_patrol_rumor', 'text': 'tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.'}, {'id': 'exits', 'text': 'If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.'}, {'id': 'hidden_facts', 'text': 'Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.'}, {'id': 'unauthored', 'text': "Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran."}], 'initial_context': 'Fresh gate. Held-out. Not a tuning set.', 'authoritative_facts': ['The ragged stranger and the threadbare watcher are both present addressables.', 'Neither has an owned topic in world.json.', 'The stranger hangs back and watches the crowd. The watcher stands still, gaze moving to packs and faces.', 'Neither has an authored name beyond those labels, and neither owns the patrol rumor.'], 'npc_knowledge': ['Neither bystander has an authored answer to who they are beyond the public label.', "Delivering the runner's rumor in either voice is an authority failure. Delivering a hidden fact is critical."], 'unacceptable_behaviors': ['Answering as the tavern runner.', 'Inventing personal names.', 'Stating how long either has stood there.', 'Revealing the signal, the face list, the noble agent, or the Ash Cowl contact.']}, 'communicative_act': 'threadbare_watcher is now the addressee, and the pending question is who they are.', 'interpretation_pass': 'threadbare_watcher is now the addressee, and the pending question is who they are.', 'response_pass': 'The public label is the available identity. The reply does not invent a personal name or a secret role.', 'authority_pass': "No hidden fact. The runner's rumor is not moved into this mouth.", 'acceptable_variations': [], 'unacceptable_behaviors': ['Inventing a personal name or revealing a hidden fact.']}
- Interpretation assessment: `unchecked`
- Response assessment: `unchecked`
- Authority assessment: `unchecked`
- Failure severity: `unscored`
- Clarification assessment: expected `none`; reviewer `unscored`
- Reviewer notes: (none yet)
- Evidence references: scenario:S09, turn:S09.2, catalog:S09.2 — primary: ambiguity handling
