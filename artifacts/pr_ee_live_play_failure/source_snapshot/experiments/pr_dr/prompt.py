"""Scene-limited prompt for the PR-DO interpretation contract.

The prompt lists only what the active disposable scene shows. It does not
include clue text, NPC answers, production saves, or narration instructions.
"""

from __future__ import annotations

import json
from typing import Any

from experiments.pr_dp.prompt import HIDDEN_PROBES, estimate_input_tokens, provider_schema
from experiments.pr_dq.gameplay import DisposableHarness

_MODE_LINE = (
    "IN_WORLD_ACTION=the character acts or speaks in the scene; "
    "OUT_OF_CHARACTER_CORRECTION=the player corrects a referent, an intention, or a committed action; "
    "RULES_QUESTION=the player asks how play works; "
    "CLARIFICATION=the utterance is unclear; "
    "OTHER=none of these."
)
_CLASS_LINE = (
    "Describable for later validation: MOVE, ATTACK, INSPECT, ASK, SOCIAL_SIGNAL, PERCEIVE, FOLLOW, USE_VISIBLE_OBJECT. "
    "Ineligible: HP_ASSIGNMENT, DICE_OVERRIDE, INVENTORY_GRANT, CANON_DECLARATION, NPC_COMMITMENT, "
    "HIDDEN_INFORMATION_REQUEST, RETCON, UNSUPPORTED_MECHANIC, TIME_CONTROL, STEALTH_MODE_TOGGLE."
)


def visible_catalog(harness: DisposableHarness) -> list[tuple[str, str, str]]:
    """Entity id, label, and kind for the active scene only."""
    scene = harness.active_envelope().get("scene") or {}
    rows: list[tuple[str, str, str]] = []
    for item in scene.get("interactables") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        kind = "inspect_target" if item.get("reveals_clue") else "perceive_target"
        rows.append((str(item["id"]), str(item.get("label") or item["id"]), kind))
    for item in scene.get("exits") or []:
        if isinstance(item, dict) and item.get("id"):
            rows.append((str(item["id"]), str(item.get("label") or item["id"]), "exit"))
    scene_id = str(scene.get("id") or "")
    for npc in harness.world.get("npcs") or []:
        if not isinstance(npc, dict) or not npc.get("id"):
            continue
        location = str(npc.get("location") or npc.get("scene_id") or "")
        if location == scene_id:
            rows.append((str(npc["id"]), str(npc.get("name") or npc["id"]), "npc"))
    return rows


def scene_line(harness: DisposableHarness) -> str:
    scene = harness.active_envelope().get("scene") or {}
    location = str(scene.get("location") or scene.get("id") or "")
    summary = str(scene.get("summary") or "")
    return f"{location}. {summary}".strip()


def build_messages_for_catalog(
    utterance: str,
    *,
    scene_summary: str,
    catalog: list[tuple[str, str, str]],
    recent_visible: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """PR-DO prompt for one visible catalog. Recent lines are player-visible text only."""
    visible = "; ".join(f"{entity_id}={label} ({kind})" for entity_id, label, kind in catalog)
    lines = [
        f"Utterance: {utterance}",
        f"Visible scene: {scene_summary}",
        f"Permitted entity references: {visible}.",
        f"Communication modes: {_MODE_LINE}",
        f"Operation classes: {_CLASS_LINE}",
        "Later validation is not authorization. Describe the attempt. Do not authorize execution.",
        "If the utterance is ambiguous between in-character play and table talk, use CLARIFICATION, one question, and no guessed id.",
        "Premises and wished results are text. No outcomes, HP, dice, inventory, time, canon, NPC commitments, hidden facts, or execution.",
        "Use only permitted entity ids. Order attempts. Empty list or string if unused.",
    ]
    if recent_visible:
        lines.append("Recent visible turns: " + json.dumps(recent_visible, ensure_ascii=False))
    return [
        {"role": "system", "content": "Fill the schema. Describe the attempt. Do not authorize execution."},
        {"role": "user", "content": "\n".join(lines)},
    ]


def build_messages(utterance: str, harness: DisposableHarness) -> list[dict[str, str]]:
    return build_messages_for_catalog(
        utterance,
        scene_summary=scene_line(harness),
        catalog=visible_catalog(harness),
    )


def context_leaks(messages: list[dict[str, str]], utterance: str) -> list[str]:
    """Hidden-information probes in the prompt context, ignoring the player's own words."""
    blob = json.dumps(messages, ensure_ascii=False).casefold().replace(utterance.casefold(), "")
    return [item for item in HIDDEN_PROBES if item.casefold() in blob]


def preflight_tokens(messages: list[dict[str, str]]) -> int:
    return estimate_input_tokens(messages, provider_schema())


def prompt_grants_tools(messages: list[dict[str, str]]) -> bool:
    blob = json.dumps(messages, ensure_ascii=False).casefold()
    return "function_call" in blob or "\"tools\"" in blob
