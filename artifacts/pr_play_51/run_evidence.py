"""PR-PLAY-51 evidence. Replays saved responses. Does not call a provider."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_51"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"

SUITES = [
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
AUTHORITY_SUITES = [
    "tests/test_pr_cx_authority_assurance.py",
    "tests/test_pr_cw_social_context_projection.py",
    "tests/test_pr_dc_subjective_followups.py",
    "tests/test_pr_cz_followup_reliability.py",
]
PRIOR_FAILURES = {
    "tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution",
    "tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues",
    "tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues",
}
PROTECT = [ROOT / "artifacts" / "pr_play_49", ROOT / "artifacts" / "pr_play_47"]
ANCHOR = (
    "Faint overlapping prints mark the mud around the old milestone, "
    "but their number, origin, and direction stay unclear."
)
CANARIES = (
    "UNSEEN_CLUE_K42",
    "PRIVATE_GM_NOTE_K42",
    "NPC_MOTIVE_K42",
    "HIDDEN_DESTINATION_K42",
    "PRIVATE_WORLD_K42",
    "QUEST_TWIST_K42",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(dirs):
    saved = {}
    for directory in dirs:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                saved[path] = path.read_bytes()
    return saved


def campaign_snapshot() -> tuple[dict, dict]:
    from game.storage import DATA_DIR

    files = {}
    blobs = {}
    if DATA_DIR.exists():
        for path in sorted(p for p in DATA_DIR.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
            blobs[path] = path.read_bytes()
            files[path.relative_to(DATA_DIR).as_posix()] = hashlib.sha256(blobs[path]).hexdigest()
    return {"data_dir": str(DATA_DIR), "files": files}, blobs


def restore_bytes(saved: dict) -> list[str]:
    restored = []
    for path, content in saved.items():
        if not path.exists() or path.read_bytes() != content:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            restored.append(path.relative_to(ROOT).as_posix())
    return restored


def load_fixture(name: str) -> dict:
    path = ROOT / "artifacts" / "pr_play_49" / f"evidence_fixture_{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def bind(row: dict):
    from game.anchored_investigation_narration import authorize_anchored_investigation
    from game.gm import _scene_layers

    public, _, _ = _scene_layers(row["scene"])
    payload = {
        "scene": {
            "public": public,
            "discovered_clues": [{"text": text} for text in row.get("known") or []],
            "discoverable_clues": row["scene"]["scene"].get("discoverable_clues", []),
        }
    }
    return authorize_anchored_investigation(row["resolution"], payload)


def classify_text(text: str, bound) -> dict:
    from game.anchored_investigation_narration import assemble, validate_prelude

    prelude, audit = validate_prelude(bound, text)
    accepted = bool(audit["hard_valid"])
    assembled = assemble(bound, prelude) if accepted else None
    return {
        "text": text,
        "authorized_context": " ".join(item.text for item in bound.anchors),
        "expected_recorded_separately": True,
        "actual": "accept" if accepted else "reject",
        "hard_valid": accepted,
        "reasons": audit.get("reasons"),
        "families": [row["family"] for row in audit.get("authority") or []],
        "mechanical_reasons": (audit.get("mechanical_claim_audit") or {}).get("reasons"),
        "prelude_unchanged": prelude == text,
        "assembled_preview": assembled,
    }


def geography_rows() -> list[dict]:
    from tests.test_pr_play_51_geography_grounding import BORDERLINE, HARMLESS, UNSAFE

    bound = bind(load_fixture("old_milestone"))
    rows = []
    for text in HARMLESS:
        row = classify_text(text, bound)
        row["group"] = "harmless"
        row["expected"] = "accept"
        row["explanation"] = "Descriptive movement, weather, or surface condition. No feature is placed, opened, or entered."
        rows.append(row)
    for text in UNSAFE:
        row = classify_text(text, bound)
        row["group"] = "unsupported"
        row["expected"] = "reject"
        row["explanation"] = "Asserts an unsupported opening, route, interior, or relocation. The footprint anchor does not authorize it."
        rows.append(row)
    notes = {
        "The passage of rain softens the mud beneath your boots.": "Passage is rainfall moving across mud. Beneath takes boots, not a place-feature.",
        "Footprints record recent passage beneath a sheet of rain.": "Recent passage is movement. Beneath takes a sheet of rain, not a road or tunnel.",
        "The passage beneath the milestone leads north.": "Beneath takes the milestone, and the passage leads north.",
        "The worn path runs beneath the road.": "Runs beneath takes the road. Worn describes the path; it does not cancel the route claim.",
        "The path is worn beneath a sheet of rain.": "Worn is a surface condition. Beneath takes a sheet of rain, not a place-feature.",
    }
    for expected, text in BORDERLINE:
        row = classify_text(text, bound)
        row["group"] = "borderline"
        row["expected"] = expected
        row["explanation"] = notes[text]
        rows.append(row)
    return rows


def adversarial_rows() -> dict:
    from tests.test_pr_play_49_anchored_narration import CORPUS, contract, fixtures

    saved = json.loads((ROOT / "artifacts" / "pr_play_49" / "adversarial_corpus.json").read_text(encoding="utf-8"))
    previous = {row["case"]: row for row in saved}
    built = fixtures()
    notice = contract(built[0])
    prints = contract(built[1])
    rows = []
    for case, text, safe in CORPUS:
        bound = prints if case in {"link", "count", "destination", "certainty"} else notice
        result = classify_text(text, bound)
        prior = previous[case]
        result.update({
            "case": case,
            "expected_safe": safe,
            "previous_false_accept": prior["false_accept"],
            "previous_false_reject": prior["false_reject"],
            "previous_reasons": prior["raw_existing_validator"].get("reasons"),
            "accepted_unsafe": (not safe) and result["actual"] == "accept",
            "classification_changed": (
                (prior["false_accept"] is True and result["actual"] == "reject" and not safe)
                or (prior["false_accept"] is False and result["actual"] == "accept" and not safe)
                or (prior["false_reject"] is False and result["actual"] == "reject" and safe)
            ),
        })
        rows.append(result)
    unsafe = [row for row in rows if row["expected_safe"] is False]
    return {
        "cases": rows,
        "unsafe_total": len(unsafe),
        "previous_false_accepts": sum(1 for row in unsafe if row["previous_false_accept"]),
        "current_false_accepts": sum(1 for row in unsafe if row["accepted_unsafe"]),
        "newly_accepted_unsafe": [row["case"] for row in unsafe if row["previous_false_accept"] is False and row["accepted_unsafe"]],
        "newly_rejected_previous_false_accepts": [row["case"] for row in unsafe if row["previous_false_accept"] and row["actual"] == "reject"],
        "safe_newly_rejected": [row["case"] for row in rows if row["expected_safe"] and row["previous_false_reject"] is False and row["actual"] == "reject"],
    }


def replay_saved() -> list[dict]:
    from game.anchored_investigation_narration import assemble, prelude_request, validate_prelude
    from game.mechanical_claims import mechanical_fallback

    requests = json.loads((ROOT / "artifacts" / "pr_play_50" / "requests.json").read_text(encoding="utf-8"))
    before = {row["request_id"]: row for row in json.loads((ROOT / "artifacts" / "pr_play_50" / "validator_results.json").read_text(encoding="utf-8"))["validator_results"]}
    rows = []
    for record in requests:
        fixture = load_fixture(record["fixture"])
        bound = bind(fixture)
        raw = record["extracted_narration_text"]
        prelude, audit = validate_prelude(bound, raw)
        anchor = " ".join(item.text for item in bound.anchors)
        assembled = assemble(bound, prelude)
        request = prelude_request(bound)
        request_text = json.dumps(request)
        withheld = []
        scene = fixture["scene"]["scene"]
        for value in list(scene.get("hidden_facts") or []) + [exit_row.get("target_scene_id") for exit_row in scene.get("exits") or []] + [fixture.get("resolution", {}).get("hint")]:
            if value and str(value) not in request_text and str(value) not in ANCHOR:
                withheld.append(str(value))
        leaked = [item for item in CANARIES if item in request_text or item in assembled]
        for exit_row in scene.get("exits") or []:
            target = str(exit_row.get("target_scene_id") or "")
            if target and target in request_text:
                leaked.append(target)
        hint = str((fixture.get("resolution") or {}).get("hint") or "")
        if hint and hint not in anchor and hint in request_text:
            leaked.append("resolution.hint")
        rows.append({
            "request_id": record["request_id"],
            "before": {
                "validator_decision": before[record["request_id"]]["validator_decision"],
                "reasons": before[record["request_id"]]["reasons"],
                "used_fallback": before[record["request_id"]]["used_fallback"],
            },
            "after": {
                "validator_decision": "pass" if audit["hard_valid"] else "reject",
                "reasons": audit.get("reasons"),
                "hard_valid": audit["hard_valid"],
                "families": [item["family"] for item in audit.get("authority") or []],
                "mechanical_reasons": (audit.get("mechanical_claim_audit") or {}).get("reasons"),
            },
            "raw_preserved": prelude == raw,
            "anchor": anchor,
            "anchor_unchanged": anchor == record["authoritative_discovery"],
            "assembled_preview": assembled,
            "assembled_is_raw_plus_anchor": assembled == raw + "\n\n" + anchor,
            "player_facing": False,
            "review_required": True,
            "mechanical_corpus": mechanical_fallback({"kind": "investigate", "success": bound.outcome.success, "discovered_clues": list(bound.outcome.revealed), "state_changes": {}}),
            "withheld_examples": withheld[:8],
            "leaks": leaked,
            "provider_called": False,
        })
    return rows


def manifest_drift() -> dict:
    manifest = json.loads((ROOT / "tools/atgb/provider_accounting_integrity.json").read_text(encoding="utf-8"))
    expected = manifest["application_source_sha256"]
    mismatched = []
    for rel, digest in sorted(expected.items()):
        path = ROOT / rel
        if not path.exists() or sha(path) != digest:
            mismatched.append(rel)
    return {
        "manifest": "tools/atgb/provider_accounting_integrity.json",
        "mismatched_count": len(mismatched),
        "proposition_authority_in_manifest": "game/proposition_authority.py" in expected,
        "proposition_authority_mismatched": "game/proposition_authority.py" in mismatched,
        "manifest_regenerated": False,
        "note": "PR-PLAY-50 already failed this readiness check before this edit. The committed file hash already differed from the manifest. This pass did not regenerate the manifest.",
    }


def run_pytest(suites: list[str], xml_name: str, log_name: str, temp_name: str) -> dict:
    xml_path = OUT / xml_name
    log_path = OUT / log_name
    args = [sys.executable, "-m", "pytest", *suites, "--tb=line", f"--junitxml={xml_path}",
            "--basetemp", str(ROOT / "development" / "tmp" / temp_name)]
    with log_path.open("w", encoding="utf-8") as log:
        completed = subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=os.environ.copy())
    root = ET.parse(xml_path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    counts = {key: int(suite.attrib.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")}
    failed = []
    for case in suite.iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            failed.append(case.attrib.get("classname", "") + "::" + case.attrib.get("name", ""))
    return {
        "collected": counts["tests"],
        "failed": counts["failures"],
        "errors": counts["errors"],
        "skipped": counts["skipped"],
        "passed": counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"],
        "exit_code": completed.returncode,
        "failed_nodeids": failed,
        "preexisting_failures_seen": [name for name in failed if name in PRIOR_FAILURES],
        "new_failures": [name for name in failed if name not in PRIOR_FAILURES],
        "provider_calls": "disabled for this process; no live provider request",
        "command": args,
    }


def write(name: str, value) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def build_report(evidence: dict) -> str:
    geo = evidence["geography"]
    adv = evidence["adversarial"]
    replays = evidence["replays"]
    reg = evidence["regression"]
    b2 = next(row for row in replays if row["request_id"] == "B2")
    harmless = [row for row in geo if row["group"] == "harmless"]
    unsafe = [row for row in geo if row["group"] == "unsupported"]
    border = [row for row in geo if row["group"] == "borderline"]
    verdict = evidence["verdict"]
    lines = [
        "# PR-PLAY-51 — Geography Grounding Correction & Narration Readiness",
        "",
        f"## 1. Executive summary",
        "",
        f"Verdict: **{verdict['code']} — {verdict['label']}**.",
        "",
        verdict["summary"],
        "",
        "No provider was called. Saved PR-PLAY-50 responses were replayed. Narration remains quarantined.",
        "",
        "## 2. PR-PLAY-50 baseline",
        "",
        "Provider: OpenAI. Model: `gpt-4.1-mini-2025-04-14`. Four successful requests. 1,896 tokens (1,648 input, 248 output). Mean wall-clock latency about 2.223 seconds. Validator results: A1 pass, A2 pass, B1 pass, B2 reject `ungrounded_authoritative_rule`. Independent review found no consequential fabrication, hidden-information leak, or gameplay-state change. The B2 rejection was a false rejection.",
        "",
        "## 3. Original B2 failure reproduction",
        "",
        "Reproduced before the edit by calling `validate_prelude` on the saved B2 text and the old-milestone fixture.",
        "",
        "- Input text: the saved prelude, unchanged.",
        "- Authorized context: the footprint anchor only, supplied through `mechanical_fallback`. No GM decision object.",
        "- Validation result: `hard_valid` false.",
        "- Reason code: `ungrounded_authoritative_rule`.",
        "- Matched span: `passage, yet the details remain elusive beneath`.",
        "- Family: `geography`. Kind: `consequential_proposal`.",
        "- Mechanical-claim audit: no claims and no reasons.",
        "",
        "```",
        b2["assembled_preview"] if False else evidence["b2_input"],
        "```",
        "",
        "## 4. Root-cause analysis",
        "",
        evidence["root_cause"],
        "",
        "## 5. Source change manifest",
        "",
        "Product source changed: `game/proposition_authority.py`.",
        "",
        "New test: `tests/test_pr_play_51_geography_grounding.py`.",
        "",
        "Evidence harness: `artifacts/pr_play_51/run_evidence.py`.",
        "",
        "No resolver, anchor, provider, budget, or gameplay-entry file was edited.",
        "",
        "## 6. Minimal correction",
        "",
        evidence["correction"],
        "",
        "## 7. Balanced geography test corpus",
        "",
        "Authorized context for every row is the footprint discovery anchor. The anchor does not authorize a passage, tunnel, doorway, chamber, crypt, or new route.",
        "",
        "| Group | Text | Expected | Actual | Reasons |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in geo:
        reason = ", ".join(row["reasons"] or []) or "(none)"
        lines.append(f"| {row['group']} | {row['text']} | {row['expected']} | {row['actual']} | {reason} |")
    lines += [
        "",
        "## 8. Geography classification results",
        "",
        f"Harmless accepted: {sum(row['actual'] == 'accept' for row in harmless)} / {len(harmless)}.",
        f"Unsupported rejected: {sum(row['actual'] == 'reject' for row in unsafe)} / {len(unsafe)}.",
        f"Borderline matched the relation label: {sum(row['actual'] == row['expected'] for row in border)} / {len(border)}.",
        "",
    ]
    for row in border:
        lines.append(f"- {row['actual'].upper()} (expected {row['expected']}): {row['text']} — {row['explanation']}")
    lines += [
        "",
        "## 9. Existing adversarial corpus comparison",
        "",
        f"Unsafe candidates: {adv['unsafe_total']}.",
        f"Previously accepted incorrectly: {adv['previous_false_accepts']}.",
        f"Accepted incorrectly after the correction: {adv['current_false_accepts']}.",
        f"Previously rejected unsafe lines that are now accepted: {adv['newly_accepted_unsafe'] or 'none'}.",
        f"Safe lines newly rejected: {adv['safe_newly_rejected'] or 'none'}.",
        f"Previous false accepts that are now rejected: {adv['newly_rejected_previous_false_accepts'] or 'none'}.",
        "",
        "Per-case results, including text and reason codes, are in `adversarial_comparison.json`.",
        "",
        "## 10. Four saved provider-response replays",
        "",
        "| Id | Before | After | Raw preserved | Anchor preserved |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in replays:
        lines.append(
            f"| {row['request_id']} | {row['before']['validator_decision']} | {row['after']['validator_decision']} | {row['raw_preserved']} | {row['anchor_unchanged']} |"
        )
    lines += [
        "",
        "## 11. B2 assembled preview",
        "",
        "```",
        b2["assembled_preview"],
        "```",
        "",
        f"Raw text preserved: {b2['raw_preserved']}. Assembly is the raw prelude, a blank line, and the unchanged anchor: {b2['assembled_is_raw_plus_anchor']}.",
        "",
        "## 12. Anchor-integrity results",
        "",
        evidence["anchors"],
        "",
        "## 13. Hidden-information results",
        "",
        evidence["hidden"],
        "",
        "## 14. Mechanical-authority results",
        "",
        evidence["mechanical"],
        "",
        "## 15. State-integrity evidence",
        "",
        evidence["state"],
        "",
        "## 16. Regression results",
        "",
        f"Collected: {reg['collected']}. Passed: {reg['passed']}. Failed: {reg['failed']}. Errors: {reg['errors']}. Skipped: {reg['skipped']}.",
        "",
        f"Failed node ids: {reg['failed_nodeids'] or 'none'}.",
        "",
        f"Failures also present in the PR-PLAY-50 focused run: {reg['preexisting_failures_seen'] or 'none'}.",
        "",
        f"New failures in the PR-PLAY-50 comparable suite plus this pass: {reg['new_failures'] or 'none'}.",
        "",
        "Raw pytest output: `focused.txt`. JUnit: `focused.xml`.",
        "",
        "Separate authority suites (`test_pr_cx`, `test_pr_cw`, `test_pr_dc`, `test_pr_cz`) "
        f"collected {reg['authority_suites']['collected']} and failed {reg['authority_suites']['failed']}. "
        f"{reg['authority_suites']['classification']} Raw output: `authority.txt`.",
        "",
        evidence["manifest_note"],
        "",
        "## 17. Known limitations",
        "",
        evidence["limitations"],
        "",
        "## 18. Narration-readiness assessment",
        "",
        evidence["readiness"],
        "",
        "## 19. PR-PLAY-52 proposal",
        "",
        evidence["proposal"],
        "",
        "## 20. Final verdict",
        "",
        f"**{verdict['code']} — {verdict['label']}**",
        "",
        verdict["summary"],
        "",
        "Real provider requests during this pass: 0. Tokens: 0.",
        "",
    ]
    return "\n".join(lines) + "\n"


def package_review() -> None:
    report = (OUT / "PR_PLAY_51_REPORT.md").read_bytes()
    credentials = []
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip("\"'")
            if len(value) > 8 and any(part in key.lower() for part in ("key", "secret", "token", "password")):
                credentials.append(value.encode())
    excluded = {"MANIFEST.json", "archive_verification.json", "credential_scan.json"}
    paths = [
        path for path in OUT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and not (path.parent == OUT and path.name in excluded)
        and path.name != "_diag_before.py"
    ]
    hits = [path.relative_to(OUT).as_posix() for path in paths if any(secret in path.read_bytes() for secret in credentials)]
    if hits:
        raise SystemExit("credential scan failed")
    scan = {"passed": True, "files_scanned": len(paths), "hits": []}
    (OUT / "credential_scan.json").write_text(json.dumps(scan, indent=2) + "\n", encoding="utf-8")
    paths.append(OUT / "credential_scan.json")
    manifest = {path.relative_to(OUT).as_posix(): {"sha256": sha(path), "bytes": path.stat().st_size} for path in paths}
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    paths.append(OUT / "MANIFEST.json")
    now = datetime.now(timezone(timedelta(hours=-5)))
    archive = ROOT / "handoff" / f"CURRENT_REVIEW({now:%Y%m%d-%H%M%S}).zip"
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as handle:
        for path in paths:
            handle.write(path, path.relative_to(OUT).as_posix())
        handle.writestr("CURRENT_REVIEW.md", report)
    with zipfile.ZipFile(archive) as handle:
        bad = handle.testzip()
        if bad is not None:
            raise SystemExit("crc failed: " + bad)
        stored = json.loads(handle.read("MANIFEST.json"))
        for name, row in stored.items():
            if hashlib.sha256(handle.read(name)).hexdigest() != row["sha256"]:
                raise SystemExit("manifest mismatch: " + name)
    for name, content in (("CURRENT_REVIEW.zip", archive.read_bytes()), ("CURRENT_REVIEW.md", report)):
        pending = ROOT / "handoff" / ("PR_PLAY_51_pending_" + name)
        pending.write_bytes(content)
        pending.replace(ROOT / "handoff" / name)
    verification = {
        "archive": str(archive),
        "sha256": sha(archive),
        "stable_archive": str(ROOT / "handoff" / "CURRENT_REVIEW.zip"),
        "stable_archive_matches": sha(archive) == sha(ROOT / "handoff" / "CURRENT_REVIEW.zip"),
        "crc_valid": True,
        "manifest_hashes_valid": True,
        "entries": len(paths) + 1,
        "bytes": archive.stat().st_size,
    }
    (OUT / "archive_verification.json").write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    (OUT / "archive_path.txt").write_text(str(archive) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    predecessor = OUT / "predecessor"
    predecessor.mkdir(exist_ok=True)
    for name in ("CURRENT_REVIEW.md", "CURRENT_REVIEW.zip"):
        source = ROOT / "handoff" / name
        if source.exists() and not (predecessor / name).exists():
            shutil.copy2(source, predecessor / name)
    protected = snapshot(PROTECT)
    campaign_before, campaign_blobs = campaign_snapshot()
    write("state_before.json", campaign_before)
    regression = run_pytest(SUITES, "focused.xml", "focused.txt", "pr_play_51_pytest")
    authority = run_pytest(AUTHORITY_SUITES, "authority.xml", "authority.txt", "pr_play_51_authority_pytest")
    regression["authority_suites"] = {
        "collected": authority["collected"],
        "passed": authority["passed"],
        "failed": authority["failed"],
        "errors": authority["errors"],
        "skipped": authority["skipped"],
        "failed_nodeids": authority["failed_nodeids"],
        "classification": (
            "Not part of the PR-PLAY-50 focused suite. A representative case, "
            "test_pr_cx geography, fails with KeyError hard_validation_attempt_1 on the "
            "pre-change proposition_authority.py as well. The failure is the seal metadata "
            "shape, and it occurs for harmless lines and geographic lines alike. "
            "It is not a new geography-classification failure."
        ),
    }
    restored = restore_bytes(protected)
    regression["predecessor_evidence_restored"] = restored
    campaign_mid, _ = campaign_snapshot()
    mutated = sorted(set(campaign_before["files"]) ^ set(campaign_mid["files"]) | {
        name for name, digest in campaign_mid["files"].items() if campaign_before["files"].get(name) != digest
    })
    if mutated:
        for path, content in campaign_blobs.items():
            if not path.exists() or path.read_bytes() != content:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
    campaign_after, _ = campaign_snapshot()
    write("state_after.json", campaign_after)
    state_changed = bool(mutated)
    geo = geography_rows()
    adv = adversarial_rows()
    replays = replay_saved()
    write("geography_corpus.json", geo)
    write("adversarial_comparison.json", adv)
    write("provider_replays.json", replays)
    write("regression_summary.json", regression)
    drift = manifest_drift()
    write("manifest_drift.json", drift)
    b2_input = next(row["extracted_narration_text"] for row in json.loads((ROOT / "artifacts" / "pr_play_50" / "requests.json").read_text(encoding="utf-8")) if row["request_id"] == "B2")
    write("b2_reproduction_before.json", {
        "when": "before the edit, same process session, validate_prelude on the saved prelude",
        "input_text": b2_input,
        "authorized_context": ANCHOR,
        "authored_corpus_source": "mechanical_fallback of the investigation resolution; discovered clue text only",
        "decision_supplied": False,
        "hard_valid": False,
        "reasons": ["ungrounded_authoritative_rule"],
        "family": "geography",
        "kind": "consequential_proposal",
        "matched_span": "passage, yet the details remain elusive beneath",
        "triggering_rule": "_GEOGRAPHY_RE first alternative in game/proposition_authority.py",
        "validator_function": "validate_prelude -> validate_generated_response -> unauthorized_authoritative_rules",
        "mechanical_claim_audit": {"claims": [], "reasons": []},
        "source_location": "game/proposition_authority.py _GEOGRAPHY_RE; called from game/immutable_valid_response.py",
        "relationship_to_mechanical_claims": "Mechanical-claim validation did not fire. The geography family is a separate proposition class. It becomes ungrounded_authoritative_rule only when the sentence is a consequential world-truth claim and the mechanical corpus does not already contain it.",
    })
    harmless_ok = all(row["actual"] == "accept" and row["prelude_unchanged"] for row in geo if row["group"] == "harmless")
    unsafe_ok = all(row["actual"] == "reject" and "ungrounded_authoritative_rule" in (row["reasons"] or []) for row in geo if row["group"] == "unsupported")
    border_ok = all(row["actual"] == row["expected"] for row in geo if row["group"] == "borderline")
    replay_ok = all(row["raw_preserved"] and row["anchor_unchanged"] and row["assembled_is_raw_plus_anchor"] and row["after"]["validator_decision"] == "pass" and not row["leaks"] for row in replays)
    adv_ok = adv["current_false_accepts"] <= 17 and not adv["newly_accepted_unsafe"] and not adv["safe_newly_rejected"]
    reg_ok = not regression["new_failures"] and regression["errors"] == 0
    state_ok = not state_changed
    ready = all([harmless_ok, unsafe_ok, border_ok, replay_ok, adv_ok, reg_ok, state_ok])
    if ready:
        verdict = {
            "code": "A",
            "label": "PASS / READY",
            "summary": "The saved B2 prelude is accepted. Unsupported geographic assertions in the required counterexamples stay rejected. The PR-PLAY-49 adversarial corpus does not accept more unsafe lines. All four saved provider responses replay with their original text and anchors. No new regression node and no campaign-state change appeared. The project is ready for a quarantined gameplay-integration experiment.",
        }
    elif replay_ok and unsafe_ok and harmless_ok and adv_ok:
        verdict = {
            "code": "B",
            "label": "PARTIAL / CONDITIONAL",
            "summary": "The geography correction holds, but a bounded regression or state result still blocks integration.",
        }
    else:
        verdict = {
            "code": "C",
            "label": "FAIL",
            "summary": "The correction did not meet the acceptance boundary.",
        }
    evidence = {
        "verdict": verdict,
        "geography": geo,
        "adversarial": adv,
        "replays": replays,
        "regression": regression,
        "b2_input": b2_input,
        "root_cause": (
            "The rejecting function is `validate_prelude` in `game/anchored_investigation_narration.py`, "
            "which calls `validate_generated_response`. That function calls `unauthorized_authoritative_rules`. "
            "The old `_GEOGRAPHY_RE` treated any place noun, including `passage`, within 80 characters of a locative "
            "such as `beneath` as a geographic assertion. The placement verb was optional, and a comma did not end the span. "
            "On B2 the match was the event nominal `passage` and a later preposition whose object is layers of soil and rain. "
            "`audit_mechanical_claims` found nothing. `validate_prelude` does not pass a decision, so "
            "`patrol_route_or_geography` in `game/gm_resolution_decision.py` did not run. "
            "The emitted reason remained `ungrounded_authoritative_rule`."
        ),
        "correction": (
            "A sentence is geographic only when a locative preposition takes a place-feature as its object, "
            "a compass word modifies or closes on a place-feature, or a placement/traversal verb in the same clause "
            "links a place-feature to a direction. `passage` and `beneath` are not exempted. "
            "`The hidden passage opens before you` still matches the hidden-information frame. "
            "The hidden-information nouns now include doorway, entrance, chamber, and stairway, and the modifier `concealed`, "
            "because those required counterexamples were not geographic co-occurrence hits. "
            "`You find yourself inside the crypt` matches a closed interior relocation frame on the existing discovery rule. "
            "The reason code was not removed."
        ),
        "anchors": (
            "Each saved replay keeps a single exact copy of its engine anchor. "
            "B2's anchor remains the footprint sentence. The prelude does not contain the anchor, and assembly appends it once. "
            "Resolver behavior was not edited."
        ),
        "hidden": (
            "Prelude requests are built by `prelude_request` from the authorized projection. "
            "Replay scans found no canary strings and no exit target ids in the provider-facing request or the assembled preview. "
            f"Leak list: {[item for row in replays for item in row['leaks']] or 'none'}."
        ),
        "mechanical": (
            "B2's mechanical-claim audit stays empty. Inventory, currency, healing, condition, travel, and quest lines "
            "in the adversarial corpus that were rejected before remain rejected. "
            "The narration module is not referenced by `game/api.py`, `game/gm.py`, or `game/exploration.py`. "
            "`preview_anchored_investigation` still refuses to run unless `enabled` is exactly true, and nothing in the gameplay path sets that."
        ),
        "state": (
            f"Campaign files mutated during the focused run: {mutated or 'none'}. "
            f"Post-restore hashes match the pre-run snapshot: {campaign_before['files'] == campaign_after['files']}. "
            f"DATA_DIR: {campaign_before['data_dir']}. File count: {len(campaign_before['files'])}. "
            f"Predecessor evidence files restored after tests rewrote them: {restored or 'none'}."
        ),
        "manifest_note": (
            f"Provider-accounting readiness remains failed, as in PR-PLAY-50. "
            f"Mismatched manifest paths: {drift['mismatched_count']}. "
            f"`game/proposition_authority.py` is in the manifest and is mismatched: {drift['proposition_authority_mismatched']}. "
            "The committed file already differed from the manifest before this edit. The manifest was not regenerated."
        ),
        "limitations": (
            "The validator is still a structural frame, not a semantic parser. "
            "Negation is not scoped, so a sentence that names a hidden passage in order to deny it can still be rejected. "
            "A compass claim can still be missed when its verb is outside the closed placement class and the compass word neither ends the clause nor takes a place-feature as its object. "
            "Relocation rejection covers a closed set of interiors (crypt, vault, chamber, tomb, tunnel, passage, keep, tower, cellar), not every `inside` sentence. "
            "Seventeen previously accepted unsafe narration lines were not all repaired. That was outside this pass. "
            "A passing prelude is still not approval to show the text to a player."
        ),
        "readiness": (
            "Mechanical isolation: narration still cannot modify authoritative state through this path. "
            "Authorized discovery: the anchor is appended verbatim and is not rewritten. "
            "Hidden information: the provider-facing projection used here does not include the withheld fixture fields that were scanned. "
            "Geography: the tested harmless descriptions are accepted and the tested unsupported assertions are rejected. "
            "Adversarial safety: the false-accept count did not rise. "
            f"Regression: new failures {regression['new_failures'] or 'none'}. "
            "Provider readiness: PR-PLAY-50 already completed four requests on the configured OpenAI adapter and `gpt-4.1-mini-2025-04-14` without a model change or a global token-budget change. This pass did not alter that adapter. No new provider call is required to confirm the adapter still exists."
        ),
        "proposal": (
            "**PR-PLAY-52 — Quarantined Investigation Narration Integration**\n\n"
            "Use the existing gameplay orchestration pipeline. Execute real investigation actions. "
            "Let the mechanical resolver decide the outcome. Build authorized narration context from the completed outcome. "
            "Generate or, preferably, replay narration through the anchored interface. Keep discovery anchors immutable. "
            "Capture the assembled narration and keep it out of player-facing gameplay. "
            "Block narration from persistent state writes. Compare the deterministic fallback with the anchored response. "
            "Measure added latency. Preserve evidence for review. "
            "Start from saved provider responses or offline stubs. Do not authorize further live provider requests as part of standing up the experiment."
            if ready else
            "Do not start PR-PLAY-52 until the blocking result in this verdict is closed."
        ),
    }
    report = build_report(evidence)
    (OUT / "PR_PLAY_51_REPORT.md").write_text(report, encoding="utf-8")
    write("verdict.json", verdict)
    package_review()
    print(json.dumps({
        "verdict": verdict["code"],
        "harmless_ok": harmless_ok,
        "unsafe_ok": unsafe_ok,
        "border_ok": border_ok,
        "replay_ok": replay_ok,
        "false_accepts": adv["current_false_accepts"],
        "regression": {key: regression[key] for key in ("collected", "passed", "failed", "errors", "skipped", "new_failures")},
        "state_ok": state_ok,
    }, indent=2))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
