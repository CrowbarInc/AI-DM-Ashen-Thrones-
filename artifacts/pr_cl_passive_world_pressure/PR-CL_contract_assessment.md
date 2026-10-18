# PR-CL contract assessment

Live provider calls: 0.

HEAD at assessment: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`.

The worktree was already dirty with the PR-CK resolver-selection repair and earlier uncommitted product work. Nothing was reset. No product file was edited in PR-CL.

PR-CK inherited decision: B — PARTIAL REPAIR. Passive waiting already reaches the generation resolver. The two remaining shared-pipeline failures are phrase assertions on the emitted beat.

## Separate responsibilities

| Responsibility | Owner | What a wait actually does |
| --- | --- | --- |
| A. Time advancement | `game.api.chat` calls `advance_clock(session, "time_pressure", 1)` on every chat, including a wait. `session.current_date` stays `"Day 1"`. `world.world_state.clocks` stays empty. | A session pressure counter moves. There is no diegetic clock and no wait-specific duration. |
| B. Evaluation of world developments | `advance_world_tick` in `game.world` runs on every chat before narration. Active projects, faction pressure, faction agenda, and mobile NPCs with `agenda_move_to_scene_id` are the existing evaluators. | Due threshold crossings and mobile moves are written to `world.event_log` and `resolution.world_tick_events`. |
| C. Selection of a development | Tick selection stays inside `advance_world_tick`. Passive-scene selection stays inside `escalate_passive_scene` / `_pick_passive_pressure_source`, and only when that rewriter is allowed to run. | A tense visible fact is not a scheduled NPC action. |
| D. Authorization of consequential changes | World tick may mutate faction pressure, agenda, flags, and a mobile NPC location. Perception grounding and the hard-valid seal forbid inventing a person, confrontation, clue, or route. | Visible-fact prose is not authority to spawn speech or an approach. |
| E. Narration of the resulting state | The provider may describe authorized developments. With a stubbed provider, a hard-valid line is sealed. Scene-stall fallback and the passive-pressure beat may later substitute a grounded visible fact. | Narration is not itself proof that the world clock or a scheduled event moved. |

## Settled constraints this cycle does not reopen

- PR-BE: there is no wait / pass-time action, duration table, or diegetic world clock. Ordinary `"I wait."` is not a missing parser cycle. `time_pressure` incrementing on every chat is not a wait-owned time system. `current_date` remaining `"Day 1"` is expected.
- Scene Momentum Rule (`docs/ai_gm_contract.md`): every 2–3 exchanges the scene should gain new information, a new actor, an environmental change, time pressure, or a consequence. That rule does not name an interruption phrase and does not authorize an unestablished actor.
- Passive-pressure prompt in `game.gm`: when a pause is detected, realize the visible scene and do not invent a person, confrontation, whispered hook, inscription, clue, or route.
- Grounded observation (`tests/test_grounded_observation_non_invention.py`): `"cuts through the crowd"` / `"stops at your shoulder"` is an unauthorized confrontation when no such actor is present.
- PR-CK: unresolved narration with no owed question or stall retry is sealed before a pressure rewrite. Sibling tests now keep a hard-valid atmosphere line, including when a suspicious-figure lead already exists.
- Historical renderer, removed at the PR-AR checkpoint (`dcbcefe` still contained it): `_render_passive_pressure_beat` invented quoted approaches (`cuts through the crowd`, `stops at your shoulder`, `Ask me now`, `east-road report`) from a visible-fact subject. The current renderer ignores that source and returns `render_grounded_perception_line`.

## What tension does and does not authorize

Visible facts containing "guard", "watch", "missing patrol", or "rumor" make `_scene_snapshot_has_tension` and `_passive_scene_pressure_due_for_fallback` true. That is a narration-pressure signal. It is not a scheduled event, not an NPC agenda, and not permission to mint dialogue.

On these fixtures the world NPCs `guard_captain` and `tavern_runner` are located at `frontier_gate`, with `availability: available` and no `agenda_move_to_scene_id`. The sentences "a tavern runner lingers" and "a guard leans" are scene prose, not those NPC records.
