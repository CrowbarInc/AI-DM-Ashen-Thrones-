"""Single process-local provider admission and durable attempt ledger.

ATGB-03B-1 reserves application request allowance before dispatch. SDK transport
retries remain part of one application request. No request content is recorded.
"""
from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
import json
import os
import threading
import time
import uuid
from typing import Any

ACCOUNTING_VERSION = "ATGB-03B-1"
_LOCK = threading.Lock()
_RECORDS: list[dict[str, Any]] = []
_EVENTS: list[dict[str, Any]] = []
_ATTEMPTS: dict[str, "RequestAttempt"] = {}
_REQUESTS = 0
_INPUT = 0
_OUTPUT = 0
_RESERVED_INPUT = 0
_RESERVED_OUTPUT = 0
_USAGE_KNOWN = True
_STOPPED = False
_STOP_REASON = ""
_INITIALIZED = False
_LEDGER_PATH: str | None = None
_RUN_ID = uuid.uuid4().hex
_LEGACY: ContextVar[Any] = ContextVar("provider_legacy_attempt", default=None)
_OPENING_DIAGNOSTIC: ContextVar[Any] = ContextVar("provider_opening_diagnostic", default=None)


def generation_diagnostics_enabled() -> bool:
    return _truthy("ASHEN_GENERATION_DIAGNOSTICS")


def record_generation_diagnostic(fields: dict[str, Any], attempt=None) -> None:
    """Structural observations only, in the existing ledger; never request/response text.

    Failure stops future admissions, but cannot turn a committed gameplay result
    into a failed opening. Callers supply explicitly constructed, content-free fields.
    """
    if not generation_diagnostics_enabled() or not accounting_active():
        return
    with _LOCK:
        try:
            _initialize_locked()
            scope = _OPENING_DIAGNOSTIC.get()
            if scope is not None and fields.get("stage") == "provider_response":
                scope.update(provider_attempt_id=attempt.attempt_id if attempt else None,
                             provider_status=fields.get("provider_status"),
                             structured_validation_result=fields.get("structured_validation_result"))
                scope.update({key: fields.get(key) for key in (
                    "narration_present", "narration_length", "player_facing_text_present",
                    "player_facing_text_length", "declarations_present", "declaration_count")})
            _append({"event": "generation_diagnostic", "version": ACCOUNTING_VERSION,
                     "run_id": _RUN_ID, "time": _now(),
                     "attempt_id": attempt.attempt_id if attempt else None,
                     "opening_attempt_id": scope["id"] if scope else None, **fields})
        except (OSError, ValueError, TypeError, ProviderAccountingError):
            _stop("generation diagnostic ledger write failed")


def begin_opening_diagnostic():
    if not generation_diagnostics_enabled():
        return None
    return _OPENING_DIAGNOSTIC.set({"id": uuid.uuid4().hex})


def observe_opening_semantics(fields: dict[str, Any]) -> None:
    """Content-free observations from the existing semantic decision boundary."""
    scope = _OPENING_DIAGNOSTIC.get()
    if scope is not None:
        scope.update(fields)
        record_generation_diagnostic({"stage": "opening_semantics",
            "logical_operation": "scene_opening", "requested_response_type": "scene_opening",
            **fields})


def capture_opening_response(text: str, attempt=None) -> None:
    """Explicit controlled-playtest evidence only; never prompts or SDK objects.

    A separate opt-in is required in addition to diagnostics, accounting, isolated
    storage and both retry controls. At most six 64-KiB artifacts per scope.
    """
    from pathlib import Path

    scope = _OPENING_DIAGNOSTIC.get()
    if not (scope is not None and generation_diagnostics_enabled() and accounting_active()
            and _truthy("ASHEN_OPENING_RESPONSE_CAPTURE")
            and _truthy("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES")
            and _truthy("ASHEN_DISABLE_PROVIDER_RETRIES")):
        return
    result = "capture_failed"
    try:
        configured = os.environ.get("ASHEN_DATA_DIR", "")
        if not configured or not Path(configured).is_absolute():
            raise ValueError("isolated data required")
        data = Path(configured).resolve(strict=True)
        from game.storage import DATA_DIR
        if data != Path(DATA_DIR).resolve():
            raise ValueError("capture must use active storage")
        if data == (Path(__file__).resolve().parents[1] / "data").resolve():
            raise ValueError("normal data forbidden")
        count = scope.get("capture_count", 0)
        if count >= 6:
            raise ValueError("capture count bound")
        scope["capture_count"] = count + 1
        # Parse the original string, independently of the normalized parser output.
        import re
        raw = text.strip()
        fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
        value = json.loads(fence.group(1).strip() if fence else raw)
        artifact = {"sensitive_game_content": True, "opening_attempt_id": scope["id"],
                    "provider_attempt_id": attempt.attempt_id if attempt else None,
                    "parsed_response": value, "truncated": False}
        encoded = json.dumps(artifact, ensure_ascii=True).encode("utf-8")
        if len(encoded) > 65536:
            artifact.pop("parsed_response")
            artifact.update(truncated=True, original_serialized_bytes=len(encoded),
                            response_prefix=json.dumps(value, ensure_ascii=True)[:8000])
            encoded = json.dumps(artifact, ensure_ascii=True).encode("utf-8")
        folder = data.parent / "opening_response_evidence"
        if folder.resolve().parent != data.parent:
            raise ValueError("capture directory escapes isolated playtest")
        folder.mkdir(exist_ok=True)
        # Exclusive files prevent accidental replacement; paths never use model data.
        with (folder / f"{scope['id']}-{count + 1}.json").open("xb") as handle:
            handle.write(encoded)
        result = "captured"
    except (OSError, ValueError, TypeError, RecursionError):
        pass  # Optional evidence must not change acceptance or dispatch behavior.
    record_generation_diagnostic({"stage": "opening_response_capture",
        "logical_operation": "scene_opening", "classification": result,
        "sensitive_game_content": True}, attempt)


def observe_opening_validation(*, rejection: str | None, recovery: str | None) -> None:
    scope = _OPENING_DIAGNOSTIC.get()
    if scope is not None:
        scope.update(rejection_reason=rejection, recovery_classification=recovery,
                     final_validation_passed=rejection is None)
        record_generation_diagnostic({"stage": "opening_validation",
            "logical_operation": "scene_opening", "requested_response_type": "scene_opening",
            "classification_source": "game.api._opening_response_rejection",
            "classification_reason": rejection or "opening_contract_passed",
            "opening_accepted": rejection is None,
            "semantic_classification": "rejected" if rejection else "accepted"})


def end_opening_diagnostic(token, *, committed: bool, tracked: bool) -> None:
    if token is None:
        return
    try:
        scope = _OPENING_DIAGNOSTIC.get()
        if tracked or scope.get("rejection_reason"):
            record_generation_diagnostic({
                "stage": "opening_outcome", "logical_operation": "scene_opening",
                "requested_response_type": "scene_opening",
                "opening_accepted": committed, "gameplay_committed": committed,
                "classification": "accepted_structured_opening" if committed else "opening_rejected",
                **{key: scope.get(key) for key in ("provider_attempt_id", "provider_status",
                    "structured_validation_result", "semantic_classification", "classification_source",
                    "classification_reason", "semantic_reasons", "narration_present", "narration_length",
                    "player_facing_text_present", "player_facing_text_length", "declarations_present", "declaration_count")},
                "final_validation_passed": scope.get("final_validation_passed"),
                "rejection_stage": None if committed else "game.api._opening_response_rejection",
                "nonresolution_origin": scope.get("nonresolution_origin") or (
                    "model" if scope.get("rejection_reason") == "generic_information_request_fallback"
                    and scope.get("recovery_classification") == "initial_generation" else None),
                "rejection_reason": scope.get("rejection_reason") or (None if committed else "pipeline_exception"),
                "recovery_classification": scope.get("recovery_classification"),
            })
    finally:
        _OPENING_DIAGNOSTIC.reset(token)

class ProviderAccountingError(RuntimeError):
    """No external dispatch is safe after an accounting failure."""

class ProviderBudgetRefused(ProviderAccountingError):
    pass


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def provider_calls_disabled() -> bool:
    return _truthy("ASHEN_DISABLE_PROVIDER_CALLS")


def provider_retries_disabled() -> bool:
    return _truthy("ASHEN_DISABLE_PROVIDER_RETRIES")


def sdk_retry_options() -> dict[str, int]:
    """Opt-in constructor options; leave the SDK's ordinary default untouched."""
    return {"max_retries": 0} if _truthy("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES") else {}


def playtest_stop_reason() -> str:
    """Non-reserving submission gate, supplemental to atomic request admission."""
    if not sdk_retry_options() or not accounting_active():
        return ""
    with _LOCK:
        ceiling = limits()
        if _STOPPED:
            return _STOP_REASON
        return "request ceiling" if ceiling and _REQUESTS >= ceiling[0] else ""


PLAYTEST_STOP_MESSAGE = "The controlled playtest request limit has been reached. Stop and export diagnostics; do not restart to continue this session."


def accounting_active() -> bool:
    return bool(os.environ.get("ASHEN_PROVIDER_REQUEST_LIMIT", "").strip() or
                os.environ.get("ASHEN_PROVIDER_USAGE_PATH", "").strip())


def limits() -> tuple[int, int, int, int] | None:
    raw = os.environ.get("ASHEN_PROVIDER_REQUEST_LIMIT", "").strip()
    if not raw:
        return None
    return (int(raw), int(os.environ.get("ASHEN_PROVIDER_INPUT_TOKEN_LIMIT", "8000")),
            int(os.environ.get("ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT", "2000")),
            int(os.environ.get("ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT", "10000")))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stop(reason: str) -> None:
    global _STOPPED, _STOP_REASON
    _STOPPED = True
    _STOP_REASON = _STOP_REASON or reason


def _append(record: dict[str, Any]) -> None:
    """Caller holds admission lock. fsync must succeed before dispatch."""
    if not _LEDGER_PATH:
        raise ProviderAccountingError("durable provider ledger path required")
    with open(_LEDGER_PATH, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    _EVENTS.append(dict(record))


def _initialize_locked() -> None:
    global _INITIALIZED, _LEDGER_PATH
    path = os.environ.get("ASHEN_PROVIDER_USAGE_PATH", "").strip()
    if _INITIALIZED:
        if path != _LEDGER_PATH:
            raise ProviderAccountingError("provider ledger changed within process")
        return
    if not path:
        raise ProviderAccountingError("durable provider ledger path required")
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    # Exclusive ownership: never reset a process counter over a prior ledger.
    with open(path, "x", encoding="utf-8"):
        pass
    _LEDGER_PATH = path
    _append({"event": "initialized", "version": ACCOUNTING_VERSION, "run_id": _RUN_ID, "time": _now()})
    _INITIALIZED = True


def initialize_accounting() -> None:
    if accounting_active():
        with _LOCK:
            try:
                _initialize_locked()
            except (OSError, ProviderAccountingError) as exc:
                _stop("provider ledger initialization failed")
                raise ProviderAccountingError(_STOP_REASON) from exc


def snapshot() -> dict[str, Any]:
    with _LOCK:
        usage_known = _USAGE_KNOWN and not any(a.dispatched and a.completed is None for a in _ATTEMPTS.values())
        return {"version": ACCOUNTING_VERSION, "run_id": _RUN_ID, "requests": _REQUESTS,
                "request_upper_bound": _REQUESTS if _INITIALIZED else None,
                "dispatched_requests": sum(a.dispatched for a in _ATTEMPTS.values()),
                "pending_requests": sum(a.completed is None for a in _ATTEMPTS.values()),
                "input_tokens": _INPUT if usage_known else None,
                "output_tokens": _OUTPUT if usage_known else None,
                "total_tokens": _INPUT + _OUTPUT if usage_known else None,
                "stopped": _STOPPED, "stop_reason": _STOP_REASON,
                "records": [dict(r) for r in _RECORDS], "events": [dict(e) for e in _EVENTS]}


class RequestAttempt:
    def __init__(self, *, purpose: str, owner: str, model: str | None,
                 estimated_input: int, max_output: int, attempt_id: str | None = None):
        self.attempt_id = attempt_id or uuid.uuid4().hex
        self.purpose, self.owner, self.model = purpose, owner, model
        self.estimated_input, self.max_output = estimated_input, max_output
        self.active = accounting_active()
        self.refusal = ""
        self.admitted_at: str | None = None
        self.dispatched = False
        self.dispatch_started = 0.0
        self.completed: dict[str, Any] | None = None
        self.sequence: int | None = None

    def dispatch(self, invoke, **kwargs):
        """Exactly one dispatch; durable admission/dispatch markers precede it."""
        if self.refusal:
            raise ProviderBudgetRefused(self.refusal)
        with _LOCK:
            if provider_calls_disabled() or accounting_active() != self.active:
                raise ProviderAccountingError("provider accounting configuration changed before dispatch")
            if self.dispatched or self.completed is not None:
                raise ProviderAccountingError("duplicate request dispatch")
            if self.active:
                if _STOPPED:
                    raise ProviderAccountingError(_STOP_REASON)
                if os.environ.get("ASHEN_PROVIDER_USAGE_PATH", "").strip() != _LEDGER_PATH:
                    _stop("provider ledger changed within process")
                    raise ProviderAccountingError(_STOP_REASON)
                try:
                    _append(self._event("dispatch_attempted"))
                except OSError as exc:
                    _stop("provider dispatch ledger write failed")
                    raise ProviderAccountingError(_STOP_REASON) from exc
            self.dispatched = True
            self.dispatch_started = time.perf_counter()
        try:
            response = invoke(**kwargs)
        except BaseException as exc:
            self.finish({"error": type(exc).__name__, "completion_status": "interrupted" if not isinstance(exc, Exception) else "failed"})
            raise
        # Account before any caller parsing can raise or silently return early.
        try:
            usage = getattr(response, "usage", None)
            record = {key: getattr(usage, key, None) for key in ("input_tokens", "output_tokens", "total_tokens")}
            record.update(request_id=getattr(response, "id", None), model=getattr(response, "model", None))
        except Exception:
            record = {"error": "PartialProviderResponse"}
        self.finish(record)
        return response

    def _event(self, event: str) -> dict[str, Any]:
        record = {"event": event, "version": ACCOUNTING_VERSION, "run_id": _RUN_ID,
                "attempt_id": self.attempt_id, "purpose": self.purpose, "owner": self.owner,
                "configured_model": self.model, "admitted_at": self.admitted_at, "time": _now()}
        if sdk_retry_options():
            ceiling = limits()
            record.update(sequence=self.sequence, admission="rejected" if self.refusal else "admitted",
                          budget_remaining=max(0, ceiling[0] - _REQUESTS - (event == "admitted")) if ceiling else None,
                          sdk_retries=0, host_retries="disabled" if provider_retries_disabled() else "unavailable")
        return record

    def finish(self, record: dict[str, Any]) -> dict[str, Any]:
        global _INPUT, _OUTPUT, _RESERVED_INPUT, _RESERVED_OUTPUT, _USAGE_KNOWN
        with _LOCK:
            if self.completed is not None:
                if record.get("model_mismatch") and self.active:
                    _stop("provider returned a different model")
                return dict(self.completed)  # Multiple observers, one completion.
            incoming, outgoing, total = (record.get(k) for k in ("input_tokens", "output_tokens", "total_tokens"))
            consistent = all(type(v) is int and v >= 0 for v in (incoming, outgoing, total)) and total == incoming + outgoing
            if not consistent:
                incoming = outgoing = total = None
            stored = {**self._event("completed"), "sent": self.dispatched,
                      "request_id": record.get("request_id") if isinstance(record.get("request_id"), str) else None,
                      "model": record.get("model") if isinstance(record.get("model"), str) else self.model,
                      "input_tokens": incoming, "output_tokens": outgoing, "total_tokens": total,
                      "usage_consistent": consistent, "refusal": self.refusal or None,
                      "completion_status": record.get("completion_status") or ("completed" if self.dispatched else "not_dispatched"),
                      "dispatch_attempted": self.dispatched,
                      "latency_ms": round((time.perf_counter() - self.dispatch_started) * 1000, 3) if self.dispatched else None}
            if record.get("error"):
                # Never persist provider exception messages or request content.
                stored["error"] = "provider_error"
            if record.get("model_mismatch"):
                stored["model_mismatch"] = True
            # A failed durable completion must not be applied twice if an owner
            # observes the accounting exception and calls finish again.
            self.completed = stored
            if self.active and not self.refusal:
                _RESERVED_INPUT -= self.estimated_input
                _RESERVED_OUTPUT -= self.max_output
                if self.dispatched and not consistent:
                    _USAGE_KNOWN = False
                    _stop("provider usage accounting unavailable")
                elif consistent:
                    _INPUT += incoming
                    _OUTPUT += outgoing
                    ceiling = limits()
                    if ceiling and (_INPUT > ceiling[1] or _OUTPUT > ceiling[2] or _INPUT + _OUTPUT > ceiling[3]):
                        _stop("provider budget exceeded after a completed request")
                if record.get("model_mismatch"):
                    _stop("provider returned a different model")
                try:
                    _append(stored)
                except (OSError, ValueError, TypeError) as exc:
                    _stop("provider completion ledger write failed")
                    raise ProviderAccountingError(_STOP_REASON) from exc
                _RECORDS.append(stored)
            return dict(stored)


def admit_request(*, purpose: str, owner: str, estimated_input: int, max_output: int,
                  model: str | None = None, attempt_id: str | None = None) -> RequestAttempt:
    global _REQUESTS, _RESERVED_INPUT, _RESERVED_OUTPUT
    attempt = RequestAttempt(purpose=purpose, owner=owner, model=model,
                             estimated_input=max(1, int(estimated_input)), max_output=max(1, int(max_output)), attempt_id=attempt_id)
    with _LOCK:
        if provider_calls_disabled():
            attempt.refusal = "provider calls disabled"
        elif attempt.active:
            try:
                _initialize_locked()
                ceiling = limits()
                if _STOPPED:
                    attempt.refusal = _STOP_REASON or "provider budget stopped"
                elif attempt.attempt_id in _ATTEMPTS:
                    attempt.refusal = "duplicate request identity"
                elif ceiling:
                    req, inp, out, total = ceiling
                    if _REQUESTS >= req:
                        attempt.refusal = "request ceiling"
                    elif _INPUT + _RESERVED_INPUT + attempt.estimated_input > inp:
                        attempt.refusal = "input-token ceiling"
                    elif _OUTPUT + _RESERVED_OUTPUT + attempt.max_output > out:
                        attempt.refusal = "output-token ceiling"
                    elif _INPUT + _OUTPUT + _RESERVED_INPUT + _RESERVED_OUTPUT + attempt.estimated_input + attempt.max_output > total:
                        attempt.refusal = "total-token ceiling"
                if not attempt.refusal:
                    attempt.admitted_at = _now()
                    attempt.sequence = _REQUESTS + 1
                    _append(attempt._event("admitted"))
                    _REQUESTS += 1
                    _RESERVED_INPUT += attempt.estimated_input
                    _RESERVED_OUTPUT += attempt.max_output
                    _ATTEMPTS[attempt.attempt_id] = attempt
            except (OSError, ValueError, ProviderAccountingError):
                _stop("provider admission accounting unavailable")
                attempt.refusal = _STOP_REASON
        if attempt.refusal and attempt.active and sdk_retry_options() and _INITIALIZED:
            try:
                _append({**attempt._event("rejected"), "refusal": attempt.refusal, "sent": False,
                         "input_tokens": None, "output_tokens": None, "total_tokens": None})
            except OSError:
                _stop("provider rejection ledger write failed")
    return attempt


def begin_request(*, purpose: str, estimated_input: int, max_output: int) -> str:
    """Legacy admission API; now reserves allowance before returning success."""
    attempt = admit_request(purpose=purpose, owner="legacy.begin_request", estimated_input=estimated_input, max_output=max_output)
    _LEGACY.set(attempt)
    return attempt.refusal


def finish_request(record: dict[str, Any]) -> dict[str, Any]:
    """Compatibility observer. New dispatch owners use explicit attempt objects."""
    attempt = _LEGACY.get()
    if attempt is None:
        raise ProviderAccountingError("completion without admission identity")
    return attempt.finish(record)
