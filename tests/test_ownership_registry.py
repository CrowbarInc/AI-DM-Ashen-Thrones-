"""Lightweight direct-owner registry + governance checks (tests only; no runtime hooks).

This module answers: *who may authoritatively define a new legality rule or shipped contract
edge case?* It does **not** claim to catalog all meaningful coverage.

Design notes (read before extending):
- **Direct owner** = exactly one canonical test module that is allowed to introduce detailed
  normative assertions for the responsibility. Other suites may overlap behaviorally.
- **Smoke / transcript / gauntlet / evaluator** paths listed here are *supporting* surfaces.
  They must not be named as the direct owner for **live legality** responsibilities (gate-era
  rules, sanitizer post-processing, shipped policy materialization, etc.).
- New validation rules should land with a clear direct owner first; only then add broad
  regression, transcript, or gauntlet coverage so failures stay attributable.

Governance consumes the live inventory from ``tests/test_inventory.json`` (regenerate via
``py -3 tools/test_audit.py``). Unclassified test files elsewhere in the repo do not affect
these checks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
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
    {"smoke", "transcript", "gauntlet"},
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


def test_canonical_validation_layers_importable() -> None:
    assert vlc is not None, "game.validation_layer_contracts must import for layer alignment"
    assert set(vlc.CANONICAL_VALIDATION_LAYERS) == _CANONICAL


def test_ownership_registry_governance(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    errors: list[str] = []
    seen_owners: dict[str, str] = {}

    for gid, rec in RESPONSIBILITY_REGISTRY.items():
        paths_to_check = (
            (rec.direct_owner, "direct_owner"),
            *[(p, "smoke_suites") for p in rec.smoke_suites],
            *[(p, "transcript_suites") for p in rec.transcript_suites],
            *[(p, "gauntlet_suites") for p in rec.gauntlet_suites],
            *[(p, "evaluator_suites") for p in rec.evaluator_suites],
        )
        for rel, field in paths_to_check:
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

        if gid in _LIVE_LEGALITY_GROUP_IDS and _path_is_disallowed_live_legality_owner(rec.direct_owner):
            errors.append(
                f"{gid}: direct_owner {rec.direct_owner!r} looks like transcript/gauntlet/"
                f"playability/evaluator suite; pick a unit/integration gate owner instead.",
            )

        row = inventory_by_path.get(rec.direct_owner.replace("\\", "/"))
        if row is not None:
            likely = row.get("likely_architecture_layer")
            if isinstance(likely, str) and not _layers_compatible(rec.declared_architecture_layer, likely):
                errors.append(
                    f"{gid}: declared layer {rec.declared_architecture_layer!r} "
                    f"vs inventory likely_architecture_layer {likely!r} for {rec.direct_owner}",
                )

    dups = inventory.get("cross_file_duplicate_test_names")
    if isinstance(dups, list):
        for block in dups:
            if not isinstance(block, dict):
                continue
            base = block.get("base_name")
            if not isinstance(base, str):
                continue
            if base in _CROSS_FILE_DUPLICATE_ALLOWLIST:
                continue
            files = block.get("files")
            fl = ", ".join(files) if isinstance(files, list) else "?"
            errors.append(
                f"cross-file duplicate test name {base!r} not allowlisted "
                f"(files: {fl}); rename tests or extend _CROSS_FILE_DUPLICATE_ALLOWLIST with a reason.",
            )

    assert not errors, "ownership governance failures:\n" + "\n".join(errors)


def test_allowlist_entries_have_non_empty_reasons() -> None:
    for name, reason in _CROSS_FILE_DUPLICATE_ALLOWLIST.items():
        assert name.startswith("test_"), name
        assert reason.strip(), f"empty allowlist reason for {name!r}"
