# PR-CK action and chat parity

Live provider calls: 0. Narration is not required to be byte-identical.

## Investigation

`/api/action` with an explicit investigate payload and `/api/chat` with "I investigate the desk." both reach `kind=discover_clue` and both record the authored clue "A map indicates patrol locations." `test_action_and_chat_investigate_both_mark_runtime_discovery_memory` passed.

`/api/chat` "I search the desk." also reaches that authored discovery without a mocked exploration action. The chat path now calls the exploration parser when the selected resolver is exploration, before world-action recovery. Travel still reaches exploration in its previous relative position.

## Observation

`/api/chat` "Describe the gate." selects generation, operation unresolved, and no interlocutor. It does not become an addressed NPC question. `/api/action` observation was already outside `select_ordinary_resolver` when the client sends an explicit action payload. The chat contract now matches that non-social intent.

## Passive waiting

`/api/chat` "I wait." selects generation and permits passive wait. Scene-stall retry again makes two provider calls when momentum is due (`test_chat_targeted_retry_scene_stall_only` passed). The two pressure tests still fail because the emitted beat does not contain the concrete interruption phrases those tests require.

## Addressed social question

"I talk to Tavern Runner." through `/api/action` and `/api/chat` again share `kind=question` and npc `runner`. `test_action_and_chat_social_use_equivalent_shared_turn_logic` passed. "Tell me plainly." with an engaged target routes to `social_probe`. "I persuade the gate guard to let me pass." reaches the engine diplomacy check and does not call the provider.
