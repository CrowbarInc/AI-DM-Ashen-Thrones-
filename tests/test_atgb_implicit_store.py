"""Implicit ATGB store ownership. These tests do not call a live model."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from tools.atgb.driver import RunConfig, _run_scenario, run_benchmark
from tools.atgb.fixtures import load_corpus
from tools.atgb.isolation import repo_root

ROOT = repo_root()


def _implicit_stores() -> set[Path]:
    temporary = ROOT / "development" / "tmp"
    if not temporary.is_dir():
        return set()
    return {path for path in temporary.glob("atgb-*") if path.is_dir()}


def _scenario(scenario_id: str = "S01") -> dict:
    loaded = load_corpus(ROOT, partitions=None)
    return next(item for item in loaded["scenarios"] if item["scenario_id"] == scenario_id), loaded["manifest"]


def test_successful_implicit_store_is_removed_and_explicit_store_remains(tmp_path: Path):
    before = _implicit_stores()
    run_benchmark(RunConfig(mode="provider_disabled_simulated", scenario_ids=("S01",)), root=ROOT)
    assert _implicit_stores() == before
    kept = run_benchmark(
        RunConfig(
            mode="provider_disabled_simulated",
            scenario_ids=("S01",),
            keep_stores=True,
            output_dir=tmp_path / "kept",
        ),
        root=ROOT,
    )
    stores = list((tmp_path / "kept" / "stores").iterdir())
    assert kept["scenario_records"][0]["isolation"]["accepted"] is True
    assert len(stores) == 1
    assert (stores[0] / ".atgb-isolated").is_file()
    assert _implicit_stores() == before


def test_early_initialization_failure_removes_the_owned_store(monkeypatch):
    before = _implicit_stores()
    created: list[Path] = []

    def fail(candidate, **kwargs):
        path = Path(candidate)
        created.append(path)
        path.mkdir(parents=True, exist_ok=True)
        (path / "partial.txt").write_text("partial", encoding="utf-8")
        raise RuntimeError("injected early failure")

    monkeypatch.setattr("tools.atgb.driver.prepare_isolated_store", fail)
    with pytest.raises(RuntimeError, match="injected early failure"):
        run_benchmark(RunConfig(mode="provider_disabled_simulated", scenario_ids=("S01",)), root=ROOT)
    assert created and not created[0].exists()
    assert _implicit_stores() == before


def test_cleanup_failure_is_reported_for_success_and_preserves_execution_failure(tmp_path, monkeypatch, capsys):
    before = _implicit_stores()

    def fail_remove(path):
        raise OSError("injected cleanup failure")

    monkeypatch.setattr("tools.execution_workspace.shutil.rmtree", fail_remove)
    with pytest.raises(OSError, match="injected cleanup failure"):
        run_benchmark(RunConfig(mode="provider_disabled_simulated", scenario_ids=("S01",)), root=ROOT)
    created = _implicit_stores() - before
    captured = capsys.readouterr()
    assert len(created) == 1
    retained = next(iter(created))
    assert str(retained) in captured.err

    def fail_run(*args, **kwargs):
        raise RuntimeError("injected execution failure")

    monkeypatch.setattr("tools.atgb.driver._simulate_scenario", fail_run)
    with pytest.raises(RuntimeError, match="injected execution failure"):
        run_benchmark(RunConfig(mode="provider_disabled_simulated", scenario_ids=("S01",)), root=ROOT)
    captured = capsys.readouterr()
    failed = _implicit_stores() - created - before
    assert len(failed) == 1
    assert str(next(iter(failed))) in captured.err
    kept = tmp_path / "caller-owned"
    kept.mkdir()
    marker = kept / "historical.txt"
    marker.write_text("keep", encoding="utf-8")
    assert marker.read_text(encoding="utf-8") == "keep"
    monkeypatch.undo()
    import shutil

    for path in created | failed:
        shutil.rmtree(path)


def test_concurrent_implicit_stores_stay_distinct(monkeypatch):
    before = _implicit_stores()
    barrier = threading.Barrier(2)
    seen: list[Path] = []
    lock = threading.Lock()
    original = __import__("tools.atgb.driver", fromlist=["prepare_isolated_store"]).prepare_isolated_store

    def pause(candidate, **kwargs):
        path = Path(candidate)
        with lock:
            seen.append(path)
        barrier.wait(timeout=30)
        assert path.is_dir()
        return original(candidate, **kwargs)

    monkeypatch.setattr("tools.atgb.driver.prepare_isolated_store", pause)
    errors: list[BaseException] = []

    def once():
        try:
            run_benchmark(RunConfig(mode="provider_disabled_simulated", scenario_ids=("S01",)), root=ROOT)
        except BaseException as exc:  # noqa: BLE001 - the test records worker failures
            errors.append(exc)

    workers = [threading.Thread(target=once) for _ in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=60)
    assert errors == []
    assert len(seen) == 2 and seen[0] != seen[1]
    assert _implicit_stores() == before


def test_caller_owned_store_is_not_deleted_when_initialization_fails(tmp_path: Path, monkeypatch, capsys):
    before = _implicit_stores()
    scenario, manifest = _scenario()

    def fail(candidate, **kwargs):
        path = Path(candidate)
        path.mkdir(parents=True, exist_ok=True)
        (path / "partial.txt").write_text("partial", encoding="utf-8")
        raise RuntimeError("injected caller-store failure")

    monkeypatch.setattr("tools.atgb.driver.prepare_isolated_store", fail)
    config = RunConfig(
        mode="provider_disabled_simulated",
        scenario_ids=("S01",),
        keep_stores=True,
        output_dir=tmp_path / "explicit",
    )
    with pytest.raises(RuntimeError, match="injected caller-store failure"):
        _run_scenario(
            scenario,
            manifest=manifest,
            config=config,
            repo=ROOT,
            player_campaign=ROOT / "data",
            started=0.0,
            provider_calls=0,
            provider_calls_known=True,
            tokens=0,
            token_status="recorded",
            cost_total=0.0,
            cost_status="recorded",
        )
    stores = list((tmp_path / "explicit" / "stores").iterdir())
    assert len(stores) == 1
    assert (stores[0] / "partial.txt").is_file()
    assert str(stores[0]) in capsys.readouterr().err
    assert _implicit_stores() == before
