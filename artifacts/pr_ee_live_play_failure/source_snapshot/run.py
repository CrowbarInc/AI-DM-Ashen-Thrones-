from __future__ import annotations

import os

import uvicorn

from game.config import ENV_PATH

SKIP_UPSTREAM_API_PREFLIGHT_ENV = "ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _openai_api_key_configured() -> bool:
    return bool((os.getenv("OPENAI_API_KEY") or "").strip())


def main() -> None:
    print("Startup cwd:", os.getcwd())
    print(".env path:", ENV_PATH)
    print(".env exists:", ENV_PATH.exists())
    print("OPENAI_API_KEY configured:", _openai_api_key_configured())
    if not _openai_api_key_configured() and not _env_flag(SKIP_UPSTREAM_API_PREFLIGHT_ENV):
        print(
            "OPENAI_API_KEY is not configured; FastAPI startup preflight will report this before "
            "live upstream-dependent gameplay can run.",
            flush=True,
        )

    # Set UVICORN_RELOAD=false temporarily when diagnosing env/reloader issues.
    reload_enabled = _env_flag("UVICORN_RELOAD", default=True)
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


if __name__ == "__main__":
    main()
