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
- **Downstream consumer** suites (Cycle AD-3): integration-visible smoke only — player-facing
  text hygiene, repair/replacement evidence, contract threading through HTTP/API, and
  layer-specific checked/failed/repaired fields owned by that consumer (e.g. answer
  completeness, response delta). They must **not** restate exact gate orchestration tables
  (``final_route``, ``final_emitted_source``, owner-bucket mapping, repair-kind enumeration)
  already owned by ``tests/test_final_emission_gate.py``; prefer ``tests/helpers/emission_smoke_assertions.py``.
- **Smoke suites**: survival / wiring / one-phrase hygiene checks; not full legality matrices.
- **Gauntlet / replay neighbors** (e.g. ``tests/test_golden_replay.py``): intentional
  diagnostic observation and drift projection locks — not runtime gate orchestration owners.
  Classifier/dashboard FEM bucket columns follow the same rule (diagnostic projection, not
  gate ownership).
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

# Cycle AD-3: integration downstream smoke paths — registry neighbors only, never direct_owner.
_DOWNSTREAM_INTEGRATION_SMOKE_ONLY: Final[frozenset[str]] = frozenset(
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
    """One governed responsibility slice.

    Neighbor field semantics (Cycle AD-3):
    - ``direct_owner``: normative / full assertion home for the responsibility.
    - ``downstream_consumer_suites``: integration-visible smoke (HTTP/API packaging, consumer
      layer meta fields); not alternate gate orchestration owners.
    - ``smoke_suites``: thin wiring / survival checks only.
    - ``gauntlet_suites`` / ``transcript_suites``: end-to-end observation; replay/classifier
      FEM projection duplication is intentional diagnostic protection, not gate ownership.
    """

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
        # Direct owner: apply_final_emission_gate orchestration, layer order, exact final_route /
        # final_emitted_source / repair-kind tables. Downstream neighbors: HTTP/API smoke and
        # consumer-layer boundary validate-only traces only (see emission_smoke_assertions.py).
        human_title="Final emission gate orchestration",
        declared_architecture_layer="gate",
        direct_owner="tests/test_final_emission_gate.py",
        transcript_suites=("tests/test_narration_transcript_regressions.py",),
        downstream_consumer_suites=(
            "tests/test_turn_pipeline_shared.py",
            "tests/test_answer_completeness_rules.py",
            "tests/test_response_delta_requirement.py",
            "tests/test_interaction_continuity_repair.py",
            "tests/test_diegetic_fallback_narration.py",
        ),
    ),
    "final_emission_meta_projection": ResponsibilityRecord(
        # Direct owner: FEM read/normalize/projection helpers. Golden replay / failure classifier
        # bucket columns are intentional diagnostic projection neighbors — not gate orchestration.
        human_title="Final emission meta (FEM) projection, replay read path, and sidecar reads",
        declared_architecture_layer="gate",
        direct_owner="tests/test_final_emission_meta.py",
        downstream_consumer_suites=(
            "tests/test_turn_packet_stage_diff_integration.py",
            "tests/test_diegetic_fallback_narration.py",
        ),
    ),
    "final_emission_visibility_semantics": ResponsibilityRecord(
        human_title="Final emission visibility fallback semantics",
        declared_architecture_layer="gate",
        direct_owner="tests/test_final_emission_visibility.py",
        downstream_consumer_suites=("tests/test_turn_pipeline_shared.py",),
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
        downstream_consumer_suites=("tests/test_prompt_and_guard.py",),
    ),
    "output_sanitizer_final_string_cleanup": ResponsibilityRecord(
        # Direct owner: full procedural phrase-ban matrix. Downstream neighbors: HTTP smoke via
        # emission_smoke_assertions helpers — not duplicate sanitizer tables.
        human_title="Output sanitizer final string cleanup",
        declared_architecture_layer="gate",
        direct_owner="tests/test_output_sanitizer.py",
        downstream_consumer_suites=(
            "tests/test_turn_pipeline_shared.py",
            "tests/test_prompt_and_guard.py",
        ),
    ),
    "social_engine_state_rules": ResponsibilityRecord(
        human_title="Social engine state / rules",
        declared_architecture_layer="engine",
        direct_owner="tests/test_social.py",
        smoke_suites=("tests/test_social_probe_determinism.py",),
    ),
    "social_emission_legality_surface": ResponsibilityRecord(
        # Direct owner: strict-social legality tables (question_resolution, first-sentence).
        # answer_completeness_rules / response_delta_requirement are downstream policy consumers.
        human_title="Social emission legality / surface",
        declared_architecture_layer="gate",
        direct_owner="tests/test_social_exchange_emission.py",
        transcript_suites=("tests/test_speaker_contract_enforcement.py",),
        downstream_consumer_suites=(
            "tests/test_answer_completeness_rules.py",
            "tests/test_response_delta_requirement.py",
        ),
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
        # Direct owner: gauntlet orchestration. golden_replay gauntlet neighbor holds intentional
        # replay observation / FEM drift locks — diagnostic projection, not gate orchestration.
        human_title="Gauntlet / playability validation",
        declared_architecture_layer="gate",
        direct_owner="tests/test_gauntlet_regressions.py",
        gauntlet_suites=(
            "tests/test_behavioral_gauntlet_smoke.py",
            "tests/test_golden_replay.py",
        ),
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
        "final_emission_meta_projection",
        "final_emission_visibility_semantics",
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
    "test_real_repo_scan_does_not_require_zero_findings": (
        "Parallel realization audit tool smoke in layer vs provenance audit modules; distinct audit surfaces."
    ),
    "test_report_generation_writes_json_and_markdown": (
        "Parallel realization audit report writers in layer vs provenance audit modules."
    ),
    "test_severity_values_are_only_expected_values": (
        "Parallel realization audit severity contract smoke in layer vs provenance audit modules."
    ),
    "test_tool_imports_successfully": (
        "Parallel realization audit import smoke in layer vs provenance audit modules."
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
            if dkey in _DOWNSTREAM_INTEGRATION_SMOKE_ONLY:
                errors.append(
                    f"{gid}: direct_owner {rec.direct_owner!r} is AD-registered downstream "
                    f"integration smoke only; assign a gate/unit owner instead.",
                )

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


def test_final_emission_meta_projection_read_side_ownership_boundaries() -> None:
    """Cycle AE4: read-side lineage/projection edits stay in meta projection ownership."""
    meta_proj = RESPONSIBILITY_REGISTRY["final_emission_meta_projection"]
    gate_orch = RESPONSIBILITY_REGISTRY["final_emission_gate_orchestration"]

    assert meta_proj.direct_owner == "tests/test_final_emission_meta.py"
    assert gate_orch.direct_owner == "tests/test_final_emission_gate.py"
    assert meta_proj.direct_owner != gate_orch.direct_owner

    gate_path = "tests/test_final_emission_gate.py"
    assert gate_path not in meta_proj.downstream_consumer_suites
    assert gate_path not in meta_proj.smoke_suites
    assert gate_path not in meta_proj.transcript_suites
    assert gate_path not in meta_proj.gauntlet_suites
    assert gate_path not in meta_proj.evaluator_suites
    assert gate_path not in meta_proj.compatibility_residue_suites

    title = meta_proj.human_title.lower()
    assert "read path" in title or "replay read path" in title
    assert "projection" in title
    assert "gate orchestration" not in title


def test_final_emission_gate_does_not_accumulate_read_side_projection_assertions() -> None:
    """AG-10: gate owner must not re-own FEM replay/read-side projection contracts."""
    gate_source = (_REPO_ROOT / "tests" / "test_final_emission_gate.py").read_text(encoding="utf-8")
    forbidden_fragments = (
        "game.final_emission_replay_projection",
        "read_side_lineage_projection_surface",
        "project_sealed_replacement_subkind_from_fem",
        "SEALED_REPLACEMENT_SUBKIND",
        "SEALED_REPLACEMENT_SUBKINDS",
        "build_fem_runtime_lineage_events",
        "final_emission_meta_read_side_surface",
        "fem_runtime_lineage_events",
    )

    found = [fragment for fragment in forbidden_fragments if fragment in gate_source]
    assert not found, (
        "tests/test_final_emission_gate.py owns gate orchestration/wrappers, not read-side "
        "replay projection assertions. Move these contracts to tests/test_final_emission_meta.py: "
        + ", ".join(found)
    )


def test_ad3_gate_orchestration_direct_owner_is_final_emission_gate() -> None:
    """Cycle AD-3: gate orchestration normative owner stays on the gate module."""
    rec = RESPONSIBILITY_REGISTRY["final_emission_gate_orchestration"]
    assert rec.direct_owner.replace("\\", "/") == "tests/test_final_emission_gate.py"


def test_ad3_downstream_integration_smoke_suites_registered_as_neighbors() -> None:
    """Cycle AD-3: AD-thinned suites are downstream neighbors, never direct owners."""
    gate = RESPONSIBILITY_REGISTRY["final_emission_gate_orchestration"]
    sanitizer = RESPONSIBILITY_REGISTRY["output_sanitizer_final_string_cleanup"]
    visibility = RESPONSIBILITY_REGISTRY["final_emission_visibility_semantics"]
    social = RESPONSIBILITY_REGISTRY["social_emission_legality_surface"]

    gate_downstream = frozenset(p.replace("\\", "/") for p in gate.downstream_consumer_suites)
    assert _DOWNSTREAM_INTEGRATION_SMOKE_ONLY.issubset(gate_downstream)

    turn_pipeline = "tests/test_turn_pipeline_shared.py"
    assert turn_pipeline in gate_downstream
    assert turn_pipeline in frozenset(
        p.replace("\\", "/") for p in sanitizer.downstream_consumer_suites
    )
    assert turn_pipeline in frozenset(
        p.replace("\\", "/") for p in visibility.downstream_consumer_suites
    )

    ac_rd = frozenset(
        {
            "tests/test_answer_completeness_rules.py",
            "tests/test_response_delta_requirement.py",
        }
    )
    assert ac_rd.issubset(gate_downstream)
    assert ac_rd.issubset(
        frozenset(p.replace("\\", "/") for p in social.downstream_consumer_suites)
    )

    for gid, rec in RESPONSIBILITY_REGISTRY.items():
        owner = rec.direct_owner.replace("\\", "/")
        assert owner not in _DOWNSTREAM_INTEGRATION_SMOKE_ONLY, (
            f"{gid} must not list {owner!r} as direct_owner "
            f"(downstream integration smoke only)."
        )


def test_ad3_golden_replay_is_gauntlet_neighbor_not_gate_direct_owner() -> None:
    """Cycle AD-3: replay observation locks live under gauntlet neighbor, not gate orchestration."""
    gate = RESPONSIBILITY_REGISTRY["final_emission_gate_orchestration"]
    gauntlet = RESPONSIBILITY_REGISTRY["gauntlet_playability_validation"]
    golden = "tests/test_golden_replay.py"

    assert golden in frozenset(p.replace("\\", "/") for p in gauntlet.gauntlet_suites)
    assert gauntlet.direct_owner.replace("\\", "/") != gate.direct_owner.replace("\\", "/")
    assert golden not in frozenset(p.replace("\\", "/") for p in gate.downstream_consumer_suites)
