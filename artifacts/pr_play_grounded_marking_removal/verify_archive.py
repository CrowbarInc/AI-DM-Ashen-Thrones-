"""Reopen the dated review archive and record its hash. The hash file stays outside the archive."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "handoff" / "CURRENT_REVIEW(20261109-230559).zip"
data = ARCHIVE.read_bytes()
digest = hashlib.sha256(data).hexdigest()
checks = []


def add(name, ok):
    checks.append({"check": name, "ok": bool(ok)})


with zipfile.ZipFile(ARCHIVE) as zf:
    add("zip_integrity", zf.testzip() is None)
    review = zf.read("CURRENT_REVIEW.md").decode("utf-8")
    add("milestone", "pr_play_grounded_marking_removal" in review and "A/PASS" in review)

    def text(name):
        return zf.read(name).decode("utf-8")

    base = "support/development/campaigns/product_realization/pr_play_grounded_marking_removal/"
    life = text(base + "CONTROLLED_HTTP_LIFECYCLE.md")
    life_json = text("support/artifacts/pr_play_grounded_marking_removal/controlled_http_lifecycle.json")
    add("http_lifecycle", "I wipe the warning off my sleeve." in life and "no longer" in life_json)
    target = text(base + "TARGET_RESOLUTION.md")
    add("target_and_marking", "ask for one marking" in target and "modification_id" in target)
    feas = text(base + "PHYSICAL_FEASIBILITY.md")
    add("physical_feasibility", "water" in feas and "not invented" in feas)
    removal = text("support/game/marking_removal.py")
    add("authoritative_removal", "prepare_removal" in removal)
    pub = text(base + "PUBLICATION_INTEGRITY.md")
    add("publication", "contradictory" in pub.casefold() and "no longer" in pub)
    conf = text(base + "CONFIDENTIALITY_VERIFICATION.md")
    add("confidentiality", "concealed" in conf and "restricted" in conf)
    persist = text(base + "PERSISTENCE_VERIFICATION.md")
    add("save_reload_snapshots", "S0" in persist and "S2" in persist)
    reg = text(base + "REGRESSION_RESULTS.md")
    add("regressions", "405 passed / 20 failed" in reg and "New failing identities: none" in reg)
    twelve = text(base + "TWELVE_TURN_COMPARISON.md")
    add("twelve_turn", "T06" in twelve and "Live provider calls: 0" in twelve)
    close = text(base + "SUBSYSTEM_CLOSURE.md")
    add("subsystem_closure", "close the marking workstream" in close)
    nxt = text("support/docs/NEXT_SESSION.md")
    add("handoff", nxt.startswith("# NEXT_SESSION — PR-PLAY Grounded Marking Removal") and "pr_play_player_marking_observation" in nxt)
    manifest = json.loads(zf.read("REVIEW_MANIFEST.json"))
    mismatched = []
    for row in manifest["included_files"]:
        if not row.get("sha256") or not row.get("bundle_path"):
            continue
        payload = zf.read(row["bundle_path"])
        if hashlib.sha256(payload).hexdigest() != row["sha256"]:
            mismatched.append(row["bundle_path"])
        source_path = row.get("canonical_source_path")
        if source_path:
            source = (ROOT / source_path).read_bytes()
            if hashlib.sha256(source).hexdigest() != row["sha256"]:
                mismatched.append("source:" + source_path)
    add("member_hashes", not mismatched)
    add("source_manifest", any(row.get("canonical_source_path") == "game/marking_removal.py" for row in manifest["included_files"]))

out = {
    "stamp": "20261109-230559",
    "archive": "handoff/CURRENT_REVIEW(20261109-230559).zip",
    "sha256": digest,
    "included_files": 37,
    "reopen": "pass" if all(item["ok"] for item in checks) else "fail",
    "checks": checks,
    "mismatched": mismatched,
}
evidence = ROOT / "artifacts" / "pr_play_grounded_marking_removal"
(evidence / "archive_verification.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
(evidence / "archive_sha256.txt").write_text(digest + "  handoff/CURRENT_REVIEW(20261109-230559).zip\n", encoding="utf-8")
print(out["reopen"], digest)
for item in checks:
    print(item["check"], item["ok"])
if mismatched:
    print("MISMATCH", mismatched)
