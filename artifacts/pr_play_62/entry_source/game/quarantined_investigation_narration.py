"""Opt-in quarantine for investigation narration. Not a player-facing path.

The gameplay pipeline calls :func:`observe_completed_investigation` only when
``ASHEN_QUARANTINE_INVESTIGATION_NARRATION`` is exactly ``1``. By default the
hook replays a saved prelude or a deterministic stub through the existing
anchored preview. It does not retry, and it does not write campaign state.

``ASHEN_QUARANTINE_NARRATION_LIVE`` must also be exactly ``1`` before the hook
asks the existing expression adapter for one prelude. That call happens after
authoritative resolution, sees only the detached projection, and its prose
stays in the quarantine record. A fault injection suppresses the live call.

``run_quarantined_hook`` accepts only the detached projection built here.
Scene catalogs, world objects, and resolver metadata stay outside that call.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

from game import anchored_investigation_narration as anchored

GATE_ENV = "ASHEN_QUARANTINE_INVESTIGATION_NARRATION"
SAMPLE_ENV = "ASHEN_QUARANTINE_NARRATION_SAMPLE"
FAULT_ENV = "ASHEN_QUARANTINE_NARRATION_FAULT"
EVIDENCE_ENV = "ASHEN_QUARANTINE_NARRATION_DIR"
LABEL_ENV = "ASHEN_QUARANTINE_NARRATION_LABEL"
LIVE_ENV = "ASHEN_QUARANTINE_NARRATION_LIVE"
MODE_ENV = "ASHEN_QUARANTINE_NARRATION_MODE"
PUBLICATION_ENV = "ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION"
PUBLICATION_SESSION_ENV = "ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION_SESSION"

MAX_LIVE_REQUESTS = 6
MAX_LIVE_OUTPUT_TOKENS = 1000
MAX_LIVE_TOTAL_TOKENS = 10000
LIVE_SYSTEM_PROMPT = (
    "The investigation is already complete. Its mechanical result is authoritative. "
    "Write one descriptive prelude of about 20 to 60 words, and end on a complete sentence. "
    "You are writing prose only. Do not decide the outcome. "
    "Do not invent rewards, possessions, currency, health, conditions, travel, quests, or any other mechanical change. "
    "Do not invent definitive conclusions, culprits, counts, links, or destinations. "
    "Preserve uncertainty that the result leaves open. "
    "Do not reveal information that is absent from the supplied context. "
    "Harmless incidental atmosphere is allowed and creates no new facts or mechanics. "
    "Avoid generic filler. Do not repeat the authorized discovery; the engine appends that sentence separately."
)

INVESTIGATION_KINDS = {"investigate", "observe", "discover_clue", "already_searched"}
SAVED_SAMPLE_IDS = {"A1", "A2", "B1", "B2"}
STUB_PRELUDE = "You take a moment to look more closely."
UNSAFE_PRELUDE = "The hidden passage opens before you."

_IN_HOOK: ContextVar[bool] = ContextVar("quarantine_investigation_hook", default=False)
_MEMORY: list[dict] = []
_SAVED: list | None = None
_SEQUENCE = 0
_LIVE_SENT = 0
_LIVE_TOKENS = 0
_LIVE_STOP = ""


def quarantine_enabled() -> bool:
    return os.environ.get(GATE_ENV, "").strip() == "1"


def live_provider_enabled() -> bool:
    """Second opt-in. The quarantine gate alone still replays saved prose."""
    return os.environ.get(LIVE_ENV, "").strip() == "1"


def reset_live_budget() -> None:
    """Test isolation. The experiment process keeps the counter across scenarios."""
    global _LIVE_SENT, _LIVE_TOKENS, _LIVE_STOP
    _LIVE_SENT = 0
    _LIVE_TOKENS = 0
    _LIVE_STOP = ""


def hook_is_active() -> bool:
    return bool(_IN_HOOK.get())


def evidence_records() -> list[dict]:
    return list(_MEMORY)


def clear_evidence() -> None:
    _MEMORY.clear()


def _elapsed(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def _saved_path() -> Path:
    return Path(__file__).resolve().parents[1] / "artifacts" / "pr_play_50" / "requests.json"


def _saved_records() -> list:
    global _SAVED
    if _SAVED is None:
        _SAVED = json.loads(_saved_path().read_text(encoding="utf-8"))
    return _SAVED


def _raw_provider_text(record: dict) -> tuple[str, str | None, bool]:
    """Return the provider message text, the stored extraction, and whether they match."""
    texts: list[str] = []
    raw = record.get("raw_provider_response") if isinstance(record.get("raw_provider_response"), dict) else {}
    response = raw.get("response") if isinstance(raw.get("response"), dict) else {}
    output = response.get("output") if isinstance(response.get("output"), list) else []
    for item in output:
        if not isinstance(item, dict):
            continue
        for part in item.get("content") or []:
            if isinstance(part, dict) and part.get("type") == "output_text" and isinstance(part.get("text"), str):
                texts.append(part["text"])
    raw_text = texts[0] if texts else ""
    extracted = record.get("extracted_narration_text") if isinstance(record.get("extracted_narration_text"), str) else None
    return raw_text, extracted, extracted == raw_text


def _sample() -> str:
    return os.environ.get(SAMPLE_ENV, "").strip() or "stub"


def _fault() -> str:
    return os.environ.get(FAULT_ENV, "").strip()


def _strings(values) -> list[str]:
    found: list[str] = []
    for value in values or ():
        if isinstance(value, str):
            text = value.strip()
            if text and text not in found:
                found.append(text)
    return found


def build_hook_input(*, resolution, scene, known_clue_texts, player_text: str) -> dict:
    """Detach the fields the anchored preview is allowed to see.

    This is the orchestration boundary. ``run_quarantined_hook`` does not receive
    ``scene`` or ``resolution`` objects.
    """
    if not isinstance(resolution, dict):
        return {"eligible": False, "reason": "missing_resolution", "player_text": player_text}
    kind = str(resolution.get("kind") or "").strip().lower()
    if kind not in INVESTIGATION_KINDS:
        return {"eligible": False, "reason": "not_investigation", "kind": kind, "player_text": player_text}
    body = scene.get("scene") if isinstance(scene, dict) and isinstance(scene.get("scene"), dict) else {}
    changes = resolution.get("state_changes") if isinstance(resolution.get("state_changes"), dict) else {}
    kept_changes = {}
    if changes.get("already_searched") is True:
        kept_changes["already_searched"] = True
    if changes.get("skill_check_failed") is True:
        kept_changes["skill_check_failed"] = True
    clues = _strings(resolution.get("discovered_clues"))
    clue_text = resolution.get("clue_text") if isinstance(resolution.get("clue_text"), str) else ""
    stripped = {
        "kind": kind,
        "success": resolution.get("success") if isinstance(resolution.get("success"), bool) else None,
        "action_id": resolution.get("action_id") if isinstance(resolution.get("action_id"), str) else None,
        "interactable_id": resolution.get("interactable_id") if isinstance(resolution.get("interactable_id"), str) else None,
        "discovered_clues": clues,
        "clue_text": clue_text.strip(),
        "state_changes": kept_changes,
    }
    payload = {
        "scene": {
            "public": {
                "location": body.get("location") if isinstance(body.get("location"), str) else None,
                "summary": body.get("summary") if isinstance(body.get("summary"), str) else None,
                "visible_facts": _strings(body.get("visible_facts")),
            },
            "discovered_clues": [{"text": text} for text in _strings(known_clue_texts)],
        }
    }
    if os.environ.get(MODE_ENV, "").strip() == "integrated":
        # Reject effects before the legacy hook drops unsupported effect fields.
        # This experiment supports disclosure-only investigations.
        anchored.authorize_anchored_investigation(resolution, payload)
    detached = json.loads(json.dumps({
        "eligible": True,
        "player_text": player_text,
        "target_id": stripped.get("interactable_id") or stripped.get("action_id"),
        "resolution": stripped,
        "narration_payload": payload,
    }))
    return detached


class _Replay:
    def __init__(self, value, fault: str):
        self.value = value
        self.fault = fault
        self.request = None
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        self.request = json.loads(json.dumps(request))
        if self.fault == "timeout":
            raise TimeoutError("simulated_experimental_hook_timeout")
        if self.fault == "provider_error":
            raise RuntimeError("simulated_provider_error")
        if self.calls != 1:
            raise RuntimeError("automatic_retry_forbidden")
        return self.value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _restore_env(saved: dict[str, str | None]) -> None:
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _live_refusal(diagnostic: str) -> dict:
    return {"admit": False, "diagnostic": diagnostic, "sent": False, "retry_count": 0}


def _live_budget(estimated_input: int, limits=None) -> dict:
    """Refuse before a call once the experiment ceilings are already spent."""
    global _LIVE_STOP
    request_limit, output_limit, total_limit = limits or (MAX_LIVE_REQUESTS, MAX_LIVE_OUTPUT_TOKENS, MAX_LIVE_TOTAL_TOKENS)
    if _LIVE_STOP:
        return _live_refusal("provider_stopped")
    if _LIVE_SENT >= request_limit:
        return _live_refusal("experiment_request_ceiling")
    if _LIVE_TOKENS >= total_limit:
        _LIVE_STOP = "experiment_token_ceiling"
        return _live_refusal("experiment_token_ceiling")
    from game.expressive_dialogue import _OUTPUT_CAP

    if _OUTPUT_CAP > output_limit:
        return _live_refusal("output_cap_exceeds_experiment")
    from game.provider_budget import accounting_active, snapshot

    if accounting_active():
        usage = snapshot()
        if usage.get("stopped"):
            _LIVE_STOP = str(usage.get("stop_reason") or "provider_budget_stopped")
            return _live_refusal("provider_stopped")
        total = usage.get("total_tokens")
        if isinstance(total, int) and total >= total_limit:
            _LIVE_STOP = "experiment_token_ceiling"
            return _live_refusal("experiment_token_ceiling")
        reserved = estimated_input + int(_OUTPUT_CAP)
        if isinstance(total, int) and total + reserved > total_limit:
            _LIVE_STOP = "experiment_token_ceiling"
            return _live_refusal("experiment_token_ceiling")
    return {"admit": True, "diagnostic": None, "max_output_tokens": int(_OUTPUT_CAP)}


class _LivePrelude:
    """One expression-adapter call. The preview supplies only the allowlisted request."""

    system_prompt = LIVE_SYSTEM_PROMPT
    limits = (MAX_LIVE_REQUESTS, MAX_LIVE_OUTPUT_TOKENS, MAX_LIVE_TOTAL_TOKENS)

    def user_payload(self):
        return {
            "player_action": self.player_text,
            "requested_prelude_length": "about 20-60 words",
            "authorized_narration_projection": self.request,
        }

    def __init__(self, player_text: str):
        self.player_text = player_text
        self.calls = 0
        self.request = None
        self.provider_user_message = None
        self.raw_text = None
        self.adapter_result = None
        self.diagnostic = None
        self.sent = False
        self.started_at = None
        self.completed_at = None
        self.outer_ms = None

    def generate(self, request):
        global _LIVE_SENT, _LIVE_TOKENS, _LIVE_STOP
        self.calls += 1
        self.request = json.loads(json.dumps(request))
        if self.calls != 1:
            self.diagnostic = "automatic_retry_forbidden"
            raise RuntimeError("automatic_retry_forbidden")
        user = self.user_payload()
        message = json.dumps(user, ensure_ascii=False)
        self.provider_user_message = message
        decision = _live_budget(max(1, len(self.system_prompt + message) // 4), self.limits)
        if not decision["admit"]:
            self.diagnostic = decision["diagnostic"]
            self.adapter_result = {"ok": False, "sent": False, "reason": decision["diagnostic"]}
            raise RuntimeError(decision["diagnostic"])
        saved = {
            "ASHEN_DISABLE_PROVIDER_CALLS": os.environ.get("ASHEN_DISABLE_PROVIDER_CALLS"),
            "ASHEN_PLAYTEST_DISABLE_SDK_RETRIES": os.environ.get("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"),
            "ASHEN_DISABLE_PROVIDER_RETRIES": os.environ.get("ASHEN_DISABLE_PROVIDER_RETRIES"),
        }
        # Player-facing narration has already been built. This call is quarantined,
        # uses the existing adapter, and does not keep the SDK's default retries.
        os.environ.pop("ASHEN_DISABLE_PROVIDER_CALLS", None)
        os.environ["ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"] = "1"
        os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
        self.started_at = _utc_now()
        started = time.perf_counter()
        try:
            from game.expressive_dialogue import request_expression

            result = request_expression({"prompt": {"system": self.system_prompt, "user": message}})
        finally:
            self.completed_at = _utc_now()
            self.outer_ms = _elapsed(started)
            _restore_env(saved)
        if not isinstance(result, dict):
            self.diagnostic = "provider_result_unusable"
            raise RuntimeError("provider_result_unusable")
        self.adapter_result = {
            key: result.get(key)
            for key in ("ok", "sent", "reason", "error", "latency_ms", "model", "usage")
        }
        self.sent = bool(result.get("sent"))
        if self.sent:
            _LIVE_SENT += 1
        usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
        tokens_known = all(isinstance(usage.get(key), int) for key in ("input_tokens", "output_tokens", "total_tokens"))
        if self.sent and not tokens_known:
            _LIVE_STOP = "usage_unknown"
        elif tokens_known:
            _LIVE_TOKENS += int(usage["total_tokens"])
            outgoing = usage.get("output_tokens")
            if isinstance(outgoing, int) and outgoing > self.limits[1]:
                _LIVE_STOP = "output_cap_exceeds_experiment"
            if _LIVE_TOKENS >= self.limits[2]:
                _LIVE_STOP = "experiment_token_ceiling"
        error_name = str(result.get("error") or "")
        if error_name in {"AuthenticationError", "PermissionDeniedError", "APIConnectionError", "APITimeoutError"}:
            _LIVE_STOP = error_name
        if not result.get("ok"):
            self.diagnostic = error_name or str(result.get("reason") or "provider_failed")
            if error_name in {"APITimeoutError", "TimeoutError"} or "timeout" in self.diagnostic.casefold():
                raise TimeoutError(self.diagnostic)
            raise RuntimeError(self.diagnostic)
        self.raw_text = result.get("text") if isinstance(result.get("text"), str) else ""
        self.diagnostic = "provider_text_received"
        return self.raw_text


def _live_metadata(generator: _LivePrelude) -> dict:
    result = generator.adapter_result if isinstance(generator.adapter_result, dict) else {}
    usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}

    def token(name: str):
        value = usage.get(name)
        return value if isinstance(value, int) else None

    error = result.get("error") or result.get("reason")
    return {
        "enabled": True,
        "provider": "openai",
        "adapter": "game.expressive_dialogue.request_expression",
        "purpose": "expression",
        "configured_output_cap": _configured_output_cap(),
        "experiment_output_token_ceiling": generator.limits[1],
        "model": result.get("model") or usage.get("model"),
        "request_started_at": generator.started_at,
        "request_completed_at": generator.completed_at,
        "provider_latency_ms": result.get("latency_ms") if isinstance(result.get("latency_ms"), (int, float)) else None,
        "outer_latency_ms": generator.outer_ms,
        "input_tokens": token("input_tokens"),
        "output_tokens": token("output_tokens"),
        "total_tokens": token("total_tokens"),
        "retry_count": 0,
        "sdk_max_retries": 0,
        "timeout": generator.diagnostic in {"APITimeoutError", "TimeoutError", "simulated_timeout"}
        or (isinstance(error, str) and "timeout" in error.casefold()),
        "provider_error": error if isinstance(error, str) and error else None,
        "sent": generator.sent,
        "estimated_cost": None,
        "estimated_cost_reason": "no configured price table",
        "sanitized_provider_user_message": generator.provider_user_message,
    }


def _configured_output_cap() -> int | None:
    try:
        from game.expressive_dialogue import _OUTPUT_CAP
    except Exception:
        return None
    return int(_OUTPUT_CAP)


def _select_prelude(target_id: str, clue_texts: set[str]) -> dict:
    sample = _sample()
    if sample == "empty":
        return {"source": "injected_empty_prelude", "sample": sample, "text": "", "paired": True}
    if sample == "malformed":
        return {"source": "injected_malformed_prelude", "sample": sample, "text": {"prelude": "You look closely."}, "paired": True}
    if sample == "unsafe":
        return {"source": "injected_validator_rejection", "sample": sample, "text": UNSAFE_PRELUDE, "paired": True}
    if sample == "missing":
        return {"source": "missing_saved_prelude", "sample": sample, "text": None, "paired": False, "missing": True}
    if sample == "stub" or sample not in SAVED_SAMPLE_IDS:
        if sample not in SAVED_SAMPLE_IDS and sample != "stub":
            return {"source": "missing_saved_prelude", "sample": sample, "text": None, "paired": False, "missing": True}
        return {"source": "deterministic_offline_stub", "sample": "stub", "text": STUB_PRELUDE, "paired": True}
    record = next((row for row in _saved_records() if row.get("request_id") == sample), None)
    if record is None:
        return {"source": "missing_saved_prelude", "sample": sample, "text": None, "paired": False, "missing": True}
    raw_text, extracted, matched = _raw_provider_text(record)
    discovery = record.get("authoritative_discovery")
    paired = isinstance(discovery, str) and discovery in clue_texts
    return {
        "source": "pr_play_50_saved_response",
        "sample": sample,
        "investigation_id": record.get("investigation_id"),
        "authoritative_discovery": discovery if isinstance(discovery, str) else None,
        "text": raw_text,
        "extracted_narration_text": extracted,
        "extraction_matches_raw": matched,
        "paired": paired,
        "missing": False,
    }


def _timed_preview(contract, generator, fault: str):
    timings = {"validation_ms": None, "assembly_ms": None}
    original_validate = anchored.validate_prelude
    original_assemble = anchored.assemble

    def validate(*args, **kwargs):
        start = time.perf_counter()
        try:
            return original_validate(*args, **kwargs)
        finally:
            timings["validation_ms"] = _elapsed(start)

    def assemble(*args, **kwargs):
        start = time.perf_counter()
        try:
            if fault == "assembly_exception":
                raise RuntimeError("simulated_narration_assembly_exception")
            return original_assemble(*args, **kwargs)
        finally:
            timings["assembly_ms"] = _elapsed(start)

    anchored.validate_prelude = validate
    anchored.assemble = assemble
    try:
        preview = anchored.preview_anchored_investigation(contract, generator, enabled=True)
    finally:
        anchored.validate_prelude = original_validate
        anchored.assemble = original_assemble
    return preview, timings


def run_quarantined_hook(hook_input: dict) -> dict:
    """Replay or reject one prelude. The argument is the detached projection."""
    if set(hook_input) - {"eligible", "player_text", "target_id", "resolution", "narration_payload"}:
        raise ValueError("hook_input_not_detached")
    if os.environ.get(MODE_ENV, "").strip() == "integrated":
        from game.integrated_investigation_narration import run_integrated_hook
        return run_integrated_hook(hook_input)
    fault = _fault()
    started = time.perf_counter()
    resolution = hook_input["resolution"]
    payload = hook_input["narration_payload"]
    if fault == "invalid_projection":
        invalid = json.loads(json.dumps(hook_input))
        invalid["resolution"]["kind"] = "travel"
        invalid["resolution"]["resolved_transition"] = True
        invalid["resolution"]["target_scene_id"] = "unlisted_destination"
        invalid["resolution"]["state_changes"]["currency_gained"] = 50
        try:
            anchored.authorize_anchored_investigation(invalid["resolution"], invalid["narration_payload"])
        except ValueError as exc:
            return {
                "diagnostic": "invalid_authorized_projection",
                "error": str(exc),
                "assembled": None,
                "anchors": [],
                "used_fallback": True,
                "projection_ms": _elapsed(started),
                "saved_lookup_ms": 0.0,
                "validation_ms": None,
                "assembly_ms": None,
                "generator_calls": 0,
                "provider_requests": 0,
            }
        raise RuntimeError("invalid_projection_was_accepted")
    if fault == "unexpected":
        raise KeyError("simulated_unexpected_experimental_hook_exception")
    projection_started = time.perf_counter()
    contract = anchored.authorize_anchored_investigation(resolution, payload)
    projection = anchored.prelude_request(contract)
    projection_ms = _elapsed(projection_started)
    lookup_started = time.perf_counter()
    clue_texts = set(_strings(resolution.get("discovered_clues")))
    if isinstance(resolution.get("clue_text"), str) and resolution["clue_text"].strip():
        clue_texts.add(resolution["clue_text"].strip())
    # A fault stays on the replay path, including when the live flag is also set.
    use_live = live_provider_enabled() and not fault
    if use_live:
        selected = {"source": "live_provider", "sample": "live", "text": None, "paired": True, "live": True}
    else:
        selected = _select_prelude(str(hook_input.get("target_id") or ""), clue_texts)
    lookup_ms = _elapsed(lookup_started)
    anchors = [asdict(anchor) for anchor in contract.anchors]
    base = {
        "target_id": hook_input.get("target_id"),
        "anchors": anchors,
        "authorized_narration_projection": projection,
        "prelude_source": selected["source"],
        "sample": selected.get("sample"),
        "saved_investigation_id": selected.get("investigation_id"),
        "saved_authoritative_discovery": selected.get("authoritative_discovery"),
        "raw_provider_text": selected.get("text") if isinstance(selected.get("text"), str) else None,
        "extracted_narration_text": selected.get("extracted_narration_text"),
        "extraction_matches_raw": selected.get("extraction_matches_raw"),
        "projection_ms": projection_ms,
        "saved_lookup_ms": lookup_ms,
        "provider_requests": 0,
        "generator_calls": 0,
        "live_provider": {"enabled": False},
    }
    if selected.get("missing"):
        base.update({
            "diagnostic": "missing_saved_prelude",
            "assembled": anchored.fallback(contract),
            "used_fallback": True,
            "validation_ms": None,
            "assembly_ms": None,
            "validation": None,
        })
        return base
    if selected.get("paired") is False:
        base.update({
            "diagnostic": "incorrect_investigation_response_pairing",
            "assembled": anchored.fallback(contract),
            "used_fallback": True,
            "validation_ms": None,
            "assembly_ms": None,
            "validation": None,
            "rejected_foreign_prelude": selected.get("text") if isinstance(selected.get("text"), str) else None,
        })
        return base
    replay = _LivePrelude(str(hook_input.get("player_text") or "")) if selected.get("live") else _Replay(selected.get("text"), fault)
    preview, timings = _timed_preview(contract, replay, fault)
    audit = {}
    if preview.validation_json:
        try:
            audit = json.loads(preview.validation_json)
        except json.JSONDecodeError:
            audit = {"unparsed": preview.validation_json}
    specific = getattr(replay, "diagnostic", None)
    diagnostic = preview.diagnostic
    if (
        preview.diagnostic == "generator_or_renderer_error"
        and isinstance(specific, str)
        and specific not in {"provider_text_received"}
    ):
        diagnostic = specific
    base.update({
        "diagnostic": diagnostic,
        "injected_fault": fault or None,
        "assembled": preview.preview_text,
        "used_fallback": preview.used_fallback,
        "validation_ms": timings["validation_ms"],
        "assembly_ms": timings["assembly_ms"],
        "validation": audit,
        "generator_calls": replay.calls,
        "generator_request": replay.request,
        "review_required": preview.review_required,
    })
    if isinstance(replay, _LivePrelude):
        base["prelude_source"] = "live_provider"
        base["raw_provider_text"] = replay.raw_text
        base["provider_requests"] = 1 if replay.sent else 0
        base["live_provider"] = _live_metadata(replay)
        base["live_provider"]["validation_result"] = diagnostic
    return base


def _evidence_dir() -> Path | None:
    raw = os.environ.get(EVIDENCE_ENV, "").strip()
    if not raw:
        return None
    path = Path(raw).resolve()
    try:
        from game.storage import DATA_DIR
        data_dir = Path(DATA_DIR).resolve()
    except Exception:
        data_dir = None
    if data_dir is not None and (path == data_dir or data_dir in path.parents):
        raise OSError("quarantine_evidence_dir_inside_campaign_data")
    return path


def _store(evidence: dict) -> None:
    """Remember the record, then write one JSON file outside the campaign tree."""
    if _fault() == "evidence_write":
        raise OSError("simulated_quarantine_evidence_write_failure")
    directory = _evidence_dir()
    if directory is None:
        evidence["evidence_write"] = "memory_only"
        evidence["serialization_ms"] = 0.0
        evidence["evidence_write_ms"] = 0.0
        return
    directory.mkdir(parents=True, exist_ok=True)
    global _SEQUENCE
    _SEQUENCE += 1
    label = os.environ.get(LABEL_ENV, "").strip() or "record"
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)[:80] or "record"
    path = directory / f"{safe}-{_SEQUENCE:03d}.json"
    evidence["evidence_write"] = "ok"
    evidence["evidence_path"] = str(path)
    started = time.perf_counter()
    encoded = json.dumps(evidence, indent=2, ensure_ascii=False) + "\n"
    evidence["serialization_ms"] = _elapsed(started)
    encoded = json.dumps(evidence, indent=2, ensure_ascii=False) + "\n"
    write_started = time.perf_counter()
    path.write_text(encoded, encoding="utf-8")
    evidence["evidence_write_ms"] = _elapsed(write_started)
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def experimental_publication_enabled(session_id: str | None) -> bool:
    """Default off. Requires the existing integrated quarantine gate and one session id.

    A process-wide flag alone publishes nothing. An unrelated campaign run id
    does not match, so another session in the same process stays deterministic.
    """
    if os.environ.get(PUBLICATION_ENV, "").strip() != "1":
        return False
    if os.environ.get(MODE_ENV, "").strip() != "integrated":
        return False
    if not quarantine_enabled():
        return False
    allowed = os.environ.get(PUBLICATION_SESSION_ENV, "").strip()
    bound = str(session_id or "").strip()
    return bool(allowed) and bool(bound) and allowed == bound


def validated_player_text(player_text: str, *, session_id: str | None, kind: str | None) -> str | None:
    """Return one already-passed integrated sentence, or None to keep deterministic text.

    FAIL, REVIEW_REQUIRED, VALIDATION_ERROR, empty, and mismatched candidates
    stay in the quarantine record. This function does not return them.
    """
    if str(kind or "").strip().lower() not in INVESTIGATION_KINDS:
        return None
    if not experimental_publication_enabled(session_id):
        return None
    if not _MEMORY:
        return None
    evidence = _MEMORY[-1]
    if str(evidence.get("player_text") or "") != str(player_text or ""):
        return None
    validation = evidence.get("validation") if isinstance(evidence.get("validation"), dict) else {}
    if validation.get("decision") != "PASS" or evidence.get("used_fallback") is not False:
        return None
    if evidence.get("mode") != "quarantined_integrated":
        return None
    text = evidence.get("assembled")
    raw = evidence.get("raw_provider_text")
    if not isinstance(text, str) or not text.strip() or text != raw:
        return None
    return text


def deterministic_fallback_text(player_text: str, *, session_id: str | None, kind: str | None) -> str | None:
    """Return the engine sentence already stored for a rejected candidate.

    The rejected provider text is not returned. Callers use this only when the
    ordinary response is the provider-disabled stub.
    """
    if str(kind or "").strip().lower() not in INVESTIGATION_KINDS:
        return None
    if not experimental_publication_enabled(session_id):
        return None
    if not _MEMORY:
        return None
    evidence = _MEMORY[-1]
    if str(evidence.get("player_text") or "") != str(player_text or ""):
        return None
    if evidence.get("used_fallback") is not True:
        return None
    text = evidence.get("assembled")
    raw = evidence.get("raw_provider_text")
    if not isinstance(text, str) or not text.strip():
        return None
    if isinstance(raw, str) and text == raw:
        return None
    return text


def note_player_facing_publication() -> None:
    """Record that the validated sentence was copied to the player response."""
    if not _MEMORY:
        return
    evidence = _MEMORY[-1]
    validation = evidence.get("validation") if isinstance(evidence.get("validation"), dict) else {}
    if validation.get("decision") != "PASS" or evidence.get("used_fallback") is not False:
        return
    evidence["player_facing_published"] = True
    path = evidence.get("evidence_path")
    if path and evidence.get("evidence_write") == "ok":
        Path(path).write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def observe_completed_investigation(*, resolution, scene, known_clue_texts, player_text: str) -> dict:
    """Build the detached projection, run the hook, and store quarantine evidence.

    Campaign objects are read only to copy public investigation fields. The hook
    result is not a gameplay instruction and is not written back to ``resolution``.
    """
    if not quarantine_enabled():
        return {"enabled": False}
    started = time.perf_counter()
    token = _IN_HOOK.set(True)
    hook_input: dict = {}
    evidence: dict = {
        "enabled": True,
        "player_text": player_text,
        "provider_requests": 0,
        "state_write_attempted": False,
    }
    try:
        build_started = time.perf_counter()
        hook_input = build_hook_input(
            resolution=resolution,
            scene=scene,
            known_clue_texts=known_clue_texts,
            player_text=player_text,
        )
        evidence["projection_build_ms"] = _elapsed(build_started)
        evidence["hook_input"] = hook_input
        evidence["eligible"] = bool(hook_input.get("eligible"))
        if not hook_input.get("eligible"):
            evidence["diagnostic"] = hook_input.get("reason")
            evidence["assembled"] = None
            evidence["anchors"] = []
            evidence["generator_calls"] = 0
        else:
            evidence.update(run_quarantined_hook(hook_input))
            evidence["hook_input"] = hook_input
            evidence["eligible"] = True
    except Exception as exc:
        evidence["diagnostic"] = "unexpected_experimental_hook_exception"
        evidence["error_type"] = type(exc).__name__
        evidence["error"] = str(exc)[:300]
        evidence["used_fallback"] = True
        if hook_input.get("eligible") and not evidence.get("anchors"):
            try:
                contract = anchored.authorize_anchored_investigation(
                    hook_input["resolution"], hook_input["narration_payload"],
                )
                evidence["anchors"] = [asdict(anchor) for anchor in contract.anchors]
                evidence["assembled"] = anchored.fallback(contract)
            except Exception:
                evidence["assembled"] = evidence.get("assembled")
    finally:
        _IN_HOOK.reset(token)
        evidence["hook_work_ms"] = _elapsed(started)
        write_started = time.perf_counter()
        try:
            _store(evidence)
        except Exception as exc:
            evidence["evidence_write"] = "failed"
            evidence["evidence_write_error"] = type(exc).__name__
            evidence["evidence_write_ms"] = _elapsed(write_started)
        evidence["total_hook_ms"] = _elapsed(started)
        _MEMORY.append(evidence)
        path = evidence.get("evidence_path")
        if path and evidence.get("evidence_write") == "ok":
            Path(path).write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return evidence
