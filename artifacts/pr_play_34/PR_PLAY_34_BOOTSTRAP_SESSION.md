# Bootstrap session

Control A, isolated store `artifacts/atgb/pr_play_34/readiness/A/20261102T010511Z-7938740cf7c8/data`.

| Observation | Before `GET /api/state` | After `GET /api/state` |
| --- | --- | --- |
| `session.json` exists | False | True |
| Inside isolated store | — | True |
| `campaign_started` | — | False |
| `turn_counter` | — | 0 |
| Chat history entries | — | 0 |
| Session log entries | — | 0 |
| Last action debug | — | False |
| Debug trace operations | — | rebuild_active_scene_entities |

Gameplay initialization did not occur. The trace `rebuild_active_scene_entities` is recorded and is compose-time scene bookkeeping, not a turn. HTTP requests: [{'method': 'GET', 'path': '/api/state'}]. Provider events: ['initialized']. Scenario steps: [].

The same unstarted result was observed for the observer worker. Failure, timeout, and occupied-port runs did not create `session.json`.
