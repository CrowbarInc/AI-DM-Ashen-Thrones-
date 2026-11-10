"""Established selected review export, preserving the prior current handoff."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
from tools.build_review_handoff import build_handoff
from artifacts.pr_play_71v.package_review import clean


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    report = ROOT / "development/campaigns/product_realization/pr_play_72"
    metrics = json.loads((OUT / "metrics.json").read_text())
    sources = [ROOT/p for p in ["game/player_initiative.py", "game/conversational_orchestration.py", "game/player_interpretation_bridge.py", "game/ordinary_semantic_ownership.py", "game/api.py", "game/storage.py", "game/authored_consequences.py", "game/player_http_projection.py", "tests/conftest.py", "tests/helpers/storage_isolation.py", "tests/test_pr_play_72_initiative.py", "tests/test_pr_play_72_failures.py", "tests/test_pr_play_72_supplemental.py", "tests/test_pr_play_72_boundary_repairs.py", "docs/NEXT_SESSION.md"]]
    sources += [ROOT/p for p in ("game/social.py", "game/journal.py", "game/exploration.py", "static/app.js")]
    diff = subprocess.run(["git", "diff", "--", *[str(p.relative_to(ROOT)) for p in sources]], cwd=ROOT, capture_output=True, text=True).stdout
    (OUT / "implementation_with_inherited_changes.diff").write_text(diff, encoding="utf-8")
    review = OUT / "review_data"; review.mkdir(exist_ok=True)
    paths = list(report.glob("*.md")) + sources
    provenance = []
    excluded = {"review_config.json", "archive_verification.json", "archive_path.txt", "preserved_session_log.jsonl"}
    for p in sorted(OUT.iterdir()):
        if not p.is_file() or p.name in excluded or p.suffix not in {".json", ".jsonl", ".txt", ".xml", ".diff", ".py"}: continue
        if p.suffix in {".json", ".jsonl"}:
            dest = review/p.name
            if p.suffix == ".json": dest.write_text(json.dumps(clean(json.loads(p.read_text())), indent=2), encoding="utf-8")
            else:
                with dest.open("w", encoding="utf-8") as f:
                    for line in p.read_text().splitlines():
                        if line.strip(): f.write(json.dumps(clean(json.loads(line))) + "\n")
            paths.append(dest); provenance.append(dict(source=str(p.relative_to(ROOT)), source_sha256=sha(p), review_sha256=sha(dest)))
        else: paths.append(p)
    (review / "provenance.json").write_text(json.dumps(provenance, indent=2))
    paths.append(review / "provenance.json")
    for p in paths:
        assert not re.search(r"\bsk-[A-Za-z0-9_-]{16,}", p.read_text(encoding="utf-8", errors="replace")), p
    config = json.loads((ROOT / "artifacts/pr_play_71v/review_config.json").read_text())
    config.update(campaign_id="PR-PLAY-72", campaign_name="Consequence-aware Player Initiative", campaign_date="2026-11-06", purpose="Extend bounded natural intentions through existing authority and publication, preserve repository data and retain honest verification limits.", objective_status="B", executive_summary=metrics["verdict"], primary_report=str((report/"01_EXECUTIVE_SUMMARY.md").relative_to(ROOT)), evidence_packets=[], max_file_bytes=90000000,
        changes=dict(production=["Default-off read-only initiative decision leaf, existing bridge validation and existing resolver integration.", "See implementation diff and final repair evidence for precise scope; inherited changes are retained."], validation=["Frozen developer holdout executed once, retained with failures.", "Two real HTTP campaigns; browser blocked.", "Protected-data audit guard and intentional-write verification."], tooling=["Isolated fixture host, stage measurements, prior regression lanes, sanitized review export."], documentation=["24 requested reports and NEXT_SESSION handoff."], generated_artifacts=["Actual HTTP/holdout responses and authority evidence, test XML, hashes, recovery search, timings."]),
        testing=dict(focused=str(metrics["development"]), broader=str({k:dict(passed=v.get("passed"), failed=len(v.get("failed", []))) for k,v in metrics["regression"].items()}), full_suite="Not run; no official ATGB or external validation.", runtime_validation="Two normal HTTP lifecycles; typed browser verification blocked.", model_runtime_boundary="0 live requests / 0 tokens; deterministic fixture only.", new_regressions="See regression assessment; combined and isolated failures retained.", pre_existing_failures="Compared to PR71V retained evidence; unclassified failures are not called historical."),
        decisions_requiring_human_review=["No commit or push. Review B limitations before enabling the experiment."],
        known_problems=dict(campaign_specific=["Browser attachment and policy-confidence blocker.", "Heldout already-searched assertions and one ambiguous-input classification failure retained.", "Exact interstage and browser paint latency unavailable.", "Any post-holdout corrections are documented separately; no fresh external independence claim."], pre_existing=["Historical original session-log bytes not recoverable from searched sources.", "Existing combined-suite/cache and authority failures remain under assessment."]), missing_concepts=["Live provider interpretation and browser end-to-end evidence."], does_not_prove=["Arbitrary natural language, unrestricted world generation, full regression suite or live AI presentation."], recommended_next_step=metrics["next_step"], self_contained_review_test="All 24 reports, immutable holdout manifest/results, original player text and responses, actual authority snapshots, preservation and limitation evidence.", supporting_files=[dict(path=p.relative_to(ROOT).as_posix(), role="source" if p in sources else "campaign_evidence", why="PR72 implementation or retained verification evidence.", human_review_required=True, behavioral_evidence=p.suffix in {".json", ".jsonl", ".xml"}) for p in sorted(set(paths))])
    (OUT / "review_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    stage = OUT/"export_stage"
    result = build_handoff(config, root=ROOT, output_dir=stage, archive_history=False)
    previous = OUT/"previous_handoff"; previous.mkdir(exist_ok=True)
    for name in ("CURRENT_REVIEW.md", "REVIEW_MANIFEST.json", "CURRENT_REVIEW.zip"):
        dest = ROOT/"handoff"/name
        if dest.exists() and not (previous/name).exists(): (previous/name).write_bytes(dest.read_bytes())
        pending = dest.with_name(name + ".pr72.tmp"); pending.write_bytes((stage/name).read_bytes()); os.replace(pending, dest)
    stamp = datetime.now(timezone(timedelta(hours=-5))).strftime("%Y%m%d-%H%M%S")
    archive = ROOT/"handoff"/f"CURRENT_REVIEW({stamp}).zip"
    with archive.open("xb") as f: f.write((stage/"CURRENT_REVIEW.zip").read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest = json.loads(z.read("REVIEW_MANIFEST.json"))
        for row in manifest["included_files"]:
            if row.get("sha256"): assert hashlib.sha256(z.read(row["bundle_path"])).hexdigest() == row["sha256"]
        count = sum("/pr_play_72/" in n and bool(re.search(r"/\d\d_[A-Z0-9_]+\.md$", n)) for n in z.namelist())
        assert count == 24, count
    (OUT/"archive_path.txt").write_text(str(archive))
    (OUT/"archive_verification.json").write_text(json.dumps(dict(path=str(archive), sha256=sha(archive), bytes=archive.stat().st_size, reports=count, crc_valid=True, manifest_hashes_verified=True, omitted=result["omitted"]), indent=2))
    print(archive)


if __name__ == "__main__": main()
