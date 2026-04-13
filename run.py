from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from game.config import OPENAI_API_KEY

ROOT_DIR = Path(__file__).resolve().parent
ENV_PATH = ROOT_DIR / ".env"

if __name__ == "__main__":
    print("Startup cwd:", os.getcwd())
    print(".env path:", ENV_PATH)
    print(".env exists:", ENV_PATH.exists())
    print("OPENAI_API_KEY present:", bool(OPENAI_API_KEY))

    # Set UVICORN_RELOAD=false temporarily when diagnosing env/reloader issues.
    reload_enabled = os.getenv("UVICORN_RELOAD", "true").strip().lower() in {"1", "true", "yes", "on"}
    print("Uvicorn reload enabled:", reload_enabled)
    print(
        "OpenAI API billing/health preflight runs during FastAPI worker startup; watch for [API preflight] lines "
        "and the following [upstream_dependent_run_gate] summary (BHC3 operator surface).",
        flush=True,
    )

    uvicorn.run(
        "game.api:app",
        host="127.0.0.1",
        port=8000,
        reload=reload_enabled,
    )
