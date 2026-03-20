"""Deterministic skill check authority layer.

The engine—not GPT—decides when rolls occur and resolves them.
All uncertain actions (exploration + social) pass through should_trigger_check
and resolve_skill_check. Result is passed to GPT for narration only.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional


# Difficulty bands (DC): easy 8–10, standard 10–14, hard 14–18
DC_EASY = 8
DC_STANDARD = 12
DC_HARD = 16


def _deterministic_d20(seed_parts: list) -> int:
    """Produce a deterministic d20 (1–20) from seed parts. Same inputs → same output."""
    if not seed_parts:
        seed_parts = ["default"]
    s = "|".join(str(p) for p in seed_parts)
    h = int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)
    return (h % 20) + 1


def resolve_skill_check(
    skill: str,
    difficulty: int,
    actor_stats: dict,
    context: dict | None = None,
) -> dict:
    """Resolve a skill check deterministically. Engine owns the roll.

    Args:
        skill: Skill id (e.g. "perception", "diplomacy").
        difficulty: DC / target number.
        actor_stats: Dict with "skills" key mapping skill_id → modifier; or direct {skill: modifier}.
        context: Optional dict with seed_parts for deterministic roll; e.g. ["turn_counter", "scene_id", "action_id"].

    Returns:
        {
            "skill": str,
            "difficulty": int,
            "modifier": int,
            "roll": int,
            "total": int,
            "success": bool
        }
        Also includes "dc" for backward compatibility.
    """
    modifier = 0
    if actor_stats and isinstance(actor_stats, dict):
        skills = actor_stats.get("skills")
        if isinstance(skills, dict):
            v = skills.get(skill)
            if v is not None:
                try:
                    modifier = int(v)
                except (TypeError, ValueError):
                    pass
        elif isinstance(actor_stats.get(skill), (int, float)):
            modifier = int(actor_stats[skill])

    ctx = context or {}
    seed_parts = ctx.get("seed_parts")
    if not isinstance(seed_parts, list):
        seed_parts = [
            ctx.get("turn_counter"),
            ctx.get("scene_id"),
            ctx.get("action_id"),
            ctx.get("character_id"),
            skill,
            str(difficulty),
        ]
    roll = _deterministic_d20(seed_parts)
    total = roll + modifier
    success = total >= difficulty

    return {
        "skill": skill,
        "difficulty": difficulty,
        "dc": difficulty,
        "modifier": modifier,
        "roll": roll,
        "total": total,
        "success": success,
    }


def should_trigger_check(action: dict, context: dict) -> dict:
    """Decide whether a skill check is required. Engine-owned decision.

    Args:
        action: Structured action with "type", "id", etc.
        context: Dict with scene, session, interactable (optional), scene_config (optional).

    Returns:
        {
            "requires_check": bool,
            "skill": str | None,
            "difficulty": int | None,
            "reason": str
        }
    """
    action_type = (action.get("type") or "").strip().lower()
    scene = context.get("scene") or {}
    session = context.get("session") or {}
    interactable = context.get("interactable")
    scene_runtime = context.get("scene_runtime") or {}
    engine = context.get("engine", "exploration")  # "exploration" | "social"

    # Already resolved: do not roll again
    if action.get("already_searched") or scene_runtime.get("already_searched"):
        return {"requires_check": False, "skill": None, "difficulty": None, "reason": "already_resolved"}
    if interactable and context.get("interactable_resolved"):
        return {"requires_check": False, "skill": None, "difficulty": None, "reason": "interactable_already_resolved"}

    # ----- Social -----
    if engine == "social":
        check_kinds = ("persuade", "intimidate", "deceive", "barter", "recruit")
        if action_type in check_kinds:
            # Base DC 10 (standard); recruit +3; deceive +2 for difficulty
            skill_map = {
                "persuade": ("diplomacy", 10),
                "intimidate": ("intimidate", 10),
                "deceive": ("bluff", 12),
                "barter": ("diplomacy", 10),
                "recruit": ("diplomacy", 13),
            }
            skill, dc = skill_map.get(action_type, ("diplomacy", DC_STANDARD))
            npc = context.get("npc") or {}
            dc_mod = 0
            if isinstance(npc.get("skill_check_modifier"), (int, float)):
                dc_mod += int(npc["skill_check_modifier"])
            overrides = npc.get("skill_check_overrides") or {}
            if isinstance(overrides, dict) and action_type in overrides:
                v = overrides[action_type]
                if isinstance(v, (int, float)):
                    dc_mod += int(v)
            dc = dc + dc_mod
            return {"requires_check": True, "skill": skill, "difficulty": dc, "reason": f"{action_type}_attempt"}
        # question / social_probe: no check by default (obvious, safe info)
        return {"requires_check": False, "skill": None, "difficulty": None, "reason": "social_probe_no_check"}

    # ----- Exploration -----
    # 1. Scene/action config takes precedence
    scene_inner = scene.get("scene", scene) if isinstance(scene, dict) else scene
    if not isinstance(scene_inner, dict):
        scene_inner = {}

    action_id = (action.get("id") or action.get("action_id") or "").strip()
    skill_config = None

    if interactable and isinstance(interactable.get("skill_check"), dict):
        sc = interactable["skill_check"]
        if sc.get("skill_id") and sc.get("dc") is not None:
            skill_config = {"skill_id": sc["skill_id"], "dc": int(sc["dc"])}

    if not skill_config:
        for raw in scene_inner.get("actions") or scene_inner.get("suggested_actions") or []:
            if not isinstance(raw, dict):
                continue
            raw_id = str(raw.get("id") or raw.get("action_id") or "").strip()
            if raw_id == action_id and isinstance(raw.get("skill_check"), dict):
                sc = raw["skill_check"]
                if sc.get("skill_id") and sc.get("dc") is not None:
                    skill_config = {"skill_id": sc["skill_id"], "dc": int(sc["dc"])}
                break

    if not skill_config:
        defaults = scene_inner.get("skill_check_defaults")
        if isinstance(defaults, dict) and action_type in ("observe", "investigate", "interact"):
            sc = defaults.get(action_type)
            if isinstance(sc, dict) and sc.get("skill_id") and sc.get("dc") is not None:
                skill_config = {"skill_id": sc["skill_id"], "dc": int(sc["dc"])}

    if skill_config:
        return {
            "requires_check": True,
            "skill": str(skill_config["skill_id"]),
            "difficulty": int(skill_config["dc"]),
            "reason": "scene_config",
        }

    # 2. Heuristics: risky exploration - only when explicit config exists.
    # Interactables with reveals_clue but no skill_check preserve legacy auto-success.
    # (Add "gated": true to interactable to require a check when no config.)
    # For now, no implicit heuristic to avoid breaking existing content.

    # 3. scene_transition, observe (no config), interact (no config) → no roll
    return {"requires_check": False, "skill": None, "difficulty": None, "reason": "no_config_or_safe"}
