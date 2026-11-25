"""Ground carried objects for live interpretation and sheet answers.

The model may name an id or leave the target empty. This module does not
invent objects, spellbook pages, or casts. Possession comes from the
authoritative inventory row. A unique match can be bound by the host when
the model supplies no target. A fabricated id is rejected and not replaced.
"""

from __future__ import annotations

import math
import re
from typing import Any, Mapping

from game.player_http_projection import CHARACTER, project
from game.player_interpretation_bridge import visible_catalog
from game.referenced_surface import content_tokens, reference_compatible

_FILLER = {
    "actually",
    "been",
    "carry",
    "carried",
    "carrying",
    "inside",
    "inscribed",
    "i've",
    "mean",
    "one",
    "pack",
    "page",
    "pages",
    "recorded",
    "same",
    "that",
    "through",
    "written",
}
_GENERIC_BOOK = {"book", "volume", "tome"}
_BOOK_CLASS = _GENERIC_BOOK | {"grimoire", "spellbook", "codex"}

_PREPARED_RE = re.compile(
    r"\b(?:what|which)\s+spells?\b.*\b(?:ready|prepared)\b"
    r"|\bremind\s+me\s+what\s+spells?\s+i\s+have\s+prepared\b",
    re.IGNORECASE,
)
_RECORDED_RE = re.compile(
    r"\b(?:what\s+spells?\s+(?:are\s+)?|spells?\s+)(?:written|recorded|inscribed)\s+(?:in|inside)\s+(?P<subject>.+)$",
    re.IGNORECASE,
)
_CONTENTS_RE = re.compile(
    r"\bwhat\s+can\s+i\s+find\s+in\s+(?P<subject>.+)$",
    re.IGNORECASE,
)
_LEAF_RE = re.compile(
    r"^(?:i|we)\s+(?:carefully\s+|slowly\s+)?(?:leaf|flip|page|thumb)\s+through\s+(?P<subject>.+)$",
    re.IGNORECASE,
)
_USE_RE = re.compile(
    r"^(?:i|we)\s+(?:use|burn|tear|throw|wield|destroy)\s+(?P<subject>.+)$",
    re.IGNORECASE,
)
_READ_RE = re.compile(
    r"^(?:i|we)\s+(?:read|open)\s+(?P<subject>.+)$",
    re.IGNORECASE,
)
_CLARIFY_RE = re.compile(
    r"^(?:the one i mean is|i mean)\s+(?P<subject>.+)$",
    re.IGNORECASE,
)
_EXAMINE_RE = re.compile(
    r"^(?:(?:i|we)\s+)?(?:examine|inspect|look at)\s+(?P<subject>.+)$",
    re.IGNORECASE,
)
_BARE_RE = re.compile(
    r"^(?:my\s+(?:book|spellbook|volume|tome|grimoire)|the\s+(?:volume|book|spellbook|tome|grimoire)\b.*)$",
    re.IGNORECASE,
)
_FROM_RE = re.compile(
    r"^(?:from|in)\s+(?P<subject>.+?),\s+what\s+spells\b",
    re.IGNORECASE,
)
_CONDITIONAL_RE = re.compile(
    r"^\s*(?:if|unless)\b.+\b(?:i|we)\s+(?:(?:leaf|flip|page|thumb)\s+through|read|open|use|burn|tear|throw|wield|examine|inspect|look at)\b",
    re.IGNORECASE,
)
_NEGATED_RE = re.compile(
    r"^\s*(?:i|we)\s+(?:do not|don't|will not|won't|never)\s+(?:(?:leaf|flip|page|thumb)\s+through|read|open|use|burn|tear|throw|wield|examine|inspect|look at)\b",
    re.IGNORECASE,
)
_POSSESSION_RE = re.compile(
    r"\b(?:my|mine|in my pack|been carrying|i am carrying|i'm carrying|i have been carrying)\b",
    re.IGNORECASE,
)
_SCENE_PLACE_RE = re.compile(
    r"\b(?:beside|near|outside|on the|notice board|at the gate)\b",
    re.IGNORECASE,
)
_DEICTIC_RE = re.compile(r"\b(?:it|that|this|same|one)\b", re.IGNORECASE)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip()).rstrip(".?!").strip()


def _subject(value: str) -> str:
    text = _clean(value)
    return re.split(r"\s+to\s+", text, maxsplit=1)[0].strip()


def _scene_id(scene: Mapping[str, Any] | None) -> str:
    inner = scene.get("scene") if isinstance(scene, Mapping) and isinstance(scene.get("scene"), dict) else scene
    if not isinstance(inner, Mapping):
        return ""
    return str(inner.get("id") or "")


def _scene_body(scene: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(scene, Mapping):
        return {}
    inner = scene.get("scene")
    return inner if isinstance(inner, dict) else scene


def _quantity_ok(value: Any, *, present: bool) -> bool:
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        return False
    return value > 0 if present else True


def _labels(row: Mapping[str, Any]) -> list[str]:
    found = [str(row.get("name") or ""), str(row.get("id") or "").replace("_", " "), str(row.get("label") or "")]
    aliases = row.get("aliases")
    if isinstance(aliases, list):
        found.extend(str(alias) for alias in aliases if isinstance(alias, str))
    return [item.strip() for item in found if item.strip()]


def _book_class(row: Mapping[str, Any]) -> bool:
    tokens: list[str] = []
    for label in _labels(row):
        tokens.extend(content_tokens(label))
    return any(token in _BOOK_CLASS or (len(token) > 4 and token.endswith("book")) for token in tokens)


def _generic_book_phrase(phrase: str) -> bool:
    tokens = [token for token in content_tokens(phrase) if token not in _FILLER]
    return bool(tokens) and all(token in _GENERIC_BOOK for token in tokens)


def _deictic(phrase: str) -> bool:
    if not _DEICTIC_RE.search(phrase or ""):
        return False
    tokens = [token for token in content_tokens(phrase) if token not in _FILLER]
    return not tokens or set(tokens) <= _GENERIC_BOOK


def _possessive(text: str, phrase: str) -> bool:
    return bool(_POSSESSION_RE.search(text or "") or _POSSESSION_RE.search(phrase or ""))


def inventory_rows(character: Mapping[str, Any] | None, *, present_only: bool = True) -> list[dict[str, Any]]:
    """Public inventory identities. Hidden, inaccessible, and stored rows stay out."""
    if not isinstance(character, Mapping):
        return []
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(character.get("inventory") or []):
        if not isinstance(raw, Mapping):
            continue
        if raw.get("hidden") is True or raw.get("accessible") is False:
            continue
        equipped = bool(raw.get("equipped") is True or raw.get("worn") is True)
        if raw.get("stored") is True and not equipped and raw.get("carried") is not True:
            continue
        if not _quantity_ok(raw.get("quantity"), present=present_only):
            continue
        public = project({"inventory": [raw]}, CHARACTER).get("inventory") or []
        if not public or not public[0].get("id") or not public[0].get("name"):
            continue
        aliases = [alias.strip() for alias in raw.get("aliases") or [] if isinstance(alias, str) and alias.strip()]
        rows.append({
            "index": index,
            "id": str(public[0]["id"]),
            "instance_id": raw.get("instance_id") if isinstance(raw.get("instance_id"), str) else None,
            "name": str(public[0]["name"]),
            "label": str(public[0]["name"]),
            "aliases": aliases,
            "quantity": raw.get("quantity"),
            "equipped": equipped,
            "scope": "equipped" if equipped else "carried",
            "owner": str(character.get("id") or ""),
        })
    return rows


def interpretation_catalog(
    scene: dict | None,
    world: dict | None,
    character: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Scene catalog plus this character's carried and equipped objects.

    Scene ids are kept. A carried id that already names a scene entity is not
    entered a second time. Rows are deterministic by id. Spell lists, notes,
    and other unpublished fields are not copied into the catalog.
    """
    catalog = dict(visible_catalog(scene, world))
    for row in inventory_rows(character):
        if row["id"] in catalog:
            continue
        catalog[row["id"]] = {
            "kind": "equipped_object" if row["equipped"] else "carried_object",
            "row": {
                "id": row["id"],
                "name": row["name"],
                "label": row["name"],
                "aliases": list(row["aliases"]),
                "scope": row["scope"],
                "owner": row["owner"],
            },
        }
    return {key: catalog[key] for key in sorted(catalog)}


def _scene_objects(scene: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    body = _scene_body(scene)
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in body.get("interactables") or []:
        if not isinstance(item, Mapping) or item.get("hidden") is True or item.get("visible") is False:
            continue
        if item.get("accessible") is False:
            continue
        entity_id = str(item.get("id") or "").strip()
        if not entity_id or entity_id in seen:
            continue
        seen.add(entity_id)
        aliases = [alias for alias in item.get("aliases") or [] if isinstance(alias, str)]
        found.append({
            "id": entity_id,
            "name": str(item.get("name") or item.get("label") or entity_id.replace("_", " ")),
            "label": str(item.get("label") or item.get("name") or entity_id.replace("_", " ")),
            "aliases": aliases,
            "scope": "scene",
        })
    return found


def _match_phrases(phrase: str) -> list[str]:
    raw = _clean(phrase)
    reduced = " ".join(token for token in content_tokens(raw) if token not in _FILLER)
    phrases = [raw] if raw else []
    if reduced and reduced not in phrases:
        phrases.append(reduced)
    return phrases


def _compatible(phrase: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    phrases = _match_phrases(phrase)
    hits = []
    for row in rows:
        labels = [label for label in _labels(row) if label]
        if any(reference_compatible(candidate, label) for candidate in phrases for label in labels):
            hits.append(row)
    return hits


def recent_carried_reference(log, scene, character) -> dict[str, Any]:
    latest = log[-1] if isinstance(log, list) and log else {}
    prior = ((latest.get("resolution") or {}).get("metadata") or {}).get("conversational_decision") or {}
    auth = prior.get("authorization") or {}
    if (
        prior.get("intent_family") in {"inventory_information", "inventory_inspection", "spell_information"}
        and auth.get("information_disposition") in {"ANSWERABLE", "ABSENT"}
        and auth.get("scene_id") == _scene_id(scene)
        and auth.get("character_id") == str((character or {}).get("id") or "")
        and auth.get("subject_id")
    ):
        return auth
    return {}


def resolve_object_reference(
    text: str,
    subject: str,
    *,
    character,
    scene,
    log=None,
) -> dict[str, Any]:
    """Resolve one object phrase. Multiple matches stay unresolved as ambiguous."""
    phrase = _clean(subject or text)
    carried = inventory_rows(character)
    visible = _scene_objects(scene)
    prior = recent_carried_reference(log, scene, character)
    if _deictic(phrase) and prior.get("subject_id"):
        held = [
            row for row in carried
            if row["id"] == prior.get("subject_id")
            and (not prior.get("subject_instance_id") or row.get("instance_id") == prior.get("subject_instance_id"))
        ]
        if len(held) == 1:
            return {"status": "resolved", "row": held[0], "carried": held, "scene": [], "binding_layer": "host_reference_resolution"}
        if len(held) > 1:
            return {"status": "ambiguous", "row": None, "carried": held, "scene": [], "binding_layer": "host_reference_resolution"}
    if _deictic(phrase) and not [token for token in content_tokens(phrase) if token not in _FILLER]:
        return {"status": "unresolved", "row": None, "carried": [], "scene": [], "binding_layer": "host_reference_resolution"}
    carried_hits = _compatible(phrase, carried)
    scene_hits = _compatible(phrase, visible)
    if not carried_hits and not scene_hits and _generic_book_phrase(phrase):
        carried_hits = [row for row in carried if _book_class(row)]
        scene_hits = [row for row in visible if _book_class(row)]
    if _possessive(text, phrase):
        scene_hits = []
    elif _SCENE_PLACE_RE.search(phrase) and not scene_hits:
        carried_hits = []
    if carried_hits and scene_hits:
        return {"status": "ambiguous", "row": None, "carried": carried_hits, "scene": scene_hits, "binding_layer": "host_reference_resolution"}
    if len(carried_hits) > 1:
        return {"status": "ambiguous", "row": None, "carried": carried_hits, "scene": [], "binding_layer": "host_reference_resolution"}
    if len(carried_hits) == 1:
        return {"status": "resolved", "row": carried_hits[0], "carried": carried_hits, "scene": [], "binding_layer": "host_reference_resolution"}
    if scene_hits:
        return {"status": "scene", "row": scene_hits[0] if len(scene_hits) == 1 else None, "carried": [], "scene": scene_hits, "binding_layer": "host_reference_resolution"}
    return {"status": "unresolved", "row": None, "carried": [], "scene": [], "binding_layer": "host_reference_resolution"}


def classify_carried_request(text: str, *, include_examine: bool = False) -> dict[str, str] | None:
    """Return the sheet act, or None when another owner should keep the turn."""
    raw = _clean(text)
    if not raw:
        return None
    if _CONDITIONAL_RE.search(raw):
        return {"act": "conditional", "subject": raw}
    if _NEGATED_RE.search(raw):
        return {"act": "negated", "subject": raw}
    if _PREPARED_RE.search(raw):
        found = _FROM_RE.search(raw)
        return {"act": "prepared_spells", "subject": _subject(found.group("subject")) if found else ""}
    for pattern, act in (
        (_RECORDED_RE, "recorded_spells"),
        (_CONTENTS_RE, "contents"),
        (_LEAF_RE, "read"),
        (_USE_RE, "unsupported_use"),
        (_READ_RE, "read"),
        (_CLARIFY_RE, "identity"),
    ):
        match = pattern.search(raw)
        if match:
            return {"act": act, "subject": _subject(match.group("subject"))}
    if include_examine:
        match = _EXAMINE_RE.search(raw)
        if match:
            return {"act": "read", "subject": _subject(match.group("subject"))}
    if _BARE_RE.search(raw):
        return {"act": "identity", "subject": _subject(raw)}
    return None


def _choice_labels(resolution: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    for row in list(resolution.get("carried") or []) + list(resolution.get("scene") or []):
        label = str(row.get("name") or row.get("label") or "").strip()
        if label and label not in labels:
            labels.append(label)
    return labels


def prepared_spell_rows(character: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Names the player sheet already publishes. No spellbook page is inferred."""
    spells = character.get("spells") if isinstance(character, Mapping) else None
    prepared = spells.get("prepared") if isinstance(spells, Mapping) else None
    if not isinstance(prepared, list):
        return []
    rows = []
    for raw in prepared:
        if not isinstance(raw, Mapping):
            continue
        name = raw.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        cast = raw.get("cast") if isinstance(raw.get("cast"), bool) else None
        rows.append({
            "id": raw.get("id") if isinstance(raw.get("id"), str) else "",
            "name": name.strip(),
            "cast": cast,
        })
    return rows


def _join(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + ", and " + names[-1]


def _which(labels: list[str]) -> str:
    if not labels:
        return "Which object do you mean? Specify the inventory item or the object in the scene."
    if len(labels) == 1:
        shown = labels[0]
    elif len(labels) == 2:
        shown = f"{labels[0]}, or {labels[1]}"
    else:
        shown = ", ".join(labels[:-1]) + ", or " + labels[-1]
    return f"Which object do you mean? {shown}."


def _decision(**kwargs):
    from game.conversational_orchestration import ConversationalDecision, ConversationalDecisionCategory

    category = kwargs.pop("category")
    return ConversationalDecision(category=ConversationalDecisionCategory(category), **kwargs)


def _auth(character, scene, *, subject, row, resolution, kind, disposition, layer, candidates) -> dict[str, Any]:
    return {
        "authority_provenance": "player_http_projection.CHARACTER",
        "source": "character.inventory" if kind != "prepared_spells" else "character.spells.prepared",
        "information_type": kind,
        "information_disposition": disposition,
        "reference_disposition": "RESOLVED" if row else ("AMBIGUOUS" if disposition == "AMBIGUOUS" else "UNMATCHED"),
        "subject": subject,
        "subject_id": row.get("id") if row else None,
        "subject_instance_id": row.get("instance_id") if row else None,
        "scene_id": _scene_id(scene),
        "character_id": str((character or {}).get("id") or ""),
        "scope": row.get("scope") if row else None,
        "binding_layer": layer,
        "inventory_candidates": [
            {"id": item.get("id"), "instance_id": item.get("instance_id")}
            for item in (resolution.get("carried") or [])
        ] if isinstance(resolution, Mapping) else candidates,
        "mutation_eligibility": False,
        "turn_advancement": False,
    }


def _sheet_text(act: str, row: Mapping[str, Any] | None, character) -> str:
    name = str((row or {}).get("name") or "that object")
    if act == "prepared_spells":
        spells = prepared_spell_rows(character)
        names = [item["name"] for item in spells]
        available = [item["name"] for item in spells if item.get("cast") is False]
        spent = [item["name"] for item in spells if item.get("cast") is True]
        if not names:
            text = "Your character sheet does not list any prepared spells. "
        else:
            text = f"Your character sheet has these spells prepared: {_join(names)}. "
            if spent:
                ready = _join(available) if available else "none"
                text += f"Still marked available to cast: {ready}. Already marked cast: {_join(spent)}. "
            text += "These are prepared spells, not a record of spells written in a spellbook. "
        if row:
            text += f"The {name} you are carrying is a separate object. "
        return text + "Nothing has been cast, and no spell slot has been used."
    if act == "recorded_spells":
        return (
            f"Your inventory records {name}. The character sheet does not record the spells written in it. "
            "Prepared spells are a separate list and are not the book's contents. Nothing has been cast."
        )
    if act == "contents":
        return (
            f"Your inventory records {name}. Its contents are not established by the available information. "
            "Nothing has been cast."
        )
    if act == "unsupported_use":
        return f"I cannot carry out that use of {name} with the available actions. No action has been attempted."
    if act == "identity":
        return f"That refers to the {name} you are carrying. No further contents are established."
    return f"Your inventory records {name}. Further descriptive details are not established by the available information."


def _nonexecution(text: str, act: str):
    if act == "conditional":
        return _decision(
            category="CLARIFY",
            primary_intention=text,
            intent_family="inventory_inspection",
            reason="conditional_player_action",
            player_facing_text="Nothing has been attempted. That action is only conditional.",
            execution_policy="answer_only",
            intent_modality="hypothetical",
            disposition="CONDITIONAL",
            authorization={"mutation_eligibility": False, "turn_advancement": False, "binding_layer": "host_reference_resolution"},
        )
    return _decision(
        category="CLARIFY",
        primary_intention=text,
        intent_family="inventory_inspection",
        reason="negated_player_action",
        player_facing_text="You do not do that. Nothing has been attempted.",
        execution_policy="answer_only",
        intent_modality="planning",
        disposition="NEGATED",
        authorization={"mutation_eligibility": False, "turn_advancement": False, "binding_layer": "host_reference_resolution"},
    )


def _answer_request(text, request, *, character, scene, log, layer: str | None = None):
    act = request["act"]
    if act in {"conditional", "negated"}:
        return _nonexecution(text, act)
    resolution = resolve_object_reference(text, request.get("subject") or "", character=character, scene=scene, log=log)
    if act == "prepared_spells":
        row = resolution.get("row") if resolution.get("status") == "resolved" and resolution.get("row", {}).get("scope") != "scene" else None
        if resolution.get("status") == "scene":
            row = None
        return _decision(
            category="ANSWER",
            primary_intention=text,
            intent_family="spell_information" if row is None else "inventory_inspection",
            reason="prepared_spell_sheet",
            player_facing_text=_sheet_text(act, row, character),
            execution_policy="answer_only",
            intent_modality="informational",
            disposition="ANSWERABLE",
            proposed_target=row.get("id") if row else None,
            authorization=_auth(
                character, scene, subject=request.get("subject") or "prepared spells", row=row,
                resolution=resolution, kind="prepared_spells", disposition="ANSWERABLE",
                layer=layer or "host_reference_resolution", candidates=[],
            ),
        )
    if resolution.get("status") == "ambiguous":
        return _decision(
            category="CLARIFY",
            primary_intention=text,
            intent_family="inventory_inspection",
            reason="ambiguous_carried_object",
            player_facing_text=_which(_choice_labels(resolution)),
            execution_policy="answer_only",
            intent_modality="informational",
            disposition="AMBIGUOUS",
            missing_information=["object_target"],
            authorization=_auth(
                character, scene, subject=request.get("subject") or "", row=None, resolution=resolution,
                kind=act, disposition="AMBIGUOUS", layer=layer or "host_reference_resolution", candidates=[],
            ),
        )
    if resolution.get("status") == "scene":
        return None
    row = resolution.get("row") if resolution.get("status") == "resolved" else None
    if row is None:
        if act == "unsupported_use":
            return None
        from game.referenced_surface import render_referenced_surface_inspection_line

        return _decision(
            category="CLARIFY",
            primary_intention=text,
            intent_family="inventory_inspection",
            reason="unresolved_object_reference",
            player_facing_text=render_referenced_surface_inspection_line({"authority": "unsupported"}, scene),
            execution_policy="answer_only",
            intent_modality="informational",
            disposition="UNMATCHED",
            missing_information=["object_target"],
            authorization=_auth(
                character, scene, subject=request.get("subject") or "", row=None, resolution=resolution,
                kind=act, disposition="UNMATCHED", layer=layer or "host_reference_resolution", candidates=[],
            ),
        )
    category = "DECLINE" if act == "unsupported_use" else "ANSWER"
    return _decision(
        category=category,
        primary_intention=text,
        intent_family="inventory_inspection",
        reason="unsupported_carried_use" if act == "unsupported_use" else "player_sheet_carried_object",
        player_facing_text=_sheet_text(act, row, character),
        execution_policy="answer_only",
        intent_modality="informational",
        disposition="UNSUPPORTED" if act == "unsupported_use" else "ANSWERABLE",
        proposed_target=row.get("id"),
        authorization=_auth(
            character, scene, subject=row.get("name") or request.get("subject") or "", row=row,
            resolution=resolution, kind=act, disposition="UNSUPPORTED" if act == "unsupported_use" else "ANSWERABLE",
            layer=layer or resolution.get("binding_layer") or "host_reference_resolution", candidates=[],
        ),
    )


def carried_object_decision(text: str, *, character, session, scene, world, log):
    """Deterministic sheet answer. Existing examine/inspect wording stays with its owner."""
    del session, world
    request = classify_carried_request(text, include_examine=False)
    if request is None:
        return None
    return _answer_request(text, request, character=character, scene=scene, log=log)


def _conflict(player_text: str, target_id: str):
    return _decision(
        category="CLARIFY",
        primary_intention=player_text,
        intent_family="inventory_inspection",
        reason="model_target_conflict",
        player_facing_text="The object in that interpretation is not the one you described. Nothing has been attempted.",
        execution_policy="answer_only",
        intent_modality="informational",
        disposition="AMBIGUOUS",
        missing_information=["object_target"],
        authorization={
            "binding_layer": "model_rejected",
            "rejected_id": target_id,
            "subject_id": None,
            "mutation_eligibility": False,
            "turn_advancement": False,
            "information_disposition": "AMBIGUOUS",
        },
    )


def _model_target(record: Mapping[str, Any]) -> tuple[str, str]:
    components = record.get("action_components") if isinstance(record.get("action_components"), list) else []
    component = components[0] if components and isinstance(components[0], Mapping) else {}
    target = component.get("target_ref")
    target_id = target.strip() if isinstance(target, str) else ""
    return target_id, str(component.get("operation_class") or "").upper()


def decision_for_model_record(record, player_text: str, *, character, scene, world, session, log):
    """Apply host grounding to a stored model record without replacing a real conflict."""
    del session
    if not isinstance(record, Mapping):
        return None
    request = classify_carried_request(player_text, include_examine=True)
    if request is None:
        return None
    if request["act"] in {"conditional", "negated"}:
        return _nonexecution(player_text, request["act"])
    target_id, _operation = _model_target(record)
    catalog = interpretation_catalog(
        scene if isinstance(scene, dict) else None,
        world if isinstance(world, dict) else None,
        character,
    )
    if target_id and target_id not in catalog:
        if request["act"] == "prepared_spells":
            target_id = ""
        else:
            return _decision(
                category="DECLINE",
                primary_intention=player_text,
                intent_family="inventory_inspection",
                reason="fabricated_object_id",
                player_facing_text="That object is not among the established objects here or in your inventory. Nothing has been attempted.",
                execution_policy="answer_only",
                intent_modality="informational",
                disposition="REJECTED",
                proposed_target=None,
                authorization={
                    "binding_layer": "model_rejected",
                    "rejected_id": target_id,
                    "mutation_eligibility": False,
                    "turn_advancement": False,
                    "information_disposition": "REJECTED",
                },
            )
    resolution = resolve_object_reference(
        player_text, request.get("subject") or "", character=character, scene=scene, log=log,
    )
    if resolution.get("status") == "scene":
        scene_ids = {str(row.get("id") or "") for row in resolution.get("scene") or []}
        if not target_id or target_id in scene_ids:
            return None
    # An unknown scene referent keeps the existing decline. This owner only
    # answers a carried object, a real ambiguity, or a character-sheet question.
    if resolution.get("status") == "unresolved" and request["act"] != "prepared_spells":
        return None
    host_id = str((resolution.get("row") or {}).get("id") or "") if resolution.get("status") == "resolved" else ""
    if resolution.get("status") == "ambiguous":
        return _answer_request(player_text, request, character=character, scene=scene, log=log)
    if target_id and host_id and target_id != host_id:
        return _conflict(player_text, target_id)
    if target_id and not host_id and request["act"] != "prepared_spells":
        return _conflict(player_text, target_id)
    layer = "model_interpretation" if target_id and target_id == host_id else None
    return _answer_request(player_text, request, character=character, scene=scene, log=log, layer=layer)
