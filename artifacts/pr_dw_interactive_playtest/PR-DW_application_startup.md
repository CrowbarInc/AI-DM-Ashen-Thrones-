PR-DW application startup

Startup command:
`.\.venv\Scripts\python.exe run.py`

Runtime environment used:
- `ASHEN_DATA_DIR=<repo>\artifacts\pr_dw_interactive_playtest\disposable_data`
- `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1`
- `ASHEN_DISABLE_LIVE_INTERPRETATION=1`
- `UVICORN_RELOAD=false`

Observed startup:
- Uvicorn started server process.
- Application startup completed.
- Server listened on `http://127.0.0.1:8000`.

Startup warning:
- Upstream preflight was skipped by env.
- Operator summary reported: `WARNING - preflight skipped by env - live-upstream conclusions not established`.

Frontend:
- Static frontend served by the same backend from `static/index.html` and `static/app.js`.

Save location:
- Production default: `data/`.
- PR-DW disposable run: `artifacts/pr_dw_interactive_playtest/disposable_data`.

