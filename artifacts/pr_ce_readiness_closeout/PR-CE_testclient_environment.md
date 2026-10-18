# PR-CE TestClient environment

Inventory taken from the project virtualenv used by the deterministic suite. No live provider calls.

## Interpreter

| Item | Value |
| --- | --- |
| Suite interpreter | `.venv\Scripts\python.exe` |
| Python | 3.12.0 (tags/v3.12.0:0fb18b0, Oct 2 2023) [MSC v.1935 64 bit (AMD64)] |
| Platform | Windows-11-10.0.26200-SP0 |
| Windows version | major 10, minor 0, build 26200, platform 2 |
| Native `socket.socketpair` | absent (`_socket.socketpair` is missing) |
| Fallback | `socket.socketpair` uses a TCP pair on `127.0.0.1` (`Python312\Lib\socket.py`, accept at line 646) |

`py` on this machine resolves to a different interpreter, Python 3.14.3. That interpreter was not used for pytest. The PR-CD faulthandler frames (`socket.py` line 646 `socketpair`, line 295 `accept`, `proactor_events.py` `_make_self_pipe`) match this Python 3.12 standard library.

## Packages in `.venv`

| Package | Version |
| --- | --- |
| fastapi | 0.140.0 |
| starlette | 1.3.1 |
| anyio | 4.14.2 |
| httpx | 0.28.1 |
| pytest | 9.1.1 |
| uvicorn | 0.51.0 |
| sniffio | 1.3.1 |
| pytest-asyncio | not installed |

Starlette 1.3.1 emits `StarletteDeprecationWarning` when `fastapi.testclient` imports `starlette.testclient` with httpx. That warning is not the hang.

## Asyncio and pytest

| Item | Value |
| --- | --- |
| Active event-loop policy | `WindowsProactorEventLoopPolicy` |
| `asyncio.new_event_loop()` | `ProactorEventLoop` |
| `WindowsSelectorEventLoopPolicy` | present on Python 3.12 |
| pytest `asyncio_mode` | unset |
| pytest-asyncio | not installed |
| Installed pytest plugin | `anyio-4.14.2` |
| `pytest.ini` | no asyncio setting; `addopts = -q --basetemp=development/tmp/pytest` |

`ProactorEventLoop` builds its self-pipe with `socket.socketpair()` in `asyncio/proactor_events.py` `_make_self_pipe`. AnyIO's blocking portal starts that loop from `starlette.testclient.TestClient._portal_factory` via `anyio.from_thread.start_blocking_portal`. On this Python, a `SelectorEventLoop` also uses `socket.socketpair()` for its self-pipe, so a Windows selector policy does not avoid the fallback pair.

## Environment variables

Checked in a fresh interpreter before pytest's `conftest.py` runs:

| Variable | Value |
| --- | --- |
| `PYTHONASYNCIODEBUG` | unset |
| `PYTEST_ADDOPTS` | unset |
| `PYTEST_ASYNCIO_MODE` | unset |
| `ANYIO_BACKEND` | unset |
| `HTTPX_LOG_LEVEL` | unset |
| `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT` | unset until pytest |
| `ASHEN_DISABLE_LIVE_INTERPRETATION` | unset until pytest |

`tests/conftest.py` sets `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1` if unset and forces `ASHEN_DISABLE_LIVE_INTERPRETATION=1` for the session. It does not change the asyncio event-loop policy.

## Existing fixtures

`tests/conftest.py` blocks accidental live model calls and skips upstream API preflight. HTTP tests construct `fastapi.testclient.TestClient` directly. No repository fixture replaces the event loop or `socket.socketpair`.
