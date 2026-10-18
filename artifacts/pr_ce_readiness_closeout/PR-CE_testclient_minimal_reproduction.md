# PR-CE TestClient minimal reproduction

Each case ran in its own process with a 12 second parent timeout, using `.venv` Python 3.12.0. No AI-DM application import. No live provider calls.

## Isolated cases

| Case | Result | Time |
| --- | --- | --- |
| `socket.socketpair()` on the main thread | completed | 0.001s |
| `socket.socketpair()` on a background thread | completed | 0.002s |
| `asyncio.ProactorEventLoop` on the main thread | completed (`ran`) | 0.001s |
| `asyncio.ProactorEventLoop` on a background thread | completed (`ran`) | 0.002s |
| `WindowsSelectorEventLoopPolicy` on a background thread | completed (`_WindowsSelectorEventLoop`, `ran`) | 0.002s |
| Trivial FastAPI `GET /ping` via `TestClient`, default policy | 200 `{"ok": true}` | 0.028s |
| Same request after `WindowsSelectorEventLoopPolicy` | 200 `{"ok": true}` | 0.027s |
| Same request with `backend_options={"loop_factory": WindowsSelectorEventLoopPolicy().new_event_loop}` | 200 `{"ok": true}` | 0.027s |

The hang does not occur in a trivial FastAPI application on this machine.

## Race stress

The Python 3.12 fallback always performs a non-blocking `connect`. A stress probe copied that algorithm:

- 8 threads, 400 attempts each (3200 pairs)
- `connect` raised `BlockingIOError` on all 3200 attempts
- `accept` with a 0.2s timeout never timed out
- maximum attempt time 0.0021s
- errors 0

So the non-blocking connect race is present, and on this Windows build `accept` still completes.

## Application tests that previously stalled

These now reach the application. They do not hang in `socketpair` / `accept`.

| Test | Result |
| --- | --- |
| `tests/test_social_question_relevance_answer_selection.py::test_general_http_ask_a_not_b` | completed in 1.57s, assertion failed |
| `tests/test_activate_scene_validation_and_get_persistence.py::test_invalid_activate_scene_id_ignored_safely` | passed in 1.26s |
| Full social relevance file | completed in 1.90s: 20 passed, 4 failed |
| Full scene activation file | completed in 1.50s: 6 passed |

The four social HTTP failures are narration assertions after the handler runs (`morning bell` / `weigh-stone` missing, or an unauthorized `second horn` span present). Clue discovery still logs. They are not a portal hang. The same four failures were observed before the subjective-classifier edit.

## Classification

Infrastructure-level hang: not reproduced here. PR-CD's stack is real for Python 3.12's Proactor self-pipe, and it matches `socket.py` line 646, but this environment completes both the trivial client and the previously stalled tests. No repository fixture was required to unblock them.
