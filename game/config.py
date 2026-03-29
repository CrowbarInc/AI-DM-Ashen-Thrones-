from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

# Always load the repo-root .env explicitly rather than relying on cwd.
load_dotenv(dotenv_path=ENV_PATH)

def _getenv_required(name: str) -> str:
    val = os.getenv(name)
    if val is None or not str(val).strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val

# Secrets (required)
OPENAI_API_KEY = _getenv_required("OPENAI_API_KEY")

# Non-secrets (defaults allowed)
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
