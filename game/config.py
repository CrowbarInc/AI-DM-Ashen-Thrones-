from __future__ import annotations

import os

from dotenv import load_dotenv

# Load environment from .env (if present). This enables local development without
# hardcoding secrets into source control.
load_dotenv()


def _getenv_required(name: str) -> str:
    val = os.getenv(name)
    if val is None or not str(val).strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


# Secrets (no defaults)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Non-secrets (defaults allowed)
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

