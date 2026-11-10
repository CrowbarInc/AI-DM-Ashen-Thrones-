"""Route mixed player intent through the existing owners.

Physical sequences stay in physical adjudication. This module only steps in
when one utterance crosses dialogue, observation, investigation, and physical
action, or when the player asks for an ordinary action those owners already
know how to refuse or describe. The provider may word a committed result or
an authorized NPC line. It does not commit state.
"""
from __future__ import annotations

import hashlib
import os
import re
import threading
import time
from typing import Any

SPEECH_GATE = "ASHEN_BOUNDED_SPEECH"
NARRATION_GATE = "ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION"

_USAGE: list[dict[str, Any]] = []
_LANES: dict[str, "_Lane"] = {}
_LANE_GUARD = threading.Lock()


def presentation_usage() -> dict[str, Any]:
    accepted = [row for row in _USAGE if row.get("decision") == "accepted"]
    rejected = [row for row in _USAGE if row.get("decision") == "rejected"]
    tokens = sum(int(row.get("tokens") or 0) for row in _USAGE)
    return {
        "requests": len(_USAGE),
        "tokens": tokens,
        "accepted": len(accepted),
        "rejected": len(rejected),
        "published": sum(1 for row in accepted if row.get("published")),
        "fallbacks": sum(1 for row in _USAGE if row.get("decision") != "accepted"),
        "log": list(_USAGE),
    }


def _note(kind, decision, *, text, reasons=None, tokens=0, latency_ms=0, published=False):
    _USAGE.append({
        "kind": kind, "decision": decision, "text": text, "reasons": list(reasons or []),
        "tokens": tokens, "latency_ms": latency_ms, "published": published, "committed_by_provider": False,
    })


class _Lane:
    def __init__(self):
        self.condition = threading.Condition()
        self.readers = 0
        self.writer = False
        self.writers_waiting = 0
        self.issued = 0
        self.serving = 0
        self.inflight: dict[str, dict[str, Any]] = {}
        self.completed: dict[str, Any] = {}


def _lane(scope: str) -> _Lane:
    with _LANE_GUARD:
        lane = _LANES.get(scope)
        if lane is None:
            lane = _Lane()
            _LANES[scope] = lane
        return lane


class ordered_turn:
    """FIFO mutations for one store. Other stores do not wait on this lane."""

    def __init__(self, scope: str, *, mutating: bool, request_key: str | None = None, text: str = ""):
        self.scope = str(scope or "default")
        self.mutating = mutating
        self.request_key = (request_key or "").strip() or None
        self.text_key = "text:" + hashlib.sha256((text or "").encode()).hexdigest() if mutating and text else None
        self.duplicate = False
        self.result = None
        self._lane = None
        self._held = False
        self._ticket = None
        self._waiting = None
        self._box = None

    def __enter__(self):
        lane = _lane(self.scope)
        self._lane = lane
        keys = [key for key in (self.request_key, self.text_key) if key]
        with lane.condition:
            for key in keys:
                if key in lane.completed and self.request_key:
                    self.duplicate = True
                    self.result = lane.completed[key]
                    return self
            for key in keys:
                box = lane.inflight.get(key)
                if box is not None:
                    waiter = box
                    break
            else:
                waiter = None
            if waiter is not None:
                self._waiting = waiter
            else:
                self._waiting = None
                if self.mutating:
                    self._ticket = lane.issued
                    lane.issued += 1
                    lane.writers_waiting += 1
                    box = {"result": None, "error": None, "ready": threading.Event()}
                    for key in keys:
                        lane.inflight[key] = box
                    self._box = box
                else:
                    self._box = None
        if self._waiting is not None:
            self._waiting["ready"].wait()
            if self._waiting.get("error") is not None:
                raise self._waiting["error"]
            self.duplicate = True
            self.result = self._waiting.get("result")
            return self
        with lane.condition:
            if self.mutating:
                while lane.writer or lane.readers or self._ticket != lane.serving:
                    lane.condition.wait()
                lane.writers_waiting -= 1
                lane.writer = True
                lane.serving += 1
            else:
                while lane.writer or lane.writers_waiting:
                    lane.condition.wait()
                lane.readers += 1
        self._held = True
        return self

    def __exit__(self, exc_type, exc, tb):
        lane = self._lane
        if lane is None or self._waiting is not None or not self._held:
            return False
        with lane.condition:
            if self.mutating:
                lane.writer = False
                box = getattr(self, "_box", None)
                if box is not None:
                    box["result"] = self.result
                    box["error"] = exc
                    box["ready"].set()
                if self.request_key and exc is None:
                    lane.completed[self.request_key] = self.result
                    if len(lane.completed) > 32:
                        lane.completed.pop(next(iter(lane.completed)))
                for key in (self.request_key, self.text_key):
                    if key:
                        lane.inflight.pop(key, None)
            else:
                lane.readers = max(0, lane.readers - 1)
            lane.condition.notify_all()
        return False


def _inner(scene):
    if isinstance(scene, dict) and isinstance(scene.get("scene"), dict):
        return scene["scene"]
    return scene if isinstance(scene, dict) else {}


def _split(text: str) -> list[str]:
    shielded = re.sub(r"\bwait and watch\b", "wait and_watch", text, flags=re.I)
    parts = re.split(
        r"\s*(?:;|,\s+then\s+|\s+and then\s+|\s+then\s+|,\s+and\s+|\s+and\s+|"
        r",\s+(?=(?:approach|ask|look|examine|inspect|introduce|thank|greet|move|open|wait|continue|step|check)\b))\s*",
        shielded.strip(),
        flags=re.I,
    )
    return [part.replace("and_watch", "and watch").strip(" ,") for part in parts if part.strip(" ,")]


def _domain(text: str) -> str:
    low = text.casefold()
    if re.search(r"\b(?:ask|greet|greeting|hello|hi|introduce|thank|thanks|goodbye|farewell|end the conversation|who are you|what concerns|tell me|say to)\b", low):
        return "dialogue"
    if re.search(r"\b(?:look around|looking around|look about|what do i see|take in the|wait and watch|watch the road)\b", low):
        return "observation"
    if re.search(r"\b(?:follow|pursue)\b", low) and re.search(r"\b(?:tracks?|prints|trail)\b", low):
        return "observation"
    if re.search(r"\b(?:look for|search for|signs of|more closely|offer to help|inspect the tracks|examine the tracks|read the)\b", low):
        return "investigation"
    if re.search(r"\b(?:seem|nervous|worried|demeanor|manner)\b", low):
        return "observation"
    from game.physical_adjudication import _operation
    if _operation(text) or re.search(r"\b(?:approach|step back|move away|walk away|leave|continue toward|go over to)\b", low):
        return "physical"
    if re.search(r"\b(?:examine|inspect|look at|check|search|study)\b", low):
        return "investigation"
    return "unsupported"


def _social_or_physical(text, session, scene, world):
    domain = _domain(text)
    if domain != "physical":
        return domain
    if not re.search(r"\b(?:approach|step back|move away|walk away|leave|go over to|walk over to|step up to)\b", text, re.I):
        return domain
    from game.physical_adjudication import _named, _objects
    if _named(text, _objects(session, scene)):
        return domain
    if _npc_from_text(text, session, scene, world, persist=False) is not None:
        return "social"
    return domain


def _single_patterns(text, session, scene, world):
    low = text.casefold()
    if re.search(r"\b(?:wait and watch|watch the road)\b", low):
        return {"mode": "answer", "id": None, "integrated": True, "mutation": False,
                "message": "You wait and watch. Nothing new approaches, and no encounter is created."}
    if re.search(r"\b(?:signs of a struggle|look for signs)\b", low):
        return {"mode": "answer", "id": None, "integrated": True, "mutation": False,
                "message": "No signs of a struggle are established here. Nothing was added."}
    if re.search(r"\b(?:offer to help|help search)\b", low):
        return {"mode": "answer", "id": None, "integrated": True, "mutation": False,
                "message": "You offer to help. No search party, duty, or reward is created. You can look at what is already here."}
    if re.search(r"\b(?:tracks|footprints|prints)\b", low) and re.search(r"\b(?:inspect|examine|closer|closely)\b", low):
        facts = " ".join(str(item) for item in (_inner(scene).get("visible_facts") or []))
        if not re.search(r"\b(?:tracks|footprints|prints)\b", facts, re.I):
            return {"mode": "decline", "id": None, "integrated": True, "mutation": False,
                    "message": "Those tracks are not established in this scene. Nothing was added."}
    return None


def plan_integrated(text, *, session, scene, world):
    """Read-only. Returns None when the physical or NPC owner should keep the utterance."""
    from game.physical_adjudication import enabled, _question
    if not enabled(session) or not isinstance(session, dict):
        return None
    raw = re.sub(r"\s+", " ", text or "").strip()
    if not raw:
        return None
    if re.fullmatch(r"(?:please\s+)?(?:ask|speak(?:\s+with)?|talk(?:\s+to)?)\s+(?:them|him|her)[.!?]*", raw, re.I) or re.fullmatch(
        r"(?:please\s+)?(?:look\s+over\s+there|move\s+that)[.!?]*", raw, re.I,
    ):
        return {
            "mode": "clarify", "id": None, "integrated": True, "mutation": False,
            "message": "Which person, object, or direction do you mean? Nothing has been attempted.",
        }
    if _question(raw) and len(_split(raw)) <= 1:
        if re.search(r"\b(?:seem|nervous|worried|demeanor|manner)\b", raw, re.I):
            npc = _npc_from_text(raw, session, scene, world, persist=False)
            if npc is not None:
                return {"mode": "answer", "id": None, "integrated": True, "mutation": False,
                        "message": f"{npc.get('name') or npc.get('label')} seems {npc.get('demeanor') or 'ordinary'}. Nothing establishes a hidden motive."}
        if _continues_conversation(raw, session, scene, world):
            return _dialogue_plan(raw, session, scene)
        return None
    if len(_split(raw)) <= 1 and _continues_conversation(raw, session, scene, world):
        return _dialogue_plan(raw, session, scene)
    pieces = _split(raw)
    if len(pieces) <= 1 and re.search(r"\b(?:seem|nervous|worried|demeanor|manner)\b", raw, re.I):
        npc = _npc_from_text(raw, session, scene, world, persist=False)
        if npc is not None:
            return {"mode": "answer", "id": None, "integrated": True, "mutation": False,
                    "message": f"{npc.get('name') or npc.get('label')} seems {npc.get('demeanor') or 'ordinary'}. Nothing establishes a hidden motive."}
    if len(pieces) <= 1:
        single = _single_patterns(raw, session, scene, world)
        if single is not None:
            return single
        if _authored_target(raw, scene):
            return None
    if len(pieces) > 3:
        return {"mode": "clarify", "id": None, "integrated": True, "mutation": False,
                "message": "That request names more than three actions. Say which three to resolve first. Nothing has been attempted."}
    domains = [_social_or_physical(piece, session, scene, world) for piece in pieces]
    if len(set(domains)) == 1 and domains[0] == "physical":
        if len(pieces) == 1:
            from game.physical_adjudication import plan_physical
            if plan_physical(raw, session=session, scene=scene, world=world) is None and re.search(r"\b(?:approach|push|climb)\b", raw, re.I):
                return {"mode": "decline", "id": None, "integrated": True, "mutation": False,
                        "message": "That is not established here. Nothing has been changed."}
        return None
    if not any(domain in {"dialogue", "observation", "investigation", "social"} for domain in domains):
        return None
    sid = str(_inner(scene).get("id") or "")
    ident = "mix_" + hashlib.sha256(f"{session.get('campaign_run_id')}|{sid}|{raw.casefold()}".encode()).hexdigest()[:16]
    steps = []
    for index, (piece, domain) in enumerate(zip(pieces, domains)):
        steps.append({
            "step_id": f"m{index + 1}", "text": piece, "domain": domain, "status": "PROPOSED",
            "depends_on": [f"m{index}"] if index and domain == "dialogue" and domains[index - 1] == "physical" else [],
        })
    return {
        "mode": "interact", "id": ident, "integrated": True, "physical": False, "mutation": True,
        "category": "A", "operation": "sequence", "steps": steps, "message": "",
    }


def _continues_conversation(text, session, scene, world) -> bool:
    """Ordinary follow-up to the person already in the conversation.

    A notice, a location question, and the player's own memory stay with those owners.
    """
    low = text.casefold()
    if re.search(
        r"\b(?:notice board|where am i|where are we|what do i see|what can i see|what is here|"
        r"what (?:do|did|have) (?:i|we) know|remind me)\b",
        low,
    ):
        return False
    if re.search(
        r"\b(?:who are you|what do you|when did you|do you think|have you|you know|"
        r"you hear|about that|about them|something happened|what about|again|"
        r"mentioned|what else|you said|you told me|"
        r"hidden|secret|payroll|reward|quest|where is the|where did they|what happened to)\b",
        low,
    ):
        from game.bounded_improvisation import focused_present_npc
        return focused_present_npc(session, scene, world) is not None
    return False


def _dialogue_plan(raw, session, scene):
    sid = str(_inner(scene).get("id") or "")
    ident = "mix_" + hashlib.sha256(f"{session.get('campaign_run_id')}|{sid}|{raw.casefold()}".encode()).hexdigest()[:16]
    return {
        "mode": "interact", "id": ident, "integrated": True, "physical": False, "mutation": True,
        "category": "A", "operation": "sequence",
        "steps": [{"step_id": "m1", "text": raw, "domain": "dialogue", "status": "PROPOSED", "depends_on": []}],
        "message": "",
    }


def _authored_target(text, scene) -> bool:
    words = set(re.findall(r"[a-z]{4,}", text.casefold()))
    for item in _inner(scene).get("interactables") or []:
        if not isinstance(item, dict):
            continue
        names = [str(item.get("label") or ""), str(item.get("id") or "").replace("_", " ")]
        names.extend(str(alias) for alias in item.get("aliases") or [])
        for name in names:
            tokens = set(re.findall(r"[a-z]{4,}", name.casefold()))
            if tokens and tokens <= words:
                return True
    return False


def _npc_in_scene(row, scene_id) -> bool:
    if not isinstance(row, dict):
        return False
    scene_mark = str(row.get("scene_id") or "")
    location = str(row.get("location") or "")
    current = str(scene_id or "")
    if scene_mark and current and scene_mark != current:
        return False
    if location and current and location != current:
        return False
    return True


def remember_interlocutor(session, npc, scene, player_text, spoken) -> None:
    """Record the minimum authoritative conversation state. Prose is not world truth."""
    if not isinstance(session, dict) or not isinstance(npc, dict) or not npc.get("id"):
        return
    from game.bounded_improvisation import ensure_bounded_improvisation_ledger
    ledger = ensure_bounded_improvisation_ledger(session)
    ending = bool(re.search(r"\b(?:goodbye|farewell|end the conversation|turn away)\b", player_text or "", re.I))
    scene_id = _inner(scene).get("id")
    if ending:
        ledger["npc_focus"] = None
    else:
        ledger["npc_focus"] = npc["id"]
    conv = session.setdefault("conversational_context", {})
    if not isinstance(conv, dict):
        return
    recent = [item for item in (conv.get("recent_exchange") or []) if isinstance(item, dict)]
    recent.append({"npc_id": npc["id"], "player": player_text, "response": spoken})
    slot = {
        "npc_id": None if ending else npc["id"],
        "scene_id": scene_id,
        "campaign_id": session.get("campaign_run_id"),
        "status": "ended" if ending else "active",
        "last_player_utterance": player_text,
        "last_npc_response": spoken,
    }
    conv["recent_exchange"] = recent[-6:]
    conv["active_interlocutor"] = slot
    from game.social import set_active_interaction_target
    from game.interaction_context import clear_stale_social_interlocutor_continuity
    if ending:
        clear_stale_social_interlocutor_continuity(session)
    else:
        set_active_interaction_target(session, str(npc["id"]), kind="social")


def _facts(scene) -> list[str]:
    return [str(item) for item in (_inner(scene).get("visible_facts") or []) if isinstance(item, str)]


def _npc_from_text(text, session, scene, world, persist=True):
    from game.bounded_improvisation import LEDGER_KEY, dynamic_npcs
    low = text.casefold()
    sid = _inner(scene).get("id")
    rows = []
    for entry in dynamic_npcs(session, sid):
        rows.append(entry)
    ledger = session.get(LEDGER_KEY) if isinstance(session.get(LEDGER_KEY), dict) else {}
    addressed = ledger.get("addressed_npcs") if isinstance(ledger.get("addressed_npcs"), dict) else {}
    for row in addressed.values():
        if isinstance(row, dict) and (not row.get("scene_id") or row.get("scene_id") == sid):
            rows.append(row)
    for item in _inner(scene).get("addressables") or []:
        if not isinstance(item, dict):
            continue
        roles = [str(role) for role in item.get("address_roles") or []]
        rows.append({
            "id": item.get("id"), "name": item.get("name") or item.get("id"),
            "label": str(item.get("name") or "person").casefold(),
            "role": roles[0] if roles else "person", "appearance": "ordinary clothes",
            "demeanor": "matter-of-fact", "social_receipts": [], "aliases": list(item.get("aliases") or []) + roles,
        })
    for npc in (world or {}).get("npcs") or []:
        if isinstance(npc, dict) and (not npc.get("location") or npc.get("location") == sid):
            rows.append(npc)

    def mentions(row):
        names = [row.get("name"), row.get("label"), row.get("role"), *(row.get("aliases") or [])]
        return any(value and re.search(r"(?<!\w)" + re.escape(str(value).casefold()) + r"(?!\w)", low) for value in names)

    matched = []
    seen = set()
    for row in rows:
        ident = row.get("id")
        if mentions(row) and ident not in seen:
            seen.add(ident)
            matched.append(row)
    scene_id = str(_inner(scene).get("id") or (session or {}).get("active_scene_id") or "")
    world_local = [row for row in matched if str(row.get("location") or "") == scene_id]
    chosen = None
    if len(world_local) == 1:
        chosen = world_local[0]
    elif len(matched) == 1:
        chosen = matched[0]
    elif not matched:
        focus = str((ledger or {}).get("npc_focus") or "")
        follow = bool(
            re.search(r"\b(?:he|she|they|them|him|her)\b", low)
            or re.search(r"\b(?:introduce|greet|thank|hello|ask|tell|goodbye|farewell|end the conversation)\b", low)
            or re.search(
                r"\b(?:who are you|what do you|when did you|do you think|have you|you know|you hear|what about|again|"
                r"mentioned|what else|you said|you told me|"
                r"hidden|secret|payroll|reward|quest|where is the|where did they|what happened to)\b",
                low,
            )
        )
        scene_question = bool(re.search(
            r"\b(?:notice board|where am i|where are we|what do i see|what can i see|what is here|"
            r"what (?:do|did|have) (?:i|we) know|remind me)\b",
            low,
        ))
        if focus and follow and not scene_question:
            chosen = next((row for row in rows if row.get("id") == focus and _npc_in_scene(row, sid)), None)
    if chosen is None:
        return None
    return _persist_npc(session, chosen) if persist else chosen


def _persist_npc(session, row):
    from game.bounded_improvisation import ensure_bounded_improvisation_ledger
    ledger = ensure_bounded_improvisation_ledger(session)
    store = ledger.setdefault("addressed_npcs", {})
    current = store.get(row.get("id"))
    if isinstance(current, dict):
        return current
    record = {
        "id": row.get("id"), "name": row.get("name") or row.get("label"),
        "label": row.get("label") or row.get("name"), "role": row.get("role") or "person",
        "appearance": row.get("appearance") or "ordinary clothes",
        "demeanor": row.get("demeanor") or "matter-of-fact",
        "social_receipts": list(row.get("social_receipts") or []),
        "scene_id": row.get("scene_id") or row.get("location") or (session or {}).get("active_scene_id"),
        "location": row.get("location") or "",
        "campaign_id": row.get("campaign_id") or (session or {}).get("campaign_run_id"),
    }
    store[record["id"]] = record
    return record


def _dialogue(text, session, scene, world):
    npc = _npc_from_text(text, session, scene, world)
    if npc is None:
        return {"ok": False, "status": "UNSUPPORTED", "mutation": False,
                "message": "No matching person is established here, so that conversation was not started."}
    from game.expressive_dialogue import background_conversation
    spoken = background_conversation(npc, session=session, scene=scene, player_text=text)
    remember_interlocutor(session, npc, scene, text, spoken)
    audit = session.get("last_background_expression") if isinstance(session.get("last_background_expression"), dict) else {}
    adopted = bool(audit.get("adopted"))
    attempt = audit.get("attempt") if isinstance(audit.get("attempt"), dict) else {}
    usage = attempt.get("usage") if isinstance(attempt.get("usage"), dict) else {}
    _note("dialogue", "accepted" if adopted else "rejected", text=spoken,
          reasons=(audit.get("validation") or {}).get("reasons") if isinstance(audit.get("validation"), dict) else [audit.get("reason")],
          tokens=int(usage.get("total_tokens") or 0), latency_ms=float(attempt.get("latency_ms") or 0), published=adopted)
    return {"ok": True, "status": "SUCCEEDED", "mutation": True, "message": spoken, "live_dialogue": adopted, "npc_id": npc["id"]}


def _observation(text, scene):
    low = text.casefold()
    if re.search(r"\b(?:seem|nervous|worried|demeanor|manner)\b", low):
        return {"ok": True, "status": "SUCCEEDED", "mutation": False,
                "message": "Only the established manner is visible. No hidden motive is known."}
    facts = _facts(scene)
    if not facts:
        return {"ok": True, "status": "SUCCEEDED", "mutation": False,
                "message": "Nothing further is established in view."}
    return {"ok": True, "status": "SUCCEEDED", "mutation": False,
            "message": "You look around. " + " ".join(facts[:3])}


def _investigation(text, scene):
    low = text.casefold()
    facts = _facts(scene)
    if re.search(r"\b(?:struggle|tracks|footprints)\b", low):
        blob = " ".join(facts)
        if not re.search(r"\b(?:struggle|tracks|footprints|prints)\b", blob, re.I):
            return {"ok": False, "status": "UNSUPPORTED", "mutation": False,
                    "message": "That evidence is not established here. Nothing was discovered."}
    words = set(re.findall(r"[a-z]{4,}", low))
    matched = [fact for fact in facts if words & set(re.findall(r"[a-z]{4,}", fact.casefold()))]
    if matched:
        return {"ok": True, "status": "SUCCEEDED", "mutation": False, "message": matched[0]}
    return {"ok": True, "status": "SUCCEEDED", "mutation": False,
            "message": "Nothing further is established about that. No hidden object or passage was added."}


def _physical(text, session, scene, world, character):
    low = text.casefold()
    npc = _npc_from_text(text, session, scene, world) if re.search(r"\b(?:approach|greet|leave|away|toward)\b", low) else None
    if re.search(r"\b(?:approach|go over to|walk over to|step up to)\b", low):
        npc = npc or _npc_from_text(text, session, scene, world)
        if npc is not None:
            from game.physical_adjudication import _ledger
            ledger = _ledger(session)
            ledger["position"] = {"kind": "beside", "target_id": npc["id"], "scene_id": _inner(scene).get("id"), "label": npc.get("name")}
            ledger["npc_focus"] = npc["id"]
            return {"ok": True, "status": "SUCCEEDED", "mutation": True,
                    "message": f"You move beside {npc.get('name') or 'them'}."}
    if re.search(r"\b(?:move away|walk away|leave|step back)\b", low):
        from game.physical_adjudication import _ledger
        ledger = _ledger(session)
        current = dict(ledger.get("position") or {})
        ledger["position"] = {"kind": "back", "target_id": current.get("target_id"), "scene_id": _inner(scene).get("id"),
                              "label": current.get("label")}
        return {"ok": True, "status": "SUCCEEDED", "mutation": True,
                "message": "You move away. No new place was created."}
    from game.physical_adjudication import commit_physical, plan_physical
    plan = plan_physical(text, session=session, scene=scene, world=world)
    if not plan:
        return {"ok": False, "status": "UNSUPPORTED", "mutation": False,
                "message": "That part is not supported here. It was not carried out."}
    if plan.get("mode") != "interact":
        return {"ok": plan.get("mode") == "answer", "status": str(plan.get("mode") or "FAILED").upper(),
                "mutation": False, "message": plan.get("message") or "That part was not carried out."}
    result = commit_physical(scene, session, world, {"id": plan["id"], "target_id": plan["id"]},
                             prompt=text, action_id=plan["id"], label="integrated", character=character or {})
    if not result:
        return {"ok": False, "status": "FAILED", "mutation": False, "message": "That part was not carried out."}
    return {"ok": bool(result.get("success")), "status": "SUCCEEDED" if result.get("success") else "FAILED",
            "mutation": bool((result.get("state_changes") or {}).get("mutation")),
            "message": result["metadata"]["engine_publication"]}


def _execute(step, session, scene, world, character):
    domain = step.get("domain")
    text = step.get("text") or ""
    if domain == "dialogue":
        return _dialogue(text, session, scene, world)
    if domain == "observation":
        outcome = _observation(text, scene)
        if re.search(r"\b(?:seem|nervous|worried|demeanor|manner)\b", text, re.I):
            npc = _npc_from_text(text, session, scene, world)
            if npc is not None:
                outcome["message"] = (
                    f"{npc.get('name') or npc.get('label')} seems {npc.get('demeanor') or 'ordinary'}. "
                    "Nothing establishes a hidden motive."
                )
                outcome["ok"] = True
                outcome["status"] = "SUCCEEDED"
        return outcome
    if domain == "investigation":
        from game.authored_action_language import authored_examination
        authored = authored_examination(text, session, scene, world)
        if authored is not None:
            return authored
        return _investigation(text, scene)
    if domain in {"physical", "social"}:
        return _physical(text, session, scene, world, character)
    return {"ok": False, "status": "UNSUPPORTED", "mutation": False,
            "message": "That part is not supported here. It was not carried out."}


_NARRATION_CLAIM = re.compile(
    r"\b(?:quest|treasure|secret|sentinel|gold|reward|you find|you discover|hidden passage|"
    r"attacked|ambush|dragged|blood|killed|hidden camp)\b",
    re.I,
)
_DIRECTION = re.compile(r"\b(?:northwest|northeast|southwest|southeast)\b", re.I)
_NEGATION = re.compile(r"\b(?:no|not|never|without|isn'?t|aren'?t|cannot|can'?t|don'?t|do not)\b", re.I)


def _established_narration_text(facts: str, session) -> str:
    parts = [facts or ""]
    knowledge = session.get("clue_knowledge") if isinstance(session, dict) else None
    if isinstance(knowledge, dict):
        for item in knowledge.values():
            if isinstance(item, dict) and str(item.get("state") or "") in {"discovered", "known"}:
                parts.append(str(item.get("text") or ""))
            elif isinstance(item, str):
                parts.append(item)
    return " ".join(parts).casefold()


def _negated_at(text: str, start: int) -> bool:
    return bool(_NEGATION.search(text[max(0, start - 24):start]))


def validate_narration(candidate: str, facts: str, *, session=None, scene=None) -> dict[str, Any]:
    text = re.sub(r"\s+", " ", candidate or "").strip()
    reasons = []
    established = _established_narration_text(facts, session)
    if not text or len(text.split()) > 80 or text.casefold() == (facts or "").casefold():
        reasons.append("not_a_variation")
    for match in _NARRATION_CLAIM.finditer(text):
        phrase = match.group(0).casefold()
        if phrase in established or _negated_at(text, match.start()):
            continue
        reasons.append("consequential_or_hidden")
        break
    for match in _DIRECTION.finditer(text):
        if match.group(0).casefold() not in established:
            reasons.append("unestablished_direction")
            break
    if isinstance(session, dict):
        from game.narrative_consistency import publication_conflict
        conflict = publication_conflict(text, session=session, resolution={"resolved_transition": False}, scene=scene)
        if conflict:
            reasons.append(conflict)
    for token in ("aside", "open", "closed", "standing", "seated", "no climbing", "not attempted", "unchanged"):
        if token in facts.casefold() and token not in text.casefold() and token in {"aside", "open", "closed"}:
            reasons.append("dropped_outcome")
            break
    if re.search(r"\byou (?:open|climb|find)\b", text, re.I) and not re.search(r"\byou (?:open|climb|find)\b", facts, re.I):
        reasons.append("invented_success")
    denied = re.search(r"\b(?:unchanged|not beside|was not taken|not carried out)\b", facts or "", re.I)
    claimed = re.search(r"\byou (?:step back|move back|back away|move away|approach)\b", text, re.I)
    if denied and claimed and not re.search(r"\b(?:unchanged|not beside|was not taken|not carried out|try to|tried to)\b", text, re.I):
        reasons.append("invented_success")
    quotes = re.findall(r'"([^"]+)"', facts or "")
    if quotes and not any(quote.casefold() in text.casefold() for quote in quotes):
        reasons.append("dropped_speech")
    if re.search(r"\b(?:arrive|arrives|new town|new scene)\b", text, re.I) and not re.search(
        r"\b(?:arrive|arrives|new town|new scene)\b", facts or "", re.I,
    ):
        reasons.append("uncommitted_transition")
    if _irrelevant_narration(text, established or facts):
        reasons.append("irrelevant")
    return {"adopt": not reasons, "reasons": reasons}


_RELEVANCE_STOP = {
    "that", "this", "with", "from", "there", "your", "have", "been", "into",
    "over", "then", "than", "them", "they", "what", "when", "where", "nothing",
    "something", "situation", "about", "after", "before", "still", "just",
    "only", "also", "here", "were", "will", "would", "could", "should",
}


def _content_tokens(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z]{4,}", (value or "").casefold())
        if token not in _RELEVANCE_STOP
    }


def _irrelevant_narration(candidate: str, facts: str) -> bool:
    """A safe sentence that does not mention the committed outcome is not a narration of it."""
    fact_tokens = _content_tokens(facts)
    if len(fact_tokens) < 2:
        return False
    return not fact_tokens & _content_tokens(candidate)


def maybe_narrate(facts: str, *, session, scene) -> dict[str, Any] | None:
    if os.environ.get(NARRATION_GATE) != "1":
        return None
    from game.expressive_dialogue import expression_generation_disabled, expression_transport, request_expression
    if expression_generation_disabled() and expression_transport() is None:
        return None
    prompt = {
        "system": (
            "Rewrite the committed outcome in ordinary sensory prose. Keep every outcome, "
            "including a direction the facts already name. Add no object, person, clue, reward, attack, or event."
        ),
        "user": "COMMITTED FACTS:\n" + facts,
    }
    attempt = request_expression({"prompt": prompt, "operation": "bounded_narration"})
    candidate = str(attempt.get("text") or "")
    verdict = validate_narration(candidate, facts, session=session, scene=scene) if attempt.get("ok") else {"adopt": False, "reasons": ["provider_unavailable"]}
    usage = attempt.get("usage") if isinstance(attempt.get("usage"), dict) else {}
    published = bool(verdict.get("adopt"))
    _note("narration", "accepted" if published else "rejected", text=candidate if published else facts,
          reasons=verdict.get("reasons"), tokens=int(usage.get("total_tokens") or 0),
          latency_ms=float(attempt.get("latency_ms") or 0), published=published)
    if isinstance(session, dict):
        session["last_narration"] = {"adopted": published, "reasons": verdict.get("reasons"), "candidate": candidate}
    if not published:
        return None
    return {"text": candidate, "audit": session.get("last_narration")}


def commit_integrated(scene, session, world, action, *, prompt, action_id, label, character=None):
    from game.models import ExplorationEngineResult
    started = time.perf_counter()
    plan = plan_integrated(prompt, session=session, scene=scene, world=world)
    if not plan or plan.get("id") != action.get("target_id") or plan.get("mode") != "interact":
        return None
    if character is None:
        try:
            from game.storage import load_character
            character = load_character()
        except Exception:
            character = {}
    spoken: list[str] = []
    other: list[str] = []
    failed = set()
    mutation = False
    success = True
    live_dialogue = False
    clue_id = None
    clue_text = None
    discovered: list[str] = []
    interactable_id = None
    for step in plan.get("steps") or []:
        if any(dep in failed for dep in step.get("depends_on") or []):
            step["status"] = "BLOCKED"
            other.append("A later part was not attempted, because it depended on a step that did not succeed.")
            success = False
            continue
        outcome = _execute(step, session, scene, world, character)
        step["status"] = outcome.get("status")
        message = str(outcome.get("message") or "").strip()
        if step.get("domain") == "dialogue" and message:
            spoken.append(message)
        elif message:
            other.append(message)
        mutation = mutation or bool(outcome.get("mutation"))
        live_dialogue = live_dialogue or bool(outcome.get("live_dialogue"))
        if outcome.get("clue_id") and not clue_id:
            clue_id = outcome.get("clue_id")
            clue_text = outcome.get("clue_text")
            interactable_id = outcome.get("interactable_id")
            discovered.extend(item for item in outcome.get("discovered_clues") or [] if item not in discovered)
        if not outcome.get("ok"):
            success = False
            failed.add(step["step_id"])
    other_text = " ".join(part for part in other if part).strip()
    speech = " ".join(part for part in spoken if part).strip()
    # Accepted speech is already the sentence the player should read.
    # A second provider call is only for a separate committed outcome.
    narrated = maybe_narrate(other_text, session=session, scene=scene) if other_text else None
    expressed = narrated["text"] if narrated else other_text
    if speech and expressed:
        publication = f"{expressed} {speech}".strip()
    else:
        publication = speech or expressed
    if isinstance(session, dict):
        if not other_text:
            session["last_narration"] = {
                "adopted": False,
                "requested": False,
                "reasons": ["dialogue_already_final"],
                "candidate": "",
            }
        session["last_publication"] = {
            "owner": "integrated_play.commit_integrated",
            "contract": "FINAL_ENGINE_RESPONSE",
            "final": True,
            "dialogue_generated": bool(speech),
            "dialogue_accepted": bool(live_dialogue),
            "dialogue_composed": bool(speech),
            "dialogue_published": bool(speech) and speech in publication,
            "narration_requested": bool(other_text),
            "narration_accepted": bool(narrated),
            "narration_published": bool(narrated) and str(narrated.get("text") or "") in publication,
            "visible": publication,
        }
    result = ExplorationEngineResult(
        kind="interact", action_id=action_id, label=label, prompt=prompt, success=success,
        resolved_transition=False, target_scene_id=None, clue_id=clue_id, clue_text=clue_text,
        discovered_clues=discovered, interactable_id=interactable_id,
        state_changes={"integrated": True, "mutation": mutation},
        metadata={
            "engine_publication": publication,
            "skip_unrelated_clue_discovery": True,
            "publication_contract": "FINAL_ENGINE_RESPONSE",
            "skip_primary_narration": True,
            "integrated_play": {
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "live_dialogue": live_dialogue,
                "live_narration": bool(narrated),
                "dialogue_published": bool(speech) and speech in publication,
                "steps": [{"id": step.get("step_id"), "domain": step.get("domain"), "status": step.get("status")}
                          for step in plan.get("steps") or []],
            },
        },
    )
    return result.to_dict()
