"""Lightweight cross-turn discourse focus.

This module owns active discourse slots only. Entity, claim, and lead records
stay with their existing owners. Slots store stable references so a later turn
can bind "that lead", "it", or "when I did that" without a coreference engine.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping, Sequence

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
    slot = {
        "id": ident or None,
        "label": label or ident,
        "kind": _clean(value.get("kind"), limit=40) or None,
        "scene_id": _clean(value.get("scene_id"), limit=80) or None,
        "turn_index": turn if isinstance(turn, int) else None,
        "source": _clean(value.get("source"), limit=40) or None,
    }
    epistemic = _clean(value.get("epistemic_status"), limit=40)
    if epistemic:
        slot["epistemic_status"] = epistemic
    return slot


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


def _speaker_from_emission(
    text: str | None,
    referents: Sequence[Mapping[str, Any]] | None,
) -> tuple[str, str] | None:
    """The one catalog interlocutor the emitted line actually attributes."""
    from game.interaction_completion import attributed_speaker_label, unique_interlocutor

    label = attributed_speaker_label(text)
    if not label or not referents:
        return None
    chosen = unique_interlocutor(label, referents)
    if not chosen:
        return None
    ident = str(chosen.get("id") or "")
    if not ident:
        return None
    return ident, str(chosen.get("label") or ident)


def commit_discourse_focus(
    session: dict[str, Any] | None,
    *,
    contract: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None = None,
    scene_id: str | None = None,
    emitted_text: str | None = None,
    canonical_referents: Sequence[Mapping[str, Any]] | None = None,
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
    from game.interpretation_proposal import discourse_commit_blocked, span_is_malformed
    from game.incidental_entity import persist_incidental_binding

    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    binding = construction.get("entity_binding") if isinstance(construction.get("entity_binding"), Mapping) else {}
    if str(binding.get("status") or "") == "bound_incidental":
        persist_incidental_binding(session, binding, current)
    explicit_unbound = bool(binding.get("explicit_new_interlocutor")) and str(binding.get("status") or "") in {
        "unresolved",
        "ambiguous",
        "rejected_consequential",
    }
    if explicit_unbound:
        focus[SLOT_INTERLOCUTOR] = None

    if contract.get("ambiguous") or discourse_commit_blocked(contract):
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
    if not interlocutor and isinstance(social, Mapping) and not binding.get("explicit_new_interlocutor"):
        interlocutor = _clean(social.get("npc_id"), limit=80)
    label = _clean(binding.get("label"), limit=120)
    if not label and isinstance(social, Mapping):
        label = _clean(social.get("npc_name"), limit=120)
    if explicit_unbound:
        interlocutor = ""
    if interlocutor:
        focus[SLOT_INTERLOCUTOR] = _slot(
            {
                "id": interlocutor,
                "label": label or interlocutor,
                "kind": "interlocutor",
                "scene_id": current,
                "turn_index": turn,
                "source": "resolution_contract",
            }
        )
    elif construction.get("interlocutor_rejected") and not explicit_unbound:
        focus[SLOT_INTERLOCUTOR] = None
        adopted = _speaker_from_emission(emitted_text, canonical_referents)
        if adopted:
            focus[SLOT_INTERLOCUTOR] = _slot(
                {
                    "id": adopted[0],
                    "label": adopted[1],
                    "kind": "interlocutor",
                    "scene_id": current,
                    "turn_index": turn,
                    "source": "emitted_speaker",
                }
            )
    if str(discourse.get("type") or "") == "claim":
        claim_id = _clean(discourse.get("id"), limit=80)
        claim_label = _clean(discourse.get("label"), limit=160)
        interlocutor_slot = focus.get(SLOT_INTERLOCUTOR) if isinstance(focus.get(SLOT_INTERLOCUTOR), Mapping) else {}
        interlocutor_id = _clean(interlocutor_slot.get("id"), limit=80)
        interlocutor_label = _clean(interlocutor_slot.get("label") or contract.get("interlocutor_id"), limit=120)
        if _claim_label_is_proposition(
            claim_label,
            claim_id=claim_id,
            interlocutor_id=interlocutor_id,
            interlocutor_label=interlocutor_label,
        ):
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
        if inspected.lower() in {"scene", "here", "around me"}:
            inspected = ""
        raw_input = _clean(contract.get("raw_input"), limit=180).lower().strip(" ?")
        if inspected and raw_input and inspected.lower().strip(" ?") == raw_input:
            inspected = ""
        if span_is_malformed(inspected):
            inspected = ""
        if inspected:
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


_CLAIM_QUOTE_RE = re.compile(r'"([^"]{12,240})"')
_CLAIM_ASSERT_RE = re.compile(
    r"\b(?:word is|i heard|i have heard|they say|rumou?r is|people say|"
    r"(?:he|she|they|travelers|someone|runner|guard|serjeant)\s+says?)\b",
    re.IGNORECASE,
)
_CLAIM_HEDGE_RE = re.compile(
    r"\b(?:can(?:not|'t)|could(?: not|n't)|do(?: not|n't)|will not|won't)\s+say\b",
    re.IGNORECASE,
)
_CLAIM_STRONG_FRAME_RE = re.compile(
    r"\b(?:word is|i heard|i have heard|they say|rumou?r is|people say)\b",
    re.IGNORECASE,
)
_CLAIM_REFUSAL_RE = re.compile(
    r"\b(?:couldn'?t tell|cannot verify|can't verify|will not swear|another source|do not know enough|"
    r"cannot be completed|no reliable source)\b",
    re.IGNORECASE,
)


def _claim_proposition(quote: str) -> str:
    """One follow-up-worthy sentence inside an asserted claim.

    An inability, a shrug, or a bare verb is not a claim. The quote must
    already be framed as something heard, said, or rumored.
    """
    if not _CLAIM_ASSERT_RE.search(quote):
        return ""
    if _CLAIM_REFUSAL_RE.search(quote) and not _CLAIM_STRONG_FRAME_RE.search(quote):
        return ""
    parts = [part.strip(" \"") for part in re.split(r"(?<=[.!?])\s+", str(quote or "")) if part.strip()]
    if not parts:
        parts = [str(quote or "").strip()]
    for part in parts:
        if _CLAIM_HEDGE_RE.search(part) and not _CLAIM_STRONG_FRAME_RE.search(part):
            continue
        if _CLAIM_REFUSAL_RE.search(part):
            continue
        if not (_CLAIM_ASSERT_RE.search(part) or _CLAIM_VERB_RE.search(part)):
            continue
        return _clean(part, limit=160)
    return ""


_CLAIM_VERB_RE = re.compile(
    r"\b(?:is|are|was|were|has|have|had|will|says?|said|heard|changed|vanished|watched|"
    r"missing|left|took|told|claims?|saw|seen|went|came)\b",
    re.IGNORECASE,
)


def _same_identity(left: str, right: str) -> bool:
    if not left or not right:
        return False
    return _norm_claim(left.replace("_", " ")) == _norm_claim(right.replace("_", " "))


def _claim_label_is_proposition(
    label: str,
    *,
    claim_id: str = "",
    interlocutor_id: str = "",
    interlocutor_label: str = "",
) -> bool:
    """A claim is an assertion. A speaker's name is not one."""
    text = _clean(label, limit=160)
    if not text or not _CLAIM_VERB_RE.search(text):
        return False
    if _same_identity(text, interlocutor_id) or _same_identity(text, interlocutor_label):
        return False
    if _same_identity(claim_id, interlocutor_id) or _same_identity(claim_id, interlocutor_label):
        return False
    return True


def _norm_claim(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def note_emitted_npc_claim(
    session: dict[str, Any] | None,
    *,
    emitted_text: str | None,
    scene_id: str | None = None,
) -> bool:
    """Point active_claim at an NPC claim that was accepted and actually emitted.

    Discourse promotion does not make the claim world truth. Rejected ledger
    entries are never promoted, even if their wording appears in the text.
    """
    if not isinstance(session, dict):
        return False
    visible = str(emitted_text or "").strip()
    if not visible:
        return False
    folded = _norm_claim(visible)
    ledger = session.get("bounded_improvisation") if isinstance(session.get("bounded_improvisation"), dict) else {}
    rejected = ledger.get("rejected") if isinstance(ledger.get("rejected"), list) else []
    blocked: set[str] = set()
    for entry in rejected:
        if not isinstance(entry, dict):
            continue
        content = _norm_claim(str(entry.get("content") or ""))
        if len(content) >= 12 and content in folded:
            blocked.add(content)
    current = _scene_id_of(session, scene_id)
    focus = read_discourse_focus(session)
    if current:
        focus["scene_id"] = current
    entries = ledger.get("entries") if isinstance(ledger.get("entries"), list) else []
    for entry in reversed(entries):
        if not isinstance(entry, dict):
            continue
        if str(entry.get("kind") or "") != "npc_claim":
            continue
        if str(entry.get("status") or "").strip().lower() not in {"accepted", "promoted"}:
            continue
        content = _norm_claim(str(entry.get("content") or ""))
        if len(content) < 12 or content not in folded or content in blocked:
            continue
        focus[SLOT_CLAIM] = _slot(
            {
                "id": _clean(entry.get("id"), limit=80) or None,
                "label": _clean(str(entry.get("content") or ""), limit=160),
                "kind": "claim",
                "scene_id": _clean(entry.get("scene_id"), limit=80) or current or None,
                "turn_index": focus.get("last_committed_turn"),
                "source": "claim_ledger",
                "epistemic_status": _clean(entry.get("epistemic_status"), limit=40) or "hearsay",
            }
        )
        session[DISCOURSE_FOCUS_KEY] = focus
        return True
    if blocked:
        return False
    for quote in _CLAIM_QUOTE_RE.findall(visible):
        label = _claim_proposition(quote)
        if not label:
            continue
        from game.proposition_authority import epistemic_frame

        frame = epistemic_frame(label) or "hearsay"
        if frame == "world_truth":
            frame = "grounded"
        focus[SLOT_CLAIM] = _slot(
            {
                "id": "emitted_" + hashlib.sha1(label.lower().encode("utf-8")).hexdigest()[:10],
                "label": label,
                "kind": "claim",
                "scene_id": current or None,
                "turn_index": focus.get("last_committed_turn"),
                "source": "emitted_npc_claim",
                "epistemic_status": frame,
            }
        )
        session[DISCOURSE_FOCUS_KEY] = focus
        return True
    return False


def commit_active_epistemic_claim(
    session: dict[str, Any] | None,
    *,
    claims: Sequence[Mapping[str, Any]] | None,
    scene_id: str | None = None,
    turn_index: int | None = None,
) -> bool:
    """Focus one meaningful inference, hypothesis, or unresolved proposition."""
    if not isinstance(session, dict):
        return False
    chosen: Mapping[str, Any] | None = None
    priorities = {
        "gm_inference": 3,
        "player_hypothesis": 2,
        "unresolved": 1,
    }
    chosen_priority = 0
    for claim in claims or []:
        if not isinstance(claim, Mapping) or claim.get("authorized") is not True:
            continue
        provenance = str(claim.get("provenance") or "")
        status = str(claim.get("epistemic_status") or "")
        kind = (
            "gm_inference"
            if provenance == "gm_inference"
            else "player_hypothesis"
            if provenance == "player_hypothesis"
            else "unresolved"
            if status == "unresolved" and str(claim.get("relation_kind") or "") == "epistemic_status"
            else ""
        )
        if priorities.get(kind, 0) > chosen_priority:
            chosen = claim
            chosen_priority = priorities.get(kind, 0)
    if chosen is None:
        return False
    label = _clean(chosen.get("text"), limit=160)
    if not label:
        return False
    focus = read_discourse_focus(session)
    current = _scene_id_of(session, scene_id)
    focus[SLOT_CLAIM] = _slot(
        {
            "id": "claim_" + hashlib.sha1(label.lower().encode("utf-8")).hexdigest()[:10],
            "label": label,
            "kind": "claim",
            "scene_id": current or None,
            "turn_index": turn_index,
            "source": str(chosen.get("provenance") or "epistemic_status"),
            "epistemic_status": str(chosen.get("epistemic_status") or "unresolved"),
        }
    )
    session[DISCOURSE_FOCUS_KEY] = focus
    return True
