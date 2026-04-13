from __future__ import annotations

"""Load environment configuration for the game package.

This module owns env loading. It preserves legacy `MODEL_NAME` support while
adding deterministic model-routing settings. These values must not change
existing turn behavior until later blocks wire routing into call sites.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

# Always load the repo-root .env explicitly rather than relying on cwd.
load_dotenv(dotenv_path=ENV_PATH)


def _getenv_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None

    value = value.strip()
    return value or None


def _getenv_required(name: str) -> str:
    val = _getenv_optional(name)
    if val is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


def env_flag(name: str, default: bool = False) -> bool:
    """Parse a boolean environment flag using common truthy and falsy strings."""
    value = _getenv_optional(name)
    if value is None:
        return default

    normalized = value.lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


# Secrets (required)
OPENAI_API_KEY = _getenv_required("OPENAI_API_KEY")

# Model configuration (defaults allowed)
# `MODEL_NAME` remains for legacy compatibility. New configuration should
# prefer `DEFAULT_MODEL_NAME`.
MODEL_NAME = _getenv_optional("MODEL_NAME") or "gpt-4o-mini"
DEFAULT_MODEL_NAME = _getenv_optional("DEFAULT_MODEL_NAME") or MODEL_NAME
HIGH_PRECISION_MODEL_NAME = (
    _getenv_optional("HIGH_PRECISION_MODEL_NAME") or DEFAULT_MODEL_NAME
)
RETRY_ESCALATION_MODEL_NAME = (
    _getenv_optional("RETRY_ESCALATION_MODEL_NAME") or HIGH_PRECISION_MODEL_NAME
)
ENABLE_MODEL_ROUTING = env_flag("ENABLE_MODEL_ROUTING", default=True)
