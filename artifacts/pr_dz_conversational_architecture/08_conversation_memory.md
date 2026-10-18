# Conversation Memory

Available information:

- Recent visible turns: `game/semantic_interpreter.py:127` and `game/live_chat_interpretation.py:222`.
- Active NPC/interlocutor: current `data/session.json` has `active_interaction_target_id: gate_serjeant`.
- Current scene facts and NPC topics: `data/scenes/frontier_gate.json`, `data/world.json`.
- Selected conversational memory: `game/prompt_context.py:2549-2577`.
- Previous actions and discovered clues: session log and scene runtime metadata.

Failure categories:

A. Information unavailable: no authoritative lore entity explaining "Ash Compact" beyond scene/topic text.
B. Available but discarded/prevented: active social target and recent Gate Serjeant line exist, but live bridge can still reject unbound/multi-component turns before narration.
C. Supplied but ignored by model: possible for repeated inspections; not proven here without exact live payload comparison.
D. Interpreted correctly but rejected downstream: proven for "Angry, I leave...".

Reference handling remains fragile for "Who are they?", "What does that mean?", "I already checked that", and corrections because they require claim/topic/correction intent, not just entity binding.
