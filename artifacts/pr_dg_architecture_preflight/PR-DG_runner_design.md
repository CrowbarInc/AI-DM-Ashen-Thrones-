# PR-DG Runner Design

The runner lives in `experiments/pr_dg/`. Production `chat` does not import it.

## Isolation

`ProductionSaveGuard` replaces `game.storage._atomic_write_bytes`, `_save_json`, and `append_log`. A path under `data/` is stored in memory and not written. Before any scenario, the guard writes a probe session, a probe world, and a probe log line, then asserts the on-disk fingerprint is unchanged. If that probe touches disk, the run stops.

`forbid_provider_calls` patches `game.gm.call_gpt` and `semantic_interpreter._invoke_interpretation_model` to raise. `ASHEN_DISABLE_LIVE_INTERPRETATION` is set.

## Shared state

Each scenario factory returns one bundle. A, B, and C each receive a deep copy. The initial hash is taken before the tick, so the three candidates share it.

The tick is idempotent via a harness flag on the session copy. That flag is not a world flag and is not part of the state hash. The hash covers the authoritative tuple: scene id, clue ids and texts, combat HP, time pressure, tick event types, interlocutor, improvisation ledger, world flags, NPC locations, entity ids, and turn counter.

## Dispatch

`select_contract` builds the ordinary contract with `enable_model_interpretation` left off and the environment pin set. It runs on a discarded copy so the selector's telemetry does not become the candidate's state.

`execute_authorized` then calls one existing function:

| Selector | Call |
|---|---|
| social | `play_turn` (the PR-DE social entry, which calls `resolve_social_action`) |
| exploration, travel, world_action | `resolve_noncombat_action` |
| exploration on the K1 scene with utterance `Search.` | `resolve_exploration_action` with the PR-DE synthetic investigate action |
| combat, and the utterance is the quarterstaff attack | `resolve_attack` with `roll_die` patched to 10 |
| generation | no resolver |

`_apply_authoritative_resolution_state_mutation` runs after a domain resolution. If it raises, the bundle returns to the post-resolver copy and the exception is recorded. That is not an engine undo log.

## What the runner does not do

It does not call a provider, write `data/`, add a combat rule, add an inventory spend, or wire downtime. A preview that would have to roll returns `unsupported` for `social_check`. Attack and configured skill previews read `player_can_act` and `_get_skill_check_config` and do not call `resolve_attack` or `resolve_skill`.
