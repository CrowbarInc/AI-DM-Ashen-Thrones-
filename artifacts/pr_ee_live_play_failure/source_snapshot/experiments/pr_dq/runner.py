"""Write PR-DQ review artifacts and run the required suites. No provider calls."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

from experiments.pr_dq.reports import current_review, message_contract, routing, safety, tests_document
from experiments.pr_dq.slice import run_vertical_slice

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_dq_vertical_slice"
HANDOFF = ROOT / "handoff"
INHERITED_REGRESSION = ROOT / "artifacts" / "pr_dp_contract_qualification" / "PR-DP_regression_results.md"

SUITES = (
    (
        "PR-DQ",
        ["tests/test_pr_dq_ic_ooc_messages.py", "tests/test_pr_dq_vertical_slice.py", "-q", "--tb=line"],
        180,
    ),
    ("PR-DO", ["tests/test_pr_do_authority_separation.py", "-q", "--tb=line"], 120),
    ("Authority", ["tests/test_pr_cx_authority_assurance.py", "-q", "--tb=line"], 180),
    ("Conversation", ["tests/test_conversational_memory_window.py", "-q", "--tb=line"], 180),
    ("Turn pipeline", ["tests/test_turn_pipeline_shared.py", "-q", "--tb=line"], 300),
)


def _failed_nodes(text: str) -> list[str]:
    found = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("FAILED "):
            found.append(stripped.removeprefix("FAILED ").strip())
    return found


def _summary_line(combined: str) -> str:
    normalized = combined.replace("\r\n", "\n").replace("\r", "\n")
    for line in normalized.splitlines():
        stripped = line.strip()
        if stripped.startswith(("FAILED ", "PASSED ", "ERROR ")):
            continue
        if any(token in stripped for token in (" passed", " failed", " error")):
            return stripped
    bar = ""
    for line in normalized.splitlines():
        if "[100%]" in line:
            bar = line
    chunk = bar.split("[", 1)[0] if bar else ""
    marks = (
        ("passed", chunk.count(".")),
        ("failed", chunk.count("F")),
        ("errors", chunk.count("E")),
        ("skipped", chunk.count("s")),
        ("xfailed", chunk.count("x")),
        ("xpassed", chunk.count("X")),
    )
    parts = [f"{count} {name}" for name, count in marks if count]
    if parts:
        return ", ".join(parts)
    failed = len(_failed_nodes(normalized))
    if failed:
        return f"{failed} failed"
    return ""


def _run_suite(name: str, args: list[str], timeout: int) -> dict:
    env = os.environ.copy()
    env["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        return_code = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return_code = None
        timed_out = True
    combined = (stdout + "\n" + stderr).strip()
    return {
        "name": name,
        "args": args,
        "timeout": timeout,
        "timed_out": timed_out,
        "return_code": return_code,
        "summary": _summary_line(combined),
        "output": combined,
        "failed": _failed_nodes(combined),
    }


def _inherited_nodes() -> list[str]:
    if not INHERITED_REGRESSION.exists():
        return []
    return _failed_nodes(INHERITED_REGRESSION.read_text(encoding="utf-8"))


def _regression_body(rows: list[dict]) -> tuple[str, str]:
    inherited = _inherited_nodes()
    inherited_set = set(inherited)
    lines = [
        "No suite was repaired. These commands do not request live provider calls.",
        "Turn-pipeline failures that appear in the PR-DP regression file are inherited.",
        "",
        "| Suite | Timeout | Timed out | Return code | Summary |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['timeout']}s | {row['timed_out']} | {row['return_code']} | {row['summary']} |"
        )
    pipeline = next((row for row in rows if row["name"] == "Turn pipeline"), None)
    lines.extend(["", "## Inherited turn-pipeline failures", ""])
    if pipeline is None:
        lines.append("Turn pipeline did not run.")
    elif pipeline["timed_out"]:
        lines.append("Turn pipeline timed out. Inherited names were not compared.")
    else:
        observed = pipeline["failed"]
        kept = [name for name in observed if name in inherited_set]
        fresh = [name for name in observed if name not in inherited_set]
        cleared = [name for name in inherited if name not in set(observed)]
        lines.append(f"Inherited and still failing: {len(kept)}")
        lines.append(f"New failures: {len(fresh)}")
        lines.append(f"Recorded in PR-DP but not in this run: {len(cleared)}")
        if fresh:
            lines.extend(["", "New failures:", ""])
            lines.extend(f"- {name}" for name in fresh)
        if cleared:
            lines.extend(["", "Not repeated from PR-DP:", ""])
            lines.extend(f"- {name}" for name in cleared)
    short = "\n".join(lines).rstrip() + "\n"
    details = ["# PR-DQ Regression Results", "", short, "## Suite output", ""]
    for row in rows:
        details.extend(
            [
                f"### {row['name']}",
                "",
                f"Command: `python -m pytest {' '.join(row['args'])}`",
                f"Timeout: {row['timeout']}s. Timed out: {row['timed_out']}. Return code: {row['return_code']}.",
                "",
                "```",
                row["output"][-5000:],
                "```",
                "",
            ]
        )
    return short, "\n".join(details).rstrip() + "\n"


def _write_zip(review: Path) -> None:
    zip_path = HANDOFF / "CURRENT_REVIEW.zip"
    temporary = HANDOFF / "CURRENT_REVIEW.zip.partial"
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(review, "CURRENT_REVIEW.md")
        for path in sorted(OUT.iterdir()):
            if path.is_file():
                archive.write(path, f"artifacts/pr_dq_vertical_slice/{path.name}")
    temporary.replace(zip_path)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    HANDOFF.mkdir(exist_ok=True)
    slice_report = run_vertical_slice()
    (OUT / "vertical_slice_trace.json").write_text(
        json.dumps(slice_report, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUT / "PR-DQ_ic_ooc_message_contract.md").write_text(message_contract(), encoding="utf-8")
    (OUT / "PR-DQ_ic_ooc_routing.md").write_text(routing(), encoding="utf-8")
    (OUT / "PR-DQ_ic_ooc_safety.md").write_text(safety(), encoding="utf-8")

    rows = [_run_suite(name, args, timeout) for name, args, timeout in SUITES]
    short_regression, full_regression = _regression_body(rows)
    (OUT / "PR-DQ_regression_results.md").write_text(full_regression, encoding="utf-8")
    (OUT / "PR-DQ_ic_ooc_tests.md").write_text(tests_document(short_regression), encoding="utf-8")
    pr_dq_row = next(row for row in rows if row["name"] == "PR-DQ")
    (OUT / "focused_tests.txt").write_text(pr_dq_row["output"] + "\n", encoding="utf-8")

    review_text = current_review(slice_report, short_regression)
    review = HANDOFF / "CURRENT_REVIEW.md"
    review.write_text(review_text if review_text.endswith("\n") else review_text + "\n", encoding="utf-8")
    changed = [
        "experiments/pr_dq/__init__.py",
        "experiments/pr_dq/envelope.py",
        "experiments/pr_dq/history.py",
        "experiments/pr_dq/classify.py",
        "experiments/pr_dq/route.py",
        "experiments/pr_dq/reclassify.py",
        "experiments/pr_dq/safety.py",
        "experiments/pr_dq/world.py",
        "experiments/pr_dq/gameplay.py",
        "experiments/pr_dq/slice.py",
        "experiments/pr_dq/reports.py",
        "experiments/pr_dq/runner.py",
        "tests/test_pr_dq_ic_ooc_messages.py",
        "tests/test_pr_dq_vertical_slice.py",
        "artifacts/pr_dq_vertical_slice/",
        "handoff/CURRENT_REVIEW.md",
        "handoff/CURRENT_REVIEW.zip",
        "handoff/REVIEW_MANIFEST.json",
    ]
    (OUT / "changed_files.txt").write_text("\n".join(changed) + "\n", encoding="utf-8")
    manifest = {
        "pr": "PR-DQ",
        "live_provider_calls": 0,
        "production_ui_changes": False,
        "artifacts": [
            f"artifacts/pr_dq_vertical_slice/{path.name}" for path in sorted(OUT.iterdir()) if path.is_file()
        ],
    }
    (HANDOFF / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _write_zip(review)
    print(json.dumps({"review": str(review), "zip": str(HANDOFF / "CURRENT_REVIEW.zip"), "pr_dq": pr_dq_row["summary"]}, indent=2))


if __name__ == "__main__":
    main()
