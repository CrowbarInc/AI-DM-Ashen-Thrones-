# Experimental configuration

| Item | Value |
| --- | --- |
| Repository revision | `d40f1ed198236c604085f1c842ead267a8104ce2` |
| Worktree | `game/` and `tools/playtest/` were already dirty before this experiment. This run did not change those files. |
| Runner SHA-256 | `2fbb17638653180f04e4995e0399f72e061a38a5506ef472e1c5e90cfc841181` |
| Process launch | `start_worker` uses the base interpreter and refuses to launch when that interpreter is missing. |
| Fixture | `frontier-gate-v1` |
| Fixture manifest SHA-256 | `9c390c78f3fcf7507793e1037eb0add59e5e373050d1996f29f0c26f3b7bf0ea` |
| Scenario file | `tools/playtest/scenarios/FiveTurnGameplay.json` (unchanged) |
| Fixture request ceiling | 6, left unchanged on disk |
| Mission request ceiling applied in memory | 10 |
| Effective request ceiling | 10 |
| Token ceilings | input 200000, output 20000, total 220000 |
| Provider | OpenAI Responses, credentials present, value not recorded |
| Configured model | `MODEL_NAME=gpt-4.1-mini` |
| Ready-attested model | `gpt-4.1-mini` |
| Returned model | `gpt-4.1-mini-2025-04-14` |
| `DEFAULT_MODEL_NAME` | unset; application falls back to `MODEL_NAME` |
| Routing flags | `ENABLE_MODEL_ROUTING` unset; pinned-model override absent |
| Interpretation / expression | not disabled |
| Opening renderer override | not set; production opening path |
| Opening response capture | enabled for evidence only |
| SDK retries | 0 |
| Host retries | disabled |
| HTTP timeout | 90 seconds, from the scenario request timeout |
| Isolated run | `artifacts/atgb/pr_play_35/live/20261102T011549Z-bd0c88693cd0` |
| User campaign | repository `data/`; fingerprint unchanged |
| Character | Galinor, wizard, HP 8/8 |
| Starting scene after reset | `frontier_gate`, Day 1, turn 0 |

The five strings prepared for submission, and not sent:

1. What is available here?
2. Have you heard any interesting rumors lately?
3. I want to investigate the footprints.
4. I want to follow the trail connected to the missing patrol.
5. I examine the footprints here more carefully.

These are the ordinary intents specified for this experiment. The exact PR-PLAY-31 lines were not substituted. The frontier-gate fixture and campaign assumptions are the same baseline PR-PLAY-31 used.

A controller preflight at `20261102T011535Z-b14a75245c0e` stopped before creating a worker because it looked for the source text `sys._base_executable`. The repair is `getattr(sys, "_base_executable", sys.executable)`. That check was corrected. It dispatched no provider request and did not start a campaign. The live run above is the single initialization attempt.
