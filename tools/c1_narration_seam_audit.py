"""C1 audit: CTIR → narration plan bundle → prompt_context seam contract (operator-facing).

Run: ``python -m tools.c1_narration_seam_audit`` from the repo root.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
GAME_API = REPO_ROOT / "game" / "api.py"
PROMPT_CONTEXT = REPO_ROOT / "game" / "prompt_context.py"


def _strings_from_ast_expr(expr: ast.AST | None) -> set[str]:
    if expr is None:
        return set()
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return {expr.value}
    if isinstance(expr, ast.IfExp):
        return _strings_from_ast_expr(expr.body) | _strings_from_ast_expr(expr.orelse)
    if isinstance(expr, ast.JoinedStr):
        parts: list[str] = []
        for p in expr.values:
            if isinstance(p, ast.Constant) and isinstance(p.value, str):
                parts.append(p.value)
        return {"".join(parts)} if parts else set()
    return set()


def _extract_path_kind_literals(api_path: Path) -> set[str]:
    text = api_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_annotate = (isinstance(func, ast.Name) and func.id == "annotate_narration_path_kind") or (
            isinstance(func, ast.Attribute) and func.attr == "annotate_narration_path_kind"
        )
        if not is_annotate:
            continue
        for kw in node.keywords:
            if kw.arg != "path_kind" or kw.value is None:
                continue
            found |= _strings_from_ast_expr(kw.value)
    return found


def _prompt_context_interlocutor_recap_guard(pc_text: str) -> list[str]:
    """Ensure local interlocutor-vs-scene recap pair is only emitted when narrative_plan is absent (CTIR branch)."""
    issues: list[str] = []
    needle_a = "Prioritize the active conversation over general scene recap."
    needle_b = (
        "Do not fall back to base scene description unless the location materially changes, "
        "a new threat emerges, the player explicitly surveys the environment, or the scene needs a transition beat."
    )
    if needle_a not in pc_text or needle_b not in pc_text:
        issues.append("prompt_context: expected interlocutor recap instruction pair missing (dialogue-hint contract)")
        return issues
    guard_line = "if has_active_interlocutor and narrative_plan is None"
    if guard_line not in pc_text:
        issues.append(
            "prompt_context: interlocutor recap hints must remain gated on "
            "`has_active_interlocutor and narrative_plan is None`"
        )
    return issues


def run_c1_narration_seam_audit() -> dict[str, Any]:
    from game.narration_seam_guards import (
        NARRATION_PATH_MATRIX,
        REGISTERED_NARRATION_PATH_KINDS,
        path_matrix_markdown,
    )

    issues: list[str] = []
    report_lines: list[str] = ["# C1 narration seam audit", ""]

    matrix_paths = [str(row.get("path") or "") for row in NARRATION_PATH_MATRIX]
    required_substrings = (
        "resolved_turn_ctir_bundle",
        "resolved_turn_ctir_upstream_fast_fallback",
        "chat procedural freeform",
        "manual_play GPT budget exceeded",
        "engine",
    )
    joined = " | ".join(matrix_paths).lower()
    for frag in required_substrings:
        if frag.lower() not in joined:
            issues.append(f"NARRATION_PATH_MATRIX: missing expected coverage fragment {frag!r}")

    report_lines.append("## Path matrix (operator view)")
    report_lines.append(path_matrix_markdown())
    report_lines.append("")

    api_kinds = _extract_path_kind_literals(GAME_API)
    unknown = sorted(api_kinds - set(REGISTERED_NARRATION_PATH_KINDS))
    if unknown:
        issues.append(
            "game.api emits annotate_narration_path_kind path_kind values not in "
            f"REGISTERED_NARRATION_PATH_KINDS: {unknown}"
        )
    report_lines.append("## Registered path_kind literals (game.api)")
    report_lines.append(", ".join(sorted(api_kinds)))
    report_lines.append("")

    issues.extend(_prompt_context_interlocutor_recap_guard(PROMPT_CONTEXT.read_text(encoding="utf-8")))

    # Matrix vs registered kinds: normal resolved-turn row is narrative, not a path_kind string.
    report_lines.append("## Contract summary")
    report_lines.append(
        "- Normal resolved-turn GPT narration: CTIR-backed, bundle-required, plan-driven; "
        "`resolved_turn_ctir_bundle` when no upstream repair exit."
    )
    report_lines.append(
        "- Emergency / repair exits: `resolved_turn_ctir_upstream_fast_fallback`, "
        "`resolved_turn_ctir_force_terminal_fallback`, manual GPT budget cap, upstream repair rows in matrix."
    )
    report_lines.append(
        "- Explicit non-plan model narration: `non_resolution_model_narration` plus debug trace "
        "`explicit_nonplan_model_narration`."
    )
    report_lines.append(
        "- Engine-authored non-GPT paths: `engine_*` path_kind set; matrix rows for checks / combat / adjudication."
    )

    return {"ok": not issues, "issues": issues, "report_markdown": "\n".join(report_lines)}


def _ascii_console_safe(text: str) -> str:
    return text.replace("\u2192", "->")


def main() -> int:
    out = run_c1_narration_seam_audit()
    print(_ascii_console_safe(out["report_markdown"]))
    if out["issues"]:
        print("\n## Issues\n")
        for i in out["issues"]:
            print(_ascii_console_safe(f"- {i}"))
        return 1
    print("\n(no issues)\n")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT))
    raise SystemExit(main())
