# PR-CE closeout

Mode: test infrastructure and subjective classification closeout.

Live provider calls: 0.

Inherited PR-CD decision: E — INCONCLUSIVE.

PR-CE decision: E — OTHER REGRESSION.

## Phase A — TestClient

The project suite uses `.venv` Python 3.12.0 on Windows 11 build 26200. The default asyncio policy is `WindowsProactorEventLoopPolicy`. Python 3.12 on Windows has no native `socket.socketpair`, so `ProactorEventLoop._make_self_pipe` uses the TCP fallback whose `accept` is the frame in the PR-CD stack.

A trivial FastAPI `TestClient` request completes in about 0.03s. The same request also completes under `WindowsSelectorEventLoopPolicy`. A 3200-iteration threaded stress of the fallback `accept` did not hang. The previously stalled tests now finish:

- `test_general_http_ask_a_not_b` fails an assertion in 1.57s
- `test_invalid_activate_scene_id_ignored_safely` passes in 1.26s

The hang is not reproduced here, and a selector policy would still call `socket.socketpair` on this Python. No event-loop or TestClient change was applied.

## Phase B — subjective classification

"Which loaf would you recommend?" already matched `recommend` / `which ... would you`. "Which loaf do you usually keep for yourself?" did not, because a noun sits between `which` and `do you` and the habit verb is `keep`, not `would`.

The existing expression now also matches ordinary `which ... do you [usually] <preference verb>` forms, habit questions, `like best`, and `keep ... for yourself`. Restricted and consequential checks still run first. Bare `murder` is now consequential, so a murder question cannot enter the harmless lane through an older `which ... would you` match.

PR-CA T1, T2, and T3 project as `harmless_subjective_response_permitted`, `claim_only`, no durable mutation. T4 stays `genuine_uncertainty` and does not promote the player's recommendation premise. Positive controls cover baker, innkeeper, merchant, artisan, traveler, and guard. Negative controls stay refusal or consequential.

## Phase C — integrity

Focused authority, narration-only, retry-contract, and C18 tests passed. See `PR-CE_authority_integrity.md`.

## Phase D — regression

| Slice | Result |
| --- | --- |
| PR-CE classification | 13 passed |
| PR-CC focused | 36 passed |
| Social resolver | 31 passed |
| Social relevance | 20 passed, 4 failed |
| PR-BY and PR-BW | 27 passed |
| Authority including C18 | 104 passed |
| Scene activation HTTP | 6 passed |
| Broad pytest | 7431 passed, 202 failed, 99 skipped, 0 timed out, 0 interrupted, 590.52s |

The broad suite completed. It is not green. Failures are assertions across 65 files, including the four social HTTP narration tests. No portal hang occurred.

## Why this is not ready for a live comparison

Deterministic tests can execute, and ordinary subjective questions are recognized without an authored answer. Consequential controls in the new tests hold. Broad regression did not pass, so PR-CC is not ready for a controlled live comparison.

## Recommended next step

Keep live calls off. Triage the 202 completed assertion failures, starting with the HTTP narration cluster that is now reachable, before any live comparison.
