#!/usr/bin/env python3
"""BV3D — materialize BV3A positive-control gate outputs for measurement corpus."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.defaults import default_scene, default_session, default_world
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.storage import get_scene_runtime
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer
from tools.bv3d_measurement_scope import POSITIVE_CONTROL_FIXTURES

OUT_DIR = ROOT / "artifacts" / "bv3d_measurement"


def _observe_bundle_with_interlocutor(*, npc_id: str = "tavern_runner", npc_name: str = "Tavern Runner"):
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    scene = default_scene(sid)
    set_social_target(session, npc_id)
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "I watch the runner closely."
    resolution = {
        "kind": "observe",
        "prompt": "I watch the runner closely.",
        "social": {"npc_id": npc_id, "npc_name": npc_name},
        "metadata": {"human_adjacent_intent_family": "observe_group"},
    }
    return session, world, scene, sid, resolution


def _observe_bundle_without_social():
    session = default_session()
    world = default_world()
    scene = default_scene("frontier_gate")
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    return session, world, scene, sid


def build_rows() -> list[dict]:
    rows: list[dict] = []
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    session, world, scene, sid, resolution = _observe_bundle_with_interlocutor()
    candidate = '"Keep your wits about you," he says, glancing toward the checkpoint.'
    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": candidate, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )
    rows.append(
        {
            "timestamp": generated_at,
            "fixture_id": "bv3a_positive_control_interlocutor_he_says",
            "resolution": resolution,
            "route_kind": "observe",
            "gm_output": out,
            "measurement_provenance": "bv3d_positive_control_from_test_bv3a",
        }
    )

    session, world, scene, sid = _observe_bundle_without_social()
    resolution = {"kind": "observe", "prompt": "I look around."}
    candidate = 'Guard Captain and Tavern Runner stand near the gate. "Back away," he says.'
    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": candidate, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )
    rows.append(
        {
            "timestamp": generated_at,
            "fixture_id": "bv3a_negative_control_multi_person_hard_replace",
            "resolution": resolution,
            "route_kind": "observe",
            "gm_output": out,
            "measurement_provenance": "bv3d_positive_control_from_test_bv3a",
        }
    )

    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    POSITIVE_CONTROL_FIXTURES.write_text(
        "\n".join(json.dumps(row, default=str) for row in rows) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "fixture_count": len(rows),
        "path": str(POSITIVE_CONTROL_FIXTURES.relative_to(ROOT)).replace("\\", "/"),
        "fixture_ids": [row["fixture_id"] for row in rows],
    }
    (OUT_DIR / "positive_control_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
