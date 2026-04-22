"""Deterministic author-time content lint (Objective #10).

Composes strict scene validation, heuristic scene lint, clue/schema checks, and graph
analysis into a single structured report. Not used on the gameplay hot path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional, Set

from game import scene_graph
from game import scene_lint
from game import validation
from game.schema_contracts import adapt_legacy_clue, validate_clue
from game.utils import slugify

Severity = Literal["error", "warning"]


@dataclass
class ContentLintMessage:
    """One finding from the content lint pipeline (dict-serializable)."""

    severity: Severity
    code: str
    message: str
    scene_id: Optional[str] = None
    path: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.scene_id is not None:
            d["scene_id"] = self.scene_id
        if self.path is not None:
            d["path"] = self.path
        if self.evidence is not None:
            d["evidence"] = self.evidence
        return d


@dataclass
class ContentLintReport:
    ok: bool
    error_count: int
    warning_count: int
    messages: List[ContentLintMessage] = field(default_factory=list)
    scene_ids_checked: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "messages": [m.as_dict() for m in self.messages],
            "scene_ids_checked": list(self.scene_ids_checked),
        }


def _norm(s: str) -> str:
    return " ".join(str(s or "").lower().split())


def _scene_inner(envelope: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(envelope, dict):
        return {}
    inner = envelope.get("scene")
    return inner if isinstance(inner, dict) else {}


def _valid_clue_refs_extended(
    scene: Dict[str, Any],
    world: Optional[Dict[str, Any]],
) -> Set[str]:
    """Clue refs accepted for interactable ``reveals_clue`` (discoverable_clues + optional world.clues)."""
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
    if world and isinstance(world.get("clues"), dict):
        for k in world["clues"]:
            if isinstance(k, str) and k.strip():
                ks = k.strip()
                refs.add(ks)
                refs.add(slugify(ks) or "")
    return refs


def _validation_issue_to_message(err: validation.SceneValidationError) -> ContentLintMessage:
    """Map strict validation issues to stable codes (mirrors :mod:`game.validation` rules)."""
    scene_id = str(err.scene_id or "")
    fld = str(err.field or "")
    msg = str(err)
    msg_l = msg.lower()

    if fld == "scene":
        code = "scene.missing_root"
    elif fld == "scene.id":
        if "missing" in msg_l or "empty" in msg_l:
            code = "scene.id.missing"
        else:
            code = "scene.id.mismatch"
    elif fld == "scene.location":
        code = "scene.missing_required_field"
    elif fld == "scene.summary":
        code = "scene.missing_required_field"
    elif "duplicate affordance action id" in msg_l:
        code = "action.duplicate_id"
    elif "exits" in fld and "target_scene_id" in fld:
        code = "exit.unknown_target"
    elif "actions" in fld and ("targetsceneid" in msg_l or "target_scene_id" in msg_l):
        code = "action.unknown_target_scene"
    elif "interactables" in fld and "not a dict" in msg_l:
        code = "interactable.invalid_shape"
    elif "interactables" in fld and "missing required field 'id'" in msg:
        code = "interactable.missing_id"
    elif "duplicate interactable" in msg_l:
        code = "interactable.duplicate_id"
    elif "references unknown clue" in msg_l:
        code = "interactable.unknown_clue_ref"
    else:
        code = "scene.validation"

    evidence: Dict[str, Any] = {"validation_field": fld}
    if code == "scene.missing_required_field":
        evidence["field"] = "location" if "location" in msg_l else "summary"

    return ContentLintMessage(
        severity="error",
        code=code,
        message=msg,
        scene_id=scene_id or None,
        path=fld or None,
        evidence=evidence,
    )


def lint_scene_structure(
    scene_envelope: Dict[str, Any],
    scene_id: str,
    known_scene_ids: Set[str],
) -> List[ContentLintMessage]:
    """Envelope + id + required fields (strict rules from :mod:`game.validation`)."""
    issues = validation.collect_scene_validation_issues(scene_envelope, scene_id, known_scene_ids)
    out: List[ContentLintMessage] = []
    for err in issues:
        m = _validation_issue_to_message(err)
        if m.code in (
            "scene.missing_root",
            "scene.id.missing",
            "scene.id.mismatch",
            "scene.missing_required_field",
        ):
            out.append(m)
    return out


def lint_scene_exits(
    scene_envelope: Dict[str, Any],
    scene_id: str,
    known_scene_ids: Set[str],
) -> List[ContentLintMessage]:
    """Exit targets, affordance transition targets, and duplicate affordance ids (strict)."""
    issues = validation.collect_scene_validation_issues(scene_envelope, scene_id, known_scene_ids)
    codes = ("exit.unknown_target", "action.unknown_target_scene", "action.duplicate_id")
    return [m for err in issues if (m := _validation_issue_to_message(err)).code in codes]


def lint_scene_interactables(
    scene_envelope: Dict[str, Any],
    scene_id: str,
    known_scene_ids: Set[str],
) -> List[ContentLintMessage]:
    """Interactable shape, ids, duplicates, runtime-strict clue refs on investigate."""
    issues = validation.collect_scene_validation_issues(scene_envelope, scene_id, known_scene_ids)
    codes = {
        "interactable.invalid_shape",
        "interactable.missing_id",
        "interactable.duplicate_id",
        "interactable.unknown_clue_ref",
    }
    return [m for err in issues if (m := _validation_issue_to_message(err)).code in codes]


def lint_scene_clue_integrity(
    scene_envelope: Dict[str, Any],
    scene_id: str,
    *,
    world: Optional[Dict[str, Any]] = None,
) -> List[ContentLintMessage]:
    """Structured clue ids, schema, overlap with hidden facts; author-only clue ref warnings."""
    out: List[ContentLintMessage] = []
    inner = _scene_inner(scene_envelope)
    if not inner:
        return out

    discoverable = inner.get("discoverable_clues") or []
    hidden = [str(v) for v in (inner.get("hidden_facts") or [])]
    norm_hidden = [_norm(v) for v in hidden]

    # Duplicate structured clue ids within the scene
    seen_clue_ids: Set[str] = set()
    for idx, raw in enumerate(discoverable):
        if not isinstance(raw, dict):
            continue
        cid = str(raw.get("id") or "").strip()
        if not cid:
            continue
        if cid in seen_clue_ids:
            out.append(
                ContentLintMessage(
                    severity="error",
                    code="clue.duplicate_id",
                    message=f"Duplicate discoverable_clues id '{cid}' in scene '{scene_id}'",
                    scene_id=scene_id,
                    path=f"scene.discoverable_clues[{idx}].id",
                    evidence={"clue_id": cid},
                )
            )
            continue
        seen_clue_ids.add(cid)

        adapted = adapt_legacy_clue(raw)
        ok, reasons = validate_clue(adapted)
        if not ok:
            out.append(
                ContentLintMessage(
                    severity="error",
                    code="clue.schema_invalid",
                    message=f"Invalid structured clue at index {idx} in scene '{scene_id}'",
                    scene_id=scene_id,
                    path=f"scene.discoverable_clues[{idx}]",
                    evidence={"reasons": list(reasons)},
                )
            )

    # Discoverable text contains hidden fact substring (deterministic; aligns with scene_lint heuristic)
    disc_texts: List[tuple[int, str, str]] = []
    for idx, raw in enumerate(discoverable):
        if isinstance(raw, str) and raw.strip():
            t = raw.strip()
            disc_texts.append((idx, t, _norm(t)))
        elif isinstance(raw, dict):
            t = raw.get("text")
            if isinstance(t, str) and t.strip():
                ts = t.strip()
                disc_texts.append((idx, ts, _norm(ts)))

    for idx, d_txt, d_norm in disc_texts:
        for h_norm in norm_hidden:
            if h_norm and h_norm in d_norm:
                out.append(
                    ContentLintMessage(
                        severity="warning",
                        code="clue.overlaps_hidden_fact",
                        message=f"Discoverable clue may directly mirror a hidden fact in scene '{scene_id}'",
                        scene_id=scene_id,
                        path=f"scene.discoverable_clues[{idx}]",
                        evidence={"discoverable": d_txt, "hidden_norm": h_norm},
                    )
                )
                break

    # Author-only: reveals_clue with clues present but non-investigate type and unresolved ref
    valid_refs = _valid_clue_refs_extended(inner, world)
    interactables = inner.get("interactables") or []
    for idx, i in enumerate(interactables):
        if not isinstance(i, dict):
            continue
        iid = str(i.get("id") or "interactable").strip()
        reveals = i.get("reveals_clue")
        if not reveals or not isinstance(reveals, str) or not reveals.strip():
            continue
        if not valid_refs:
            continue
        i_type = (i.get("type") or "").strip().lower()
        if i_type == "investigate":
            continue
        r_raw = reveals.strip()
        r_slug = slugify(r_raw) or ""
        if r_slug in valid_refs or r_raw in valid_refs:
            continue
        out.append(
            ContentLintMessage(
                severity="warning",
                code="interactable.clue_ref_non_investigate",
                message=(
                    f"Interactable '{iid}' has reveals_clue that does not resolve to a known clue "
                    f"(non-investigate types are not validated at runtime) in scene '{scene_id}'"
                ),
                scene_id=scene_id,
                path=f"scene.interactables[{idx}].reveals_clue",
                evidence={"interactable_id": iid, "reveals_clue": r_raw, "type": i_type or None},
            )
        )

    return out


def lint_scene_heuristic_warnings(
    scene_envelope: Dict[str, Any],
    scene_id: str,
    known_scene_ids: Set[str],
) -> List[ContentLintMessage]:
    """Translate :mod:`game.scene_lint` warnings into canonical codes (errors are covered by strict validation)."""
    raw = scene_lint.validate_scene(scene_envelope, known_scene_ids)
    inner = _scene_inner(scene_envelope)
    sid = str(inner.get("id") or scene_id or "<unknown>")
    out: List[ContentLintMessage] = []

    for w in raw.get("warnings") or []:
        wlow = str(w).lower()
        if "very similar to a visible fact" in wlow and "discoverable" in wlow:
            code = "clue.similar_to_visible"
        elif "very similar to a visible fact" in wlow and "hidden" in wlow:
            code = "hidden.similar_to_visible"
        elif "may directly state a hidden fact" in wlow:
            code = "clue.overlaps_hidden_fact"
        elif "no visible facts and no exits" in wlow:
            code = "scene.missing_player_anchor"
        elif "sensory grounding" in wlow:
            code = "scene.missing_sensory_grounding"
        else:
            code = "scene.heuristic_warning"
        out.append(
            ContentLintMessage(
                severity="warning",
                code=code,
                message=str(w),
                scene_id=sid if sid != "<unknown>" else str(scene_id),
                evidence={"source": "scene_lint"},
            )
        )

    # Dedupe clue.overlaps_hidden_fact if already emitted by clue pass (same scene)
    # Caller merges messages; optional dedupe in merge_report

    return out


def lint_scene_graph_connectivity(
    *,
    known_scene_ids: Set[str],
    load_scene_fn: Callable[[str], Dict[str, Any]],
    graph_seed_scene_ids: Optional[List[str]] = None,
) -> List[ContentLintMessage]:
    """Graph build, load/orphan hints, optional unreachable warnings (multi-scene aggregation)."""

    def _list_ids() -> List[str]:
        return sorted(known_scene_ids)

    messages: List[ContentLintMessage] = []

    graph = scene_graph.build_scene_graph(_list_ids, load_scene_fn)

    for sid in sorted(known_scene_ids):
        try:
            env = load_scene_fn(sid)
        except Exception as exc:  # noqa: BLE001 — author tooling surfaces load failures
            messages.append(
                ContentLintMessage(
                    severity="warning",
                    code="graph.scene_load_failed",
                    message=f"Could not load scene '{sid}' while building graph: {exc}",
                    scene_id=sid,
                    path="graph",
                    evidence={"error": str(exc)},
                )
            )
            continue
        inner = _scene_inner(env)
        if not inner:
            messages.append(
                ContentLintMessage(
                    severity="warning",
                    code="graph.missing_scene_body",
                    message=f"Scene '{sid}' envelope has no usable inner 'scene' for graph",
                    scene_id=sid,
                    path="scene",
                )
            )
            continue

    # Unreachable scenes from seeds (warning-only)
    seeds: List[str] = []
    if graph_seed_scene_ids is not None:
        seeds = [str(s).strip() for s in graph_seed_scene_ids if str(s).strip() in known_scene_ids]
    elif known_scene_ids:
        seeds = [sorted(known_scene_ids)[0]]

    if seeds:
        reachable: Set[str] = set()
        stack = list(seeds)
        while stack:
            cur = stack.pop()
            if cur in reachable:
                continue
            reachable.add(cur)
            for nxt in graph.get(cur, set()):
                if nxt not in reachable:
                    stack.append(nxt)
        for sid in sorted(known_scene_ids):
            if sid not in reachable:
                messages.append(
                    ContentLintMessage(
                        severity="warning",
                        code="graph.unreachable_scene",
                        message=f"Scene '{sid}' is not reachable from graph seeds {seeds!r}",
                        scene_id=sid,
                        path="graph",
                        evidence={"seeds": list(seeds)},
                    )
                )

    return messages


def _merge_messages(parts: List[List[ContentLintMessage]]) -> List[ContentLintMessage]:
    """Stable merge with dedupe on (severity, code, scene_id, path, message)."""
    seen: Set[tuple[Any, ...]] = set()
    out: List[ContentLintMessage] = []
    for group in parts:
        for m in group:
            key = (m.severity, m.code, m.scene_id, m.path, m.message)
            if key in seen:
                continue
            seen.add(key)
            out.append(m)
    return out


def lint_all_content(
    scenes: Dict[str, Dict[str, Any]],
    *,
    world: Optional[Dict[str, Any]] = None,
    graph_seed_scene_ids: Optional[List[str]] = None,
    reference_known_scene_ids: Optional[Set[str]] = None,
    graph_known_scene_ids: Optional[Set[str]] = None,
) -> ContentLintReport:
    """Run all passes over an in-memory scene map (scene_id -> envelope).

    ``reference_known_scene_ids`` — when set, used as the known scene registry for strict
    validation and heuristics (exit/action targets, duplicate stems on disk, etc.) while
    still only running per-scene passes for keys present in ``scenes``. When omitted,
    defaults to ``set(scenes.keys())`` (single full-map run).

    ``graph_known_scene_ids`` — universe of scene ids for the graph/reachability pass only.
    When omitted, defaults to ``reference_known`` (same registry as validation). For
    subset linting, pass ``set(scenes.keys())`` so reachability is evaluated **only among
    loaded scenes**; otherwise unreachable warnings would spuriously flag scenes that were
    never loaded into ``scenes``.
    """
    reference_known = set(reference_known_scene_ids) if reference_known_scene_ids is not None else set(scenes.keys())
    graph_known = set(graph_known_scene_ids) if graph_known_scene_ids is not None else set(reference_known)
    scene_ids_checked = sorted(scenes.keys())
    all_parts: List[List[ContentLintMessage]] = []

    for sid in scene_ids_checked:
        env = scenes[sid]
        issues = validation.collect_scene_validation_issues(env, sid, reference_known)
        all_parts.append([_validation_issue_to_message(e) for e in issues])
        all_parts.append(lint_scene_clue_integrity(env, sid, world=world))
        all_parts.append(lint_scene_heuristic_warnings(env, sid, reference_known))

    def _load(s: str) -> Dict[str, Any]:
        if s not in scenes:
            return {}
        return scenes[s]

    all_parts.append(
        lint_scene_graph_connectivity(
            known_scene_ids=graph_known,
            load_scene_fn=_load,
            graph_seed_scene_ids=graph_seed_scene_ids,
        )
    )

    messages = _merge_messages(all_parts)
    err = sum(1 for m in messages if m.severity == "error")
    warn = sum(1 for m in messages if m.severity == "warning")
    return ContentLintReport(
        ok=err == 0,
        error_count=err,
        warning_count=warn,
        messages=messages,
        scene_ids_checked=scene_ids_checked,
    )
