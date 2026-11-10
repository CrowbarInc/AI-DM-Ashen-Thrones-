"""Bounded physical removal of one established visible marking.

Recognition and resolution are pure. The chat turn commits through the existing
prepare_removal service. Player wording is not evidence that a marking, a
cleaning material, or a hidden inscription exists.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from game.marking_action import (
    _names,
    _norm,
    _operation_request_id,
    _phrase,
    _phrase_matches,
    _ref,
    _surfaces,
)
from game.object_instances import inspect_object_identity
from game.object_marking import LEDGER, REMOVAL_PRECONDITIONS, prepare_removal, request_digest

_LEAD = re.compile(
    r"^\s*(?:(?:i|we)\s+)?(?:(?:try|attempt)(?:\s+to)?\s+)?"
    r"(?P<verb>wipe|rub|erase|clean|remove|wash)"
    r"(?:\s+(?P<particle>away|off|out))?"
    r"\s+(?P<rest>.+?)\s*$",
    re.IGNORECASE,
)
_DEST = re.compile(
    r"^(?:the\s+)?(?P<marking>.+?)\s+(?P<prep>away from|off|from|on)\s+(?P<target>.+?)"
    r"(?:\s+(?:using|with)\s+(?P<resource>.+))?$",
    re.IGNORECASE,
)
_DELEGATED = re.compile(
    r"\b(?:tell|ask|order|have|make)\s+\S+\s+(?:to\s+)?(?:wipe|rub|erase|clean|remove|wash)\b",
    re.IGNORECASE,
)
_NOT_PHYSICAL = re.compile(r"\b(?:memory|mind|remember|recall|dream|thought|thoughts)\b", re.IGNORECASE)
_OBSERVATION = re.compile(
    r"^\s*(?:(?:i|we)\s+)?(?:examine|inspect|study|read|look|check|see)\b",
    re.IGNORECASE,
)
_PURPOSE = re.compile(r"\s+\b(?:so|because|to remember|to forget)\b.*$", re.IGNORECASE)
_MARKING_TOKENS = frozenset({
    "writing", "marking", "markings", "marks", "mark", "inscription", "inscriptions",
    "note", "notes", "words", "wording", "text", "message", "warning", "name",
    "ink", "letters", "lettering",
})
_CLASS = frozenset({
    "writing", "marking", "markings", "marks", "mark", "inscription", "inscriptions",
    "note", "notes", "words", "wording", "text", "message", "letters", "lettering",
})
_STOP = frozenset({
    "the", "a", "an", "my", "our", "this", "that", "those", "these", "some", "of", "to",
    "off", "from", "on", "it",
})
_PRONOUNS = frozenset({"there", "here", "it", "that", "them", "this"})
_FROM = frozenset({"erase", "remove"})
_DENIAL = re.compile(
    r"\b(?:nothing was removed|nothing further was removed|could not be removed|"
    r"was not removed|still (?:written|there|visible|reads|present)|remains)\b",
    re.IGNORECASE,
)
_ABSENCE = re.compile(r"\b(?:no longer|not there|gone)\b", re.IGNORECASE)
_CONSUMPTION = re.compile(r"\b(?:used up|consumed|ran out)\b", re.IGNORECASE)
_MISSING = {
    "target": "No established object matches what you tried to clean.",
    "ambiguous_target": "More than one established object matches.",
    "surface": "That object has no established surface you can reach.",
    "access": "You cannot reach that surface from here.",
    "reference": "Say which object you mean.",
    "marking": "No established marking matches what you tried to remove.",
    "ambiguous_marking": "More than one marking matches. Name the one you mean.",
    "method": "That marking is not established as removable that way.",
    "resource": "No established cleaning material is available for that.",
    "ambiguous_resource": "More than one cleaning material matches.",
    "consumption": "Using up that cleaning material cannot be recorded safely.",
    "capability": "You are not established as able to do that.",
    "mechanics": "That action needs a rules decision before it can be carried out.",
    "environment": "The conditions for that removal are not established.",
}


def recognize_removal(text: str | None) -> dict[str, Any] | None:
    """Return a structured removal proposal, or None when this is not that class."""
    raw = " ".join(str(text or "").split()).rstrip(".! ")
    if not raw or "?" in raw or _DELEGATED.search(raw) or _NOT_PHYSICAL.search(raw) or _OBSERVATION.search(raw):
        return None
    lead = _LEAD.search(raw)
    if lead is None:
        return None
    verb = lead.group("verb").casefold()
    rest = _PURPOSE.sub("", lead.group("rest").strip())
    dest = _DEST.search(rest)
    if dest is not None:
        marking = _phrase(dest.group("marking"))
        if not _has_marking_token(marking):
            return None
        return _proposal(raw, verb, marking, _phrase(dest.group("target")), _phrase(dest.group("resource") or ""))
    if _has_marking_token(rest):
        return _proposal(raw, verb, _phrase(rest), "", "")
    return None


def resolve_removal(proposal: Mapping[str, Any], character: Mapping[str, Any],
                    session: Mapping[str, Any]) -> dict[str, Any]:
    """Bind one visible marking. Missing facts stay missing and do not mutate."""
    resolution = _blank(proposal, character, session)
    missing: list[str] = []
    if _removal_blocked(character):
        missing.append("capability")
    target = _resolve_target(str(proposal.get("target_phrase") or ""), character, session)
    if target.get("error"):
        missing.append({
            "ambiguous": "ambiguous_target",
            "surface": "surface",
            "access": "access",
            "reference": "reference",
        }.get(target["error"], "target"))
    else:
        resolution["instance_id"] = target["instance_id"]
        resolution["expected_revision"] = target["revision"]
        resolution["surface_name"] = target["surface_name"]
        resolution["surface_kind"] = target["kind"]
    mark = None
    if not target.get("error"):
        visible = _visible_marks(target["row"])
        hits = _match_marks(str(proposal.get("marking_phrase") or ""), visible, character)
        if len(hits) > 1:
            missing.append("ambiguous_marking")
        elif len(hits) != 1:
            missing.append("marking")
        else:
            mark = hits[0]
            resolution["modification_id"] = mark.get("modification_id")
            resolution["content"] = str(mark.get("content") or "")
    if mark is not None and "capability" not in missing:
        _feasibility(proposal, target, mark, character, missing)
    if missing:
        resolution["missing"] = list(dict.fromkeys(missing))
        resolution["player_text"] = _failure_text(resolution["missing"])
        return resolution
    method = str(proposal.get("method") or "")
    resolution["outcome"] = "ready"
    resolution["evidence"] = {
        "target_exists": _ref("object", target["instance_id"]),
        "accessible": _ref("access", target["instance_id"]),
        "rights": "possessor",
        "marking_exists": _ref("marking", str(mark.get("modification_id") or "")),
        "removable": _ref("method", method),
        "capability": "ordinary_removal_unblocked",
    }
    resolution["player_text"] = ""
    return resolution


def stage_grounded_removal(character: dict, resolution: Mapping[str, Any], operation_id: str) -> dict[str, Any]:
    """Stage one ID-specific removal. A repeated operation id replays the receipt."""
    if not str(operation_id or "").strip():
        return {"outcome": "rejected", "committed": False, "error": "not_ready"}
    request_id = _operation_request_id(operation_id, "remove_marking")
    receipt = _removal_receipt(character, request_id)
    proposal = resolution.get("proposal") or {}
    if receipt is not None:
        return _stage_replay(character, resolution, proposal, receipt, operation_id, request_id)
    if resolution.get("outcome") != "ready":
        return {"outcome": "rejected", "committed": False, "error": "not_ready"}
    prepared = prepare_removal(character, _removal_request(resolution, operation_id))
    return _from_prepare(prepared, resolution, None, replay_only=False)


def committed_removal_text(*, method: str, surface: str, content: str) -> str:
    """Deterministic sentence for a removal that has already committed."""
    verb = method if method in {"wipe", "rub", "erase", "clean", "remove", "wash"} else "remove"
    prep = "from" if verb in _FROM else "off"
    sentence = f"You {verb} the marking {prep} the {surface}. It is no longer there."
    if content:
        sentence += f" It read: {content}"
    return sentence


def technical_removal_text(error: str | None) -> str:
    if error == "conflicting_request":
        return "Nothing further was removed."
    if error == "stale_revision":
        return "The object changed before the marking could be removed. Nothing was removed."
    if error == "missing_marking":
        return "That marking is not there. Nothing was removed."
    return "The removal could not be confirmed. Nothing was removed."


def removal_commit_compatible(evidence: Mapping[str, Any], published: str, *, forbidden: list[str] | None = None) -> bool:
    """Accept a removal paraphrase only when it agrees with the committed facts."""
    text = str(published or "").strip()
    content = str(evidence.get("content") or "")
    surface = str(evidence.get("surface") or "")
    if not text or not content or content not in text or surface.casefold() not in text.casefold():
        return False
    if _DENIAL.search(text) or not _ABSENCE.search(text):
        return False
    if re.search(r"\b(?:request_id|modification_id|receipt)\b", text, re.IGNORECASE):
        return False
    if not evidence.get("consumption") and _CONSUMPTION.search(text):
        return False
    return not _leaks(text, [content], list(forbidden or []))


def removal_failure_compatible(published: str, *, forbidden: list[str] | None = None) -> bool:
    """A failed removal must still say that nothing was removed."""
    text = str(published or "").strip()
    folded = text.casefold()
    if "nothing was removed" not in folded and "nothing further was removed" not in folded:
        return False
    if "no longer" in folded or "it read:" in folded:
        return False
    return not _leaks(text, [], list(forbidden or []))


def _proposal(utterance, verb, marking, target, resource) -> dict[str, Any]:
    return {
        "utterance": utterance,
        "operation": "remove_marking",
        "method": verb,
        "target_phrase": target,
        "marking_phrase": marking,
        "resource_phrase": resource,
    }


def _has_marking_token(phrase: str) -> bool:
    return bool(set(re.findall(r"[a-z0-9']+", phrase.casefold())) & _MARKING_TOKENS)


def _blank(proposal, character, session) -> dict[str, Any]:
    return {
        "outcome": "unresolved",
        "proposal": dict(proposal),
        "missing": [],
        "player_text": "",
        "instance_id": "",
        "expected_revision": None,
        "modification_id": "",
        "surface_name": "",
        "surface_kind": "",
        "content": "",
        "method": str(proposal.get("method") or ""),
        "campaign_run_id": str(session.get("campaign_run_id") or ""),
        "character_id": str(character.get("id") or ""),
        "evidence": {},
    }


def _failure_text(missing: list[str]) -> str:
    sentences = [_MISSING[item] for item in missing if item in _MISSING]
    if not sentences:
        sentences = ["The removal could not be confirmed."]
    return "Nothing was removed. " + " ".join(sentences)


def _tokens(phrase: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9']+", phrase.casefold()) if token not in _STOP and len(token) > 1]


def _match_marks(phrase: str, marks: list[Mapping[str, Any]], character: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    tokens = _tokens(phrase)
    if not tokens:
        return []
    distinctive = [token for token in tokens if token not in _CLASS]
    if not distinctive:
        return list(marks)
    hits = []
    for mark in marks:
        content = set(re.findall(r"[a-z0-9']+", str(mark.get("content") or "").casefold()))
        medium = set(_medium_tokens(mark, character))
        if all(token in content or token in medium for token in distinctive):
            hits.append(mark)
    return hits


def _visible_marks(row: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    metadata = row.get("marking_visibility")
    classes = metadata.get("markings") if isinstance(metadata, dict) and metadata.get("version") == 1 else {}
    if not isinstance(classes, dict):
        classes = {}
    found = []
    for mark in row.get("markings") or []:
        if not isinstance(mark, dict) or mark.get("type") != "add_marking":
            continue
        visibility = classes.get(mark.get("modification_id"))
        if not isinstance(visibility, dict) or set(visibility) != {"classification"} or visibility.get("classification") != "visible":
            continue
        content = mark.get("content")
        if isinstance(content, str) and content.strip():
            found.append(mark)
    return found


def _medium_record(mark: Mapping[str, Any], character: Mapping[str, Any]):
    preconditions = (mark.get("authorization") or {}).get("preconditions") or {}
    ref = str(preconditions.get("medium_available") or "")
    if not ref.startswith("medium:"):
        return None
    item_id = ref.split(":", 1)[1]
    for row in character.get("inventory") or []:
        if isinstance(row, dict) and str(row.get("id") or "") == item_id and isinstance(row.get("marking_medium"), dict):
            return row, row["marking_medium"]
    return None


def _medium_tokens(mark: Mapping[str, Any], character: Mapping[str, Any]) -> list[str]:
    found = _medium_record(mark, character)
    if found is None:
        return []
    row, medium = found
    tokens = []
    for name in _names(medium, "name", "id") + _names(row, "name"):
        tokens.extend(re.findall(r"[a-z0-9']+", name))
    return tokens


def _affordance(medium: Mapping[str, Any], method: str):
    removal = medium.get("removal")
    methods = removal.get("methods") if isinstance(removal, dict) else None
    spec = methods.get(method) if isinstance(methods, dict) else None
    if not isinstance(spec, dict):
        return None
    resource = spec.get("resource", "none")
    if not isinstance(resource, str) or not resource.strip():
        return None
    surfaces = spec.get("surfaces")
    if surfaces is not None and not (
        isinstance(surfaces, list) and all(isinstance(item, str) and item.strip() for item in surfaces)
    ):
        return None
    return spec


def _feasibility(proposal, target, mark, character, missing: list[str]) -> None:
    method = str(proposal.get("method") or "")
    surface = target["surface"]
    found = _medium_record(mark, character)
    if found is None:
        missing.append("method")
        return
    _row, medium = found
    spec = _affordance(medium, method)
    if spec is None:
        missing.append("method")
        return
    surfaces = spec.get("surfaces")
    if isinstance(surfaces, list) and target.get("kind") not in surfaces:
        missing.append("method")
    allowed = surface.get("removal_methods")
    if isinstance(allowed, list) and method not in allowed:
        missing.append("method")
    if surface.get("removal_environment") == "blocked" or medium.get("removal_environment") == "blocked":
        missing.append("environment")
    if spec.get("mechanics") == "required" or surface.get("removal_mechanics") == "required" or medium.get("removal_mechanics") == "required":
        missing.append("mechanics")
    _resolve_resource(proposal, spec, character, missing)


def _resource_hits(phrase: str, character: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    hits = []
    for row in character.get("inventory") or []:
        if isinstance(row, dict) and _phrase_matches(phrase, _names(row, "name", "id")):
            hits.append(row)
    return hits


def _usable(row: Mapping[str, Any]) -> bool:
    return row.get("usable") is True and isinstance(row.get("quantity"), int) and row["quantity"] >= 1


def _resolve_resource(proposal, spec, character, missing: list[str]) -> None:
    required = str(spec.get("resource") or "none")
    named = str(proposal.get("resource_phrase") or "")
    if required == "none":
        if not named:
            return
        phrase = named
    else:
        if named and not _phrase_matches(named, [_norm(required)]):
            missing.append("resource")
            return
        phrase = named or required
    raw_hits = _resource_hits(phrase, character)
    usable = [row for row in raw_hits if _usable(row)]
    if len(raw_hits) > 1:
        missing.append("ambiguous_resource")
    elif len(usable) != 1:
        missing.append("resource")
    elif spec.get("consumption") == "required":
        missing.append("consumption")


def _removal_blocked(character: Mapping[str, Any]) -> bool:
    status = character.get("physical_status")
    if isinstance(status, dict) and status.get("ordinary_removal") == "unable":
        return True
    conditions = character.get("conditions")
    if isinstance(conditions, list):
        for condition in conditions:
            if isinstance(condition, dict) and condition.get("blocks_ordinary_removal") is True:
                return True
    return False


def _resolve_target(phrase: str, character: Mapping[str, Any], session: Mapping[str, Any]):
    if not phrase or _norm(phrase) in _PRONOUNS:
        return {"error": "reference" if _norm(phrase) in _PRONOUNS else "target"}
    inventory = character.get("inventory")
    if not isinstance(inventory, list):
        return {"error": "target"}
    hits = []
    for index, row in enumerate(inventory):
        if not isinstance(row, dict):
            continue
        surfaces = _surfaces(row)
        surface_hits = []
        for surface in surfaces:
            names = _names(surface, "name", "id")
            kind = surface.get("kind")
            if isinstance(kind, str) and kind.strip():
                names.append(_norm(kind))
            if _phrase_matches(phrase, names):
                surface_hits.append(surface)
        if len(surface_hits) > 1:
            return {"error": "ambiguous"}
        object_match = _phrase_matches(phrase, _names(row, "name", "id"))
        if surface_hits:
            hits.append((index, row, surface_hits[0]))
        elif object_match:
            accessible = [surface for surface in surfaces if surface.get("accessible") is True]
            if len(accessible) > 1:
                hits.append((index, row, None))
            else:
                hits.append((index, row, accessible[0] if accessible else None))
    if len(hits) > 1:
        return {"error": "ambiguous"}
    if len(hits) != 1:
        return {"error": "target"}
    index, row, surface = hits[0]
    if surface is None:
        return {"error": "ambiguous"}
    if surface.get("accessible") is not True:
        return {"error": "surface"}
    if row.get("usable") is not True or row.get("quantity") != 1:
        return {"error": "access"}
    identity = inspect_object_identity(character, index, campaign_run_id=str(session.get("campaign_run_id") or ""))
    if identity.status != "existing" or not isinstance(row.get("revision"), int) or not row.get("instance_id"):
        return {"error": "identity"}
    return {
        "instance_id": row.get("instance_id"),
        "revision": row.get("revision"),
        "surface_name": str(surface.get("name") or surface.get("id") or "surface"),
        "kind": str(surface.get("kind") or ""),
        "surface": surface,
        "row": row,
    }


def _removal_request(resolution: Mapping[str, Any], operation_id: str) -> dict[str, Any]:
    request = {
        "version": 1,
        "operation": "remove_marking",
        "campaign_run_id": resolution["campaign_run_id"],
        "character_id": resolution["character_id"],
        "instance_id": resolution["instance_id"],
        "modification_id": resolution["modification_id"],
        "request_id": _operation_request_id(operation_id, "remove_marking"),
        "expected_revision": resolution["expected_revision"],
        "authorization": {
            "caller_id": "grounded_marking_removal",
            "decision_id": _operation_request_id(operation_id, "removal_decision"),
            "mechanics": "not_applicable",
            "preconditions": {key: resolution["evidence"][key] for key in REMOVAL_PRECONDITIONS},
        },
    }
    request["request_digest"] = request_digest(request)
    return request


def _removal_receipt(character: Mapping[str, Any], request_id: str):
    entries = (character.get(LEDGER) or {}).get("entries") if isinstance(character.get(LEDGER), dict) else None
    receipt = entries.get(request_id) if isinstance(entries, dict) else None
    if isinstance(receipt, dict) and receipt.get("operation") == "remove_marking":
        return receipt
    return None


def _same_method(receipt: Mapping[str, Any], method: str) -> bool:
    preconditions = ((receipt.get("request") or {}).get("authorization") or {}).get("preconditions") or {}
    return preconditions.get("removable") == _ref("method", method)


def _stage_replay(character, resolution, proposal, receipt, operation_id, request_id) -> dict[str, Any]:
    original = receipt.get("request") if isinstance(receipt.get("request"), dict) else None
    removed = receipt.get("removed_marking") if isinstance(receipt.get("removed_marking"), dict) else None
    if original is None or removed is None:
        return {"outcome": "technical_failure", "committed": False, "error": "missing_marking"}
    method = str(proposal.get("method") or "")
    same_object = bool(resolution.get("instance_id")) and resolution.get("instance_id") == original.get("instance_id")
    same_method = _same_method(receipt, method)
    same_mark = same_object and len(_match_marks(str(proposal.get("marking_phrase") or ""), [removed], character)) == 1
    ready_same = (
        resolution.get("outcome") == "ready"
        and resolution.get("modification_id") == original.get("modification_id")
        and same_object
        and same_method
    )
    if ready_same or (resolution.get("outcome") != "ready" and same_mark and same_method):
        prepared = prepare_removal(character, original)
        return _from_prepare(prepared, resolution, receipt, replay_only=True)
    if resolution.get("outcome") == "ready":
        prepared = prepare_removal(character, _removal_request(resolution, operation_id))
        staged = _from_prepare(prepared, resolution, receipt, replay_only=False)
        if staged.get("outcome") == "staged":
            return {"outcome": "technical_failure", "committed": False, "error": "conflicting_request", "request_id": request_id}
        return staged
    if resolution.get("instance_id"):
        return {"outcome": "technical_failure", "committed": False, "error": "conflicting_request", "request_id": request_id}
    return {"outcome": "rejected", "committed": False, "error": "not_ready"}


def _from_prepare(prepared, resolution, receipt, *, replay_only: bool) -> dict[str, Any]:
    method = str((resolution.get("proposal") or {}).get("method") or resolution.get("method") or "")
    surface = str(resolution.get("surface_name") or "")
    if prepared.get("status") == "rejected":
        return {"outcome": "technical_failure", "committed": False, "error": prepared.get("error")}
    if prepared.get("status") == "replay":
        removed = (receipt or {}).get("removed_marking") if isinstance(receipt, dict) else {}
        content = str((removed or {}).get("content") or resolution.get("content") or "")
        instance_id = str(resolution.get("instance_id") or ((receipt or {}).get("request") or {}).get("instance_id") or "")
        return {
            "outcome": "replay",
            "committed": True,
            "character": None,
            "content": content,
            "surface_name": surface,
            "method": method,
            "instance_id": instance_id,
            "error": None,
        }
    if replay_only or prepared.get("status") != "validated":
        return {"outcome": "technical_failure", "committed": False, "error": prepared.get("error") or "not_replayed"}
    return {
        "outcome": "staged",
        "committed": False,
        "character": prepared["character"],
        "content": str(resolution.get("content") or ""),
        "surface_name": surface,
        "method": method,
        "instance_id": str(resolution.get("instance_id") or ""),
        "error": None,
    }


def _leaks(text: str, permitted: list[str], forbidden: list[str]) -> bool:
    allowed = [item for item in permitted if item]
    for item in forbidden:
        if not item or item in allowed or any(item in permitted_item for permitted_item in allowed):
            continue
        if item in text:
            return True
    return False
