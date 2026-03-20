"""Structured scene actions for exploration: normalize legacy or structured input to a canonical shape."""
from __future__ import annotations

from typing import Any, Dict, List

from game.utils import slugify


ACTION_TYPES = ("scene_transition", "investigate", "interact", "travel", "observe", "custom")


def infer_action_type_from_label(label: str) -> str:
    """Best-effort type from legacy text. Used when type is not already set."""
    if not label or not isinstance(label, str):
        return "custom"
    t = label.strip().lower()
    if t.startswith("go:") or t.startswith("go to") or t.startswith("travel to"):
        return "scene_transition"
    if t.startswith("investigate:") or t.startswith("investigate ") or "investigate" in t[:20]:
        return "investigate"
    if t.startswith("observe") or t.startswith("scan") or "observe" in t[:15] or "scan" in t[:15]:
        return "observe"
    if t.startswith("talk") or t.startswith("speak") or "interact" in t[:20] or "gauge" in t[:20]:
        return "interact"
    if "travel" in t[:25] or "route" in t[:25]:
        return "travel"
    return "custom"


def normalize_scene_action(raw: Any) -> Dict[str, Any]:
    """Accept legacy string or legacy affordance dict or structured action; return canonical structured action.

    Canonical shape: id, label, type, targetSceneId?, targetEntityId?, targetLocationId?, metadata?
    Legacy: string (label only), or dict with label/category/prompt (old affordance) -> type inferred, prompt in metadata.
    """
    out: Dict[str, Any] = {
        "id": "",
        "label": "",
        "type": "custom",
        "metadata": {},
        # Keep these keys present for a stable frontend-facing shape.
        "targetSceneId": None,
        "targetEntityId": None,
        "targetLocationId": None,
    }
    if raw is None:
        return out
    if isinstance(raw, str):
        # Legacy: plain string action
        out["label"] = raw.strip() or "Action"
        out["id"] = slugify(out["label"]) or "action"
        out["type"] = infer_action_type_from_label(out["label"])
        out["prompt"] = out["label"]
        return out
    if not isinstance(raw, dict):
        return out
    # Dict: may be legacy affordance (id, label, category, prompt) or already structured
    out["id"] = str(raw.get("id") or "").strip() or slugify(str(raw.get("label") or raw.get("prompt") or "action")) or "action"
    out["label"] = str(raw.get("label") or raw.get("prompt") or "").strip() or out["id"]
    out["type"] = str(raw.get("type") or "").strip().lower()
    if out["type"] not in ACTION_TYPES:
        # Legacy category or infer from label
        leg_cat = str(raw.get("category") or "").strip().lower()
        if leg_cat in ("travel", "scene_transition"):
            out["type"] = "scene_transition" if raw.get("target_scene_id") or raw.get("targetSceneId") else "travel"
        elif leg_cat == "investigate":
            out["type"] = "investigate"
        elif leg_cat == "observe":
            out["type"] = "observe"
        elif leg_cat in ("social", "interact"):
            out["type"] = "interact"
        else:
            out["type"] = infer_action_type_from_label(out["label"])
    out["targetSceneId"] = raw.get("targetSceneId") or raw.get("target_scene_id") or None
    if out["targetSceneId"] is not None:
        out["targetSceneId"] = str(out["targetSceneId"]).strip() or None
    out["targetEntityId"] = raw.get("targetEntityId") or raw.get("target_entity_id") or None
    if out["targetEntityId"] is not None:
        out["targetEntityId"] = str(out["targetEntityId"]).strip() or None
    out["targetLocationId"] = raw.get("targetLocationId") or raw.get("target_location_id") or None
    if out["targetLocationId"] is not None:
        out["targetLocationId"] = str(out["targetLocationId"]).strip() or None
    out["metadata"] = dict(raw.get("metadata") or {})
    # Legacy: preserve prompt for UI (fill chat input)
    if raw.get("prompt") and "prompt" not in out["metadata"]:
        out["metadata"]["prompt"] = str(raw["prompt"]).strip()
    # Backward compat: top-level prompt for consumers that expect it (e.g. UI, tests)
    out["prompt"] = out["metadata"].get("prompt") or out["label"]
    # Optional conditions for affordance filtering (requires_flags, requires_clues, excludes_flags, excludes_clues)
    cond = raw.get("conditions")
    if isinstance(cond, dict) and cond:
        out["conditions"] = {
            "requires_flags": list(cond["requires_flags"]) if isinstance(cond.get("requires_flags"), list) else [],
            "requires_clues": list(cond["requires_clues"]) if isinstance(cond.get("requires_clues"), list) else [],
            "excludes_flags": list(cond["excludes_flags"]) if isinstance(cond.get("excludes_flags"), list) else [],
            "excludes_clues": list(cond["excludes_clues"]) if isinstance(cond.get("excludes_clues"), list) else [],
        }
        # Drop empty condition lists to keep payload lean
        out["conditions"] = {k: v for k, v in out["conditions"].items() if v}
        if not out["conditions"]:
            del out["conditions"]
    # Drop None keys for a lean payload; keep metadata and stable target keys.
    preserve_none = {"targetSceneId", "targetEntityId", "targetLocationId"}
    for k in list(out):
        if out[k] is None and k not in ("metadata",) and k not in preserve_none:
            del out[k]
    return out


def normalize_scene_actions_list(raw_list: Any) -> List[Dict[str, Any]]:
    """Normalize a list of legacy or structured actions; skips invalid entries."""
    if not isinstance(raw_list, list):
        return []
    result: List[Dict[str, Any]] = []
    for raw in raw_list:
        action = normalize_scene_action(raw)
        if action.get("id") and action.get("label"):
            result.append(action)
    return result
