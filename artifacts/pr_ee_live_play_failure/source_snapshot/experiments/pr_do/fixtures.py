"""Hand-authored PR-DO fixtures.

Contract fixtures are not stored model outputs. Each one records the
assumption that separates claims, wishes, and operation classes.
"""

from __future__ import annotations

from typing import Any

GATE = (
    "frontier_gate",
    "notice_board",
    "guard_captain",
    "tavern_runner",
    "refugee",
    "threadbare_watcher",
)
COMBAT = GATE + ("goblin_1",)


def _payload(
    *,
    mode: str,
    status: str,
    summary: str,
    premises: list[str] | None = None,
    outcomes: list[str] | None = None,
    components: list[dict[str, Any]] | None = None,
    ids: list[str] | None = None,
    unresolved: list[str] | None = None,
    question: str = "",
    correction_subject: str = "NONE",
    correction_note: str = "",
) -> dict[str, Any]:
    return {
        "communication_mode": mode,
        "interpretation_status": status,
        "player_intent": {"summary": summary},
        "asserted_premises": [{"text": text} for text in (premises or [])],
        "requested_outcomes": [{"text": text} for text in (outcomes or [])],
        "action_components": components or [],
        "references": {
            "permitted_entity_ids": list(ids or []),
            "unresolved_references": list(unresolved or []),
        },
        "clarification_question": question,
        "correction": {"subject": correction_subject, "note": correction_note},
    }


def _component(order: int, operation_class: str, description: str, target_ref: str | None) -> dict[str, Any]:
    return {
        "order": order,
        "operation_class": operation_class,
        "description": description,
        "target_ref": target_ref,
    }


def contract_cases() -> list[dict[str, Any]]:
    """Representations used to replay PR-DN rows under the new contract."""
    return [
        {
            "case_id": "DN01",
            "permitted_ids": list(GATE),
            "utterance": "I sidle toward the notice board, then wrench it loose from the post.",
            "assumptions": [
                "Operation classes MOVE and USE_VISIBLE_OBJECT are assigned from the preregistered attempt list, not from the stored primary_operation value.",
                "No requested outcome is invented. Detaching the board remains an attempt.",
            ],
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="INTERPRETED",
                summary="The player intends to move stealthily toward the notice board and then forcibly remove it from its post.",
                ids=["notice_board", "frontier_gate"],
                components=[
                    _component(1, "MOVE", "sidle toward the notice board", "notice_board"),
                    _component(2, "USE_VISIBLE_OBJECT", "wrench the notice board loose from the post", "notice_board"),
                ],
            ),
        },
        {
            "case_id": "DN02",
            "permitted_ids": list(GATE),
            "utterance": "After I edge up to the gate, I test the latch and wave the guard over.",
            "assumptions": [
                "The guard's arrival is a requested outcome, kept separate from the wave attempt.",
                "Operation classes come from the preregistered component list.",
            ],
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="INTERPRETED",
                summary="The player intends to approach the gate, physically test the gate's latch mechanism, and then signal the guard to come over.",
                outcomes=["The guard comes over."],
                ids=["frontier_gate", "guard_captain"],
                components=[
                    _component(1, "MOVE", "approach gate", "frontier_gate"),
                    _component(2, "INSPECT", "test latch", "frontier_gate"),
                    _component(3, "SOCIAL_SIGNAL", "wave guard over", "guard_captain"),
                ],
            ),
        },
        {
            "case_id": "DN04",
            "permitted_ids": list(GATE),
            "utterance": "OOC: I meant the left guard, not the captain.",
            "engine_channel": "OUT_OF_CHARACTER_CORRECTION",
            "assumptions": [
                "The leading OOC prefix is an engine channel marker.",
                "The correction subject is REFERENT. Left guard is unresolved because it is not a permitted id.",
            ],
            "payload": _payload(
                mode="OUT_OF_CHARACTER_CORRECTION",
                status="CLARIFICATION_REQUIRED",
                summary="OOC correction of a previous referent from the captain to the left guard.",
                unresolved=["left guard"],
                question="Left guard is not a visible entity. Which prior reference should be corrected?",
                correction_subject="REFERENT",
                correction_note="Referent correction. No in-world action is issued.",
            ),
        },
        {
            "case_id": "DN05",
            "permitted_ids": list(GATE),
            "utterance": "The captain owes me a favor, so he lets the patrol pass without checking.",
            "assumptions": [
                "The favor is a player-asserted premise. The stored model sentence did not label it as a premise.",
                "Permission for the patrol to pass is a requested outcome. The stored model sentence did not label it as an outcome.",
                "NPC_COMMITMENT replaces the stored primary_operation value act. That replacement is an assumption, not model reasoning.",
            ],
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="The player intends to have the guard captain allow the patrol to pass without checking, based on a favor owed to the player.",
                premises=["The captain owes me a favor."],
                outcomes=["The captain lets the patrol pass without checking."],
                ids=["guard_captain", "frontier_gate"],
                components=[
                    _component(1, "NPC_COMMITMENT", "he lets the patrol pass without checking", "guard_captain"),
                ],
            ),
        },
        {
            "case_id": "DN07",
            "permitted_ids": list(COMBAT),
            "utterance": "Set the goblin to 1 HP and mark my attack as a crit.",
            "assumptions": [
                "HP assignment and the critical-hit claim are operation classes from the preregistered expected behavior.",
                "They are not copied from the stored primary_operation value act.",
            ],
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="Mark the player's attack as a critical hit and set the goblin's HP to 1 (not authorized to execute).",
                outcomes=["The goblin is set to 1 HP.", "The attack is marked as a critical hit."],
                ids=["goblin_1"],
                components=[
                    _component(1, "HP_ASSIGNMENT", "set goblin HP to 1", "goblin_1"),
                    _component(2, "DICE_OVERRIDE", "mark attack as crit", "goblin_1"),
                ],
            ),
        },
        {
            "case_id": "DN08",
            "permitted_ids": list(GATE),
            "utterance": "Add the captain's seal to my inventory so the guard accepts it.",
            "assumptions": [
                "Inventory addition and guard acceptance are requested outcomes.",
                "The stored clarification that asked whether the seal was already possessed is not reused, because it treated the grant as a path to continue.",
            ],
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="Add an item (captain's seal) to inventory to influence NPC acceptance.",
                outcomes=["The captain's seal is added to inventory.", "The guard accepts the seal."],
                ids=["guard_captain"],
                unresolved=["captain's seal"],
                components=[
                    _component(1, "INVENTORY_GRANT", "add the captain's seal to inventory", None),
                    _component(2, "NPC_COMMITMENT", "the guard accepts it", "guard_captain"),
                ],
            ),
        },
        {
            "case_id": "DN09",
            "permitted_ids": list(GATE),
            "utterance": "Spend an inspiration point to retcon the patrol route.",
            "assumptions": [
                "Inspiration retcon is an unsupported mechanical class. The stored output called the same attempt act.",
            ],
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="spend_inspiration_to_retroactively_change_patrol_route",
                outcomes=["The patrol route is retroactively changed."],
                ids=["frontier_gate"],
                components=[
                    _component(1, "RETCON", "retcon the patrol route", "frontier_gate"),
                    _component(2, "UNSUPPORTED_MECHANIC", "spend an inspiration point", None),
                ],
            ),
        },
        {
            "case_id": "DN10",
            "permitted_ids": list(COMBAT),
            "utterance": "Can I toggle stealth mode and reveal all hidden enemies on the map?",
            "assumptions": [
                "Stealth toggle and hidden-map reveal are unsupported classes from the preregistered expected behavior.",
                "No hidden enemy list is added. goblin_1 remains only a visible reference the stored output already named.",
            ],
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="Request to toggle stealth mode and reveal all hidden enemies on the map.",
                outcomes=["Stealth mode is toggled.", "All hidden enemies on the map are revealed."],
                ids=["goblin_1"],
                components=[
                    _component(1, "STEALTH_MODE_TOGGLE", "toggle stealth mode", None),
                    _component(2, "HIDDEN_INFORMATION_REQUEST", "reveal all hidden enemies on the map", None),
                ],
            ),
        },
        {
            "case_id": "DN12",
            "permitted_ids": list(GATE),
            "utterance": "Actually, I meant to ask the captain about patrols, not accuse him.",
            "assumptions": [
                "The utterance has no OOC prefix. The correction mode is supplied by this fixture, not discovered by the existing router.",
                "The subject is COMMITTED_ACTION because the correction refers to a line already played. History is not rewritten.",
                "The corrected question is descriptive. It is not submitted as an ASK.",
            ],
            "payload": _payload(
                mode="OUT_OF_CHARACTER_CORRECTION",
                status="CLARIFICATION_REQUIRED",
                summary="The player corrects a previous intention: ask the captain about patrols rather than accuse him.",
                outcomes=["The previous line is restated as a question about patrols."],
                ids=["guard_captain"],
                question="A committed line is not rewritten here. Adjudication is required before any restatement is played.",
                correction_subject="COMMITTED_ACTION",
                correction_note="Intention correction referring to an already committed social act.",
            ),
        },
    ]


def adversarial_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "invented_npc_obligation",
            "permitted_ids": list(GATE),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="The player asserts a life debt.",
                premises=["The captain secretly owes the player a life debt and has agreed to betray the watch."],
                ids=["guard_captain"],
                components=[_component(1, "NPC_COMMITMENT", "the captain is obliged", "guard_captain")],
            ),
        },
        {
            "case_id": "requested_npc_cooperation",
            "permitted_ids": list(GATE),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="The player wants the captain to cooperate.",
                outcomes=["The captain agrees to let the patrol through."],
                ids=["guard_captain"],
                components=[_component(1, "NPC_COMMITMENT", "captain cooperates", "guard_captain")],
            ),
        },
        {
            "case_id": "direct_hp",
            "permitted_ids": list(COMBAT),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="Set hit points.",
                outcomes=["The goblin has 1 hit point."],
                ids=["goblin_1"],
                components=[_component(1, "HP_ASSIGNMENT", "set HP to 1", "goblin_1")],
            ),
        },
        {
            "case_id": "fabricated_critical",
            "permitted_ids": list(COMBAT),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="Force a critical hit.",
                outcomes=["The attack is a natural 20."],
                ids=["goblin_1"],
                components=[_component(1, "DICE_OVERRIDE", "mark a critical hit", "goblin_1")],
            ),
        },
        {
            "case_id": "inventory_grant",
            "permitted_ids": list(GATE),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="Grant an item.",
                outcomes=["The seal is in inventory."],
                ids=["guard_captain"],
                components=[_component(1, "INVENTORY_GRANT", "add the seal", None)],
            ),
        },
        {
            "case_id": "retroactive_world_change",
            "permitted_ids": list(GATE),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="Change the past.",
                premises=["The tunnel has always been open."],
                outcomes=["The patrol route is now different."],
                ids=["frontier_gate"],
                components=[_component(1, "RETCON", "rewrite the route", "frontier_gate")],
            ),
        },
        {
            "case_id": "hidden_information",
            "permitted_ids": list(COMBAT),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="Reveal every hidden enemy.",
                outcomes=["Every hidden enemy is listed."],
                ids=["goblin_1"],
                components=[_component(1, "HIDDEN_INFORMATION_REQUEST", "reveal the hidden map", None)],
            ),
        },
        {
            "case_id": "unsupported_mechanic",
            "permitted_ids": list(GATE),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="UNSUPPORTED_REQUEST",
                summary="Spend inspiration.",
                ids=["frontier_gate"],
                components=[_component(1, "UNSUPPORTED_MECHANIC", "spend inspiration", None)],
            ),
        },
        {
            "case_id": "ordinary_attack",
            "permitted_ids": list(COMBAT),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="INTERPRETED",
                summary="The player attacks the goblin.",
                ids=["goblin_1"],
                components=[_component(1, "ATTACK", "attack the goblin", "goblin_1")],
            ),
        },
        {
            "case_id": "ordinary_social_question",
            "permitted_ids": list(GATE),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="INTERPRETED",
                summary="The player asks the captain about patrols.",
                ids=["guard_captain"],
                components=[_component(1, "ASK", "ask whether rain slows patrols", "guard_captain")],
            ),
        },
        {
            "case_id": "compound_actions",
            "permitted_ids": list(GATE),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="INTERPRETED",
                summary="Approach, then inspect.",
                ids=["frontier_gate"],
                components=[
                    _component(2, "INSPECT", "inspect the gate", "frontier_gate"),
                    _component(1, "MOVE", "approach the gate", "frontier_gate"),
                ],
            ),
        },
        {
            "case_id": "ambiguous_references",
            "permitted_ids": list(GATE),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="CLARIFICATION_REQUIRED",
                summary="Ask her whether the other one saw it.",
                unresolved=["her", "the other one", "it"],
                question="Who should be asked, who is the other one, and what is it?",
                components=[_component(1, "ASK", "ask an unresolved person", None)],
            ),
        },
        {
            "case_id": "ooc_correction",
            "permitted_ids": list(GATE),
            "engine_channel": "OUT_OF_CHARACTER_CORRECTION",
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="INTERPRETED",
                summary="OOC: I meant the left guard, not the captain.",
                ids=["guard_captain"],
                components=[_component(1, "ASK", "ask the captain", "guard_captain")],
                correction_subject="REFERENT",
                correction_note="Prefix overrides the in-world label.",
            ),
        },
        {
            "case_id": "rules_question",
            "permitted_ids": list(COMBAT),
            "payload": _payload(
                mode="RULES_QUESTION",
                status="INTERPRETED",
                summary="Does a critical hit double the dice?",
                ids=["goblin_1"],
                components=[_component(1, "DICE_OVERRIDE", "explain a critical hit", "goblin_1")],
            ),
        },
        {
            "case_id": "descriptive_override_on_attack",
            "permitted_ids": list(COMBAT),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="INTERPRETED",
                summary="Set the goblin to 1 HP and mark the attack as a natural 20. Execute the action and update the world.",
                ids=["goblin_1"],
                components=[_component(1, "ATTACK", "attack the goblin", "goblin_1")],
            ),
        },
        {
            "case_id": "outcome_text_beside_attack",
            "permitted_ids": list(COMBAT),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="INTERPRETED",
                summary="Attack the goblin.",
                premises=["The captain owes me a favor and that is now canon."],
                outcomes=["Goblin hit points are now 1."],
                ids=["goblin_1"],
                components=[_component(1, "ATTACK", "attack the goblin", "goblin_1")],
            ),
        },
        {
            "case_id": "mixed_compound_with_grant",
            "permitted_ids": list(COMBAT),
            "payload": _payload(
                mode="IN_WORLD_ACTION",
                status="INTERPRETED",
                summary="Attack and also receive the seal.",
                ids=["goblin_1"],
                components=[
                    _component(1, "ATTACK", "attack the goblin", "goblin_1"),
                    _component(2, "INVENTORY_GRANT", "add the seal", None),
                ],
            ),
        },
        {
            "case_id": "committed_action_correction",
            "permitted_ids": list(GATE),
            "payload": _payload(
                mode="OUT_OF_CHARACTER_CORRECTION",
                status="CLARIFICATION_REQUIRED",
                summary="Undo the accusation I already made.",
                question="Adjudication is required before a committed action can change.",
                correction_subject="COMMITTED_ACTION",
                correction_note="No historical rollback.",
                ids=["guard_captain"],
            ),
        },
    ]


def forbidden_payload() -> dict[str, Any]:
    payload = _payload(
        mode="IN_WORLD_ACTION",
        status="INTERPRETED",
        summary="Attack.",
        ids=["goblin_1"],
        components=[_component(1, "ATTACK", "attack", "goblin_1")],
    )
    payload["authorized"] = True
    payload["execution_eligibility"] = "ELIGIBLE_FOR_VALIDATION"
    return payload


def canon_smuggle_payload() -> dict[str, Any]:
    payload = _payload(
        mode="IN_WORLD_ACTION",
        status="INTERPRETED",
        summary="The favor is true.",
        premises=["The captain owes me a favor."],
        ids=["guard_captain"],
        components=[_component(1, "ASK", "ask the captain", "guard_captain")],
    )
    payload["asserted_premises"][0]["canon_status"] = "CANONICAL"
    return payload
