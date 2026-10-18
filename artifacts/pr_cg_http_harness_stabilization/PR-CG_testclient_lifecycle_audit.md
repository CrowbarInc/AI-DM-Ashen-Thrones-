# PR-CG TestClient Lifecycle Audit

## Findings

- Direct `TestClient(app).get(...)` and context-managed `with TestClient(app)` both require AnyIO's blocking portal.
- The observed hang happens while AnyIO starts the portal, before the ASGI app handler runs.
- The stack enters `asyncio.runners.Runner`, then event-loop initialization, then `socket.socketpair()`.
- This is lower than FastAPI lifespan, application startup/shutdown, background tasks, or leaked TestClient portals.
- Existing project tests mostly construct per-test clients; no fixture-scope client leak was demonstrated.
- `tests/conftest.py` already disables live interpretation/preflight paths for deterministic local pytest.

## Fixture / Order Notes

- An early probe accidentally disabled the repo-local pytest basetemp and exposed a sandbox temp `PermissionError`; that was a diagnostic artifact, not the TestClient root cause.
- With repo-local basetemp and unsandboxed local execution, previously stalled HTTP tests execute and report pass/fail normally.

