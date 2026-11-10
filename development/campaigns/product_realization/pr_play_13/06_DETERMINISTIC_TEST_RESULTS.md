# 06 — Deterministic Test Results

`tests/test_pr_play_13_opening_renderer.py` collects 30 tests. All 30 passed. No live provider dispatch was used. Provider clients in these tests are stubs.

| Id | Result | Where |
| --- | --- | --- |
| R1 | Pass | Legacy opening text and guidance unchanged with the flag unset |
| R2 | Pass | Enabled flag selects the renderer and commits |
| R3 | Pass | Public notice, gate, and runner entries included |
| R4 | Pass | Secret identity, quest outcome, undiscovered place, faction, motivation, and restricted metadata excluded |
| R5 | Pass | Unknown id rejected |
| R6 | Pass | Unknown variant rejected |
| R7 | Pass | Duplicate rejected |
| R8 | Pass | Missing required entry rejected |
| R9 | Pass | Reversed required order rejected |
| R10 | Pass | Narration field rejected and not published |
| R11 | Pass | Model authority field rejected |
| R12 | Pass | Exact authored notice accepted |
| R13 | Pass | Reviewed concise notice accepted |
| R14 | Pass | Unsupported gloss cannot enter the output |
| R15–R20 | Pass | Gold, movement, combat, skill success, quest completion, and hidden identity are absent |
| R21 | Pass | Required facts present in the committed opening |
| R22 | Pass | One commit; a repeat start is 409 |
| R23 | Pass | Injected prose returns 422 and does not commit |
| R24 | Pass | The failed opening can be started again |
| R25 | Pass | Concurrent starts commit one opening |
| R26 | Pass | Pre-existing lantern overlay remains |
| R27 | Pass | Model scene update is rejected and does not add gold |
| R28 | Pass | Every trace row has id, variant, source, text, disclosure, and position |
| R29 | Pass | Injected provider sentence is absent from the response body |
| R30 | Pass | Success and failure bodies do not carry the injected fact |
| R31 | Pass | Historical accepted opening `20261030T191257Z-ecc1b6062bdc` still commits in legacy mode |
| R32 | Pass | Historical rejected opening `20261031T015747Z-5a6c03c902e3` still returns 422 in legacy mode |
| R33 | Pass | The same plan renders the same text with no provider |
| R34 | Pass | Harness `success` fixture emits a plan only when the flag is enabled; later turns keep narration fixtures |
| R35 | Pass | Rendered opening commits and a non-opening contract stays an ordinary turn. Five-turn run attempted 4 turns after the opening |
| R36 | Pass | Stubbed dispatches only. The five-turn run records zero live calls |

Historical captures were not forced through the new schema. Legacy mode preserved their 200 and 422 outcomes. Renderer mode used a new plan built from the same opening context.

Five-turn evidence: `artifacts/atgb/automated_playtests/20261101T144743Z-14b8c942e340`. Deterministic mode, renderer selected, opening accepted, 6 synthetic requests, stop `provider_budget_exhaustion`, 4 attempted turns.
