# Continuation 9 code references

Discovery citations only. No production edit in this continuation.

## Contract construction

- `game/resolution_contract.py` `_AT_OBJECT_RE` — `on|at` plus a span ending at ` and ` or punctuation. This is the `duty` hit.
- `game/resolution_contract.py` `_EXPLICIT_TARGET_RE` — verb plus up to 60 non-punctuation characters. This is the sentence-sized examine target.
- `game/resolution_contract.py` `_explicit_target` — a pronoun is rejected only when the entire span is a bare pronoun.
- `game/resolution_contract.py` `_resolve_referent` — an explicit target returns immediately as `explicit_player`. A single filled slot binds any later anaphor as `unambiguous_discourse_referent`.
- `game/resolution_contract.py` `_operation` — one operation. `action_type` `observe` or `investigate` forces `inspect`.
- `game/resolution_contract.py` `construct_resolution_contract` — no confidence field. `ambiguous` only for the listed cues.
- `game/resolution_contract.py` `generation_projection` — “Resolve {operation} for {target}.”
- `game/prompt_context.py` — instruction to obey that constraint and not infer a different request.

## Intent and surface, parallel to the contract

- `game/intent_parser.py` `INVESTIGATE_PATTERNS` — `look for` extracts the rest of the sentence and runs before `ask`.
- `game/intent_parser.py` `segment_mixed_player_turn` / `_extract_contingency` — a leading `If …,` is removed before classification. Explore 4’s contract was built from the remainder.
- `game/referenced_surface.py` `extract_inspection_target` — a single slug such as `duty` is ignored and the sentence is reparsed.
- `game/referenced_surface.py` `classify_referenced_surface` — longest-to-shortest token prefixes. Token `someone` matched a hidden fact.
- `game/referenced_surface.py` `render_referenced_surface_inspection_line` — `authored_hidden` renders “You find no such thing…”; `unsupported` renders “Nothing here matches that.”
- `game/perception_grounding.py` `apply_perception_non_invention_to_gm` — investigate plus hidden or unsupported authority force-replaces the model line.

## Discourse

- `game/discourse_state.py` `commit_discourse_focus` — inspect/perceive writes `active_inspected` from `target_ref` with no entity check. An ambiguous contract returns without clearing slots.
- `game/live_resolution.py` `attach_interaction_obligation` — builds the contract from `resolution.prompt`, then derives the obligation.
- `tools/run_pr_br_level2_probes.py` `_isolate_storage` — does not reset `session.json`. Continuation 8 called it once per persona on the same temp directory.

## Tests the smoke did not resemble

- `tests/test_pr_br_resolution_contract.py` — known phrases: look it over, that lead, source, confidence, sheet content, wear, explicit targets that override focus.
- `tests/test_pr_br_outcome_precedence.py` — rumor, repeat, sheet, content, wear. The Continuation 7 script.
- Neither file contains “on duty,” “look for someone and ask,” or a clause-sized examine target.
