"""Lightweight cross-turn discourse focus.

This module owns active discourse slots only. Entity, claim, and lead records
stay with their existing owners. Slots store stable references so a later turn
can bind "that lead", "it", or "when I did that" without a coreference engine.
"""
from __future__ import annotations

from typing import Any, Mapping

DISCOURSE_FOCUS_KEY = "discourse_focus"
DISCOURSE_VERSION = 1

SLOT_INTERLOCUTOR = "active_interlocutor"
SLOT_CLAIM = "active_claim"
SLOT_LEAD = "active_actionable_lead"
SLOT_INSPECTED = "active_inspected"
SLOT_ACTION = "last_attempted_action"

SCENE_BOUND_SLOTS = frozenset({SLOT_INTERLOCUTOR, SLOT_INSPECTED, SLOT_ACTION})
ALL_SLOTS = (
    SLOT_INTERLOCUTOR,
    SLOT_CLAIM,
    SLOT_LEAD,
    SLOT_INSPECTED,
    SLOT_ACTION,
)


def _clean(value: Any, *, limit: int = 160) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())[:limit]


def _scene_id_of(session: Mapping[str, Any] | None, scene_id: str | None = None) -> str:
    explicit = _clean(scene_id, limit=80)
    if explicit:
        return explicit
    if isinstance(session, Mapping):
        return _clean(session.get("active_scene_id"), limit=80)
    return ""


def empty_discourse_focus(scene_id: str | None = None) -> dict[str, Any]:
    return {
        "version": DISCOURSE_VERSION,
        "scene_id": _clean(scene_id, limit=80),
        SLOT_INTERLOCUTOR: None,
        SLOT_CLAIM: None,
        SLOT_LEAD: None,
        SLOT_INSPECTED: None,
        SLOT_ACTION: None,
        "last_committed_turn": None,
        "last_committed_contract_id": None,
    }


def _slot(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    label = _clean(value.get("label"), limit=160)
    ident = _clean(value.get("id"), limit=80)
    if not label and not ident:
        return None
    turn = value.get("turn_index")
    return {
        "id": ident or None,
        "label": label or ident,
        "kind": _clean(value.get("kind"), limit=40) or None,
        "scene_id": _clean(value.get("scene_id"), limit=80) or None,
        "turn_index": turn if isinstance(turn, int) else None,
        "source": _clean(value.get("source"), limit=40) or None,
    }


def read_discourse_focus(session: Mapping[str, Any] | None) -> dict[str, Any]:
    raw = session.get(DISCOURSE_FOCUS_KEY) if isinstance(session, Mapping) else None
    focus = empty_discourse_focus()
    if not isinstance(raw, Mapping):
        return focus
    focus["version"] = DISCOURSE_VERSION
    focus["scene_id"] = _clean(raw.get("scene_id"), limit=80)
    for name in ALL_SLOTS:
        focus[name] = _slot(raw.get(name))
    turn = raw.get("last_committed_turn")
    focus["last_committed_turn"] = turn if isinstance(turn, int) else None
    focus["last_committed_contract_id"] = _clean(raw.get("last_committed_contract_id"), limit=80) or None
    return focus


def _latest_claim(session: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(session, Mapping):
        return None
    ledger = session.get("bounded_improvisation")
    entries = ledger.get("entries") if isinstance(ledger, Mapping) else None
    if not isinstance(entries, list):
        return None
    for entry in reversed(entries):
        if not isinstance(entry, Mapping):
            continue
        if str(entry.get("kind") or "") != "npc_claim":
            continue
        if str(entry.get("status") or "").strip().lower() not in {"accepted", "promoted"}:
            continue
        return {
            "id": _clean(entry.get("id"), limit=80) or None,
            "label": _clean(entry.get("content"), limit=160),
            "kind": "claim",
            "scene_id": _clean(entry.get("scene_id"), limit=80) or None,
            "source": "claim_ledger",
        }
    return None


def _context_interlocutor(session: Mapping[str, Any] | None, scene_id: str) -> dict[str, Any] | None:
    if not isinstance(session, Mapping):
        return None
    ctx = session.get("interaction_context")
    if not isinstance(ctx, Mapping):
        return None
    ident = _clean(ctx.get("active_interaction_target_id"), limit=80)
    if not ident:
        return None
    ctx_scene = _clean(ctx.get("scene_id") or ctx.get("active_scene_id"), limit=80)
    if ctx_scene and scene_id and ctx_scene != scene_id:
        return None
    return {
        "id": ident,
        "label": _clean(ctx.get("active_interaction_target_label"), limit=120) or ident,
        "kind": "interlocutor",
        "scene_id": ctx_scene or scene_id or None,
        "source": "interaction_context",
    }


def _pending_lead(session: Mapping[str, Any] | None, scene_id: str) -> dict[str, Any] | None:
    if not isinstance(session, Mapping) or not scene_id:
        return None
    root = session.get("scene_runtime")
    runtime = root.get(scene_id) if isinstance(root, Mapping) else None
    pending = runtime.get("pending_leads") if isinstance(runtime, Mapping) else None
    if not isinstance(pending, list):
        return None
    for lead in reversed(pending):
        if not isinstance(lead, Mapping):
            continue
        ident = _clean(lead.get("authoritative_lead_id") or lead.get("clue_id"), limit=80)
        label = _clean(lead.get("text") or lead.get("label"), limit=160)
        if not ident and not label:
            continue
        return {
            "id": ident or None,
            "label": label or ident,
            "kind": "lead",
            "scene_id": scene_id,
            "source": "pending_leads",
        }
    return None


def effective_discourse_focus(
    session: Mapping[str, Any] | None,
    *,
    scene_id: str | None = None,
) -> dict[str, Any]:
    """Focus visible to this turn. Scene-bound slots from another scene are hidden.

    Empty slots are filled from the systems that already own those records.
    This read does not copy those records into a second authority.
    """
    current = _scene_id_of(session, scene_id)
    focus = read_discourse_focus(session)
    stored_scene = _clean(focus.get("scene_id"), limit=80)
    if current and stored_scene and stored_scene != current:
        for name in SCENE_BOUND_SLOTS:
            focus[name] = None
        focus["scene_id"] = current
    elif current:
        focus["scene_id"] = current
    for name in SCENE_BOUND_SLOTS:
        slot = focus.get(name)
        slot_scene = _clean(slot.get("scene_id"), limit=80) if isinstance(slot, Mapping) else ""
        if slot_scene and current and slot_scene != current:
            focus[name] = None
    if focus.get(SLOT_CLAIM) is None:
        focus[SLOT_CLAIM] = _latest_claim(session)
    if focus.get(SLOT_INTERLOCUTOR) is None:
        focus[SLOT_INTERLOCUTOR] = _context_interlocutor(session, current)
    if focus.get(SLOT_LEAD) is None:
        focus[SLOT_LEAD] = _pending_lead(session, current)
    return focus


def focus_summary(focus: Mapping[str, Any] | None) -> dict[str, Any]:
    src = focus if isinstance(focus, Mapping) else {}
    out: dict[str, Any] = {"scene_id": src.get("scene_id") or None}
    for name in ALL_SLOTS:
        slot = src.get(name)
        if isinstance(slot, Mapping) and (slot.get("id") or slot.get("label")):
            out[name] = {"id": slot.get("id"), "label": slot.get("label")}
        else:
            out[name] = None
    return out


def commit_discourse_focus(
    session: dict[str, Any] | None,
    *,
    contract: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None = None,
    scene_id: str | None = None,
) -> dict[str, Any]:
    """Record focus established by this turn. A retry of the same contract is a no-op."""
    if not isinstance(session, dict) or not isinstance(contract, Mapping):
        return read_discourse_focus(session)
    current = _scene_id_of(session, scene_id)
    contract_id = _clean(contract.get("contract_id"), limit=80)
    focus = read_discourse_focus(session)
    if contract_id and focus.get("last_committed_contract_id") == contract_id:
        return focus
    stored_scene = _clean(focus.get("scene_id"), limit=80)
    if current and stored_scene and stored_scene != current:
        for name in SCENE_BOUND_SLOTS:
            focus[name] = None
    if current:
        focus["scene_id"] = current
    if contract.get("ambiguous"):
        focus["last_committed_contract_id"] = contract_id or None
        turn = contract.get("turn_index")
        focus["last_committed_turn"] = turn if isinstance(turn, int) else focus.get("last_committed_turn")
        session[DISCOURSE_FOCUS_KEY] = focus
        return focus

    turn = contract.get("turn_index") if isinstance(contract.get("turn_index"), int) else None
    operation = str(contract.get("operation") or "")
    provenance = str(contract.get("referent_provenance") or "")
    discourse = contract.get("discourse_ref") if isinstance(contract.get("discourse_ref"), Mapping) else {}
    target = contract.get("target_ref") if isinstance(contract.get("target_ref"), Mapping) else {}
    social = resolution.get("social") if isinstance(resolution, Mapping) else None
    interlocutor = _clean(contract.get("interlocutor_id"), limit=80)
    if not interlocutor and isinstance(social, Mapping):
        interlocutor = _clean(social.get("npc_id"), limit=80)
    if interlocutor:
        focus[SLOT_INTERLOCUTOR] = _slot(
            {
                "id": interlocutor,
                "label": _clean(social.get("npc_name"), limit=120) if isinstance(social, Mapping) else interlocutor,
                "kind": "interlocutor",
                "scene_id": current,
                "turn_index": turn,
                "source": "resolution_contract",
            }
        )
    if str(discourse.get("type") or "") == "claim" or str(contract.get("dimension") or "") in {
        "source",
        "confidence",
        "location",
        "time",
    }:
        claim_id = _clean(discourse.get("id"), limit=80)
        claim_label = _clean(discourse.get("label") or contract.get("conversational_subject"), limit=160)
        if claim_id or claim_label:
            focus[SLOT_CLAIM] = _slot(
                {
                    "id": claim_id,
                    "label": claim_label,
                    "kind": "claim",
                    "scene_id": current,
                    "turn_index": turn,
                    "source": "resolution_contract",
                }
            )
    if operation == "follow" or str(discourse.get("type") or "") == "lead":
        lead_id = _clean(discourse.get("id"), limit=80)
        lead_label = _clean(discourse.get("label") or target.get("id_or_text"), limit=160)
        if lead_id or lead_label:
            focus[SLOT_LEAD] = _slot(
                {
                    "id": lead_id,
                    "label": lead_label,
                    "kind": "lead",
                    "scene_id": current,
                    "turn_index": turn,
                    "source": "resolution_contract",
                }
            )
    if operation in {"perceive", "inspect"} and provenance != "unresolved":
        inspected = _clean(target.get("id_or_text") or discourse.get("label"), limit=160)
        if inspected and inspected.lower() not in {"scene", "here", "around me"}:
            focus[SLOT_INSPECTED] = _slot(
                {
                    "id": _clean(discourse.get("id") or target.get("id_or_text"), limit=80),
                    "label": inspected,
                    "kind": _clean(target.get("type"), limit=40) or "object",
                    "scene_id": current,
                    "turn_index": turn,
                    "source": "resolution_contract",
                }
            )
    if operation in {"act", "follow", "confirm"}:
        action_label = _clean(contract.get("raw_input") or target.get("id_or_text"), limit=160)
        if action_label:
            focus[SLOT_ACTION] = _slot(
                {
                    "id": contract_id,
                    "label": action_label,
                    "kind": operation,
                    "scene_id": current,
                    "turn_index": turn,
                    "source": "resolution_contract",
                }
            )
    focus["last_committed_turn"] = turn
    focus["last_committed_contract_id"] = contract_id or None
    session[DISCOURSE_FOCUS_KEY] = focus
    return focus
