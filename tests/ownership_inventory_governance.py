"""Ownership inventory governance orchestration (import-light; no pytest).

Committed governance inventory schema validation, registry/inventory parity checks,
and ``collect_ownership_governance_errors``. Enforced by governance tests in
``tests/test_inventory_governance.py`` (registry/inventory integration in
``tests/test_ownership_registry.py``). Canonical registry data is sourced from
``tests/ownership_registry_contract.py``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import AbstractSet, Final, Mapping

from tests.ownership_registry_contract import (
    build_ownership_registry_index,
)
from tests.ownership_registry_contract import (
    ResponsibilityRecord,
    _neighbor_paths_for_group,
    _paths_for_group,
)

try:
    from game import validation_layer_contracts as vlc
except ImportError:  # pragma: no cover - repo layout guard
    vlc = None  # type: ignore[assignment]

_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOVERNANCE_INVENTORY_PATH: Final[Path] = _REPO_ROOT / "tests" / "test_inventory_governance.json"

CANONICAL_VALIDATION_LAYERS: Final[AbstractSet[str]] = (
    frozenset(vlc.CANONICAL_VALIDATION_LAYERS)
    if vlc is not None
    else frozenset({"engine", "planner", "gpt", "gate", "evaluator"})
)

_PERMISSIVE_INVENTORY_LAYERS: Final[AbstractSet[str]] = frozenset(
    {"smoke", "transcript", "gauntlet", "general"},
)

_SOFT_ADJACENT: Final[AbstractSet[frozenset[str]]] = frozenset(
    {
        frozenset({"engine", "planner"}),
        frozenset({"engine", "gpt"}),
        frozenset({"planner", "gpt"}),
    }
)

LIVE_LEGALITY_GROUP_IDS: Final[AbstractSet[str]] = frozenset(
    {
        "final_emission_gate_orchestration",
        "final_emission_validators",
        "final_emission_repairs",
        "response_policy_contract_materialization",
        "prompt_context_contract_assembly",
        "output_sanitizer_final_string_cleanup",
        "social_emission_legality_surface",
    }
)

# Cycle AD-3: integration downstream smoke paths — registry neighbors only, never direct_owner.
DOWNSTREAM_INTEGRATION_SMOKE_ONLY: Final[frozenset[str]] = frozenset(
    {
        "tests/test_turn_pipeline_shared.py",
        "tests/test_answer_completeness_rules.py",
        "tests/test_response_delta_requirement.py",
    }
)


def _normalize_layer(name: str | None) -> str | None:
    if name is None:
        return None
    n = name.strip().lower()
    aliases = {"truth": "engine", "structure": "planner", "expression": "gpt", "legality": "gate", "scoring": "evaluator"}
    return aliases.get(n, n)


def _layers_compatible(declared: str | None, likely: str | None) -> bool:
    """Return True if inventory ``likely`` does not contradict ``declared`` in a sharp way."""
    if declared is None or likely is None:
        return True
    d = _normalize_layer(declared)
    l = _normalize_layer(likely)
    if d is None or l is None:
        return True
    if l in _PERMISSIVE_INVENTORY_LAYERS:
        return True
    if d == l:
        return True
    if d in CANONICAL_VALIDATION_LAYERS and l in CANONICAL_VALIDATION_LAYERS and frozenset({d, l}) in _SOFT_ADJACENT:
        return True
    return False


def direct_owner_inventory_layer_ok(declared: str | None, likely: str | None) -> bool:
    """Inventory ``general`` is permissive for neighbors, but not for a declared direct owner with a layer."""
    if likely is None or not isinstance(likely, str):
        return True
    if _normalize_layer(likely) == "general" and declared is not None:
        return False
    return _layers_compatible(declared, likely)


def path_is_disallowed_live_legality_owner(path: str) -> bool:
    """True when ``path`` looks like transcript / gauntlet / playability / evaluator *suite* ownership."""
    norm = path.replace("\\", "/").lower()
    base = norm.rsplit("/", 1)[-1]
    if "playability" in base:
        return True
    if base.endswith("_eval.py") or "evaluator" in base:
        return True
    if "transcript_gauntlet" in base:
        return True
    if base == "test_transcript_regression.py" or "transcript_regressions" in base:
        return True
    if "gauntlet" in base:
        return True
    return False


def load_governance_inventory(path: Path | None = None) -> dict:
    """Load committed governance inventory JSON."""
    inventory_path = DEFAULT_GOVERNANCE_INVENTORY_PATH if path is None else path
    if not inventory_path.is_file():
        raise FileNotFoundError(f"missing inventory: {inventory_path} (run py -3 tools/test_audit.py)")
    return json.loads(inventory_path.read_text(encoding="utf-8"))


def inventory_paths(data: dict) -> dict[str, dict]:
    files = data.get("files")
    assert isinstance(files, list), "inventory.files must be a list"
    out: dict[str, dict] = {}
    for row in files:
        assert isinstance(row, dict) and "path" in row
        out[str(row["path"]).replace("\\", "/")] = row
    return out


def full_inventory_by_path(full_inventory: dict) -> dict[str, dict]:
    """Index full diagnostic ``files[]`` rows by normalized path."""
    out: dict[str, dict] = {}
    for row in full_inventory.get("files", ()):
        if isinstance(row, dict) and "path" in row:
            out[str(row["path"]).replace("\\", "/")] = row
    return out


def allowed_governance_committed_paths(
    registry: Mapping[str, ResponsibilityRecord],
    inventory: dict,
    *,
    cross_file_duplicate_test_names: list | None = None,
) -> set[str]:
    """Paths permitted in committed governance ``files[]`` (registry + cross-file dup files)."""
    paths: set[str] = set()
    files_roles = build_ownership_registry_index(registry).get("files_roles", {})
    if isinstance(files_roles, dict):
        paths.update(str(fp).replace("\\", "/") for fp in files_roles)
    dups = cross_file_duplicate_test_names
    if dups is None:
        dups = inventory.get("cross_file_duplicate_test_names")
    if isinstance(dups, list):
        for block in dups:
            if not isinstance(block, dict):
                continue
            files = block.get("files")
            if isinstance(files, list):
                paths.update(str(fp).replace("\\", "/") for fp in files)
    return paths


def collect_ownership_governance_errors(
    registry: Mapping[str, ResponsibilityRecord],
    inventory: dict,
    inventory_by_path: dict[str, dict],
    *,
    cross_file_allowlist: Mapping[str, str],
    live_legality_group_ids: AbstractSet[str],
    cross_file_duplicate_test_names: list | None = None,
    full_inventory_by_path: Mapping[str, dict] | None = None,
) -> list[str]:
    """Pure governance checks for tests and unit tests with synthetic registries."""
    errors: list[str] = []
    seen_owners: dict[str, str] = {}

    if "tests" in inventory:
        errors.append(
            "governance inventory must not store tests[] "
            "(derive per-test marker coverage via tools/test_audit.py --check)",
        )
    if "block_b_overlap_clusters" in inventory:
        errors.append(
            "governance inventory must not store block_b_overlap_clusters "
            "(use py -3 tools/test_audit.py --full for triage aggregates)",
        )
    if "import_hub_modules" in inventory:
        errors.append(
            "governance inventory must not store import_hub_modules "
            "(use py -3 tools/test_audit.py --full for triage aggregates)",
        )
    if "cross_file_duplicate_test_names" in inventory:
        errors.append(
            "governance inventory must not store cross_file_duplicate_test_names "
            "(derive via tools/test_audit.py --check)",
        )

    allowed_paths = allowed_governance_committed_paths(
        registry,
        inventory,
        cross_file_duplicate_test_names=cross_file_duplicate_test_names,
    )
    for fp in inventory_by_path:
        if fp not in allowed_paths:
            errors.append(
                f"governance files[] must not store non-governance path {fp!r} "
                f"(registry-owned and cross-file duplicate paths only)",
            )

    for _fp, row in inventory_by_path.items():
        if not isinstance(row, dict):
            errors.append(f"inventory row for {_fp!r} is not an object")
            continue
        if "marker_set" in row:
            errors.append(
                f"{_fp}: governance inventory must not store marker_set "
                f"(derive via tools/test_audit.py --check)",
            )
        if "ownership_registry_positions" in row:
            errors.append(
                f"{_fp}: governance inventory must not store ownership_registry_positions "
                f"(derive via build_ownership_registry_index())",
            )
        if "pytest_collected" in row:
            errors.append(
                f"{_fp}: governance inventory must not store pytest_collected "
                f"(derive via tools/test_audit.py --check)",
            )
        if "collected_duplicate_base_names" in row:
            errors.append(
                f"{_fp}: governance inventory must not store collected_duplicate_base_names "
                f"(derive via tools/test_audit.py --check)",
            )
        if "likely_architecture_layer" in row:
            errors.append(
                f"{_fp}: governance inventory must not store likely_architecture_layer "
                f"(derive via tools/test_audit.py --check)",
            )

    derived_roles = build_ownership_registry_index(registry).get("files_roles", {})
    if isinstance(derived_roles, dict):
        for fp in derived_roles:
            if fp not in inventory_by_path:
                errors.append(f"derived registry path not in inventory: {fp}")

    for gid, rec in registry.items():
        neighbors = _neighbor_paths_for_group(rec)
        seen_neighbor: dict[str, str] = {}
        for npath, field in neighbors:
            if npath in seen_neighbor and seen_neighbor[npath] != field:
                errors.append(
                    f"{gid}: neighbor path {npath!r} listed under both {seen_neighbor[npath]!r} and {field!r}",
                )
            seen_neighbor[npath] = field

        for rel, field in _paths_for_group(rec):
            key = rel.replace("\\", "/")
            if key not in inventory_by_path:
                errors.append(f"{gid}: {field} not in inventory: {key}")

        if rec.direct_owner:
            dkey = rec.direct_owner.replace("\\", "/")
            if dkey in seen_owners and seen_owners[dkey] != gid:
                errors.append(
                    f"duplicate direct_owner claim: {dkey!r} used by {seen_owners[dkey]!r} and {gid!r}",
                )
            seen_owners[dkey] = gid
            if dkey in DOWNSTREAM_INTEGRATION_SMOKE_ONLY:
                errors.append(
                    f"{gid}: direct_owner {rec.direct_owner!r} is AD-registered downstream "
                    f"integration smoke only; assign a gate/unit owner instead.",
                )

        if gid in live_legality_group_ids and path_is_disallowed_live_legality_owner(rec.direct_owner):
            errors.append(
                f"{gid}: direct_owner {rec.direct_owner!r} looks like transcript/gauntlet/"
                f"playability/evaluator suite; pick a unit/integration gate owner instead.",
            )

        row = None
        if full_inventory_by_path is not None:
            row = full_inventory_by_path.get(rec.direct_owner.replace("\\", "/"))
        if row is not None:
            likely = row.get("likely_architecture_layer")
            if isinstance(likely, str) and not direct_owner_inventory_layer_ok(rec.declared_architecture_layer, likely):
                if _normalize_layer(likely) == "general" and rec.declared_architecture_layer is not None:
                    detail = "direct owners may not rest on heuristic `general` when a declared validation layer is set"
                else:
                    detail = "tighten tools/test_audit.py heuristics or adjust declared_architecture_layer in the registry"
                errors.append(
                    f"{gid}: direct owner inventory layer incompatible with declared "
                    f"{rec.declared_architecture_layer!r}: likely_architecture_layer {likely!r} "
                    f"for {rec.direct_owner} ({detail}).",
                )

    dups = cross_file_duplicate_test_names
    if dups is None:
        dups = inventory.get("cross_file_duplicate_test_names")
    if isinstance(dups, list):
        for block in dups:
            if not isinstance(block, dict):
                continue
            base = block.get("base_name")
            if not isinstance(base, str):
                continue
            if base in cross_file_allowlist:
                continue
            files = block.get("files")
            fl = ", ".join(files) if isinstance(files, list) else "?"
            errors.append(
                f"cross-file duplicate test name {base!r} not allowlisted "
                f"(files: {fl}); rename tests or extend allowlist with a reason.",
            )

    return errors
