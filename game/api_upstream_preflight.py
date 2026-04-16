"""Tiny upstream OpenAI health probe using the same Responses API path as ``call_gpt``.

Stores the latest result in-process for startup logs, CLI tools, and tests.
"""

from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from typing import Any, Callable, TypedDict

SKIP_UPSTREAM_API_PREFLIGHT_ENV = "ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"

from openai import APIConnectionError, APITimeoutError, AuthenticationError, PermissionDeniedError

from game.config import DEFAULT_MODEL_NAME, OPENAI_API_KEY
from game.gm import _classify_upstream_gpt_error, _error_code_from_upstream_error, _status_code_from_upstream_error

_PREFLIGHT_LOCK = threading.Lock()
_LATEST: dict[str, Any] | None = None

HealthClass = str  # literal union for readability at call sites


class UpstreamApiPreflightStatus(TypedDict, total=False):
    ok: bool
    health_class: HealthClass
    retryable: bool | None
    status_code: int | None
    error_code: str | None
    message_excerpt: str | None
    checked_at: str
    invalidates_upstream_dependent_runs: bool


# OpenAI Responses API requires max_output_tokens >= 16; lower values fail validation locally.
_OPENAI_RESPONSES_MIN_MAX_OUTPUT_TOKENS = 16
_PREFLIGHT_MAX_OUTPUT_TOKENS = 16


def _clamp_preflight_max_output_tokens(requested: int) -> int:
    """Ensure preflight never sends a sub-minimum token budget (API rejects < 16)."""
    return max(int(requested), _OPENAI_RESPONSES_MIN_MAX_OUTPUT_TOKENS)


_MODEL_ACCESS_FAILURE_CLASSES: frozenset[str] = frozenset(
    {
        "model_not_found",
        "model_removed",
        "model_not_available",
        "unsupported_model",
        "invalid_model",
    }
)


def get_latest_upstream_api_preflight() -> UpstreamApiPreflightStatus | None:
    with _PREFLIGHT_LOCK:
        return None if _LATEST is None else dict(_LATEST)


def _set_latest_upstream_api_preflight(status: UpstreamApiPreflightStatus) -> None:
    global _LATEST
    with _PREFLIGHT_LOCK:
        _LATEST = dict(status)


def reset_upstream_api_preflight_cache_for_tests() -> None:
    global _LATEST
    with _PREFLIGHT_LOCK:
        _LATEST = None


def upstream_api_preflight_disabled_by_env() -> bool:
    return os.environ.get(SKIP_UPSTREAM_API_PREFLIGHT_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def log_upstream_api_preflight_at_startup() -> None:
    """Run probe (unless skipped by env) and print developer-facing lines to stdout."""
    if upstream_api_preflight_disabled_by_env():
        print(
            f"[API preflight] skipped ({SKIP_UPSTREAM_API_PREFLIGHT_ENV} is set)",
            flush=True,
        )
        return
    cached = get_latest_upstream_api_preflight()
    if cached is not None:
        hc = cached.get("health_class", "")
        inv = bool(cached.get("invalidates_upstream_dependent_runs"))
        print(
            f"[API preflight] using in-process cache health_class={hc} "
            f"invalidates_upstream_dependent_runs={inv} checked_at={cached.get('checked_at')}",
            flush=True,
        )
        return
    status = run_upstream_api_preflight()
    if status.get("ok"):
        print(
            f"[API preflight] ok health_class=healthy checked_at={status.get('checked_at')}",
            flush=True,
        )
        return
    for line in format_upstream_api_preflight_startup_lines(status):
        print(line, flush=True)


def _utc_checked_at() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _invalidates_runs(health_class: str) -> bool:
    return health_class != "healthy"


def compute_api_runtime_health_from_exception(exc: Exception, *, checked_at: str | None = None) -> UpstreamApiPreflightStatus:
    """Map an upstream exception to the canonical preflight status shape (no network I/O)."""
    at = checked_at or _utc_checked_at()
    cl = _classify_upstream_gpt_error(exc)
    fc = str(cl.get("failure_class") or "unknown_api_error")
    status_code = cl.get("status_code")
    if not isinstance(status_code, int):
        status_code = _status_code_from_upstream_error(exc)
    error_code = cl.get("error_code")
    if not isinstance(error_code, str) or not error_code.strip():
        error_code = _error_code_from_upstream_error(exc)
    retry_raw = cl.get("retryable")
    retryable: bool | None
    if isinstance(retry_raw, bool):
        retryable = retry_raw
    else:
        retryable = None
    excerpt = cl.get("message_excerpt")
    if not isinstance(excerpt, str):
        excerpt = str(exc or "").strip()[:240] or None

    health_class = _health_class_from_exception(exc, fc, status_code, error_code)

    return {
        "ok": False,
        "health_class": health_class,
        "retryable": retryable,
        "status_code": status_code if isinstance(status_code, int) else None,
        "error_code": error_code if isinstance(error_code, str) and error_code.strip() else None,
        "message_excerpt": excerpt,
        "checked_at": at,
        "invalidates_upstream_dependent_runs": _invalidates_runs(health_class),
    }


def _health_class_from_exception(
    exc: Exception,
    failure_class: str,
    status_code: int | None,
    error_code: str | None,
) -> str:
    """Prefer SDK exception types, then structured fields from ``_classify_upstream_gpt_error``."""
    if isinstance(exc, AuthenticationError):
        return "auth_failure"
    if isinstance(exc, PermissionDeniedError):
        return "permission_failure"
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        return "transient_upstream_failure"

    ec = (error_code or "").strip().lower()
    if ec == "insufficient_quota" or failure_class == "insufficient_quota":
        return "insufficient_quota"
    if ec in {"billing_hard_limit_reached"} or failure_class in {"billing_hard_limit_reached"}:
        return "insufficient_quota"
    if failure_class in {"invalid_api_key"} or ec in {"invalid_api_key", "invalid_api_key_provided"}:
        return "auth_failure"
    if failure_class in _MODEL_ACCESS_FAILURE_CLASSES:
        return "model_access_failure"
    if failure_class == "auth_failure":
        if status_code == 403:
            return "permission_failure"
        return "auth_failure"
    if failure_class in {"rate_limit", "server_error", "timeout", "connection_error"}:
        return "transient_upstream_failure"
    return "unknown_failure"


def format_upstream_api_preflight_startup_lines(status: UpstreamApiPreflightStatus | dict[str, Any]) -> list[str]:
    """Developer-facing lines (no secrets)."""
    hc = status.get("health_class", "unknown_failure")
    ok = bool(status.get("ok"))
    inv = bool(status.get("invalidates_upstream_dependent_runs"))
    lines = [
        "=== OPENAI API PREFLIGHT ===",
        f"ok={ok} health_class={hc} invalidates_upstream_dependent_runs={inv}",
        f"checked_at={status.get('checked_at')}",
    ]
    if status.get("status_code") is not None:
        lines.append(f"status_code={status.get('status_code')}")
    if status.get("error_code"):
        lines.append(f"error_code={status.get('error_code')}")
    if status.get("retryable") is not None:
        lines.append(f"retryable={status.get('retryable')}")
    if status.get("message_excerpt"):
        lines.append(f"message_excerpt={status.get('message_excerpt')}")
    if not ok:
        lines.append(
            "MANUAL / gameplay runs that depend on live narration should be treated as INVALID until upstream is healthy."
        )
    lines.append("=== END OPENAI API PREFLIGHT ===")
    return lines


def _default_openai_client_factory(api_key: str) -> Any:
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def run_upstream_api_preflight(
    *,
    api_key: str | None = None,
    model: str | None = None,
    timeout: float = 25.0,
    client_factory: Callable[[str], Any] | None = None,
) -> UpstreamApiPreflightStatus:
    """Perform a minimal ``responses.create`` probe; store and return canonical status."""
    key = (api_key or OPENAI_API_KEY or "").strip()
    mdl = (model or DEFAULT_MODEL_NAME or "").strip()
    checked_at = _utc_checked_at()
    factory = client_factory or _default_openai_client_factory

    # Same message shape as ``call_gpt`` (list of role/content dicts).
    probe_input: list[dict[str, str]] = [
        {"role": "system", "content": "You are an infrastructure health probe. Reply with exactly: OK"},
        {"role": "user", "content": "ping"},
    ]

    try:
        client = factory(key)
        client.responses.create(
            model=mdl,
            input=probe_input,
            max_output_tokens=_clamp_preflight_max_output_tokens(_PREFLIGHT_MAX_OUTPUT_TOKENS),
            temperature=0,
            timeout=timeout,
        )
    except Exception as e:  # noqa: BLE001 - probe must never raise
        st = compute_api_runtime_health_from_exception(e, checked_at=checked_at)
        _set_latest_upstream_api_preflight(st)
        return st

    healthy: UpstreamApiPreflightStatus = {
        "ok": True,
        "health_class": "healthy",
        "retryable": None,
        "status_code": None,
        "error_code": None,
        "message_excerpt": None,
        "checked_at": checked_at,
        "invalidates_upstream_dependent_runs": False,
    }
    _set_latest_upstream_api_preflight(healthy)
    return healthy


# Discoverability aliases (same behavior, canonical storage).
check_openai_api_health = run_upstream_api_preflight
compute_api_runtime_health = compute_api_runtime_health_from_exception
