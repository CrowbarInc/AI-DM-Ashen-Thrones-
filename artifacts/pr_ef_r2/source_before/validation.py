"""Scene validation: fail-fast checks for broken references and missing required fields.

Raises SceneValidationError with scene id and exact offending field.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Set

from game.utils import slugify


class SceneValidationError(ValueError):
    """Raised when scene content fails validation. Includes scene_id and field context."""

    def __init__(self, message: str, scene_id: str = "", field: str = ""):
        self.scene_id = scene_id
        self.field = field
        super().__init__(message)


def _scene_data(scene_envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Extract scene dict from envelope."""
    if not isinstance(scene_envelope, dict):
        return {}
    scene = scene_envelope.get("scene")
    return scene if isinstance(scene, dict) else {}


def _get_action_id(raw: Any) -> str | None:
    """Extract normalized action id from raw action."""
    if isinstance(raw, str):
        return (slugify(raw) or "action") if raw and str(raw).strip() else None
    if isinstance(raw, dict):
        aid = str(raw.get("id") or "").strip()
        if aid:
            return aid
        label = str(raw.get("label") or raw.get("prompt") or "").strip()
        return (slugify(label) or "action") if label else None
    return None


def _valid_clue_refs(scene: Dict[str, Any]) -> Set[str]:
    """Build set of valid clue identifiers from discoverable_clues (ids and normalized text)."""
    refs: Set[str] = set()
    clues = scene.get("discoverable_clues") or []
    for c in clues:
        if isinstance(c, dict):
            cid = str(c.get("id") or "").strip()
            text = str(c.get("text") or "").strip()
            if cid:
                refs.add(cid)
                refs.add(slugify(cid) or "")
            if text:
                refs.add(text)
                refs.add(slugify(text) or "")
        elif isinstance(c, str) and c.strip():
            refs.add(c.strip())
            refs.add(slugify(c) or "")
    return refs


def collect_scene_validation_issues(
    scene_envelope: Dict[str, Any],
    scene_id: str,
    known_scene_ids: Set[str],
) -> List[SceneValidationError]:
    """Return all strict validation issues for a scene (same rules as :func:`validate_scene`).

    Order matches the first error :func:`validate_scene` would raise, but every issue is collected.
    """
    issues: List[SceneValidationError] = []
    scene = _scene_data(scene_envelope)
    if not scene:
        issues.append(
            SceneValidationError(
                f"Scene envelope missing 'scene' root object",
                scene_id=scene_id,
                field="scene",
            )
        )
        return issues

    # 1) Scene id present and matches
    sid = scene.get("id")
    if not sid or not isinstance(sid, str) or not str(sid).strip():
        issues.append(
            SceneValidationError(
                f"Scene id is missing or empty",
                scene_id=str(scene_id),
                field="scene.id",
            )
        )
    elif str(sid).strip() != str(scene_id).strip():
        issues.append(
            SceneValidationError(
                f"Scene id '{sid}' does not match file scene_id '{scene_id}'",
                scene_id=str(scene_id),
                field="scene.id",
            )
        )

    # 2) Required fields: location, summary (architecture uses both)
    location = scene.get("location")
    if location is None or (isinstance(location, str) and not location.strip()):
        issues.append(
            SceneValidationError(
                f"Scene '{scene_id}' is missing required field 'location'",
                scene_id=str(scene_id),
                field="scene.location",
            )
        )
    summary = scene.get("summary")
    if summary is None or (isinstance(summary, str) and not summary.strip()):
        issues.append(
            SceneValidationError(
                f"Scene '{scene_id}' is missing required field 'summary'",
                scene_id=str(scene_id),
                field="scene.summary",
            )
        )

    # 3) Exits: target_scene_id must reference known scene when present
    exits = scene.get("exits") or []
    for idx, ex in enumerate(exits):
        if not isinstance(ex, dict):
            continue
        tid = ex.get("target_scene_id") or ex.get("targetSceneId")
        if tid is None or (isinstance(tid, str) and not tid.strip()):
            continue
        tid = str(tid).strip()
        if tid and tid not in known_scene_ids:
            label = ex.get("label", "")
            exit_label = f"'{label}'" if label else f"at index {idx}"
            issues.append(
                SceneValidationError(
                    f"Invalid scene '{scene_id}': exit {exit_label} points to missing target_scene_id '{tid}'",
                    scene_id=str(scene_id),
                    field=f"scene.exits[{idx}].target_scene_id",
                )
            )

    # 4) Affordance (scene.actions) ids unique within scene; targetSceneId references known scene
    actions = scene.get("actions") or scene.get("suggested_actions") or []
    seen_action_ids: Set[str] = set()
    for idx, raw in enumerate(actions):
        aid = _get_action_id(raw)
        if not aid:
            continue
        if aid in seen_action_ids:
            issues.append(
                SceneValidationError(
                    f"Invalid scene '{scene_id}': duplicate affordance action id '{aid}' in actions",
                    scene_id=str(scene_id),
                    field=f"scene.actions[{idx}].id",
                )
            )
            continue
        seen_action_ids.add(aid)

        # Action with targetSceneId must point to known scene
        if isinstance(raw, dict):
            tid = raw.get("targetSceneId") or raw.get("target_scene_id")
            if tid and isinstance(tid, str) and tid.strip():
                tid = tid.strip()
                if tid not in known_scene_ids:
                    issues.append(
                        SceneValidationError(
                            f"Invalid scene '{scene_id}': action '{aid}' points to missing targetSceneId '{tid}'",
                            scene_id=str(scene_id),
                            field=f"scene.actions[{idx}].targetSceneId",
                        )
                    )

    # 5) Interactables: required id, no duplicates; if reveals_clue, reference valid clue
    interactables = scene.get("interactables") or []
    seen_interactable_ids: Set[str] = set()
    valid_clue_refs = _valid_clue_refs(scene)

    for idx, i in enumerate(interactables):
        if not isinstance(i, dict):
            issues.append(
                SceneValidationError(
                    f"Invalid scene '{scene_id}': interactable at index {idx} is not a dict",
                    scene_id=str(scene_id),
                    field=f"scene.interactables[{idx}]",
                )
            )
            continue
        iid = str(i.get("id") or "").strip()
        if not iid:
            issues.append(
                SceneValidationError(
                    f"Invalid scene '{scene_id}': interactable at index {idx} is missing required field 'id'",
                    scene_id=str(scene_id),
                    field=f"scene.interactables[{idx}].id",
                )
            )
            continue
        if iid in seen_interactable_ids:
            issues.append(
                SceneValidationError(
                    f"Invalid scene '{scene_id}': duplicate interactable id '{iid}'",
                    scene_id=str(scene_id),
                    field=f"scene.interactables[{idx}].id",
                )
            )
            continue
        seen_interactable_ids.add(iid)

        # If interactable has reveals_clue and type investigate, validate clue reference
        reveals = i.get("reveals_clue")
        if reveals and isinstance(reveals, str) and reveals.strip():
            i_type = (i.get("type") or "").strip().lower()
            if i_type == "investigate" and valid_clue_refs:
                r_slug = slugify(reveals.strip()) or ""
                r_raw = reveals.strip()
                if r_slug not in valid_clue_refs and r_raw not in valid_clue_refs:
                    issues.append(
                        SceneValidationError(
                            f"Invalid scene '{scene_id}': interactable '{iid}' references unknown clue '{reveals.strip()}' (not in discoverable_clues)",
                            scene_id=str(scene_id),
                            field=f"scene.interactables[{idx}].reveals_clue",
                        )
                    )

    return issues


def validate_scene(
    scene_envelope: Dict[str, Any],
    scene_id: str,
    known_scene_ids: Set[str],
) -> None:
    """Validate a single scene. Raises SceneValidationError on failure."""
    issues = collect_scene_validation_issues(scene_envelope, scene_id, known_scene_ids)
    if issues:
        raise issues[0]


def validate_all_scenes(
    scenes_dir: Path,
    list_scene_ids_fn: Any,
) -> None:
    """Load and validate all scene files. Raises on first error."""
    scenes_dir = Path(scenes_dir)
    if not scenes_dir.exists():
        return
    known_ids = set(list_scene_ids_fn())
    seen_ids: Set[str] = set()

    for path in sorted(scenes_dir.glob("*.json")):
        scene_id = path.stem
        if scene_id in seen_ids:
            raise SceneValidationError(
                f"Duplicate scene id '{scene_id}' (multiple files with same stem)",
                scene_id=scene_id,
                field="file",
            )
        seen_ids.add(scene_id)

        # Load raw (avoid storage's default machinery for validation)
        import json
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            raise SceneValidationError(
                f"Scene file is empty: {path}",
                scene_id=scene_id,
                field="file",
            )
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise SceneValidationError(
                f"Invalid JSON in scene file {path}: {e}",
                scene_id=scene_id,
                field="file",
            ) from e

        validate_scene(data, scene_id, known_ids)
