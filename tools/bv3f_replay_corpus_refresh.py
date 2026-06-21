#!/usr/bin/env python3
"""BV3F — regenerate canonical FEM corpus under current BV3E gate code."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import game.api as api_mod
import game.storage as st
from game.api import app
from fastapi.testclient import TestClient
from tests.helpers.golden_replay_fixtures import gm_response, golden_replay_chat_stubs, seed_frontier_gate_world

HYGIENE_ROOT = ROOT / "artifacts" / "scene_canon_hygiene_runtime"
REFRESH_DIR = ROOT / "artifacts" / "bv3f_replay_refresh"
SESSION_LOG_BACKUP = REFRESH_DIR / "session_log.pre_refresh.jsonl"
REFRESH_MANIFEST = REFRESH_DIR / "corpus_refresh_manifest.json"
OBSERVE_PROMPTS = (
    "I look around.",
    "I scan the notice board and watch who reacts.",
    "I keep my eyes on the gate serjeant and the runner.",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _patch_repo_data_dir(base: Path) -> None:
    data_dir = base / "data"
    scenes_dir = data_dir / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    if base.resolve() != ROOT.resolve():
        for src in (ROOT / "data" / "scenes").glob("*.json"):
            shutil.copy2(src, scenes_dir / src.name)
        for name in (
            "character.json",
            "campaign.json",
            "session.json",
            "world.json",
            "combat.json",
            "conditions.json",
        ):
            src = ROOT / "data" / name
            if src.is_file():
                shutil.copy2(src, data_dir / name)
    st.BASE_DIR = base
    st.DATA_DIR = data_dir
    st.SCENES_DIR = scenes_dir
    st.CHARACTER_PATH = data_dir / "character.json"
    st.CAMPAIGN_PATH = data_dir / "campaign.json"
    st.SESSION_PATH = data_dir / "session.json"
    st.WORLD_PATH = data_dir / "world.json"
    st.COMBAT_PATH = data_dir / "combat.json"
    st.CONDITIONS_PATH = data_dir / "conditions.json"
    st.SESSION_LOG_PATH = data_dir / "session_log.jsonl"


def _observe_playthrough(*, base: Path, prompt_index: int) -> dict[str, int]:
    _patch_repo_data_dir(base)
    st.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    api_mod.log_upstream_api_preflight_at_startup = lambda: None

    call_count = 0

    def _gpt(_messages):
        nonlocal call_count
        call_count += 1
        return gm_response(
            (
                'Near the checkpoint a guard shifts his weight. "Keep moving," he says, '
                f"watching the queue at pass {call_count}."
            )
        )

    class _Patch:
        def setattr(self, target, value):
            if target == "game.api.call_gpt":
                api_mod.call_gpt = value
            elif target == "game.api.parse_social_intent":
                api_mod.parse_social_intent = value
            elif target == "game.api.parse_exploration_intent":
                api_mod.parse_exploration_intent = value
            elif target == "game.api.parse_intent":
                api_mod.parse_intent = value
            else:
                raise AttributeError(target)

    golden_replay_chat_stubs(_Patch(), gpt_callback=_gpt, suppress_exploration=False)
    seed_frontier_gate_world()

    with TestClient(app) as client:
        client.post("/api/new_campaign")
        client.post("/api/start_campaign")
        prompt = OBSERVE_PROMPTS[prompt_index % len(OBSERVE_PROMPTS)]
        client.post("/api/chat", json={"text": prompt})

    return {"prompt_index": prompt_index, "log_lines": len(st.load_log()), "gpt_calls": call_count}


def _snapshot_baseline_metrics() -> None:
    """Preserve pre-refresh BV3D/BV3E metric artifacts for delta comparison."""
    REFRESH_DIR.mkdir(parents=True, exist_ok=True)
    for name in (
        "bv3a_referential_clarity_metrics.json",
        "bv3d_eligibility_report.json",
        "bv3e_eligibility_metrics.json",
        "bv3e_shape_simulation.json",
    ):
        src = ROOT / "artifacts" / name
        if src.is_file():
            shutil.copy2(src, REFRESH_DIR / f"pre_refresh.{name}")


def refresh_session_log(*, hygiene_batches: int) -> dict:
    REFRESH_DIR.mkdir(parents=True, exist_ok=True)
    src = ROOT / "data" / "session_log.jsonl"
    if src.is_file():
        shutil.copy2(src, SESSION_LOG_BACKUP)

    archive_hygiene = REFRESH_DIR / f"scene_canon_hygiene_runtime.{_utc_now().replace(':', '')}"
    if HYGIENE_ROOT.is_dir():
        shutil.copytree(HYGIENE_ROOT, archive_hygiene, dirs_exist_ok=True)
        shutil.rmtree(HYGIENE_ROOT)
    HYGIENE_ROOT.mkdir(parents=True, exist_ok=True)

    observe_runs: list[dict] = []
    for index in range(len(OBSERVE_PROMPTS)):
        observe_runs.append(_observe_playthrough(base=ROOT, prompt_index=index))

    hygiene_runs: list[dict] = []
    for batch in range(hygiene_batches):
        run_dir = HYGIENE_ROOT / uuid.uuid4().hex
        run_dir.mkdir(parents=True, exist_ok=False)
        stats = _observe_playthrough(base=run_dir, prompt_index=batch)
        hygiene_runs.append({"path": str(run_dir.relative_to(ROOT)).replace("\\", "/"), **stats})

    best = max(observe_runs, key=lambda row: row["log_lines"])
    best_index = int(best["prompt_index"])
    _observe_playthrough(base=ROOT, prompt_index=best_index)

    return {
        "generated_at": _utc_now(),
        "session_log_backup": str(SESSION_LOG_BACKUP.relative_to(ROOT)).replace("\\", "/"),
        "hygiene_archive": str(archive_hygiene.relative_to(ROOT)).replace("\\", "/") if archive_hygiene.is_dir() else None,
        "observe_runs": observe_runs,
        "hygiene_runs": hygiene_runs,
        "canonical_session_log_lines": len(st.load_log()),
    }


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\n{result.stderr or result.stdout}")


def refresh_projection_artifacts() -> None:
    _run([sys.executable, str(ROOT / "tools" / "fallback_projection_gap_reality_audit.py")])
    _run([sys.executable, str(ROOT / "tools" / "projection_drift_watch.py")])


def refresh_manifest() -> None:
    _run([sys.executable, str(ROOT / "tools" / "refresh_protected_replay_manifest.py"), "--check"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hygiene-batches", type=int, default=30, help="Hygiene runtime batches to regenerate.")
    parser.add_argument("--skip-session-log", action="store_true", help="Skip session_log/hygiene regeneration.")
    parser.add_argument("--skip-projection", action="store_true", help="Skip projection artifact refresh.")
    parser.add_argument("--skip-manifest", action="store_true", help="Skip protected replay manifest check.")
    parser.add_argument("--skip-baseline-snapshot", action="store_true", help="Skip pre-refresh metric snapshot.")
    args = parser.parse_args(argv)

    if not args.skip_baseline_snapshot:
        _snapshot_baseline_metrics()
        snapshot_step = "baseline_metrics_snapshot"
    else:
        snapshot_step = None

    manifest: dict = {"schema_version": 1, "generated_at": _utc_now(), "phase": "BV3F", "steps": []}
    if snapshot_step:
        manifest["steps"].append(snapshot_step)
    if not args.skip_session_log:
        manifest["corpus"] = refresh_session_log(hygiene_batches=max(1, int(args.hygiene_batches)))
        manifest["steps"].append("session_log_and_hygiene_refresh")
    if not args.skip_projection:
        refresh_projection_artifacts()
        manifest["steps"].append("projection_artifact_refresh")
    if not args.skip_manifest:
        refresh_manifest()
        manifest["steps"].append("protected_replay_manifest_check")

    REFRESH_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    REFRESH_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
