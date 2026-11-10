"""Build a bounded review package, test identity comparison, and SHA256 inventory."""
import difflib
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "artifacts/pr_play_21"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def read_run(name):
    root = ET.parse(EVIDENCE / (name + ".xml"))
    results = {}
    for case in root.iter("testcase"):
        node = case.get("classname").replace(".", "/") + ".py::" + case.get("name")
        issue = case.find("failure")
        if issue is None:
            issue = case.find("error")
        results[node] = {
            "status": "failed" if issue is not None else "skipped" if case.find("skipped") is not None else "passed",
            "windows_permission_error": issue is not None and "WinError 5" in (issue.text or ""),
        }
    return results


def main():
    known = set(json.loads((ROOT / "artifacts/pr_play_20/preexisting_failure_comparison.json").read_text())["failure_node_ids"])
    runs = {name: read_run(name) for name in ("baseline_tests", "repaired_tests", "focused_final_tests", "windows_io_retry_tests")}
    failures = {name: {k: v for k, v in rows.items() if v["status"] == "failed"} for name, rows in runs.items()}
    baseline_known = known & set(failures["baseline_tests"])
    final_known = known & set(failures["repaired_tests"])
    comparison = {
        "pr_play_20_known_failure_count": len(known),
        "all_known_failures_reproduced_before_and_after": baseline_known == final_known == known,
        "known_failure_node_ids": sorted(known),
        "additional_baseline_failures": sorted(set(failures["baseline_tests"]) - known),
        "additional_repaired_failures": sorted(set(failures["repaired_tests"]) - known),
        "runs": runs,
    }
    assert comparison["all_known_failures_reproduced_before_and_after"]
    for stage in ("baseline_tests", "repaired_tests"):
        for node in set(failures[stage]) - known:
            assert failures[stage][node]["windows_permission_error"]
            assert any(rows.get(node, {}).get("status") == "passed" for name, rows in runs.items() if "retry" in name or "focused_final" in name)
    write_json(EVIDENCE / "failure_comparison.json", comparison)

    # Keep the source patch specific to this pass, even though the workspace
    # contains many preexisting modifications and the PR-PLAY-20 test is untracked.
    changed = ["game/api_ui_mode.py", "tests/test_ui_mode_backend_integration.py",
               "tests/test_ui_mode_regression_matrix_objective15.py"]
    patch = ""
    snapshots = EVIDENCE / "source"
    for rel in changed:
        before = subprocess.check_output(["git", "show", "HEAD:" + rel], cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
        after = (ROOT / rel).read_text(encoding="utf-8")
        patch += "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile="a/" + rel, tofile="b/" + rel))
        target = snapshots / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(after, encoding="utf-8")
        if rel == "game/api_ui_mode.py":
            (EVIDENCE / "baseline_api_ui_mode.py.txt").write_text(before, encoding="utf-8")
            captured = json.loads((EVIDENCE / "baseline_http.json").read_text())["resolver_sha256"]
            assert captured in {hashlib.sha256(before.encode()).hexdigest(), hashlib.sha256(before.replace("\n", "\r\n").encode()).hexdigest()}

    rel = "tests/test_pr_play_20_response_confidentiality.py"
    after = (ROOT / rel).read_text(encoding="utf-8")
    new_block = '''        assert client.get("/api/state?ui_mode=debug").status_code == 403
        assert client.get("/api/state?ui_mode=author").status_code == 403
        # PR-PLAY-21 closes unauthenticated HTTP reads; the internal projection
        # remains available to local author/developer code.
        debug = api._project_state_for_ui_mode(api.compose_state(), "debug")
        author = api._project_state_for_ui_mode(api.compose_state(), "author")
'''
    old_block = '''        debug = client.get("/api/state?ui_mode=debug").json()
        author = client.get("/api/state?ui_mode=author").json()
'''
    assert after.count(new_block) == 1
    before = after.replace(new_block, old_block)
    patch += "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile="a/" + rel, tofile="b/" + rel))
    (snapshots / rel).write_text(after, encoding="utf-8")
    rel = "tests/test_pr_play_21_privileged_reads.py"
    after = (ROOT / rel).read_text(encoding="utf-8")
    patch += "".join(difflib.unified_diff([], after.splitlines(True), fromfile="/dev/null", tofile="b/" + rel))
    (snapshots / rel).write_text(after, encoding="utf-8")
    (EVIDENCE / "source_diff.patch").write_text(patch, encoding="utf-8")

    for rel in ("game/ui_mode_policy.py", "game/state_channels.py", "run.py"):
        target = snapshots / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")
    api_lines = (ROOT / "game/api.py").read_text(encoding="utf-8").splitlines()
    excerpts = []
    for start, end in ((296, 315), (4946, 5034), (5093, 5211), (5298, 5369)):
        excerpts.append("\n".join(f"{i}: {api_lines[i-1]}" for i in range(start, end + 1)))
    (EVIDENCE / "api_boundary_source_excerpt.txt").write_text("\n\n".join(excerpts), encoding="utf-8")

    baseline = json.loads((EVIDENCE / "baseline_http.json").read_text())
    repaired = json.loads((EVIDENCE / "repaired_http.json").read_text())
    rows = []
    for original, current in zip(baseline["rows"], repaired["rows"]):
        assert original["path"] == current["path"]
        privileged = original["requested_mode"] in ("author", "debug")
        assert current["status"] == (403 if privileged or original["path"] == "/api/debug_trace" else 200)
        assert not current["sentinel_in_serialized_http"]
        rows.append({"path": current["path"], "before_status": original["status"], "after_status": current["status"],
                     "before_sentinel": original["sentinel_in_serialized_http"], "after_sentinel": current["sentinel_in_serialized_http"],
                     "projection_selector": "_project_log_entry_for_ui_mode" if "/log" in current["path"] else
                         "_project_state_for_ui_mode" if "/state" in current["path"] else "direct diagnostic/metadata return",
                     "authorization_before": "requested mode policy only; no independent authorization",
                     "authorization_after": "shared resolver rejects privileged mode before data access" if privileged else "player-only policy"})
    write_json(EVIDENCE / "authorization_trace.json", rows)

    included = sorted(p for p in EVIDENCE.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                      and p.name not in {"MANIFEST.json", "archive_verification.json"})
    manifest = [{"path": str(p.relative_to(ROOT)).replace("\\", "/"), "bytes": p.stat().st_size,
                 "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in included]
    write_json(EVIDENCE / "MANIFEST.json", {"scope": "PR-PLAY-21 only; no environment files, credentials or real campaign data", "files": manifest})
    included.append(EVIDENCE / "MANIFEST.json")
    try:
        stamp = datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York")).strftime("%Y%m%d-%H%M%S")
    except ZoneInfoNotFoundError:
        # Windows supplies the DST-aware zone via .NET even without Python tzdata.
        stamp = subprocess.check_output(["powershell", "-NoProfile", "-Command",
            "[TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow, [TimeZoneInfo]::FindSystemTimeZoneById('Eastern Standard Time')).ToString('yyyyMMdd-HHmmss')"], text=True).strip()
    archive = ROOT / "handoff" / ("CURRENT_REVIEW(" + stamp + ").zip")
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as output:
        for path in included:
            output.write(path, str(path.relative_to(ROOT)))
    with zipfile.ZipFile(archive) as saved:
        assert saved.testzip() is None
        for entry in manifest:
            assert hashlib.sha256(saved.read(entry["path"])).hexdigest() == entry["sha256"]
        assert not any(Path(name).name == ".env" for name in saved.namelist())
    write_json(EVIDENCE / "archive_verification.json", {"archive": str(archive), "entries": len(included),
               "bytes": archive.stat().st_size, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
               "testzip": "passed", "all_manifest_hashes_verified": True, "timestamp_timezone": "America/New_York"})
    print(str(archive))
    print(f"Verified {len(included)} entries, {archive.stat().st_size} bytes")


if __name__ == "__main__":
    main()
