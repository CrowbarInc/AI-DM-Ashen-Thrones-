"""N2 closure: fixture matrix, dedup/noise, determinism, severity, ownership boundary."""

from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

import pytest

from game.content_lint import (
    BundleIdOccurrence,
    ContentBundleSnapshot,
    build_bundle_content_index,
    build_content_bundle,
    bundle_index_fingerprint,
    lint_all_content,
    lint_bundle_governance,
    lint_faction_progression_uid_collisions,
)

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = REPO_ROOT / "game"


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


# ---------------------------------------------------------------------------
# 1) Compact regression fixture matrix (states → expected bundle-level codes)
# ---------------------------------------------------------------------------

MatrixRow = Tuple[str, Dict[str, Any], Optional[Dict[str, Any]], Optional[Dict[str, Any]], FrozenSet[str], Optional[Tuple[str, ...]]]


def _matrix_rows() -> List[MatrixRow]:
    """Rows: label, scenes, world, campaign, expected bundle governance codes, optional scene registry overlay."""
    rows: List[MatrixRow] = []

    hub = _minimal_envelope("hub")
    coherent = _coherent_minimal_world(scene_key="hub")
    rows.append(("clean_bundle", {"hub": hub}, coherent, None, frozenset(), None))

    rows.append(
        (
            "duplicate_id_bundle",
            {"s": _minimal_envelope("s")},
            {"npcs": [{"id": "dup", "name": "A"}, {"id": "dup", "name": "B"}]},
            None,
            frozenset({"bundle.duplicate_id.npc"}),
            None,
        )
    )

    rows.append(
        (
            "broken_cross_reference_bundle",
            {"hub": _minimal_envelope("hub")},
            _coherent_minimal_world(scene_key="hub")
            | {"npcs": [{"id": "n1", "location": "phantom_scene", "affiliation": "fac_a"}]},
            {"starting_scene_id": "also_missing"},
            frozenset({"scene.reference.npc_scene_link_unknown", "campaign.reference.starting_scene_unknown"}),
            None,
        )
    )

    rows.append(
        (
            "contradiction_bundle",
            {"s": _minimal_envelope("s")},
            {
                "clues": {
                    "k1": {"id": "same_id", "text": "alpha"},
                    "k2": {"id": "same_id", "text": "beta"},
                }
            },
            None,
            frozenset(
                {
                    "bundle.contradiction.clue_registry_row_conflict",
                    "clue.reference.world_registry_key_mismatch",
                }
            ),
            None,
        )
    )

    rows.append(
        (
            "world_state_mismatch_bundle",
            {"s": _minimal_envelope("s")},
            {
                "world_state": {
                    "flags": {},
                    "counters": {},
                    "clocks": {"alarm": {"id": "not_alarm", "segments": 3, "filled": 0}},
                }
            },
            None,
            frozenset({"world_state.reference.clock_key_row_id_mismatch"}),
            None,
        )
    )

    # Same as subset CLI: link targets exist on registry extension, not in loaded scenes map.
    rows.append(
        (
            "subset_safe_bundle",
            {"hub": _minimal_envelope("hub")},
            {
                **_coherent_minimal_world(scene_key="hub"),
                "npcs": [{"id": "n1", "location": "leaf_only_on_registry", "affiliation": "fac_a"}],
            },
            {"starting_scene_id": "leaf_only_on_registry"},
            frozenset(),
            ("hub", "leaf_only_on_registry"),
        )
    )

    bad_exit = _minimal_envelope("a")
    bad_exit["scene"]["exits"] = [{"label": "x", "target_scene_id": "missing"}]
    mixed_world = _coherent_minimal_world(scene_key="a")
    mixed_world["npcs"] = [{"id": "n1", "location": "ghost_scene", "affiliation": "fac_a"}]
    rows.append(
        (
            "mixed_scene_plus_bundle",
            {"a": bad_exit},
            mixed_world,
            None,
            frozenset({"scene.reference.npc_scene_link_unknown"}),
            None,
        )
    )

    return rows


@pytest.mark.parametrize(
    "label,scenes,world,campaign,expected_codes,registry_ids",
    _matrix_rows(),
    ids=[r[0] for r in _matrix_rows()],
)
def test_n2_fixture_matrix_bundle_governance_codes(
    label: str,
    scenes: Dict[str, Any],
    world: Optional[Dict[str, Any]],
    campaign: Optional[Dict[str, Any]],
    expected_codes: FrozenSet[str],
    registry_ids: Optional[Tuple[str, ...]],
) -> None:
    kwargs: Dict[str, Any] = {}
    if registry_ids is not None:
        kwargs["world_scene_registry_ids"] = list(registry_ids)
    bundle = build_content_bundle(scenes, world=world, campaign=campaign, **kwargs)
    codes = {m.code for m in lint_bundle_governance(bundle)}
    assert codes == expected_codes, label


def test_subset_safe_matrix_row_via_lint_all_content() -> None:
    """Registry extension matches CLI subset: NPC + campaign resolve to unloaded stems."""
    hub = _minimal_envelope("hub")
    world = {
        **_coherent_minimal_world(scene_key="hub"),
        "npcs": [{"id": "n1", "location": "leaf_only_on_registry", "affiliation": "fac_a"}],
    }
    report = lint_all_content(
        {"hub": hub},
        world=world,
        campaign={"starting_scene_id": "leaf_only_on_registry"},
        reference_known_scene_ids={"hub", "leaf_only_on_registry"},
        graph_known_scene_ids={"hub"},
    )
    bundle_codes = {
        m.code
        for m in report.messages
        if m.code.startswith(
            ("bundle.", "campaign.", "scene.reference.", "clue.reference.", "world_state.", "faction.reference.")
        )
    }
    assert bundle_codes == set()


# ---------------------------------------------------------------------------
# 2) No-duplicate-noise guarantees
# ---------------------------------------------------------------------------


def test_duplicate_npc_emits_only_bundle_duplicate_id_npc() -> None:
    world = {"npcs": [{"id": "x"}, {"id": "x"}]}
    bundle = build_content_bundle({"s": _minimal_envelope("s")}, world=world)
    msgs = lint_bundle_governance(bundle)
    assert [m.code for m in msgs] == ["bundle.duplicate_id.npc"]
    assert all(m.severity == "error" for m in msgs)


def test_contradiction_fixture_emits_distinct_registry_and_row_conflict_codes() -> None:
    """Two registry keys sharing one row id: key-mismatch findings + row-conflict (no scene-vs-world drift)."""
    world = {
        "clues": {
            "k1": {"id": "same_id", "text": "alpha"},
            "k2": {"id": "same_id", "text": "beta"},
        }
    }
    bundle = build_content_bundle({"s": _minimal_envelope("s")}, world=world)
    msgs = lint_bundle_governance(bundle)
    codes = [m.code for m in msgs]
    assert codes.count("clue.reference.world_registry_key_mismatch") == 2
    assert codes.count("bundle.contradiction.clue_registry_row_conflict") == 1
    assert "bundle.contradiction.clue_scene_vs_world_definition" not in codes


def test_clue_registry_key_mismatch_does_not_emit_row_conflict_or_scene_vs_world() -> None:
    """Single structural mode: registry key ≠ row id (no contradiction family for that row)."""
    world = {"clues": {"registry_key": {"id": "row_id", "text": "body"}}}
    bundle = build_content_bundle({"s": _minimal_envelope("s")}, world=world)
    msgs = lint_bundle_governance(bundle)
    codes = [m.code for m in msgs]
    assert codes == ["clue.reference.world_registry_key_mismatch"]
    assert "bundle.contradiction.clue_registry_row_conflict" not in codes
    assert "bundle.contradiction.clue_scene_vs_world_definition" not in codes


def test_identical_faction_rows_progression_collision_suppressed_vs_duplicate_id() -> None:
    world = {"factions": [{"id": "same", "name": "A"}, {"id": "same", "name": "B"}]}
    bundle = build_content_bundle({"s": _minimal_envelope("s")}, world=world)
    msgs = lint_bundle_governance(bundle)
    assert [m.code for m in msgs] == ["bundle.duplicate_id.faction"]


# ---------------------------------------------------------------------------
# 3) Determinism locks
# ---------------------------------------------------------------------------


def _canonical_report_json(report: Any) -> str:
    return json.dumps(report.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def test_lint_all_content_identical_on_repeated_runs() -> None:
    hub = _minimal_envelope("hub")
    world = {
        **_coherent_minimal_world(scene_key="hub"),
        "npcs": [{"id": "n1", "location": "bad", "affiliation": "fac_a"}],
        "event_log": [{"type": "faction_pressure", "text": "t", "source": "nope"}],
    }
    scenes = {"hub": hub, "z": _minimal_envelope("z"), "a": _minimal_envelope("a")}
    a = _canonical_report_json(lint_all_content(scenes, world=world, campaign={"starting_scene_id": "missing"}))
    b = _canonical_report_json(lint_all_content(scenes, world=world, campaign={"starting_scene_id": "missing"}))
    assert a == b


def test_lint_all_content_invariant_to_scene_dict_insertion_order() -> None:
    hub = _minimal_envelope("hub")
    leaf = _minimal_envelope("leaf")
    hub["scene"]["discoverable_clues"] = [{"id": "c1", "text": "scene text"}]
    leaf["scene"]["discoverable_clues"] = [{"id": "c1", "text": "other scene text"}]
    world = {"clues": {"c1": {"id": "c1", "text": "world text"}}}
    order_a = {"hub": hub, "leaf": leaf}
    order_b = {"leaf": leaf, "hub": hub}
    assert _canonical_report_json(lint_all_content(order_a, world=world)) == _canonical_report_json(
        lint_all_content(order_b, world=world)
    )


def test_bundle_index_fingerprint_stable_across_dict_order() -> None:
    w = _coherent_minimal_world(scene_key="hub")
    a = {"hub": _minimal_envelope("hub"), "z": _minimal_envelope("z")}
    b = {"z": _minimal_envelope("z"), "hub": _minimal_envelope("hub")}
    i1 = build_bundle_content_index(a, world=w)
    i2 = build_bundle_content_index(b, world=w)
    assert bundle_index_fingerprint(i1) == bundle_index_fingerprint(i2)


def test_evidence_json_stable_for_bundle_scope_payload() -> None:
    scenes = {"hub": _minimal_envelope("hub")}
    bundle = build_content_bundle(
        scenes,
        world=_coherent_minimal_world(scene_key="hub"),
        campaign={"starting_scene_id": "x"},
        world_scene_registry_ids=["extra", "hub"],
    )
    msgs = lint_bundle_governance(bundle)
    camp = next(m for m in msgs if m.code == "campaign.reference.starting_scene_unknown")
    j1 = json.dumps(camp.evidence, sort_keys=True, separators=(",", ":"))
    j2 = json.dumps(camp.evidence, sort_keys=True, separators=(",", ":"))
    assert j1 == j2
    assert camp.evidence["resolved_world_scene_link_registry_ids"] == ["extra", "hub"]


# ---------------------------------------------------------------------------
# 4) Severity consistency (regression lock, not policy)
# ---------------------------------------------------------------------------

_BUNDLE_GOVERNANCE_ERROR_CODES = frozenset(
    {
        "bundle.duplicate_id.npc",
        "bundle.duplicate_id.faction",
        "bundle.duplicate_id.project",
        "bundle.reference.event_log_source_unknown_faction",
        "bundle.contradiction.clue_registry_row_conflict",
        "bundle.contradiction.clue_scene_vs_world_definition",
        "campaign.reference.starting_scene_unknown",
        "scene.reference.npc_scene_link_unknown",
        "scene.reference.npc_affiliation_unknown",
        "clue.reference.world_registry_key_mismatch",
        "world_state.reference.clock_key_row_id_mismatch",
    }
)


@pytest.mark.parametrize("code", sorted(_BUNDLE_GOVERNANCE_ERROR_CODES))
def test_bundle_governance_error_codes_remain_error_severity(code: str) -> None:
    """Synthetic minimal repro per code; fails if severity flips without intentional doc+test update."""
    scenes: Dict[str, Any] = {"s": _minimal_envelope("s")}
    world: Optional[Dict[str, Any]] = None
    campaign: Optional[Dict[str, Any]] = None

    if code == "bundle.duplicate_id.npc":
        world = {"npcs": [{"id": "d"}, {"id": "d"}]}
    elif code == "bundle.duplicate_id.faction":
        world = {"factions": [{"id": "d", "name": "A"}, {"id": "d", "name": "B"}]}
    elif code == "bundle.duplicate_id.project":
        world = {"projects": [{"id": "d"}, {"id": "d"}]}
    elif code == "bundle.reference.event_log_source_unknown_faction":
        world = {**_coherent_minimal_world(scene_key="s"), "event_log": [{"type": "faction_x", "source": "ghost_f"}]}
    elif code == "bundle.contradiction.clue_registry_row_conflict":
        world = {"clues": {"a": {"id": "z", "text": "1"}, "b": {"id": "z", "text": "2"}}}
    elif code == "bundle.contradiction.clue_scene_vs_world_definition":
        world = {"clues": {"c1": {"id": "c1", "text": "w"}}}
        env = _minimal_envelope("s")
        env["scene"]["discoverable_clues"] = [{"id": "c1", "text": "s"}]
        scenes = {"s": env}
    elif code == "campaign.reference.starting_scene_unknown":
        world = _coherent_minimal_world(scene_key="s")
        campaign = {"starting_scene_id": "missing_start"}
    elif code == "scene.reference.npc_scene_link_unknown":
        world = _coherent_minimal_world(scene_key="s")
        world["npcs"] = [{"id": "n", "location": "nowhere", "affiliation": "fac_a"}]
    elif code == "scene.reference.npc_affiliation_unknown":
        world = _coherent_minimal_world(scene_key="s")
        world["npcs"] = [{"id": "n", "location": "s", "affiliation": "not_real"}]
    elif code == "clue.reference.world_registry_key_mismatch":
        world = {"clues": {"k": {"id": "other", "text": "t"}}}
    elif code == "world_state.reference.clock_key_row_id_mismatch":
        world = {
            "world_state": {
                "flags": {},
                "counters": {},
                "clocks": {"outer": {"id": "inner", "segments": 2, "filled": 0}},
            }
        }
    else:  # pragma: no cover
        pytest.fail(f"Unhandled code {code!r} — update matrix when adding bundle rules")

    bundle = build_content_bundle(scenes, world=world, campaign=campaign)
    hit = [m for m in lint_bundle_governance(bundle) if m.code == code]
    assert len(hit) == 1, (code, [m.code for m in lint_bundle_governance(bundle)])
    assert hit[0].severity == "error", code


def test_faction_progression_uid_collision_remains_error_via_synthetic_index() -> None:
    """Realistic JSON rarely hits this without duplicate_id; lock severity on the dedicated pass."""
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
    assert len(msgs) == 1 and msgs[0].severity == "error"


def test_bundle_duplicate_id_scene_remains_warning() -> None:
    a = _minimal_envelope("shared")
    b = _minimal_envelope("shared")
    bundle = build_content_bundle({"f1": a, "f2": b})
    msgs = [m for m in lint_bundle_governance(bundle) if m.code == "bundle.duplicate_id.scene"]
    assert len(msgs) == 1
    assert msgs[0].severity == "warning"


def test_subset_full_same_severity_for_equivalent_reference_registry() -> None:
    hub = _minimal_envelope("hub")
    leaf = _minimal_envelope("leaf")
    world = {
        "settlements": [{"id": "set1", "name": "S"}],
        "factions": [{"id": "fac1", "name": "F"}],
        "projects": [],
        "assets": [],
        "world_flags": [],
        "event_log": [],
        "inference_rules": [],
        "clues": {},
        "npcs": [{"id": "n1", "location": "ghost", "affiliation": "fac1"}],
        "world_state": {"flags": {}, "counters": {}, "clocks": {}},
    }
    ref: Set[str] = {"hub", "leaf"}
    full = lint_all_content({"hub": hub, "leaf": leaf}, world=world, graph_seed_scene_ids=["hub"])
    sub = lint_all_content(
        {"hub": hub},
        world=world,
        reference_known_scene_ids=ref,
        graph_known_scene_ids={"hub"},
        graph_seed_scene_ids=["hub"],
    )
    key = lambda r: (r.code, r.severity, r.scene_id, r.path, r.message)
    full_npc = sorted((m for m in full.messages if m.code == "scene.reference.npc_scene_link_unknown"), key=key)
    sub_npc = sorted((m for m in sub.messages if m.code == "scene.reference.npc_scene_link_unknown"), key=key)
    assert [(m.severity, m.message) for m in full_npc] == [(m.severity, m.message) for m in sub_npc]


def test_scene_insertion_order_does_not_change_bundle_message_severity() -> None:
    hub = _minimal_envelope("hub")
    leaf = _minimal_envelope("leaf")
    world = {
        **_coherent_minimal_world(scene_key="hub"),
        "npcs": [{"id": "n1", "location": "ghost", "affiliation": "fac_a"}],
    }
    r1 = lint_all_content({"hub": hub, "leaf": leaf}, world=world)
    r2 = lint_all_content({"leaf": leaf, "hub": hub}, world=world)
    b1 = sorted((m.code, m.severity) for m in r1.messages if m.code.startswith("scene.reference."))
    b2 = sorted((m.code, m.severity) for m in r2.messages if m.code.startswith("scene.reference."))
    assert b1 == b2


# ---------------------------------------------------------------------------
# 5) Ownership: bundle governance stays author-time / tooling-only
# ---------------------------------------------------------------------------


def _game_py_files() -> List[Path]:
    return sorted(p for p in GAME_DIR.rglob("*.py") if p.name != "content_lint.py")


def _imports_content_lint_module(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in ("game.content_lint", "content_lint"):
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == "game.content_lint":
                return True
            if node.module == "game" and any(a.name == "content_lint" for a in node.names):
                return True
    return False


def test_game_package_does_not_import_content_lint_on_runtime_paths() -> None:
    """Guardrail: no other game module statically imports the lint engine (CLI/tests may)."""
    offenders: List[str] = []
    for path in _game_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if _imports_content_lint_module(tree):
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], "Unexpected imports of game.content_lint: " + ", ".join(offenders)


# ---------------------------------------------------------------------------
# Matrix completeness: every row runs without raising
# ---------------------------------------------------------------------------


def test_matrix_row_world_state_has_minimal_keys_for_clock_pass() -> None:
    """Sanity: world_state_mismatch row only supplies clocks (other branches tolerate missing)."""
    row = next(r for r in _matrix_rows() if r[0] == "world_state_mismatch_bundle")
    _label, scenes, world, _camp, expected, reg = row
    bundle = build_content_bundle(scenes, world=world, world_scene_registry_ids=list(reg) if reg else None)
    assert {m.code for m in lint_bundle_governance(bundle)} == expected
