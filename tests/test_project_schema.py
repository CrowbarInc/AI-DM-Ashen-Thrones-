"""Tests for canonical project shape, legacy compatibility, and advancement."""
from game.projects import (
    PROJECT_STATUSES,
    create_project,
    update_project,
    _normalize_project_shape,
)
from game.world import advance_world_tick


def test_advancement_uses_canonical_target_progress_status():
    """Project advancement uses canonical target, progress, and status (complete not completed)."""
    world = {"projects": [], "event_log": [], "factions": []}
    proj = create_project(world, {"name": "Build Wall", "category": "infrastructure", "progress": 0, "target": 3})
    assert proj["progress"] == 0
    assert proj["target"] == 3
    assert proj["status"] == "active"

    result = advance_world_tick(world, {})
    p = world["projects"][0]
    assert p["progress"] == 1
    assert p["target"] == 3
    assert p["status"] == "active"

    advance_world_tick(world, {})
    advance_world_tick(world, {})
    p = world["projects"][0]
    assert p["progress"] == 3
    assert p["target"] == 3
    assert p["status"] == "complete"
    assert "completed" not in (p.get("status"),)


def test_legacy_project_using_goal_still_works():
    """Legacy project data using 'goal' instead of 'target' still advances and completes."""
    world = {"projects": [], "event_log": [], "factions": []}
    # Simulate legacy record: has goal, no target
    world["projects"].append({
        "id": "legacy-goal",
        "name": "Legacy Project",
        "category": "infrastructure",
        "status": "active",
        "progress": 0,
        "goal": 2,
    })

    result = advance_world_tick(world, {})
    p = world["projects"][0]
    assert p["progress"] == 1
    assert p.get("target") == 2
    assert p["status"] == "active"

    advance_world_tick(world, {})
    p = world["projects"][0]
    assert p["progress"] == 2
    assert p["target"] == 2
    assert p["status"] == "complete"


def test_legacy_completed_status_normalizes_safely():
    """Legacy status 'completed' normalizes to 'complete' via create/update path."""
    normalized = _normalize_project_shape({
        "name": "Done Thing",
        "status": "completed",
        "progress": 5,
        "goal": 5,
    })
    assert normalized["status"] == "complete"
    assert normalized["target"] == 5
    assert normalized["progress"] == 5
    assert normalized["status"] in PROJECT_STATUSES

    # update_project path: legacy project with completed -> stored as complete
    world = {"projects": [{"id": "x", "name": "X", "category": "infrastructure", "status": "completed", "progress": 3, "goal": 3}]}
    updated = update_project(world, "x", {})
    assert updated is not None
    assert updated["status"] == "complete"
    assert updated["target"] == 3


def test_project_completion_behavior_end_to_end():
    """Project completion: advance until complete, event emitted, status stable."""
    world = {"projects": [], "event_log": [], "factions": []}
    create_project(world, {"name": "Tower", "category": "infrastructure", "progress": 0, "target": 2})

    result = advance_world_tick(world, {})
    assert result["events"] == []
    assert world["projects"][0]["status"] == "active"

    result = advance_world_tick(world, {})
    assert len(result["events"]) == 1
    assert result["events"][0]["type"] == "project_completed"
    assert "Tower" in result["events"][0]["text"]
    p = world["projects"][0]
    assert p["status"] == "complete"
    assert p["progress"] == 2
    assert p["target"] == 2

    # Further ticks do not re-advance or re-emit (only active projects advance)
    result = advance_world_tick(world, {})
    assert len(result["events"]) == 0
    assert world["projects"][0]["progress"] == 2
    assert world["projects"][0]["status"] == "complete"
