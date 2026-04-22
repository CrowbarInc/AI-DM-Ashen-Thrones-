"""Unit tests for :mod:`game.content_lint` (author-time deterministic pipeline)."""
from __future__ import annotations

import pytest

from game import content_lint
from game import validation
from game.content_lint import (
    lint_all_content,
    lint_scene_clue_integrity,
    lint_scene_graph_connectivity,
    lint_scene_heuristic_warnings,
    lint_scene_interactables,
)


pytestmark = pytest.mark.unit


def _minimal_scene(scene_id: str) -> dict:
    return {
        "scene": {
            "id": scene_id,
            "location": "Somewhere",
            "summary": "You smell rain on stone; the wind carries smoke from the quay.",
            "visible_facts": ["A door stands open."],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "interactables": [],
            "actions": [],
        }
    }


def test_lint_all_separates_errors_and_warnings():
    """Strict issues are errors; heuristics and graph reachability surface as warnings."""
    a = _minimal_scene("hub")
    b = _minimal_scene("island")
    b["scene"]["exits"] = []  # no way in from hub in this map
    report = lint_all_content({"hub": a, "island": b}, graph_seed_scene_ids=["hub"])
    codes = {(m.severity, m.code) for m in report.messages}
    assert ("warning", "graph.unreachable_scene") in codes
    assert report.warning_count >= 1
    assert report.error_count == 0


def test_exit_unknown_target_is_error():
    a = _minimal_scene("a")
    a["scene"]["exits"] = [{"label": "Nowhere", "target_scene_id": "missing"}]
    report = lint_all_content({"a": a})
    errs = [m for m in report.messages if m.code == "exit.unknown_target"]
    assert len(errs) == 1
    assert errs[0].severity == "error"
    assert report.ok is False


def test_duplicate_interactable_error():
    a = _minimal_scene("a")
    a["scene"]["interactables"] = [
        {"id": "x", "type": "investigate"},
        {"id": "x", "type": "investigate"},
    ]
    report = lint_all_content({"a": a})
    dup = [m for m in report.messages if m.code == "interactable.duplicate_id"]
    assert len(dup) == 1
    assert dup[0].severity == "error"


def test_clue_duplicate_structured_id_error():
    a = _minimal_scene("a")
    a["scene"]["discoverable_clues"] = [
        {"id": "c1", "text": "First"},
        {"id": "c1", "text": "Duplicate id"},
    ]
    report = lint_all_content({"a": a})
    dups = [m for m in report.messages if m.code == "clue.duplicate_id"]
    assert len(dups) == 1


def test_non_investigate_reveals_clue_warning_when_unresolved():
    a = _minimal_scene("a")
    a["scene"]["discoverable_clues"] = ["Known clue text"]
    a["scene"]["interactables"] = [
        {"id": "obj", "type": "use", "reveals_clue": "not_a_real_ref"},
    ]
    msgs = lint_scene_clue_integrity(a, "a", world=None)
    warn = [m for m in msgs if m.code == "interactable.clue_ref_non_investigate"]
    assert len(warn) == 1
    assert warn[0].severity == "warning"


def test_collect_matches_validate_scene_first_issue():
    """First collected issue must match what fail-fast validate_scene raises."""
    a = _minimal_scene("room")
    a["scene"]["location"] = ""
    a["scene"]["exits"] = [{"label": "Bad", "target_scene_id": "nope"}]
    collected = validation.collect_scene_validation_issues(a, "room", {"room"})
    assert len(collected) >= 2
    with pytest.raises(validation.SceneValidationError) as exc:
        validation.validate_scene(a, "room", {"room"})
    assert str(exc.value) == str(collected[0])


def test_lint_scene_interactables_filters_strict_subset():
    a = _minimal_scene("a")
    a["scene"]["interactables"] = [{"id": "i", "type": "investigate"}]
    msgs = lint_scene_interactables(a, "a", {"a"})
    assert msgs == []


def test_graph_level_aggregation_multiple_scenes():
    """Graph pass runs across the full known_scene_ids registry."""
    hub = _minimal_scene("hub")
    leaf = _minimal_scene("leaf")
    hub["scene"]["exits"] = [{"label": "To leaf", "target_scene_id": "leaf"}]
    messages = content_lint.lint_scene_graph_connectivity(
        known_scene_ids={"hub", "leaf"},
        load_scene_fn=lambda sid: {"hub": hub, "leaf": leaf}[sid],
        graph_seed_scene_ids=["hub"],
    )
    assert not any(m.code == "graph.unreachable_scene" for m in messages)

    island = _minimal_scene("island")
    report = lint_all_content({"hub": hub, "leaf": leaf, "island": island}, graph_seed_scene_ids=["hub"])
    unreachable = [m for m in report.messages if m.code == "graph.unreachable_scene"]
    assert any(m.scene_id == "island" for m in unreachable)


def test_missing_player_anchor_warning_from_scene_lint():
    a = _minimal_scene("lonely")
    a["scene"]["visible_facts"] = []
    a["scene"]["exits"] = []
    a["scene"]["summary"] = "A plain room with chairs."  # avoid sensory heuristic
    msgs = lint_scene_heuristic_warnings(a, "lonely", {"lonely"})
    assert any(m.code == "scene.missing_player_anchor" for m in msgs)


def test_report_as_dict_roundtrip_shape():
    report = lint_all_content({"x": _minimal_scene("x")})
    d = report.as_dict()
    assert d["ok"] is True
    assert "messages" in d
    assert all("severity" in m and "code" in m for m in d["messages"])


def test_subset_scopes_graph_but_keeps_exit_reference_registry():
    """Loaded subset + full reference_known: exits to unloaded scenes stay valid; graph ignores unloaded ids."""
    hub = _minimal_scene("hub")
    leaf = _minimal_scene("leaf")
    hub["scene"]["exits"] = [{"label": "To leaf", "target_scene_id": "leaf"}]
    island = _minimal_scene("island")
    reference = {"hub", "leaf", "island"}
    report = lint_all_content(
        {"hub": hub},
        reference_known_scene_ids=reference,
        graph_known_scene_ids={"hub"},
    )
    assert not any(m.code == "exit.unknown_target" for m in report.messages)
    assert not any(m.code == "graph.unreachable_scene" and m.scene_id == "island" for m in report.messages)
