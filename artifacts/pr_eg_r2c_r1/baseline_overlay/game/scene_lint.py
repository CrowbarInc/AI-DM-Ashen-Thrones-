from __future__ import annotations

from typing import Any, Dict, List, Set


def _norm(s: str) -> str:
    return " ".join(str(s or "").lower().split())


def validate_scene(scene_envelope: Dict[str, Any], known_scene_ids: Set[str]) -> Dict[str, List[str]]:
    """Return {'errors': [...], 'warnings': [...]} for a single scene envelope."""
    errors: List[str] = []
    warnings: List[str] = []

    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    sid = scene.get("id") or "<unknown>"

    # 1) Exits with missing targets (supports target_scene_id and targetSceneId).
    exits = scene.get("exits") or []
    for ex in exits:
        tid = ex.get("target_scene_id") or ex.get("targetSceneId")
        if isinstance(tid, str) and tid.strip() and tid.strip() not in known_scene_ids:
            errors.append(f"{sid}: exit to unknown scene_id '{tid}'")

    visible_facts = [str(v) for v in (scene.get("visible_facts") or [])]
    discoverable = [str(v) for v in (scene.get("discoverable_clues") or [])]
    hidden = [str(v) for v in (scene.get("hidden_facts") or [])]

    norm_visible = [_norm(v) for v in visible_facts]
    norm_disc = [_norm(v) for v in discoverable]
    norm_hidden = [_norm(v) for v in hidden]

    # 2) Discoverable too similar to visible.
    for d_txt, d_norm in zip(discoverable, norm_disc):
        for v_norm in norm_visible:
            if d_norm and (d_norm == v_norm or d_norm in v_norm or v_norm in d_norm):
                warnings.append(f"{sid}: discoverable clue '{d_txt}' is very similar to a visible fact")
                break

    # 3) Hidden too similar to visible.
    for h_txt, h_norm in zip(hidden, norm_hidden):
        for v_norm in norm_visible:
            if h_norm and (h_norm == v_norm or h_norm in v_norm or v_norm in h_norm):
                warnings.append(f"{sid}: hidden fact '{h_txt}' is very similar to a visible fact")
                break

    # 4) Discoverable directly states hidden conclusion (very rough).
    for d_txt, d_norm in zip(discoverable, norm_disc):
        for h_norm in norm_hidden:
            if h_norm and h_norm in d_norm:
                warnings.append(f"{sid}: discoverable clue '{d_txt}' may directly state a hidden fact")
                break

    # 5) Missing affordance anchors: no visible facts and no exits.
    if not visible_facts and not exits:
        warnings.append(f"{sid}: scene has no visible facts and no exits; may lack obvious player anchors")

    # 6) Missing sensory grounding: simple lexical heuristic.
    sensory_words = ("smell", "scent", "sound", "hear", "noise", "see", "sight", "feel", "touch", "taste", "rain", "wind", "smoke")
    summary = _norm(scene.get("summary", ""))
    combined = " ".join([summary] + norm_visible)
    if not any(w in combined for w in sensory_words):
        warnings.append(f"{sid}: scene may lack sensory grounding words")

    return {"errors": errors, "warnings": warnings}

