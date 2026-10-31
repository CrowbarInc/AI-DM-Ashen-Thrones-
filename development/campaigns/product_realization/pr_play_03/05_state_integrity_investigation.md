# 05 — State Integrity Investigation

**Observed:** These are deterministic engine-owned mutations, not model-authored gameplay changes. The missing narration alone does not prove the turn/time/faction changes lacked authority. The documented successful-opening latch is nevertheless misleading, and an exception path permits repeated pressure advancement without a committed turn.

| Boundary | Actual ownership / behavior |
|---|---|
| Campaign record / creation | Existing campaign/character/scene bootstrap files exist independently. New Campaign calls `campaign_reset.apply_new_campaign_hard_reset`; session/combat roots reset, world playthrough residue clears, transcript empties. It intentionally does not narrate. |
| Initialization | Active scene/frontier_gate and required runtime roots exist before Start; addressability and scene runtime are synchronized. Preserve these legitimate bootstrap facts on failure. |
| Start attempt | `api.start_campaign:6217` increments turn in memory. `world.advance_world_tick` advances projects/factions/NPC agendas; `save_world` at 6222 persists it before the provider. `advance_clock` then adds time_pressure in session memory. |
| Opening delivered | No independent successful-opening test gates the tail. The resolution's success=true means engine bootstrap succeeded. Generic accepted text may be immutable and contract_satisfying despite failing opening meaning. |
| Turn committed | Common tail saves world at 5933, sets campaign_started=true at 6017, records delivered exchange as RESOLVED/ACTION_RESULT, saves session/combat and builds/logs response. The caller passes mark_campaign_started=True after any returned GM payload. Exceptions alone avoid this tail. |

Faction progression: `world._tick_advance_factions_one_step` adds pressure and agenda progress through existing progression owners; threshold crossings generate events. Original log has House Verevin and Ash Cowl faction_pressure events. Saved/reconstructed pressure values are 3/3/2 (starting frozen/default seed 2/2/1), agendas 1/1/1. Original pre-start snapshot is absent, so original deltas are inferred from source and the prescribed seed; the offline before/after deltas are directly observed. No GM world_updates/scene_update/new_scene_draft was accepted in the historical row.

| Failure case | Commit, counters and retry behavior |
|---|---|
| Provider operation raises inside call_gpt | Exception converted to normal GM error payload, fast fallback selected; synthetic RuntimeError yields 200, latch=true, turn=1, pressure=1, faction progression +1. Safe narration success is not established by this path. Unknown accounting usage also stops the playtest budget. |
| Provider returns plain/invalid response | Parser rejection returns a dict rather than raising; empty repair → safe answer; normal tail commits all above. Synthetic invalid and preserved-seed cases reproduce exact historical message. |
| Structured validator rejects | Same normal-return recovery boundary; rich but authority-rejected structured control also yields the generic answer and commits. |
| Retry disabled | Prevents extra provider dispatch, not tick/turn commits. Original 1 admission, 0 retries, five admissions remaining. |
| Fallback accepted / no usable opening | Delivery is sealed and success/latch/turn/time/factions persist. Current system conflates runtime response success with opening completion. |
| Sequential repeated Start after returned fallback | Latch, nonempty log, and turn gate reject with 409 before another tick. Controls confirm no additional state change or SDK call. The UI also disables Start. This prevents duplication but strands a player who never received an opening. |
| Uncaught pipeline exception | start_campaign catches it, subtracts turn only, saves session, rethrows. World was already saved; pressure is not reverted. Offline: false latch, turn 0, empty transcript, pressure 1; eligibility remains true. Repeating the failure yields pressure 2 and another faction +1. Existing “failed start does not mark started” test misses this pressure boundary. |

Original state therefore follows current engine authorization. There is no evidence of model-authorized truth injection or arbitrary provider mutation. What is demonstrably wrong is the claim that a successful opening occurred and the incomplete rollback/retry boundary. Whether one failed Start attempt should retain a simulation tick is a product commit-policy decision, not a fact derivable from narration failure. For PR-PLAY-04 recommend an explicit policy: preserve pre-Start initialization, commit opening turn/pressure once only on validated opening success; failed opening and failure retries do not advance them.

Implement that policy at the existing opening orchestration boundary, with staged working state and no early durable opening-only writes before success. Merely resetting campaign_started is unsafe: turn/log gates would still block retry, and bypassing them could duplicate the already-persisted tick. Do not blanket-reset legitimate initialization, replay this historical mutated save, or add a new persistent retry-state schema. Concurrent starts and process-crash atomicity were not tested; no concurrency/crash guarantee is claimed. If safe staging requires a new persistence subsystem or unbounded shared-turn refactor, stop for review.
