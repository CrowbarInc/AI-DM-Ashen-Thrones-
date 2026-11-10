# PR-PLAY-19 State Integrity
PASS for deterministic mutations; FAIL for confidentiality of the raw successful HTTP envelope. Before/after snapshots: artifacts/atgb/pr_play_19/live/20261101T155921Z-dece64b94204/baseline and /after, including API states and persistent documents. normalized_state_diff.json records full normalized differences. Baseline follows silent new_campaign reset and precedes start_campaign; it is not the player's canonical store.

| Domain | Before / after |
| --- | --- |
| Character/location | Character identical; active_scene_id frontier_gate unchanged; scene addressability unchanged. |
| Campaign time | No separate campaign_time/date field present. Engine time_pressure clock 0 -> 1; other clocks remain 0. |
| Turn/transcript | 0 -> 1 and one appended opening log; this is internal bootstrap, zero ordinary player turns. |
| Campaign latch | false -> true. |
| Inventory/currency | Entire character document unchanged; inventory unchanged. No separate currency field introduced. |
| Quest/NPC state | No quest changes; world NPC/relationship rows unchanged. |
| Combat | Normalized combat identical; only persistence-envelope metadata changed. |
| World facts | Flags/counters unchanged; faction pressure and agenda each +1, with two existing threshold events. |
| Overlays | No overlay entries changed; zero additions/omissions. |

Accepted mutations are owned by existing initialization: game/api.py:6439-6456 tracks provisional state, increments turn, advance_world_tick and time_pressure; game/world.py:259-350 defines faction progression/threshold events. World faction pressure [2,2,1] -> [3,3,2], agenda [0,0,0] -> [1,1,1]. This is deterministic engine progression, not provider-supplied state. Runtime narration/conversation caches and one committed log are expected. No unexpected state mutation identified; harness field/overlay checks also pass.

Provider plan only selects public variants. scene_update, world_updates, activate_scene_id and new_scene_draft are null in published gm_output. No proposed state mutation required rejection; rejected initialization/rollback was not exercised in this successful live attempt. Do not infer rollback correctness from success. No unsupported consequential narration published.

Hidden-information assessment: hidden truth absent from assembled provider request and opening text; all render traces public. However raw start_campaign response includes campaign.character_secret.hidden_truth, unlike public_state in both before/after snapshots. This is a confirmed HTTP publication boundary problem; it does not alter deterministic campaign data. Debug snapshots are reviewer-only and contain internal campaign information. UI display and unrelated secret boundaries were not audited. No broad claim of full information-boundary preservation is justified.
