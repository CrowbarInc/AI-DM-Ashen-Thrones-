"""Deterministic N1 scenario-spine fixtures for analyzer-driven regression tests (test-only)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from tests.helpers.n1_continuity_analysis import (
    N1LongitudinalContinuityReport,
    analyze_n1_longitudinal_continuity,
)
from tests.helpers.n1_scenario_spine_contract import (
    N1BranchDefinition,
    N1BranchPointDefinition,
    N1DeterministicRunConfig,
    N1RevisitExpectation,
    N1ScenarioSpineDefinition,
    N1SessionHealthSummary,
)
from tests.helpers.n1_scenario_spine_harness import (
    build_n1_scenario_spine_definition,
    compute_n1_session_health_summary,
    execute_n1_spine_branch_with_shared_prefix,
)
from tests.helpers.synthetic_fake_gm import make_deterministic_fake_responder
from tests.helpers.synthetic_types import SyntheticProfile, SyntheticRunResult


def make_n1_scripted_fake_gm_responder(
    script: Mapping[str, tuple[str, str | None]],
) -> Callable[[str], dict[str, Any]]:
    """Map exact latest player lines to GM-facing text and optional scene_id (deterministic)."""

    table = {str(k).strip(): (str(text), sid) for k, (text, sid) in script.items()}
    default = make_deterministic_fake_responder()

    def _inner(latest_player_text: str) -> dict[str, Any]:
        key = str(latest_player_text or "").strip()
        if key in table:
            text, scene = table[key]
            payload: dict[str, Any] = {
                "ok": True,
                "source": "n1_scripted_fixture",
                "player_facing_text": text,
            }
            if isinstance(scene, str) and scene.strip():
                payload["scene_id"] = scene.strip()
            return payload
        return default(key)

    return _inner


def n1_player_texts_from_run(run: SyntheticRunResult) -> tuple[str, ...]:
    return tuple(str(v.get("player_text") or "") for v in (run.turn_views or ()))


@dataclass(frozen=True)
class N1AnalyzedScenarioRun:
    run_result: SyntheticRunResult
    summary: N1SessionHealthSummary
    longitudinal_report: N1LongitudinalContinuityReport


# Shared linear branch point for code-defined fixtures (matches analyzer regression tests).
N1_LINEAR_BRANCH_POINT = N1BranchPointDefinition(
    branch_point_id="n1_linear_bp",
    shared_prefix_turn_count=0,
    description="linear",
)


@dataclass(frozen=True)
class N1RegisteredScenario:
    """CLI/registry metadata for a deterministic N1 fixture (single source for scenario ids)."""

    scenario_id: str
    description: str
    spine: N1ScenarioSpineDefinition
    branch_point: N1BranchPointDefinition
    shared_prefix_player_texts: tuple[str, ...]
    branches: tuple[N1BranchDefinition, ...]
    supports_compare_branches: bool

    def min_scripted_player_turns(self) -> int:
        """Minimum player-line count across branches (prefix + suffix per branch)."""
        k = len(self.shared_prefix_player_texts)
        return max(k + len(b.suffix_player_texts) for b in self.branches)


def validate_n1_registered_scenario_bundle(specs: tuple[N1RegisteredScenario, ...]) -> None:
    """Fail fast on duplicate ids or inconsistent branch metadata (registry guardrails)."""

    ids = [s.scenario_id for s in specs]
    if len(ids) != len(set(ids)):
        dup = sorted({x for x in ids if ids.count(x) > 1})
        raise ValueError(f"duplicate N1 scenario_id values in registry bundle: {dup!r}")
    for spec in specs:
        bp_id = spec.branch_point.branch_point_id
        pfx_n = len(spec.shared_prefix_player_texts)
        need_pfx = int(spec.branch_point.shared_prefix_turn_count)
        if pfx_n != need_pfx:
            raise ValueError(
                f"scenario {spec.scenario_id!r}: shared_prefix_player_texts has length {pfx_n} "
                f"but branch_point.shared_prefix_turn_count is {need_pfx!r}",
            )
        seen_branch: set[str] = set()
        for b in spec.branches:
            if b.branch_id in seen_branch:
                raise ValueError(f"scenario {spec.scenario_id!r}: duplicate branch_id {b.branch_id!r}")
            seen_branch.add(b.branch_id)
            if b.branch_point_id != bp_id:
                raise ValueError(
                    f"scenario {spec.scenario_id!r}: branch {b.branch_id!r} has branch_point_id "
                    f"{b.branch_point_id!r} but scenario branch_point is {bp_id!r}",
                )
        if spec.supports_compare_branches:
            if len(spec.branches) < 2:
                raise ValueError(
                    f"scenario {spec.scenario_id!r}: supports_compare_branches=True requires "
                    f"at least 2 branches (got {len(spec.branches)})",
                )
        elif len(spec.branches) != 1:
            raise ValueError(
                f"scenario {spec.scenario_id!r}: non-branching scenarios must define exactly one "
                f"synthetic branch (got {len(spec.branches)}); use supports_compare_branches for forks",
            )


def n1_registered_scenarios() -> tuple[N1RegisteredScenario, ...]:
    """All code-defined N1 scenarios, sorted by ``scenario_id`` (deterministic CLI ordering)."""

    linear_main = (
        N1BranchDefinition(
            branch_id="n1_main",
            branch_point_id=N1_LINEAR_BRANCH_POINT.branch_point_id,
            suffix_player_texts=N1_ANCHOR_PERSISTENCE_LINES,
        ),
    )
    scenarios: tuple[N1RegisteredScenario, ...] = (
        N1RegisteredScenario(
            scenario_id="n1_anchor_persistence",
            description="Long linear session: ledger anchor stays foregrounded every turn (fixture).",
            spine=N1_SPINE_ANCHOR_PERSISTENCE,
            branch_point=N1_LINEAR_BRANCH_POINT,
            shared_prefix_player_texts=(),
            branches=linear_main,
            supports_compare_branches=False,
        ),
        N1RegisteredScenario(
            scenario_id="n1_branch_divergence",
            description="Shared-prefix fork with divergent final scene ids under scripted fake-GM (fixture).",
            spine=N1_SPINE_BRANCH,
            branch_point=N1_BRANCH_POINT_MAIN,
            shared_prefix_player_texts=N1_BRANCH_PREFIX_LINES,
            branches=tuple(sorted((N1_BRANCH_LEFT, N1_BRANCH_RIGHT), key=lambda b: b.branch_id)),
            supports_compare_branches=True,
        ),
        N1RegisteredScenario(
            scenario_id="n1_investigation_revisit",
            description="Two explicit revisits with stable map token and wax_seal consistency (fixture).",
            spine=N1_SPINE_REVISIT,
            branch_point=N1_LINEAR_BRANCH_POINT,
            shared_prefix_player_texts=(),
            branches=(
                N1BranchDefinition(
                    branch_id="n1_main",
                    branch_point_id=N1_LINEAR_BRANCH_POINT.branch_point_id,
                    suffix_player_texts=N1_REVISIT_LINES,
                ),
            ),
            supports_compare_branches=False,
        ),
        N1RegisteredScenario(
            scenario_id="n1_progression_chain",
            description="Ordered progression-chain steps across a short linear session (fixture).",
            spine=N1_SPINE_PROGRESSION,
            branch_point=N1_LINEAR_BRANCH_POINT,
            shared_prefix_player_texts=(),
            branches=(
                N1BranchDefinition(
                    branch_id="n1_main",
                    branch_point_id=N1_LINEAR_BRANCH_POINT.branch_point_id,
                    suffix_player_texts=N1_PROGRESSION_LINES,
                ),
            ),
            supports_compare_branches=False,
        ),
    )
    out = tuple(sorted(scenarios, key=lambda s: s.scenario_id))
    validate_n1_registered_scenario_bundle(out)
    return out


def n1_registered_scenario_ids() -> tuple[str, ...]:
    return tuple(s.scenario_id for s in n1_registered_scenarios())


def get_n1_registered_scenario(scenario_id: str) -> N1RegisteredScenario:
    sid = str(scenario_id).strip()
    if not sid:
        raise ValueError("scenario_id must be a non-empty string (after stripping whitespace)")
    for s in n1_registered_scenarios():
        if s.scenario_id == sid:
            return s
    known = ", ".join(n1_registered_scenario_ids())
    raise ValueError(f"unknown N1 scenario_id {scenario_id!r}; registered: {known}")


def run_n1_scenario_and_analyze(
    *,
    spine: N1ScenarioSpineDefinition,
    branch_point: N1BranchPointDefinition,
    branch: N1BranchDefinition,
    profile: SyntheticProfile,
    deterministic_config: N1DeterministicRunConfig,
    shared_prefix_player_texts: tuple[str, ...],
    fake_gm_responder: Callable[[str], dict[str, Any]],
    synthetic_runner_kwargs: dict[str, Any] | None = None,
) -> N1AnalyzedScenarioRun:
    """Execute one N1 branch via the spine harness, summarize, and run longitudinal analysis.

    Longitudinal analysis receives ``player_texts_by_turn`` keyed by each turn view's
    ``turn_index`` (falling back to enumeration order only when ``turn_index`` is absent).
    """
    extra = dict(synthetic_runner_kwargs or {})
    extra["fake_gm_responder"] = fake_gm_responder
    run = execute_n1_spine_branch_with_shared_prefix(
        spine=spine,
        branch_point=branch_point,
        branch=branch,
        profile=profile,
        deterministic_config=deterministic_config,
        shared_prefix_player_texts=shared_prefix_player_texts,
        synthetic_runner_kwargs=extra,
    )
    views = run.turn_views or ()
    if not views:
        raise ValueError(
            "run_n1_scenario_and_analyze produced zero turn_views; "
            "check shared_prefix_player_texts + branch.suffix_player_texts and synthetic runner wiring.",
        )
    summary = compute_n1_session_health_summary(
        spine=spine,
        branch=branch,
        run_result=run,
        deterministic_config=deterministic_config,
    )
    by_turn = {int(v.get("turn_index", idx)): str(v.get("player_text") or "") for idx, v in enumerate(views)}
    report = analyze_n1_longitudinal_continuity(spine=spine, summary=summary, player_texts_by_turn=by_turn)
    return N1AnalyzedScenarioRun(run_result=run, summary=summary, longitudinal_report=report)


# --- Shared scripted GM table (keys are exact player lines; values are GM text + optional scene_id) ---

N1_SCRIPTED_GM_TABLE: dict[str, tuple[str, str | None]] = {
    # Anchor persistence: anchor present every turn; stable scene to avoid referent heuristic noise.
    "n1|ap|t00": ("Establishing n1_anchor_ledger in the record.", "n1_scene_ap"),
    "n1|ap|t01": ("The n1_anchor_ledger remains in view as you advance.", "n1_scene_ap"),
    "n1|ap|t02": ("Still tracking n1_anchor_ledger without contradiction.", "n1_scene_ap"),
    "n1|ap|t03": ("The n1_anchor_ledger stays foregrounded in the fiction.", "n1_scene_ap"),
    "n1|ap|t04": ("Mid-session beat: n1_anchor_ledger is still true.", "n1_scene_ap"),
    "n1|ap|t05": ("Late session: n1_anchor_ledger persists in the tail.", "n1_scene_ap"),
    "n1|ap|t06": ("Closing pressure: n1_anchor_ledger remains consistent.", "n1_scene_ap"),
    "n1|ap|t07": ("Final stance: n1_anchor_ledger is still acknowledged.", "n1_scene_ap"),
    # Investigation / revisit: two explicit revisits, same scene, token present on triggered GM lines.
    "n1|rv|t00": ("You approach the approach lane; n1_map_ref is noted.", "n1_scene_hall"),
    "n1|rv|t01": ("You study details; n1_map_ref stays visible.", "n1_scene_hall"),
    "n1|rv|t02": ("You return to n1 postern and see wax_seal on the orders.", "n1_scene_hall"),
    "n1|rv|t03": ("Between revisits, n1_map_ref remains on the table.", "n1_scene_hall"),
    "n1|rv|t04": ("You press forward; n1_map_ref is still accurate.", "n1_scene_hall"),
    "n1|rv|t05": ("You double-check bearings; n1_map_ref holds.", "n1_scene_hall"),
    "n1|rv|t06": ("You return to n1 postern again; wax_seal still matches the orders.", "n1_scene_hall"),
    # Progression chain: ordered steps across turns.
    "n1|pg|t00": ("Objective n1_chain_a is clearly achieved this turn.", "n1_scene_pg"),
    "n1|pg|t01": ("With n1_chain_a done, n1_chain_b locks into place.", "n1_scene_pg"),
    "n1|pg|t02": ("After n1_chain_b, the operation is coherent end-to-end.", "n1_scene_pg"),
    # Branching: shared prefix establishes shared anchor; suffix picks divergent finals.
    "n1|br|p00": ("Shared prefix beat: n1_branch_fact is established for everyone.", "n1_scene_fork"),
    "n1|br|p01": ("Shared prefix continues: n1_branch_fact remains uncontested.", "n1_scene_fork"),
    "n1|br|left": ("Left fork resolves; n1_branch_fact stays true in scene_left_final.", "n1_scene_left_final"),
    "n1|br|right": ("Right fork resolves; n1_branch_fact stays true in scene_right_final.", "n1_scene_right_final"),
}


def n1_fixture_fake_gm_responder() -> Callable[[str], dict[str, Any]]:
    return make_n1_scripted_fake_gm_responder(N1_SCRIPTED_GM_TABLE)


# --- Spine fixtures ---

N1_SPINE_ANCHOR_PERSISTENCE = build_n1_scenario_spine_definition(
    scenario_spine_id="n1_fixture_anchor_persistence",
    narrative_anchor_ids=("n1_anchor_ledger",),
    metadata={"fixture_role": "anchor_persistence"},
)

N1_SPINE_REVISIT = build_n1_scenario_spine_definition(
    scenario_spine_id="n1_fixture_revisit",
    narrative_anchor_ids=("n1_map_ref",),
    revisit_expectations=(
        N1RevisitExpectation(
            revisit_node_id="n1_postern",
            consistency_token="wax_seal",
            trigger_player_substrings=("return to n1 postern",),
        ),
    ),
    metadata={"fixture_role": "revisit"},
)

N1_SPINE_PROGRESSION = build_n1_scenario_spine_definition(
    scenario_spine_id="n1_fixture_progression_chain",
    progression_chain_step_ids=("n1_chain_a", "n1_chain_b"),
    metadata={"fixture_role": "progression_chain"},
)

N1_SPINE_BRANCH = build_n1_scenario_spine_definition(
    scenario_spine_id="n1_fixture_branch",
    narrative_anchor_ids=("n1_branch_fact",),
    metadata={"fixture_role": "branch"},
)


N1_ANCHOR_PERSISTENCE_LINES: tuple[str, ...] = tuple(f"n1|ap|t0{i}" for i in range(8))
N1_REVISIT_LINES: tuple[str, ...] = (
    "n1|rv|t00",
    "n1|rv|t01",
    "n1|rv|t02",
    "n1|rv|t03",
    "n1|rv|t04",
    "n1|rv|t05",
    "n1|rv|t06",
)
N1_PROGRESSION_LINES: tuple[str, ...] = ("n1|pg|t00", "n1|pg|t01", "n1|pg|t02")

N1_BRANCH_POINT_MAIN = N1BranchPointDefinition(
    branch_point_id="n1_fixture_fork",
    shared_prefix_turn_count=2,
    description="shared prefix then divergent suffix",
)
N1_BRANCH_PREFIX_LINES: tuple[str, ...] = ("n1|br|p00", "n1|br|p01")
N1_BRANCH_LEFT = N1BranchDefinition(
    branch_id="n1_branch_left",
    branch_point_id=N1_BRANCH_POINT_MAIN.branch_point_id,
    suffix_player_texts=("n1|br|left",),
)
N1_BRANCH_RIGHT = N1BranchDefinition(
    branch_id="n1_branch_right",
    branch_point_id=N1_BRANCH_POINT_MAIN.branch_point_id,
    suffix_player_texts=("n1|br|right",),
)


def n1_default_fixture_deterministic_config(profile: SyntheticProfile) -> N1DeterministicRunConfig:
    return N1DeterministicRunConfig(
        seed=20260422,
        use_fake_gm=True,
        max_turns=32,
        profile_id=profile.profile_id,
        starting_scene_id=None,
        extra_scene_ids=("n1_scene_ap", "n1_scene_fork"),
        stall_repeat_threshold=3,
    )
