"""Gate orchestration facade for downstream consumer integration tests (Cycle BV12A).

Owns full gate orchestration via ``game.final_emission_runtime`` and minimal fake-GM
HTTP fixture stubs. Downstream tests should import this module instead of
``tests.helpers.gate_integration_smoke``.

Compatibility re-export: ``tests.helpers.gate_integration_smoke``.

Registry reference: ``tests/test_gate_boundary_governance.py`` (Cycle BV12A).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output


def apply_final_emission_gate_consumer(
    gm_output: Mapping[str, Any],
    *,
    resolution: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    scene_id: str = "",
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run full gate orchestration for downstream consumer integration tests; return (output, fem)."""
    from game.final_emission_runtime import finalize_player_facing_emission

    out = finalize_player_facing_emission(
        dict(gm_output),
        resolution=dict(resolution) if isinstance(resolution, Mapping) else resolution,
        session=dict(session) if isinstance(session, Mapping) else session,
        scene_id=scene_id,
        scene=dict(scene) if isinstance(scene, Mapping) else scene,
        world=dict(world) if isinstance(world, Mapping) else world,
    )
    return out, final_emission_meta_from_output(out)


def gm_response_stub(
    text: str,
    *,
    tags: Sequence[str] | None = None,
    debug_notes: str = "",
) -> dict[str, Any]:
    """Minimal fake ``call_gpt`` return dict for HTTP/pipeline integration tests."""
    return {
        "player_facing_text": text,
        "tags": list(tags or []),
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": debug_notes,
    }


def gate_orchestration_smoke_surface() -> dict[str, object]:
    """Diagnostic registry surface for ownership governance (read-only)."""
    return {
        "facade": "tests.helpers.gate_orchestration_smoke",
        "symbols": (
            "apply_final_emission_gate_consumer",
            "gm_response_stub",
        ),
        "authority": "game.final_emission_runtime",
        "fem_read_facade": "tests.helpers.replay_fem_read_smoke",
    }
