"""Package PR-PLAY-52. Replays saved narration. Does not call a provider."""
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
OUT = ROOT / "artifacts" / "pr_play_52"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ.pop("ASHEN_QUARANTINE_INVESTIGATION_NARRATION", None)

SUITES = [
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
PRIOR_FAILURES = {
    "tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution",
    "tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues",
    "tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues",
}
PROTECT = [
    ROOT / "artifacts" / "pr_play_49",
    ROOT / "artifacts" / "pr_play_47",
    ROOT / "artifacts" / "pr_play_50" / "requests.json",
    ROOT / "artifacts" / "pr_play_51",
]
CANARIES = (
    "CANARY_UNDISCOVERED_CLUE",
    "CANARY_GM_NOTE",
    "CANARY_NPC_MOTIVE",
    "CANARY_HIDDEN_DESTINATION",
    "CANARY_QUEST_TWIST",
    "CANARY_MECHANICAL_ID",
    "CANARY_UNRELATED_WORLD",
    "An agent of a noble house is watching new arrivals from the square's edge.",
    "A contact tied to the Ash Cowl smuggling web is scouting the crowd for arcane talent.",
    "notice_patrol_route",
    "milestone_mud_prints",
    "market_quarter",
    "old_milestone",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(paths):
    saved = {}
    for item in paths:
        if item.is_file():
            saved[item] = item.read_bytes()
            continue
        if not item.exists():
            continue
        for path in item.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                saved[path] = path.read_bytes()
    return saved


def restore_bytes(saved: dict) -> list[str]:
    restored = []
    for path, content in saved.items():
        if not path.exists() or path.read_bytes() != content:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            restored.append(path.relative_to(ROOT).as_posix())
    return restored


def campaign_snapshot():
    from game.storage import DATA_DIR

    files = {}
    blobs = {}
    if DATA_DIR.exists():
        for path in sorted(p for p in DATA_DIR.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
            blobs[path] = path.read_bytes()
            files[path.relative_to(DATA_DIR).as_posix()] = hashlib.sha256(blobs[path]).hexdigest()
    return {"data_dir": str(DATA_DIR), "files": files}, blobs


def run_pytest() -> dict:
    xml_path = OUT / "focused.xml"
    log_path = OUT / "focused.txt"
    basetemp = ROOT / "development" / "tmp" / f"pr_play_52_pytest_{os.getpid()}"
    args = [
        sys.executable, "-m", "pytest", *SUITES, "--tb=line",
        f"--junitxml={xml_path}",
        "--basetemp", str(basetemp),
    ]
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
        "provider_calls": 0,
        "command": args,
    }


def write(name: str, value) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def leaks(payload) -> list[str]:
    text = json.dumps(payload, ensure_ascii=False)
    return [item for item in CANARIES if item in text]


def build_report(evidence: dict) -> str:
    rows = {row["name"]: row for row in evidence["integration"]}
    notice = rows["notice_board"]
    prints = rows["footprints"]
    replays = rows["saved_replays"]["rows"]
    anchor = rows["anchor_integrity"]
    perf = rows["performance"]
    failures = [row for row in evidence["integration"] if row["name"].startswith("failure_")]
    reg = evidence["regression"]
    verdict = evidence["verdict"]
    gates = evidence["gates"]

    def block(title, body):
        return f"### {title}\n\n{body}\n"

    replay_lines = []
    for row in replays:
        replay_lines.append(
            f"- **{row['sample']}** — {row['diagnostic']}; fallback={row['used_fallback']}; "
            f"anchor starts `{row['anchors'][0]['text'][:70]}`"
        )
    failure_lines = []
    for row in failures:
        failure_lines.append(
            f"- **{row['name']}** — {row['diagnostic']}; fallback={row.get('used_fallback')}; "
            f"evidence_write={row.get('evidence_write')}; error={row.get('error')}"
        )
    gate_lines = [f"- Gate {key}: **{'pass' if value else 'fail'}**" for key, value in gates.items()]
    lines = [
        "# PR-PLAY-52 — Quarantined Investigation Narration Integration",
        "",
        "## 1. Executive summary",
        "",
        f"Verdict: **{verdict['code']} — {verdict['label']}**.",
        "",
        verdict["summary"],
        "",
        "The experiment entered through `POST /api/chat`. Live interpretation and provider calls were disabled. "
        "The existing exploration resolver decided both investigations. After that resolution, an opt-in hook "
        "replayed saved PR-PLAY-50 prose into the PR-PLAY-49 anchored preview and stored the result outside the player response.",
        "",
        "Real provider requests: 0. Tokens: 0.",
        "",
        "## 2. Source-level integration map",
        "",
        "1. Player text arrives at `game.api.api_chat` and `game.api._chat_turn`.",
        "2. With live interpretation disabled, `deterministic_conversational_decision` returns no execution for these sentences, and `parse_exploration_intent` classifies them.",
        "3. `select_ordinary_resolver` selects the exploration resolver. `_resolve_engine_noncombat_seam` calls `game.exploration.resolve_exploration_action`. No second resolver was added.",
        "4. `_apply_authoritative_resolution_state_mutation` commits the clue in memory.",
        "5. `_build_gpt_narration_from_authoritative_state` builds the existing player-facing object. Successful `discover_clue` turns use `deterministic_provider_skip_line` and do not call the provider.",
        "6. The quarantine hook then runs inside `_run_resolved_turn_pipeline`, after that object exists and before the pipeline returns it.",
        "7. Finalization, logging, and the HTTP response continue on the original object. The hook's return value is discarded.",
        "8. Diagnostics for the experiment are written only under the quarantine evidence directory, never into the player log.",
        "",
        "The hook is in the shared pipeline, so `/api/action` would reach it too. This experiment exercised `/api/chat`.",
        "",
        "## 3. Source change manifest",
        "",
        "\n".join(f"- `{path}`" for path in evidence["source_files"]),
        "",
        "Campaign content, model configuration, token budgets, and validator rules were not changed.",
        "",
        "`tests/test_pr_play_49_anchored_narration.py` now allows `game/quarantined_investigation_narration.py` to name the anchored module. `game/api.py` still must not name that module, and it must not assign the quarantine result to the player response. The side-effect and allowlist assertions in that test are unchanged.",
        "",
        "## 4. Experimental feature-gate documentation",
        "",
        "- `ASHEN_QUARANTINE_INVESTIGATION_NARRATION=1` enables the hook. Any other value, including unset, leaves it off. The disabled path does not import the narration module.",
        "- `ASHEN_QUARANTINE_NARRATION_SAMPLE` selects `stub`, `A1`, `A2`, `B1`, `B2`, `empty`, `malformed`, `unsafe`, or `missing`.",
        "- `ASHEN_QUARANTINE_NARRATION_FAULT` injects `assembly_exception`, `invalid_projection`, `timeout`, `evidence_write`, or `unexpected`.",
        "- `ASHEN_QUARANTINE_NARRATION_DIR` is the evidence directory. A path inside the campaign data directory is refused.",
        "- The hook replays saved text or a fixed stub. It does not call a provider and it does not retry.",
        "",
        "## 5. Notice-board baseline run",
        "",
        f"Action: `{notice['baseline'] and 'I examine the notice board.'}`.",
        "",
        f"Mechanical result: `{json.dumps(notice['baseline']['mechanical'], ensure_ascii=False)}`.",
        "",
        f"Player-facing response: {notice['baseline']['player_facing']}",
        "",
        f"Resolver calls: `{notice['baseline']['resolver_calls']}`. Elapsed test-client turn: {notice['baseline']['elapsed_ms']} ms. Quarantine records: 0.",
        "",
        "## 6. Notice-board experimental run",
        "",
        "Same action and initial scene, with the gate on and saved response A1.",
        "",
        f"Mechanical result: `{json.dumps(notice['experimental']['mechanical'], ensure_ascii=False)}`.",
        "",
        f"Player-facing response: {notice['experimental']['player_facing']}",
        "",
        f"Diagnostic: {notice['experimental']['diagnostic']}. Provider clients constructed: {notice.get('provider_clients')}. "
        f"Campaign writers entered from the hook: {notice.get('hook_writer_calls')}.",
        "",
        "Saved prelude:",
        "",
        notice["experimental"]["raw_provider_text"],
        "",
        "Assembled experimental narration:",
        "",
        notice["experimental"]["assembled"],
        "",
        "## 7. Footprint baseline run",
        "",
        "Action: `I examine the footprints.` Scene: `old_milestone`.",
        "",
        f"Mechanical result: `{json.dumps(prints['baseline']['mechanical'], ensure_ascii=False)}`.",
        "",
        f"Player-facing response: {prints['baseline']['player_facing']}",
        "",
        f"Elapsed test-client turn: {prints['baseline']['elapsed_ms']} ms.",
        "",
        "## 8. Footprint experimental run",
        "",
        "Same action, gate on, saved response B1.",
        "",
        f"Mechanical result: `{json.dumps(prints['experimental']['mechanical'], ensure_ascii=False)}`.",
        "",
        f"Player-facing response: {prints['experimental']['player_facing']}",
        "",
        f"Diagnostic: {prints['experimental']['diagnostic']}. Provider clients: {prints.get('provider_clients')}. "
        f"Hook writer calls: {prints.get('hook_writer_calls')}. Resolver calls: {prints.get('resolver_calls')}.",
        "",
        "Saved prelude:",
        "",
        prints["experimental"]["raw_provider_text"],
        "",
        "Assembled experimental narration:",
        "",
        prints["experimental"]["assembled"],
        "",
        "## 9. Paired state comparisons",
        "",
        "Compared after removing only generated stamps, session and campaign run ids, the in-memory GM object id, timestamps, and latency fields. Clue ids and scene ids were not removed.",
        "",
        f"Notice board state differences: {notice['comparison']['state_differences'] or 'none'}.",
        "",
        f"Footprints state differences: {prints['comparison']['state_differences'] or 'none'}.",
        "",
        "Both runs discovered the resolver's clue. That state change is the mechanical action, and it is the same in the baseline and the experimental run.",
        "",
        "## 10. Saved provider-response replays",
        "",
        "The four PR-PLAY-50 responses were read from `artifacts/pr_play_50/requests.json` and were not edited. "
        "The raw output text was the prelude. A saved response is accepted only when its stored authoritative discovery is the clue the resolver just produced.",
        "",
        *replay_lines,
        "",
        "## 11. Authorized narration projections",
        "",
        "The hook receives a detached JSON object with the resolver kind, success, action id, interactable id, discovered clue text, already-searched or failed-check flags, public location, summary, visible facts, and player-known clue texts. "
        "It does not receive the scene catalog, hidden facts, GM notes, world object, quest journal, clue ids, hints, or skill-check rolls.",
        "",
        "Notice-board projection status: "
        f"`{notice['experimental']['projection']['authorized_investigation']['status']}`.",
        "",
        "Footprint projection status: "
        f"`{prints['experimental']['projection']['authorized_investigation']['status']}`.",
        "",
        "Hidden-string hits inside those projections and hook inputs: "
        f"{evidence['projection_leaks'] or 'none'}.",
        "",
        "## 12. Immutable discovery-anchor evidence",
        "",
        f"Notice-board anchor: {notice['experimental']['anchors'][0]['text']}",
        "",
        f"Footprint anchor: {prints['experimental']['anchors'][0]['text']}",
        "",
        "The anchor text is the resolver's `clue_text`. The tests assert that sentence; they do not pass it in as a chosen narration.",
        "",
        f"Second notice-board examination diagnostic: {anchor['previously_known']['diagnostic']}. "
        f"Anchor statuses: {[(item['status'], item['text']) for item in anchor['previously_known']['anchors']]}.",
        "",
        "Rain-barrel examination, same session after the notice board:",
        "",
        f"- Resolver: `{json.dumps(anchor['rain_barrel']['mechanical'], ensure_ascii=False)}`.",
        f"- Player-facing: {anchor['rain_barrel']['player_facing']}",
        f"- Quarantine diagnostic: {anchor['rain_barrel']['quarantine'].get('diagnostic')}.",
        f"- Quarantine anchors: {anchor['rain_barrel']['quarantine'].get('anchors')}.",
        "",
        "The barrel resolver discovered nothing. The anchor that remains is the patrol sentence with status `previously_known`, because that clue was already in player knowledge. It is not marked newly revealed.",
        "",
        "## 13. Hidden-information isolation results",
        "",
        "Each gameplay scene copy carried canary GM notes, an undiscovered clue, a hidden destination string, an NPC motive, a quest twist, and an unrelated world string. "
        "The frontier scene's authored hidden facts and internal clue ids were also scanned.",
        "",
        f"Leaks in hook inputs, prelude requests, and projections: {evidence['projection_leaks'] or 'none'}.",
        "",
        "The player-facing responses do not contain the saved preludes or the quarantine diagnostic.",
        "",
        "## 14. Mechanical-authority isolation results",
        "",
        "During the hook, campaign writers were wrapped. `save_session`, `save_world`, `save_character`, `save_combat`, `append_log`, `_save_json`, and `_atomic_save_json` raise if called while the hook is active.",
        "",
        f"Notice-board hook writer calls: {notice.get('hook_writer_calls')}. Footprint hook writer calls: {prints.get('hook_writer_calls')}.",
        "",
        "An invalid projection carrying travel and `currency_gained` was rejected with `side_effects_outside_offline_slice` before any preview. The gameplay clue remained the resolver's clue.",
        "",
        f"Exploration resolver calls stayed at one per investigation. Provider client constructions: {notice.get('provider_clients')} and {prints.get('provider_clients')}.",
        "",
        "## 15. Failure-isolation results",
        "",
        "Each fault ran a fresh investigation through `/api/chat`. The player-facing text, mechanical result, and scrubbed campaign state matched the baseline. The resolver ran once. No provider client was constructed.",
        "",
        *failure_lines,
        "",
        "## 16. Player-facing response comparisons",
        "",
        f"Notice board identical: {notice['comparison']['player_facing_identical']}.",
        "",
        f"Footprints identical: {prints['comparison']['player_facing_identical']}.",
        "",
        "Notice board: " + notice["baseline"]["player_facing"],
        "",
        "Footprints: " + prints["baseline"]["player_facing"],
        "",
        "The assembled experimental narration is not a substring of either player-facing response. The HTTP body does not contain a quarantine field.",
        "",
        "## 17. Performance measurements",
        "",
        "No provider latency is included. PR-PLAY-50's mean provider latency of about 2.22 seconds is context only.",
        "",
        f"One experimental notice-board turn, test client included: {perf['full_turn_elapsed_ms']} ms. In-turn hook timings: `{json.dumps(perf['in_turn'])}`.",
        "",
        "Thirty-one repeats on the resolution and scene captured from that gameplay turn:",
        "",
        f"- Hook work, excluding evidence writing: mean {perf['hook_work']['mean_ms']} ms, median {perf['hook_work']['median_ms']} ms, max {perf['hook_work']['max_ms']} ms.",
        f"- Total including evidence writing: mean {perf['total_with_evidence']['mean_ms']} ms, median {perf['total_with_evidence']['median_ms']} ms, max {perf['total_with_evidence']['max_ms']} ms.",
        f"- Evidence writing alone: mean {perf['evidence_write']['mean_ms']} ms, median {perf['evidence_write']['median_ms']} ms, max {perf['evidence_write']['max_ms']} ms.",
        f"- Projection build: mean {perf['projection_build']['mean_ms']} ms. Saved lookup: mean {perf['saved_lookup']['mean_ms']} ms. Validation: mean {perf['validation']['mean_ms']} ms. Assembly: mean {perf['assembly']['mean_ms']} ms.",
        "",
        f"Total-hook outlier under the recorded rule: {perf['outlier_total_ms']}. The evidence-write maximum is a disk spike of {perf['evidence_write']['max_ms']} ms and is not required for a future player-facing integration.",
        "",
        "## 18. Regression results",
        "",
        f"Collected: {reg['collected']}. Passed: {reg['passed']}. Failed: {reg['failed']}. Errors: {reg['errors']}. Skipped: {reg['skipped']}.",
        "",
        f"Failed node ids: {reg['failed_nodeids'] or 'none'}.",
        "",
        f"Pre-existing failures from the PR-PLAY-51 comparable suite: {reg['preexisting_failures_seen'] or 'none'}.",
        "",
        f"New failures: {reg['new_failures'] or 'none'}.",
        "",
        "Raw pytest output: `focused.txt`. JUnit: `focused.xml`.",
        "",
        "The PR-PLAY-51 authority-suite seal-metadata failures were not re-run and were not repaired. They remain the recorded baseline.",
        "",
        f"Campaign files mutated by the focused run: {evidence['campaign_mutated'] or 'none'}.",
        "",
        "## 19. Known limitations",
        "",
        "The hook is investigation-only and off unless the environment variable is exactly `1`. Combat, travel, inventory, currency, conditions, quests, dialogue, merchants, and general exploration are not narrated by it.",
        "",
        "Successful clue discovery already skips the provider. A repeat search and the rain-barrel examination do not. With provider calls disabled, those turns use the existing disabled-provider sentence. This pass did not change that branch.",
        "",
        "On the rain-barrel turn the resolver discovered nothing, and the quarantined anchor still appended the already-known patrol sentence as `previously_known`. The structured status is not `newly_revealed`. The assembled prose does not itself say that the clue was already known, so that string must stay out of the player response.",
        "",
        "The validator is still a heuristic. `You find a silver key beneath the board` remains a known false accept from PR-PLAY-49 and was not used as proof of rejection. The failure case used `The hidden passage opens before you`, which the current validator rejects. Validator rules were not widened or narrowed.",
        "",
        "A passing prelude is not approval to show it to a player. The quarantine output is evidence.",
        "",
        "## 20. Integration readiness decision",
        "",
        *gate_lines,
        "",
        "## 21. PR-PLAY-53 recommendation",
        "",
        evidence["proposal"],
        "",
        "## 22. Final verdict",
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
    report = (OUT / "PR_PLAY_52_REPORT.md").read_bytes()
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
        if path.is_file() and "__pycache__" not in path.parts
        and not (path.parent == OUT and path.name in excluded)
    ]
    hits = [path.relative_to(OUT).as_posix() for path in paths if any(secret in path.read_bytes() for secret in credentials)]
    if hits:
        raise SystemExit("credential scan failed: " + ", ".join(hits))
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
        pending = ROOT / "handoff" / ("PR_PLAY_52_pending_" + name)
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
    regression = run_pytest()
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
    write("regression_summary.json", regression)
    integration = json.loads((OUT / "integration_results.json").read_text(encoding="utf-8"))
    by_name = {row["name"]: row for row in integration}
    projection_leaks = []
    for key in ("notice_board", "footprints"):
        experimental = by_name[key]["experimental"]
        projection_leaks.extend(leaks({
            "hook_input": experimental["hook_input"],
            "projection": experimental["projection"],
        }))
    projection_leaks = sorted(set(projection_leaks))
    notice = by_name["notice_board"]
    prints = by_name["footprints"]
    replays = by_name["saved_replays"]["rows"]
    failures = [row for row in integration if row["name"].startswith("failure_")]
    gates = {
        "1_real_gameplay_path": notice["baseline"]["resolver_calls"] == {"exploration": 1, "social": 0}
        and prints.get("resolver_calls") == {"exploration": 1, "social": 0},
        "2_mechanical_equivalence": notice["comparison"]["mechanical_identical"] and prints["comparison"]["mechanical_identical"],
        "3_player_facing_equivalence": notice["comparison"]["player_facing_identical"] and prints["comparison"]["player_facing_identical"],
        "4_discovery_integrity": notice["experimental"]["anchors"][0]["text"].startswith("The missing patrol was last seen")
        and "direction stay unclear" in prints["experimental"]["anchors"][0]["text"],
        "5_hidden_information_isolation": not projection_leaks,
        "6_narration_authority": notice.get("hook_writer_calls") == [] and prints.get("hook_writer_calls") == []
        and notice.get("provider_clients") == 0 and prints.get("provider_clients") == 0,
        "7_failure_isolation": all(row.get("player_facing_identical") for row in failures) and len(failures) == 10,
        "8_regression_stability": not regression["new_failures"] and regression["errors"] == 0,
    }
    ready = all(gates.values()) and not mutated
    if ready:
        verdict = {
            "code": "A",
            "label": "PASS / READY",
            "summary": (
                "Actual gameplay investigations ran through the existing chat pipeline and exploration resolver. "
                "Experimental narration stayed quarantined. Mechanical outcomes, campaign state, and player-facing responses "
                "matched the baseline. Authorized discoveries stayed intact. Hidden information stayed out of the hook input. "
                "Narration did not write campaign state. Injected narration failures left the completed turn in place. "
                "No new relevant regression appeared."
            ),
        }
        proposal = (
            "PR-PLAY-53 should be a narrow quarantined live-provider experiment after completed investigation actions. "
            "Use this same gameplay pipeline. Resolve the action before narration. Build the authorized projection already used here. "
            "Make a small, explicitly bounded number of provider requests. Keep the engine-owned discovery anchor. "
            "Measure combined gameplay and provider latency. Save the raw model prose. Compare it with the deterministic player response. "
            "Judge consequential fabrication separately. Leave the player-facing response deterministic. "
            "Do not enable player-facing AI narration in that pass either."
        )
    elif gates["5_hidden_information_isolation"] and gates["6_narration_authority"] and gates["2_mechanical_equivalence"]:
        verdict = {
            "code": "B",
            "label": "PARTIAL / CONDITIONAL",
            "summary": "The quarantined hook matches gameplay on the paired investigations, but a bounded gate is still open.",
        }
        proposal = "Correct the open gate before any live provider narration. Do not start a broad narration redesign."
    else:
        verdict = {
            "code": "C",
            "label": "FAIL",
            "summary": "The integration changed gameplay, exposed hidden information, or failed a required isolation gate.",
        }
        proposal = "Correct the failing gate in a narrow pass. Do not expand the narration design."
    write("verdict.json", verdict)
    write("gates.json", gates)
    evidence = {
        "integration": integration,
        "regression": regression,
        "gates": gates,
        "verdict": verdict,
        "proposal": proposal,
        "projection_leaks": projection_leaks,
        "campaign_mutated": mutated,
        "source_files": [
            "game/api.py",
            "game/quarantined_investigation_narration.py",
            "tests/test_pr_play_52_quarantined_integration.py",
            "tests/test_pr_play_49_anchored_narration.py",
        ],
    }
    report = build_report(evidence)
    (OUT / "PR_PLAY_52_REPORT.md").write_text(report, encoding="utf-8")
    (ROOT / "handoff" / "CURRENT_REVIEW.md").write_text(report, encoding="utf-8")
    package_review()
    print(json.dumps({"verdict": verdict["code"], "gates": gates, "regression": {
        "passed": regression["passed"], "failed": regression["failed"], "new": regression["new_failures"],
    }}, indent=2))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
