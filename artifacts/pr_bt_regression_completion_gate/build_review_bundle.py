"""Package existing deterministic evidence; does not execute gameplay or tests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/pr_bt_regression_completion_gate"


def main() -> None:
    tree = ET.parse(OUT / "final_regression.xml")
    cases = list(tree.iter("testcase"))
    failures = [case for case in cases if case.find("failure") is not None]
    summary = {
        "mode": "DETERMINISTIC REGRESSION COMPLETION",
        "model_api_calls": 0,
        "passed": len(cases) - len(failures),
        "failed": len(failures),
        "deselected": 1,
        "decision": "C - BOUNDED PR-BT REPAIR NEEDED",
        "c18": "PASS",
        "test_ids": [case.attrib for case in cases],
        "failures": [case.attrib for case in failures],
    }
    (OUT / "final_test_inventory.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    lines = (ROOT / "game/prompt_context.py").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if '"ANSWER POLICY:' in line) - 1
    end = next(i for i, line in enumerate(lines[start:], start) if '"SCENE ANCHORING (POLICY)."' in line) + 1
    anchors = lines[start:end]
    # Only the newly restored policy-anchor block, not the dirty-worktree diff.
    diff = [
        "# Addition-only excerpt; see repair_inventory.md for the other changed lines.",
        "--- a/game/prompt_context.py",
        "+++ b/game/prompt_context.py",
        f"@@ -{start},0 +{start + 1},{len(anchors)} @@",
        *["+" + line for line in anchors],
    ]
    (OUT / "repair_policy_anchors.diff").write_text("\n".join(diff) + "\n", encoding="utf-8")

    files: dict[str, Path] = {
        "CURRENT_REVIEW.md": ROOT / "handoff/CURRENT_REVIEW.md",
        "PR-BT_regression_completion_gate.md": ROOT / "PR-BT_regression_completion_gate.md",
        "tools/measure_pr_bt_policy_instruction_payloads.py": ROOT / "tools/measure_pr_bt_policy_instruction_payloads.py",
        "pytest.ini": ROOT / "pytest.ini",
    }
    for folder in (OUT, ROOT / "artifacts/pr_bt_policy_instruction_deduplication", ROOT / "game", ROOT / "tests/helpers"):
        for path in folder.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
                files[path.relative_to(ROOT).as_posix()] = path
    for name in sorted({case.attrib["classname"].replace(".", "/") + ".py" for case in cases}):
        files[name] = ROOT / name
    files["tests/conftest.py"] = ROOT / "tests/conftest.py"
    for probe in ("P1", "P2", "P3"):
        base = ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence" / probe
        files[(base / "api_response.json").relative_to(ROOT).as_posix()] = base / "api_response.json"
        for path in (base / "isolated/data").rglob("*"):
            if path.is_file():
                files[path.relative_to(ROOT).as_posix()] = path

    manifest = {
        "review": "PR-BT regression completion gate",
        "decision": summary["decision"],
        "model_api_calls": 0,
        "files": [
            {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
            for name, path in sorted(files.items())
        ],
    }
    destination = ROOT / "handoff/CURRENT_REVIEW.zip"
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(files.items()):
            archive.write(path, name)
        archive.writestr("REVIEW_MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        archived_manifest = json.loads(archive.read("REVIEW_MANIFEST.json"))
        for entry in archived_manifest["files"]:
            assert hashlib.sha256(archive.read(entry["path"])).hexdigest() == entry["sha256"]
    print(json.dumps({"archive": str(destination), "entries": len(files) + 1, "passed": summary["passed"], "failed": summary["failed"], "crc_and_hashes": "PASS"}))


if __name__ == "__main__":
    main()
