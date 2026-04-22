"""N1 scenario-spine / long-session validation contracts (test tooling only).

These types describe session-health artifacts that are intentionally separate from
playability scoring and from ``summarize_synthetic_run`` summaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict


N1_SESSION_HEALTH_ARTIFACT_KIND = "n1_session_health"
N1_SESSION_HEALTH_ARTIFACT_VERSION = 1

# Machine-readable reason codes (stable lexical ordering for emission).
N1_REASON_CONTINUITY_OK = "N1_CONTINUITY_OK"
N1_REASON_CONTINUITY_SCENE_GAP = "N1_CONTINUITY_SCENE_GAP"
N1_REASON_DRIFT_GM_TEXT_EMPTY = "N1_DRIFT_GM_TEXT_EMPTY"
N1_REASON_DRIFT_PLAYER_TEXT_EMPTY = "N1_DRIFT_PLAYER_TEXT_EMPTY"
N1_REASON_FORGOTTEN_ANCHOR = "N1_FORGOTTEN_ANCHOR"
N1_REASON_PROGRESSION_CHAIN_BROKEN = "N1_PROGRESSION_CHAIN_BROKEN"
N1_REASON_PROGRESSION_CHAIN_OK = "N1_PROGRESSION_CHAIN_OK"
N1_REASON_REVISIT_INCONSISTENT = "N1_REVISIT_INCONSISTENT"
N1_REASON_REVISIT_NOT_APPLICABLE = "N1_REVISIT_NOT_APPLICABLE"
N1_REASON_REVISIT_OK = "N1_REVISIT_OK"
N1_REASON_REFERENT_INCONSISTENT = "N1_REFERENT_INCONSISTENT"
N1_REASON_NARRATIVE_GROUNDING_DEGRADED = "N1_NARRATIVE_GROUNDING_DEGRADED"
N1_REASON_BRANCH_SHARED_FACT_VIOLATION = "N1_BRANCH_SHARED_FACT_VIOLATION"
N1_REASON_BRANCH_DIVERGENT_FINAL_SCENE_ID = "N1_BRANCH_DIVERGENT_FINAL_SCENE_ID"
N1_REASON_REVISIT_SCENE_UNSTABLE = "N1_REVISIT_SCENE_UNSTABLE"


N1FinalSessionVerdict = Literal["pass", "warn", "fail", "not_evaluated"]


class N1DeterministicRunConfigDict(TypedDict):
    """JSON-friendly, explicit deterministic configuration fingerprint."""

    seed: int
    use_fake_gm: bool
    max_turns: int
    profile_id: str
    starting_scene_id: str | None
    extra_scene_ids: tuple[str, ...]
    stall_repeat_threshold: int


@dataclass(frozen=True)
class N1DeterministicRunConfig:
    """Strongly typed deterministic runner inputs (mirrors ``run_synthetic_session`` knobs)."""

    seed: int
    use_fake_gm: bool
    max_turns: int
    profile_id: str
    starting_scene_id: str | None = None
    extra_scene_ids: tuple[str, ...] = ()
    stall_repeat_threshold: int = 3

    def to_dict(self) -> N1DeterministicRunConfigDict:
        return {
            "seed": int(self.seed),
            "use_fake_gm": bool(self.use_fake_gm),
            "max_turns": int(self.max_turns),
            "profile_id": str(self.profile_id),
            "starting_scene_id": self.starting_scene_id,
            "extra_scene_ids": tuple(str(x) for x in self.extra_scene_ids),
            "stall_repeat_threshold": int(self.stall_repeat_threshold),
        }


@dataclass(frozen=True)
class N1RevisitExpectation:
    """Declares a revisit node id and a token that should remain stable when revisited."""

    revisit_node_id: str
    consistency_token: str
    trigger_player_substrings: tuple[str, ...] = ()


@dataclass(frozen=True)
class N1ScenarioSpineDefinition:
    """Authoritative N1 spine description for a long-session validation scenario."""

    scenario_spine_id: str
    narrative_anchor_ids: tuple[str, ...] = ()
    progression_chain_step_ids: tuple[str, ...] = ()
    revisit_expectations: tuple[N1RevisitExpectation, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class N1BranchPointDefinition:
    """Branch point: shared prefix length (in player lines) before suffix divergence."""

    branch_point_id: str
    shared_prefix_turn_count: int
    description: str = ""


@dataclass(frozen=True)
class N1BranchDefinition:
    """One executable branch under a branch point (suffix lines only; prefix is shared)."""

    branch_id: str
    branch_point_id: str
    suffix_player_texts: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class N1PerTurnContinuityObservation:
    """Read-only continuity observation for a single turn (derived from harness snapshots)."""

    turn_index: int
    scene_id: str | None
    gm_text_fingerprint: str
    player_text_fingerprint: str
    anchor_hits: dict[str, bool]
    progression_hits: dict[str, bool]
    progression_chain_index_ceiling: int
    revisit_hits: dict[str, bool]


@dataclass(frozen=True)
class N1SessionHealthSummary:
    """Per-run session health (N1); not a playability aggregate."""

    run_id: str
    scenario_spine_id: str
    branch_id: str
    deterministic_config: N1DeterministicRunConfig
    turn_count: int
    per_turn_observations: tuple[N1PerTurnContinuityObservation, ...]
    continuity_verdict_ok: bool
    continuity_verdict_notes: str
    drift_flags: dict[str, bool]
    forgotten_anchor_flags: dict[str, bool]
    progression_chain_integrity_ok: bool
    progression_chain_integrity_flags: dict[str, bool]
    revisit_consistency_ok: bool
    revisit_consistency_flags: dict[str, bool]
    aggregate_issue_counts: dict[str, int]
    final_session_verdict: N1FinalSessionVerdict
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class N1BranchComparisonSummary:
    """Cross-branch comparison after shared-prefix execution."""

    scenario_spine_id: str
    branch_point_id: str
    compared_branch_ids: tuple[str, ...]
    shared_prefix_turn_count: int
    shared_prefix_fingerprint: str
    per_branch_suffix_fingerprint: dict[str, str]
    per_branch_final_scene_id: dict[str, str | None]
    divergence_detected: bool
    reason_codes: tuple[str, ...]


class N1SessionHealthArtifactDict(TypedDict):
    """Serialized session-health artifact (stable keys via harness normalizer)."""

    artifact_kind: str
    artifact_version: int
    run_id: str
    scenario_spine_id: str
    branch_id: str
    deterministic_config: dict[str, Any]
    turn_count: int
    per_turn_observations: list[dict[str, Any]]
    continuity_verdict_ok: bool
    continuity_verdict_notes: str
    drift_flags: dict[str, bool]
    forgotten_anchor_flags: dict[str, bool]
    progression_chain_integrity_ok: bool
    progression_chain_integrity_flags: dict[str, bool]
    revisit_consistency_ok: bool
    revisit_consistency_flags: dict[str, bool]
    aggregate_issue_counts: dict[str, int]
    final_session_verdict: str
    reason_codes: list[str]
