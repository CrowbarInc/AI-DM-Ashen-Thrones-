"""Player-facing read of current object markings.

Recognition and resolution are pure. Disclosure goes through the existing
observation service. Player wording never grants visibility, and this module
does not write character state.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Mapping

from game.immutable_valid_response import seal_accepted_response, seal_delivery_contract, semantic_equal
from game.marking_action import _names, _norm, _phrase, _phrase_matches, _surfaces
from game.object_instances import inspect_object_identity
from game import object_observation

_PROPERTY = r"(?:(?:hidden|secret|concealed)\s+)?(?:writing|markings|marks|inscription|note|words|warning)"
_EXAMINE = re.compile(
    rf"^\s*(?:(?:i|we)\s+)?(?:examine|inspect|study|read|check)\s+(?:the\s+)?{_PROPERTY}\s+"
    rf"(?:on|upon)\s+(?P<target>.+?)\s*\.?\s*$",
    re.IGNORECASE,
)
_LOOK = re.compile(
    rf"^\s*(?:(?:i|we)\s+)?look\s+(?:at|over)\s+(?:the\s+)?{_PROPERTY}\s+"
    rf"(?:on|upon)\s+(?P<target>.+?)\s*\.?\s*$",
    re.IGNORECASE,
)
_WHAT = re.compile(
    rf"^\s*what\s+does\s+(?:the\s+)?(?:(?P<kind>{_PROPERTY})\s+on\s+)?"
    rf"(?P<target>.+?)\s+say\s*\??\s*$",
    re.IGNORECASE,
)
_STILL = re.compile(
    rf"^\s*(?:is|are)\s+the\s+{_PROPERTY}\s+still\s+(?:written|visible|there)"
    rf"(?:\s+on\s+(?P<target>.+?)|\s+(?P<pronoun>there|here))?\s*\??\s*$",
    re.IGNORECASE,
)
_CHECK = re.compile(
    rf"^\s*(?:(?:i|we)\s+)?check\s+whether\s+the\s+{_PROPERTY}\s+(?:is\s+)?still\s+"
    rf"(?:there|written|visible)(?:\s+on\s+(?P<target>.+?))?\s*\.?\s*$",
    re.IGNORECASE,
)
_SEE = re.compile(
    rf"^\s*(?:(?:i|we)\s+)?(?:can\s+)?(?:clearly\s+)?see\s+(?:the\s+)?{_PROPERTY}\s+"
    rf"(?:on|upon)\s+(?P<target>.+?)\s*\.?\s*$",
    re.IGNORECASE,
)
_NOT_OBSERVATION = re.compile(
    r"\b(?:remember|recall|erase|scratch|engrave|carve|etch|tell|ask|order|write|copy|jot|scribble|inscribe)\b",
    re.IGNORECASE,
)
_PRONOUNS = frozenset({"there", "here", "it", "that", "them", "this"})
_DENIAL = re.compile(
    r"\b(?:nothing was written|nothing further was written|could not be confirmed|"
    r"not carried out|was not written)\b",
    re.IGNORECASE,
)
_CONSUMPTION = re.compile(r"\b(?:used up|consumed|ran out)\b", re.IGNORECASE)
_PRESENCE = re.compile(r"\b(?:on it now|it reads:|reads:)\b", re.IGNORECASE)
_HIDDEN_WORD = re.compile(r"\b(?:concealed|hidden|secret|restricted)\b", re.IGNORECASE)
_VISIBLE_ABSENCE = re.compile(r"no (?:writing is visible|visible writing)", re.IGNORECASE)
_CLAIM_REASONS = frozenset({None, "unsupported_physical_manipulation", "recent_visible_context_answer"})


def recognize_observation(text: str | None) -> dict[str, Any] | None:
    """Return a structured look-at-markings proposal, or None for other speech."""
    raw = " ".join(str(text or "").split())
    if not raw or _NOT_OBSERVATION.search(raw):
        return None
    for pattern in (_EXAMINE, _LOOK, _WHAT, _STILL, _CHECK, _SEE):
        match = pattern.search(raw)
        if match is None:
            continue
        target = match.groupdict().get("target") or ""
        pronoun = match.groupdict().get("pronoun") or ""
        phrase = _phrase(pronoun or target)
        return {
            "utterance": raw,
            "target_phrase": phrase,
            "pronoun": _norm(phrase) in _PRONOUNS or not phrase,
        }
    return None


def claim_observation(reason: str | None, proposal: Mapping[str, Any] | None) -> bool:
    """True when this turn should leave the existing path for a marking read."""
    return proposal is not None and reason in _CLAIM_REASONS


def resolve_observation(proposal: Mapping[str, Any], character: Mapping[str, Any],
                        session: Mapping[str, Any], scene: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Bind one carried surface. Missing or contested targets stay unresolved."""
    if proposal.get("pronoun"):
        return _outcome("reference", "Say which object you mean.")
    phrase = str(proposal.get("target_phrase") or "")
    if _scene_named(phrase, str(proposal.get("utterance") or ""), scene):
        hits = _hits(phrase, character)
        if not isinstance(hits, list) or len(hits) != 1:
            return _outcome("defer", "")
        return _outcome("ambiguous", "More than one established object matches. Name the one you mean.")
    found = _hits(phrase, character)
    if found == "ambiguous":
        return _outcome("ambiguous", "More than one established object matches. Name the one you mean.")
    if not isinstance(found, list) or len(found) != 1:
        return _outcome("missing", "No established object matches what you tried to examine.")
    index, row, surface = found[0]
    if surface is None:
        return _outcome("missing", "That object has no established surface you can examine.")
    if surface.get("accessible") is not True or row.get("usable") is not True or row.get("quantity") != 1:
        return _outcome("inaccessible", "You cannot see that surface from here.")
    if _observation_blocked(character):
        return _outcome("blocked", "You are not established as able to examine that.")
    if surface.get("observation_mechanics") == "required":
        return _outcome("mechanics", "That examination needs a rules decision before it can be answered.")
    identity = inspect_object_identity(character, index, campaign_run_id=str(session.get("campaign_run_id") or ""))
    if identity.status != "existing":
        return _outcome("technical", "The writing could not be read.")
    return {
        "outcome": "ready",
        "player_text": "",
        "instance_id": row.get("instance_id"),
        "surface_name": str(surface.get("name") or surface.get("id") or "surface"),
        "revision": row.get("revision"),
    }


def project_observation(character: Mapping[str, Any], session: Mapping[str, Any],
                        resolved: Mapping[str, Any]) -> dict[str, Any]:
    """Project current visible markings. Concealed state is not copied out."""
    surface = str(resolved.get("surface_name") or "surface")
    request = {
        "version": 1,
        "campaign_run_id": str(session.get("campaign_run_id") or ""),
        "character_id": str(character.get("id") or ""),
        "instance_id": resolved.get("instance_id"),
        "observer_id": str(character.get("id") or ""),
        "scope": "carried",
        "categories": ["markings"],
    }
    try:
        grant = object_observation._establish_observation_authorization(
            character, request,
            decision_ref="ordinary-carried-surface",
            visibility_ref="current-marking-visibility",
            access_ref="inventory-accessible-surface",
            concealed=False, restricted_scopes=(), complete=False,
        )
        projection = object_observation.observe_object(character, request, authorization=grant)
    except (TypeError, ValueError, KeyError, AttributeError):
        projection = None
    if not isinstance(projection, dict) or projection.get("status") != "observed":
        text = "The writing could not be read."
        projection = {"version": 1, "status": "unresolved", "target": None, "properties": [], "limitations": ["observation_unavailable"], "evidence": []}
    else:
        text = narration_from_projection(surface, projection)
    return {
        "player_text": text,
        "projection": projection,
        "surface_name": surface,
        "instance_id": str(resolved.get("instance_id") or ""),
    }


def narration_from_projection(surface: str, projection: Mapping[str, Any]) -> str:
    """Sentences from the disclosure DTO only."""
    props = projection.get("properties") if isinstance(projection, Mapping) else None
    prop = props[0] if isinstance(props, list) and props and isinstance(props[0], Mapping) else None
    if not isinstance(prop, Mapping) or prop.get("category") != "markings":
        return "The writing could not be read."
    values = prop.get("values") if isinstance(prop.get("values"), list) else []
    contents = [str(item.get("content")) for item in values if isinstance(item, Mapping) and isinstance(item.get("content"), str) and item.get("content")]
    knowledge = prop.get("knowledge")
    if knowledge == "known_present" and contents:
        first = f"On the {surface}, the visible writing reads: {contents[0]}"
        rest = " ".join(f"Also visible: {item}" for item in contents[1:])
        return f"{first} {rest}".strip()
    if knowledge == "known_absent":
        return f"On the {surface}, no marking is present."
    return f"You look at the {surface}. No writing is visible there."


def observation_compatible(surface: str, projection: Mapping[str, Any], published: str, *, forbidden: list[str]) -> bool:
    """Accept a paraphrase only when it preserves the permitted projection."""
    text = str(published or "").strip()
    if not text or surface.casefold() not in text.casefold():
        return False
    if re.search(r"\b(?:request_id|modification_id|receipt)\b", text, re.IGNORECASE):
        return False
    prop = _marking_property(projection)
    if prop is None:
        return False
    contents = _contents(prop)
    knowledge = prop.get("knowledge")
    if knowledge == "known_present":
        if re.search(r"no writing is visible|no marking is present", text, re.IGNORECASE):
            return False
        if not contents or any(content not in text for content in contents):
            return False
    elif knowledge == "known_absent":
        if "no marking is present" not in text.casefold() or contents:
            return False
    else:
        if not _VISIBLE_ABSENCE.search(text) or _HIDDEN_WORD.search(text):
            return False
        if re.search(r"no marking is present", text, re.IGNORECASE):
            return False
    return not _leaks(text, contents, forbidden)


def marking_commit_compatible(evidence: Mapping[str, Any], published: str, *, forbidden: list[str] | None = None) -> bool:
    """Accept a marking paraphrase only when it agrees with the committed facts."""
    text = str(published or "").strip()
    content = str(evidence.get("content") or "")
    surface = str(evidence.get("surface") or "")
    medium = str(evidence.get("medium") or "")
    if not text or not content or content not in text:
        return False
    if _DENIAL.search(text) or surface.casefold() not in text.casefold() or medium.casefold() not in text.casefold():
        return False
    if evidence.get("visibility") == "concealed":
        if re.search(r"\bon it now\b", text, re.IGNORECASE) or not re.search(r"\bconcealed\b", text, re.IGNORECASE):
            return False
    else:
        if re.search(r"\b(?:concealed|hidden)\b", text, re.IGNORECASE) or not _PRESENCE.search(text):
            return False
    if not evidence.get("consumption") and _CONSUMPTION.search(text):
        return False
    return not _leaks(text, [content], list(forbidden or []))


def undisclosed_marking_contents(character: Mapping[str, Any], instance_id: str, permitted: list[str]) -> list[str]:
    """Contents present on the object and absent from the permitted projection."""
    allowed = {item for item in permitted if isinstance(item, str) and item}
    found = []
    for row in character.get("inventory") or []:
        if not isinstance(row, dict) or row.get("instance_id") != instance_id:
            continue
        for mark in row.get("markings") or []:
            if not isinstance(mark, dict):
                continue
            content = mark.get("content")
            if isinstance(content, str) and content and content not in allowed and content not in found:
                found.append(content)
    return found


def reconcile_publication(*, proposed: str, sealed: str | None, compatible: Callable[[str], bool]) -> dict[str, str]:
    """Keep a sealed paraphrase only when it agrees with the committed evidence."""
    if sealed is None:
        return {"text": proposed, "disposition": "sealer_exception"}
    if not str(sealed).strip():
        return {"text": proposed, "disposition": "empty"}
    if semantic_equal(sealed, proposed):
        return {"text": str(sealed), "disposition": "unchanged"}
    try:
        agreed = bool(compatible(str(sealed)))
    except Exception:
        agreed = False
    if agreed:
        return {"text": str(sealed), "disposition": "paraphrase"}
    return {"text": proposed, "disposition": "rejected_fallback"}


def install_published_line(gm: dict, *, text: str, resolution: Mapping[str, Any] | None,
                           player_text: str, source: str) -> None:
    """Seal the reconciled sentence so a rejected draft cannot be restored."""
    seal_accepted_response(
        gm, text=text, provenance="authorized_host_speech", attempt=0,
        validation={
            "hard_valid": True, "reasons": [], "soft_flags": [],
            "speaker": "GM", "addressee": "player", "operation": "ask",
            "interaction_complete": True, "contract_satisfying": True, "authority": [source],
        },
        contract={"contract_id": "", "operation": "ask"},
        player_text=player_text, resolution=resolution,
    )
    seal_delivery_contract(gm)


def _outcome(name: str, text: str) -> dict[str, Any]:
    return {"outcome": name, "player_text": text, "instance_id": "", "surface_name": "", "revision": None}


def _scene_named(phrase: str, utterance: str, scene: Mapping[str, Any] | None) -> bool:
    from game.conversational_continuity import established_scene_object_ids

    return bool(established_scene_object_ids(phrase, scene) or established_scene_object_ids(utterance, scene))


def _observation_blocked(character: Mapping[str, Any]) -> bool:
    status = character.get("physical_status")
    if isinstance(status, dict) and status.get("ordinary_observation") == "unable":
        return True
    conditions = character.get("conditions")
    if isinstance(conditions, list):
        for condition in conditions:
            if isinstance(condition, dict) and condition.get("blocks_ordinary_observation") is True:
                return True
    return False


def _hits(phrase: str, character: Mapping[str, Any]):
    inventory = character.get("inventory")
    if not isinstance(inventory, list):
        return []
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
            return "ambiguous"
        object_match = _phrase_matches(phrase, _names(row, "name", "id"))
        if surface_hits:
            hits.append((index, row, surface_hits[0]))
        elif object_match:
            accessible = [surface for surface in surfaces if surface.get("accessible") is True]
            if len(accessible) > 1:
                return "ambiguous"
            hits.append((index, row, accessible[0] if accessible else None))
    if len(hits) > 1:
        return "ambiguous"
    return hits


def _marking_property(projection: Mapping[str, Any]):
    props = projection.get("properties") if isinstance(projection, Mapping) else None
    if not isinstance(props, list) or not props or not isinstance(props[0], Mapping):
        return None
    prop = props[0]
    return prop if prop.get("category") == "markings" else None


def _contents(prop: Mapping[str, Any]) -> list[str]:
    values = prop.get("values") if isinstance(prop.get("values"), list) else []
    return [str(item.get("content")) for item in values if isinstance(item, Mapping) and isinstance(item.get("content"), str)]


def _leaks(text: str, permitted: list[str], forbidden: list[str]) -> bool:
    allowed = [item for item in permitted if item]
    for item in forbidden:
        if not item or item in allowed or any(item in permitted_item for permitted_item in allowed):
            continue
        if item in text:
            return True
    return False
