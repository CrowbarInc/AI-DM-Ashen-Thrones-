"""Readiness checks only. No live provider and no conversational scoring."""
import copy
import json
import shutil
from pathlib import Path

import pytest

from tools.atgb.baseline import BASELINE_VERSION, BaselineError, load_baseline
from tools.atgb.driver import RunConfig, run_benchmark
from tools.atgb.fixtures import load_corpus
from tools.atgb.isolation import UnsafeBenchmarkDataDir, prepare_isolated_store, repo_root
from tools.atgb.preflight import check_start

ROOT = repo_root()


def test_all_scenarios_reset_reproducibly_without_chat_or_canonical_changes(tmp_path):
    protected = [p for p in (ROOT / "data").glob("*.json")] + [ROOT / "data/session_log.jsonl"]
    before = {p: p.read_bytes() for p in protected if p.is_file()}
    runs = [run_benchmark(RunConfig(mode="provider_disabled_host", preflight_only=True,
                                  output_dir=tmp_path / f"run{i}")) for i in range(2)]
    assert {p: p.read_bytes() for p in before} == before
    fingerprints = []
    for run in runs:
        assert run["turns"] == [] and run["stop_reason"] is None
        assert run["gameplay_performance_claim"] is False
        records = run["scenario_records"]
        assert [r["scenario_id"] for r in records] == [s["scenario_id"] for s in load_corpus(ROOT)["scenarios"]]
        assert all(r["preflight"]["ok"] for r in records)
        assert all(r["preflight"]["unverified_conditions"] for r in records)
        fingerprints.append([r["preflight"]["starting_state_sha256"] for r in records])
    assert fingerprints[0] == fingerprints[1]
    assert len(set(fingerprints[0])) == 1


@pytest.mark.parametrize("damage", ["missing_manifest", "wrong_version", "missing_world", "wrong_topic", "missing_scene"])
def test_incompatible_baseline_refused_before_store_creation(tmp_path, damage):
    source, _ = load_baseline(ROOT)
    fake_repo = tmp_path / "repo"
    baseline = fake_repo / "data/validation/atgb/baselines" / BASELINE_VERSION
    shutil.copytree(source, baseline)
    if damage == "missing_manifest":
        (baseline / "manifest.json").unlink()
    elif damage == "wrong_version":
        manifest = json.loads((baseline / "manifest.json").read_text())
        manifest["baseline_version"] = "unexpected"
        (baseline / "manifest.json").write_text(json.dumps(manifest))
    elif damage == "missing_world":
        (baseline / "world.json").unlink()
    elif damage == "missing_scene":
        (baseline / "scenes/frontier_gate.json").unlink()
    else:
        world = json.loads((baseline / "world.json").read_text())
        world["npcs"][0]["topics"] = []
        (baseline / "world.json").write_text(json.dumps(world))
    target = tmp_path / "store"
    with pytest.raises(BaselineError):
        prepare_isolated_store(target, scenario_id="S01", repo=fake_repo,
                               player_campaign_dir=tmp_path / "player")
    assert not target.exists()


@pytest.mark.parametrize("target", ["canonical", "nested", "ancestor", "active", "occupied", "reused", "alternate_source"])
def test_unsafe_stores_and_alternate_sources_refused(tmp_path, target):
    active = tmp_path / "player"
    candidate = tmp_path / "store"
    kwargs = {}
    if target == "canonical":
        candidate = ROOT / "data"
    elif target == "nested":
        candidate = ROOT / "data/unsafe"
    elif target == "ancestor":
        candidate = ROOT
    elif target == "active":
        candidate = active
    elif target == "occupied":
        candidate.mkdir()
        (candidate / "world.json").write_text("{}")
    elif target == "reused":
        prepare_isolated_store(candidate, scenario_id="S01", player_campaign_dir=active)
    else:
        kwargs["source_data_dir"] = ROOT / "data"
    with pytest.raises(UnsafeBenchmarkDataDir):
        prepare_isolated_store(candidate, scenario_id="S01", player_campaign_dir=active, **kwargs)


def test_readonly_preflight_reports_missing_facts_npcs_and_history(tmp_path):
    from game.campaign_state import create_fresh_session_document, create_fresh_combat_state

    store = prepare_isolated_store(tmp_path / "store", scenario_id="S04", player_campaign_dir=tmp_path / "player")
    world = json.loads((store / "world.json").read_text())
    session = create_fresh_session_document()
    kwargs = dict(repo=ROOT, data_dir=store, imported_data_dir=store,
                  player_campaign_dir=tmp_path / "player", expected_location_id="frontier_gate",
                  session=session, world=world, combat=create_fresh_combat_state(), log=[])
    assert check_start(**kwargs)["ok"]
    for damage in ("topic", "npc", "history", "location", "scene", "binding", "version"):
        args = copy.deepcopy(kwargs)
        if damage == "topic":
            args["world"]["npcs"][1]["topics"] = []
        elif damage == "npc":
            args["world"]["npcs"].pop()
        elif damage == "history":
            args["session"]["chat_history"] = [{"text": "old turn"}]
        elif damage == "location":
            args["session"]["active_scene_id"] = "market_quarter"
        elif damage == "binding":
            args["imported_data_dir"] = ROOT / "data"
        elif damage == "version":
            marker = store / ".atgb-isolated"
            original = marker.read_bytes()
            marker.write_text('{}')
        else:
            scene = store / "scenes/frontier_gate.json"
            original = scene.read_bytes()
            scene.write_text('{}')
        result = check_start(**args)
        assert not result["ok"] and result["critical_failures"], damage
        assert result["unverified_conditions"]
        if damage == "scene":
            scene.write_bytes(original)
        elif damage == "version":
            marker.write_bytes(original)


def test_worker_submits_no_turns_on_failed_preflight(monkeypatch, tmp_path):
    monkeypatch.setattr("tools.atgb.driver._location_id", lambda *args: "missing_location")
    result = run_benchmark(RunConfig(mode="provider_disabled_host", scenario_ids=("S01",), output_dir=tmp_path))
    assert result["turns"] == []
    assert result["stop_reason"] == "preflight_failed"
    record = result["scenario_records"][0]
    assert not record["preflight"]["ok"]
    assert "starting_location" in record["preflight"]["critical_failures"]
    assert record["isolation"]["reset_invoked"]
