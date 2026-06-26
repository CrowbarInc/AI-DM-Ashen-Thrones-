"""BA-7 / AG-10 gate magnet guards (import-light; no pytest).

Gate-layer direct-owner suites must not import replay/dashboard/classifier read-side
projection helpers or accumulate read-side projection assertion creep. Enforced by
``test_ba7_*`` and ``test_final_emission_gate_does_not_accumulate_*`` in
``tests/test_ownership_registry.py``.
"""
from __future__ import annotations

import ast
from typing import Final, Mapping

from tests.ownership_registry_contract import RESPONSIBILITY_REGISTRY, ResponsibilityRecord

# Cycle BA-7 / AG-10: gate orchestration direct owners must not import replay/dashboard/classifier
# read-side projection helpers (FEM meta projection + gauntlet/classifier neighbors are excluded).
_GATE_MAGNET_GUARD_EXCLUDED_GROUP_IDS: Final[frozenset[str]] = frozenset(
    {
        "final_emission_meta_projection",
        "gauntlet_playability_validation",
    }
)
_GATE_MAGNET_GUARD_EXCLUDED_PATHS: Final[frozenset[str]] = frozenset(
    {
        "tests/test_failure_classifier.py",
        "tests/test_failure_classification_contract.py",
        "tests/test_failure_dashboard_controlled_failures.py",
        "tests/test_golden_replay.py",
    }
)
_FORBIDDEN_REPLAY_READ_SIDE_IMPORT_PREFIXES: Final[tuple[str, ...]] = (
    "tests.helpers.golden_replay_projection",
    "tests.helpers.golden_replay",
    "tests.helpers.failure_classifier",
    "tests.helpers.failure_dashboard_report",
    "tests.helpers.failure_dashboard_fixtures",
    "game.final_emission_replay_projection",
)
_FORBIDDEN_GATE_READ_SIDE_SOURCE_FRAGMENTS: Final[tuple[str, ...]] = (
    "game.final_emission_replay_projection",
    "read_side_lineage_projection_surface",
    "project_sealed_replacement_subkind_from_fem",
    "SEALED_REPLACEMENT_SUBKIND",
    "SEALED_REPLACEMENT_SUBKINDS",
    "build_fem_runtime_lineage_events",
    "final_emission_meta_read_side_surface",
    "fem_runtime_lineage_events",
    "tests.helpers.golden_replay_projection",
    "tests.helpers.failure_classifier",
    "tests.helpers.failure_dashboard_report",
    "protected_observation_field_registry",
    "protected_observation_field_paths",
    "project_turn_observation",
    "build_classified_dashboard_row",
    "validate_failure_classification_row",
    "FailureClassification",
)


def _collect_import_module_paths(source: str) -> set[str]:
    tree = ast.parse(source)
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def _import_matches_forbidden_prefix(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def gate_magnet_guard_paths(
    registry: Mapping[str, ResponsibilityRecord] | None = None,
) -> tuple[str, ...]:
    """Gate-layer direct owners that must not accumulate replay read-side projection ownership."""
    reg = RESPONSIBILITY_REGISTRY if registry is None else registry
    paths: list[str] = []
    for gid, rec in reg.items():
        if gid in _GATE_MAGNET_GUARD_EXCLUDED_GROUP_IDS:
            continue
        if rec.declared_architecture_layer != "gate":
            continue
        rel = rec.direct_owner.replace("\\", "/")
        if rel in _GATE_MAGNET_GUARD_EXCLUDED_PATHS:
            continue
        paths.append(rel)
    return tuple(sorted(paths))


def collect_gate_magnet_guard_import_violations(
    rel_path: str,
    source: str,
    *,
    forbidden_prefixes: tuple[str, ...] = _FORBIDDEN_REPLAY_READ_SIDE_IMPORT_PREFIXES,
) -> list[str]:
    """Return import violations when a gate direct-owner suite pulls replay read-side projection helpers."""
    violations: list[str] = []
    for mod in sorted(_collect_import_module_paths(source)):
        for prefix in forbidden_prefixes:
            if _import_matches_forbidden_prefix(mod, prefix):
                violations.append(
                    f"{rel_path}: forbidden import {mod!r} "
                    f"(replay/dashboard/classifier read-side projection; owner is "
                    f"tests/test_final_emission_meta.py, tests/test_golden_replay.py, or classifier/dashboard suites)",
                )
    return violations


def collect_gate_magnet_guard_source_fragment_violations(
    rel_path: str,
    source: str,
    *,
    forbidden_fragments: tuple[str, ...] = _FORBIDDEN_GATE_READ_SIDE_SOURCE_FRAGMENTS,
) -> list[str]:
    """Return source-fragment violations for read-side projection assertion creep in gate owners."""
    return [
        f"{rel_path}: forbidden read-side projection fragment {fragment!r} "
        f"(move replay/dashboard/classifier contracts to meta projection or gauntlet/classifier owners)"
        for fragment in forbidden_fragments
        if fragment in source
    ]
