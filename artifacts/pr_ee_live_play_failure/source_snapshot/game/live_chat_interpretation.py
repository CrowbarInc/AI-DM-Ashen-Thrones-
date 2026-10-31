"""Connect the PR-DO/DR interpretation contract to production chat.

This module does not interpret on its own. It asks the existing contract for a
description, then the existing PR-DU bridge decides whether a resolver may see it.
A rejected, malformed, or ambiguous result never falls through to another parser.
"""

from __future__ import annotations

import json
import os
import re
import time
from contextvars import ContextVar
from typing import Any

from game.player_interpretation_bridge import visible_catalog
from game.provider_budget import (
    accounting_active,
    begin_request,
    finish_request,
    provider_calls_disabled,
)
from game.semantic_interpreter import live_interpretation_enabled, player_visible_turns

_CONSUMED: ContextVar[bool] = ContextVar("live_chat_interpretation_consumed", default=False)
_SECRET_RE = re.compile(r"sk-[A-Za-z0-9_\-]{8,}|Bearer\s+\S+", re.IGNORECASE)
_OUTPUT_CAP = 320
_CONTRACT = None


def redact(text: str) -> str:
    return _SECRET_RE.sub("[REDACTED]", str(text or ""))


def reset_live_interpretation_consumed() -> None:
    _CONSUMED.set(False)


def mark_live_interpretation_consumed() -> None:
    _CONSUMED.set(True)


def live_interpretation_consumed() -> bool:
    return bool(_CONSUMED.get())


def production_live_interpretation_enabled() -> bool:
    return live_interpretation_enabled() and not provider_calls_disabled()


def _contract():
    """Import the existing contract after its packages force interpretation off."""
    global _CONTRACT
    if _CONTRACT is not None:
        return _CONTRACT
    previous = os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION")
    try:
        from experiments.pr_do.adapter import adapt_interpretation
        from experiments.pr_dp import CONFIGURED_MODEL
        from experiments.pr_dp.prompt import provider_schema
        from experiments.pr_dr.prompt import build_messages_for_catalog, context_leaks, preflight_tokens
    finally:
        if previous is None:
            os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)
        else:
            os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = previous
    _CONTRACT = (
        adapt_interpretation,
        build_messages_for_catalog,
        context_leaks,
        preflight_tokens,
        CONFIGURED_MODEL,
        provider_schema,
    )
    return _CONTRACT


def _scene_summary(scene: dict | None) -> str:
    current = scene.get("scene") if isinstance(scene, dict) and isinstance(scene.get("scene"), dict) else scene
    if not isinstance(current, dict):
        return ""
    location = str(current.get("location") or current.get("id") or "")
    summary = str(current.get("summary") or "")
    return f"{location}. {summary}".strip()


def _catalog_rows(scene: dict | None, world: dict | None) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for entity_id, info in sorted(visible_catalog(scene, world).items()):
        row = info.get("row") if isinstance(info.get("row"), dict) else {}
        label = str(row.get("label") or row.get("name") or entity_id)
        aliases = [str(item) for item in (row.get("aliases") or []) if str(item).strip()]
        if aliases:
            label = f"{label} [{' | '.join(aliases)}]"
        rows.append((entity_id, label, str(info.get("kind") or "")))
    return rows


def _blocked(reason: str, player_facing_text: str, *, tags: list[str], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "status": "blocked",
        "reason": reason,
        "player_facing_text": player_facing_text,
        "tags": tags,
        "record": None,
        "raw_interpretation": "",
        "provider_requests": [],
    }
    if extra:
        payload.update(extra)
    return payload


def _usage_triplet(resp: Any) -> tuple[int | None, int | None, int | None]:
    usage = getattr(resp, "usage", None)
    if usage is None:
        return None, None, None
    incoming = getattr(usage, "input_tokens", None)
    outgoing = getattr(usage, "output_tokens", None)
    total = getattr(usage, "total_tokens", None)
    if incoming is None or outgoing is None or total is None:
        return None, None, None
    return int(incoming), int(outgoing), int(total)


def request_interpretation(messages: list[dict[str, str]], *, estimated_input: int) -> dict[str, Any]:
    """One structured completion. No retry and no model switch."""
    _adapt, _build, _leaks, _preflight, model_id, schema_fn = _contract()
    refusal = begin_request(purpose="interpretation", estimated_input=estimated_input, max_output=_OUTPUT_CAP)
    if refusal:
        usage = finish_request(
            {
                "purpose": "interpretation",
                "sent": False,
                "model": model_id,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "refusal": refusal,
            }
        )
        return {"ok": False, "sent": False, "reason": refusal, "error": refusal, "usage": usage}
    from openai import OpenAI

    from game.config import get_openai_api_key

    started = time.perf_counter()
    try:
        from game.gm import provider_timeout_seconds

        client = OpenAI(api_key=get_openai_api_key(), timeout=provider_timeout_seconds())
        response = client.responses.create(
            model=model_id,
            input=messages,
            temperature=0,
            max_output_tokens=_OUTPUT_CAP,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "pr_dr_interpretation",
                    "strict": True,
                    "schema": schema_fn(),
                }
            },
        )
    except Exception as exc:  # noqa: BLE001 - a failed call is not retried
        finish_request(
            {
                "purpose": "interpretation",
                "sent": True,
                "model": model_id,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "error": redact(str(exc))[:200],
            }
        )
        return {"ok": False, "sent": True, "reason": "provider_failure", "error": type(exc).__name__}
    incoming, outgoing, total = _usage_triplet(response)
    model = str(getattr(response, "model", "") or "")
    record = finish_request(
        {
            "purpose": "interpretation",
            "sent": True,
            "configured_model": model_id,
            "model": model,
            "request_id": getattr(response, "id", None),
            "input_tokens": incoming,
            "output_tokens": outgoing,
            "total_tokens": total,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "estimated_input_tokens": estimated_input,
            "max_output_tokens": _OUTPUT_CAP,
        }
    )
    if model and not model.startswith(model_id):
        return {
            "ok": False,
            "sent": True,
            "reason": "model_mismatch",
            "error": "provider returned a different model",
            "usage": record,
        }
    return {"ok": True, "sent": True, "text": str(getattr(response, "output_text", "") or ""), "usage": record}


def interpret_production_turn(
    *,
    player_text: str,
    mode: str,
    scene: dict | None,
    world: dict | None,
    log: list | None,
) -> dict[str, Any]:
    """Return skipped, blocked, or accepted. Accepted carries a bridge record."""
    if not production_live_interpretation_enabled():
        reason = "provider_calls_disabled" if provider_calls_disabled() else "live_interpretation_disabled"
        return {"status": "skipped", "reason": reason, "record": None, "provider_requests": []}

    adapt_interpretation, build_messages_for_catalog, context_leaks, preflight_tokens, _model, _schema = _contract()
    catalog = _catalog_rows(scene, world)
    recent = player_visible_turns(log or [], limit=2)
    messages = build_messages_for_catalog(
        player_text,
        scene_summary=_scene_summary(scene),
        catalog=catalog,
        recent_visible=recent or None,
    )
    leaks = context_leaks(messages, player_text)
    for turn in recent:
        for value in turn.values():
            for leak in list(leaks):
                if leak.casefold() in str(value or "").casefold():
                    leaks = [item for item in leaks if item != leak]
    if leaks:
        return _blocked(
            "context_leak",
            "I can't interpret that from the current scene without using information you have not been shown.",
            tags=["interpretation_rejected", "non_mutating"],
        )

    estimated = preflight_tokens(messages)
    if accounting_active() and estimated <= 0:
        return _blocked(
            "token_estimate_unavailable",
            "I can't send that for interpretation because the token estimate is unavailable.",
            tags=["interpretation_rejected", "non_mutating"],
        )
    call = request_interpretation(messages, estimated_input=estimated)
    provider_requests = [call.get("usage")] if isinstance(call.get("usage"), dict) else []
    if not call.get("ok"):
        reason = str(call.get("reason") or "provider_failure")
        return _blocked(
            reason,
            "I couldn't interpret that just now, so no gameplay action was taken.",
            tags=["interpretation_rejected", "non_mutating"],
            extra={"provider_requests": provider_requests, "provider_error": call.get("error")},
        )

    raw = redact(str(call.get("text") or ""))
    try:
        parsed = json.loads(call.get("text") or "")
    except json.JSONDecodeError:
        return _blocked(
            "malformed_interpretation",
            "I couldn't read that as a gameplay action. Please say it again in plain words.",
            tags=["interpretation_rejected", "non_mutating", "malformed_interpretation"],
            extra={"raw_interpretation": raw, "provider_requests": provider_requests},
        )
    if not isinstance(parsed, dict):
        return _blocked(
            "malformed_interpretation",
            "I couldn't read that as a gameplay action. Please say it again in plain words.",
            tags=["interpretation_rejected", "non_mutating", "malformed_interpretation"],
            extra={"raw_interpretation": raw, "provider_requests": provider_requests},
        )

    payload = dict(parsed)
    if mode == "IC":
        payload["communication_mode"] = "IN_WORLD_ACTION"
    adapted = adapt_interpretation(payload, permitted_ids=[entity_id for entity_id, _label, _kind in catalog])
    record = adapted.get("record") if isinstance(adapted.get("record"), dict) else None
    eligibility = adapted.get("eligibility") if isinstance(adapted.get("eligibility"), dict) else {}
    disposition = str(eligibility.get("disposition") or "")
    common = {
        "raw_interpretation": raw,
        "provider_requests": provider_requests,
        "eligibility_disposition": disposition,
        "model_communication_mode": parsed.get("communication_mode"),
        "interpretation_status": None if record is None else record.get("interpretation_status"),
    }
    if not adapted.get("structurally_valid") or record is None:
        return _blocked(
            "malformed_interpretation",
            "I couldn't read that as a gameplay action. Please say it again in plain words.",
            tags=["interpretation_rejected", "non_mutating", "malformed_interpretation"],
            extra=common,
        )
    if disposition == "OUT_OF_CHARACTER" and mode != "IC":
        return _blocked(
            "automatic_ooc",
            "Understood. I'll treat that as out of character. No gameplay action is executed, "
            "no game time advances, and committed state is unchanged.",
            tags=["ooc_correction", "non_mutating", "automatic_ooc"],
            extra={**common, "record": record},
        )
    if disposition in {"NEEDS_CLARIFICATION", "SAFE_ABSTENTION"}:
        question = str(record.get("clarification_question") or "").strip()
        text = question or "I need a clearer action or target before I change anything in the scene."
        return _blocked(
            "clarification_required",
            text,
            tags=["interpretation_clarification", "non_mutating"],
            extra={**common, "record": record},
        )
    if disposition != "ELIGIBLE_FOR_VALIDATION":
        return _blocked(
            "interpretation_rejected",
            "I can't carry that out from the available interpretation. Tell me the action and who or what it concerns.",
            tags=["interpretation_rejected", "non_mutating"],
            extra={**common, "record": record},
        )
    components = record.get("action_components") if isinstance(record.get("action_components"), list) else []
    if len(components) != 1:
        return _blocked(
            "clarification_required",
            "Which single action should I resolve first?",
            tags=["interpretation_clarification", "non_mutating"],
            extra={**common, "record": record},
        )
    mark_live_interpretation_consumed()
    return {
        "status": "accepted",
        "reason": "eligible_for_bridge",
        "record": record,
        "player_facing_text": "",
        "tags": ["live_interpretation"],
        **common,
    }
