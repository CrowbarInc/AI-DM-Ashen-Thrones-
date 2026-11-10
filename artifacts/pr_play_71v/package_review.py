"""Selected sanitized PR-PLAY-71V review export. Does not commit or push."""
import sys, json, hashlib, zipfile, re, os
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
from tools.build_review_handoff import build_handoff


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def clean(v):
    private = {
        "gm_notes", "hidden_facts", "private_notes", "gm_only", "character_secret",
        "gm_guidance", "inference_rules", "current_plan", "current_agenda", "goal", "topics",
    }
    if isinstance(v, dict):
        return {
            k: (
                "[REDACTED PRIVATE CAMPAIGN CONTENT]" if k in private
                else "[OMITTED NONAUTHORITATIVE DIAGNOSTICS]" if k in {"debug_traces", "last_action_debug"}
                else clean(x)
            )
            for k, x in v.items()
        }
    if isinstance(v, list):
        return [clean(x) for x in v]
    return v


def main():
    report = ROOT / "development/campaigns/product_realization/pr_play_71v"
    review = OUT / "review_data"
    review.mkdir(exist_ok=True)
    paths = list(report.glob("*.md"))
    provenance = []
    for original in sorted(OUT.iterdir()):
        if not original.is_file() or original.name in {"review_config.json", "archive_path.txt", "archive_verification.json"}:
            continue
        if original.suffix not in {".json", ".jsonl", ".txt", ".xml", ".png", ".diff", ".py"}:
            continue
        if original.suffix in {".json", ".jsonl"}:
            dest = review / original.name
            if original.suffix == ".json":
                dest.write_text(json.dumps(clean(json.loads(original.read_text(encoding="utf-8"))), indent=2, ensure_ascii=False), encoding="utf-8")
            else:
                with dest.open("w", encoding="utf-8") as handle:
                    for line in original.read_text(encoding="utf-8").splitlines():
                        if not line.strip():
                            continue
                        handle.write(json.dumps(clean(json.loads(line)), ensure_ascii=False) + "\n")
            paths.append(dest)
            provenance.append(dict(source=original.relative_to(ROOT).as_posix(), original_sha256=sha(original), review=dest.relative_to(ROOT).as_posix(), review_sha256=sha(dest)))
        else:
            paths.append(original)
    for shot in (OUT / "screenshots").glob("*.png"):
        paths.append(shot)
    sources = [
        ROOT / p for p in [
            "game/api.py", "game/storage.py", "game/authored_consequences.py", "game/campaign_reset.py",
            "game/player_http_projection.py", "game/player_http_boundary.py", "static/app.js",
            "tests/test_pr_play_71v_verification.py", "docs/NEXT_SESSION.md",
        ]
    ]
    paths += sources
    (review / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    paths.append(review / "provenance.json")
    for p in paths:
        if p.suffix != ".png":
            assert not re.search(r"\bsk-[A-Za-z0-9_-]{16,}", p.read_text(encoding="utf-8", errors="replace")), p
    v = json.loads((OUT / "verdict.json").read_text(encoding="utf-8"))
    config = json.loads((ROOT / "artifacts/pr_play_70/review_config.json").read_text(encoding="utf-8"))
    config.update(
        campaign_id="PR-PLAY-71V",
        campaign_name="Final Persistence and Lifecycle Verification",
        campaign_date="2026-11-05",
        purpose="Verify the final PR-PLAY-71 persistence and two-campaign lifecycle on the source that was actually executed.",
        objective_status=v["verdict"],
        executive_summary="Verdict A. Both HTTP and browser lifecycles passed. Frozen holdout 59/60 with W12 left as a harness KeyError. No live provider calls. No commit or push.",
        primary_report=(report / "01_EXECUTIVE_SUMMARY.md").relative_to(ROOT).as_posix(),
        evidence_packets=[],
        max_file_bytes=60000000,
        changes=dict(
            production=["No product edit after the frozen holdout. The tested source already contained the Windows rename retry and runtime_commit_scope."],
            validation=["60-case developer holdout once: 59 passed, W12 retained.", "Isolated lifecycle and persistence tests: 39 passed.", "Both HTTP campaigns and both browser campaigns completed."],
            tooling=["Isolated browser host and selected sanitized review export."],
            documentation=["20 cycle reports and NEXT_SESSION orientation."],
            generated_artifacts=["Holdout, HTTP traces, browser network log, screenshots, regression XML, and the session-log truncation record."],
        ),
        testing=dict(
            focused="Combined 1065 passed / 20 failed; 17 were suite-order HTTP 503s. Isolated rerun 39 passed / 0 failed.",
            broader="Nine historical authority failures.",
            full_suite="Not run. No official ATGB or external independence.",
            runtime_validation="Two real HTTP campaigns and two normal browser campaigns, including cross-load.",
            model_runtime_boundary="0 live requests and 0 tokens. Offline fixture only.",
            new_regressions="0 product regressions. Protected session log hash was not recovered after a test truncated it.",
            pre_existing_failures="Three historical focused, six historical boundary, nine historical broader.",
        ),
        decisions_requiring_human_review=["No approval requested. No commit or push."],
        known_problems=dict(
            campaign_specific=["W12 misses expect_delays. Publication HTTP 500 was not reproduced and is unexplained.", "Browser-visible paint time was not instrumented.", "data/session_log.jsonl no longer matches the protected working-tree hash."],
            pre_existing=["Six startup/opening failures and nine authority failures remain."],
        ),
        missing_concepts=["Separate browser paint timings.", "A reproduced trace of the historical publication HTTP 500."],
        does_not_prove=["Full suite, official ATGB, external independent validation, live narration quality, or crash durability beyond the atomic replace."],
        recommended_next_step=v["next_step"],
        self_contained_review_test="20 requested reports, player-facing sentences, one-shot holdout, HTTP and browser traces, and explicit limits.",
        supporting_files=[
            dict(path=p.relative_to(ROOT).as_posix(), role="source" if p in sources else "campaign_evidence", why="PR-PLAY-71V source or verification evidence.", human_review_required=True, behavioral_evidence=p.suffix in {".json", ".jsonl", ".png", ".xml"})
            for p in sorted(set(paths))
        ],
    )
    (OUT / "review_config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    stage = OUT / "export_stage"
    result = build_handoff(config, root=ROOT, output_dir=stage, archive_history=False)
    previous = OUT / "previous_handoff"
    previous.mkdir(exist_ok=True)
    for name in ["CURRENT_REVIEW.md", "REVIEW_MANIFEST.json", "CURRENT_REVIEW.zip"]:
        dest = ROOT / "handoff" / name
        if dest.exists() and not (previous / name).exists():
            (previous / name).write_bytes(dest.read_bytes())
        pending = dest.with_name(name + ".pr71v.tmp")
        pending.write_bytes((stage / name).read_bytes())
        os.replace(pending, dest)
    stamp = datetime.now(timezone(timedelta(hours=-5))).strftime("%Y%m%d-%H%M%S")
    archive = ROOT / "handoff" / f"CURRENT_REVIEW({stamp}).zip"
    with archive.open("xb") as handle:
        handle.write((stage / "CURRENT_REVIEW.zip").read_bytes())
    with zipfile.ZipFile(archive) as zf:
        assert zf.testzip() is None
        manifest = json.loads(zf.read("REVIEW_MANIFEST.json"))
        for row in manifest["included_files"]:
            if row.get("sha256"):
                assert hashlib.sha256(zf.read(row["bundle_path"])).hexdigest() == row["sha256"]
        count = sum("/pr_play_71v/" in n and bool(re.search(r"/\d\d_[A-Z0-9_]+\.md$", n)) for n in zf.namelist())
        assert count == 20, count
    (OUT / "archive_path.txt").write_text(str(archive), encoding="utf-8")
    (OUT / "archive_verification.json").write_text(json.dumps(dict(path=str(archive), sha256=sha(archive), crc_valid=True, manifest_hashes_verified=True, reports=count, bytes=archive.stat().st_size, omitted=result["omitted"]), indent=2), encoding="utf-8")
    print(archive)


if __name__ == "__main__":
    main()
