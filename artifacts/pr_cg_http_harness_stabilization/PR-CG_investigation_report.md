# PR-CG Investigation Report

## Decision

B - ENVIRONMENTAL CAUSE ISOLATED

## Summary

The intermittent Windows TestClient hang was reproduced below the application stack. The managed sandbox can hang in Python's Windows `socket.socketpair()` implementation, specifically while waiting in `accept()`. Starlette/FastAPI TestClient reaches this through AnyIO's blocking portal before an ASGI handler executes.

The same interpreter and tests complete normally in unsandboxed local Windows execution. Therefore no gameplay change, production event-loop override, or dependency change is justified in this repository.

## Evidence

- `sandbox_socketpair_probe.stderr.txt`: sandboxed socketpair timeout and stack.
- `PR-CG_reliability_matrix.json`: supported unsandboxed bounded HTTP run.
- `repetition_verification.txt`: repeated supported-run verification.
- `probe_outputs/`: stdout/stderr for each bounded probe.

## Root Cause

Managed sandbox loopback/socketpair behavior on Windows. The blocked call chain is:

```text
Starlette/FastAPI TestClient
AnyIO blocking portal
asyncio event-loop initialization
socket.socketpair()
socket.accept()
```

## Minimal Reproduction

`socket.socketpair()` alone reproduces the hang inside the managed sandbox. No FastAPI app, pytest fixture, application startup, or game state is required.

## Repair

No repository repair was implemented. The supported deterministic configuration is to run HTTP/TestClient tests with `.venv\Scripts\python.exe` in normal local Windows execution, outside the managed sandbox loopback restriction.

## Recommended Next Step

Continue PR-CF's classified gameplay/application assertion failures using the supported local execution configuration. Treat future socketpair/accept timeouts inside the managed sandbox as environmental infrastructure failures, not application regressions.

