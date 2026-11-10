"""Bounded physical marking for one established object, source, and medium.

Recognition and resolution are pure. The API turn commits through the existing
marking and visibility services. Player wording is not evidence that a
garment, material, or hidden text exists.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

from game.object_instances import inspect_object_identity
from game.object_marking import (
    PRECONDITIONS,
    VISIBILITY_PRECONDITIONS,
    prepare_marking,
    prepare_visibility,
    request_digest,
    _establish_visibility_authorization,
)

_LEAD = re.compile(
    r"^\s*(?:(?:i|we)\s+(?:(?:will|'ll|ll)\s+)?)?(?:(?:try|attempt)(?:\s+to)?\s+)?"
    r"(?:(?:secretly|quietly|carefully)\s+|in\s+secret\s+)?"
    r"(?P<verb>copy|write|jot|scribble|mark|inscribe|scratch|engrave|carve|etch)\s+"
    r"(?P<rest>.+?)\s*$",
    re.IGNORECASE,
)
_USE = re.compile(
    r"^\s*(?:(?:i|we)\s+)?(?:use|using)\s+(?P<medium>.+?)\s+to\s+"
    r"(?P<verb>copy|write|jot|scribble|mark|inscribe)\s+(?P<rest>.+?)\s*$",
    re.IGNORECASE,
)
_DEST = re.compile(
    r"^(?P<content>.+?)\s+(?P<prep>onto|on|into)\s+(?P<target>.+?)"
    r"(?:\s+(?:using|with)\s+(?P<medium>.+))?$",
    re.IGNORECASE,
)
_DELEGATED = re.compile(
    r"\b(?:tell|ask|order|have|make)\s+\S+\s+(?:to\s+)?(?:write|copy|mark|inscribe|jot)\b",
    re.IGNORECASE,
)
_NOT_MARKING = re.compile(
    r"\b(?:remember|recall|mental note|in my head|fighting stance|fighting style)\b",
    re.IGNORECASE,
)
_PURPOSE = re.compile(r"\s+\b(?:so|because|to remember|to forget)\b.*$", re.IGNORECASE)
_DESTRUCTIVE = frozenset({"scratch", "engrave", "carve", "etch"})
_ORDINARY = frozenset({"copy", "write", "jot", "scribble", "mark", "inscribe"})
_GENERIC_CONTENT = frozenset({
    "warning", "message", "name", "words", "wording", "text", "note", "notes", "writing",
})
_CONTENT_STOP = frozenset({
    "the", "a", "an", "my", "our", "this", "that", "those", "these", "some", "of", "to",
})
_PREFIXES = (
    "my ", "the ", "a ", "an ", "this ", "that ", "some ", "available ",
    "bit of ", "piece of ", "dab of ",
)


def recognize_marking(text: str | None) -> dict[str, Any] | None:
    """Return a structured proposal, or None when this is not that action class."""
    raw = " ".join(str(text or "").split())
    if not raw or "?" in raw or _DELEGATED.search(raw) or _NOT_MARKING.search(raw):
        return None
    used = _USE.search(raw)
    if used:
        verb = used.group("verb").casefold()
        rest = _PURPOSE.sub("", used.group("rest").strip())
        medium = used.group("medium").strip()
        dest = _DEST.search(rest)
        if dest is None:
            return _proposal(raw, verb, "", "", "", "", False)
        return _proposal(
            raw, verb, dest.group("prep").casefold(), dest.group("target"),
            dest.group("content"), medium, _destructive(verb, dest.group("prep")),
        )
    lead = _LEAD.search(raw)
    if lead is None:
        return None
    verb = lead.group("verb").casefold()
    rest = _PURPOSE.sub("", lead.group("rest").strip())
    dest = _DEST.search(rest)
    if dest is None:
        return None
    medium = (dest.group("medium") or "").strip()
    return _proposal(
        raw, verb, dest.group("prep").casefold(), dest.group("target"),
        dest.group("content"), medium, _destructive(verb, dest.group("prep")),
    )


def resolve_marking(proposal: Mapping[str, Any], character: Mapping[str, Any],
                    session: Mapping[str, Any]) -> dict[str, Any]:
    """Bind a proposal to authoritative records. Missing facts stay missing."""
    if proposal.get("destructive") or proposal.get("operation") not in _ORDINARY:
        return _unresolved(proposal, ["destructive"])
    if proposal.get("preparation") == "into":
        return _unresolved(proposal, ["destructive"])
    missing: list[str] = []
    target = _resolve_target(proposal.get("target_phrase") or "", character, session)
    if target is None:
        missing.append("ambiguous_target" if _target_matches(proposal.get("target_phrase") or "", character) > 1 else "target")
    elif target.get("error") == "surface":
        missing.append("surface")
    elif target.get("error") == "ambiguous":
        missing.append("ambiguous_target")
    elif target.get("error"):
        missing.append("target")
    medium = _resolve_medium(proposal.get("medium_phrase") or "", character)
    if not proposal.get("medium_phrase"):
        missing.append("medium")
        medium = None
    elif medium is None:
        missing.append("ambiguous_medium" if _medium_matches(proposal.get("medium_phrase") or "", character) > 1 else "medium")
    content = _resolve_content(proposal.get("content_phrase") or "", session)
    if content is None:
        missing.append("content")
    elif content.get("ambiguous"):
        missing.append("ambiguous_content")
        content = None
    if not _capable(character):
        missing.append("capability")
    if target and not target.get("error") and medium and not _compatible(target, medium):
        missing.append("compatibility")
    if medium and medium.get("consumption") == "required":
        missing.append("consumption")
    if (target and target.get("mechanics") == "required") or (medium and medium.get("mechanics") == "required"):
        missing.append("mechanics")
    if missing:
        return _unresolved(proposal, missing)
    concealed = bool(re.search(r"\b(?:secretly|concealed|in secret)\b", str(proposal.get("utterance") or ""), re.I))
    evidence = {
        "target_exists": _ref("object", target["instance_id"]),
        "accessible": _ref("access", target["instance_id"]),
        "rights": "possessor",
        "writable_surface": _ref("surface", target["surface_id"]),
        "medium_available": _ref("medium", medium["item_id"]),
        "medium_compatible": _ref("compatible", target["kind"]),
        "source_disclosed": _ref("source", content["reference"]),
        "capability": "ordinary_marking_unblocked",
    }
    return {
        "outcome": "ready",
        "proposal": dict(proposal),
        "missing": [],
        "player_text": "",
        "instance_id": target["instance_id"],
        "expected_revision": target["revision"],
        "surface_name": target["surface_name"],
        "medium_name": medium["name"],
        "content": content["text"],
        "source": {"kind": content["kind"], "reference": content["reference"]},
        "visibility": {"classification": "concealed" if concealed else "visible"},
        "evidence": evidence,
        "campaign_run_id": str(session.get("campaign_run_id") or ""),
        "character_id": str(character.get("id") or ""),
    }


def stage_grounded_marking(character: dict, resolution: Mapping[str, Any], operation_id: str) -> dict[str, Any]:
    """Stage marking and visibility together. The caller saves one character.

    A repeated operation id replays the stored request. Changed content under
    that same id conflicts and does not write a second marking.
    """
    if resolution.get("outcome") != "ready":
        return {"outcome": "rejected", "committed": False, "error": "not_ready"}
    request_id = _operation_request_id(operation_id, "add_marking")
    existing = _existing_mark(character, request_id)
    if existing is not None:
        row, mark = existing
        if mark.get("content") != resolution.get("content"):
            return {"outcome": "technical_failure", "committed": False, "error": "conflicting_request",
                    "request_id": request_id}
        marking_request = _request_from_mark(resolution, row, mark)
    else:
        marking_request = _marking_request(resolution, operation_id)
    marking = prepare_marking(character, marking_request)
    if marking.get("status") == "rejected":
        return {"outcome": "technical_failure", "committed": False, "error": marking.get("error"),
                "request_id": marking_request["request_id"]}
    modification_id = marking["result"]["modification_id"]
    expected = marking["result"]["resulting_revision"] if marking.get("status") == "replay" else marking["result"]["resulting_revision"]
    host = character if marking.get("status") == "replay" else marking["character"]
    visibility_request = _visibility_request(resolution, operation_id, modification_id, expected)
    authorization = _establish_visibility_authorization(visibility_request)
    visibility = prepare_visibility(host, visibility_request, authorization=authorization)
    if visibility.get("status") == "rejected":
        return {"outcome": "technical_failure", "committed": False, "error": visibility.get("error"),
                "request_id": marking_request["request_id"]}
    staged = host if visibility.get("status") == "replay" else visibility["character"]
    outcome = "replay" if marking.get("status") == "replay" else "staged"
    return {
        "outcome": outcome,
        "committed": outcome == "replay",
        "character": staged,
        "marking": marking["result"],
        "visibility": visibility["result"],
        "content": _committed_content(staged, resolution["instance_id"], modification_id) or resolution["content"],
        "error": None,
    }


def player_outcome_text(resolution: Mapping[str, Any], *, content: str = "") -> str:
    """Player sentence from grounded facts only."""
    if resolution.get("outcome") != "ready":
        missing = list(resolution.get("missing") or ["target"])
        sentences = [_MISSING[item] for item in missing if item in _MISSING]
        if not sentences:
            sentences = ["The marking could not be confirmed."]
        return "Nothing was written. " + " ".join(sentences)
    surface = str(resolution.get("surface_name") or "surface")
    medium = str(resolution.get("medium_name") or "writing medium")
    verb = str((resolution.get("proposal") or {}).get("operation") or "mark")
    written = content or str(resolution.get("content") or "")
    visible = (resolution.get("visibility") or {}).get("classification") == "visible"
    ending = "The marking is on it now." if visible else "The marking is concealed."
    return f"You {verb} the known wording onto the {surface} with the {medium}. {ending} It reads: {written}"


def technical_player_text(error: str | None) -> str:
    if error == "conflicting_request":
        return "Nothing further was written."
    if error == "stale_revision":
        return "The object changed before the marking could be applied. Nothing was written."
    return "The marking could not be confirmed. Nothing was written."


_MISSING = {
    "target": "No established object matches what you tried to mark.",
    "ambiguous_target": "More than one established object matches.",
    "surface": "That object has no established surface for ordinary writing.",
    "medium": "No usable writing medium is established.",
    "ambiguous_medium": "More than one writing medium matches.",
    "compatibility": "That writing medium is not established as usable on that surface.",
    "content": "The wording to copy is not established.",
    "ambiguous_content": "More than one known wording matches what you asked to copy.",
    "capability": "You are not established as able to do that.",
    "mechanics": "That action needs a rules decision before it can be carried out.",
    "consumption": "Using up that writing medium cannot be recorded safely.",
    "destructive": "Scratching or engraving is not carried out as ordinary writing.",
}


def _phrase(text) -> str:
    return " ".join(str(text or "").split()).strip(" .")


def _proposal(utterance, verb, prep, target, content, medium, destructive) -> dict[str, Any]:
    return {
        "utterance": utterance,
        "operation": verb,
        "preparation": prep,
        "target_phrase": _phrase(target),
        "content_phrase": _phrase(content),
        "medium_phrase": _phrase(medium),
        "destructive": bool(destructive),
    }


def _destructive(verb: str, prep: str) -> bool:
    return verb in _DESTRUCTIVE or (verb == "inscribe" and prep.casefold() == "into") or prep.casefold() == "into"


def _unresolved(proposal, missing) -> dict[str, Any]:
    resolution = {"outcome": "unresolved", "proposal": dict(proposal), "missing": list(dict.fromkeys(missing))}
    resolution["player_text"] = player_outcome_text(resolution)
    return resolution


def _norm(text: str) -> str:
    phrase = re.sub(r"[^a-z0-9' ]+", " ", str(text or "").casefold())
    phrase = re.sub(r"\s+", " ", phrase).strip()
    changed = True
    while changed and phrase:
        changed = False
        for prefix in _PREFIXES:
            if phrase.startswith(prefix):
                phrase = phrase[len(prefix):].strip()
                changed = True
    return phrase


def _names(record: Mapping[str, Any], *fields: str) -> list[str]:
    found = []
    for field in fields:
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            found.append(_norm(value))
    aliases = record.get("aliases")
    if isinstance(aliases, list):
        found.extend(_norm(alias) for alias in aliases if isinstance(alias, str) and alias.strip())
    return [name for name in found if name]


def _phrase_matches(phrase: str, names: list[str]) -> bool:
    normal = _norm(phrase)
    if not normal:
        return False
    return any(normal == name or name.endswith(" " + normal) or normal.endswith(" " + name) for name in names)


def _surfaces(row: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    surfaces = row.get("marking_surfaces")
    if not isinstance(surfaces, list):
        return []
    return [surface for surface in surfaces if isinstance(surface, dict)]


def _target_matches(phrase: str, character: Mapping[str, Any]) -> int:
    count = 0
    for row in character.get("inventory") or []:
        if not isinstance(row, dict):
            continue
        object_match = _phrase_matches(phrase, _names(row, "name", "id"))
        surface_hits = [surface for surface in _surfaces(row) if _phrase_matches(phrase, _names(surface, "name", "id"))]
        if surface_hits or object_match:
            count += 1
    return count


def _medium_matches(phrase: str, character: Mapping[str, Any]) -> int:
    count = 0
    for row in character.get("inventory") or []:
        if isinstance(row, dict) and isinstance(row.get("marking_medium"), dict):
            if _phrase_matches(phrase, _names(row["marking_medium"], "name", "id") + _names(row, "name")):
                count += 1
    return count


def _resolve_target(phrase: str, character: Mapping[str, Any], session: Mapping[str, Any]):
    hits = []
    inventory = character.get("inventory")
    if not isinstance(inventory, list):
        return None
    for index, row in enumerate(inventory):
        if not isinstance(row, dict):
            continue
        surfaces = _surfaces(row)
        surface_hits = [surface for surface in surfaces if _phrase_matches(phrase, _names(surface, "name", "id"))]
        object_match = _phrase_matches(phrase, _names(row, "name", "id"))
        if surface_hits:
            if len(surface_hits) != 1:
                return {"error": "ambiguous"}
            hits.append((index, row, surface_hits[0]))
        elif object_match:
            writable = [surface for surface in surfaces if surface.get("ordinary_writing") is True and surface.get("accessible") is True]
            if len(writable) == 1:
                hits.append((index, row, writable[0]))
            elif not writable:
                hits.append((index, row, None))
            else:
                return {"error": "surface"}
    if len(hits) != 1:
        return None
    index, row, surface = hits[0]
    if surface is None:
        return {"error": "surface"}
    if surface.get("ordinary_writing") is not True or surface.get("accessible") is not True:
        return {"error": "surface"}
    if row.get("usable") is not True or row.get("quantity") != 1:
        return {"error": "access"}
    identity = inspect_object_identity(character, index, campaign_run_id=str(session.get("campaign_run_id") or ""))
    if identity.status != "existing":
        return {"error": "identity"}
    return {
        "instance_id": row.get("instance_id"),
        "revision": row.get("revision"),
        "surface_id": str(surface.get("id") or surface.get("name") or "surface"),
        "surface_name": str(surface.get("name") or surface.get("id") or "surface"),
        "kind": str(surface.get("kind") or ""),
        "mechanics": surface.get("mechanics") or "not_applicable",
    }


def _resolve_medium(phrase: str, character: Mapping[str, Any]):
    if not phrase:
        return None
    hits = []
    for row in character.get("inventory") or []:
        if not isinstance(row, dict) or not isinstance(row.get("marking_medium"), dict):
            continue
        medium = row["marking_medium"]
        names = _names(medium, "name", "id") + _names(row, "name")
        if _phrase_matches(phrase, names):
            hits.append((row, medium))
    if len(hits) != 1:
        return None
    row, medium = hits[0]
    if medium.get("accessible") is not True or row.get("usable") is not True or not isinstance(row.get("quantity"), int) or row["quantity"] < 1:
        return None
    compatible = medium.get("compatible_surfaces")
    if not isinstance(compatible, list) or not all(isinstance(item, str) and item.strip() for item in compatible):
        return None
    return {
        "item_id": str(row.get("id") or medium.get("id") or "medium"),
        "name": str(medium.get("name") or row.get("name") or "medium"),
        "compatible": [str(item) for item in compatible],
        "consumption": medium.get("consumption") or "none",
        "mechanics": medium.get("mechanics") or "not_applicable",
    }


def _compatible(target, medium) -> bool:
    return bool(target.get("kind")) and target["kind"] in medium["compatible"]


def _capable(character: Mapping[str, Any]) -> bool:
    status = character.get("physical_status")
    if isinstance(status, dict) and status.get("ordinary_marking") == "unable":
        return False
    conditions = character.get("conditions")
    if isinstance(conditions, list):
        for condition in conditions:
            if isinstance(condition, dict) and condition.get("blocks_ordinary_marking") is True:
                return False
    return True


def _known_sources(session: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    knowledge = session.get("clue_knowledge")
    if isinstance(knowledge, dict):
        for clue_id, entry in knowledge.items():
            if not isinstance(entry, dict):
                continue
            text = entry.get("text")
            if not isinstance(text, str) or not text.strip():
                continue
            aliases = entry.get("aliases") if isinstance(entry.get("aliases"), list) else []
            rows.append({
                "id": str(clue_id),
                "text": text.strip(),
                "aliases": [alias.strip() for alias in aliases if isinstance(alias, str) and alias.strip()],
            })
    runtime = session.get("scene_runtime")
    if isinstance(runtime, dict):
        for data in runtime.values():
            if not isinstance(data, dict):
                continue
            for text in data.get("discovered_clues") or []:
                if isinstance(text, str) and text.strip() and all(row["text"] != text.strip() for row in rows):
                    rows.append({"id": "", "text": text.strip(), "aliases": []})
    return rows


def _resolve_content(phrase: str, session: Mapping[str, Any]):
    quoted = re.search(r'"([^"]+)"|\'([^\']+)\'', phrase or "")
    if quoted:
        literal = (quoted.group(1) or quoted.group(2) or "").strip()
        if literal:
            return {"text": literal, "kind": "explicit_literal", "reference": "player_utterance"}
    tokens = [token for token in re.findall(r"[a-z0-9']+", str(phrase or "").casefold()) if token not in _CONTENT_STOP and len(token) > 1]
    distinctive = [token for token in tokens if token not in _GENERIC_CONTENT]
    required = distinctive or tokens
    if not required:
        return None
    matches = []
    for row in _known_sources(session):
        hay = set(re.findall(r"[a-z0-9']+", " ".join([row["id"], row["text"], *row["aliases"]]).casefold()))
        if all(token in hay for token in required):
            matches.append(row)
    if len(matches) > 1:
        return {"ambiguous": True}
    if len(matches) != 1:
        return None
    reference = matches[0]["id"] or "known_text"
    return {"text": matches[0]["text"], "kind": "disclosed_copy", "reference": reference}


def _ref(label: str, value: str) -> str:
    return f"{label}:{value}"[:240]


def _operation_request_id(operation_id: str, kind: str) -> str:
    return hashlib.sha256(f"{operation_id}|{kind}".encode("utf-8")).hexdigest()


def _marking_request(resolution: Mapping[str, Any], operation_id: str) -> dict[str, Any]:
    content = str(resolution["content"])
    request = {
        "version": 1,
        "operation": "add_marking",
        "campaign_run_id": resolution["campaign_run_id"],
        "character_id": resolution["character_id"],
        "instance_id": resolution["instance_id"],
        "request_id": _operation_request_id(operation_id, "add_marking"),
        "expected_revision": resolution["expected_revision"],
        "content": content,
        "source": {"kind": resolution["source"]["kind"], "reference": resolution["source"]["reference"]},
        "authorization": {
            "caller_id": "grounded_marking_action",
            "decision_id": _operation_request_id(operation_id, "decision"),
            "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "preconditions": {key: resolution["evidence"][key] for key in PRECONDITIONS},
            "mechanics": "not_applicable",
        },
    }
    request["request_digest"] = request_digest(request)
    return request


def _visibility_request(resolution, operation_id, modification_id, expected_revision) -> dict[str, Any]:
    request = {
        "version": 1,
        "operation": "set_marking_visibility",
        "campaign_run_id": resolution["campaign_run_id"],
        "character_id": resolution["character_id"],
        "instance_id": resolution["instance_id"],
        "request_id": _operation_request_id(operation_id, "set_visibility"),
        "expected_revision": expected_revision,
        "modification_id": modification_id,
        "visibility": dict(resolution["visibility"]),
        "authorization": {
            "caller_id": "grounded_marking_action",
            "decision_id": _operation_request_id(operation_id, "visibility_decision"),
            "mechanics": "not_applicable",
            "preconditions": {
                "target_exists": resolution["evidence"]["target_exists"],
                "marking_exists": _ref("marking", modification_id),
                "rights": "possessor",
                "classification_basis": "actor_applied_ordinary_marking",
                "capability": "ordinary_marking_unblocked",
            },
        },
    }
    if set(request["authorization"]["preconditions"]) != VISIBILITY_PRECONDITIONS:
        raise RuntimeError("visibility preconditions drifted")
    request["request_digest"] = request_digest(request)
    return request


def _existing_mark(character, request_id):
    for row in character.get("inventory") or []:
        if not isinstance(row, dict):
            continue
        for mark in row.get("markings") or []:
            if isinstance(mark, dict) and mark.get("request_id") == request_id:
                return row, mark
    return None


def _request_from_mark(resolution, row, mark) -> dict[str, Any]:
    request = {
        "version": 1,
        "operation": "add_marking",
        "campaign_run_id": resolution["campaign_run_id"],
        "character_id": resolution["character_id"],
        "instance_id": row["instance_id"],
        "request_id": mark["request_id"],
        "expected_revision": mark["applied_revision"] - 1,
        "content": mark["content"],
        "source": mark["source"],
        "authorization": mark["authorization"],
    }
    request["request_digest"] = request_digest(request)
    return request


def _committed_content(character, instance_id, modification_id) -> str:
    for row in character.get("inventory") or []:
        if isinstance(row, dict) and row.get("instance_id") == instance_id:
            for mark in row.get("markings") or []:
                if isinstance(mark, dict) and mark.get("modification_id") == modification_id:
                    return str(mark.get("content") or "")
    return ""
