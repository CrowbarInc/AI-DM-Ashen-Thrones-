"""CL5 semantic mutation projection policy locks."""
from __future__ import annotations

import json

import pytest

from tests.helpers.golden_replay_fixtures import minimal_turn_payload
from tests.helpers.golden_replay_projection import (
    project_semantic_mutation_summary as facade_project_semantic_mutation_summary,
    project_turn_observation,
)
from tests.helpers.golden_replay_projection_extractors import (
    project_semantic_mutation_summary as extractor_project_semantic_mutation_summary,
)
from tests.helpers.golden_replay_projection_semantic import project_semantic_mutation_summary

pytestmark = pytest.mark.unit


_SEMANTIC_TRACE = {
    "first_semantic_mutation_bucket": "narrative_authenticity",
    "first_semantic_mutation_source": "stage_diff",
    "first_semantic_mutation_checkpoint_id": "checkpoint-7",
    "first_semantic_mutation_sequence": 3,
    "semantic_mutation_changed_count": 2,
    "semantic_mutation_unknown_count": 1,
    "semantic_mutation_risk_score": 40,
    "semantic_mutation_risk_band": "medium",
    "semantic_mutation_trace_complete": False,
    "trace_continuity": None,
    "semantic_mutation_trace": [{"sequence": 3}],
    "first_semantic_mutation_owner": "not projected by replay summary",
}


def test_cl5_semantic_summary_projection_shape_locked() -> None:
    expected = {
        "first_semantic_mutation_bucket": "narrative_authenticity",
        "first_semantic_mutation_source": "stage_diff",
        "first_semantic_mutation_checkpoint_id": "checkpoint-7",
        "first_semantic_mutation_sequence": 3,
        "semantic_mutation_changed_count": 2,
        "semantic_mutation_unknown_count": 1,
        "semantic_mutation_risk_score": 40,
        "semantic_mutation_risk_band": "medium",
        "semantic_mutation_trace_complete": False,
        "trace_continuity": None,
    }
    assert project_semantic_mutation_summary(_SEMANTIC_TRACE) == expected
    assert json.dumps(project_semantic_mutation_summary(_SEMANTIC_TRACE), sort_keys=True) == json.dumps(
        expected,
        sort_keys=True,
    )


def test_cl5_semantic_summary_compatibility_imports_are_same_callable() -> None:
    assert extractor_project_semantic_mutation_summary is project_semantic_mutation_summary
    assert facade_project_semantic_mutation_summary is project_semantic_mutation_summary


def test_cl5_semantic_summary_ignores_missing_or_none_optional_values() -> None:
    assert project_semantic_mutation_summary(None) == {}
    assert project_semantic_mutation_summary({"semantic_mutation_trace_complete": None}) == {
        "semantic_mutation_trace_complete": None,
    }
    assert project_semantic_mutation_summary(
        {
            "first_semantic_mutation_bucket": None,
            "semantic_mutation_changed_count": 0,
            "trace_continuity": False,
        }
    ) == {
        "semantic_mutation_changed_count": 0,
        "trace_continuity": False,
    }


def test_cl5_project_turn_observation_semantic_output_locked() -> None:
    observed = project_turn_observation(
        {
            **minimal_turn_payload(
                scenario_id="cl5_semantic_projection",
                gm_text="The road bends toward the gate.",
            ),
            "semantic_mutation_trace": _SEMANTIC_TRACE,
        }
    )
    summary = project_semantic_mutation_summary(_SEMANTIC_TRACE)
    assert {key: observed.get(key) for key in summary} == summary
    assert "semantic_mutation_trace" not in observed
    assert "first_semantic_mutation_owner" not in observed
