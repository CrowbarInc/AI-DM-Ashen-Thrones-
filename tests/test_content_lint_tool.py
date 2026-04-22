"""Tool-level tests for ``tools/run_content_lint.py`` (CLI contract, exit codes, subset policy).

Engine rule matrices live in ``tests/test_content_lint.py``; this module pins process and
artifact semantics only.

Note: both blocking lint failures and operator/file failures currently exit with code ``1``;
``2`` is reserved for ``--fail-on-warnings`` when there are warnings but no errors.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pytest

from game.content_lint import lint_all_content

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "tools" / "run_content_lint.py"


def _run_cli(
    *argv: str,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(RUNNER), *argv]
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _minimal_scene(scene_id: str) -> Dict[str, Any]:
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


def _warning_only_scene(scene_id: str) -> Dict[str, Any]:
    """Heuristic warning (no strict errors): missing player anchor."""
    return {
        "scene": {
            "id": scene_id,
            "location": "Somewhere",
            "summary": "A plain room with chairs.",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "interactables": [],
            "actions": [],
        }
    }


def _write_scene(scenes_dir: Path, scene_id: str, envelope: Dict[str, Any]) -> None:
    (scenes_dir / f"{scene_id}.json").write_text(
        json.dumps(envelope, ensure_ascii=False),
        encoding="utf-8",
    )


def _mk_scenes_dir(tmp_path: Path) -> Path:
    """Scene envelopes only (so sibling ``--json-out`` files are never picked up as scenes)."""
    root = tmp_path / "scenes"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _try_load_world_dict(root: Path) -> Optional[Dict[str, Any]]:
    """Same policy as ``tools/run_content_lint.py`` (optional ``data/world.json``)."""
    path = root / "data" / "world.json"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    try:
        w = json.loads(text)
    except json.JSONDecodeError:
        return None
    return w if isinstance(w, dict) else None


def _engine_report_for_runner_disk_state(
    scenes_dir: Path,
    *,
    scene_ids_filter: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Mirror ``main()`` load + ``lint_all_content`` kwargs (no world.json dependency)."""
    all_ids = sorted(p.stem for p in scenes_dir.glob("*.json"))
    reference_known: Set[str] = set(all_ids)
    wanted = sorted(scene_ids_filter) if scene_ids_filter is not None else list(all_ids)
    if scene_ids_filter is not None:
        unknown = sorted(set(wanted) - reference_known)
        assert not unknown, unknown
        load_order = sorted(wanted)
        subset = True
    else:
        load_order = list(all_ids)
        subset = False
    scenes: Dict[str, Dict[str, Any]] = {}
    for sid in load_order:
        text = (scenes_dir / f"{sid}.json").read_text(encoding="utf-8").strip()
        scenes[sid] = json.loads(text)
    report = lint_all_content(
        scenes,
        world=_try_load_world_dict(REPO_ROOT),
        graph_seed_scene_ids=None,
        reference_known_scene_ids=reference_known if subset else None,
        graph_known_scene_ids=set(scenes.keys()) if subset else None,
    )
    return report.as_dict()


def test_cli_clean_authored_content_exit_zero(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    _write_scene(sd, "hub", _minimal_scene("hub"))
    r = _run_cli("--scenes-dir", str(sd))
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "errors=0 warnings=0" in r.stdout
    assert "graph.unreachable_scene" not in r.stdout


def test_cli_warnings_only_exit_zero(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    _write_scene(sd, "lonely", _warning_only_scene("lonely"))
    r = _run_cli("--scenes-dir", str(sd))
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "errors=0" in r.stdout
    assert "warnings=" in r.stdout
    assert int(r.stdout.split("warnings=")[1].split()[0]) >= 1


def test_cli_warnings_only_fail_on_warnings_exit_two(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    _write_scene(sd, "lonely", _warning_only_scene("lonely"))
    r = _run_cli("--scenes-dir", str(sd), "--fail-on-warnings")
    assert r.returncode == 2, (
        "warnings-only with --fail-on-warnings must exit 2 (distinct from blocking lint / "
        "operator failures, which use 1)"
    )
    assert r.stderr == ""


def test_cli_blocking_lint_errors_exit_one(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    bad = _minimal_scene("a")
    bad["scene"]["exits"] = [{"label": "Void", "target_scene_id": "not_a_real_scene"}]
    _write_scene(sd, "a", bad)
    r = _run_cli("--scenes-dir", str(sd))
    assert r.returncode == 1, (r.stdout, r.stderr)
    assert "exit.unknown_target" in r.stdout


def test_cli_unknown_scene_id_exit_one_clear_stderr(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    _write_scene(sd, "hub", _minimal_scene("hub"))
    r = _run_cli("--scenes-dir", str(sd), "--scene-id", "hub", "--scene-id", "nope")
    assert r.returncode == 1
    assert r.stdout == ""
    assert r.stderr == "Unknown scene id(s) (no JSON on disk): nope\n"


def test_cli_invalid_json_exit_one(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    (sd / "bad.json").write_text("{ not json", encoding="utf-8")
    r = _run_cli("--scenes-dir", str(sd))
    assert r.returncode == 1
    assert "Invalid JSON" in r.stderr
    assert r.stdout == ""


def test_cli_empty_scene_file_exit_one(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    (sd / "empty.json").write_text("", encoding="utf-8")
    r = _run_cli("--scenes-dir", str(sd))
    assert r.returncode == 1
    assert "Empty scene file" in r.stderr


def test_cli_json_out_matches_canonical_as_dict(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    _write_scene(sd, "x", _minimal_scene("x"))
    out = tmp_path / "report.json"
    r = _run_cli("--scenes-dir", str(sd), "--json-out", str(out))
    assert r.returncode == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    expected = _engine_report_for_runner_disk_state(sd)
    assert written == expected
    assert set(written) == {"ok", "error_count", "warning_count", "messages", "scene_ids_checked"}


def test_cli_quiet_prints_only_summary_line(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    hub = _minimal_scene("hub")
    leaf = _minimal_scene("leaf")
    hub["scene"]["exits"] = [{"label": "Leaf", "target_scene_id": "leaf"}]
    _write_scene(sd, "hub", hub)
    _write_scene(sd, "leaf", leaf)
    r = _run_cli("--scenes-dir", str(sd), "--quiet")
    assert r.returncode == 0
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1
    assert lines[0].startswith("scenes_checked=")
    assert "errors=" in lines[0] and "warnings=" in lines[0]
    assert "[" not in r.stdout


def test_subset_cli_exit_to_unloaded_real_scene_not_unknown_target(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    hub = _minimal_scene("hub")
    leaf = _minimal_scene("leaf")
    hub["scene"]["exits"] = [{"label": "To leaf", "target_scene_id": "leaf"}]
    _write_scene(sd, "hub", hub)
    _write_scene(sd, "leaf", leaf)
    _write_scene(sd, "island", _minimal_scene("island"))
    r = _run_cli("--scenes-dir", str(sd), "--scene-id", "hub", "--json-out", str(tmp_path / "r.json"))
    assert r.returncode == 0, (r.stdout, r.stderr)
    data = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    codes = {m["code"] for m in data["messages"]}
    assert "exit.unknown_target" not in codes


def test_subset_cli_no_unreachable_warnings_for_unloaded_scenes(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    hub = _minimal_scene("hub")
    leaf = _minimal_scene("leaf")
    hub["scene"]["exits"] = [{"label": "To leaf", "target_scene_id": "leaf"}]
    _write_scene(sd, "hub", hub)
    _write_scene(sd, "leaf", leaf)
    _write_scene(sd, "island", _minimal_scene("island"))
    r_full = _run_cli("--scenes-dir", str(sd))
    assert r_full.returncode == 0
    assert any("graph.unreachable_scene" in ln and "island" in ln for ln in r_full.stdout.splitlines())
    r_sub = _run_cli("--scenes-dir", str(sd), "--scene-id", "hub")
    assert r_sub.returncode == 0
    assert "graph.unreachable_scene" not in r_sub.stdout


def test_subset_cli_exit_to_scene_not_on_disk_still_errors(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    hub = _minimal_scene("hub")
    hub["scene"]["exits"] = [{"label": "Nowhere", "target_scene_id": "ghost"}]
    _write_scene(sd, "hub", hub)
    _write_scene(sd, "leaf", _minimal_scene("leaf"))
    r = _run_cli("--scenes-dir", str(sd), "--scene-id", "hub", "--json-out", str(tmp_path / "out.json"))
    assert r.returncode == 1
    data = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert any(m.get("code") == "exit.unknown_target" for m in data["messages"])


def test_subset_graph_unreachable_only_among_loaded_ids(tmp_path: Path) -> None:
    """Graph seeds and reachability universe are the loaded subset only (via CLI)."""
    sd = _mk_scenes_dir(tmp_path)
    a = _minimal_scene("a")
    b = _minimal_scene("b")
    a["scene"]["exits"] = []
    b["scene"]["exits"] = []
    _write_scene(sd, "a", a)
    _write_scene(sd, "b", b)
    r = _run_cli("--scenes-dir", str(sd), "--scene-id", "b")
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "graph.unreachable_scene" not in r.stdout


def test_cli_json_preserves_engine_message_codes_unchanged(tmp_path: Path) -> None:
    sd = _mk_scenes_dir(tmp_path)
    dup = _minimal_scene("room")
    dup["scene"]["discoverable_clues"] = [
        {"id": "c1", "text": "First"},
        {"id": "c1", "text": "Duplicate id"},
    ]
    _write_scene(sd, "room", dup)
    out = tmp_path / "lint.json"
    r = _run_cli("--scenes-dir", str(sd), "--json-out", str(out))
    assert r.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    clue_msgs = [m for m in payload["messages"] if m["code"] == "clue.duplicate_id"]
    assert len(clue_msgs) == 1
    eng = lint_all_content({"room": dup})
    eng_msg = next(m for m in eng.messages if m.code == "clue.duplicate_id")
    assert clue_msgs[0]["message"] == eng_msg.message
    assert clue_msgs[0]["severity"] == eng_msg.severity


def test_operator_failure_exit_one_distinct_from_fail_on_warnings_doc(tmp_path: Path) -> None:
    """Invalid JSON is exit 1 (operator); do not confuse with --fail-on-warnings (exit 2)."""
    sd = _mk_scenes_dir(tmp_path)
    (sd / "x.json").write_text("{", encoding="utf-8")
    r_op = _run_cli("--scenes-dir", str(sd))
    assert r_op.returncode == 1
    (sd / "x.json").unlink(missing_ok=True)
    _write_scene(sd, "lonely", _warning_only_scene("lonely"))
    r_warn = _run_cli("--scenes-dir", str(sd), "--fail-on-warnings")
    assert r_warn.returncode == 2
