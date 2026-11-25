"""Remove credential-shaped text from evaluation artifacts."""
from __future__ import annotations

import re

SECRET_RE = re.compile(
    r"sk-[A-Za-z0-9_\-]{8,}|Bearer\s+\S+|OPENAI_API_KEY\s*[=:]\s*\S+",
    re.IGNORECASE,
)


class RedactionError(RuntimeError):
    pass


def redact(text: str) -> str:
    return SECRET_RE.sub("[REDACTED]", str(text or ""))


def assert_redacted(text: str) -> None:
    if SECRET_RE.search(text or ""):
        raise RedactionError("secret redaction failed")
