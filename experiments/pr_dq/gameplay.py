"""Experimental gameplay adapter for accepted IC messages.

The adapter calls existing resolvers on a disposable world. It does not call
a provider, production chat, or storage.activate_scene. An unaccepted attempt
is discarded before it is marked committed.
"""

from __future__ import annotations

import copy
from typing import Any

from experiments.pr_do.schema import UNSUPPORTED_OPERATION_CLASSES
from experiments.pr_dq.classify import ingest_player_message
from experiments.pr_dq.envelope import PlayerMessage
from experiments.pr_dq.history import ConversationHistory
from experiments.pr_dq.route import execution_permitted
from experiments.pr_dq.safety import (
    authoritative_snapshot,
    nonmutating_response,
    refuse_unexecuted_mutation,
)
from experiments.pr_dq.world import (
    GATE_ID,
    LANTERN_ID,
    LANTERN_TEXT,
    NOTICE_ID,
    STREET_ARRIVAL,
    STREET_ID,
    build_disposable_world,
)
from experiments.pr_dq.surface_compat import accepted_visible_surface_text
from game.clocks import advance_clock
from game.exploration import resolve_exploration_action
from game.scene_graph import build_scene_graph, is_transition_valid
from game.social import resolve_social_action
from game.storage import mark_interactable_resolved


def _dice_rolled(resolution: dict[str, Any]) -> bool:
    if resolution.get("skill_check"):
        return True
    meta = resolution.get("metadata")
    if isinstance(meta, dict) and meta.get("skill_check"):
        return True
    social = resolution.get("social")
    return isinstance(social, dict) and bool(social.get("skill_check"))


def _closed_result(**extra: Any) -> dict[str, Any]:
    result = {
        "executed": False,
        "resolver_invoked": False,
        "mutated_state": False,
        "advances_time": False,
        "consumes_action": False,
        "rolls_dice": False,
        "history_rewritten": False,
        "includes_model_text": False,
        "adjudication_required": False,
        "response": "",
        "reason": "",
        "resolution_kind": None,
        "resolution_success": None,
    }
    result.update(extra)
    return result


class DisposableHarness:
    """One courtyard session. Production files are not this object's state."""

    def __init__(self) -> None:
        built = build_disposable_world()
        self.session = built["session"]
        self.world = built["world"]
        self.scenes = built["scenes"]
        self.character = built["character"]
        self.combat = built["combat"]
        self.history = ConversationHistory()
        self.resolver_calls: list[str] = []

    def active_envelope(self) -> dict[str, Any]:
        return self.scenes[self.session["active_scene_id"]]

    def list_scene_ids(self) -> list[str]:
        return sorted(self.scenes)

    def load_scene(self, scene_id: str) -> dict[str, Any]:
        return self.scenes[scene_id]

    def submit(
        self,
        text: str,
        *,
        message_id: str,
        mode_override: str = "AUTO",
        intent: str | None = None,
        correction_subject: str = "NONE",
        action: dict[str, Any] | None = None,
    ) -> PlayerMessage:
        message = ingest_player_message(
            text,
            message_id=message_id,
            mode_override=mode_override,
            intent=intent,
            correction_subject=correction_subject,
        )
        self.history.append(message)
        dispatch_message(message, self, action)
        return message


def dispatch_message(
    message: PlayerMessage,
    harness: DisposableHarness,
    action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Route a prepared message. OOC, mixed, and unresolved paths do not resolve."""
    before = authoritative_snapshot(harness)
    if message.mode == "OOC" and message.correction_subject == "COMMITTED_ACTION":
        message.adjudication_required = True
    if not execution_permitted(message):
        result = _closed_result(
            response=nonmutating_response(message),
            reason=_defer_reason(message),
            adjudication_required=message.adjudication_required,
        )
        _finish_unexecuted(message, result)
        refuse_unexecuted_mutation(before, authoritative_snapshot(harness), message)
        return result
    return _execute_ic(message, harness, action or {}, before)


def _defer_reason(message: PlayerMessage) -> str:
    if message.mode == "OOC":
        return "ooc_cannot_execute_authoritative_gameplay"
    if message.mode == "MIXED":
        return "mixed_message_deferred"
    if message.mode == "UNRESOLVED":
        return "unresolved_mode_not_executed"
    if message.destination == "CLARIFICATION_REQUIRED":
        return "clarification_required"
    if message.status == "REJECTED":
        return "rejected"
    return "execution_not_permitted"


def _finish_unexecuted(message: PlayerMessage, result: dict[str, Any]) -> None:
    prior = message.processing_result.get("reclassification")
    if prior:
        result["reclassification"] = prior
    message.processing_result = result
    message.committed = False
    if message.adjudication_required or message.destination in {
        "MIXED_MESSAGE",
        "CLARIFICATION_REQUIRED",
    }:
        message.status = "AWAITING_CLARIFICATION"
    elif message.status != "REJECTED":
        message.status = "PROCESSED"


def _execute_ic(
    message: PlayerMessage,
    harness: DisposableHarness,
    action: dict[str, Any],
    before: str,
) -> dict[str, Any]:
    operation = str(action.get("operation_class") or "")
    if operation in UNSUPPORTED_OPERATION_CLASSES or not operation:
        result = _closed_result(
            reason="unsupported_mechanic" if operation else "no_hand_authored_action",
            response="That in-character request is not a supported mechanic. No state was changed.",
        )
        message.status = "REJECTED"
        message.processing_result = result
        message.committed = False
        refuse_unexecuted_mutation(before, authoritative_snapshot(harness), message)
        return result

    normalized, refusal = _validated_action(harness, action, message.text)
    if normalized is None:
        result = _closed_result(
            reason=refusal,
            response="That in-character action is blocked. No state was changed.",
        )
        message.status = "REJECTED"
        message.processing_result = result
        message.committed = False
        refuse_unexecuted_mutation(before, authoritative_snapshot(harness), message)
        return result

    pre_session = copy.deepcopy(harness.session)
    pre_character = copy.deepcopy(harness.character)
    pre_world = copy.deepcopy(harness.world)
    pre_combat = copy.deepcopy(harness.combat)
    resolution = _invoke_resolver(harness, message, normalized)
    harness.character = pre_character
    harness.world = pre_world
    harness.combat = pre_combat
    accepted, visible = _accept_resolution(harness, action, resolution)
    if not accepted:
        harness.session = pre_session
        result = _closed_result(
            resolver_invoked=True,
            reason="engine_rejected_attempt",
            response="The engine did not accept that action. No state was changed.",
            resolution_kind=resolution.get("kind"),
            resolution_success=resolution.get("success"),
            rolls_dice=_dice_rolled(resolution),
        )
        message.status = "REJECTED"
        message.processing_result = result
        message.committed = False
        refuse_unexecuted_mutation(before, authoritative_snapshot(harness), message)
        return result

    _apply_accepted(harness, action, resolution)
    after = authoritative_snapshot(harness)
    result = _closed_result(
        executed=True,
        resolver_invoked=True,
        mutated_state=before != after,
        advances_time=action.get("engine_type") == "scene_transition",
        consumes_action=False,
        response=visible,
        reason="accepted_by_engine",
        resolution_kind=resolution.get("kind"),
        resolution_success=resolution.get("success"),
        rolls_dice=_dice_rolled(resolution),
    )
    message.processing_result = result
    message.status = "PROCESSED"
    message.committed = True
    return result


def _validated_action(
    harness: DisposableHarness,
    action: dict[str, Any],
    text: str,
) -> tuple[dict[str, Any] | None, str]:
    engine_type = str(action.get("engine_type") or "")
    target_id = str(action.get("target_id") or "")
    scene = harness.active_envelope().get("scene") or {}
    if engine_type in {"observe", "investigate"}:
        ids = {
            str(item.get("id") or "")
            for item in (scene.get("interactables") or [])
            if isinstance(item, dict)
        }
        if target_id not in ids:
            return None, "target_not_in_active_scene"
    elif engine_type == "question":
        ids = {
            str(npc.get("id") or "")
            for npc in (harness.world.get("npcs") or [])
            if isinstance(npc, dict)
        }
        if target_id not in ids:
            return None, "npc_not_in_world"
    elif engine_type == "scene_transition":
        target_scene = str(action.get("target_scene_id") or "")
        exit_row = None
        for item in scene.get("exits") or []:
            if not isinstance(item, dict):
                continue
            if str(item.get("id") or "") == target_id and str(item.get("target_scene_id") or "") == target_scene:
                exit_row = item
                break
        if exit_row is None:
            return None, "exit_not_in_active_scene"
        graph = build_scene_graph(harness.list_scene_ids, harness.load_scene)
        known = set(harness.scenes)
        if not is_transition_valid(
            str(scene.get("id") or ""),
            target_scene,
            graph,
            session=harness.session,
            known_scene_ids=known,
        ):
            return None, "transition_not_in_scene_graph"
    else:
        return None, "no_resolver_for_engine_type"

    normalized = {
        "id": target_id or engine_type,
        "type": engine_type,
        "label": target_id or engine_type,
        "prompt": text,
        "target_id": target_id,
        "targetEntityId": target_id,
    }
    if engine_type == "scene_transition":
        normalized["targetSceneId"] = action.get("target_scene_id")
    return normalized, ""


def _invoke_resolver(
    harness: DisposableHarness,
    message: PlayerMessage,
    normalized: dict[str, Any],
) -> dict[str, Any]:
    if message.mode != "IC":
        raise RuntimeError("OOC messages must not execute authoritative gameplay actions")
    engine_type = normalized["type"]
    envelope = copy.deepcopy(harness.active_envelope())
    if engine_type == "question":
        harness.resolver_calls.append("game.social.resolve_social_action")
        return resolve_social_action(
            envelope,
            harness.session,
            harness.world,
            normalized,
            raw_player_text=message.text,
            character=harness.character,
            turn_counter=int(harness.session.get("turn_counter") or 0),
        )
    harness.resolver_calls.append("game.exploration.resolve_exploration_action")
    return resolve_exploration_action(
        envelope,
        harness.session,
        harness.world,
        normalized,
        raw_player_text=message.text,
        list_scene_ids=harness.list_scene_ids,
        scene_graph=build_scene_graph(harness.list_scene_ids, harness.load_scene),
        load_scene_fn=harness.load_scene,
        character=harness.character,
    )


def _accept_resolution(
    harness: DisposableHarness,
    action: dict[str, Any],
    resolution: dict[str, Any],
) -> tuple[bool, str]:
    engine_type = action.get("engine_type")
    target_id = str(action.get("target_id") or "")
    kind = str(resolution.get("kind") or "")
    if engine_type == "observe":
        if kind != "observe" or resolution.get("success") is not None:
            return False, ""
        if _dice_rolled(resolution):
            return False, ""
        return True, _lantern_visible(harness, target_id, resolution)
    if engine_type == "investigate":
        if action.get("visible_surface_inspection") is True:
            visible = accepted_visible_surface_text(harness, action, resolution)
            if visible is None or _dice_rolled(resolution):
                return False, ""
            return True, visible
        if kind != "discover_clue" or resolution.get("interactable_id") != target_id:
            return False, ""
        if _dice_rolled(resolution):
            return False, ""
        clues = resolution.get("discovered_clues") or []
        visible = clues[0] if clues else str(resolution.get("hint") or "")
        return True, str(visible)
    if engine_type == "question":
        social = resolution.get("social") or {}
        if kind != "question" or social.get("npc_id") != target_id:
            return False, ""
        if _dice_rolled(resolution):
            return False, ""
        clues = resolution.get("discovered_clues") or []
        visible = clues[0] if clues else str(resolution.get("hint") or "")
        return True, str(visible)
    if engine_type == "scene_transition":
        if not resolution.get("resolved_transition"):
            return False, ""
        if resolution.get("target_scene_id") != action.get("target_scene_id"):
            return False, ""
        if _dice_rolled(resolution):
            return False, ""
        return True, STREET_ARRIVAL
    return False, ""


def _lantern_visible(harness: DisposableHarness, target_id: str, resolution: dict[str, Any]) -> str:
    if target_id == LANTERN_ID:
        return LANTERN_TEXT
    scene = harness.active_envelope().get("scene") or {}
    for item in scene.get("interactables") or []:
        if isinstance(item, dict) and item.get("id") == target_id:
            return str(item.get("description") or resolution.get("hint") or "")
    return str(resolution.get("hint") or "")


def _apply_accepted(
    harness: DisposableHarness,
    action: dict[str, Any],
    resolution: dict[str, Any],
) -> None:
    if action.get("engine_type") == "scene_transition" and resolution.get("resolved_transition"):
        target = str(resolution.get("target_scene_id") or "")
        harness.session["active_scene_id"] = target
        visited = list(harness.session.get("visited_scene_ids") or [])
        if target not in visited:
            visited.append(target)
        harness.session["visited_scene_ids"] = visited
        scene_state = harness.session.get("scene_state")
        if isinstance(scene_state, dict):
            scene_state["active_scene_id"] = target
        advance_clock(harness.session, "time_pressure", 1)
    if action.get("engine_type") == "investigate" and resolution.get("kind") == "discover_clue":
        mark_interactable_resolved(
            harness.session,
            str(harness.session.get("active_scene_id") or ""),
            str(resolution.get("interactable_id") or ""),
        )
    harness.session["turn_counter"] = int(harness.session.get("turn_counter") or 0) + 1


# Re-exported ids used by the slice fixtures.
SLICE_TARGET_IDS = {
    "lantern": LANTERN_ID,
    "gate": GATE_ID,
    "street": STREET_ID,
    "notice": NOTICE_ID,
}
