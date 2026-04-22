"""Bundle-level content governance (Objective N2): index extraction + message codes."""
from __future__ import annotations

import copy
from dataclasses import replace

import pytest

from game.content_lint import (
    BundleIdOccurrence,
    ContentBundleSnapshot,
    build_bundle_content_index,
    build_content_bundle,
    bundle_compare_id,
    bundle_index_fingerprint,
    lint_all_content,
    lint_bundle_duplicate_ids,
    lint_bundle_governance,
    lint_bundle_clue_registry_row_conflicts,
    lint_bundle_clue_scene_vs_world_definitions,
    lint_campaign_scene_references,
    lint_clue_world_registry_references,
    lint_faction_progression_uid_collisions,
    lint_scene_world_npc_affiliations,
    lint_scene_world_npc_scene_links,
    lint_world_state_registry_consistency,
)

pytestmark = pytest.mark.unit


def _minimal_envelope(scene_id: str) -> dict:
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


def test_bundle_index_fingerprint_is_deterministic():
    scenes = {"b": _minimal_envelope("b"), "a": _minimal_envelope("a")}
    world = {
        "npcs": [{"id": "z_npc"}, {"id": "a_npc"}],
        "factions": [],
        "projects": [],
        "clues": {},
        "world_state": {"flags": {"z": True, "a": False}, "counters": {}, "clocks": {}},
    }
    i1 = build_bundle_content_index(scenes, world=world, campaign={"title": "T", "revision": 1})
    i2 = build_bundle_content_index(scenes, world=world, campaign={"title": "T", "revision": 1})
    assert bundle_index_fingerprint(i1) == bundle_index_fingerprint(i2)


def test_build_bundle_content_index_does_not_mutate_inputs():
    scenes = {"hub": _minimal_envelope("hub")}
    world = {
        "npcs": [{"id": "n1", "tags": [1, 2]}],
        "factions": [{"id": "f1", "name": "F"}],
        "projects": [{"id": "p1", "name": "P", "category": "research", "status": "active", "progress": 0, "target": 3}],
        "clues": {"c1": {"id": "c1", "text": "t"}},
        "world_state": {"flags": {"x": True}, "counters": {"n": 1}, "clocks": {"clk": {"id": "clk", "segments": 4, "filled": 0}}},
    }
    campaign = {"meta": {"k": "v"}}
    s_snap = copy.deepcopy(scenes)
    w_snap = copy.deepcopy(world)
    c_snap = copy.deepcopy(campaign)
    build_bundle_content_index(scenes, world=world, campaign=campaign)
    assert scenes == s_snap
    assert world == w_snap
    assert campaign == c_snap


def test_bundle_compare_id_is_reference_only():
    assert bundle_compare_id("  x  ") == "x"
    assert bundle_compare_id(42) == "42"


def test_bundle_duplicate_npc_emits_stable_code():
    world = {"npcs": [{"id": "dup", "name": "A"}, {"id": "dup", "name": "B"}]}
    scenes = {"s": _minimal_envelope("s")}
    bundle = build_content_bundle(scenes, world=world)
    msgs = lint_bundle_duplicate_ids(bundle)
    assert len(msgs) == 1
    assert msgs[0].code == "bundle.duplicate_id.npc"
    assert msgs[0].severity == "error"
    d = msgs[0].as_dict()
    assert set(d.keys()) >= {"severity", "code", "message", "path", "evidence"}
    assert d["evidence"]["compare_key"] == "dup"


def test_clue_world_registry_key_mismatch_code():
    world = {"clues": {"registry_key": {"id": "different_row_id", "text": "body"}}}
    bundle = build_content_bundle({"s": _minimal_envelope("s")}, world=world)
    msgs = lint_clue_world_registry_references(bundle)
    assert len(msgs) == 1
    assert msgs[0].code == "clue.reference.world_registry_key_mismatch"
    assert msgs[0].severity == "error"
    assert msgs[0].as_dict()["evidence"]["registry_key"] == "registry_key"


def test_world_state_clock_key_row_id_mismatch_code():
    world = {"world_state": {"flags": {}, "counters": {}, "clocks": {"alarm": {"id": "not_alarm", "segments": 3, "filled": 0}}}}
    bundle = build_content_bundle({"s": _minimal_envelope("s")}, world=world)
    msgs = lint_world_state_registry_consistency(bundle)
    assert len(msgs) == 1
    assert msgs[0].code == "world_state.reference.clock_key_row_id_mismatch"
    assert msgs[0].severity == "error"


def test_bundle_duplicate_scene_inner_compare_key_across_envelopes():
    a = _minimal_envelope("shared")
    b = _minimal_envelope("shared")
    bundle = build_content_bundle({"file_a": a, "file_b": b})
    msgs = [m for m in lint_bundle_duplicate_ids(bundle) if m.code == "bundle.duplicate_id.scene"]
    assert len(msgs) == 1
    assert msgs[0].severity == "warning"
    ev = msgs[0].as_dict()["evidence"]
    assert set(ev["envelope_ids"]) == {"file_a", "file_b"}


def test_faction_progression_uid_collision_distinct_authored():
    """Synthetic index rows: same compare_key, different authored labels → error code."""
    scenes = {"s": _minimal_envelope("s")}
    base = build_bundle_content_index(scenes, world=None)
    idx = replace(
        base,
        faction_occurrences=(
            BundleIdOccurrence(
                authored_id="display_a",
                compare_key="collision_uid",
                source_kind="world.factions",
                source_detail="[0]",
            ),
            BundleIdOccurrence(
                authored_id="display_b",
                compare_key="collision_uid",
                source_kind="world.factions",
                source_detail="[1]",
            ),
        ),
    )
    bundle = ContentBundleSnapshot(scenes=scenes, world={"factions": []}, campaign=None, index=idx)
    msgs = lint_faction_progression_uid_collisions(bundle)
    assert len(msgs) == 1
    assert msgs[0].code == "faction.reference.progression_uid_collision"
    assert msgs[0].severity == "error"


def _coherent_minimal_world(*, scene_key: str) -> dict:
    return {
        "settlements": [{"id": "settle_a", "name": "Settle A"}],
        "factions": [{"id": "fac_a", "name": "Faction A"}],
        "projects": [],
        "assets": [],
        "world_flags": [],
        "event_log": [],
        "inference_rules": [],
        "clues": {},
        "npcs": [{"id": "npc_a", "location": scene_key, "affiliation": "fac_a"}],
        "world_state": {"flags": {}, "counters": {}, "clocks": {}},
    }


def test_lint_bundle_governance_clean_bundle_zero_findings():
    scenes = {"hub": _minimal_envelope("hub")}
    bundle = build_content_bundle(scenes, world=_coherent_minimal_world(scene_key="hub"), campaign=None)
    assert lint_bundle_governance(bundle) == []


def test_campaign_reference_starting_scene_unknown():
    scenes = {"hub": _minimal_envelope("hub")}
    campaign = {"starting_scene_id": "missing_scene"}
    bundle = build_content_bundle(scenes, world=_coherent_minimal_world(scene_key="hub"), campaign=campaign)
    msgs = lint_campaign_scene_references(bundle)
    assert len(msgs) == 1
    assert msgs[0].code == "campaign.reference.starting_scene_unknown"
    assert msgs[0].severity == "error"


def test_campaign_starting_scene_resolved_no_message():
    scenes = {"hub": _minimal_envelope("hub")}
    bundle = build_content_bundle(scenes, world=_coherent_minimal_world(scene_key="hub"), campaign={"starting_scene_id": "hub"})
    assert lint_campaign_scene_references(bundle) == []


def test_scene_reference_npc_scene_link_unknown():
    scenes = {"hub": _minimal_envelope("hub")}
    world = _coherent_minimal_world(scene_key="hub")
    world["npcs"] = [{"id": "n1", "location": "nowhere", "affiliation": "fac_a"}]
    bundle = build_content_bundle(scenes, world=world)
    msgs = lint_scene_world_npc_scene_links(bundle)
    assert len(msgs) == 1
    assert msgs[0].code == "scene.reference.npc_scene_link_unknown"
    assert msgs[0].evidence and msgs[0].evidence.get("field") == "location"


def test_scene_reference_npc_affiliation_unknown():
    scenes = {"hub": _minimal_envelope("hub")}
    world = _coherent_minimal_world(scene_key="hub")
    world["npcs"] = [{"id": "n1", "location": "hub", "affiliation": "not_a_faction_or_settlement"}]
    bundle = build_content_bundle(scenes, world=world)
    msgs = lint_scene_world_npc_affiliations(bundle)
    assert len(msgs) == 1
    assert msgs[0].code == "scene.reference.npc_affiliation_unknown"


def test_bundle_reference_event_log_unknown_faction_source():
    scenes = {"hub": _minimal_envelope("hub")}
    world = _coherent_minimal_world(scene_key="hub")
    world["event_log"] = [{"type": "faction_pressure", "text": "x", "source": "unknown_faction"}]
    bundle = build_content_bundle(scenes, world=world)
    msgs = lint_bundle_governance(bundle)
    codes = {m.code for m in msgs}
    assert "bundle.reference.event_log_source_unknown_faction" in codes


def test_bundle_contradiction_clue_registry_row_conflict():
    world = {
        "clues": {
            "k1": {"id": "same_id", "text": "alpha"},
            "k2": {"id": "same_id", "text": "beta"},
        }
    }
    bundle = build_content_bundle({"s": _minimal_envelope("s")}, world=world)
    msgs = lint_bundle_clue_registry_row_conflicts(bundle)
    assert len(msgs) == 1
    assert msgs[0].code == "bundle.contradiction.clue_registry_row_conflict"


def test_ambiguous_world_clue_texts_row_conflict_not_scene_vs_world():
    """Same canonical clue id with incompatible world rows → one row-conflict; skip scene drift."""
    world = {
        "clues": {
            "k1": {"id": "  shared  ", "text": "first"},
            "k2": {"id": "shared", "text": "second"},
        }
    }
    env = _minimal_envelope("hub")
    env["scene"]["discoverable_clues"] = [{"id": "shared", "text": "scene version"}]
    bundle = build_content_bundle({"hub": env}, world=world)
    msgs = lint_bundle_governance(bundle)
    codes = [m.code for m in msgs]
    assert codes.count("bundle.contradiction.clue_registry_row_conflict") == 1
    assert "bundle.contradiction.clue_scene_vs_world_definition" not in codes


def test_bundle_contradiction_clue_scene_vs_world_definition():
    world = {"clues": {"c1": {"id": "c1", "text": "from world"}}}
    env = _minimal_envelope("hub")
    env["scene"]["discoverable_clues"] = [{"id": "c1", "text": "from scene"}]
    scenes = {"hub": env}
    bundle = build_content_bundle(scenes, world=world)
    msgs = lint_bundle_clue_scene_vs_world_definitions(bundle)
    assert len(msgs) == 1
    assert msgs[0].code == "bundle.contradiction.clue_scene_vs_world_definition"


def test_duplicate_faction_id_does_not_also_emit_progression_collision():
    world = {
        "factions": [
            {"id": "dup", "name": "A"},
            {"id": "dup", "name": "B"},
        ]
    }
    bundle = build_content_bundle({"s": _minimal_envelope("s")}, world=world)
    msgs = lint_bundle_governance(bundle)
    codes = [m.code for m in msgs]
    assert codes.count("bundle.duplicate_id.faction") == 1
    assert "faction.reference.progression_uid_collision" not in codes


def test_lint_all_content_mixed_scene_error_and_bundle_error():
    bad_exit = _minimal_envelope("a")
    bad_exit["scene"]["exits"] = [{"label": "x", "target_scene_id": "missing"}]
    world = _coherent_minimal_world(scene_key="a")
    world["npcs"] = [{"id": "n1", "location": "ghost_scene", "affiliation": "fac_a"}]
    report = lint_all_content({"a": bad_exit}, world=world)
    codes = {m.code for m in report.messages}
    assert "exit.unknown_target" in codes
    assert "scene.reference.npc_scene_link_unknown" in codes
    assert report.ok is False


def test_lint_all_content_merges_bundle_passes_without_changing_report_shape():
    report = lint_all_content({"x": _minimal_envelope("x")}, world=None, campaign=None)
    d = report.as_dict()
    assert set(d) == {"ok", "error_count", "warning_count", "messages", "scene_ids_checked"}


def test_lint_bundle_governance_merge_is_stable():
    world = {"npcs": [{"id": "d"}, {"id": "d"}]}
    bundle = build_content_bundle({"s": _minimal_envelope("s")}, world=world)
    m1 = lint_bundle_governance(bundle)
    m2 = lint_bundle_governance(bundle)
    assert [x.as_dict() for x in m1] == [x.as_dict() for x in m2]


def test_build_content_bundle_materializes_reference_registry_extension_ids():
    scenes = {"hub": _minimal_envelope("hub")}
    bundle = build_content_bundle(
        scenes,
        world=_coherent_minimal_world(scene_key="hub"),
        world_scene_registry_ids=["leaf", "hub"],
    )
    assert bundle.loaded_envelope_ids == ("hub",)
    assert bundle.reference_registry_extension_ids == ("leaf",)
    assert "leaf" in bundle.resolved_world_scene_link_registry_ids


def test_subset_campaign_starting_scene_resolves_when_id_only_on_reference_registry():
    scenes = {"hub": _minimal_envelope("hub")}
    report = lint_all_content(
        scenes,
        world=_coherent_minimal_world(scene_key="hub"),
        campaign={"starting_scene_id": "leaf"},
        reference_known_scene_ids={"hub", "leaf"},
        graph_known_scene_ids={"hub"},
    )
    assert not any(m.code == "campaign.reference.starting_scene_unknown" for m in report.messages)


def test_campaign_unknown_evidence_includes_loaded_and_resolved_registry():
    scenes = {"hub": _minimal_envelope("hub")}
    bundle = build_content_bundle(
        scenes,
        world=_coherent_minimal_world(scene_key="hub"),
        campaign={"starting_scene_id": "phantom"},
        world_scene_registry_ids=["hub"],
    )
    msgs = lint_campaign_scene_references(bundle)
    assert len(msgs) == 1
    ev = msgs[0].as_dict()["evidence"]
    assert ev["loaded_envelope_ids"] == ["hub"]
    assert ev["reference_registry_extension_ids"] == []
    assert "phantom" not in ev["resolved_world_scene_link_registry_ids"]
    assert ev["known_scene_ids"] == ev["resolved_world_scene_link_registry_ids"]
