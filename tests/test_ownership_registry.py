"""Lightweight direct-owner registry + governance checks (tests only; no runtime hooks).

This module answers: *who may authoritatively define a new legality rule or shipped contract
edge case?* It does **not** claim to catalog all meaningful coverage.

Design notes (read before extending):
- **Direct owner** = exactly one canonical test module that is allowed to introduce detailed
  normative assertions for the responsibility. Other suites may overlap behaviorally.
- **Neighbor** paths (smoke, transcript, gauntlet, evaluator, downstream consumer, compatibility
  residue) are *supporting* surfaces. They must not be named as the direct owner for **live
  legality** responsibilities (gate-era rules, sanitizer post-processing, shipped policy
  materialization, etc.).
- New validation rules should land with a clear direct owner first; only then add broad
  regression, transcript, or gauntlet coverage so failures stay attributable.

Governance consumes the live inventory from ``tests/test_inventory.json`` (regenerate via
``py -3 tools/test_audit.py``). Unclassified test files elsewhere in the repo do not affect
these checks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import AbstractSet, Final, Mapping, Tuple

import pytest

try:
    from game import validation_layer_contracts as vlc
except ImportError:  # pragma: no cover - repo layout guard
    vlc = None  # type: ignore[assignment]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_INVENTORY_PATH = _REPO_ROOT / "tests" / "test_inventory.json"

# ---------------------------------------------------------------------------
# Canonical validation-layer ids (engine / planner / gpt / gate / evaluator)
# ---------------------------------------------------------------------------

_CANONICAL: Final[AbstractSet[str]] = (
    frozenset(vlc.CANONICAL_VALIDATION_LAYERS)
    if vlc is not None
    else frozenset({"engine", "planner", "gpt", "gate", "evaluator"})
)

# Heuristic inventory buckets that are too noisy to treat as contradicting a canonical owner.
_PERMISSIVE_INVENTORY_LAYERS: Final[AbstractSet[str]] = frozenset(
    {"smoke", "transcript", "gauntlet", "general"},
)

# Adjacent layers often co-score in static import heuristics; treat as compatible, not drift.
_SOFT_ADJACENT: Final[AbstractSet[frozenset[str]]] = frozenset(
    {
        frozenset({"engine", "planner"}),
        frozenset({"engine", "gpt"}),
        frozenset({"planner", "gpt"}),
    }
)

_LIVE_LEGALITY_GROUP_IDS: Final[AbstractSet[str]] = frozenset(
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
    if d in _CANONICAL and l in _CANONICAL and frozenset({d, l}) in _SOFT_ADJACENT:
        return True
    return False


def _direct_owner_inventory_layer_ok(declared: str | None, likely: str | None) -> bool:
    """Inventory ``general`` is permissive for neighbors, but not for a declared direct owner with a layer."""
    if likely is None or not isinstance(likely, str):
        return True
    if _normalize_layer(likely) == "general" and declared is not None:
        return False
    return _layers_compatible(declared, likely)


_NEIGHBOR_SUITE_FIELDS: Final[tuple[str, ...]] = (
    "smoke_suites",
    "transcript_suites",
    "gauntlet_suites",
    "evaluator_suites",
    "downstream_consumer_suites",
    "compatibility_residue_suites",
)


def _neighbor_paths_for_group(rec: ResponsibilityRecord) -> list[tuple[str, str]]:
    """(normalized_path, field_name) for neighbor slots only."""
    out: list[tuple[str, str]] = []
    for field in _NEIGHBOR_SUITE_FIELDS:
        for p in getattr(rec, field):
            out.append((str(p).replace("\\", "/"), field))
    return out


def _paths_for_group(rec: ResponsibilityRecord) -> list[tuple[str, str]]:
    """All governed paths: direct_owner plus each neighbor field."""
    seq: list[tuple[str, str]] = [(rec.direct_owner.replace("\\", "/"), "direct_owner")]
    seq.extend(_neighbor_paths_for_group(rec))
    return seq


def _path_is_disallowed_live_legality_owner(path: str) -> bool:
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


@dataclass(frozen=True)
class ResponsibilityRecord:
    """One governed responsibility slice."""

    human_title: str
    declared_architecture_layer: str | None
    direct_owner: str
    smoke_suites: Tuple[str, ...] = ()
    transcript_suites: Tuple[str, ...] = ()
    gauntlet_suites: Tuple[str, ...] = ()
    evaluator_suites: Tuple[str, ...] = ()
    downstream_consumer_suites: Tuple[str, ...] = ()
    compatibility_residue_suites: Tuple[str, ...] = ()


# Keys are stable ids consumed by governance tests.
RESPONSIBILITY_REGISTRY: Final[Mapping[str, ResponsibilityRecord]] = {
    "engine_truth_persistence_mechanics": ResponsibilityRecord(
        human_title="Engine truth / persistence / mechanics",
        declared_architecture_layer="engine",
        direct_owner="tests/test_save_load.py",
        smoke_suites=("tests/test_startup_and_timestamps.py",),
    ),
    "planner_prompt_bundle_shipped_contract": ResponsibilityRecord(
        human_title="Planner prompt bundle and shipped contract structure",
        declared_architecture_layer="planner",
        direct_owner="tests/test_narrative_plan_structural_readiness.py",
        smoke_suites=("tests/test_planner_convergence_live_pipeline.py",),
    ),
    # Normative GPT *shape* checks are thin here by design; gate suites own hard legality.
    "gpt_expression_surface_smoke": ResponsibilityRecord(
        human_title="GPT expression surface (smoke-oriented owner)",
        declared_architecture_layer="gpt",
        direct_owner="tests/test_narrative_mode_output_validator.py",
        smoke_suites=("tests/test_c4_narrative_mode_live_pipeline.py",),
    ),
    "final_emission_gate_orchestration": ResponsibilityRecord(
        human_title="Final emission gate orchestration",
        declared_architecture_layer="gate",
        direct_owner="tests/test_final_emission_gate.py",
        transcript_suites=("tests/test_narration_transcript_regressions.py",),
    ),
    "final_emission_validators": ResponsibilityRecord(
        human_title="Final emission validators",
        declared_architecture_layer="gate",
        direct_owner="tests/test_final_emission_validators.py",
        smoke_suites=("tests/test_final_emission_boundary_audit.py",),
    ),
    "final_emission_repairs": ResponsibilityRecord(
        human_title="Final emission repairs",
        declared_architecture_layer="gate",
        direct_owner="tests/test_final_emission_repairs.py",
        smoke_suites=("tests/test_final_emission_boundary_convergence.py",),
    ),
    "response_policy_contract_materialization": ResponsibilityRecord(
        human_title="Response policy contract materialization",
        declared_architecture_layer="engine",
        direct_owner="tests/test_response_policy_contracts.py",
    ),
    "prompt_context_contract_assembly": ResponsibilityRecord(
        human_title="Prompt context contract assembly",
        declared_architecture_layer="engine",
        direct_owner="tests/test_prompt_context.py",
        smoke_suites=("tests/test_prompt_context_plan_only_convergence.py",),
    ),
    "output_sanitizer_final_string_cleanup": ResponsibilityRecord(
        human_title="Output sanitizer final string cleanup",
        declared_architecture_layer="gate",
        direct_owner="tests/test_output_sanitizer.py",
    ),
    "social_engine_state_rules": ResponsibilityRecord(
        human_title="Social engine state / rules",
        declared_architecture_layer="engine",
        direct_owner="tests/test_social.py",
        smoke_suites=("tests/test_social_probe_determinism.py",),
    ),
    "social_emission_legality_surface": ResponsibilityRecord(
        human_title="Social emission legality / surface",
        declared_architecture_layer="gate",
        direct_owner="tests/test_social_exchange_emission.py",
        transcript_suites=("tests/test_speaker_contract_enforcement.py",),
    ),
    "lead_clue_lifecycle": ResponsibilityRecord(
        human_title="Lead / clue lifecycle",
        declared_architecture_layer="engine",
        direct_owner="tests/test_clue_lead_registry_integration.py",
        smoke_suites=("tests/test_clue_idempotence.py", "tests/test_clue_discovery.py"),
    ),
    "transcript_regression": ResponsibilityRecord(
        human_title="Transcript regression",
        declared_architecture_layer=None,
        direct_owner="tests/test_transcript_regression.py",
        transcript_suites=("tests/test_narration_transcript_regressions.py",),
        smoke_suites=("tests/test_transcript_runner_smoke.py",),
    ),
    "gauntlet_playability_validation": ResponsibilityRecord(
        human_title="Gauntlet / playability validation",
        declared_architecture_layer="gate",
        direct_owner="tests/test_gauntlet_regressions.py",
        gauntlet_suites=("tests/test_behavioral_gauntlet_smoke.py",),
        smoke_suites=("tests/test_playability_smoke.py",),
    ),
    "offline_evaluator_scoring": ResponsibilityRecord(
        human_title="Offline evaluator scoring",
        declared_architecture_layer="evaluator",
        direct_owner="tests/test_narrative_authenticity_eval.py",
        evaluator_suites=("tests/test_player_agency_evaluator.py", "tests/test_intent_fulfillment_evaluator.py"),
    ),
}

_REQUIRED_GROUP_IDS: Final[AbstractSet[str]] = frozenset(
    {
        "engine_truth_persistence_mechanics",
        "planner_prompt_bundle_shipped_contract",
        "gpt_expression_surface_smoke",
        "final_emission_gate_orchestration",
        "final_emission_validators",
        "final_emission_repairs",
        "response_policy_contract_materialization",
        "prompt_context_contract_assembly",
        "output_sanitizer_final_string_cleanup",
        "social_engine_state_rules",
        "social_emission_legality_surface",
        "lead_clue_lifecycle",
        "transcript_regression",
        "gauntlet_playability_validation",
        "offline_evaluator_scoring",
    }
)

# Block A cross-file duplicate top-level ``test_*`` names: tolerate only with an explicit reason.
_CROSS_FILE_DUPLICATE_ALLOWLIST: Final[Mapping[str, str]] = {
    "test_deterministic_json_stable": (
        "Parallel JSON stability probes in narrative planning vs referent tracking; "
        "distinct modules and docstrings disambiguate intent for pytest -k."
    ),
    "test_version_constant": (
        "Parallel shipped-version sentinels in narrative planning vs referent tracking; "
        "distinct modules disambiguate ownership of each contract surface."
    ),
    "test_maybe_attach_respects_env": (
        "Separate offline evaluator harnesses (intent fulfillment vs player agency) each "
        "need the same env-guard smoke; names intentionally parallel across evaluator suites."
    ),
}


def _load_inventory() -> dict:
    if not _INVENTORY_PATH.is_file():
        pytest.fail(f"missing inventory: {_INVENTORY_PATH} (run py -3 tools/test_audit.py)")
    return json.loads(_INVENTORY_PATH.read_text(encoding="utf-8"))


def _inventory_paths(data: dict) -> dict[str, dict]:
    files = data.get("files")
    assert isinstance(files, list), "inventory.files must be a list"
    out: dict[str, dict] = {}
    for row in files:
        assert isinstance(row, dict) and "path" in row
        out[str(row["path"]).replace("\\", "/")] = row
    return out


@pytest.fixture(scope="module")
def inventory() -> dict:
    return _load_inventory()


@pytest.fixture(scope="module")
def inventory_by_path(inventory: dict) -> dict[str, dict]:
    return _inventory_paths(inventory)


def test_registry_defines_all_required_groups() -> None:
    assert set(RESPONSIBILITY_REGISTRY) == _REQUIRED_GROUP_IDS


def test_inventory_schema_version_matches_audit_tool() -> None:
    """Block A: inventory generator and governance tests agree on schema generation."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_inv_audit", _REPO_ROOT / "tools" / "test_audit.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = _load_inventory()
    assert data.get("summary", {}).get("inventory_schema_version") == mod.INVENTORY_SCHEMA_VERSION


def test_inventory_embeds_neighbor_registry_index(inventory: dict) -> None:
    idx = inventory.get("ownership_registry_index")
    assert isinstance(idx, dict) and idx.get("available") is True
    groups = idx.get("groups")
    roles = idx.get("files_roles")
    assert isinstance(groups, dict) and isinstance(roles, dict)
    assert set(groups) == _REQUIRED_GROUP_IDS
    assert "final_emission_gate_orchestration" in groups
    gate = groups["final_emission_gate_orchestration"]
    assert isinstance(gate, dict)
    assert gate.get("direct_owner") == "tests/test_final_emission_gate.py"
    assert isinstance(gate.get("transcript_suites"), list)
    for key in (
        "smoke_suites",
        "transcript_suites",
        "gauntlet_suites",
        "evaluator_suites",
        "downstream_consumer_suites",
        "compatibility_residue_suites",
    ):
        assert key in gate, f"missing ownership_registry_index.groups field {key!r}"


def test_inventory_block_b_schema_v2_coherence(inventory: dict) -> None:
    clusters = inventory.get("block_b_overlap_clusters")
    assert isinstance(clusters, list) and clusters, "block_b_overlap_clusters must be a non-empty list"
    kinds = {c.get("kind") for c in clusters if isinstance(c, dict)}
    assert "dense_ownership_theme_by_architecture_layer" in kinds
    hubs = inventory.get("import_hub_modules")
    assert isinstance(hubs, list)
    idx = inventory.get("ownership_registry_index", {})
    fr = idx.get("files_roles", {})
    for fp, row in _inventory_paths(inventory).items():
        pos = row.get("ownership_registry_positions")
        assert isinstance(pos, list)
        if fp in fr:
            assert pos == fr[fp], f"files_roles mismatch for {fp}"


def test_evaluator_neighbor_may_have_general_inventory_layer(inventory_by_path: dict[str, dict]) -> None:
    """Heuristic ``general`` is allowed for non-owner paths; governance only sharpens direct owners."""
    p = "tests/test_player_agency_evaluator.py"
    row = inventory_by_path.get(p)
    assert row is not None and row.get("likely_architecture_layer") == "general"
    errs = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        _load_inventory(),
        inventory_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=_LIVE_LEGALITY_GROUP_IDS,
    )
    assert not any(p in e for e in errs)


def test_governance_rejects_duplicate_direct_owner(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    owner = "tests/test_save_load.py"
    reg = {
        "a": replace(RESPONSIBILITY_REGISTRY["engine_truth_persistence_mechanics"], direct_owner=owner),
        "b": replace(RESPONSIBILITY_REGISTRY["planner_prompt_bundle_shipped_contract"], direct_owner=owner),
    }
    errs = collect_ownership_governance_errors(
        reg,
        inventory,
        inventory_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("duplicate direct_owner" in e for e in errs)


def test_governance_rejects_missing_inventory_path(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    reg = {
        "__missing__": ResponsibilityRecord(
            human_title="Synthetic",
            declared_architecture_layer="engine",
            direct_owner="tests/__this_file_should_not_exist__.py",
        ),
    }
    errs = collect_ownership_governance_errors(
        reg,
        inventory,
        inventory_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("not in inventory" in e for e in errs)


def test_direct_owner_general_disallowed_when_declared_layer_set() -> None:
    assert not _direct_owner_inventory_layer_ok("engine", "general")
    assert not _direct_owner_inventory_layer_ok("gate", "General")
    assert _direct_owner_inventory_layer_ok(None, "general")
    assert _direct_owner_inventory_layer_ok("engine", "smoke")
    assert _direct_owner_inventory_layer_ok("engine", "engine")


def test_governance_rejects_sharp_direct_owner_layer_mismatch(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    reg = {
        "__layer__": ResponsibilityRecord(
            human_title="Synthetic layer mismatch",
            declared_architecture_layer="gate",
            direct_owner="tests/test_save_load.py",
        ),
    }
    errs = collect_ownership_governance_errors(
        reg,
        inventory,
        inventory_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("inventory layer incompatible" in e for e in errs)


def test_inventory_per_test_rows_include_marker_set(inventory: dict) -> None:
    tests = inventory.get("tests")
    assert isinstance(tests, list) and tests
    missing = [t.get("nodeid") for t in tests if not isinstance(t, dict) or "marker_set" not in t]
    assert not missing, f"missing marker_set on {len(missing)} items (first: {missing[:3]!r})"


def test_canonical_validation_layers_importable() -> None:
    assert vlc is not None, "game.validation_layer_contracts must import for layer alignment"
    assert set(vlc.CANONICAL_VALIDATION_LAYERS) == _CANONICAL


def collect_ownership_governance_errors(
    registry: Mapping[str, ResponsibilityRecord],
    inventory: dict,
    inventory_by_path: dict[str, dict],
    *,
    cross_file_allowlist: Mapping[str, str],
    live_legality_group_ids: AbstractSet[str],
) -> list[str]:
    """Pure governance checks for tests and unit tests with synthetic registries."""
    errors: list[str] = []
    seen_owners: dict[str, str] = {}

    for _fp, row in inventory_by_path.items():
        if not isinstance(row, dict):
            errors.append(f"inventory row for {_fp!r} is not an object")
            continue
        for key in ("marker_set", "ownership_registry_positions", "collected_duplicate_base_names"):
            if key not in row:
                errors.append(f"{_fp}: missing inventory field {key!r}")

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

        if gid in live_legality_group_ids and _path_is_disallowed_live_legality_owner(rec.direct_owner):
            errors.append(
                f"{gid}: direct_owner {rec.direct_owner!r} looks like transcript/gauntlet/"
                f"playability/evaluator suite; pick a unit/integration gate owner instead.",
            )

        row = inventory_by_path.get(rec.direct_owner.replace("\\", "/"))
        if row is not None:
            likely = row.get("likely_architecture_layer")
            if isinstance(likely, str) and not _direct_owner_inventory_layer_ok(rec.declared_architecture_layer, likely):
                if _normalize_layer(likely) == "general" and rec.declared_architecture_layer is not None:
                    detail = "direct owners may not rest on heuristic `general` when a declared validation layer is set"
                else:
                    detail = "tighten tools/test_audit.py heuristics or adjust declared_architecture_layer in the registry"
                errors.append(
                    f"{gid}: direct owner inventory layer incompatible with declared "
                    f"{rec.declared_architecture_layer!r}: likely_architecture_layer {likely!r} "
                    f"for {rec.direct_owner} ({detail}).",
                )

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


def test_ownership_registry_governance(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    errors = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        inventory,
        inventory_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=_LIVE_LEGALITY_GROUP_IDS,
    )
    assert not errors, "ownership governance failures:\n" + "\n".join(errors)


def test_allowlist_entries_have_non_empty_reasons() -> None:
    for name, reason in _CROSS_FILE_DUPLICATE_ALLOWLIST.items():
        assert name.startswith("test_"), name
        assert reason.strip(), f"empty allowlist reason for {name!r}"
