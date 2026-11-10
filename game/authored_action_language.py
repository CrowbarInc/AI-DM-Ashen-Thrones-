"""Match ordinary speech to currently available authored actions.

The match proposes an identifier. It does not change campaign state and it does
not apply consequences. Availability is rechecked, and the existing authored
executor remains the only writer.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any

PROVIDER_GATE = "ASHEN_AUTHORED_MATCH_PROVIDER"
_MAX_REQUESTS = 8
_MAX_TOKENS = 16000
_REQUESTS = 0
_TOKENS = 0
_TRACES: list[dict[str, Any]] = []
_CACHE: dict[str, dict[str, Any]] = {}
_FINGERPRINTS: list[tuple[str, list[str]]] | None = None
_REJECTED_PUBLICATIONS: list[dict[str, Any]] = []

_STOP = {
    "i", "we", "the", "a", "an", "to", "of", "my", "your", "our", "and", "at", "in",
    "on", "for", "me", "us", "it", "that", "this", "with", "from", "please", "will",
    "want", "like", "back", "return", "go", "head", "walk", "toward", "towards",
    "into", "here", "there", "just", "now", "then", "myself", "yourself",
}
_ANCHORS = {
    "trail", "track", "tracks", "print", "prints", "milestone", "watch", "guard",
    "guards", "patrol", "uncertain", "finding", "findings", "limit", "limits",
    "survey", "cinderwatch", "notice",
}
_ALLOWED_OBJECT = {
    "uncertain", "trail", "survey", "patrol", "watch", "limits", "limit", "findings",
    "finding", "tracks", "track", "prints", "print", "these", "this", "those", "guards", "guard",
}
_PROGRESS = re.compile(
    r"\b(?:what can i do(?: here)?|what are my options|what should i (?:investigate|do) next)\b",
    re.I,
)
_QUESTION = re.compile(
    r"^\s*(?:who|what|when|where|why|how|should|can|could|would|do|does|is|are|will)\b|\?",
    re.I,
)
# Established-knowledge questions belong to the memory owner, not the choice menu.
_MEMORY_QUESTION = re.compile(
    r"\bwhat\s+do\s+(?:i|we)\s+know\b|"
    r"\bwhat\s+(?:is|was)\s+(?:visible|known|discovered|learned|found)\b|"
    r"\bwhat\s+did\s+(?:i|we)\b|"
    r"\bremind\s+me\b",
    re.I,
)
# Scene and place questions are not requests to run an authored choice.
_ENVIRONMENT_QUESTION = re.compile(
    r"\b(?:notice board|what does the .+ say|what do i see|what can i see|what is here)\b",
    re.I,
)
_WORLD_QUESTION = re.compile(r"\b(?:where am i|where are we)\b", re.I)
# Speaking to someone is dialogue unless the utterance commits an authored choice.
_ASK_SPEECH = re.compile(r"\b(?:ask|speak to|speak with|talk to|talk with)\b", re.I)
_AUTHORED_COMMIT = re.compile(
    r"\b(?:survey|record|document|write down|warn the watch|"
    r"report(?:ed|ing)?\s+(?:the|my|these|this|our|uncertain))\b",
    re.I,
)
_NEGATION = re.compile(r"\b(?:don't|do not|won't|will not|not going to|never)\b", re.I)
_HYPOTHETICAL = re.compile(
    r"\b(?:what if|what would|what happens if|suppose|supposing|imagine if|hypothetically)\b",
    re.I,
)
_DISCUSSION = re.compile(
    r"\b(?:should i|was thinking|am thinking|i'm thinking|im thinking|considering whether|ought i)\b",
    re.I,
)
_CONDITIONAL = re.compile(r"\b(?:if|unless|otherwise|provided that)\b", re.I)
_QUOTE = re.compile(r"""^\s*['\"]|\b(?:he|she|they|the notice|the board)\s+(?:said|says|reads|wrote)\b""", re.I)
_EXAMINE = re.compile(r"\b(?:examine|inspect|read|check|study|look at)\b", re.I)


def traces() -> list[dict[str, Any]]:
    return list(_TRACES)


def provider_usage() -> dict[str, Any]:
    accepted = [row for row in _TRACES if row.get("provider") and row.get("accepted")]
    rejected = [row for row in _TRACES if row.get("provider") and not row.get("accepted")]
    return {
        "requests": _REQUESTS,
        "tokens": _TOKENS,
        "accepted": len(accepted),
        "rejected": len(rejected),
        "traces": traces(),
    }


def rejected_publications() -> list[dict[str, Any]]:
    return list(_REJECTED_PUBLICATIONS)


def _inner(scene) -> dict:
    if isinstance(scene, dict) and isinstance(scene.get("scene"), dict):
        return scene["scene"]
    return scene if isinstance(scene, dict) else {}


def _flags(world) -> dict:
    state = (world or {}).get("world_state") if isinstance(world, dict) else {}
    flags = state.get("flags") if isinstance(state, dict) else {}
    return flags if isinstance(flags, dict) else {}


def _place(scene) -> str:
    inner = _inner(scene)
    return str(inner.get("location") or inner.get("name") or inner.get("id") or "here")


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z]+", text.casefold()) if token not in _STOP and len(token) > 2}


def _status(action: dict, scene_id: str, session, world) -> str:
    if action.get("hidden") is True or str(action.get("visibility") or "") == "hidden":
        return "hidden"
    effect = action.get("consequence") if isinstance(action.get("consequence"), dict) else {}
    flags = _flags(world)
    own = [key for key, value in (effect.get("set_flags") or {}).items() if value is True]
    if own and all(flags.get(key) is True for key in own):
        return "completed"
    from game.affordances import _affordance_passes_conditions
    if _affordance_passes_conditions(action, scene_id, session or {}, world or {}):
        return "available"
    return "unavailable"


def discover(scene, session, world) -> list[dict[str, Any]]:
    """Current-scene authored choices only. Hidden rows stay out of the result."""
    from game.authored_consequences import enabled_for_session
    if not enabled_for_session(session or {}):
        return []
    inner = _inner(scene)
    scene_id = str(inner.get("id") or "")
    found = []
    for action in inner.get("actions") or []:
        if not isinstance(action, dict) or "consequence" not in action or not action.get("id"):
            continue
        status = _status(action, scene_id, session, world)
        if status == "hidden":
            continue
        found.append({
            "id": str(action["id"]),
            "label": str(action.get("label") or action["id"]),
            "status": status,
            "scene_id": scene_id,
            "conditions": action.get("conditions") if isinstance(action.get("conditions"), dict) else {},
            "consequence": action.get("consequence") if isinstance(action.get("consequence"), dict) else {},
        })
    return found


def _body(text: str) -> str:
    low = re.sub(r"\s+", " ", text or "").strip().casefold()
    low = re.sub(r"^(?:please\s+)?(?:i'll|i will|we'll|we will|i|we|let's|lets|let us)\s+(?:will\s+|want to\s+|would like to\s+|'d like to\s+)?", "", low)
    low = re.sub(r"^(?:will\s+|want to\s+)", "", low)
    return low.strip(" .!")


def _foreign_object(text: str) -> bool:
    match = re.match(r"(?:survey|report)\s+(?:(?:the|a|an|my)\s+)?(.+)$", _body(text), re.I)
    if not match:
        return False
    words = re.findall(r"[a-z]+", match.group(1))
    return not any(word in _ALLOWED_OBJECT for word in words)


def _lexical(text: str, action: dict) -> int:
    body = _body(text)
    label = action["label"].casefold().strip(" .!")
    if label and (label in body or body.startswith(label)):
        return 12
    overlap = _tokens(body) & _tokens(label)
    score = len(overlap)
    if action["id"] == "patrol_report" and re.search(r"\b(?:tell the watch|tell the guards|give (?:my |the )?report|report(?:ed|ing)?\s+(?:the\s+|these\s+|this\s+)?(?:uncertain\s+)?(?:trail|tracks|prints)|reported to the watch|(?:trail|tracks|prints)\b.*\bto the watch)\b", body):
        score += 4
    if action["id"] == "patrol_survey" and re.search(r"\b(?:survey|document|write down|make a note|note of)\b", body) and re.search(r"\b(?:survey|trail|tracks|prints|findings|milestone)\b", body):
        score += 3
    if action["id"] == "patrol_record_survey" and re.search(r"\b(?:record|document|write down|log|note)\b", body) and re.search(r"\b(?:survey|limits|findings)\b", body):
        score += 4
    if action["id"] == "patrol_warn_watch" and re.search(r"\b(?:warn the watch|give the watch|patrol report)\b", body):
        score += 4
    return score


def _boost(text: str, action: dict, rows: list[dict]) -> int:
    if action["status"] != "available":
        return 0
    body = _body(text)
    if re.search(r"\b(?:follow|pursue|chase|wait|look for|search for|determine)\b", body) and not re.search(
        r"\b(?:survey|record|document|note|write)\b", body
    ):
        return 0
    if not re.search(r"\b(?:survey|record|document|note|findings|tracks|trail)\b", body):
        return 0
    own = set((action.get("consequence") or {}).get("set_flags") or {})
    for other in rows:
        if other["id"] == action["id"] or other["status"] == "available":
            continue
        needed = set((other.get("conditions") or {}).get("requires_flags") or [])
        if own & needed:
            return 5
    return 0


def _reason_for(action: dict, rows: list[dict], place: str) -> str:
    labels = [row["label"] for row in rows if row["status"] == "available"]
    listed = "; ".join(labels[:4])
    tail = f" You can: {listed}." if listed else ""
    if action["status"] == "completed":
        return "You already did that. Nothing further was changed." + tail
    needed = (action.get("conditions") or {}).get("requires_flags") or []
    if needed:
        return "That follows a choice which is not completed yet." + tail
    return f"That choice cannot be taken here at {place}." + tail


def _speech(text: str) -> str:
    raw = text or ""
    if _PROGRESS.search(raw):
        return "progress"
    if _QUOTE.search(raw):
        return "quotation"
    if _NEGATION.search(raw):
        return "negation"
    if _HYPOTHETICAL.search(raw):
        return "hypothetical"
    if _DISCUSSION.search(raw):
        return "discussion"
    if _QUESTION.search(raw):
        return "question"
    if _CONDITIONAL.search(raw):
        return "conditional"
    return "action"


def _nonaction(kind: str, message: str, *, reason: str) -> dict[str, Any]:
    return {"kind": kind, "message": message, "reason": reason, "id": None}


def _physical_owns(text, session, scene, world) -> bool:
    try:
        from game.physical_adjudication import enabled, plan_physical
    except Exception:
        return False
    if not enabled(session):
        return False
    plan = plan_physical(text, session=session, scene=scene, world=world)
    return bool(plan and plan.get("mode") in {"interact", "answer", "clarify"} and plan.get("operation"))


def _foreign_scene(text: str, scene_id: str) -> dict | None:
    from game.authored_consequences import FIXTURE
    try:
        definitions = json.loads(FIXTURE.read_text(encoding="utf-8"))
    except Exception:
        return None
    body = _body(text)
    best = None
    for other_id, actions in definitions.items():
        if other_id == scene_id:
            continue
        for action in actions:
            label = str(action.get("label") or "").casefold().strip(" .!")
            if label and label in body:
                best = {"id": action.get("id"), "label": action.get("label"), "scene_id": other_id}
    return best


def propose(text, *, scene, world, session, invoke=None) -> dict[str, Any] | None:
    """Return a proposal, or None when ordinary adjudication should continue."""
    from game.authored_consequences import enabled_for_session
    raw = re.sub(r"\s+", " ", text or "").strip()
    if not raw or not enabled_for_session(session or {}):
        return None
    if _foreign_object(raw):
        return None
    rows = discover(scene, session, world)
    place = _place(scene)
    mode = _speech(raw)
    if mode == "progress":
        labels = [row["label"] for row in rows if row["status"] == "available"]
        facts = [str(item) for item in (_inner(scene).get("visible_facts") or [])[:2] if isinstance(item, str)]
        message = "You are at " + place + "."
        if facts:
            message += " Established in view: " + " ".join(facts)
        if labels:
            message += " Available choices: " + "; ".join(labels) + "."
        else:
            message += " No authored continuation is available. You can look at what is already here or speak to someone present."
        message += " Nothing was attempted."
        return _note(_nonaction("answer", message, reason="player_progress"), raw, rows)
    if _physical_owns(raw, session, scene, world):
        return None
    if mode == "question" and (
        _MEMORY_QUESTION.search(raw) or _ENVIRONMENT_QUESTION.search(raw) or _WORLD_QUESTION.search(raw)
    ):
        return None
    if _ASK_SPEECH.search(raw) and not _AUTHORED_COMMIT.search(raw):
        return None
    anchors = bool(_tokens(raw) & _ANCHORS) or any(row["label"].casefold() in _body(raw) for row in rows)
    if mode == "question" and anchors:
        from game.bounded_improvisation import focused_present_npc
        # An ordinary question to the person already in the conversation stays
        # in dialogue. A question that commits an authored choice does not.
        if focused_present_npc(session, scene, world) is not None and not _AUTHORED_COMMIT.search(raw):
            return None
    if mode in {"quotation", "negation", "hypothetical", "discussion", "question"} and anchors:
        if mode == "question":
            labels = [row["label"] for row in rows if row["status"] == "available"]
            message = "Nothing was attempted."
            if labels:
                message += " Available choices: " + "; ".join(labels) + "."
            else:
                message += " That is not available here yet."
        else:
            message = "Nothing was attempted. That was not taken as an action."
        return _note(_nonaction("answer" if mode == "question" else "decline", message, reason="not_an_action"), raw, rows)
    if mode == "conditional" and anchors:
        return _note(_nonaction(
            "decline",
            f"That depends on a condition, so nothing was attempted. You are still at {place}.",
            reason="conditional",
        ), raw, rows)
    if mode != "action":
        return None
    if re.search(r"\bfollow up on the patrol\b|\bcontinue the patrol\b", raw, re.I):
        open_rows = [row for row in rows if row["status"] == "available"]
        if len(open_rows) >= 2:
            return _note(_nonaction(
                "clarify",
                "Do you mean " + " or ".join(row["label"] for row in open_rows[:3]) + "? Nothing has been attempted.",
                reason="ambiguous",
            ), raw, rows)
    ranked = []
    for row in rows:
        score = _lexical(raw, row) + _boost(raw, row, rows)
        ranked.append((score, row))
    ranked.sort(key=lambda item: item[0], reverse=True)
    available = [(score, row) for score, row in ranked if row["status"] == "available"]
    scene_id = str(_inner(scene).get("id") or "")
    foreign = _foreign_scene(raw, scene_id)
    local_best = available[0][0] if available else 0
    if foreign and local_best < 8:
        return _note(_nonaction(
            "decline",
            f"That choice is not available in this place. You are still at {place}.",
            reason="wrong_scene",
        ), raw, rows)
    if len(available) >= 2 and available[0][0] >= 4 and available[1][0] >= 4 and available[0][0] - available[1][0] <= 1:
        lexical = sorted(((_lexical(raw, row), row) for _, row in available), key=lambda item: item[0], reverse=True)
        if lexical[0][0] >= 4 and lexical[0][0] - lexical[1][0] >= 2:
            available = lexical
        else:
            return _note(_nonaction(
                "clarify",
                "Do you mean " + available[0][1]["label"] + " or " + available[1][1]["label"] + "? Nothing has been attempted.",
                reason="ambiguous",
            ), raw, rows)
    if available and available[0][0] >= 4:
        return _note({
            "kind": "execute", "id": available[0][1]["id"], "label": available[0][1]["label"],
            "reason": "authored_choice", "message": "", "provider": False,
        }, raw, rows)
    blocked = [(score, row) for score, row in ranked if row["status"] in {"unavailable", "completed"} and score >= 6 and (not available or score > available[0][0])]
    if blocked:
        return _note(_nonaction("decline", _reason_for(blocked[0][1], rows, place), reason=blocked[0][1]["status"]), raw, rows)
    if available and 1 <= available[0][0] < 4 and (_tokens(raw) & _ANCHORS):
        assisted = _provider(raw, available, session=session, scene=scene, invoke=invoke)
        if assisted is not None:
            return _note(assisted, raw, rows)
    if not rows:
        return None
    return None


def _note(proposal: dict, text: str, rows: list[dict]) -> dict:
    _TRACES.append({
        "text": text,
        "kind": proposal.get("kind"),
        "id": proposal.get("id"),
        "reason": proposal.get("reason"),
        "provider": bool(proposal.get("provider")),
        "accepted": proposal.get("kind") == "execute",
        "candidates": [{"id": row["id"], "status": row["status"]} for row in rows],
    })
    return proposal


def _cache_key(text: str, rows: list[tuple[int, dict]]) -> str:
    ident = "|".join(f"{score}:{row['id']}" for score, row in rows)
    return hashlib.sha256((text.casefold() + "|" + ident).encode()).hexdigest()


def _provider(text, available, *, session, scene, invoke) -> dict | None:
    global _REQUESTS, _TOKENS
    key = _cache_key(text, available)
    cached = _CACHE.get(key)
    if cached is not None:
        return dict(cached)
    if invoke is None and os.environ.get(PROVIDER_GATE) != "1":
        return None
    if invoke is None and os.environ.get("ASHEN_DISABLE_PROVIDER_CALLS") == "1":
        return None
    if _REQUESTS >= _MAX_REQUESTS or _TOKENS >= _MAX_TOKENS:
        _TRACES.append({"text": text, "provider": True, "accepted": False, "reason": "budget"})
        return None
    started = time.perf_counter()
    retries = 0
    raw = None
    while retries < 2:
        try:
            if invoke is not None:
                raw = invoke(text, [row["id"] for _, row in available])
            else:
                raw = _live_provider(text, available)
            break
        except Exception as exc:
            retries += 1
            raw = {"error": type(exc).__name__}
            if retries >= 2:
                _TRACES.append({"text": text, "provider": True, "accepted": False, "reason": type(exc).__name__, "retries": retries})
                return None
    verdict = _validate_provider(raw, available)
    verdict["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
    verdict["retries"] = retries
    if verdict.get("kind") == "execute":
        _CACHE[key] = dict(verdict)
    return verdict


def _validate_provider(raw, available) -> dict:
    ids = {row["id"]: row for _, row in available}
    if not isinstance(raw, dict):
        return {"kind": "decline", "id": None, "message": "That could not be matched to an available choice. Nothing was attempted.", "reason": "malformed", "provider": True}
    chosen = str(raw.get("action_id") or "")
    if chosen in {"", "none", "null"}:
        return {"kind": None, "reason": "no_provider_match", "provider": True, "message": ""}
    if chosen not in ids:
        return {"kind": "decline", "id": None, "message": "That choice is not available here. Nothing was attempted.", "reason": "rejected_identifier", "provider": True}
    if raw.get("ambiguity") in {"ambiguous", "unclear"}:
        labels = " or ".join(row["label"] for _, row in available[:3])
        return {"kind": "clarify", "id": None, "message": f"Do you mean {labels}? Nothing has been attempted.", "reason": "provider_ambiguous", "provider": True}
    try:
        confidence = float(raw.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0
    if confidence < 0.6:
        return {"kind": None, "reason": "low_confidence", "provider": True, "message": ""}
    row = ids[chosen]
    return {"kind": "execute", "id": row["id"], "label": row["label"], "reason": "provider_match", "message": "", "provider": True, "confidence": confidence}


def _live_provider(text, available) -> dict:
    global _REQUESTS, _TOKENS
    from openai import OpenAI
    from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
    from game.provider_budget import admit_request, sdk_retry_options
    shown = [{"id": row["id"], "label": row["label"]} for _, row in available]
    schema = {
        "type": "object", "additionalProperties": False,
        "required": ["action_id", "confidence", "ambiguity"],
        "properties": {
            "action_id": {"type": "string"},
            "confidence": {"type": "number"},
            "ambiguity": {"type": "string"},
        },
    }
    messages = [
        {"role": "system", "content": "Choose one available action id that the player is committing to now, or none. Do not invent ids. Do not say the action succeeded."},
        {"role": "user", "content": json.dumps({"utterance": text, "available": shown})},
    ]
    attempt = admit_request(purpose="authored_action_match", owner="authored_action_language", model=DEFAULT_MODEL_NAME, estimated_input=500, max_output=80)
    if attempt.refusal:
        raise RuntimeError("provider_admission_refused")
    response = attempt.dispatch(
        OpenAI(api_key=get_openai_api_key(), timeout=30, **sdk_retry_options()).responses.create,
        model=DEFAULT_MODEL_NAME, input=messages, max_output_tokens=80,
        text={"format": {"type": "json_schema", "name": "authored_match", "strict": True, "schema": schema}},
    )
    usage = response.usage
    _REQUESTS += 1
    _TOKENS += int(getattr(usage, "total_tokens", 0) or 0)
    attempt.finish({
        "purpose": "authored_action_match", "sent": True, "model": getattr(response, "model", DEFAULT_MODEL_NAME),
        "request_id": getattr(response, "id", ""), "input_tokens": getattr(usage, "input_tokens", 0),
        "output_tokens": getattr(usage, "output_tokens", 0), "total_tokens": getattr(usage, "total_tokens", 0),
    })
    return json.loads(response.output_text)


def decision_for(text, *, scene, world, session, invoke=None):
    """Conversational decision for a proposal. None leaves the existing owners in place."""
    proposal = propose(text, scene=scene, world=world, session=session, invoke=invoke)
    if not proposal or proposal.get("kind") in {None, ""}:
        return None
    from game.conversational_orchestration import ConversationalDecision, ConversationalDecisionCategory as C, _operation_record
    kind = proposal["kind"]
    if kind == "execute":
        return ConversationalDecision(
            category=C.EXECUTE, primary_intention=text, intent_family="player_initiative",
            proposed_operation="CUSTOM", proposed_target=proposal["id"],
            proposed_record=_operation_record(operation="CUSTOM", target_id=proposal["id"], player_text=text),
            requires_authoritative_execution=True, confidence=0.9, reason="initiative_authored_choice",
        )
    category = {"clarify": C.CLARIFY, "answer": C.ANSWER}.get(kind, C.DECLINE)
    return ConversationalDecision(
        category=category, primary_intention=text, intent_family="player_initiative",
        reason="initiative_" + str(proposal.get("reason") or kind),
        player_facing_text=proposal.get("message") or "Nothing was attempted.",
        confidence=0.4 if category == C.CLARIFY else 0.8,
    )


def authored_examination(text, session, scene, world) -> dict[str, Any] | None:
    """Run one authored inspect through the existing exploration resolver."""
    if not _EXAMINE.search(text or ""):
        return None
    low = (text or "").casefold()
    hits = []
    for item in _inner(scene).get("interactables") or []:
        if not isinstance(item, dict) or not item.get("reveals_clue"):
            continue
        names = [item.get("label"), str(item.get("id") or "").replace("_", " "), *(item.get("aliases") or [])]
        if any(name and str(name).casefold() in low and len(str(name)) >= 4 for name in names):
            hits.append(item)
    if len(hits) != 1:
        return None
    item = hits[0]
    from game.exploration import resolve_exploration_action
    resolved = resolve_exploration_action(
        scene, session, world,
        {"id": item.get("id"), "type": "investigate", "label": item.get("label") or item.get("id"),
         "prompt": text, "target_id": item.get("id")},
        raw_player_text=text,
    )
    if not isinstance(resolved, dict):
        return None
    if resolved.get("kind") == "discover_clue" and resolved.get("clue_text"):
        from game.clues import apply_authoritative_clue_discovery
        from game.storage import mark_interactable_resolved
        scene_id = str(_inner(scene).get("id") or "")
        apply_authoritative_clue_discovery(
            session, scene_id, clue_id=resolved.get("clue_id"), clue_text=resolved.get("clue_text"),
            discovered_clues=resolved.get("discovered_clues"), world=world,
        )
        if item.get("id"):
            mark_interactable_resolved(session, scene_id, str(item.get("id")))
        return {
            "ok": True, "status": "SUCCEEDED", "mutation": True, "message": resolved.get("clue_text"),
            "clue_id": resolved.get("clue_id"), "clue_text": resolved.get("clue_text"),
            "discovered_clues": list(resolved.get("discovered_clues") or []),
            "interactable_id": item.get("id"),
        }
    if resolved.get("kind") == "already_searched":
        return {"ok": True, "status": "SUCCEEDED", "mutation": False, "message": "You find nothing new there."}
    return None


def scene_publication_replacement(text: str, *, session, resolution, scene=None) -> str | None:
    """Replace narration that contradicts the committed scene, place, or object state."""
    raw = re.sub(r"\s+", " ", text or "").strip()
    if len(raw) < 40 or not isinstance(session, dict):
        return None
    if isinstance(resolution, dict) and (
        resolution.get("resolved_transition") is True
        or (isinstance(resolution.get("state_changes"), dict) and resolution["state_changes"].get("scene_changed"))
    ):
        return None
    active = str(session.get("active_scene_id") or "")
    disclosed = []
    if isinstance(resolution, dict):
        disclosed.append(str(resolution.get("clue_text") or ""))
        disclosed.extend(str(item) for item in (resolution.get("discovered_clues") or []) if isinstance(item, str))
    if any(len(clue) > 24 and clue.casefold() in raw.casefold() for clue in disclosed):
        return None
    from game.narrative_consistency import publication_conflict
    conflict = publication_conflict(raw, session=session, resolution=resolution, scene=scene)
    if conflict:
        return _replacement(active, raw, conflict)
    low = raw.casefold()
    for scene_id, facts in _fingerprints():
        if scene_id == active:
            continue
        for fact in facts:
            if fact in low:
                return _replacement(active, raw, "foreign_scene_fact:" + scene_id)
    return None


def _replacement(active: str, original: str, reason: str) -> str:
    place = active.replace("_", " ") or "your current place"
    try:
        from game.storage import load_scene
        loaded = load_scene(active) if active else {}
        place = str((loaded.get("scene") or {}).get("location") or place)
    except Exception:
        pass
    message = f"You are still at {place}. No travel was completed, so another place's description was not published."
    _REJECTED_PUBLICATIONS.append({"reason": reason, "active_scene_id": active, "rejected_excerpt": original[:240]})
    return message


def _fingerprints() -> list[tuple[str, list[str]]]:
    global _FINGERPRINTS
    if _FINGERPRINTS is not None:
        return _FINGERPRINTS
    rows = []
    try:
        from game.storage import list_scene_ids, load_scene
        for scene_id in list_scene_ids():
            try:
                inner = (load_scene(scene_id) or {}).get("scene") or {}
            except Exception:
                continue
            facts = []
            for item in list(inner.get("opening_seed_facts") or []) + [inner.get("summary") or ""]:
                if isinstance(item, str) and len(item.strip()) >= 48:
                    facts.append(item.strip().casefold())
            rows.append((str(scene_id), facts))
    except Exception:
        rows = []
    _FINGERPRINTS = rows
    return rows
