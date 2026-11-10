# PR-PLAY-23 test results

Zero live-provider requests. Pytest live-model guards apply; SDK/interpretation transports are synthetic. Owned worker runs use Deterministic mode and reject external socket connections. No live mode or live gameplay was executed.

| Run | Passed | Failed | Errors |
| --- | ---: | ---: | ---: |
| focused | 37 | 0 | 0 |
| existing | 268 | 26 | 1 |
| paired_before | 74 | 8 | 0 |
| io_retry | 6 | 0 | 0 |
| harness_final | 70 | 0 | 0 |

Focused matrix: original captured failure; accessible runner; equivalent guard wording; direct ASK; notice-board INSPECT; unavailable/cross-scene/unregistered/unknown-access/hostile/locked/player-barrier targets; explicit authored access=false; travel; extra/mismatched/unsupported consequential components; state integrity; publication and public projection. Opening → original RAW interpretation replay → real parser/binding → social resolver → canonical NPC response → serialized Player HTTP publication is exercised. A synthetic hidden sentinel stays authoritative and absent from HTTP. Character/inventory/currency/campaign/combat/conditions remain identical; world changes equal one existing authorized world tick. Negative HTTP integration rejects the consequential first step without running ASK or changing world/character state.

Harness coverage: classifier units plus owned real deterministic worker, HTTP transport, actual snapshots/evaluator/loop/export. A synthetic decisive HTTP 200 failure causes exactly one chat submission, one initialization, one opening, zero executed/completed gameplay turns, and cleanup. A separate configured ceiling run never exceeds two synthetic dispatches. Existing six-request ceiling and failure/export controls also run.

Relevant existing command: 17 files listed in existing.xml/text: PR-PLAY-20/18/13/04, start API, state/UI policies and regressions, shared turn pipeline, PR-PLAY-21, PR-EA orchestration, PR-EC movement, physical compound/perception, PR-DU pipeline and PR-DY live adapter (mocked). Raw result: 268 passed, 26 failed, 1 setup error. The original 17 functional failures persist (3 opening / 14 shared turn). Seven additional physical-action tests and one PR-DY clarification test fail identically with the new normalizer disabled: paired_before.xml contains 74 passed / 8 failed across the five expanded files. These are confirmed preexisting in the expanded test scope, not newly introduced regressions. They do not exercise the exact same-target approach + supported interaction rule; no unrelated repair was attempted.

Two separate Windows os.replace WinError 5 failures affected an opening setup case and second-start rejection. The focused rerun of all five invalid-provider controls and second-start rejection passed 6/6 (io_retry.xml); the external cause remains unknown. Thus 25 reproducible functional failures remain in the full expanded scope, including all original 17. No historical functional failures resolved; no new reproducible regressions found in the exercised scope. Do not interpret this as a green full repository suite.

Harness expectations intentionally migrated: a text-only envelope cannot establish execution; missing player-facing text is decisive; the existing five-turn fixture's T2 binding refusal must stop before T3 injection/budget exhaustion. Its actual three synthetic requests total 60 input / 30 output / 90 tokens, two requests on ordinary turns and one opening request. The positive evaluator fixture now supplies native accepted-speaker evidence. Intermediate failures and their exact causes are retained in intermediate_findings.md and initial logs.

Commands use .venv/Scripts/python.exe -m pytest, --tb=short and separate --basetemp directories. XML preserves test IDs, counts and detailed failures. focused_initial/second/third/fourth are fixture-development logs; focused and harness_final are the final checks. Paired baseline uses -p artifacts.pr_play_23.baseline_plugin (identity normalization) and changes no production files.
