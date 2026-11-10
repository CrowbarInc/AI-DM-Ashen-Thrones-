"""Focused regression for PR-PLAY-64. Provider calls stay disabled."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_64"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ.pop("ASHEN_QUARANTINE_INVESTIGATION_NARRATION", None)
os.environ.pop("ASHEN_QUARANTINE_NARRATION_LIVE", None)
os.environ.pop("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", None)
os.environ.pop("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION_SESSION", None)
os.environ.pop("ASHEN_PROVIDER_USAGE_PATH", None)
os.environ.pop("ASHEN_PROVIDER_REQUEST_LIMIT", None)

SUITES = [
    "tests/test_pr_play_64_discovery_language.py",
    "tests/test_pr_play_63_disclosure.py",
    "tests/test_state_authority.py",
    "tests/test_pr_play_61_player_facing.py",
    "tests/test_pr_play_62_investigation_quality.py",
    "tests/test_pr_play_60_inventory_projection.py",
    "tests/test_pr_play_60_gameplay_readiness.py",
    "tests/test_pr_play_59_persistent_consequences.py",
    "tests/test_pr_play_57_integrated_narration.py",
    "tests/test_pr_play_58_semantic_coverage.py",
    "tests/test_pr_play_55_discovery_claims.py",
    "tests/test_pr_play_54_consequential_validation.py",
    "tests/test_pr_play_53_quarantined_live.py",
    "tests/test_pr_play_52_quarantined_integration.py",
    "tests/test_pr_play_42_evidence_boundaries.py",
    "tests/test_pr_play_51_geography_grounding.py",
    "tests/test_pr_play_49_anchored_narration.py",
    "tests/test_pr_play_47_controlled_renderer.py",
    "tests/test_pr_play_45_narration_authority.py",
    "tests/test_pr_play_46_mechanical_boundary.py",
    "tests/test_pr_play_44_information_delivery.py",
    "tests/test_pr_bu_lexical_scope.py",
    "tests/test_provider_accounting_integrity.py",
    "tests/test_pr_bw_narration_only_envelope.py",
    "tests/test_diegetic_fallback_narration.py",
    "tests/test_narration_state_consistency.py",
]
PRIOR = {
    "tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution",
    "tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues",
    "tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues",
}
PROTECT_ROOTS = [
    ROOT / "artifacts" / "pr_play_49",
    ROOT / "artifacts" / "pr_play_47",
    ROOT / "artifacts" / "pr_play_52",
    ROOT / "artifacts" / "pr_play_50",
    ROOT / "artifacts" / "pr_play_55" / "evaluation.json",
]


def snapshot(roots):
    saved = {}
    for root in roots:
        if root.is_file():
            saved[root] = root.read_bytes()
            continue
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                saved[path] = path.read_bytes()
    return saved


def restore(saved) -> list[str]:
    restored = []
    for path, content in saved.items():
        if not path.exists() or path.read_bytes() != content:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            restored.append(path.relative_to(ROOT).as_posix())
    return restored


def run_pytest(label: str, files: list[str]) -> dict:
    xml_path = OUT / f"{label}_final.xml"
    log_path = OUT / f"{label}_final.txt"
    basetemp = ROOT / "development" / "tmp" / f"pr_play_64_{label}_{os.getpid()}"
    args = [sys.executable, "-m", "pytest", *files, "--tb=line", f"--junitxml={xml_path}", "--basetemp", str(basetemp)]
    with log_path.open("w", encoding="utf-8") as log:
        completed = subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=os.environ.copy())
    if completed.returncode not in (0, 1):
        raise RuntimeError(f'{label}: pytest did not execute normally; see {log_path}')
    import xml.etree.ElementTree as ET

    root = ET.parse(xml_path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    counts = {key: int(suite.attrib.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")}
    failed = []
    for case in suite.iter("testcase"):
        failure = case.find("failure")
        error = case.find("error")
        if failure is None and error is None:
            continue
        node = case.attrib.get("classname", "") + "::" + case.attrib.get("name", "")
        message = (failure if failure is not None else error).attrib.get("message", "")
        failed.append({"nodeid": node, "message": message[:500]})
    return {
        "label": label,
        "collected": counts["tests"],
        "failed": counts["failures"],
        "errors": counts["errors"],
        "skipped": counts["skipped"],
        "passed": counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"],
        "exit_code": completed.returncode,
        "failed_nodeids": [row["nodeid"] for row in failed],
        "failure_messages": failed,
        "command": args,
        "provider_calls": "disabled",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    saved = snapshot(PROTECT_ROOTS)
    focused = run_pytest("focused", SUITES)
    focused["preexisting_failures_seen"] = [name for name in focused["failed_nodeids"] if name in PRIOR]
    focused["new_failures"] = [name for name in focused["failed_nodeids"] if name not in PRIOR]
    holdout = run_pytest("holdout", ["tests/test_pr_play_55_holdout.py"])
    broader = run_pytest("broader_hard_validation", ["tests/test_pr_cx_authority_assurance.py"])
    summary = {
        "focused": focused,
        "holdout": holdout,
        "broader_hard_validation": broader,
        "restored": restore(saved),
        "known_failures_not_modified": sorted(PRIOR),
        "note": "Historical PR61 focused baseline was 741 passed and 3 known failures. This run adds PR62 quality and bypass tests. Broader authority-assurance failures involving hard_validation_attempt_1 are reported separately.",
    }
    (OUT / "regression_summary_final.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "focused": {key: focused[key] for key in ("collected", "passed", "failed", "errors", "skipped", "new_failures", "preexisting_failures_seen")},
        "holdout": {key: holdout[key] for key in ("collected", "passed", "failed", "errors", "skipped", "failed_nodeids")},
        "broader": {key: broader[key] for key in ("collected", "passed", "failed", "errors", "skipped")},
        "restored_count": len(summary["restored"]),
    }, indent=2))
    return 0 if not focused["new_failures"] and focused["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
