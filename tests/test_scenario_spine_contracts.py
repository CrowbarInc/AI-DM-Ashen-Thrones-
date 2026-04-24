"""Contract tests for ``game.scenario_spine`` (deterministic, no API keys)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from game.scenario_spine import (
    ContinuityAnchor,
    ProgressionAnchor,
    ReferentAnchor,
    ScenarioBranch,
    ScenarioCheckpoint,
    ScenarioSpine,
    ScenarioTurn,
    scenario_spine_from_dict,
    scenario_spine_to_dict,
    validate_scenario_spine_definition,
)

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "data" / "validation" / "scenario_spines" / "frontier_gate_long_session.json"


def _minimal_valid_spine(*, smoke_only: bool = False, branch_turn_counts: tuple[int, ...] = (20,)) -> ScenarioSpine:
    turns_main = tuple(
        ScenarioTurn(turn_id=f"t_{i:02d}", player_prompt=f"line {i}") for i in range(branch_turn_counts[0])
    )
    branches: list[ScenarioBranch] = [
        ScenarioBranch(branch_id="main", label="Main", turns=turns_main),
    ]
    for idx, n in enumerate(branch_turn_counts[1:], start=1):
        branches.append(
            ScenarioBranch(
                branch_id=f"extra_{idx}",
                label=f"Extra {idx}",
                turns=tuple(ScenarioTurn(turn_id=f"x{idx}_{i:02d}", player_prompt=f"x {i}") for i in range(n)),
            ),
        )
    return ScenarioSpine(
        spine_id="test_spine",
        title="Test",
        smoke_only=smoke_only,
        fixed_start_state={"scene_id": "test_scene", "seed": 1},
        branches=tuple(branches),
        continuity_anchors=(
            ContinuityAnchor(anchor_id="ca_loc", anchor_kind="location", description="loc"),
        ),
        referent_anchors=(ReferentAnchor(anchor_id="ref_a", label="A", description="d"),),
        progression_anchors=(ProgressionAnchor(anchor_id="prog_a", description="p", expected_change_summary="w"),),
        checkpoints=(
            ScenarioCheckpoint(
                checkpoint_id="cp1",
                label="c",
                referenced_anchor_ids=("ca_loc", "ref_a"),
            ),
        ),
    )


def test_frontier_gate_fixture_loads_and_validates() -> None:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    spine = scenario_spine_from_dict(raw)
    errs = validate_scenario_spine_definition(spine)
    assert errs == []
    assert spine.spine_id == "frontier_gate_long_session"
    assert len(spine.branches) == 3
    by_id = {b.branch_id: b for b in spine.branches}
    assert len(by_id["branch_social_inquiry"].turns) >= 25
    assert scenario_spine_from_dict(scenario_spine_to_dict(spine)).spine_id == spine.spine_id


def test_duplicate_turn_ids_within_branch_rejected() -> None:
    spine = ScenarioSpine(
        spine_id="dup_turn",
        fixed_start_state={"k": 1},
        branches=(
            ScenarioBranch(
                branch_id="b1",
                label="B",
                turns=(
                    ScenarioTurn(turn_id="same", player_prompt="a"),
                    ScenarioTurn(turn_id="same", player_prompt="b"),
                ),
            ),
        ),
        smoke_only=True,
    )
    errs = validate_scenario_spine_definition(spine)
    assert any("duplicate turn_id" in e for e in errs)


def test_checkpoint_unknown_anchor_id_rejected() -> None:
    spine = ScenarioSpine(
        spine_id="bad_cp",
        fixed_start_state={"k": 1},
        branches=(
            ScenarioBranch(
                branch_id="b1",
                label="B",
                turns=tuple(ScenarioTurn(turn_id=f"t{i}", player_prompt=str(i)) for i in range(20)),
            ),
        ),
        continuity_anchors=(
            ContinuityAnchor(anchor_id="ca1", anchor_kind="location", description="d"),
        ),
        checkpoints=(
            ScenarioCheckpoint(
                checkpoint_id="c1",
                label="l",
                referenced_anchor_ids=("ca1", "missing_anchor"),
            ),
        ),
    )
    errs = validate_scenario_spine_definition(spine)
    assert any("unknown anchor_id" in e and "missing_anchor" in e for e in errs)


def test_long_session_minimum_enforced_without_smoke_only() -> None:
    spine = _minimal_valid_spine(smoke_only=False, branch_turn_counts=(5, 3))
    errs = validate_scenario_spine_definition(spine)
    assert any(">= 20 turns" in e for e in errs)


def test_smoke_only_allows_short_branches() -> None:
    spine = _minimal_valid_spine(smoke_only=True, branch_turn_counts=(3,))
    errs = validate_scenario_spine_definition(spine)
    assert errs == []


def test_empty_branches_rejected() -> None:
    spine = ScenarioSpine(
        spine_id="no_br",
        fixed_start_state={"k": 1},
        branches=(),
        smoke_only=True,
    )
    errs = validate_scenario_spine_definition(spine)
    assert any("branches must be non-empty" in e for e in errs)


def test_empty_fixed_start_state_rejected() -> None:
    spine = ScenarioSpine(
        spine_id="no_fss",
        fixed_start_state={},
        branches=(
            ScenarioBranch(branch_id="b1", label="B", turns=(ScenarioTurn("t1", "p"),)),
        ),
        smoke_only=True,
    )
    errs = validate_scenario_spine_definition(spine)
    assert any("fixed_start_state" in e for e in errs)


def test_branch_id_collision_rejected() -> None:
    spine = ScenarioSpine(
        spine_id="collide",
        fixed_start_state={"k": 1},
        branches=(
            ScenarioBranch("same", "A", (ScenarioTurn("a1", "p"),)),
            ScenarioBranch("same", "B", (ScenarioTurn("b1", "p"),)),
        ),
        smoke_only=True,
    )
    errs = validate_scenario_spine_definition(spine)
    assert any("duplicate branch_id" in e for e in errs)
