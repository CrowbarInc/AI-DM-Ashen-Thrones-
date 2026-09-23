# PR-BE wait / time-passage probe

Date: 2026-09-22
Scene: canonical `frontier_gate`
Script: `development/tmp/prbe_wait_action_probe.py`
JSON: `artifacts/prbe_wait_action_ownership/probe_matrix.json`

Parser / helper / exploration-resolution snapshot. No live model. No production change.

| Input | parse type | lane | stay | local move | travel dest | passive wait | HA | resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `I wait.` | None | — | no | no | no | no | none | None |
| `I wait a moment.` | None | — | no | no | no | no | none | None |
| `I pause for a moment.` | None | — | no | no | no | no | none | None |
| `I stay here for a while.` | observe | explicit_stay | yes | no | no | no | none | observe |
| `I stand here and wait.` | None | — | no | no | no | no | none | None |
| `I wait until evening.` | None | — | no | no | no | no | none | None |
| `I wait for an hour.` | None | — | no | no | no | no | none | None |
| `I wait for the guard to leave.` | travel | — | no | no | no | no | none | travel, dest unresolved |
| `I wait until someone arrives.` | None | — | no | no | no | no | none | None |
| `I look around.` | observe | — | no | no | no | no | none | observe |
| `I listen.` | observe | human_adjacent_observe | no | no | no | no | listen | observe |
| `I rest.` | None | — | no | no | no | no | none | None |
| `I step back.` | None | — | no | no | no | no | none | None |
| `I step back and wait.` | None | — | no | no | no | no | none | None |
| `I go to the quay.` | travel | — | no | no | yes | no | none | travel, dest unresolved |
| `I stay here.` | observe | explicit_stay | yes | no | no | no | none | observe |
| `I hold position and wait.` | None | — | no | no | no | no | none | None |
| `I wait for the commotion to pass.` | observe | passive_interruption_wait | no | no | no | yes | none | observe |
| `I pace.` | custom | local_physical_movement | no | yes | no | no | none | custom |
| `I step closer.` | custom | local_physical_movement | no | yes | no | no | none | custom |

Notes:

- Stay is remain-in-place, realized as observe. Hint is scene observation, not elapsed time.
- Passive interruption wait is observe of a disturbance easing. It is not ordinary wait.
- `I wait for the guard to leave.` is leftover `leave` → travel, not a wait owner.
- `I step back.` is outside the PR-AQ local-movement regex (`closer` / `along` / `beside` / `a few steps` / `pace`).
- Custom resolution hint is generic narration. No `state_changes` or `world_updates` for wait, stay, pace, or step closer.
