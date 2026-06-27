"""BV16C terminal monkeypatch guards (import-light; no pytest).

Tests must monkeypatch finalize-tail owner modules, not ``terminal_pipeline`` delegate
symbols. Enforced by ``test_bv16c_ownership_registry_terminal_pipeline_delegate_monkeypatch_governance``
in ``tests/test_compat_import_governance.py``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Cycle BV16C — tests must monkeypatch finalize-tail owner modules, not terminal_pipeline namespace.
BV16C_TERMINAL_PIPELINE_MODULE: Final[str] = "game.final_emission_terminal_pipeline"
BV16C_VISIBILITY_OWNER: Final[str] = "game.final_emission_visibility_fallback"
BV16C_N4_OWNER: Final[str] = "game.final_emission_acceptance_quality"
BV16C_IC_OWNER: Final[str] = "game.interaction_continuity"
BV16C_OPENING_OWNER: Final[str] = "game.final_emission_opening_fallback"
BV16C_REPAIRS_OWNER: Final[str] = "game.final_emission_repairs"
BV16C_TERMINAL_ORCHESTRATION_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "run_gate_terminal_enforcement_pipeline",
        "apply_strict_social_emergency_fallback_patch",
        "GateTerminalEnforcementProfile",
        "_apply_referent_clarity_pre_finalize",
        "_patch_fem_text_fingerprint",
    }
)
BV16C_FORBIDDEN_TERMINAL_DELEGATE_MONKEYPATCH_MARKERS: Final[tuple[str, ...]] = (
    'monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement"',
    'monkeypatch.setattr(terminal_pipeline, "apply_acceptance_quality_n4_floor_seam"',
    'monkeypatch.setattr(terminal_pipeline, "attach_interaction_continuity_validation"',
    'monkeypatch.setattr(terminal_pipeline, "apply_interaction_continuity_emission_step"',
    'monkeypatch.setattr(terminal_pipeline, "_apply_fallback_behavior_layer"',
    "terminal_pipeline.apply_visibility_enforcement",
    "terminal_pipeline.apply_acceptance_quality_n4_floor_seam",
    "terminal_pipeline.attach_interaction_continuity_validation",
    "terminal_pipeline.apply_interaction_continuity_emission_step",
    "terminal_pipeline._apply_fallback_behavior_layer",
)
BV16C_TERMINAL_MONKEYPATCH_SCAN_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "tests/test_compat_import_governance.py",
        "tests/ownership_guard_bv16c_terminal_monkeypatch.py",
        "tools/bv16c_migrate_monkeypatches.py",
        "tools/bv16_generate_audit_docs.py",
    }
)
BV16C_TERMINAL_MONKEYPATCH_SCAN_ROOTS: Final[tuple[str, ...]] = ("tests",)


def _normalize_test_rel_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def collect_bv16c_terminal_delegate_monkeypatch_violations(
    rel_path: str,
    source: str,
    *,
    allowlist: frozenset[str] | None = None,
    forbidden_markers: tuple[str, ...] | None = None,
) -> list[str]:
    """Return violations when tests monkeypatch terminal_pipeline delegate symbols (BV16C)."""
    norm = _normalize_test_rel_path(rel_path)
    allowed = BV16C_TERMINAL_MONKEYPATCH_SCAN_ALLOWLIST if allowlist is None else allowlist
    if norm in allowed:
        return []
    markers = (
        BV16C_FORBIDDEN_TERMINAL_DELEGATE_MONKEYPATCH_MARKERS
        if forbidden_markers is None
        else forbidden_markers
    )
    violations: list[str] = []
    for marker in markers:
        if marker in source:
            violations.append(
                f"{norm}: forbidden terminal_pipeline delegate monkeypatch {marker!r} "
                f"(patch owner module: visibility_fallback / acceptance_quality / interaction_continuity / emission_repairs)",
            )
    return violations


def iter_bv16c_terminal_monkeypatch_scan_paths(
    repo_root: Path | None = None,
    *,
    scan_roots: tuple[str, ...] = BV16C_TERMINAL_MONKEYPATCH_SCAN_ROOTS,
) -> tuple[str, ...]:
    root = _REPO_ROOT if repo_root is None else repo_root
    paths: list[str] = []
    for scan_root in scan_roots:
        base = root / scan_root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            rel = _normalize_test_rel_path(path.relative_to(root))
            if rel in BV16C_TERMINAL_MONKEYPATCH_SCAN_ALLOWLIST:
                continue
            paths.append(rel)
    return tuple(paths)
