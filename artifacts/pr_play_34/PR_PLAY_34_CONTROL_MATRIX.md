# Readiness control matrix

| Control | Result | Evidence |
| --- | --- | --- |
| A | PASS | `artifacts/atgb/pr_play_34/readiness/A/20261102T010511Z-7938740cf7c8` |
| B | PASS | `artifacts/atgb/pr_play_34/readiness/A/20261102T010511Z-7938740cf7c8` |
| G | PASS | `artifacts/atgb/pr_play_34/readiness/A/20261102T010511Z-7938740cf7c8` |
| C | PASS | `artifacts/atgb/pr_play_34/readiness/C/20261102T010515Z-b271a1306a2f` |
| D | PASS | `artifacts/atgb/pr_play_34/readiness/D/20261102T010518Z-72a5246c067d` |
| E | PASS | `artifacts/atgb/pr_play_34/readiness/E/20261102T010519Z-a99ec2897600` |
| F | PASS | `artifacts/atgb/pr_play_34/readiness/F/20261102T010523Z-c621ea52169f` |

| Gate | Result |
| --- | --- |
| Process ownership | PASS |
| Normal startup | PASS |
| HTTP readiness | PASS |
| Normal shutdown | PASS |
| Startup failure cleanup | PASS |
| Timeout cleanup | PASS |
| Observer worker | PASS |
| Occupied-port protection | PASS |
| Bootstrap state integrity | PASS |
| Provider requests | 0 |
| Live gameplay turns | 0 |
| Gameplay code modifications | 0 |
| Relevant regression tests | PASS |

Observer startup is supported through `runner.start_worker(script=...)` and was executed. It is not "not applicable."

Startup failure (C) removed the existing retry-suppression environment flags so the real worker refused to become ready at stage `socket_listening` (`RuntimeError`). No HTTP readiness file was written. Verdict `BLOCKED`.

Timeout (D) used `startup_timeout=0.4`. The poll records `readiness_deadline_expired`. Verdict `BLOCKED`.

Occupied port (F) records stage `socket_binding` and OS error 10048. The unrelated holder was not terminated by the harness. The worker image query was empty because that process had already exited; its launch command is the base interpreter.
