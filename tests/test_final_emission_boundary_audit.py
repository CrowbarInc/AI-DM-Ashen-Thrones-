"""Block A / D static audit hooks for final-emission boundary modules.

``DISALLOWED_BOUNDARY_MUTATION_MARKERS`` is split for Block D:

- **SDK markers** must not appear in ``final_emission_gate.py`` or ``final_emission_repairs.py``
  (comments/docstrings stripped so audit targets executable surface).
- **Gate semantic markers** must not appear in ``final_emission_gate.py`` only. Legacy helpers may
  remain defined in ``final_emission_repairs.py`` (not invoked from the gate).

See: ``docs/final_emission_boundary_audit.md``.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "game" / "final_emission_gate.py"
REPAIRS = REPO_ROOT / "game" / "final_emission_repairs.py"
AUDIT_DOC = REPO_ROOT / "docs" / "final_emission_boundary_audit.md"

_SDK_MARKERS: tuple[str, ...] = (
    "openai.",
    "anthropic.",
    "litellm.",
    "groq.",
    "cohere.",
)

# Final gate must not reintroduce finalize-time semantic repair calls or success flags.
_GATE_BOUNDARY_SEMANTIC_MARKERS: tuple[str, ...] = (
    "apply_social_response_structure_repair(",
    "repair_narrative_authenticity_minimal(",
    "allow_semantic_text_repair=True",
    "referent_repaired = True",
    "social_response_structure_repair_applied = True",
    "narrative_authenticity_repaired = True",
    "narrative_authenticity_repair_applied = True",
    "sentence_micro_smoothing_applied = True",
    "acceptance_quality_repaired = True",
    "synthesize_known_edge_phrase(",
    "reorder_answer_to_front(",
    "reconstruct_narration(",
    "semantic_fallback_composition(",
)

# Backward-compatible name for docs/CI grep: union of both buckets.
DISALLOWED_BOUNDARY_MUTATION_MARKERS: tuple[str, ...] = _SDK_MARKERS + _GATE_BOUNDARY_SEMANTIC_MARKERS


def _docstring_line_numbers(tree: ast.AST) -> set[int]:
    out: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None) or []
        if not body:
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            val = first.value.value
            if isinstance(val, str):
                for ln in range(first.lineno, first.end_lineno + 1):
                    out.add(ln)
    return out


def _source_without_docstrings_and_full_line_comments(source: str) -> str:
    """Remove docstrings and full-line ``#`` comments; keep string literals (code)."""
    tree = ast.parse(source)
    skip_lines = _docstring_line_numbers(tree)
    lines = source.splitlines(keepends=True)
    kept: list[str] = []
    for i, line in enumerate(lines, start=1):
        if i in skip_lines:
            continue
        if line.lstrip().startswith("#"):
            continue
        kept.append(line)
    return "".join(kept)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_audit_document_exists() -> None:
    assert AUDIT_DOC.is_file(), f"missing {AUDIT_DOC}"


def test_audit_document_names_classification_legend() -> None:
    body = _read(AUDIT_DOC)
    for needle in (
        "PACKAGING_ALLOWED",
        "LEGALITY_ALLOWED",
        "SEMANTIC_DISALLOWED",
        "UPSTREAM_OWNER",
        "final_emission_gate.py",
        "final_emission_repairs.py",
    ):
        assert needle in body, f"audit doc should mention {needle!r}"


def test_marker_list_is_documented_in_audit() -> None:
    """Keep the audit doc aligned with the existence of the static marker hook."""
    body = _read(AUDIT_DOC)
    assert "DISALLOWED_BOUNDARY_MUTATION_MARKERS" in body or "test_final_emission_boundary_audit" in body


@pytest.mark.parametrize("marker", _SDK_MARKERS)
def test_sdk_marker_not_in_gate_or_repairs(marker: str) -> None:
    gate = _source_without_docstrings_and_full_line_comments(_read(GATE))
    repairs = _source_without_docstrings_and_full_line_comments(_read(REPAIRS))
    assert marker not in gate, f"{marker!r} leaked into final_emission_gate.py"
    assert marker not in repairs, f"{marker!r} leaked into final_emission_repairs.py"


@pytest.mark.parametrize("marker", _GATE_BOUNDARY_SEMANTIC_MARKERS)
def test_semantic_repair_marker_not_in_final_emission_gate(marker: str) -> None:
    """Regression lock: semantic repair must not creep back into the gate module."""
    gate = _source_without_docstrings_and_full_line_comments(_read(GATE))
    assert marker not in gate, f"{marker!r} must not appear in final_emission_gate.py (active source)"


def test_disallowed_tuple_is_superset_for_doc_alignment() -> None:
    assert set(_SDK_MARKERS) <= set(DISALLOWED_BOUNDARY_MUTATION_MARKERS)
    assert set(_GATE_BOUNDARY_SEMANTIC_MARKERS) <= set(DISALLOWED_BOUNDARY_MUTATION_MARKERS)
