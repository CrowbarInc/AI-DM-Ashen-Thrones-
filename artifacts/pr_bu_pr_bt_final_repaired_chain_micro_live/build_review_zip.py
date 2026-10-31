"""Refresh handoff/CURRENT_REVIEW.zip for the repaired-chain micro-live gate."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "artifacts" / "pr_bu_pr_bt_final_repaired_chain_micro_live" / "evidence"
ZIP_PATH = ROOT / "handoff" / "CURRENT_REVIEW.zip"
MANIFEST_PATH = ROOT / "handoff" / "REVIEW_MANIFEST.json"

ROOT_FILES = [
    "handoff/CURRENT_REVIEW.md",
    "PR-BU_PR-BT_final_repaired_chain_micro_live.md",
]


def evidence_files() -> list[Path]:
    found = []
    for path in EVIDENCE.rglob("*"):
        if not path.is_file():
            continue
        if "isolated" in path.parts:
            continue
        found.append(path)
    return sorted(found)


def main() -> None:
    files = [ROOT / item for item in ROOT_FILES] + evidence_files()
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise SystemExit("missing:\n" + "\n".join(missing))
    manifest = []
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            data = path.read_bytes()
            if path.name == "CURRENT_REVIEW.md":
                arc = "CURRENT_REVIEW.md"
            else:
                arc = path.relative_to(ROOT).as_posix()
            archive.writestr(arc, data)
            manifest.append(
                {"path": arc, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            )
        body = {
            "review": "PR-BU / PR-BT final repaired-chain micro-live",
            "mode": "FINAL REPAIRED-CHAIN MICRO LIVE",
            "model": "gpt-4.1-mini-2025-04-14",
            "model_api_calls": 6,
            "gameplay_generations": 5,
            "retry_count": 2,
            "pr_bu_decision": "BU-B - one bounded validator defect remains",
            "pr_bt_decision": "BT-C - model first-pass competence remains the blocker",
            "pr_br": "CLOSED",
            "initial_quality": {"P1": "Q0", "P2": "Q0", "P3": "Q2"},
            "final_quality": {"P1": "Q1", "P2": "Q2", "P3": "Q2"},
            "correct_accepts": 1,
            "correct_rejects": 2,
            "false_accepts": 0,
            "false_rejects_initial": 0,
            "false_rejects_retry": 1,
            "retry_classifications": {"P1": "R1", "P2": "R1", "P3": None},
            "initial_input_tokens": {"P1": 21952, "P2": 24534, "P3": 21977, "total": 68463},
            "complete_turn_input_tokens": 117776,
            "vs_pr_bs_initial_input": -9773,
            "vs_pr_bs_complete_turn_input": 39540,
            "vs_raw_pr_bt_complete_turn_input": 3287,
            "vs_selective_pre_pr_bu_initial_input": 0,
            "vs_selective_pre_pr_bu_complete_turn_input": 26072,
            "c18": "PASS",
            "authority_integrity": "HELD",
            "validators_changed": False,
            "retry_changed": False,
            "prompts_changed": False,
            "files": manifest,
        }
        encoded = json.dumps(body, indent=2).encode("utf-8")
        archive.writestr("REVIEW_MANIFEST.json", encoded)
    MANIFEST_PATH.write_bytes(encoded)
    print(f"wrote {ZIP_PATH} files={len(manifest)+1} bytes={ZIP_PATH.stat().st_size}")


if __name__ == "__main__":
    main()
