"""BI-8 golden replay ownership boundary guards (import-light; no pytest).

Golden replay is a consumer/bridge, not a subsystem legality owner. Enforced by
``test_bi8_golden_replay_ownership_boundary_is_locked`` in
``tests/test_ownership_registry.py``.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import AbstractSet, Final, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Cycle BI-8: golden replay is a consumer/bridge, not a subsystem legality owner.
BI8_GOLDEN_REPLAY_TARGETS: Final[tuple[str, ...]] = (
    "tests/test_golden_replay.py",
    "tests/helpers/golden_replay.py",
    "tests/helpers/golden_replay_api.py",
)
BI8_GOLDEN_REPLAY_OWNED_EXPORTS: Final[frozenset[str]] = frozenset(
    {
        "run_golden_replay",
        "assert_golden_turn_observation",
        "assert_protected_golden_turn_observation",
        "assert_golden_replay_profile_bundle",
        "format_golden_replay_debug",
        "observed_turn_from_payload",
        "protected_social_speaker_observation_expectation",
        "protected_structural_expectation",
        "render_long_session_replay_summary_markdown",
        "summarize_long_session_replay_observations",
    }
)
BI8_GOLDEN_REPLAY_FORBIDDEN_EXPORTS: Final[frozenset[str]] = frozenset(
    {
        "protected_no_scaffold_expectation",
        "protected_route_expectation",
        "protected_source_expectation",
        "protected_unavailable_expectation",
        "protected_social_structural_base",
        "protected_social_directed_question_expectation",
        "protected_social_trace_target_expectation",
        "protected_social_vocative_canonical_entry_expectation",
        "protected_social_supplemental_structural_expectation",
    }
)
BI8_GOLDEN_REPLAY_FORBIDDEN_SOURCE_FRAGMENTS: Final[Mapping[str, str]] = {
    "PROTECTED_SOCIAL_RESOLUTION_KINDS": "route enum legality",
    "PROTECTED_SOCIAL_ROUTE_KINDS": "route enum legality",
    "PROTECTED_DIALOGUE_TRACE_ROUTES": "route enum legality",
    "PROTECTED_VOCATIVE_CANONICAL_ENTRY": "speaker/vocative legality",
    "protected_social_structural_base": "speaker legality",
    "protected_social_directed_question_expectation": "speaker legality",
    "protected_social_trace_target_expectation": "speaker legality",
    "protected_social_vocative_canonical_entry_expectation": "speaker/vocative legality",
    "protected_social_supplemental_structural_expectation": "speaker/route legality",
    "successful_opening_observed_fields": "opening/fallback owner-bucket semantics",
    "OPENING_FALLBACK_OWNER_": "opening/fallback owner-bucket semantics",
    "OPENING_FALLBACK_AUTHORSHIP": "opening fallback authorship semantics",
    "FRONTIER_GATE_SOCIAL_INQUIRY_STABILITY_PROFILE": "stability threshold meaning",
    "FRONTIER_GATE_SOCIAL_INQUIRY_LINEAGE_PROFILE": "lineage threshold meaning",
    "FRONTIER_GATE_SOCIAL_INQUIRY_FALLBACK_ESCALATION_PROFILE": "fallback escalation threshold meaning",
    "FRONTIER_GATE_RESUME_STABILITY_PROFILE": "stability threshold meaning",
    "FRONTIER_GATE_RESUME_LINEAGE_PROFILE": "lineage threshold meaning",
    "FRONTIER_GATE_RESUME_FALLBACK_ESCALATION_PROFILE": "fallback escalation threshold meaning",
    "FRONTIER_GATE_DIRECT_INTRUSION_STABILITY_PROFILE": "stability threshold meaning",
    "FRONTIER_GATE_DIRECT_INTRUSION_LINEAGE_PROFILE": "lineage threshold meaning",
    "FRONTIER_GATE_DIRECT_INTRUSION_FALLBACK_ESCALATION_PROFILE": "fallback escalation threshold meaning",
}
BI8_GOLDEN_REPLAY_DOCUMENTATION_PHRASES: Final[tuple[str, ...]] = (
    "replay orchestration",
    "observation consumption",
    "protected assertion bridge diagnostics",
    "long-session",
    "speaker legality",
    "route enum legality",
    "final emission gate orchestration",
    "opening/fallback owner-bucket semantics",
    "sanitizer phrase legality",
    "dashboard/classifier",
    "stability/taxonomy threshold",
)


def _module_all_exports(source: str) -> frozenset[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
            continue
        value = ast.literal_eval(node.value)
        assert isinstance(value, tuple), "__all__ must be a literal tuple"
        assert all(isinstance(item, str) for item in value), "__all__ entries must be strings"
        return frozenset(value)
    raise AssertionError("module must define literal __all__")


def load_bi8_golden_replay_target_sources(
    repo_root: Path | None = None,
    *,
    targets: tuple[str, ...] = BI8_GOLDEN_REPLAY_TARGETS,
) -> dict[str, str]:
    """Return source text for each BI-8 governed golden replay path."""
    root = _REPO_ROOT if repo_root is None else repo_root
    return {
        rel_path: (root / rel_path).read_text(encoding="utf-8")
        for rel_path in targets
    }


def parse_bi8_golden_replay_api_exports(
    target_sources: Mapping[str, str],
    *,
    api_path: str = "tests/helpers/golden_replay_api.py",
) -> frozenset[str]:
    """Return ``__all__`` exports from the golden replay API facade."""
    return _module_all_exports(target_sources[api_path])


def collect_bi8_golden_replay_documentation_phrase_violations(
    combined_docs: str,
    *,
    phrases: tuple[str, ...] = BI8_GOLDEN_REPLAY_DOCUMENTATION_PHRASES,
) -> list[str]:
    """Return documentation phrase violations for BI-8 ownership boundary notes."""
    lowered = combined_docs.lower()
    return [
        f"BI-8 golden replay ownership note missing {phrase!r}"
        for phrase in phrases
        if phrase not in lowered
    ]


def collect_bi8_golden_replay_owned_export_violations(
    api_exports: AbstractSet[str],
    *,
    owned_exports: frozenset[str] = BI8_GOLDEN_REPLAY_OWNED_EXPORTS,
) -> list[str]:
    """Return violations when the golden replay API facade drops owned exports."""
    missing = owned_exports - frozenset(api_exports)
    if not missing:
        return []
    return [f"golden replay API missing owned exports: {sorted(missing)!r}"]


def collect_bi8_golden_replay_forbidden_export_violations(
    api_exports: AbstractSet[str],
    *,
    forbidden_exports: frozenset[str] = BI8_GOLDEN_REPLAY_FORBIDDEN_EXPORTS,
) -> list[str]:
    """Return violations when the golden replay API exports subsystem legality presets."""
    found = forbidden_exports & frozenset(api_exports)
    if not found:
        return []
    return [
        "golden replay API must not export subsystem legality helper presets: "
        f"{sorted(found)!r}"
    ]


def collect_bi8_golden_replay_forbidden_source_fragment_violations(
    helper_api_source: str,
    *,
    forbidden_fragments: Mapping[str, str] = BI8_GOLDEN_REPLAY_FORBIDDEN_SOURCE_FRAGMENTS,
) -> list[str]:
    """Return violations when golden replay helper/API re-owns subsystem legality details."""
    found = {
        fragment: reason
        for fragment, reason in forbidden_fragments.items()
        if fragment in helper_api_source
    }
    if not found:
        return []
    return [
        "golden replay helper/API must not re-own subsystem legality details: "
        f"{found!r}"
    ]
