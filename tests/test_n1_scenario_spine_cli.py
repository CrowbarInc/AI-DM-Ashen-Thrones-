"""Operational tests for ``tools/run_n1_scenario_spine_validation.py`` (N1 CLI surface)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tests.helpers.n1_scenarios import n1_registered_scenario_ids


def _assert_n1_session_health_artifact_non_empty(body: dict) -> None:
    """Guard against accidental empty harness payloads in CLI runs."""
    assert int(body.get("turn_count") or 0) > 0
    assert body.get("per_turn_observations"), "expected non-empty per_turn_observations"
    assert body.get("run_id"), "expected non-empty run_id"
from tests.validation_coverage_registry import validate_registry

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "tools" / "run_n1_scenario_spine_validation.py"


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def test_validation_registry_still_valid() -> None:
    errs = validate_registry()
    assert not errs, "\n".join(errs)


def test_cli_list_json_matches_registered_ids_order() -> None:
    r = _run_cli(["list", "--json"])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    ids = [row["scenario_id"] for row in data]
    assert ids == list(n1_registered_scenario_ids())
    assert ids == sorted(ids)
    for row in data:
        assert list(row.keys()) == sorted(row.keys())
        assert row["branches"] == sorted(row["branches"])


def test_cli_list_json_is_deterministic() -> None:
    a = _run_cli(["list", "--json"])
    b = _run_cli(["list", "--json"])
    assert a.stdout == b.stdout


def test_cli_run_single_scenario_emits_artifacts(tmp_path: Path) -> None:
    art = tmp_path / "n1_out"
    r = _run_cli(
        [
            "run",
            "--scenario",
            "n1_progression_chain",
            "--artifact-dir",
            str(art),
            "--seed",
            "20260422",
        ],
    )
    assert r.returncode == 0, r.stderr + r.stdout
    sh = art / "n1_progression_chain" / "n1_main" / "session_health.json"
    cr = art / "n1_progression_chain" / "n1_main" / "continuity_report.json"
    assert sh.is_file()
    assert cr.is_file()
    sh_body = json.loads(sh.read_text(encoding="utf-8"))
    assert sh_body["artifact_kind"] == "n1_session_health"
    _assert_n1_session_health_artifact_non_empty(sh_body)
    cr_body = json.loads(cr.read_text(encoding="utf-8"))
    assert "merged_reason_codes" in cr_body
    assert cr_body["merged_reason_codes"] == sorted(cr_body["merged_reason_codes"])
    assert cr_body.get("issues") is not None


def test_cli_run_all_scenarios_zero_exit(tmp_path: Path) -> None:
    art = tmp_path / "n1_all"
    r = _run_cli(["run", "--all", "--artifact-dir", str(art)])
    assert r.returncode == 0, r.stderr + r.stdout
    for sid in n1_registered_scenario_ids():
        assert (art / sid).is_dir()


def test_cli_run_compare_branches_emits_branch_comparison(tmp_path: Path) -> None:
    art = tmp_path / "n1_branch"
    r = _run_cli(
        [
            "run",
            "--scenario",
            "n1_branch_divergence",
            "--compare-branches",
            "--artifact-dir",
            str(art),
        ],
    )
    assert r.returncode == 0, r.stderr + r.stdout
    cmp_path = art / "n1_branch_divergence" / "branch_comparison.json"
    assert cmp_path.is_file()
    bundle = json.loads(cmp_path.read_text(encoding="utf-8"))
    assert bundle["branch_comparison_summary"]["divergence_detected"] is True
    codes = {i["reason_code"] for i in bundle["branch_analyzer_issues"]}
    assert "N1_BRANCH_DIVERGENT_FINAL_SCENE_ID" in codes
    for bid in ("n1_branch_left", "n1_branch_right"):
        assert (art / "n1_branch_divergence" / bid / "continuity_report.json").is_file()


def test_cli_session_health_stable_across_runs(tmp_path: Path) -> None:
    def _once(base: Path) -> str:
        r = _run_cli(
            [
                "run",
                "--scenario",
                "n1_anchor_persistence",
                "--artifact-dir",
                str(base),
                "--seed",
                "99",
                "--max-turns",
                "64",
            ],
        )
        assert r.returncode == 0, r.stderr + r.stdout
        p = base / "n1_anchor_persistence" / "n1_main" / "session_health.json"
        return p.read_text(encoding="utf-8")

    a = _once(tmp_path / "a")
    b = _once(tmp_path / "b")
    assert a == b


def test_cli_unknown_scenario_exit(tmp_path: Path) -> None:
    r = _run_cli(["run", "--scenario", "not_a_registered_n1_scenario", "--artifact-dir", str(tmp_path)])
    assert r.returncode == 2
    assert "unknown" in r.stderr.lower()


def test_cli_rejects_non_integer_max_turns(tmp_path: Path) -> None:
    r = _run_cli(
        [
            "run",
            "--scenario",
            "n1_progression_chain",
            "--artifact-dir",
            str(tmp_path),
            "--max-turns",
            "not_an_int",
        ],
    )
    assert r.returncode == 2
    assert "max-turns" in (r.stderr + r.stdout).lower()


def test_cli_rejects_zero_max_turns(tmp_path: Path) -> None:
    r = _run_cli(
        [
            "run",
            "--scenario",
            "n1_progression_chain",
            "--artifact-dir",
            str(tmp_path),
            "--max-turns",
            "0",
        ],
    )
    assert r.returncode == 2
    assert "max-turns" in r.stderr.lower()


def test_cli_rejects_max_turns_below_scripted(tmp_path: Path) -> None:
    r = _run_cli(
        [
            "run",
            "--scenario",
            "n1_anchor_persistence",
            "--artifact-dir",
            str(tmp_path),
            "--max-turns",
            "1",
        ],
    )
    assert r.returncode == 2
    assert "scripted" in r.stderr and "minimum" in r.stderr


def test_cli_rejects_invalid_branch_on_linear_scenario(tmp_path: Path) -> None:
    r = _run_cli(
        [
            "run",
            "--scenario",
            "n1_progression_chain",
            "--artifact-dir",
            str(tmp_path),
            "--branch",
            "n1_branch_left",
        ],
    )
    assert r.returncode == 2
    assert "invalid --branch" in r.stderr
    assert "n1_main" in r.stderr


def test_cli_rejects_compare_branches_on_linear_scenario(tmp_path: Path) -> None:
    r = _run_cli(
        [
            "run",
            "--scenario",
            "n1_anchor_persistence",
            "--artifact-dir",
            str(tmp_path),
            "--compare-branches",
        ],
    )
    assert r.returncode == 2
    assert "does not support --compare-branches" in r.stderr


def test_cli_linear_run_does_not_emit_branch_comparison(tmp_path: Path) -> None:
    art = tmp_path / "linear_only"
    r = _run_cli(["run", "--scenario", "n1_progression_chain", "--artifact-dir", str(art)])
    assert r.returncode == 0, r.stderr + r.stdout
    assert not (art / "n1_progression_chain" / "branch_comparison.json").exists()


def test_cli_run_creates_deep_artifact_dir(tmp_path: Path) -> None:
    deep = tmp_path / "a" / "b" / "c" / "n1_deep"
    r = _run_cli(["run", "--scenario", "n1_progression_chain", "--artifact-dir", str(deep)])
    assert r.returncode == 0, r.stderr + r.stdout
    assert (deep / "n1_progression_chain" / "n1_main" / "session_health.json").is_file()


def test_cli_stdout_line_has_stable_key_order(tmp_path: Path) -> None:
    art = tmp_path / "o"
    r = _run_cli(["run", "--scenario", "n1_progression_chain", "--artifact-dir", str(art)])
    assert r.returncode == 0, r.stderr + r.stdout
    line = r.stdout.strip().splitlines()[-1]
    frags = (
        "scenario_id=",
        " branch_id=",
        " run_id=",
        " final_session_verdict=",
        " severity_counters=",
        " merged_reason_codes_top=",
        " session_health=",
        " continuity_report=",
        " branch_comparison=",
    )
    pos = 0
    for frag in frags:
        idx = line.find(frag, pos)
        assert idx != -1, (frag, line)
        pos = idx + len(frag)


def test_cli_compare_emits_branch_comparison_and_marks_stdout(tmp_path: Path) -> None:
    art = tmp_path / "cmp_stdout"
    r = _run_cli(
        ["run", "--scenario", "n1_branch_divergence", "--compare-branches", "--artifact-dir", str(art)],
    )
    assert r.returncode == 0, r.stderr + r.stdout
    lines = [ln for ln in r.stdout.strip().splitlines() if ln.strip()]
    assert len(lines) == 3
    assert lines[-1].startswith("scenario_id=n1_branch_divergence branch_id=*compare*")
    assert "branch_comparison=" in lines[-1] and "branch_comparison=-" not in lines[-1]
    for ln in lines[:-1]:
        assert "branch_comparison=-" in ln
