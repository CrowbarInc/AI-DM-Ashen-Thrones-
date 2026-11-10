# PLAYER SAFE RESPONSE CONTRACT

response_contract.json documents each allowlisted leaf's source, purpose, visibility rule, frontend consumer, optionality, safe default and JSON behavior. The executable schemas live in game/player_http_projection.py. State envelopes keep public_state; runtime action responses retain the existing flat shape. No internal object is copied wholesale to the player.

Allowed: session/run IDs; current/visited scene identity; public scene description and visible facts; player-sheet stats, finite numeric skill ranks, explicit inventory and spell records; existing published journal facts/clues/leads; server-filtered affordances with public labels/prompts/targets; current public NPC roster; status/save-slot summaries; final published narration; player log input and narration. Resolution is an empty compatibility placeholder. Unknown nested fields are omitted. Wrong-typed object leaves become empty safe primitives, never stringified objects.

Absent optional fields are omitted. Invalid strings/lists/numbers/booleans become empty string/list/zero/false. Empty world {} intentionally represents missing per-item visibility contracts. Numeric skills are a documented player-sheet identifier namespace, not an arbitrary nested JSON exception. Safe statuses/errors are finite allowlists; unexpected diagnostic errors become actionable generic copy.
