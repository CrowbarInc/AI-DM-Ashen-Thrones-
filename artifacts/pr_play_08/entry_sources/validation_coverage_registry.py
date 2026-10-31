"""
Objective #12 — validation coverage registry (governance / tooling only).

This module is the canonical, machine-readable map from feature/domain IDs to
which validation surfaces must defend them. It does not implement scoring,
gates, or runtime gameplay behavior.

Existing evaluators (playability, behavioral gauntlet, AER/NA operators, etc.)
remain the only scoring authorities for their domains; entries here only
point at existing tests, tools, and scenario IDs.

Schema validation: ``validate_entries()`` / ``validate_registry()``; enforced
by pytest (``tests/test_validation_coverage_registry.py``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Final, Sequence


class RequiredSurface(str, Enum):
    """Finite allowed set for ``CoverageEntry.required_surfaces``."""

    TRANSCRIPT = "transcript"
    BEHAVIORAL_GAUNTLET = "behavioral_gauntlet"
    MANUAL_GAUNTLET = "manual_gauntlet"
    PLAYABILITY = "playability"
    UNIT_CONTRACT = "unit_contract"
    INTEGRATION_SMOKE = "integration_smoke"


class CoverageStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


# --- Governance allowlists (extend when new harness IDs are added deliberately) ---

ALLOWED_MANUAL_GAUNTLET_IDS: Final[frozenset[str]] = frozenset(f"g{i}" for i in range(1, 13))

ALLOWED_BEHAVIORAL_GAUNTLET_AXES: Final[frozenset[str]] = frozenset(
    {
        "neutrality",
        "escalation_correctness",
        "reengagement_quality",
        "dialogue_coherence",
    }
)

# Stable IDs: pytest function names in ``tests/test_playability_smoke.py``.
ALLOWED_PLAYABILITY_SCENARIO_IDS: Final[frozenset[str]] = frozenset(
    {
        "test_playability_smoke_direct_answer_pressure",
        "test_playability_smoke_narrowing_player_intent",
        "test_playability_smoke_escalation_under_pressure",
        "test_playability_smoke_immersion_guard_adversarial_upstream",
    }
)

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent


def _normalize_manual_gauntlet_id(raw: str) -> str:
    s = raw.strip().lower()
    if s.startswith("g") and s[1:].isdigit():
        return f"g{int(s[1:])}"
    return s


@dataclass(frozen=True, slots=True)
class CoverageEntry:
    """
    One feature/domain row.

    Pointer fields must reference existing tests, tools, or scenario IDs — never
    duplicate evaluator rubrics inline.

    For each value in ``required_surfaces``, the matching typed tuple field
    below must be non-empty (machine-checked). ``notes`` and
    ``optional_smoke_overlap`` are explanatory only.

    Example shape (documentation only — not a live row):

        CoverageEntry(
            feature_id="example_feature",
            title="Example: social emission repair",
            owner_domain="emission_gate",
            status=CoverageStatus.DRAFT,
            required_surfaces=frozenset({
                RequiredSurface.UNIT_CONTRACT,
                RequiredSurface.TRANSCRIPT,
            }),
            transcript_modules=("tests/test_example_transcript.py",),
            behavioral_gauntlet_axes=(),
            manual_gauntlets=("g9",),
            playability_scenarios=(),
            unit_contract_modules=("tests/test_example_contracts.py",),
            integration_smoke_modules=(),
            notes="Primary: unit+transcript; manual g9 for feel.",
            optional_smoke_overlap=(
                "tests/test_behavioral_gauntlet_smoke.py — axis smoke only; "
                "does not replace transcript contract depth.",
            ),
        )
    """

    feature_id: str
    title: str
    owner_domain: str
    status: CoverageStatus
    required_surfaces: frozenset[RequiredSurface]
    transcript_modules: tuple[str, ...]
    behavioral_gauntlet_axes: tuple[str, ...]
    manual_gauntlets: tuple[str, ...]
    playability_scenarios: tuple[str, ...]
    unit_contract_modules: tuple[str, ...]
    integration_smoke_modules: tuple[str, ...]
    notes: str
    optional_smoke_overlap: tuple[str, ...]


# ---------------------------------------------------------------------------
# Registry contents (incremental seed — do not bulk-fill in Objective #12).
# ---------------------------------------------------------------------------

REGISTRY: Final[tuple[CoverageEntry, ...]] = (
    # Validation-layer *contracts* (Objective #11): fast unit/AST contract tests;
    # not defended by playability/transcript/gauntlet lanes.
    CoverageEntry(
        feature_id="validation_layer_contracts",
        title="Validation layer responsibility / ownership contracts",
        owner_domain="validation_layer",
        status=CoverageStatus.ACTIVE,
        required_surfaces=frozenset({RequiredSurface.UNIT_CONTRACT}),
        transcript_modules=(),
        behavioral_gauntlet_axes=(),
        manual_gauntlets=(),
        playability_scenarios=(),
        unit_contract_modules=("tests/test_validation_layer_contracts.py",),
        integration_smoke_modules=(),
        notes=(
            "Canonical contract home: game.validation_layer_contracts. "
            "No second evaluator; registry documents coverage intent only."
        ),
        optional_smoke_overlap=(
            "tests/test_validation_layer_audit_smoke.py — audit/diagnostics smoke; "
            "harness depth differs from AST contract tests.",
        ),
    ),
    # Deterministic four-axis behavioral gauntlet (complete track per docs/testing.md).
    CoverageEntry(
        feature_id="behavioral_gauntlet_validation",
        title="Behavioral gauntlet - deterministic axis-scored narration smoke",
        owner_domain="behavioral_gauntlet",
        status=CoverageStatus.ACTIVE,
        required_surfaces=frozenset({RequiredSurface.BEHAVIORAL_GAUNTLET}),
        transcript_modules=(),
        behavioral_gauntlet_axes=(
            "neutrality",
            "escalation_correctness",
            "reengagement_quality",
            "dialogue_coherence",
        ),
        manual_gauntlets=(),
        playability_scenarios=(),
        unit_contract_modules=(),
        integration_smoke_modules=(),
        notes=(
            "Smoke lane: tests/test_behavioral_gauntlet_smoke.py (integration + regression). "
            "Axes are the canonical ids enforced by evaluate_behavioral_gauntlet."
        ),
        optional_smoke_overlap=(
            "tests/test_behavioral_gauntlet_eval.py - evaluator contract depth; "
            "does not replace multi-turn smoke slices in test_behavioral_gauntlet_smoke.py.",
        ),
    ),
    # Turn-scored playability: canonical CI-style owner per docs/testing.md.
    CoverageEntry(
        feature_id="playability_validation",
        title="Playability validation - turn-scored /api/chat smoke scenarios",
        owner_domain="playability",
        status=CoverageStatus.ACTIVE,
        required_surfaces=frozenset({RequiredSurface.PLAYABILITY}),
        transcript_modules=(),
        behavioral_gauntlet_axes=(),
        manual_gauntlets=(),
        playability_scenarios=(
            "test_playability_smoke_direct_answer_pressure",
            "test_playability_smoke_narrowing_player_intent",
            "test_playability_smoke_escalation_under_pressure",
            "test_playability_smoke_immersion_guard_adversarial_upstream",
        ),
        unit_contract_modules=(),
        integration_smoke_modules=(),
        notes=(
            "Scoring authority is evaluate_playability only; pytest ids match "
            "tests/test_playability_smoke.py. Multi-turn CLI runner uses "
            "tools/run_playability_validation.py scenario keys (audit prints both)."
        ),
        optional_smoke_overlap=(),
    ),
    # Named human pass outside pytest (docs/manual_gauntlets.md); representative slice g1.
    CoverageEntry(
        feature_id="manual_gauntlet_lead_narration_smoke",
        title="Manual gauntlet - lead / narration scripted feel pass (G1 slice)",
        owner_domain="manual_gauntlet",
        status=CoverageStatus.ACTIVE,
        required_surfaces=frozenset({RequiredSurface.MANUAL_GAUNTLET}),
        transcript_modules=(),
        behavioral_gauntlet_axes=(),
        manual_gauntlets=("g1",),
        playability_scenarios=(),
        unit_contract_modules=(),
        integration_smoke_modules=(),
        notes=(
            "Canonical rubric and prompt scripts: docs/manual_gauntlets.md (G1 - same-NPC "
            "follow-up). Run after changes that can still feel wrong when pytest is green."
        ),
        optional_smoke_overlap=(
            "docs/manual_gauntlets.md G9-G12 - behavioral_eval advisory slices on manual runs; "
            "manual judgment still owns pass/fail.",
        ),
    ),
    # Transcript-named regressions locking final-emission anti-railroading contracts.
    CoverageEntry(
        feature_id="anti_railroading_transcript_regressions",
        title="Anti-railroading + final gate transcript regressions (quoted lines, constraints)",
        owner_domain="emission_gate",
        status=CoverageStatus.ACTIVE,
        required_surfaces=frozenset({RequiredSurface.TRANSCRIPT}),
        transcript_modules=("tests/test_anti_railroading_transcript_regressions.py",),
        behavioral_gauntlet_axes=(),
        manual_gauntlets=(),
        playability_scenarios=(),
        unit_contract_modules=(),
        integration_smoke_modules=(),
        notes=(
            "Deterministic unit-marked module; locks apply_final_emission_gate behavior "
            "for anti_railroading_repaired and constraint bridges - not live narration wording."
        ),
        optional_smoke_overlap=(),
    ),
    # N1: synthetic harness longitudinal continuity (session-health + analyzer JSON); tooling-only lane.
    CoverageEntry(
        feature_id="n1_longitudinal_scenario_spine_validation",
        title="N1 longitudinal continuity / scenario-spine validation (deterministic synthetic harness)",
        owner_domain="validation_layer",
        status=CoverageStatus.ACTIVE,
        required_surfaces=frozenset({RequiredSurface.INTEGRATION_SMOKE}),
        transcript_modules=(),
        behavioral_gauntlet_axes=(),
        manual_gauntlets=(),
        playability_scenarios=(),
        unit_contract_modules=(),
        integration_smoke_modules=(
            "tools/run_n1_scenario_spine_validation.py",
            "tests/test_n1_scenario_spine_cli.py",
        ),
        notes=(
            "Canonical scenario definitions live in tests/helpers/n1_scenarios.py (code-defined fixtures). "
            "CLI emits session_health.json (harness artifact) and continuity_report.json (longitudinal analyzer) "
            "as separate files; optional branch_comparison.json for shared-prefix multi-branch runs. "
            "This lane is not a playability replacement, not a runtime evaluator, and does not change game/ ownership."
        ),
        optional_smoke_overlap=(
            "tests/test_n1_analyzer_regression.py — analyzer regression depth; "
            "tests/test_n1_scenario_spine_validation.py — harness contract/unit coverage.",
        ),
    ),
)


def _dup_stripped_values(values: tuple[str, ...]) -> frozenset[str]:
    counts = Counter(v.strip() for v in values if v.strip())
    return frozenset(k for k, n in counts.items() if n > 1)


def _require_pointer(
    errors: list[str],
    entry: CoverageEntry,
    surface: RequiredSurface,
    field_name: str,
    values: tuple[str, ...],
) -> None:
    if surface not in entry.required_surfaces:
        return
    if any(not v.strip() for v in values):
        errors.append(
            f"{entry.feature_id}: {field_name} must not contain empty strings "
            f"when {surface.value!r} is required",
        )
        return
    if not values:
        errors.append(
            f"{entry.feature_id}: {field_name} must be non-empty "
            f"when {surface.value!r} is required (status={entry.status.value})",
        )


def _is_tests_py_module(p: str) -> bool:
    s = p.strip()
    return s.startswith("tests/") and s.endswith(".py")


def _is_integration_pointer(p: str) -> bool:
    s = p.strip()
    return (s.startswith("tests/") or s.startswith("tools/")) and s.endswith(".py")


def validate_entries(entries: Sequence[CoverageEntry] | None = None) -> list[str]:
    """
    Return a list of human-readable validation errors (empty if OK).

    Rules:

    - If a surface appears in ``required_surfaces``, the matching typed pointer
      field must be non-empty (all statuses).
    - ``notes`` / ``optional_smoke_overlap`` are never used to satisfy a
      required surface.
    - ``ACTIVE`` rows are additionally checked for allowlists, duplicate pointer
      values, and on-disk module paths where applicable.
    """

    rows = tuple(entries) if entries is not None else REGISTRY
    errors: list[str] = []
    seen_ids: set[str] = set()

    for entry in rows:
        if not entry.feature_id.strip():
            errors.append("feature_id must be non-empty")
        if entry.feature_id in seen_ids:
            errors.append(f"duplicate feature_id: {entry.feature_id!r}")
        seen_ids.add(entry.feature_id)

        if not entry.title.strip():
            errors.append(f"{entry.feature_id}: title must be non-empty")
        if not entry.owner_domain.strip():
            errors.append(f"{entry.feature_id}: owner_domain must be non-empty")

        if not entry.required_surfaces:
            errors.append(f"{entry.feature_id}: required_surfaces must be non-empty")

        unknown = {s for s in entry.required_surfaces if not isinstance(s, RequiredSurface)}
        if unknown:
            errors.append(f"{entry.feature_id}: unknown surfaces: {unknown!r}")

        _require_pointer(errors, entry, RequiredSurface.TRANSCRIPT, "transcript_modules", entry.transcript_modules)
        _require_pointer(
            errors,
            entry,
            RequiredSurface.BEHAVIORAL_GAUNTLET,
            "behavioral_gauntlet_axes",
            entry.behavioral_gauntlet_axes,
        )
        _require_pointer(errors, entry, RequiredSurface.MANUAL_GAUNTLET, "manual_gauntlets", entry.manual_gauntlets)
        _require_pointer(
            errors,
            entry,
            RequiredSurface.PLAYABILITY,
            "playability_scenarios",
            entry.playability_scenarios,
        )
        _require_pointer(
            errors,
            entry,
            RequiredSurface.UNIT_CONTRACT,
            "unit_contract_modules",
            entry.unit_contract_modules,
        )
        _require_pointer(
            errors,
            entry,
            RequiredSurface.INTEGRATION_SMOKE,
            "integration_smoke_modules",
            entry.integration_smoke_modules,
        )

        dup_fields: list[tuple[str, tuple[str, ...]]] = [
            ("transcript_modules", entry.transcript_modules),
            ("behavioral_gauntlet_axes", entry.behavioral_gauntlet_axes),
            ("manual_gauntlets", entry.manual_gauntlets),
            ("playability_scenarios", entry.playability_scenarios),
            ("unit_contract_modules", entry.unit_contract_modules),
            ("integration_smoke_modules", entry.integration_smoke_modules),
        ]
        for fname, vals in dup_fields:
            dups = _dup_stripped_values(vals)
            if dups:
                errors.append(
                    f"{entry.feature_id}: {fname} contains duplicate pointer(s): {sorted(dups)!r}",
                )

        if entry.status is not CoverageStatus.ACTIVE:
            continue

        # Typed allowlists and on-disk checks apply only to non-empty pointer
        # lists (required surfaces already enforce non-empty via _require_pointer).

        if entry.transcript_modules:
            for mod in entry.transcript_modules:
                if not _is_tests_py_module(mod):
                    errors.append(
                        f"{entry.feature_id}: transcript_modules entries must be tests/*.py paths; "
                        f"got {mod!r}",
                    )
                elif not (_REPO_ROOT / mod.strip()).is_file():
                    errors.append(f"{entry.feature_id}: transcript_modules path not found: {mod!r}")

        if entry.behavioral_gauntlet_axes:
            for axis in entry.behavioral_gauntlet_axes:
                a = axis.strip()
                if a not in ALLOWED_BEHAVIORAL_GAUNTLET_AXES:
                    errors.append(
                        f"{entry.feature_id}: unknown behavioral_gauntlet axis {a!r} "
                        f"(allowed: {sorted(ALLOWED_BEHAVIORAL_GAUNTLET_AXES)!r})",
                    )

        if entry.manual_gauntlets:
            for gid in entry.manual_gauntlets:
                norm = _normalize_manual_gauntlet_id(gid)
                if norm not in ALLOWED_MANUAL_GAUNTLET_IDS:
                    errors.append(
                        f"{entry.feature_id}: unknown manual_gauntlet id {gid!r} "
                        f"(allowed: g1..g12, case-insensitive)",
                    )

        if entry.playability_scenarios:
            for scen in entry.playability_scenarios:
                s = scen.strip()
                if s not in ALLOWED_PLAYABILITY_SCENARIO_IDS:
                    errors.append(
                        f"{entry.feature_id}: unknown playability_scenario id {s!r} "
                        f"(allowed: {sorted(ALLOWED_PLAYABILITY_SCENARIO_IDS)!r})",
                    )

        if entry.unit_contract_modules:
            for mod in entry.unit_contract_modules:
                if not _is_tests_py_module(mod):
                    errors.append(
                        f"{entry.feature_id}: unit_contract_modules entries must be tests/*.py paths; "
                        f"got {mod!r}",
                    )
                elif not (_REPO_ROOT / mod.strip()).is_file():
                    errors.append(f"{entry.feature_id}: unit_contract_modules path not found: {mod!r}")

        if entry.integration_smoke_modules:
            for mod in entry.integration_smoke_modules:
                if not _is_integration_pointer(mod):
                    errors.append(
                        f"{entry.feature_id}: integration_smoke_modules entries must be tests/*.py or "
                        f"tools/*.py paths; got {mod!r}",
                    )
                elif not (_REPO_ROOT / mod.strip()).is_file():
                    errors.append(f"{entry.feature_id}: integration_smoke_modules path not found: {mod!r}")

    return errors


def validate_registry() -> list[str]:
    """Validate the committed :data:`REGISTRY` (convenience wrapper)."""

    return validate_entries(REGISTRY)
