# Understanding vs Execution

The codebase is moving toward separation, but production does not complete it.

Evidence of separation:

- `game/semantic_interpreter.py` describes model interpretation as a proposal, never a contract.
- `game/resolution_contract.py` records what the player wants resolved.
- `game/ordinary_semantic_ownership.py` separates contract construction from resolver selection.
- `game/live_resolution.py` distinguishes authoritative mechanical action, grounded information request, bounded improvisable request, NPC claim response, unsupported consequential request, and target failure.

Evidence of remaining coupling:

- `game/live_chat_interpretation.py` blocks the turn before normal pipeline when interpretation is multi-component or unbridgeable.
- `game/player_interpretation_bridge.py` converts understanding directly into normalized resolver action.
- Final generation can answer only after the turn survives routing/contract construction.

Missing or incomplete outcomes: answer IC knowledge question without target, continue NPC dialogue from implicit focus in live bridge, acknowledge correction beyond OOC, establish intended destination, propose multi-step plan, and distinguish incidental narrative behavior from action components.

Recommendation: introduce a pre-execution conversational decision record. It should decide whether execution is needed before resolver selection. Existing resolvers should only see validated executable operations.
