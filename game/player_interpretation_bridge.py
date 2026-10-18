"""Production-safe bridge from stored interpretation records to engine actions.

The bridge accepts an already-produced interpretation record. It does not call a
model and it does not execute a resolver. Its job is only to validate that the
record names a visible target and convert it into the normalized action shape
the existing production turn pipeline already understands.
"""

from __future__ import annotations

from typing import Any, Callable


CONNECTED_OPERATIONS = {
    "PERCEIVE": "observe",
    "INSPECT": "investigate",
    "ASK": "question",
    "MOVE": "scene_transition",
}

_EXPECTED_VISIBLE_KIND = {
    "PERCEIVE": "perceive_target",
    "INSPECT": "inspect_target",
    "ASK": "npc",
    "MOVE": "exit",
}


def _scene_obj(scene: dict | None) -> dict:
    if not isinstance(scene, dict):
        return {}
    inner = scene.get("scene")
    return inner if isinstance(inner, dict) else scene


def visible_catalog(scene: dict | None, world: dict | None) -> dict[str, dict[str, Any]]:
    """Return visible entity ids for the active scene, with coarse engine kinds."""
    current_scene = _scene_obj(scene)
    scene_id = str(current_scene.get("id") or "").strip()
    out: dict[str, dict[str, Any]] = {}
    for item in current_scene.get("interactables") or []:
        if not isinstance(item, dict):
            continue
        entity_id = str(item.get("id") or "").strip()
        if not entity_id:
            continue
        out[entity_id] = {
            "kind": "inspect_target" if item.get("reveals_clue") else "perceive_target",
            "row": item,
        }
    for item in current_scene.get("exits") or []:
        if not isinstance(item, dict):
            continue
        entity_id = str(item.get("id") or "").strip()
        if not entity_id:
            continue
        out[entity_id] = {"kind": "exit", "row": item}
    for npc in (world or {}).get("npcs") or []:
        if not isinstance(npc, dict):
            continue
        entity_id = str(npc.get("id") or "").strip()
        if not entity_id:
            continue
        if str(npc.get("location") or "").strip() == scene_id:
            out[entity_id] = {"kind": "npc", "row": npc}
    return out


def _single_component(record: dict[str, Any]) -> tuple[str, str | None]:
    components = record.get("action_components")
    if not isinstance(components, list) or len(components) != 1:
        return "", None
    component = components[0] if isinstance(components[0], dict) else {}
    return str(component.get("operation_class") or "").strip().upper(), component.get("target_ref")


def _record_from_interpretation(interpretation: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(interpretation, dict):
        return None
    if isinstance(interpretation.get("record"), dict):
        return interpretation["record"]
    return interpretation


def reconcile_reference_annotations(record: dict, *, player_text: str, scene: dict | None,
                                    world: dict | None, session: dict | None = None) -> tuple[dict, dict]:
    """Reconcile proposals against existing grounding; never select facts or effects.

    Subject presence is independent of knowledge/disclosure eligibility. Authored
    topics establish vocabulary only; the social resolver still owns disclosure.
    Unidentified annotations stay unresolved, including provider/player conflicts.
    """
    import copy
    import re
    from game.ordinary_semantic_ownership import assess_addressee_grounding
    from game.conversational_orchestration import _place_match

    result = copy.deepcopy(record)
    refs = result.get("references") or {}
    unresolved = refs.get("unresolved_references") or []
    evidence = {"annotations": [], "addressee": None, "operation": None}
    operation, target_id = _single_component(result)
    evidence["operation"] = operation
    if (result.get("interpretation_status") not in {"INTERPRETED", "CLARIFICATION_REQUIRED"}
            or operation not in CONNECTED_OPERATIONS
            or (not unresolved and result.get("interpretation_status") == "INTERPRETED")):
        return result, evidence
    catalog = visible_catalog(scene, world)
    grounding = None
    if operation == "ASK":
        grounding = assess_addressee_grounding(player_text, scene=scene, world=world,
                                               session=session, proposed_target_id=target_id)
        evidence["addressee"] = grounding
    grounded_id = str((grounding or {}).get("target_id") or "")
    addressee_ok = bool(grounding and grounding.get("operation_eligibility") == "executable")
    if operation == "ASK" and addressee_ok and grounding.get("direct_address") and not target_id:
        # Reuse the existing addressee resolver for a missing proposed target.
        result["action_components"][0]["target_ref"] = grounded_id
        if grounded_id not in refs.get("permitted_entity_ids", []):
            refs.setdefault("permitted_entity_ids", []).append(grounded_id)
        evidence["target_handoff"] = {"status": "RESOLVABLE", "target_id": grounded_id}
    speaker = (catalog.get(grounded_id) or {}).get("row") or {}
    current = _scene_obj(scene)
    # Engine-owned authored/visible passages, never provider subject/summary.
    passages = [("scene", str(current.get("summary") or ""))]
    passages += [("scene.visible_fact", str(v)) for v in current.get("visible_facts") or []]
    from game.dialogue_authority import npc_source_permitted
    if addressee_ok:
        passages += [("npc.authored_subject", str(t.get("text") or ""))
                     for t in speaker.get("topics") or [] if isinstance(t, dict) and npc_source_permitted(speaker, t)]
    def mentioned(phrase, text):
        return bool(phrase and re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, re.I))
    remaining = []
    for annotation in unresolved:
        phrase = str(annotation).strip()
        explicit = mentioned(phrase, player_text)
        candidates = [entity_id for entity_id, info in catalog.items()
                      if any(_place_match(phrase, str(label)) for label in
                             [info["row"].get("name"), info["row"].get("label"),
                              *info["row"].get("aliases", [])] if label)]
        status, source, role = "MISSING", None, "subject" if operation == "ASK" else "target"
        # These are role identifiers, not entity names or free-text matches.
        # Their proposed role grants nothing: the existing engine resolver must
        # independently confirm the player-addressed person.
        if operation == "ASK" and not explicit and phrase in {"npc_to_ask", "addressee", "interlocutor"}:
            role = "addressee"
            if addressee_ok and grounding.get("direct_address"):
                status, source = "GROUNDED", grounding.get("target_provenance")
        if operation == "ASK" and not addressee_ok and grounding.get("target_resolution") == "ambiguous":
            from game.interaction_completion import addressed_person_nominal
            nominal = addressed_person_nominal(player_text)
            if mentioned(phrase, nominal):
                status, role = "AMBIGUOUS", "addressee"
        if operation == "ASK" and grounded_id in candidates:
            role = "addressee"
            if addressee_ok and explicit and len(candidates) == 1:
                status, source = "GROUNDED", grounding.get("target_provenance")
        elif explicit and len(candidates) == 1 and (operation == "ASK" or candidates[0] == target_id):
            status, source = "GROUNDED", "visible_catalog:" + candidates[0]
        elif len(candidates) > 1:
            status = "AMBIGUOUS"
        elif operation == "ASK" and addressee_ok and explicit:
            source = next((owner for owner, text in passages if mentioned(phrase, text)), None)
            if source:
                status = "GROUNDED"
        if status == "MISSING" and operation == "ASK" and addressee_ok and not explicit and not candidates:
            from game.conversational_continuity import _DEICTIC
            from game.social import _next_topic_to_reveal
            # An unmentioned noun cannot veto a uniquely supported explicit
            # question. Ask the existing read-only selector for eligibility;
            # no fact is adopted here and disclosure still runs in the resolver.
            if not _DEICTIC.search(player_text):
                selection = {}
                supported = _next_topic_to_reveal(
                    speaker, ((session or {}).get("npc_runtime") or {}).get(grounded_id) or {},
                    player_text=player_text, allow_revealed=True, selection=selection)
                if supported and not selection.get("ambiguous"):
                    status, source = "NOT_APPLICABLE", selection.get("selected_source")
        if status not in {"GROUNDED", "NOT_APPLICABLE"}:
            remaining.append(annotation)
        evidence["annotations"].append(dict(annotation=annotation, role=role, status=status,
                                              explicit=explicit, candidates=candidates, source=source))
    result["references"]["unresolved_references"] = remaining
    if (operation == "ASK" and addressee_ok and grounding.get("direct_address")
            and not remaining and result.get("interpretation_status") == "CLARIFICATION_REQUIRED"):
        from game.conversational_continuity import _DEICTIC
        # Do not override a potentially unresolved deictic subject merely
        # because the person addressed is known.
        if not _DEICTIC.search(player_text):
            result["interpretation_status"] = "INTERPRETED"
            result["clarification_question"] = ""
            result["communication_mode"] = "IN_WORLD_ACTION"
            evidence["status_reconciled"] = "explicit_addressee_no_remaining_reference"
    return result, evidence


def normalized_action_from_interpretation(
    interpretation: dict[str, Any] | None,
    *,
    scene: dict,
    world: dict,
    player_text: str,
    known_scene_ids: Callable[[], list[str]] | None = None,
    session: dict | None = None,
    authorized_target_id: str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Validate a stored interpretation and return a production normalized action.

    The metadata return value is intended for traces and failure reports.
    """
    record = _record_from_interpretation(interpretation)
    if not isinstance(record, dict):
        return None, {"source": "stored_interpretation", "accepted": False, "reason": "missing_record"}
    if str(record.get("communication_mode") or "").strip() != "IN_WORLD_ACTION":
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "not_in_world_action",
            "communication_mode": record.get("communication_mode"),
        }
    if str(record.get("interpretation_status") or "").strip() != "INTERPRETED":
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "not_interpreted",
            "interpretation_status": record.get("interpretation_status"),
        }
    record, reconciliation = reconcile_reference_annotations(
        record, player_text=player_text, scene=scene, world=world, session=session)
    refs = record.get("references") if isinstance(record.get("references"), dict) else {}
    unresolved = refs.get("unresolved_references") if isinstance(refs, dict) else []
    if unresolved:
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "unresolved_references",
            "unresolved_references": list(unresolved),
            "reference_reconciliation": reconciliation,
        }
    operation, target_ref = _single_component(record)
    if operation not in CONNECTED_OPERATIONS:
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "unsupported_operation",
            "operation": operation,
        }
    target_id = str(target_ref or "").strip()
    if not target_id:
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "missing_target",
            "operation": operation,
        }

    confirmed = str(authorized_target_id or "").strip()
    if operation == "ASK" and confirmed != target_id:
        from game.ordinary_semantic_ownership import assess_addressee_grounding, pending_addressee_clarification

        grounding = assess_addressee_grounding(
            player_text,
            scene=scene,
            world=world,
            session=session,
            proposed_target_id=target_id,
        )
        eligibility = str(grounding.get("operation_eligibility") or "")
        grounded_id = str(grounding.get("target_id") or "").strip()
        if eligibility == "executable" and grounded_id:
            target_id = grounded_id
        else:
            reason = "ambiguous_addressee" if eligibility == "requires_clarification" or grounding.get("direct_address") else "ungrounded_provider_target"
            pending = pending_addressee_clarification(grounding, player_text, scene)
            clarification = str(grounding.get("clarification") or "").strip()
            if not clarification:
                clarification = "Which person do you mean? Nothing has been attempted." if reason == "ambiguous_addressee" else "I cannot tell who that is addressed to. Nothing has been attempted."
            return None, {
                "source": "stored_interpretation",
                "accepted": False,
                "reason": reason,
                "operation": operation,
                "target_ref": target_id,
                "candidate_target_ids": list(grounding.get("candidate_target_ids") or []),
                "clarification": clarification,
                "authorization": grounding,
                "pending_intention": pending,
            }
    catalog = visible_catalog(scene, world)
    target = catalog.get(target_id)
    if not target:
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "target_not_visible",
            "operation": operation,
            "target_ref": target_id,
        }
    expected_kind = _EXPECTED_VISIBLE_KIND[operation]
    target_kind = str(target.get("kind") or "")
    visible_surface_inspection = False
    if operation == "INSPECT" and target_kind == "perceive_target":
        visible_surface_inspection = True
    elif target_kind != expected_kind:
        return None, {
            "source": "stored_interpretation",
            "accepted": False,
            "reason": "operation_incompatible_with_entity_kind",
            "operation": operation,
            "target_ref": target_id,
            "target_kind": target_kind,
        }

    normalized: dict[str, Any] = {
        "id": target_id,
        "label": str((target.get("row") or {}).get("label") or (target.get("row") or {}).get("name") or target_id),
        "type": CONNECTED_OPERATIONS[operation],
        "prompt": player_text,
        "target_id": target_id,
        "targetEntityId": target_id,
        "metadata": {
            "stored_interpretation": {
                "operation": operation,
                "target_ref": target_id,
                "visible_surface_inspection": visible_surface_inspection,
                "reference_reconciliation": record.get("reference_reconciliation") or reconciliation,
            }
        },
    }
    semantic_plan = record.get("unified_semantic_plan")
    if isinstance(semantic_plan, dict) and semantic_plan.get("locked"):
        normalized["metadata"]["unified_semantic_plan"] = dict(semantic_plan)
    communication = record.get("communication")
    if isinstance(communication, dict):
        normalized["metadata"]["communication"] = dict(communication)
        normalized["metadata"]["public_conversation_evidence"] = dict(record.get("public_evidence") or {})
    if visible_surface_inspection:
        normalized["metadata"]["stored_interpretation"]["compatibility"] = "visible_surface_inspection"
    if operation == "MOVE":
        row = target.get("row") if isinstance(target.get("row"), dict) else {}
        destination = str(row.get("target_scene_id") or "").strip()
        if not destination:
            return None, {
                "source": "stored_interpretation",
                "accepted": False,
                "reason": "exit_has_no_authored_destination",
                "operation": operation,
                "target_ref": target_id,
            }
        if known_scene_ids is not None and destination not in set(known_scene_ids()):
            return None, {
                "source": "stored_interpretation",
                "accepted": False,
                "reason": "unknown_destination_scene",
                "operation": operation,
                "target_ref": target_id,
                "target_scene_id": destination,
            }
        normalized["targetSceneId"] = destination
        normalized["target_scene_id"] = destination
    return normalized, {
        "source": "stored_interpretation",
        "accepted": True,
        "operation": operation,
        "target_ref": target_id,
        "engine_type": normalized["type"],
        "visible_surface_inspection": visible_surface_inspection,
    }
