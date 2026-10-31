"""Infrastructure checks for the ATGB harness.

These tests do not score conversational competence and do not call a provider.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from tools.atgb import EVIDENCE_INFRASTRUCTURE
from tools.atgb.budget import Budget, BudgetError
from tools.atgb.driver import (
    SIMULATED_ORIGIN,
    SIMULATED_RESPONSE,
    LiveRunRefused,
    RunConfig,
    project_for_comparison,
    run_benchmark,
)
from tools.atgb.fixtures import FixtureError, load_corpus, partition_counts
from tools.atgb.isolation import (
    UnsafeBenchmarkDataDir,
    canonical_data_dir,
    prepare_isolated_store,
    repo_root,
)
from tools.atgb.results import apply_scores

ROOT = repo_root()
CATALOG = ROOT / "development" / "reports" / "atgb_01_scenario_catalog.md"
CANONICAL_FILES = (
    "session.json",
    "session_log.jsonl",
    "world.json",
    "combat.json",
)


def _hashes() -> dict[str, str]:
    data = canonical_data_dir(ROOT)
    found = {}
    for name in CANONICAL_FILES:
        path = data / name
        found[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing"
    return found


def _catalog_player_lines() -> list[str]:
    return re.findall(r"^Player: `(.+)`\s*$", CATALOG.read_text(encoding="utf-8"), re.MULTILINE)


def test_catalog_lines_and_partitions_match_the_adopted_fixtures():
    loaded = load_corpus(ROOT)
    counts = partition_counts(loaded["scenarios"])
    assert counts == {
        "development_visible": 25,
        "related_variation": 4,
        "held_out": 8,
        "total": 37,
    }
    lines = [
        turn["player_input"]
        for scenario in loaded["scenarios"]
        for turn in scenario["turns"]
    ]
    assert lines == _catalog_player_lines()
    by_id = {scenario["scenario_id"]: scenario for scenario in loaded["scenarios"]}
    assert by_id["S07"]["partition"] == "held_out"
    assert by_id["S07"]["catalog_partition"] == "development-visible"
    assert by_id["S07"]["evidence_status"] == "held_out_previously_exposed"
    assert by_id["S09"]["evidence_status"] == "held_out_previously_exposed"
    assert by_id["S10"]["evidence_status"] == "held_out_previously_exposed"
    assert by_id["S08"]["partition"] == "related_variation"
    catalog = CATALOG.read_text(encoding="utf-8")
    assert "| S07 In the queue | development-visible |" in catalog
    joined = json.dumps(loaded["scenarios"])
    assert "At least two visible public facts" in joined
    assert "The start time is not known or not posted" in joined
    assert "necessary_pass" in joined
    assert "expected_gm_text" not in joined
    assert "exact_response" not in joined


def test_loader_rejects_an_unknown_partition():
    with pytest.raises(FixtureError):
        load_corpus(ROOT, partitions=("tuning_set",))


def test_unsafe_data_directories_are_rejected_without_touching_canonical_files():
    before = _hashes()
    with pytest.raises(UnsafeBenchmarkDataDir):
        prepare_isolated_store(ROOT / "data", scenario_id="S01", repo=ROOT)
    occupied = ROOT / "development" / "tmp" / "atgb-occupied-check"
    occupied.mkdir(parents=True, exist_ok=True)
    (occupied / "session.json").write_text("{}\n", encoding="utf-8")
    try:
        with pytest.raises(UnsafeBenchmarkDataDir):
            prepare_isolated_store(occupied, scenario_id="S01", repo=ROOT)
    finally:
        (occupied / "session.json").unlink(missing_ok=True)
        occupied.rmdir()
    assert _hashes() == before


def test_each_scenario_gets_a_new_store_and_cannot_be_reused():
    first = ROOT / "development" / "tmp" / "atgb-store-a"
    second = ROOT / "development" / "tmp" / "atgb-store-b"
    for path in (first, second):
        if path.exists():
            import shutil

            shutil.rmtree(path)
    prepared_a = prepare_isolated_store(first, scenario_id="S01", repo=ROOT)
    prepared_b = prepare_isolated_store(second, scenario_id="S02", repo=ROOT)
    try:
        assert prepared_a != prepared_b
        assert not (prepared_a / "session.json").exists()
        assert (prepared_a / "scenes" / "frontier_gate.json").is_file()
        with pytest.raises(UnsafeBenchmarkDataDir):
            prepare_isolated_store(prepared_a, scenario_id="S03", repo=ROOT)
    finally:
        import shutil

        shutil.rmtree(prepared_a, ignore_errors=True)
        shutil.rmtree(prepared_b, ignore_errors=True)


def test_simulated_run_preserves_order_labels_responses_and_leaves_canonical_data_alone(tmp_path: Path):
    before = _hashes()
    result = run_benchmark(
        RunConfig(mode="provider_disabled_simulated", output_dir=tmp_path / "run"),
        root=ROOT,
    )
    assert _hashes() == before
    assert result["evidence_distinction"] == EVIDENCE_INFRASTRUCTURE
    assert result["gameplay_performance_claim"] is False
    assert [turn["turn_id"] for turn in result["turns"]] == [
        turn["turn_id"] for _scenario, turn in (
            (scenario, turn)
            for scenario in load_corpus(ROOT)["scenarios"]
            for turn in scenario["turns"]
        )
    ]
    assert [turn["order"] for turn in result["turns"] if turn["scenario_id"] == "S03"] == [0, 1, 2, 3, 4]
    assert {turn["response_origin"] for turn in result["turns"]} == {SIMULATED_ORIGIN}
    assert {turn["response_text"] for turn in result["turns"]} == {SIMULATED_RESPONSE}
    assert all(turn["simulated"] is True for turn in result["turns"])
    assert all(turn["telemetry"]["elapsed_ms"]["status"] == "unavailable" for turn in result["turns"])
    assert all(turn["telemetry"]["input_tokens"]["value"] is None for turn in result["turns"])
    assert all(turn["judgment"]["interpretation"] == "unchecked" for turn in result["turns"])
    assert "not an Ashen Thrones Gameplay Benchmark performance result" in result["report"]
    worksheet = json.loads((tmp_path / "run" / "worksheet.json").read_text(encoding="utf-8"))
    rendered = (tmp_path / "run" / "worksheet.md").read_text(encoding="utf-8")
    rows = [turn for conversation in worksheet["conversations"] for turn in conversation["turns"]]
    assert len(rows) == 37
    assert rows[0]["interpretation_assessment"] == "unchecked"
    assert rows[0]["response_assessment"] == "unchecked"
    assert rows[0]["authority_assessment"] == "unchecked"
    assert "simulated test double" in worksheet["banner"].lower() or "simulated" in worksheet["banner"].lower()
    assert "Interpretation assessment" in rendered
    assert "Conversation quality" in rendered
    assert all(conversation["qualitative"]["scored"] is False for conversation in worksheet["conversations"])
    again = run_benchmark(RunConfig(mode="provider_disabled_simulated"), root=ROOT)
    assert project_for_comparison(result) == project_for_comparison(again)


def test_elapsed_ceiling_stops_before_mutation_and_live_mode_is_refused(tmp_path: Path):
    before = _hashes()
    stopped = run_benchmark(
        RunConfig(
            mode="provider_disabled_simulated",
            output_dir=tmp_path / "stopped",
            budget=Budget(max_elapsed_seconds=0),
        ),
        root=ROOT,
    )
    assert stopped["turns"] == []
    assert stopped["stop_reason"] == "elapsed_time_ceiling"
    assert stopped["gameplay_performance_claim"] is False
    assert _hashes() == before
    with pytest.raises(LiveRunRefused):
        run_benchmark(RunConfig(mode="live_provider", budget=Budget(max_provider_calls=1, max_elapsed_seconds=1)), root=ROOT)
    with pytest.raises(BudgetError):
        run_benchmark(
            RunConfig(
                mode="live_provider",
                confirm_live_provider=True,
                budget=Budget(max_elapsed_seconds=1),
            ),
            root=ROOT,
        )
    with pytest.raises(BudgetError):
        Budget(max_estimated_cost=1.0).validate(mode="provider_disabled_simulated")


def test_human_scores_stay_separate_and_do_not_make_a_simulated_run_a_gameplay_claim(tmp_path: Path):
    result = run_benchmark(RunConfig(mode="provider_disabled_simulated", scenario_ids=("S01",)), root=ROOT)
    scored = apply_scores(
        result,
        {
            "turns": {
                "S01.1": {
                    "interpretation": "pass",
                    "response": "uncertain",
                    "authority": "pass",
                    "severity": "uncertain",
                    "clarification": "none",
                    "continuity": "not_applicable",
                    "human_review_status": "HUMAN_AMBIGUOUS",
                    "reviewer_notes": "The double is not a reply.",
                }
            },
            "conversations": {"S01": {"observations": ["mechanical or validation-like dialogue"], "notes": "Not a score."}},
        },
    )
    first = scored["turns"][0]["judgment"]
    assert first["interpretation"] == "pass"
    assert first["response"] == "uncertain"
    assert first["authority"] == "pass"
    assert first["acceptable"] == "not_established"
    assert scored["gameplay_performance_claim"] is False
    assert scored["conversations"][0]["qualitative_observations"] == ["mechanical or validation-like dialogue"]
    with pytest.raises(ValueError):
        apply_scores(result, {"turns": {"S01.1": {"response": "excellent"}}})


def test_production_modules_do_not_import_the_benchmark():
    game = ROOT / "game"
    for path in game.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        assert "tools.atgb" not in text
        assert "run_atgb" not in text
    harness = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tools" / "atgb").rglob("*.py"))
    assert "evaluate_playability(" not in harness


def test_provider_disabled_host_uses_chat_and_isolates_state(tmp_path: Path):
    before = _hashes()
    result = run_benchmark(
        RunConfig(
            mode="provider_disabled_host",
            scenario_ids=("S06",),
            output_dir=tmp_path / "host",
            worker_timeout_seconds=240,
        ),
        root=ROOT,
    )
    assert _hashes() == before
    assert result["gameplay_performance_claim"] is False
    assert result["evidence_distinction"] == "host_deterministic"
    assert result["turns"], result.get("scenario_records")
    assert [turn["turn_id"] for turn in result["turns"]] == ["S06.1", "S06.2", "S06.3", "S06.4"]
    assert all(turn["simulated"] is False for turn in result["turns"])
    assert all(turn["response_origin"] == "host_provider_disabled" for turn in result["turns"])
    assert all("SIMULATED TEST DOUBLE" not in turn["response_text"] for turn in result["turns"])
    assert result["stop_reason"] is None
    fallback = result["turns"][3]
    assert fallback["response_text"] == "Provider calls are disabled for this run, so no live narration was generated."
    assert fallback["provider_calls_disabled"] is True
    assert fallback["provider_request_sent"] is False
    assert fallback["error"] is None
    record = result["scenario_records"][0]
    assert record["isolation"]["reset_invoked"] is True
    assert record["isolation"]["canonical_data_used_as_store"] is False
    assert "not an Ashen Thrones Gameplay Benchmark performance result" in result["report"]
