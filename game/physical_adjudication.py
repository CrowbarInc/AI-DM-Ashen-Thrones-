"""General-purpose physical adjudication for ordinary, previously unauthored actions.

The provider may suggest an operation and a target. This module checks the
current scene, explicit object properties, and any already configured check.
It commits posture, position, and open state. It does not invent difficulty
classes, rolls, rooms, inventory, or success.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any

GATE = "ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION"
PROVIDER_GATE = "ASHEN_PHYSICAL_PROVIDER"
ROUTINES = frozenset({
    "sit", "stand", "open", "close", "move", "push", "pull", "lift", "place",
    "approach", "retreat", "establish", "inspect_result",
})
DEFERRED = frozenset({"take", "drop", "place"})
_MAX_REQUESTS = 8
_MAX_TOKENS = 16000
_REQUESTS = 0
_TOKENS = 0
_LOG: list[dict[str, Any]] = []
_STAMPS: dict[tuple, dict[str, Any]] = {}

_QUESTION = re.compile(
    r"^(?:is|are|was|were|am|can|could|would|should|do|does|did|what|where|which|who|how|whether)\b",
    re.I,
)
_MEMORY = re.compile(
    r"\b(?:what (?:have|did|do) (?:i|we)|my (?:inventory|journal|spells|character)|what happened|remind me|what do i know)\b",
    re.I,
)
_TRAVEL = re.compile(r"\b(?:go|head|return|travel|walk|follow)\b|\bmove\s+(?:to|toward|towards|back to|into)\b", re.I)
_CLIMB = re.compile(r"\b(?:climb|clamber|scale|scramble\s+up)\b", re.I)
_BAD_SIT = re.compile(r"\b(?:throne|imaginary|magic|magical)\b", re.I)
_CONSEQUENTIAL_WORDS = re.compile(r"\b(?:break|smash|destroy|force|pry|steal|secret|treasure|quest|passage|tunnel)\b", re.I)
_STOP = {"a", "an", "the", "i", "we", "to", "on", "in", "at", "my", "your", "please", "now", "just"}


def enabled(session) -> bool:
    from game.bounded_improvisation import controlled_enabled
    return os.environ.get(GATE) == "1" and controlled_enabled(session or {})


def provider_usage() -> dict[str, Any]:
    return {"requests": _REQUESTS, "tokens": _TOKENS, "retries": 0, "log": list(_LOG)}


def _inner(scene) -> dict:
    if isinstance(scene, dict) and isinstance(scene.get("scene"), dict):
        return scene["scene"]
    return scene if isinstance(scene, dict) else {}


def _tokens(text: str) -> set[str]:
    return {tok for tok in re.findall(r"[a-z0-9]+", (text or "").casefold()) if tok not in _STOP}


def _plan(**kwargs) -> dict[str, Any]:
    base = {
        "mode": "decline", "category": "D", "operation": None, "id": None, "message": "",
        "routine": None, "physical": True, "requires_check": False, "mechanic": None,
        "mutation": False, "deferred": False, "steps": [], "candidates": [],
    }
    base.update(kwargs)
    if base["mode"] == "interact":
        base["routine"] = base["routine"] or base["operation"]
    return base


def _question(text: str) -> bool:
    low = text.casefold().strip()
    if re.match(r"^(?:i|we|let me)\b", low):
        return low.endswith("?") and _QUESTION.search(low) is not None
    return bool(_QUESTION.search(low) or low.endswith("?"))


def _view(session) -> dict:
    ledger = session.get("bounded_improvisation") if isinstance(session, dict) else None
    return ledger if isinstance(ledger, dict) else {}


def _ledger(session) -> dict:
    from game.bounded_improvisation import ensure_bounded_improvisation_ledger
    ledger = ensure_bounded_improvisation_ledger(session)
    if not isinstance(ledger.get("physical_consequences"), list):
        ledger["physical_consequences"] = []
    if not isinstance(ledger.get("physical_state"), dict):
        ledger["physical_state"] = {}
    return ledger


def _objects(session, scene) -> list[dict[str, Any]]:
    from game.bounded_improvisation import controlled_facts
    inner = _inner(scene)
    sid = str(inner.get("id") or session.get("active_scene_id") or "")
    campaign = str(session.get("campaign_run_id") or "")
    overlay = _view(session).get("physical_state") or {}
    rows = []
    for entry in controlled_facts(session, sid):
        if entry.get("campaign_id") != campaign:
            continue
        if entry.get("family") == "environment" and not (entry.get("properties") or {}).get("use"):
            continue
        if entry.get("entity_type") == "npc" or entry.get("family") == "npc":
            continue
        props = dict(entry.get("properties") or {})
        names = [str(entry.get("label") or "")]
        names.extend(str(a) for a in entry.get("aliases") or [])
        rows.append({
            "id": entry["id"], "label": str(entry.get("label") or entry["id"]), "names": names,
            "scene_id": sid, "properties": props, "entry": entry, "source": "ledger",
        })
    for item in inner.get("interactables") or []:
        if not isinstance(item, dict) or item.get("hidden") or item.get("visible") is False:
            continue
        ident = str(item.get("id") or "")
        if not ident or any(row["id"] == ident for row in rows):
            continue
        props = dict(item.get("affordances") or {}) if isinstance(item.get("affordances"), dict) else {}
        props.update(dict(overlay.get(f"{sid}|{ident}") or {}))
        names = [str(item.get("label") or ident), ident.replace("_", " ")]
        names.extend(str(a) for a in item.get("aliases") or [])
        rows.append({
            "id": ident, "label": str(item.get("label") or ident), "names": names,
            "scene_id": sid, "properties": props, "entry": None, "source": "interactable",
        })
    for row in rows:
        row["properties"].setdefault("accessible", True)
        row["properties"].setdefault("visible", True)
    return rows


def _named(text: str, rows: list[dict]) -> list[dict]:
    words = _tokens(text)
    scored = []
    for row in rows:
        best = 0
        for name in row["names"]:
            tokens = _tokens(name)
            if tokens and tokens <= words:
                best = max(best, len(tokens))
        if best:
            scored.append((best, row))
    if not scored:
        return []
    top = max(score for score, _row in scored)
    return [row for score, row in scored if score == top]


def _pronoun(text: str) -> bool:
    return bool(re.search(r"\b(?:it|that|this|them)\b", text, re.I))


def _focus_row(session, rows):
    focus = str(_view(session).get("physical_focus") or "")
    return next((row for row in rows if row["id"] == focus), None)


def _explicit(props, key):
    return key in props


def _consequential(props) -> bool:
    return bool(props.get("consequential") is True or str(props.get("ownership") or "") in {"owned", "restricted", "guarded"})


def _check(props):
    raw = props.get("skill_check")
    if not isinstance(raw, dict):
        return None
    if not raw.get("skill_id") or type(raw.get("dc")) is not int:
        return None
    return {"skill": str(raw["skill_id"]), "difficulty": raw["dc"]}


def _stone_anchor(scene):
    for index, fact in enumerate(_inner(scene).get("visible_facts") or []):
        if not isinstance(fact, str):
            continue
        if re.search(r"\b(no|not|without|empty|absent|imagined|painted|picture|dead)\b", fact, re.I):
            continue
        if re.search(r"\b(stone|stonework|rock|rocks|boulder|boulders)\b", fact, re.I):
            return index, fact
    return None


def _fitting_id(session, scene_id) -> str:
    basis = f"{session.get('campaign_run_id')}|{scene_id}|fitting"
    return "wf_" + hashlib.sha256(basis.encode()).hexdigest()[:20]


# Same sentence integrated play already uses when a physical plan is absent.
# It does not claim that the player moved.
UNADJUDICATED_RETREAT_SENTENCE = "That part is not supported here. It was not carried out."
_SIMPLE_RETREAT = re.compile(
    r"^(?:please\s+)?"
    r"(?:i|we|let me|let's|lets|let us)\s+"
    r"(?:"
    r"step back(?:\s+from\b|(?=\s*[.!]?\s*$))"
    r"|back away(?:\s+from\b|(?=\s*[.!]?\s*$))"
    r"|move back\s+from\b"
    r")"
    r"(?!.*\b(?:and|then)\b)"
    r".{0,160}"
    r"\s*[.!]?\s*$",
    re.IGNORECASE,
)


def clear_simple_retreat(text: str) -> bool:
    """A first-person step-back this module already calls retreat.

    Questions, quotations, compounds, and 'step back to <place>' stay out.
    The check does not read or write position.
    """
    raw = re.sub(r"\s+", " ", text or "").strip()
    if not raw or _question(raw) or any(mark in raw for mark in ('"', "“", "”")):
        return False
    if not _SIMPLE_RETREAT.match(raw):
        return False
    return _operation(raw) == "retreat"


def disabled_retreat_skip(text: str, session) -> str | None:
    """Host sentence for a simple retreat when physical adjudication is off.

    Returns None when the physical pathway is enabled, so that pathway keeps
    the utterance. Does not mutate session, position, or scene state.
    """
    if enabled(session):
        return None
    if not clear_simple_retreat(text or ""):
        return None
    return UNADJUDICATED_RETREAT_SENTENCE


def _operation(text: str) -> str | None:
    low = text.casefold()
    if _CLIMB.search(low):
        return "climb"
    if re.search(r"\b(?:pick up|grab|steal|pocket)\b", low) or re.search(r"\btake\b(?!\s+a\s+seat)", low):
        return "take"
    if re.search(r"\b(?:drop|put down)\b", low):
        return "drop"
    if re.search(r"\b(?:place|set down|put)\b", low) and re.search(r"\b(?:on|down|aside|there)\b", low):
        return "place"
    if re.search(r"\b(?:stand up|get up|rise)\b", low) or re.search(r"\bi stand\b", low):
        return "stand"
    if re.search(r"\b(?:step back|back away|move back from)\b", low):
        return "retreat"
    if re.search(r"\b(?:sit|take a seat|have a seat)\b|\brest\b", low):
        return "sit"
    if re.search(r"\b(?:opening|open|unlatch)\b", low):
        return "open"
    if re.search(r"\b(?:close|shut)\b", low):
        return "close"
    if re.search(r"\b(?:lift|heave|raise)\b", low):
        return "lift"
    if re.search(r"\b(?:approach|walk over to|step up to|go over to)\b", low):
        return "approach"
    if re.search(r"\b(?:push|shove|nudge)\b", low):
        return "push"
    if re.search(r"\bpull\b", low):
        return "pull"
    if re.search(r"\b(?:move|shift|slide)\s+(?:the|a|an|it|that|this|them)\b", low):
        return "move"
    if re.search(r"\b(?:look inside|check underneath|look beneath|check the doorway)\b", low):
        return "inspect_result"
    return None


def _ground(text, session, scene, rows, operation):
    named = _named(text, rows)
    if len(named) > 1:
        labels = " or ".join(row["label"] for row in named[:4])
        return None, _plan(
            mode="clarify", category="F", operation=operation, candidates=[row["id"] for row in named],
            message=f"Which do you mean: {labels}? Nothing has been attempted.",
        )
    if len(named) == 1:
        return named[0], None
    if _pronoun(text):
        focus = _focus_row(session, rows)
        if focus is not None:
            return focus, None
        if len(rows) == 1:
            return rows[0], None
        if len(rows) > 1:
            return None, _plan(mode="clarify", category="F", operation=operation,
                               message="Which object do you mean? Nothing has been attempted.")
    return None, None


def _state_answer(text, session, scene) -> dict | None:
    low = text.casefold()
    rows = _objects(session, scene)
    sid = str(_inner(scene).get("id") or "")
    posture = _view(session).get("posture") if isinstance(_view(session).get("posture"), dict) else {}
    if re.search(r"\b(?:am i|are we)\b", low) and re.search(r"\bbeside\b", low):
        position = _view(session).get("position") if isinstance(_view(session).get("position"), dict) else {}
        beside = position.get("kind") == "beside" and position.get("scene_id") == sid
        return _plan(mode="answer", category="A", operation="approach", mutation=False,
                     message=(f"You are beside the {position.get('label')}." if beside else "You are not beside that."))
    if re.search(r"\b(?:am i|are we)\b", low) and re.search(r"\b(?:sitting|seated|standing)\b", low):
        seated = posture.get("kind") == "sitting" and posture.get("scene_id") == sid
        if "standing" in low and "sitting" not in low:
            return _plan(mode="answer", category="A", operation="stand", mutation=False,
                         message="You are standing here." if not seated else "You are seated here, not standing.")
        return _plan(mode="answer", category="A", operation="sit", mutation=False,
                     message="You are seated here." if seated else "You are not seated in this scene.")
    if re.search(r"\bdoorway\b", low) and re.search(r"\b(?:clear|blocked|obstruct)\b", low):
        mentions = [row for row in rows if "doorway" in json.dumps(row["properties"]).casefold()]
        if not mentions:
            return _plan(mode="answer", category="D", operation="inspect_result",
                         message="No doorway obstruction is established.")
        blocking = [row for row in mentions if row["properties"].get("obstructs") == "doorway"
                    or "blocking" in str(row["properties"].get("position") or "")]
        return _plan(mode="answer", category="A", operation="inspect_result",
                     message="The doorway is not clear." if blocking else "The doorway is clear.")
    row, ambiguous = _ground(text, session, scene, rows, "inspect_result")
    if ambiguous:
        return ambiguous
    if row is None:
        return None
    props = row["properties"]
    if re.search(r"\b(?:open|closed)\b", low):
        if not _explicit(props, "open"):
            return _plan(mode="answer", category="D", operation="open", id=row["id"],
                         message=f"Whether the {row['label']} is open is not established. It is unchanged.")
        return _plan(mode="answer", category="A", operation="open", id=row["id"],
                     message=f"The {row['label']} is {'open' if props.get('open') else 'closed'}.")
    if re.search(r"\blocked\b", low):
        if not _explicit(props, "locked"):
            return _plan(mode="answer", category="D", operation="open", id=row["id"],
                         message=f"Whether the {row['label']} is locked is not established.")
        return _plan(mode="answer", category="A", operation="open", id=row["id"],
                     message=f"The {row['label']} is {'locked' if props.get('locked') else 'unlocked'}.")
    if re.search(r"\bwhere\b", low) or re.search(r"\bstill\b", low):
        position = props.get("position")
        if not position:
            return _plan(mode="answer", category="D", operation="move", id=row["id"],
                         message=f"No position is established for the {row['label']}.")
        return _plan(mode="answer", category="A", operation="move", id=row["id"],
                     message=f"The {row['label']} is {position}.")
    if re.search(r"\bcan i\b", low):
        return _possibility(row, _operation(text) or "move")
    return None


def _possibility(row, operation) -> dict:
    props = row["properties"]
    if props.get("accessible") is False:
        return _plan(mode="answer", category="E", operation=operation, id=row["id"],
                     message=f"The {row['label']} is not accessible from here. Nothing has been changed.")
    if operation in {"push", "pull", "move", "lift"}:
        if props.get("mobility") == "immovable":
            return _plan(mode="answer", category="E", operation=operation, id=row["id"],
                         message=f"The {row['label']} cannot be moved. Nothing has been moved.")
        if props.get("mobility") == "movable" and props.get("weight") == "light":
            return _plan(mode="answer", category="A", operation=operation, id=row["id"],
                         message=f"The {row['label']} is accessible and established as light enough to move. Nothing has been moved.")
        if props.get("weight") == "heavy" or props.get("mobility") == "movable":
            check = _check(props)
            if check:
                return _plan(mode="answer", category="B", operation=operation, id=row["id"], requires_check=True,
                             mechanic=check["skill"], message=f"Moving the {row['label']} requires the established {check['skill']} check. Nothing has been moved.")
            return _plan(mode="answer", category="B", operation=operation, id=row["id"], mechanic="strength",
                         message=f"No strength check is configured for the {row['label']}. Nothing has been moved.")
        return _plan(mode="answer", category="D", operation=operation, id=row["id"],
                     message=f"Whether the {row['label']} can be moved is not established. Nothing has been moved.")
    if operation in {"open", "close"}:
        if props.get("openable") is not True:
            return _plan(mode="answer", category="D", operation=operation, id=row["id"],
                         message=f"The {row['label']} is not established as something you can open. Nothing has been opened.")
        if props.get("locked") is True:
            return _plan(mode="answer", category="D", operation=operation, id=row["id"],
                         message=f"The {row['label']} is locked. Nothing has been opened.")
        return _plan(mode="answer", category="A", operation=operation, id=row["id"],
                     message=f"The {row['label']} can be opened or closed without a check. Nothing has been opened or closed.")
    if operation == "sit":
        if props.get("use") == "seat":
            return _plan(mode="answer", category="A", operation="sit", id=row["id"],
                         message=f"The {row['label']} is an accessible seat. You have not sat down.")
        return _plan(mode="answer", category="D", operation="sit", id=row["id"],
                     message=f"Whether the {row['label']} can be sat on is not established. Your posture is unchanged.")
    return _plan(mode="answer", category="D", operation=operation, id=row["id"],
                 message="That possibility is not established. Nothing has been changed.")


def _establish_plan(text, session, scene):
    low = text.casefold()
    if not re.search(r"\b(?:loose stone|small loose stone|small stone|anything light|something light)\b", low):
        return None
    if re.search(r"\b(?:door|crate|chest|cup|treasure|weapon|passage|secret|quest)\b", low):
        return _plan(mode="decline", category="D", operation="establish",
                     message="The public scene does not support that ordinary object. Nothing has been added.")
    sid = str(_inner(scene).get("id") or "")
    ident = _fitting_id(session, sid)
    existing = next((row for row in _objects(session, scene) if row["id"] == ident), None)
    if existing:
        return _plan(mode="answer", category="A", operation="establish", id=ident,
                     message=existing["entry"]["content"] + " It has not been moved.")
    if _stone_anchor(scene) is None:
        return _plan(mode="decline", category="D", operation="establish",
                     message="The public scene does not support that ordinary object. Nothing has been added.")
    return _plan(mode="interact", category="A", operation="establish", id=ident, mutation=True,
                 message="An ordinary small loose stone can be established here.")


def _refuse_missing(operation, label="That"):
    return _plan(mode="decline", category="E", operation=operation,
                 message=f"{label} is not established here. Nothing has been changed.")


def _assess_clause(text, session, scene, *, pronoun_rows=None, compound=False, bound_row=None):
    operation = _operation(text)
    if operation is None and compound:
        operation = _compound_operation(text)
    if operation is None:
        return None
    if operation == "climb":
        rows = _objects(session, scene)
        row, ambiguous = _ground(text, session, scene, rows, operation)
        if ambiguous:
            return ambiguous
        label = row["label"] if row else "That feature"
        if row is None:
            return _plan(mode="decline", category="E", operation="climb", mechanic="climb",
                         message="That feature is not established. It has not been added, and your position is unchanged.")
        check = _check(row["properties"])
        if check is None:
            return _plan(mode="decline", category="D", operation="climb", id=row["id"], mechanic="climb",
                         message=(f"{label} is here, but no climbing check is configured, "
                                  "so the climb is not resolved and your position is unchanged."))
        return _plan(mode="interact", category="B", operation="climb", id=row["id"], requires_check=True,
                     mechanic=check["skill"], message="")
    if operation in {"take", "drop"}:
        return _plan(mode="decline", category="D", operation=operation, deferred=True,
                     message="Carrying ordinary objects is not available. Nothing was added to your inventory or dropped.")
    if _CONSEQUENTIAL_WORDS.search(text) and operation not in {"open", "close", "move", "push", "pull"}:
        return _plan(mode="decline", category="C", operation=operation,
                     message="That would change important state, and no authorized mechanic resolves it. Nothing has been changed.")
    if operation == "traverse":
        return _plan(mode="decline", category="E", operation="traverse",
                     message="No passage through is established. Your position is unchanged.")
    if operation == "gesture":
        return _plan(mode="decline", category="D", operation="gesture",
                     message="That gesture is not resolved as an action here. Nothing was changed.")
    if operation == "stand":
        return _plan(mode="interact", category="A", operation="stand", id="posture", message="")
    if operation == "retreat":
        return _plan(mode="interact", category="A", operation="retreat", id="position", message="")
    if operation == "inspect_result" and re.search(r"\b(?:doorway|inside|underneath|beneath)\b", text, re.I):
        return _plan(mode="interact", category="A", operation="inspect_result",
                     id="doorway" if re.search(r"\bdoorway\b", text, re.I) else "inspection", mutation=False, message="")
    if operation == "inspect_result" and compound and re.search(r"\b(?:road|around|vantage|view)\b", text, re.I):
        return _plan(mode="interact", category="A", operation="inspect_result", id="vantage", mutation=False, message="")
    rows = pronoun_rows or _objects(session, scene)
    if operation == "sit":
        if _BAD_SIT.search(text):
            return _plan(mode="decline", category="E", operation="sit",
                         message="That seat is not established. Your posture is unchanged.")
        seats = [row for row in rows if row["properties"].get("use") == "seat"]
        phrase = _seat_phrase(text)
        named = _phrase_matches(phrase, seats) if phrase else _named(text, seats)
        focus = bound_row if bound_row is not None and bound_row.get("properties", {}).get("use") == "seat" else _focus_row(session, seats)
        if len(named) > 1:
            return _plan(mode="clarify", category="F", operation="sit", candidates=[row["id"] for row in named],
                         message="Which seat do you mean? Nothing has been attempted.")
        if len(named) == 1:
            row = named[0]
        elif _pronoun(text):
            if focus is not None:
                row = focus
            elif len(seats) == 1:
                row = seats[0]
            elif len(seats) > 1:
                return _plan(mode="clarify", category="F", operation="sit",
                             message="Which seat do you mean? Nothing has been attempted.")
            else:
                row = None
        elif phrase:
            # A named seat with no local candidate is missing, not ambiguous.
            others = _phrase_matches(phrase, [row for row in rows if row not in seats])
            if len(others) > 1:
                labels = " or ".join(item["label"] for item in others[:4])
                return _plan(mode="clarify", category="F", operation="sit", candidates=[item["id"] for item in others],
                             message=f"Which do you mean: {labels}? Nothing has been attempted.")
            if len(others) == 1:
                return _plan(mode="decline", category="D", operation="sit", id=others[0]["id"],
                             message=f"The {others[0]['label']} is not an accessible seat. Your posture is unchanged.")
            return _plan(mode="decline", category="E", operation="sit",
                         message="That seat is not established here. Your posture is unchanged.")
        elif len(seats) > 1:
            return _plan(mode="clarify", category="F", operation="sit",
                         message="Which seat do you mean? Nothing has been attempted.")
        elif len(seats) == 1:
            row = seats[0]
        else:
            row = None
        if row is None:
            return _plan(mode="decline", category="E", operation="sit",
                         message="No accessible seat is established. Your posture is unchanged.")
        if row["properties"].get("accessible") is False or row["properties"].get("visible") is False:
            return _plan(mode="decline", category="E", operation="sit", id=row["id"],
                         message=f"The {row['label']} is not accessible. Your posture is unchanged.")
        return _plan(mode="interact", category="A", operation="sit", id=row["id"], message="")
    if bound_row is not None and (_pronoun(text) or re.search(r"\bwhere it was\b", text, re.I)):
        row, ambiguous = bound_row, None
    else:
        row, ambiguous = _ground(text, session, scene, rows, operation)
    if ambiguous:
        return ambiguous
    if row is None:
        if operation == "approach":
            return None
        return _refuse_missing(operation)
    return _preconditions(row, operation, text)


def _preconditions(row, operation, text) -> dict:
    props = row["properties"]
    label = row["label"]
    if operation == "sit":
        if props.get("use") != "seat" or props.get("accessible") is False or props.get("visible") is False:
            return _plan(mode="decline", category="D", operation="sit", id=row["id"],
                         message=f"The {label} is not an accessible seat. Your posture is unchanged.")
        return _plan(mode="interact", category="A", operation="sit", id=row["id"], message="")
    if operation == "climb":
        check = _check(props)
        if check:
            return _plan(mode="interact", category="B", operation="climb", id=row["id"],
                         requires_check=True, mechanic=check["skill"], message="")
        return _plan(mode="decline", category="D", operation="climb", id=row["id"], mechanic="climb",
                     message=(f"The {label} is here, but no climbing check is configured, "
                              "so the climb is not resolved and your position is unchanged."))
    if props.get("visible") is False or props.get("accessible") is False:
        return _plan(mode="decline", category="E", operation=operation, id=row["id"],
                     message=f"The {label} is not accessible from here. It is unchanged.")
    if _consequential(props) and operation in {"open", "close", "move", "push", "pull", "lift", "place"}:
        return _plan(mode="decline", category="C", operation=operation, id=row["id"],
                     message=f"Changing the {label} would alter important state, and no authorized mechanic resolves it. It is unchanged.")
    if operation in {"open", "close"}:
        if props.get("openable") is not True:
            return _plan(mode="decline", category="D", operation=operation, id=row["id"],
                         message=f"The {label} is here, but it is not established as something you can open. It is unchanged.")
        if not _explicit(props, "locked") or not _explicit(props, "open"):
            return _plan(mode="decline", category="D", operation=operation, id=row["id"],
                         message=f"Whether the {label} is locked or open is not established. It is unchanged.")
        if props.get("locked") is True and operation == "open":
            return _plan(mode="decline", category="D", operation="open", id=row["id"],
                         message=f"The {label} is locked. It stays closed.")
        if props.get("obstructed") is True and operation == "open":
            return _plan(mode="decline", category="D", operation="open", id=row["id"],
                         message=f"The {label} is obstructed. It stays closed.")
        check = _check(props)
        if check and not (operation == "close" and props.get("open") is True):
            return _plan(mode="interact", category="B", operation=operation, id=row["id"],
                         requires_check=True, mechanic=check["skill"], message="")
        return _plan(mode="interact", category="A", operation=operation, id=row["id"], message="")
    if operation in {"move", "push", "pull", "lift"}:
        if props.get("mobility") == "immovable" or props.get("weight") == "immovable":
            return _plan(mode="decline", category="E", operation=operation, id=row["id"],
                         message=f"The {label} cannot be moved. It is unchanged.")
        if props.get("mobility") != "movable":
            return _plan(mode="decline", category="D", operation=operation, id=row["id"],
                         message=f"The {label} is here, but whether it can be moved is not established. It is unchanged.")
        if props.get("weight") != "light":
            check = _check(props)
            if check:
                return _plan(mode="interact", category="B", operation=operation, id=row["id"],
                             requires_check=True, mechanic=check["skill"], message="")
            return _plan(mode="decline", category="B", operation=operation, id=row["id"], mechanic="strength",
                         message=f"The {label} is not established as light, and no strength check is configured. It is unchanged.")
        if _destination(text, row).get("valid") is False:
            reason = _destination(text, row).get("reason")
            if reason == "no_doorway":
                message = "No doorway obstruction is established, so nothing was moved to clear one."
            else:
                message = f"That is not an established place to move the {label}. It is unchanged."
            return _plan(mode="decline", category="E", operation=operation, id=row["id"], message=message)
        return _plan(mode="interact", category="A", operation=operation, id=row["id"], message="")
    if operation == "approach":
        return _plan(mode="interact", category="A", operation="approach", id=row["id"], message="")
    if operation == "inspect_result":
        if re.search(r"\bdoorway\b", text, re.I):
            return _plan(mode="interact", category="A", operation="inspect_result", id="doorway", mutation=False, message="")
        return _plan(mode="interact", category="A", operation="inspect_result", id=row["id"], mutation=False, message="")
    if operation == "place":
        if str(props.get("position") or "") != "raised in place":
            return _plan(mode="decline", category="D", operation="place", id=row["id"], deferred=True,
                         message="You are not holding that, and carrying is not available. Nothing was placed.")
        return _plan(mode="interact", category="A", operation="place", id=row["id"], message="")
    return _plan(mode="decline", category="D", operation=operation, id=row["id"],
                 message=f"The {label} cannot be handled that way. It is unchanged.")


def _destination(text: str, row) -> dict:
    low = text.casefold()
    if re.search(r"\b(?:through|into)\s+(?:the|a)\s+wall\b|\bnext room\b|\banother room\b", low):
        return {"valid": False, "reason": "invalid_destination"}
    position = str(row["properties"].get("position") or "")
    if "doorway" in low:
        if row["properties"].get("obstructs") == "doorway" or "doorway" in position:
            return {"valid": True, "position": "aside from the doorway", "clear": "doorway"}
        return {"valid": False, "reason": "no_doorway"}
    if re.search(r"\bfarther\b", low):
        if position.startswith("farther"):
            return {"valid": True, "position": position, "unchanged": True}
        if position.startswith("aside"):
            return {"valid": True, "position": "farther " + position}
        return {"valid": True, "position": "farther aside"}
    if "stonework" in position and re.search(r"\b(?:aside|away|out of the way)\b", low):
        return {"valid": True, "position": "aside from the stonework"}
    if re.search(r"\b(?:aside|away|out of the way|back)\b", low):
        return {"valid": True, "position": "aside from where it was"}
    return {"valid": True, "position": "shifted from where it was"}


_MAX_STEPS = 3
_BREAK = re.compile(r"\s*(?:;\s*|,\s+and\s+|\s+and\s+then\s+|\s+then\s+|\s+and\s+)\s*", re.I)
_ACTIONISH = re.compile(
    r"^(?:please\s+|let me\s+|let's\s+|i\s+|we\s+|i'll\s+|i will\s+|first\s+|next\s+|after that\s+|afterwards\s+|then\s+)?"
    r"(?:stand|get up|rise|sit|rest|open|unlatch|close|shut|push|pull|move|shift|slide|lift|heave|place|set|"
    r"approach|walk|step|look|inspect|check|read|climb|clamber|wave|greet|survey|peer|examine|nudge|shove|"
    r"back away|step back|try)\b",
    re.I,
)
_STRUCTURAL_IDS = {"posture", "position", "inspection", "doorway", "vantage"}


def _seat_phrase(text: str) -> list[str]:
    match = re.search(r"\b(?:on|onto|upon)\s+(?:the\s+|a\s+|an\s+)?(.+)$", text, re.I)
    if not match:
        return []
    drop = {"it", "that", "this", "them", "down"}
    return [tok for tok in re.findall(r"[a-z0-9]+", match.group(1).casefold()) if tok not in _STOP and tok not in drop]


def _phrase_matches(phrase: list[str], rows: list[dict]) -> list[dict]:
    if not phrase:
        return []
    found = []
    for row in rows:
        names: set[str] = set()
        for name in row["names"]:
            names |= _tokens(name)
        if all(tok in names for tok in phrase):
            found.append(row)
    return found


def _compound_operation(text: str) -> str | None:
    low = text.casefold()
    if re.search(r"\b(?:step|go|walk|pass)\s+through\b", low):
        return "traverse"
    if re.search(r"\b(?:wave|greet|nod)\b", low):
        return "gesture"
    if re.search(r"\b(?:look|peer|survey|read|inspect|examine|check)\b", low):
        return "inspect_result"
    return None


def _combat_active() -> bool:
    try:
        from game.storage import load_combat
        combat = load_combat()
    except Exception:
        return False
    return isinstance(combat, dict) and combat.get("in_combat") is True


def _actionish(text: str) -> bool:
    return _ACTIONISH.match(text.strip()) is not None


def _split_commas(chunk: str) -> list[str]:
    bits = [bit.strip(" .") for bit in re.split(r"\s*,\s+", chunk) if bit.strip(" .")]
    if len(bits) > 1 and all(_actionish(bit) for bit in bits):
        return bits
    return [chunk.strip(" .")]


def _split_sequence(text: str) -> list[str]:
    chunks = [chunk.strip(" .") for chunk in _BREAK.split(text) if chunk.strip(" .")]
    refined = []
    for chunk in chunks or [text]:
        refined.extend(_split_commas(chunk))
    return [part for part in refined if part]


def _clause_condition(part: str) -> tuple[str | None, str]:
    match = re.match(r"^if\s+(.+?),\s*(?:then\s+)?(.+)$", part.strip(), re.I)
    if match:
        return match.group(1).strip(), match.group(2).strip(" .")
    return None, part.strip(" .")


def _split_actions(text: str) -> list[dict[str, Any]]:
    match = re.match(r"^if\s+(.+?),\s*(?:then\s+)?(.+)$", text.strip(), re.I)
    if match and not re.search(r"\b(?:and then|\band\b|\bthen\b)\b", match.group(1), re.I):
        return [{"text": match.group(2).strip(" ."), "condition": match.group(1).strip(), "condition_only": True}]
    steps = []
    for part in _split_sequence(text):
        condition, action = _clause_condition(part)
        steps.append({"text": action, "condition": condition, "condition_only": False})
    return steps


def _clauses(text: str) -> list[str]:
    return [piece["text"] for piece in _split_actions(text)]


def _row_by_id(session, scene, ident):
    if not ident or ident in _STRUCTURAL_IDS:
        return None
    return next((row for row in _objects(session, scene) if row["id"] == ident), None)


def _condition_state(clause, session, scene, bound=None) -> dict[str, Any]:
    low = (clause or "").casefold()
    if re.search(r"\b(?:can reach|reachable|able to)\b", low):
        return {"known": False}
    rows = _objects(session, scene)
    if bound is not None and (_pronoun(clause) or not _named(clause, rows)):
        row, ambiguous = bound, None
    else:
        row, ambiguous = _ground(clause, session, scene, rows, "inspect_result")
    if ambiguous is not None:
        return {"known": False, "ambiguous": True}
    if re.search(r"\b(?:opens|open|opened|unlatched)\b", low):
        if row is None or "open" not in row["properties"]:
            return {"known": False}
        return {"known": True, "satisfied": bool(row["properties"].get("open")), "id": row["id"]}
    if re.search(r"\bbeside\b", low):
        position = _view(session).get("position") if isinstance(_view(session).get("position"), dict) else {}
        sid = str(_inner(scene).get("id") or "")
        if row is None:
            return {"known": False}
        satisfied = position.get("kind") == "beside" and position.get("target_id") == row["id"] and position.get("scene_id") == sid
        return {"known": True, "satisfied": satisfied, "id": row["id"]}
    if re.search(r"\b(?:moves|moved|aside|shifts|shifted)\b", low):
        if row is None:
            return {"known": False}
        position = str(row["properties"].get("position") or "")
        if not position:
            return {"known": False}
        return {"known": True, "satisfied": bool(re.search(r"\b(?:aside|farther|shifted)\b", position)), "id": row["id"]}
    return {"known": False}


def _dependency_kind(prev, step) -> str:
    low = (step.get("text") or "").casefold()
    prev_op = prev.get("operation")
    operation = step.get("operation")
    if prev_op == "climb" and (operation == "inspect_result" or re.search(r"\b(?:road|down|vantage|view)\b", low)):
        return "mechanical"
    if prev_op == "traverse" or (re.search(r"\b(?:inside|through)\b", low) and prev_op in {"open", "close", "traverse"}):
        return "physical"
    if re.search(r"\b(?:where it was|beneath|underneath)\b", low):
        return "target"
    if _pronoun(low) and operation in {"inspect_result", "sit", "place", "open", "close", "move", "push", "pull", "lift"}:
        return "target"
    if prev_op == "approach" and operation in {"sit", "inspect_result", "retreat"}:
        return "positional"
    if prev_op in {"move", "push", "pull"} and operation == "open":
        return "physical"
    if prev_op == "lift" and operation == "place":
        return "target"
    if operation in {"stand", "gesture", "approach", "retreat", "sit"} and not _pronoun(low):
        return "independent"
    if step.get("id") and prev.get("id") and step.get("id") != prev.get("id") and not _pronoun(low) and operation not in {"inspect_result", "traverse"}:
        return "independent"
    if operation == "inspect_result" and step.get("id") and prev.get("id") and step.get("id") != prev.get("id") and not re.search(r"\b(?:inside|it|that|where it was)\b", low):
        return "independent"
    if operation == "inspect_result" and prev_op in {"open", "close", "move", "push", "pull", "lift", "place"}:
        return "target"
    return "uncertain"


def _public_step(step) -> dict[str, Any]:
    copy = dict(step)
    copy.pop("steps", None)
    return copy


def _decorate(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for index, step in enumerate(steps):
        step["step_id"] = f"s{index + 1}"
        step["status"] = "PROPOSED"
        step["explicit_dependencies"] = []
        step["inferred_dependencies"] = []
        if step.get("condition") and index:
            step["dependency_kind"] = "explicit"
            step["explicit_dependencies"] = [steps[index - 1]["step_id"]]
        elif index == 0:
            step["dependency_kind"] = "independent"
        else:
            kind = _dependency_kind(steps[index - 1], step)
            step["dependency_kind"] = kind
            if kind != "independent":
                step["inferred_dependencies"] = [steps[index - 1]["step_id"]]
        step["depends_on"] = list(dict.fromkeys(step["explicit_dependencies"] + step["inferred_dependencies"]))
        step["publication"] = "pending"
    return steps


def _prepare_steps(pieces, session, scene):
    prepared = []
    bound = None
    compound = len(pieces) > 1
    for piece in pieces:
        assessed = _assess_clause(piece["text"], session, scene, compound=compound, bound_row=bound)
        if assessed is None:
            if not prepared:
                return None
            assessed = _plan(mode="decline", category="D", operation="inspect_result",
                             message="The rest of that request was not carried out.")
        step = dict(assessed, text=piece["text"], condition=piece.get("condition"))
        step.pop("steps", None)
        prepared.append(step)
        if step.get("id") not in _STRUCTURAL_IDS and step.get("id"):
            bound = _row_by_id(session, scene, step["id"]) or bound
    return _decorate(prepared)


def _can_continue_independently(steps) -> bool:
    first = steps[0]
    if first.get("mode") == "interact" or not first.get("id") or first.get("id") in _STRUCTURAL_IDS:
        return False
    return all(step.get("dependency_kind") == "independent" and step.get("mode") == "interact" for step in steps[1:])


def _conditional_only(piece, session, scene):
    state = _condition_state(piece["condition"], session, scene)
    action = _assess_clause(piece["text"], session, scene, compound=True)
    if action is None:
        return _plan(mode="decline", category="D", operation="inspect_result", mutation=False,
                     message="That follow-up is not an action that can be resolved. Nothing was changed.")
    if state.get("ambiguous"):
        return _plan(mode="clarify", category="F", operation=action.get("operation"),
                     message="Which target does that condition refer to? Nothing has been attempted.")
    if not state.get("known"):
        return _plan(mode="decline", category="D", operation=action.get("operation"), mutation=False,
                     message="That condition is not established, so nothing was attempted.")
    if not state.get("satisfied"):
        return _plan(mode="answer", category="A", operation=action.get("operation"), mutation=False, id=state.get("id"),
                     message="That condition is not met, so the later action was skipped. Nothing was changed.")
    action = dict(action)
    action["condition"] = piece["condition"]
    action["status"] = "READY" if action.get("mode") == "interact" else action.get("mode", "").upper()
    return action


def plan_physical(text, *, session, scene, world):
    """Read-only interpretation. Establishment and movement happen in commit."""
    if not enabled(session) or not isinstance(session, dict):
        return None
    raw = re.sub(r"\s+", " ", text or "").strip()
    if not raw or _MEMORY.search(raw):
        return None
    if _CONSEQUENTIAL_WORDS.search(raw) and _operation(raw) is None and not re.search(r"\b(?:and then|and|then)\b", raw, re.I):
        return _plan(mode="decline", category="C", operation="manipulate",
                     message="That would change important state, and no authorized mechanic resolves it. Nothing has been changed.")
    if re.search(r"\b(?:teleport|phase through|walk through the wall)\b", raw, re.I):
        return _plan(mode="decline", category="E", operation="move",
                     message="You cannot move through a solid barrier. Your position is unchanged.")
    if _question(raw):
        if re.search(r"\b(?:is there|are there|anything light|something light)\b", raw, re.I):
            established = _establish_plan(raw, session, scene)
            if established is not None:
                return established
        if re.search(r"\b(?:sit|seat|rest)\b", raw, re.I) and not re.search(r"\b(?:loose stone|small stone)\b", raw, re.I):
            seats = [row for row in _objects(session, scene) if row["properties"].get("use") == "seat"]
            if not seats:
                return None
            return _plan(mode="answer", category="A", operation="sit", id=seats[0]["id"] if len(seats) == 1 else None,
                         message=seats[0]["entry"]["content"] if len(seats) == 1 and seats[0].get("entry") else "An accessible seat is here. You have not sat down.")
        answer = _state_answer(raw, session, scene)
        if re.search(r"\b(?:other side|hidden side|what lies beyond)\b", raw, re.I):
            note = "Nothing on the other side is established, and nothing was opened or moved."
            if answer is None:
                return _plan(mode="answer", category="D", mutation=False,
                             message="That is not established. " + note)
            answer["message"] = (answer.get("message") or "").rstrip() + " " + note
            answer["mutation"] = False
        return answer
    plans = _view(session).get("physical_plans")
    if plans and re.match(r"^(?:continue|resume the plan|carry on with that)\b", raw, re.I):
        return _plan(mode="answer", category="A", mutation=False, operation="sequence",
                     message="No unfinished sequence resumes on its own. Say the next action you want. Nothing further was attempted.")
    pieces = _split_actions(raw)
    if len(pieces) == 1 and _TRAVEL.search(raw) and _operation(raw) not in {"push", "pull", "move", "retreat", "approach", "climb"}:
        return None
    if len(pieces) > 3:
        return _plan(mode="clarify", category="F", operation="sequence",
                     message="That request names more than three actions. Say which three to resolve first. Nothing has been attempted.")
    if len(pieces) > 1 and _combat_active():
        return _plan(mode="decline", category="D", operation="sequence",
                     message="That sequence is not resolved during combat. Nothing has been attempted.")
    if len(pieces) > 1 and any(_question(piece["text"]) for piece in pieces):
        return _plan(mode="clarify", category="F", operation="sequence",
                     message="That mixes a question with an action. Nothing has been attempted.")
    if len(pieces) == 1 and pieces[0].get("condition") and pieces[0].get("condition_only"):
        return _conditional_only(pieces[0], session, scene)
    prepared = _prepare_steps(pieces, session, scene)
    if prepared is None and _CONSEQUENTIAL_WORDS.search(raw):
        message = "That would change important state, and no authorized mechanic resolves it. Nothing has been changed."
        if len(pieces) > 1:
            message += " The rest was not attempted."
        return _plan(mode="decline", category="C", operation="manipulate", message=message)
    if prepared is None:
        return None
    if any(step.get("mode") == "clarify" for step in prepared):
        if len(prepared) == 1:
            return prepared[0]
        return _plan(mode="clarify", category="F", operation=prepared[0].get("operation"),
                     message="Which part do you mean? Nothing has been attempted.")
    if len(prepared) == 1 and not prepared[0].get("condition"):
        return prepared[0]
    if prepared[0].get("mode") != "interact":
        if _can_continue_independently(prepared):
            lead = dict(prepared[1])
            lead["preface"] = prepared[0].get("message", "").rstrip() + " "
            lead["steps"] = [_public_step(step) for step in prepared[1:]]
            return lead
        prepared[0]["message"] = (prepared[0].get("message", "") + " The rest was not attempted.").strip()
        prepared[0].pop("steps", None)
        return prepared[0]
    first = dict(prepared[0])
    first["steps"] = [_public_step(step) for step in prepared]
    return first


def _record_plan(session, scene, steps) -> None:
    ledger = _ledger(session)
    ledger.setdefault("physical_plans", [])
    ledger["physical_plans"] = (ledger["physical_plans"] + [{
        "turn": session.get("turn_counter"),
        "scene_id": str(_inner(scene).get("id") or ""),
        "statuses": [step.get("status") for step in steps],
        "operations": [step.get("operation") for step in steps],
        "consequences": [step.get("consequence_id") for step in steps if step.get("consequence_id")],
        "automatic_resume": False,
    }])[-12:]


def _remember(session, target_id):
    if target_id and target_id not in {"posture", "position"}:
        _ledger(session)["physical_focus"] = target_id


def _write_props(session, row, props):
    if row.get("entry") is not None:
        row["entry"]["properties"] = props
        row["properties"] = props
        return
    _ledger(session)["physical_state"][f"{row['scene_id']}|{row['id']}"] = dict(props)
    row["properties"] = props


def _consequence(session, scene, *, target, operation, prior, result):
    if prior == result:
        return None
    ledger = _ledger(session)
    sid = str(_inner(scene).get("id") or "")
    basis = "|".join([str(session.get("campaign_run_id")), sid, str(session.get("turn_counter")),
                      str(target), operation, json.dumps(prior, sort_keys=True), json.dumps(result, sort_keys=True)])
    ident = "pc_" + hashlib.sha256(basis.encode()).hexdigest()[:20]
    if any(item.get("id") == ident for item in ledger["physical_consequences"]):
        return None
    item = {
        "id": ident, "target_id": target, "action": operation, "prior": prior, "result": result,
        "campaign_id": session.get("campaign_run_id"), "scene_id": sid,
        "turn": session.get("turn_counter"), "provenance": "physical_adjudication",
    }
    ledger["physical_consequences"].append(item)
    return item


def _roll(session, scene, row, check, character):
    from game.skill_checks import resolve_skill_check
    rolled = resolve_skill_check(check["skill"], check["difficulty"], character or {}, {
        "seed_parts": [session.get("turn_counter"), row["scene_id"], row["id"], check["skill"], check["difficulty"]],
    })
    rolled["invented"] = False
    return rolled


_RETREAT_SUBJECT = re.compile(
    r"\b(?:step back|back away|move back)(?:\s+from)?(?:\s+(?:the|a|an))?\s+([a-z0-9][a-z0-9' -]{0,48})",
    re.I,
)


def _retreat_subject(text: str) -> str:
    """The thing the player named in a step-back. Empty when they named none."""
    match = _RETREAT_SUBJECT.search(text or "")
    if not match:
        return ""
    label = re.split(r"\b(?:and|then|so|before|after)\b|[.!?]", match.group(1), maxsplit=1, flags=re.I)[0]
    return re.sub(r"\s+", " ", label).strip(" ,")


def _apply(step, session, scene, character) -> dict:
    operation = step.get("operation")
    if operation == "traverse":
        return {"ok": False, "mutation": False, "category": "E",
                "message": "No passage through is established. Your position is unchanged."}
    if operation == "gesture":
        return {"ok": False, "mutation": False, "category": "D",
                "message": "That gesture is not resolved as an action here. Nothing was changed."}
    if operation == "inspect_result" and step.get("id") == "vantage":
        return {"ok": True, "mutation": False, "category": "A",
                "message": "Nothing further is established from there. No hidden road, room, or passage was added."}
    if operation == "establish":
        return _apply_establish(session, scene)
    if operation == "stand":
        ledger = _ledger(session)
        prior = dict(ledger.get("posture") or {})
        sid = str(_inner(scene).get("id") or "")
        if prior.get("kind") == "sitting" and prior.get("scene_id") == sid:
            ledger["posture"] = {"kind": "standing", "seat_id": prior.get("seat_id"), "scene_id": sid}
            _consequence(session, scene, target=prior.get("seat_id") or "posture", operation="stand",
                         prior={"posture": "sitting"}, result={"posture": "standing"})
            return {"ok": True, "message": "You stand.", "mutation": True, "category": "A"}
        return {"ok": True, "message": "You are already standing.", "mutation": False, "category": "A"}
    if operation == "retreat":
        ledger = _ledger(session)
        current = dict(ledger.get("position") or {})
        sid = str(_inner(scene).get("id") or "")
        named = _retreat_subject(step.get("text") or "")
        beside = current.get("scene_id") == sid and current.get("kind") not in {None, "", "back"}
        label = str(current.get("label") or "")
        same = not named or bool(label) and (
            named.casefold() in label.casefold() or label.casefold() in named.casefold()
        )
        if not beside or not same:
            target = f"the {named}" if named else "anything"
            if beside and not same:
                message = (
                    f"You try to step back from {target}. You are beside the {label}, "
                    "so that step was not taken and your position is unchanged."
                )
            elif current.get("kind") == "back" and current.get("scene_id") == sid:
                message = f"You are already back from {target}. Stepping back again leaves your position unchanged."
            elif named:
                message = f"You try to step back from {target}. You are not beside it, so your position is unchanged."
            else:
                message = "You try to step back. You are not beside anything here, so your position is unchanged."
            return {"ok": True, "message": message, "mutation": False, "category": "A", "outcome": "no_op"}
        ledger["position"] = {"kind": "back", "target_id": current.get("target_id"), "scene_id": sid,
                              "label": current.get("label")}
        _consequence(session, scene, target=current.get("target_id") or "position", operation="retreat",
                     prior={"position": current.get("kind")}, result={"position": "back"})
        shown = label or named or "object"
        return {"ok": True, "message": f"You step back from the {shown}.",
                "mutation": True, "category": "A", "outcome": "success"}
    if operation == "inspect_result" and (step.get("id") == "doorway" or re.search(r"\bdoorway\b", step.get("text") or "", re.I)):
        answer = _state_answer("Is the doorway clear?", session, scene)
        return {"ok": True, "mutation": False, "category": "A", "message": answer["message"] if answer else "No doorway obstruction is established."}
    if operation == "inspect_result" and (step.get("id") == "inspection" or re.search(r"\b(?:inside|underneath|beneath)\b", step.get("text") or "", re.I)):
        return {"ok": True, "mutation": False, "category": "A",
                "message": "Nothing concealed is established there. No room, passage, or contents were created."}
    rows = _objects(session, scene)
    row = next((item for item in rows if item["id"] == step.get("id")), None)
    if row is None:
        return {"ok": False, "message": "That is not established here. Nothing further was changed.",
                "mutation": False, "category": "E"}
    fresh = _preconditions(row, operation, step.get("text") or operation)
    if operation in {"move", "push", "pull", "lift", "place", "open", "close", "sit", "approach", "climb"} and fresh["mode"] != "interact":
        return {"ok": False, "message": fresh["message"], "mutation": False, "category": fresh["category"],
                "mechanic": fresh.get("mechanic")}
    props = dict(row["properties"])
    check = _check(props) if fresh.get("requires_check") else None
    rolled = None
    if check:
        rolled = _roll(session, scene, row, check, character)
        if not rolled["success"]:
            return {"ok": False, "mutation": False, "category": "B", "rolled": rolled,
                    "message": (f"{check['skill'].title()} check: d20 {rolled['roll']} + {rolled['modifier']} = {rolled['total']} "
                                f"against DC {rolled['difficulty']}. The attempt fails. The {row['label']} is unchanged.")}
    if operation == "sit":
        ledger = _ledger(session)
        prior = dict(ledger.get("posture") or {})
        if prior.get("kind") == "sitting" and prior.get("seat_id") == row["id"] and prior.get("scene_id") == row["scene_id"]:
            return {"ok": True, "mutation": False, "category": "A", "rolled": rolled,
                    "message": _sit_message(row["label"], already=True)}
        ledger["posture"] = {"kind": "sitting", "seat_id": row["id"], "scene_id": row["scene_id"]}
        _remember(session, row["id"])
        _consequence(session, scene, target=row["id"], operation="sit",
                     prior={"posture": prior.get("kind")}, result={"posture": "sitting", "seat_id": row["id"]})
        return {"ok": True, "mutation": True, "category": "A", "rolled": rolled, "message": _sit_message(row["label"])}
    if operation == "approach":
        ledger = _ledger(session)
        prior = dict(ledger.get("position") or {})
        ledger["position"] = {"kind": "beside", "target_id": row["id"], "scene_id": row["scene_id"], "label": row["label"]}
        _remember(session, row["id"])
        _consequence(session, scene, target=row["id"], operation="approach",
                     prior={"position": prior.get("kind")}, result={"position": "beside", "target_id": row["id"]})
        return {"ok": True, "mutation": True, "category": "A", "message": f"You move beside the {row['label']}."}
    if operation == "inspect_result":
        _remember(session, row["id"])
        position = row["properties"].get("position")
        message = f"The {row['label']} is {position}." if position else f"Nothing concealed is established about the {row['label']}."
        return {"ok": True, "mutation": False, "category": "A", "message": message}
    if operation == "climb":
        if not rolled:
            return {"ok": False, "mutation": False, "category": "D",
                    "message": f"{row['label']} is here, but no climbing check is configured, so the climb is not resolved and your position is unchanged."}
        _ledger(session)["position"] = {"kind": "elevated", "target_id": row["id"], "scene_id": row["scene_id"], "label": row["label"]}
        _consequence(session, scene, target=row["id"], operation="climb", prior={"position": "ground"}, result={"position": "elevated"})
        return {"ok": True, "mutation": True, "category": "B", "rolled": rolled,
                "message": (f"{check['skill'].title()} check: d20 {rolled['roll']} + {rolled['modifier']} = {rolled['total']} "
                            f"against DC {rolled['difficulty']}. You reach the {row['label']}. No additional view is established.")}
    if operation in {"open", "close"}:
        new_open = operation == "open"
        if bool(props.get("open")) == new_open:
            return {"ok": True, "mutation": False, "category": "A", "rolled": rolled,
                    "message": f"The {row['label']} is already {'open' if new_open else 'closed'}. It stays that way."}
        prior = {"open": props.get("open")}
        props["open"] = new_open
        _write_props(session, row, props)
        _remember(session, row["id"])
        _consequence(session, scene, target=row["id"], operation=operation, prior=prior, result={"open": new_open})
        extra = " No further space is established beyond it." if new_open else ""
        prefix = ""
        if rolled:
            prefix = (f"{check['skill'].title()} check: d20 {rolled['roll']} + {rolled['modifier']} = {rolled['total']} "
                      f"against DC {rolled['difficulty']}. ")
        return {"ok": True, "mutation": True, "category": "B" if rolled else "A", "rolled": rolled,
                "message": f"{prefix}You {operation} the {row['label']}. It is now {'open' if new_open else 'closed'}.{extra}"}
    if operation in {"move", "push", "pull", "lift", "place"}:
        dest = {"position": "raised in place"} if operation == "lift" else (
            {"position": "aside from where it was"} if operation == "place" else _destination(step.get("text") or "", row)
        )
        if dest.get("valid") is False:
            return {"ok": False, "mutation": False, "category": "E",
                    "message": f"That is not an established place to move the {row['label']}. It is unchanged."}
        new_position = dest.get("position")
        if props.get("position") == new_position:
            return {"ok": True, "mutation": False, "category": "A",
                    "message": f"The {row['label']} is already {new_position}. It stays there."}
        prior = {"position": props.get("position"), "obstructs": props.get("obstructs")}
        props["position"] = new_position
        if dest.get("clear") == "doorway":
            props.pop("obstructs", None)
        _write_props(session, row, props)
        _remember(session, row["id"])
        _consequence(session, scene, target=row["id"], operation=operation, prior=prior,
                     result={"position": new_position, "obstructs": props.get("obstructs")})
        return {"ok": True, "mutation": True, "category": "A",
                "message": f"You {operation} the {row['label']}. It is now {new_position}."}
    return {"ok": False, "mutation": False, "category": "D", "message": "That action was not carried out."}


def _sit_message(label, already=False) -> str:
    if label == "ordinary stone seat":
        return "You are already seated on the accessible ordinary stone seat." if already else "You sit on the accessible ordinary stone seat."
    return f"You are already seated on the {label}." if already else f"You sit on the {label}."


def _apply_establish(session, scene) -> dict:
    anchor = _stone_anchor(scene)
    sid = str(_inner(scene).get("id") or "")
    active = session.get("active_scene_id")
    if anchor is None or (active and active != sid):
        return {"ok": False, "mutation": False, "category": "D",
                "message": "The public scene does not support that ordinary object. Nothing has been added."}
    ident = _fitting_id(session, sid)
    existing = next((row for row in _objects(session, scene) if row["id"] == ident), None)
    if existing:
        return {"ok": True, "mutation": False, "category": "A",
                "message": existing["entry"]["content"] + " It has not been moved."}
    description = "A small loose stone lies beside the established stonework."
    entry = {
        "id": ident, "campaign_id": session.get("campaign_run_id"), "scene_id": sid, "category": "C",
        "family": "fitting", "entity_type": "object", "label": "ordinary loose stone",
        "aliases": ["loose stone", "small stone", "small loose stone"],
        "content": description, "canonical_description": description,
        "properties": {"material": "stone", "size": "small", "weight": "light", "mobility": "movable",
                       "accessible": True, "visible": True, "position": "beside the stonework", "use": "none"},
        "anchor": anchor[0], "provenance": "accepted_improvisation", "source": "physical_adjudication",
        "creation_turn": int(session.get("turn_counter") or 0), "visibility": "public", "status": "accepted",
        "authority": "controlled_world_fact", "truth_status": "runtime_incidental", "scope": "scene",
        "persistence_status": "campaign", "interactions": [],
    }
    _ledger(session).setdefault("entries", []).append(entry)
    _remember(session, ident)
    _consequence(session, scene, target=ident, operation="establish", prior={"present": False},
                 result={"present": True, "position": "beside the stonework"})
    return {"ok": True, "mutation": True, "category": "A",
            "message": description + " It is ordinary and light enough to shift. It has not been moved."}


def commit_physical(scene, session, world, action, *, prompt, action_id, label, character=None):
    """Commit one revalidated plan inside the existing exploration result."""
    from game.models import ExplorationEngineResult
    started = time.perf_counter()
    plan = plan_physical(prompt, session=session, scene=scene, world=world)
    if not plan or plan.get("id") != action.get("target_id") or plan.get("mode") != "interact":
        return None
    if character is None:
        try:
            from game.storage import load_character
            character = load_character()
        except Exception:
            character = {}
    steps = plan.get("steps") or [dict(plan, text=prompt)]
    for step in steps:
        step.setdefault("text", prompt)
        step.setdefault("step_id", "s1")
        step.setdefault("depends_on", [])
        step.setdefault("dependency_kind", "independent")
        step.setdefault("status", "READY" if step.get("mode") == "interact" else "PROPOSED")
    messages = [plan.get("preface") or ""]
    mutation = False
    success = True
    category = plan.get("category")
    rolled = None
    failed_ids = set()
    uncertain_stop = False
    for index, step in enumerate(steps):
        if uncertain_stop or any(dep in failed_ids for dep in step.get("depends_on") or []):
            blocked = any(dep in failed_ids for dep in step.get("depends_on") or [])
            step["status"] = "BLOCKED" if blocked else "SKIPPED"
            step["failure_reason"] = "dependency" if blocked else "unattempted"
            step["publication"] = "withheld"
            if blocked:
                messages.append("A later part was not attempted, because it depended on a step that did not succeed.")
            else:
                messages.append("The rest was not attempted.")
            success = False
            continue
        if step.get("condition"):
            bound = _row_by_id(session, scene, steps[index - 1].get("id") if index else None)
            state = _condition_state(step["condition"], session, scene, bound=bound)
            if not state.get("known") or not state.get("satisfied"):
                step["status"] = "SKIPPED"
                unknown = not state.get("known")
                step["failure_reason"] = "condition_unknown" if unknown else "condition_false"
                step["publication"] = "player"
                messages.append("That condition is not established, so the next part was skipped." if unknown
                                else "That condition was not met, so the next part was skipped. Nothing further was invented.")
                failed_ids.add(step["step_id"])
                success = False
                continue
        step["status"] = "EXECUTING"
        outcome = _apply(step, session, scene, character)
        messages.append(outcome["message"])
        mutation = mutation or bool(outcome.get("mutation"))
        rolled = outcome.get("rolled") or rolled
        category = outcome.get("category") or category
        if outcome["ok"]:
            step["status"] = "SUCCEEDED"
            step["publication"] = "player"
            step["authoritative_result"] = {"mutation": bool(outcome.get("mutation"))}
            if outcome.get("mutation"):
                receipts = _ledger(session).get("physical_consequences") or []
                if receipts:
                    step["consequence_id"] = receipts[-1].get("id")
        else:
            success = False
            message = (outcome.get("message") or "").casefold()
            unsupported = bool(outcome.get("mechanic") or step.get("operation") in {"traverse", "gesture"}
                               or "no climbing check" in message or "no strength check" in message or "not configured" in message)
            step["status"] = "UNSUPPORTED" if unsupported else "FAILED"
            step["failure_reason"] = step["status"].lower()
            step["publication"] = "player"
            failed_ids.add(step["step_id"])
            if index + 1 < len(steps):
                nxt = steps[index + 1]
                if nxt.get("dependency_kind") == "uncertain" and step["step_id"] not in (nxt.get("depends_on") or []):
                    uncertain_stop = True
                    messages.append("The earlier part stands. What follows was not attempted, because it is not clearly independent.")
    publication = " ".join(part for part in messages if part).strip()
    _record_plan(session, scene, steps)
    operations = [step.get("operation") for step in steps]
    stamp = _STAMPS.get((id(session), prompt))
    provider_plan = "not_used"
    if isinstance(stamp, dict) and stamp.get("accepted") and stamp.get("operations") == operations:
        provider_plan = "accepted"
        stamp["used"] = True
    contract = "ADJUDICATION_RESULT" if success and mutation else (
        "UNSUPPORTED_ACTION" if not success else "FINAL_ENGINE_RESPONSE"
    )
    metadata = {
        "engine_publication": publication,
        "skip_unrelated_clue_discovery": True,
        "publication_contract": contract,
        "skip_primary_narration": contract != "ADJUDICATION_RESULT",
        "controlled_world_fact": True,
        "physical_adjudication": {
            "category": category, "operation": plan.get("operation"), "target_id": plan.get("id"),
            "requires_check": bool(plan.get("requires_check") or rolled), "mechanic": plan.get("mechanic"),
            "mutation": mutation, "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "invented_dc": False, "invented_roll": False,
            "provider_plan": provider_plan,
            "step_results": [
                {"id": step.get("step_id"), "status": step.get("status"), "operation": step.get("operation"),
                 "dependency": step.get("dependency_kind")}
                for step in steps
            ],
        },
    }
    if rolled:
        metadata["physical_adjudication"]["difficulty"] = rolled.get("difficulty")
    result = ExplorationEngineResult(
        kind="interact", action_id=action_id, label=label, prompt=prompt, success=success,
        resolved_transition=False, target_scene_id=None, clue_id=None, discovered_clues=[],
        state_changes={"physical_operation": plan.get("operation"), "mutation": mutation},
        metadata=metadata, skill_check=rolled,
    )
    return result.to_dict()


def validate_provider_interpretation(raw, *, session, scene, world) -> dict[str, Any]:
    """A proposal may name an operation and an existing target. It cannot decide success."""
    if not isinstance(raw, dict):
        return {"accepted": False, "reason": "malformed"}
    if set(raw) - {"operation", "target_ref"}:
        return {"accepted": False, "reason": "invented_outcome_or_hidden_field"}
    operation = str(raw.get("operation") or "")
    target = str(raw.get("target_ref") or "")
    if operation not in ROUTINES | {"climb", "take", "drop"}:
        return {"accepted": False, "reason": "unsupported_operation"}
    known = {row["id"] for row in _objects(session, scene)} | {"posture", "position"}
    if target and target not in known:
        return {"accepted": False, "reason": "invented_target"}
    blob = json.dumps(raw).casefold()
    if "sentinel" in blob or "hidden_facts" in blob:
        return {"accepted": False, "reason": "hidden_information"}
    return {"accepted": True, "reason": "interpretation_only", "operation": operation, "target_ref": target}


def interpret_with_provider(text, *, session, scene, world, invoke=None) -> dict[str, Any]:
    """One bounded interpretation attempt. The host still adjudicates any later action."""
    global _REQUESTS, _TOKENS
    started = time.perf_counter()
    deterministic = plan_physical(text, session=session, scene=scene, world=world)
    if deterministic and deterministic.get("mode") == "interact":
        return {"accepted": False, "reason": "deterministic", "committed": False, "retries": 0}
    try:
        if invoke is not None:
            raw = invoke(text)
        else:
            if os.environ.get(PROVIDER_GATE) != "1" or os.environ.get("ASHEN_DISABLE_PROVIDER_CALLS") == "1":
                raise RuntimeError("provider_disabled")
            if _REQUESTS >= _MAX_REQUESTS or _TOKENS >= _MAX_TOKENS:
                raise RuntimeError("provider_budget")
            from openai import OpenAI
            from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
            from game.provider_budget import admit_request, sdk_retry_options
            schema = {"type": "object", "additionalProperties": False, "required": ["operation", "target_ref"],
                      "properties": {"operation": {"type": "string"}, "target_ref": {"type": "string"}}}
            messages = [{"role": "system", "content": "Name one ordinary physical operation and an existing target id. Do not declare success, a roll, or a difficulty."},
                        {"role": "user", "content": text}]
            attempt = admit_request(purpose="physical_interpretation", owner="physical_adjudication",
                                    model=DEFAULT_MODEL_NAME, estimated_input=400, max_output=80)
            if attempt.refusal:
                raise RuntimeError("provider_admission_refused")
            response = attempt.dispatch(OpenAI(api_key=get_openai_api_key(), timeout=30, **sdk_retry_options()).responses.create,
                                       model=DEFAULT_MODEL_NAME, input=messages, max_output_tokens=80,
                                       text={"format": {"type": "json_schema", "name": "physical_interpretation", "strict": True, "schema": schema}})
            raw = json.loads(response.output_text)
            usage = response.usage
            _TOKENS += int(getattr(usage, "total_tokens", 0) or 0)
            attempt.finish({"purpose": "physical_interpretation", "sent": True, "model": response.model,
                            "request_id": response.id, "input_tokens": usage.input_tokens,
                            "output_tokens": usage.output_tokens, "total_tokens": usage.total_tokens})
        _REQUESTS += 1
        verdict = validate_provider_interpretation(raw, session=session, scene=scene, world=world)
        if verdict["accepted"] and deterministic and deterministic.get("operation") not in {None, verdict["operation"]}:
            verdict = {"accepted": False, "reason": "deterministic_disagreement", "operation": verdict["operation"]}
        if verdict["accepted"] and deterministic and deterministic.get("candidates") and verdict.get("target_ref") not in deterministic["candidates"]:
            verdict = {"accepted": False, "reason": "not_a_candidate"}
        verdict.update(committed=False, retries=0, latency_ms=round((time.perf_counter() - started) * 1000, 3))
        _LOG.append({"player_text": text, "result": "accepted" if verdict["accepted"] else "rejected",
                     "reason": verdict["reason"], "committed": False})
        return verdict
    except Exception as exc:
        _REQUESTS += 0 if isinstance(exc, RuntimeError) and str(exc) in {"provider_disabled", "provider_budget"} else 1
        _LOG.append({"player_text": text, "result": "rejected", "reason": type(exc).__name__, "committed": False})
        return {"accepted": False, "reason": type(exc).__name__, "committed": False, "retries": 0,
                "latency_ms": round((time.perf_counter() - started) * 1000, 3)}


_OP_ALIAS = {
    "look": "inspect_result", "inspect": "inspect_result", "examine": "inspect_result",
    "check": "inspect_result", "read": "inspect_result", "survey": "inspect_result",
    "peer": "inspect_result", "opening": "open", "unlatch": "open", "shut": "close",
    "heave": "lift", "shove": "push", "nudge": "push", "slide": "move", "shift": "move",
}
_PLAN_FIELDS = {"operation", "target_ref", "depends_on", "condition"}
_PLAN_OPERATIONS = ROUTINES | {"climb", "take", "drop", "gesture", "traverse", "inspect_result"}


def validate_provider_plan(raw, *, session, scene, world) -> dict[str, Any]:
    """A proposal may name ordered steps. It cannot execute them or decide success."""
    if not isinstance(raw, dict) or set(raw) - {"steps"}:
        return {"accepted": False, "reason": "malformed"}
    steps = raw.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= _MAX_STEPS:
        return {"accepted": False, "reason": "bound"}
    known = {row["id"] for row in _objects(session, scene)} | {"posture", "position", "inspection", "doorway", "vantage", ""}
    clean = []
    seen = set()
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or set(step) - _PLAN_FIELDS:
            return {"accepted": False, "reason": "unauthorized_field"}
        operation = str(step.get("operation") or "")
        target = str(step.get("target_ref") or "")
        depends = step.get("depends_on") or []
        condition = str(step.get("condition") or "")
        operation = _OP_ALIAS.get(operation, operation)
        if operation not in _PLAN_OPERATIONS:
            return {"accepted": False, "reason": "unauthorized_operation"}
        if target not in known:
            return {"accepted": False, "reason": "invented_target"}
        if not isinstance(depends, list) or any(type(item) is not int or item < 0 or item >= index for item in depends):
            return {"accepted": False, "reason": "invalid_dependency"}
        blob = json.dumps(step).casefold()
        if "sentinel" in blob or "hidden_facts" in blob or "success" in step or "dc" in step:
            return {"accepted": False, "reason": "hidden_or_outcome"}
        seen.add(index)
        clean.append({"operation": operation, "target_ref": target, "depends_on": depends, "condition": condition})
    return {"accepted": True, "reason": "interpretation_only", "steps": clean, "committed": False}


def _deterministic_operations(plan) -> list[str]:
    if not plan:
        return []
    steps = plan.get("steps") or [plan]
    return [str(step.get("operation") or "") for step in steps]


def interpret_plan_with_provider(text, *, session, scene, world, invoke=None) -> dict[str, Any]:
    """Validate one bounded plan proposal. Execution remains in commit_physical."""
    global _REQUESTS, _TOKENS
    started = time.perf_counter()
    deterministic = plan_physical(text, session=session, scene=scene, world=world)
    expected = _deterministic_operations(deterministic)
    try:
        if invoke is not None:
            raw = invoke(text)
        else:
            if os.environ.get(PROVIDER_GATE) != "1" or os.environ.get("ASHEN_DISABLE_PROVIDER_CALLS") == "1":
                raise RuntimeError("provider_disabled")
            if _REQUESTS >= _MAX_REQUESTS or _TOKENS >= _MAX_TOKENS:
                raise RuntimeError("provider_budget")
            from openai import OpenAI
            from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
            from game.provider_budget import admit_request, sdk_retry_options
            visible = [{"id": row["id"], "label": row["label"]} for row in _objects(session, scene)]
            schema = {
                "type": "object", "additionalProperties": False, "required": ["steps"],
                "properties": {"steps": {"type": "array", "maxItems": 3, "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["operation", "target_ref", "depends_on", "condition"],
                    "properties": {
                        "operation": {"type": "string"}, "target_ref": {"type": "string"},
                        "depends_on": {"type": "array", "items": {"type": "integer"}},
                        "condition": {"type": "string"},
                    },
                }}},
            }
            messages = [
                {"role": "system", "content": "Propose at most three physical steps. Use only a visible target id. Do not declare success, a roll, a difficulty, or hidden information."},
                {"role": "user", "content": json.dumps({"player": text, "visible_targets": visible, "operations": sorted(_PLAN_OPERATIONS)})},
            ]
            attempt = admit_request(purpose="physical_plan", owner="physical_adjudication",
                                    model=DEFAULT_MODEL_NAME, estimated_input=500, max_output=180)
            if attempt.refusal:
                raise RuntimeError(attempt.refusal)
            response = attempt.dispatch(
                OpenAI(api_key=get_openai_api_key(), timeout=45, **sdk_retry_options()).responses.create,
                model=DEFAULT_MODEL_NAME, input=messages, max_output_tokens=180,
                text={"format": {"type": "json_schema", "name": "physical_plan", "strict": True, "schema": schema}},
            )
            raw = json.loads(response.output_text)
            usage = response.usage
            _TOKENS += int(getattr(usage, "total_tokens", 0) or 0)
            attempt.finish({"purpose": "physical_plan", "sent": True, "model": response.model,
                            "request_id": response.id, "input_tokens": usage.input_tokens,
                            "output_tokens": usage.output_tokens, "total_tokens": usage.total_tokens})
        _REQUESTS += 1
        verdict = validate_provider_plan(raw, session=session, scene=scene, world=world)
        if verdict["accepted"] and [step["operation"] for step in verdict["steps"]] != expected:
            verdict = {"accepted": False, "reason": "deterministic_disagreement", "committed": False,
                       "proposed": [step["operation"] for step in verdict.get("steps") or []]}
        if verdict["accepted"]:
            _STAMPS[(id(session), text)] = {"accepted": True, "operations": expected, "prompt": text, "used": False}
        verdict.update(committed=False, retries=0, executed=False,
                       latency_ms=round((time.perf_counter() - started) * 1000, 3))
        _LOG.append({"player_text": text, "result": "accepted" if verdict["accepted"] else "rejected",
                     "reason": verdict.get("reason"), "committed": False})
        return verdict
    except Exception as exc:
        counted = not (isinstance(exc, RuntimeError) and str(exc) in {"provider_disabled", "provider_budget"})
        if counted:
            _REQUESTS += 1
        _LOG.append({"player_text": text, "result": "rejected", "reason": type(exc).__name__, "detail": str(exc)[:180], "committed": False})
        return {"accepted": False, "reason": type(exc).__name__, "detail": str(exc)[:180], "committed": False, "retries": 0, "executed": False,
                "latency_ms": round((time.perf_counter() - started) * 1000, 3)}
