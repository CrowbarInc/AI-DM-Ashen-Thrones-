"""Shared resolver dispatch. Existing engines only. No second rules implementation."""
from __future__ import annotations

import json
import time
from copy import deepcopy
from typing import Any
from unittest.mock import patch

from game.api import _apply_authoritative_resolution_state_mutation
from game.combat import resolve_attack
from game.exploration import resolve_exploration_action
from game.intent_parser import parse_freeform_to_action
from game.live_resolution import attach_interaction_obligation
from game.noncombat_resolution import resolve_noncombat_action
from game.ordinary_semantic_ownership import establish_ordinary_gameplay_contract, select_ordinary_resolver
from game.scene_actions import normalize_scene_action
from game.storage import list_scene_ids, load_scene
from tests.test_pr_db_speaker_grounding import play_turn

from experiments.pr_dg.state import Bundle, state_tuple

ATTACK_LINE = "I attack the goblin with my quarterstaff."
SEARCH_LINE = "Search."


def select_contract(bundle: Bundle, text: str) -> dict[str, Any]:
    """Contract and selector on a discarded copy so the live bundle stays untouched."""
    scratch = bundle.clone()
    shell: dict[str, Any] = {"prompt": text, "metadata": {}}
    scene_id = str((scratch.scene.get("scene") or {}).get("id") or scratch.session.get("active_scene_id") or "")
    contract = establish_ordinary_gameplay_contract(
        shell,
        player_text=text,
        session=scratch.session,
        scene_id=scene_id,
        scene=scratch.scene,
        world=scratch.world,
    )
    resolver, family = select_ordinary_resolver(contract, in_combat=bool(scratch.combat.get("in_combat")))
    construction = contract.get("construction") if isinstance(contract.get("construction"), dict) else {}
    return {
        "resolver": resolver,
        "family": family,
        "operation": contract.get("operation"),
        "subject": construction.get("resolution_subject"),
        "commitment": construction.get("commitment_status"),
        "ambiguous": bool(contract.get("ambiguous")),
        "fast_path_abstained": bool(construction.get("fast_path_abstained")),
        "model_interpretation_appropriate": bool(construction.get("model_interpretation_appropriate")),
        "interlocutor_id": contract.get("interlocutor_id"),
        "contract_id": contract.get("contract_id"),
    }


def _scene_id(bundle: Bundle) -> str:
    return str((bundle.scene.get("scene") or {}).get("id") or bundle.session.get("active_scene_id") or "")


def _restore(bundle: Bundle, snap: Bundle) -> None:
    bundle.session = snap.session
    bundle.world = snap.world
    bundle.scene = snap.scene
    bundle.combat = snap.combat
    bundle.character = snap.character


def _apply_mutator(bundle: Bundle, resolution: dict, normalized: dict | None) -> dict[str, Any]:
    """Apply the existing mutator. On exception, keep the resolver commit and undo mutator writes."""
    if not isinstance(resolution, dict):
        return {"applied": False, "reason": "no_resolution"}
    if resolution.get("route") == "none":
        return {"applied": False, "reason": "route_none"}
    held = bundle.clone()
    started = time.perf_counter()
    try:
        scene, session, combat, clues, _scene_rt = _apply_authoritative_resolution_state_mutation(
            session=bundle.session,
            world=bundle.world,
            combat=bundle.combat,
            scene=bundle.scene,
            resolution=resolution,
            normalized_action=normalized,
        )
        bundle.scene = scene
        bundle.session = session
        bundle.combat = combat
        return {
            "applied": True,
            "clue_updates": list(clues or []),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        }
    except Exception as exc:  # noqa: BLE001 - mutator failure is an observed engine limit
        _restore(bundle, held)
        return {
            "applied": False,
            "reason": "mutator_exception",
            "error": f"{type(exc).__name__}: {exc}"[:300],
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        }


def _social(bundle: Bundle, text: str) -> dict[str, Any]:
    started = time.perf_counter()
    view = play_turn(bundle.session, bundle.scene, bundle.world, text)
    resolution = view.get("resolution") if isinstance(view.get("resolution"), dict) else {}
    mutator = _apply_mutator(bundle, resolution, {"type": view.get("parsed_type"), "prompt": text, "label": text})
    return {
        "operations": ["play_turn", "resolve_social_action", "_apply_authoritative_resolution_state_mutation"],
        "resolver": view.get("resolver") or "social",
        "kind": resolution.get("kind"),
        "parsed_type": view.get("parsed_type"),
        "interlocutor_id": view.get("social_npc_id") or view.get("contract_interlocutor"),
        "resolution": _public_resolution(resolution),
        "mutator": mutator,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "unsupported": not bool(view.get("should_route_social")),
        "unsupported_reason": None if view.get("should_route_social") else "social_entry_did_not_route",
        "player_visible": "",
    }


def _noncombat(bundle: Bundle, text: str) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = parse_freeform_to_action(text, bundle.scene)
    if not isinstance(parsed, dict):
        parsed = {"type": "custom", "label": text, "prompt": text}
    parsed = dict(parsed)
    parsed.setdefault("label", text)
    parsed.setdefault("prompt", text)
    parsed.setdefault("id", "pr_dg_step")
    resolution = resolve_noncombat_action(
        bundle.scene,
        bundle.session,
        bundle.world,
        parsed,
        raw_player_text=text,
        character=bundle.character,
        turn_counter=int(bundle.session.get("turn_counter") or 0),
        exploration_kwargs={"list_scene_ids": list_scene_ids, "load_scene_fn": load_scene},
    )
    attach_interaction_obligation(
        resolution,
        player_text=text,
        session=bundle.session,
        normalized_action=parsed,
        scene_id=_scene_id(bundle),
        scene=bundle.scene,
        world=bundle.world,
        enable_model_interpretation=False,
    )
    metadata = resolution.setdefault("metadata", {})
    contract = metadata.get("resolution_contract") if isinstance(metadata.get("resolution_contract"), dict) else {}
    selected = None
    if contract:
        selected, _family = select_ordinary_resolver(contract, in_combat=bool(bundle.combat.get("in_combat")))
        metadata["selected_resolver"] = selected
    route_none = resolution.get("route") == "none" or bool(resolution.get("unsupported_reason_codes"))
    mutator = {"applied": False, "reason": "route_none"} if route_none else _apply_mutator(bundle, resolution, parsed)
    return {
        "operations": ["parse_freeform_to_action", "resolve_noncombat_action", "attach_interaction_obligation"],
        "resolver": selected or "exploration",
        "kind": resolution.get("kind"),
        "parsed_type": parsed.get("type"),
        "resolution": _public_resolution(resolution),
        "mutator": mutator,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "unsupported": bool(route_none),
        "unsupported_codes": list(resolution.get("unsupported_reason_codes") or []),
        "player_visible": "",
    }


def _skill(bundle: Bundle, text: str) -> dict[str, Any]:
    started = time.perf_counter()
    action = normalize_scene_action({"id": "inv", "label": "Investigate", "type": "investigate", "prompt": text or SEARCH_LINE})
    resolution = resolve_exploration_action(
        bundle.scene,
        bundle.session,
        bundle.world,
        action,
        raw_player_text=text or SEARCH_LINE,
        character=bundle.character,
        list_scene_ids=lambda: [],
    )
    attach_interaction_obligation(
        resolution,
        player_text=text or SEARCH_LINE,
        session=bundle.session,
        normalized_action=action,
        scene_id="x",
        scene=bundle.scene,
        world=bundle.world,
        enable_model_interpretation=False,
    )
    mutator = _apply_mutator(bundle, resolution, action)
    return {
        "operations": ["resolve_exploration_action", "attach_interaction_obligation"],
        "resolver": "exploration",
        "kind": resolution.get("kind"),
        "parsed_type": "investigate",
        "resolution": _public_resolution(resolution),
        "mutator": mutator,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "unsupported": False,
        "player_visible": "",
    }


def _attack(bundle: Bundle) -> dict[str, Any]:
    started = time.perf_counter()
    patcher = patch("game.combat.roll_die", return_value=10) if bundle.dice == 10 else None
    if patcher:
        patcher.start()
    try:
        resolution = resolve_attack(
            bundle.character,
            bundle.scene,
            "quarterstaff",
            "goblin_1",
            [],
            bundle.conditions,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "operations": ["resolve_attack"],
            "resolver": "combat",
            "kind": "attack",
            "resolution": {},
            "mutator": {"applied": False, "reason": "resolver_exception", "error": f"{type(exc).__name__}: {exc}"[:300]},
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "unsupported": True,
            "player_visible": "",
        }
    finally:
        if patcher:
            patcher.stop()
    attach_interaction_obligation(
        resolution,
        player_text=ATTACK_LINE,
        session=bundle.session,
        normalized_action={"type": "attack", "prompt": ATTACK_LINE, "label": "Attack"},
        scene_id=_scene_id(bundle),
        scene=bundle.scene,
        world=bundle.world,
        enable_model_interpretation=False,
    )
    mutator = _apply_mutator(
        bundle,
        resolution,
        {"type": "attack", "prompt": ATTACK_LINE, "label": "Attack"},
    )
    return {
        "operations": ["resolve_attack"],
        "resolver": "combat",
        "kind": resolution.get("kind"),
        "parsed_type": "attack",
        "resolution": _public_resolution(resolution),
        "mutator": mutator,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "unsupported": False,
        "player_visible": str(resolution.get("hint") or ""),
    }


def _public_resolution(resolution: dict) -> dict[str, Any]:
    """Resolver fields the comparison records. Narration prose is not included."""
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    skill = resolution.get("skill_check") if isinstance(resolution.get("skill_check"), dict) else None
    combat = resolution.get("combat") if isinstance(resolution.get("combat"), dict) else {}
    return {
        "kind": resolution.get("kind"),
        "success": resolution.get("success"),
        "route": resolution.get("route"),
        "resolved_transition": resolution.get("resolved_transition"),
        "target_scene_id": resolution.get("target_scene_id"),
        "unsupported_reason_codes": list(resolution.get("unsupported_reason_codes") or []),
        "blocked_reason_codes": list(resolution.get("blocked_reason_codes") or []),
        "social_npc_id": social.get("npc_id"),
        "reply_plan_kind": social.get("reply_plan_kind"),
        "skill_check": skill,
        "hit": (combat.get("rolls") or {}).get("attack_total") if isinstance(combat.get("rolls"), dict) else resolution.get("success"),
        "damage_dealt": (combat.get("damage_dealt") if "damage_dealt" in combat else None),
    }


def execute_authorized(bundle: Bundle, text: str, selector: dict[str, Any]) -> dict[str, Any]:
    """Run the resolver the contract selector named. Generation does not invent a resolver."""
    resolver = str(selector.get("resolver") or "generation")
    before = bundle.clone()
    try:
        if resolver == "social":
            result = _social(bundle, text)
        elif resolver in {"exploration", "travel"}:
            if bundle.lane == "skill" and text.strip() == SEARCH_LINE:
                result = _skill(bundle, text)
            else:
                result = _noncombat(bundle, text)
        elif resolver == "combat":
            if not bundle.combat.get("in_combat"):
                return _unsupported(selector, "combat_while_not_in_combat")
            if "quarterstaff" not in text.lower() and text.strip() != ATTACK_LINE:
                return _unsupported(selector, "not_the_authored_attack")
            result = _attack(bundle)
        elif resolver == "world_action":
            result = _noncombat(bundle, text)
            if result.get("unsupported"):
                result["unsupported_reason"] = "world_action_not_delegated"
        elif resolver == "adjudication":
            if bundle.lane == "skill":
                result = _skill(bundle, text)
            else:
                return _unsupported(selector, "adjudication_preview_or_resolver_not_separated")
        else:
            return _unsupported(selector, "generation_no_specialized_resolver")
    except Exception as exc:  # noqa: BLE001
        _restore(bundle, before)
        return {
            "operations": [],
            "resolver": resolver,
            "unsupported": True,
            "unsupported_reason": "resolver_exception",
            "error": f"{type(exc).__name__}: {exc}"[:300],
            "resolution": {},
            "mutator": {"applied": False, "reason": "restored"},
            "player_visible": "",
            "elapsed_ms": 0,
        }
    result["selector"] = selector
    result["state_after_step"] = state_tuple(bundle)
    return result


def _unsupported(selector: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "operations": [],
        "resolver": selector.get("resolver"),
        "selector": selector,
        "unsupported": True,
        "unsupported_reason": reason,
        "resolution": {},
        "mutator": {"applied": False, "reason": reason},
        "player_visible": "",
        "elapsed_ms": 0,
        "kind": "unsupported",
    }


def narration_payload_bytes(bundle: Bundle, resolution: dict | None, text: str) -> dict[str, Any]:
    """Byte size of the narration request PR-DE would build. Does not call a provider."""
    from tools.measure_pr_de_affordability import _load_pr_dd

    measure = _load_pr_dd()
    scratch = bundle.clone()
    payload_resolution = deepcopy(resolution) if isinstance(resolution, dict) else {"kind": "generation", "prompt": text, "metadata": {}}
    try:
        messages = measure._messages_for(
            payload_resolution,
            scratch.session,
            scratch.scene,
            scratch.world,
            text,
            combat=scratch.combat,
            character=scratch.character,
        )
        blob, _system, _parts, _payload = measure._split(messages)
        raw = blob.encode("utf-8")
        return {
            "narration_bytes": len(raw),
            "estimated_input_tokens_ceil_bytes_div_4": (len(raw) + 3) // 4,
            "estimation_method": "ceil(utf8_bytes/4)",
            "provider_call": False,
            "sha256": __import__("hashlib").sha256(raw).hexdigest(),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "narration_bytes": None,
            "estimated_input_tokens_ceil_bytes_div_4": None,
            "estimation_method": "ceil(utf8_bytes/4)",
            "provider_call": False,
            "error": f"{type(exc).__name__}: {exc}"[:300],
        }


def serialized_bytes(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8"))
