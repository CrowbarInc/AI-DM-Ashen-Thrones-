"""Process-local provider budget for a bounded live run.

Inactive unless ASHEN_PROVIDER_REQUEST_LIMIT or ASHEN_PROVIDER_USAGE_PATH is set.
Token fields stay null when the provider does not supply them.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any

_LOCK = threading.Lock()
_RECORDS: list[dict[str, Any]] = []
_REQUESTS = 0
_INPUT = 0
_OUTPUT = 0
_STOPPED = False
_STOP_REASON = ""


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def provider_calls_disabled() -> bool:
    return _truthy("ASHEN_DISABLE_PROVIDER_CALLS")


def provider_retries_disabled() -> bool:
    return _truthy("ASHEN_DISABLE_PROVIDER_RETRIES")


def accounting_active() -> bool:
    return bool(os.environ.get("ASHEN_PROVIDER_REQUEST_LIMIT", "").strip()) or bool(
        os.environ.get("ASHEN_PROVIDER_USAGE_PATH", "").strip()
    )


def limits() -> tuple[int, int, int, int] | None:
    raw = os.environ.get("ASHEN_PROVIDER_REQUEST_LIMIT", "").strip()
    if not raw:
        return None
    return (
        int(raw),
        int(os.environ.get("ASHEN_PROVIDER_INPUT_TOKEN_LIMIT", "8000")),
        int(os.environ.get("ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT", "2000")),
        int(os.environ.get("ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT", "10000")),
    )


def snapshot() -> dict[str, Any]:
    with _LOCK:
        return {
            "requests": _REQUESTS,
            "input_tokens": _INPUT,
            "output_tokens": _OUTPUT,
            "total_tokens": _INPUT + _OUTPUT,
            "stopped": _STOPPED,
            "stop_reason": _STOP_REASON,
            "records": list(_RECORDS),
        }


def _append(record: dict[str, Any]) -> None:
    path = os.environ.get("ASHEN_PROVIDER_USAGE_PATH", "").strip()
    if not path:
        return
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def begin_request(*, purpose: str, estimated_input: int, max_output: int) -> str:
    """Return a refusal reason, or an empty string when the request may be sent."""
    global _STOPPED, _STOP_REASON
    if not accounting_active():
        return ""
    estimated_input = max(1, int(estimated_input))
    max_output = max(1, int(max_output))
    with _LOCK:
        if _STOPPED:
            return _STOP_REASON or "provider budget stopped"
        ceiling = limits()
        if ceiling is None:
            return ""
        request_limit, input_limit, output_limit, total_limit = ceiling
        if _REQUESTS + 1 > request_limit:
            return "request ceiling"
        if _INPUT + estimated_input > input_limit:
            return "input-token ceiling"
        if _OUTPUT + max_output > output_limit:
            return "output-token ceiling"
        if _INPUT + _OUTPUT + estimated_input + max_output > total_limit:
            return "total-token ceiling"
    return ""


def finish_request(record: dict[str, Any]) -> dict[str, Any]:
    """Record one completed or failed provider attempt. Does not invent token counts."""
    global _REQUESTS, _INPUT, _OUTPUT, _STOPPED, _STOP_REASON
    incoming = record.get("input_tokens")
    outgoing = record.get("output_tokens")
    total = record.get("total_tokens")
    sent = bool(record.get("sent"))
    with _LOCK:
        if sent:
            _REQUESTS += 1
        consistent = (
            isinstance(incoming, int)
            and isinstance(outgoing, int)
            and isinstance(total, int)
            and total == incoming + outgoing
        )
        stored = dict(record)
        stored["usage_consistent"] = consistent
        if sent and not consistent:
            _STOPPED = True
            _STOP_REASON = _STOP_REASON or "provider usage accounting unavailable"
            stored["accounting"] = "unavailable"
        elif consistent:
            _INPUT += int(incoming)
            _OUTPUT += int(outgoing)
            ceiling = limits()
            if ceiling is not None:
                request_limit, input_limit, output_limit, total_limit = ceiling
                if (
                    _REQUESTS > request_limit
                    or _INPUT > input_limit
                    or _OUTPUT > output_limit
                    or _INPUT + _OUTPUT > total_limit
                ):
                    _STOPPED = True
                    _STOP_REASON = _STOP_REASON or "provider budget exceeded after a completed request"
        if record.get("model_mismatch"):
            _STOPPED = True
            _STOP_REASON = _STOP_REASON or "provider returned a different model"
        _RECORDS.append(stored)
        _append(stored)
        return stored
