"""Static anti-regression audit for Planner Convergence (Block D).

Scans selected runtime modules for patterns that would reintroduce:
  second planners (:func:`build_narrative_plan` outside approved owners),
  unsafe ``prompt_context`` narrative-plan shipment / raw shortcuts,
  manual-play paths that skip convergence instrumentation,
  and emergency player-facing output without seam registration.

Run from repo root::

    python tools/planner_convergence_audit.py

Rules use path names, AST shape, and allowlisted markers — not hard-coded
production line numbers. When a raw-state read in ``prompt_context`` is
intentionally presentation-only, tag the line with::

    # planner_convergence_presentation_only

See ``docs/planner_convergence.md``.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# --- Allowlists (contract mirrors ``game.planner_convergence`` + Block C projection) ---

# Callers permitted to invoke ``build_narrative_plan`` (single planner seam).
APPROVED_BUILD_NARRATIVE_PLAN_OWNER_PATHS: frozenset[str] = frozenset(
    {
        "game/narrative_planning.py",
        "game/narrative_plan_upstream.py",
        "game/narration_plan_bundle.py",
    }
)

# Top-level ``narrative_plan`` keys allowed in the model prompt (must stay aligned
# with ``public_narrative_plan_projection_for_prompt`` in ``game/narration_plan_bundle``).
APPROVED_PROMPT_NARRATIVE_PLAN_TOP_KEYS: frozenset[str] = frozenset(
    {
        "version",
        "narrative_mode",
        "role_allocation",
        "scene_anchors",
        "active_pressures",
        "required_new_information",
        "allowable_entity_references",
        "narrative_roles",
        "narrative_mode_contract",
    }
)

# Primary modules scanned every run (plus ``_discover_opening_scene_modules``).
PRIMARY_AUDIT_REL_PATHS: tuple[str, ...] = (
    "game/api.py",
    "game/gm.py",
    "game/prompt_context.py",
    "game/narration_plan_bundle.py",
    "game/narrative_plan_upstream.py",
    "game/narrative_planning.py",
    "game/final_emission_gate.py",
    "game/narration_seam_guards.py",
)


def _discover_opening_scene_modules() -> list[str]:
    """Opening / scene-adjacent helpers that may ship narration-shaped payloads."""
    game = REPO_ROOT / "game"
    if not game.is_dir():
        return []
    names: set[str] = set()
    for p in game.glob("opening*.py"):
        try:
            rel = p.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            continue
        names.add(rel)
    return sorted(names)


def _rel_posix(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def _is_build_narrative_plan_call(node: ast.Call) -> bool:
    f = node.func
    if isinstance(f, ast.Name) and f.id == "build_narrative_plan":
        return True
    if isinstance(f, ast.Attribute) and f.attr == "build_narrative_plan":
        return True
    return False


def _find_build_narrative_plan_calls(tree: ast.AST) -> list[tuple[int, int]]:
    hits: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_build_narrative_plan_call(node):
            hits.append((node.lineno, node.col_offset or 0))
    return hits


def audit_build_narrative_plan_call_sites(rel_path: str, source: str) -> list[str]:
    """Flag ``build_narrative_plan`` invocations outside approved owner modules."""
    issues: list[str] = []
    if rel_path not in APPROVED_BUILD_NARRATIVE_PLAN_OWNER_PATHS:
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return [f"{rel_path}: syntax error ({e.msg}) at line {e.lineno}"]
        for ln, _co in _find_build_narrative_plan_calls(tree):
            issues.append(
                f"{rel_path}:{ln}: build_narrative_plan(...) call outside approved owners "
                f"{sorted(APPROVED_BUILD_NARRATIVE_PLAN_OWNER_PATHS)} — use bundle/upstream instead."
            )
    return issues


def _is_public_projection_call(node: ast.AST) -> bool:
    if isinstance(node, ast.IfExp):
        return _is_public_projection_call(node.body) and _is_public_projection_call(node.orelse)
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name) and f.id == "public_narrative_plan_projection_for_prompt":
            return True
        if isinstance(f, ast.Attribute) and f.attr == "public_narrative_plan_projection_for_prompt":
            return True
    if isinstance(node, ast.Constant) and node.value is None:
        return True
    return False


def _dict_key_str(k: ast.expr) -> str | None:
    if isinstance(k, ast.Constant) and isinstance(k.value, str):
        return k.value
    return None


def _audit_prompt_context_top_level_narrative_plan_entries(
    rel_path: str, tree: ast.Module
) -> list[str]:
    """Ensure the **model payload** ``payload['narrative_plan']`` uses only the public projection.

    Nested dicts (e.g. ``prompt_debug_anchor['narrative_plan']``) intentionally use the debug
    mirror helper and must be ignored here.
    """
    issues: list[str] = []
    if rel_path != "game/prompt_context.py":
        return issues
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef) or fn.name != "build_narration_context":
            continue
        for node in fn.body:
            payload_dict: ast.Dict | None = None
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == "payload" and isinstance(node.value, ast.Dict):
                    payload_dict = node.value
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "payload" and isinstance(node.value, ast.Dict):
                        payload_dict = node.value
                        break
            if payload_dict is None:
                continue
            for i, key in enumerate(payload_dict.keys):
                if key is None:
                    continue
                if _dict_key_str(key) != "narrative_plan":
                    continue
                val = payload_dict.values[i]
                if val is None:
                    continue
                if not _is_public_projection_call(val):
                    issues.append(
                        f"{rel_path}:{getattr(val, 'lineno', payload_dict.lineno)}: "
                        "payload['narrative_plan'] must ship only "
                        "public_narrative_plan_projection_for_prompt(...) (if/else to None) — "
                        "not a raw plan dict or alternate assembly."
                    )
    return issues


def _audit_prompt_context_local_narrative_plan_dicts(rel_path: str, tree: ast.Module) -> list[str]:
    """Flag inline ``{{ ... }}`` narrative_plan-shaped dict assembly inside ``build_narration_context``."""
    issues: list[str] = []
    if rel_path != "game/prompt_context.py":
        return issues
    plan_shape_keys = {"narrative_mode", "scene_anchors", "narrative_mode_contract", "narrative_roles"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "build_narration_context":
            continue
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Dict):
                continue
            keys: set[str] = set()
            for k in sub.keys:
                s = _dict_key_str(k) if k is not None else None
                if s:
                    keys.add(s)
            if len(keys & plan_shape_keys) >= 2 and "narrative_plan" not in keys:
                issues.append(
                    f"{rel_path}:{sub.lineno}: local dict resembles narrative_plan assembly "
                    "(multiple structural keys) inside build_narration_context — use bundle + "
                    "public_narrative_plan_projection_for_prompt only."
                )
    return issues


_RAW_STATE_RE = re.compile(
    r"\b(world|session|scene|combat)\s*\.\s*(get|\[)",
    re.MULTILINE,
)


def audit_prompt_context_raw_semantic_shortcuts(rel_path: str, source: str) -> list[str]:
    """Heuristic: raw engine containers + narrative_plan on same line without presentation marker.

    Legitimate formatting reads should carry ``# planner_convergence_presentation_only`` on the same line.
    """
    issues: list[str] = []
    if rel_path != "game/prompt_context.py":
        return issues
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return issues
    fn_ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "build_narration_context":
            end = getattr(node, "end_lineno", None) or node.lineno
            fn_ranges.append((node.lineno, end))
    if not fn_ranges:
        return [f"{rel_path}: build_narration_context not found (cannot scope raw-state scan)"]
    lines = source.splitlines()
    for start, end in fn_ranges:
        for i in range(max(1, start) - 1, min(len(lines), end)):
            line = lines[i]
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if "planner_convergence_presentation_only" in line:
                continue
            if "narrative_plan" not in line:
                continue
            if not _RAW_STATE_RE.search(line):
                continue
            issues.append(
                f"{rel_path}:{i + 1}: possible raw-state -> narrative_plan semantic shortcut "
                "(world/session/scene/combat access on same line as narrative_plan). "
                "Mark presentation-only lines with: # planner_convergence_presentation_only"
            )
    return issues


def _collect_projection_out_keys_from_bundle_ast(tree: ast.Module) -> set[str]:
    keys: set[str] = set()
    target_fn: ast.FunctionDef | None = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "public_narrative_plan_projection_for_prompt":
            target_fn = node
            break
    if target_fn is None:
        return keys
    for sub in ast.walk(target_fn):
        if isinstance(sub, ast.Assign):
            for t in sub.targets:
                if isinstance(t, ast.Subscript):
                    if isinstance(t.value, ast.Name) and t.value.id == "out":
                        sl = t.slice
                        if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                            keys.add(sl.value)
        if isinstance(sub, ast.For):
            if isinstance(sub.iter, ast.Tuple):
                for elt in sub.iter.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        keys.add(elt.value)
    return keys


def audit_narration_plan_bundle_projection_keys(rel_path: str, source: str) -> list[str]:
    """Ensure ``public_narrative_plan_projection_for_prompt`` only emits approved top-level keys."""
    issues: list[str] = []
    if rel_path != "game/narration_plan_bundle.py":
        return issues
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"{rel_path}: syntax error ({e.msg}) at line {e.lineno}"]
    emitted = _collect_projection_out_keys_from_bundle_ast(tree)
    extra = emitted - APPROVED_PROMPT_NARRATIVE_PLAN_TOP_KEYS
    missing = APPROVED_PROMPT_NARRATIVE_PLAN_TOP_KEYS - emitted
    if extra:
        issues.append(
            f"{rel_path}: public_narrative_plan_projection_for_prompt emits unknown keys {sorted(extra)} — "
            f"update APPROVED_PROMPT_NARRATIVE_PLAN_TOP_KEYS in tools/planner_convergence_audit.py and docs."
        )
    if missing:
        issues.append(
            f"{rel_path}: public_narrative_plan_projection_for_prompt appears missing keys {sorted(missing)} vs audit contract."
        )
    return issues


def _slice_function_source(source: str, name: str) -> str | None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            lines = source.splitlines()
            end = getattr(node, "end_lineno", None) or node.lineno
            return "\n".join(lines[node.lineno - 1 : end])
    return None


def audit_api_manual_play_convergence_structure(rel_path: str, source: str) -> list[str]:
    """Structural checks on ``game.api`` manual-play narration: pre/post convergence + seam labels."""
    issues: list[str] = []
    if rel_path != "game/api.py":
        return issues
    if "resolved_turn_ctir_planner_convergence_seam" not in source:
        issues.append(f"{rel_path}: missing resolved_turn_ctir_planner_convergence_seam annotation")
    if 'path_kind="resolved_turn_ctir_planner_convergence_seam"' not in source and (
        "path_kind='resolved_turn_ctir_planner_convergence_seam'" not in source
    ):
        issues.append(f"{rel_path}: missing annotate_narration_path_kind planner convergence seam path_kind literal")
    seam = _slice_function_source(source, "_gm_planner_convergence_seam_terminal")
    if seam is None:
        issues.append(f"{rel_path}: missing _gm_planner_convergence_seam_terminal")
    elif "record_emergency_nonplan_output" not in seam:
        issues.append(
            f"{rel_path}: _gm_planner_convergence_seam_terminal must call record_emergency_nonplan_output "
            "(Block B emergency registration)"
        )
    try:
        pre_i = source.index("pre_planner_report = build_planner_convergence_report")
        bm_i = source.index("messages = build_messages(")
        if pre_i > bm_i:
            issues.append(
                f"{rel_path}: pre_prompt build_planner_convergence_report must appear before build_messages("
            )
    except ValueError:
        issues.append(f"{rel_path}: expected pre_prompt convergence + build_messages markers missing")
    # Guard is on the *call site* ``guard_gm_output(_bounded_call_gpt(messages), ...)``, not the
    # nested helper ``def _bounded_call_gpt`` (which appears earlier in the same outer function).
    if not re.search(
        r"if\s+gm\s+is\s+None\s*:\s*(?:[^\n]*\n)*?\s*gm\s*=\s*guard_gm_output\s*\(\s*\n\s*_bounded_call_gpt\s*\(\s*messages\s*\)",
        source,
        re.MULTILINE,
    ):
        issues.append(
            f"{rel_path}: primary GPT path must wrap _bounded_call_gpt(messages) in "
            "`if gm is None:` + guard_gm_output (convergence seam pre-sets gm to skip GPT)"
        )
    if "post_planner_report = build_planner_convergence_report" not in source:
        issues.append(f"{rel_path}: missing post-prompt build_planner_convergence_report (prompt_payload check)")
    if "if not planner_convergence_ok(post_planner_report)" not in source:
        issues.append(f"{rel_path}: missing post-prompt planner_convergence_ok gate")
    return issues


def _is_call_to(node: ast.Call, name: str) -> bool:
    f = node.func
    if isinstance(f, ast.Name) and f.id == name:
        return True
    if isinstance(f, ast.Attribute) and f.attr == name:
        return True
    return False


def _assigns_player_facing_text(node: ast.AST) -> bool:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Subscript):
                if isinstance(t.slice, ast.Constant) and t.slice.value == "player_facing_text":
                    return True
            if isinstance(t, ast.Attribute) and t.attr == "player_facing_text":
                return True
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Subscript):
        if isinstance(node.target.slice, ast.Constant) and node.target.slice.value == "player_facing_text":
            return True
    return False


def audit_emergency_player_facing_functions(source: str, *, rel_path: str = "synthetic_emergency_fixture.py") -> list[str]:
    """For small synthetic modules: any function that assigns player_facing_text must register emergency output.

    Registration = call to ``record_emergency_nonplan_output`` anywhere in the same function body.
    """
    issues: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"{rel_path}: syntax error ({e.msg}) at line {e.lineno}"]
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        assigns = any(_assigns_player_facing_text(n) for n in ast.walk(node))
        if not assigns:
            continue
        records = any(isinstance(n, ast.Call) and _is_call_to(n, "record_emergency_nonplan_output") for n in ast.walk(node))
        if not records:
            issues.append(
                f"{rel_path}:{node.lineno}: function {node.name!r} assigns player_facing_text without "
                "record_emergency_nonplan_output in the same function (nonplan emergency must register)"
            )
    return issues


def audit_file(rel_path: str, *, source: str | None = None, repo_root: Path | None = None) -> list[str]:
    """Run all rules applicable to one repo-relative POSIX path."""
    root = repo_root or REPO_ROOT
    path = root / Path(rel_path)
    text = source if source is not None else path.read_text(encoding="utf-8")
    issues: list[str] = []
    issues.extend(audit_build_narrative_plan_call_sites(rel_path, text))
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return issues + [f"{rel_path}: syntax error ({e.msg}) at line {e.lineno}"]
    if isinstance(tree, ast.Module):
        issues.extend(_audit_prompt_context_top_level_narrative_plan_entries(rel_path, tree))
        issues.extend(_audit_prompt_context_local_narrative_plan_dicts(rel_path, tree))
    issues.extend(audit_prompt_context_raw_semantic_shortcuts(rel_path, text))
    issues.extend(audit_narration_plan_bundle_projection_keys(rel_path, text))
    issues.extend(audit_api_manual_play_convergence_structure(rel_path, text))
    return issues


def run_planner_convergence_audit(*, repo_root: Path | None = None) -> tuple[bool, list[str]]:
    """Audit primary game modules + opening helpers. Returns (ok, issues)."""
    root = repo_root or REPO_ROOT
    rels = list(dict.fromkeys([*PRIMARY_AUDIT_REL_PATHS, *_discover_opening_scene_modules()]))
    issues: list[str] = []
    for rel in rels:
        p = root / Path(rel)
        if not p.is_file():
            issues.append(f"missing audit target: {rel}")
            continue
        issues.extend(audit_file(rel, repo_root=root))
    return (len(issues) == 0, issues)


def main() -> int:
    ok, issues = run_planner_convergence_audit()
    if ok:
        print("planner_convergence_audit: OK (no issues)")
        return 0
    print("planner_convergence_audit: FAILED\n")
    for msg in issues:
        print(f"- {msg}")
    return 1


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT))
    raise SystemExit(main())
