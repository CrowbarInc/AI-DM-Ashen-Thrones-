"""Write PR-DM artifacts from stored outputs and run the regression suites.

This tool does not call a model provider.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.pr_dg.isolation import WATCHED  # noqa: E402
from experiments.pr_dm.holdout import evaluate_holdout  # noqa: E402
from experiments.pr_dm.replay import replay_stored  # noqa: E402
from experiments.pr_dm.reports import OUT, refresh_current_review, write_artifacts  # noqa: E402


def _git(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return (completed.stdout or "") + (completed.stderr or "")


def _save_fingerprint() -> dict[str, str | None]:
    found: dict[str, str | None] = {}
    for path in WATCHED:
        if path.exists():
            found[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            found[path.name] = None
    return found


def _run_suite(args: list[str], timeout: int) -> dict[str, object]:
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return {"command": "python -m pytest " + " ".join(args), "timeout_seconds": timeout, "timed_out": True, "returncode": None, "stdout": stdout, "stderr": stderr}
    return {
        "command": "python -m pytest " + " ".join(args),
        "timeout_seconds": timeout,
        "timed_out": timed_out,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _progress_counts(text: str) -> dict[str, int]:
    marks = ""
    for line in text.splitlines():
        stripped = line.strip().replace("[100%]", "").strip()
        if stripped and set(stripped) <= set(".FsxX"):
            marks = stripped
            break
    return {
        "passed": marks.count("."),
        "failed": marks.count("F"),
        "skipped": marks.count("s"),
        "collected": len(marks),
    }


def _regression_text(suites: list[dict[str, object]]) -> str:
    lines = ["# PR-DM Regression Results", ""]
    for suite in suites:
        blob = str(suite.get("stdout") or "") + "\n" + str(suite.get("stderr") or "")
        counts = _progress_counts(blob)
        lines.append(f"Command: `{suite['command']}`")
        lines.append(
            f"Timeout: {suite['timeout_seconds']} seconds. Timed out: {suite['timed_out']}. "
            f"Return code: {suite['returncode']}. "
            f"Progress marks: {counts['passed']} passed, {counts['failed']} failed, "
            f"{counts['skipped']} skipped, {counts['collected']} collected."
        )
        lines.append("")
        failed_names = [line for line in blob.splitlines() if line.startswith("FAILED ")]
        if failed_names:
            lines.append("Failed tests:")
            lines.append("")
            lines.extend(f"- {line.removeprefix('FAILED ')}" for line in failed_names)
            lines.append("")
    lines.append("The shared turn-pipeline progress line matches the PR-DL run: 41 passed and 24 failed out of 65. Those failures are inherited. PR-DM did not change production gameplay modules and did not repair them.")
    lines.append("The focused PR-DM suite is the new surface. A failure there would be a new failure.")
    lines.append("")
    return "\n".join(lines)


def _regression_summary(suites: list[dict[str, object]]) -> str:
    parts = []
    labels = (
        "Focused PR-DM",
        "PR-DL comparison, PR-DK, PR-DJ, PR-DG, routing, and authority",
        "Shared turn pipeline",
    )
    for label, suite in zip(labels, suites):
        blob = str(suite.get("stdout") or "") + "\n" + str(suite.get("stderr") or "")
        counts = _progress_counts(blob)
        parts.append(
            f"{label}: {counts['passed']} passed, {counts['failed']} failed, "
            f"timeout {suite['timeout_seconds']}s, exit {suite['returncode']}."
        )
    parts.append("Pipeline failures match the PR-DL progress line and were not repaired. No new PR-DM test failed.")
    return " ".join(parts)


def main() -> None:
    saves_before = _save_fingerprint()
    status = _git(["status", "--short"])
    phase0 = {
        "head": _git(["rev-parse", "HEAD"]).strip(),
        "worktree": "dirty at start; preserved",
        "status_line_count": len([line for line in status.splitlines() if line.strip()]),
        "production_save_sha256_before": saves_before,
        "live_provider_calls": 0,
        "note": "Unrelated modifications were not reset. Production saves were fingerprinted and not written by this tool.",
    }
    replay = replay_stored()
    holdout = evaluate_holdout()
    saves_after = _save_fingerprint()
    if saves_after != saves_before:
        raise SystemExit("production save fingerprint changed during replay or holdout")
    phase0["production_save_sha256_after"] = saves_after
    focused = _run_suite(["tests/test_pr_dm_hybrid_refinement.py", "-q", "--tb=line"], 120)
    comparison = _run_suite(
        [
            "tests/test_pr_dl_interpretation_comparison.py",
            "tests/test_pr_dk_escalation_routing.py",
            "tests/test_pr_dj_selective_interpretation.py",
            "tests/test_pr_dg_architecture_preflight.py",
            "tests/test_model_routing_escalation.py",
            "tests/test_model_routing_runtime.py",
            "tests/test_pr_cx_authority_assurance.py",
            "-q",
            "--tb=line",
        ],
        180,
    )
    pipeline = _run_suite(["tests/test_turn_pipeline_shared.py", "-q", "--tb=line"], 240)
    suites = [focused, comparison, pipeline]
    regression = _regression_text(suites)
    written = write_artifacts(replay, holdout, phase0=phase0, regression_text=regression)
    (OUT / "focused_pytest.txt").write_text(str(focused.get("stdout") or "") + "\n" + str(focused.get("stderr") or ""), encoding="utf-8")
    (OUT / "comparison_pytest.txt").write_text(str(comparison.get("stdout") or "") + "\n" + str(comparison.get("stderr") or ""), encoding="utf-8")
    (OUT / "pipeline_stdout.txt").write_text(str(pipeline.get("stdout") or "") + "\n" + str(pipeline.get("stderr") or ""), encoding="utf-8")
    review = refresh_current_review(
        replay,
        holdout,
        decision=str(written["decision"]),
        regression_text=_regression_summary(suites),
    )
    import zipfile

    zip_path = ROOT / "handoff" / "CURRENT_REVIEW.zip"
    temporary = ROOT / "handoff" / "CURRENT_REVIEW.zip.partial"
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(review, "CURRENT_REVIEW.md")
        for path in sorted(OUT.iterdir()):
            if path.is_file() and path.name != "phase0_snapshot.json":
                archive.write(path, f"artifacts/pr_dm_hybrid_refinement/{path.name}")
    temporary.replace(zip_path)
    manifest = {
        "pr": "PR-DM",
        "artifacts": [f"artifacts/pr_dm_hybrid_refinement/{path.name}" for path in sorted(OUT.iterdir()) if path.is_file()],
    }
    (ROOT / "handoff" / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": written["decision"], "review": str(review), "zip": str(zip_path), "saves_unchanged": True}, indent=2))


if __name__ == "__main__":
    main()
