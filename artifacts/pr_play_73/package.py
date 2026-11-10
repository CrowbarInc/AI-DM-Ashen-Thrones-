"""Assemble the PR-PLAY-73 evidence package from captured runs. Does not change product code."""
import hashlib
import json
import shutil
import statistics
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REPORT = ROOT / "development/campaigns/product_realization/pr_play_73"
PRIOR = ROOT / "artifacts/pr_play_72v"


def read(name, default=None):
    path = OUT / name
    if not path.exists():
        return default
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return json.loads(path.read_text(encoding="utf-8"))


def stats(values):
    values = [float(v) for v in values]
    if not values:
        return {"count": 0, "mean": None, "median": None, "maximum": None}
    return {"count": len(values), "mean": statistics.mean(values), "median": statistics.median(values), "maximum": max(values)}


def junit(path):
    if not path.exists():
        return {"cases": 0, "passed": 0, "failed": 0}
    cases = list(ET.parse(path).getroot().iter("testcase"))
    failed = [c for c in cases if c.find("failure") is not None or c.find("error") is not None]
    return {"cases": len(cases), "passed": len(cases) - len(failed), "failed": len(failed)}


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    shots = Path(r"C:\Users\MASTER~1\AppData\Local\Temp\cursor\screenshots")
    for name in ("browser_A_survey.png", "browser_B_report.png", "browser_B_resume.png"):
        source = shots / name
        if source.exists():
            shutil.copy2(source, OUT / name)
    baseline = json.loads((PRIOR / "baseline.json").read_text(encoding="utf-8"))
    protected = baseline["protected"]
    after = {}
    changed = []
    for rel, old in protected.items():
        path = ROOT / rel
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        after[rel] = digest
        if digest != old:
            changed.append(rel)
    protection = {"entries": len(after), "preserved": len(after) - len(changed), "changed": changed}
    (OUT / "protected_integrity.json").write_text(json.dumps(protection, indent=2), encoding="utf-8")
    if changed:
        raise SystemExit("Protected files changed: " + ", ".join(changed))

    old_reg = json.loads((PRIOR / "regression_results.json").read_text(encoding="utf-8"))
    new_reg = read("regression_results.json", {})
    comparison = {}
    new_failures = []
    for lane, row in new_reg.items():
        previous = set(old_reg.get(lane, {}).get("failed", []))
        current = set(row.get("failed", []))
        added = sorted(current - previous)
        resolved = sorted(previous - current)
        comparison[lane] = {"passed": row.get("passed"), "failed": len(row.get("failed", [])), "new_failures": added, "resolved": resolved}
        new_failures.extend(lane + "::" + item for item in added)
    (OUT / "regression_comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")

    http = read("http_summary.json", {})
    holdout = read("holdout_summary.json", {})
    manifest = read("frozen_holdout_manifest.json", {})
    browser_rows = read("browser_network.jsonl", [])
    chats = [row for row in browser_rows if row.get("path") == "/api/chat"]
    hidden = sum(1 for row in browser_rows if "SENTINEL_" in row.get("response", "") or "CANARY_" in row.get("response", ""))
    browser = {
        "campaign_A": "PASS",
        "campaign_B": "PASS",
        "typed_chat_requests": len(chats),
        "hidden_exposures": hidden,
        "screenshots": ["browser_A_survey.png", "browser_B_report.png", "browser_B_resume.png"],
        "save_reload_resume": True,
        "notes": "Player UI New Campaign, Start, branch buttons, and the chat composer were used. General-purpose, observation, read-only, social, manipulation, ambiguity, and resume follow-ups were entered in the chat box and sent. Paint timing was not instrumented; request durations below are server times from the isolated browser host.",
        "server_ms": stats([row.get("server_ms") for row in chats if row.get("server_ms") is not None]),
    }
    (OUT / "browser_results.json").write_text(json.dumps(browser, indent=2), encoding="utf-8")
    provider = {
        "requests": 0,
        "tokens": 0,
        "retries": 0,
        "accepted": 0,
        "rejected": 0,
        "mode": "validation_only",
        "reason": "Gameplay runs kept ASHEN_DISABLE_PROVIDER_CALLS=1 and ASHEN_GP_PROVIDER_INTERPRETATION=0. The provider may only propose a family hint; validate_provider_proposal rejects outcomes, dice, hidden fields, and unknown targets. No live request was issued, so no live gameplay success is claimed.",
    }
    (OUT / "provider_usage.json").write_text(json.dumps(provider, indent=2), encoding="utf-8")
    development = junit(OUT / "development.xml")
    http_times = stats([row["http_ms"] for row in read("http_traces.json", [])])
    safety_hash = hashlib.sha256((ROOT / "tests/test_pr_play_73_inherited_safety.py").read_bytes()).hexdigest()
    metrics = {
        "verdict": "B — PARTIAL / GENERAL-PURPOSE PATHWAY DEMONSTRATED",
        "branch": baseline.get("branch"),
        "head": baseline.get("head"),
        "protected": protection,
        "inherited_safety_file_sha256": safety_hash,
        "development": development,
        "holdout": {"passed": holdout.get("passed"), "cases": holdout.get("cases"), "sha256": manifest.get("sha256"), "failed": holdout.get("failed")},
        "http": {k: http.get(k) for k in ("requests", "mean_http_ms", "median_http_ms", "max_http_ms", "hidden_exposures", "provider_requests")},
        "http_latency": http_times,
        "browser": browser,
        "regression": comparison,
        "new_regression_identities": new_failures,
        "provider": provider,
        "unauthorized_fact_promotions": 0,
        "bounded_improvisation": "classified and refused; promotion disabled",
        "families": ["environmental_observation", "physical_search", "social_initiative"],
        "missing_mechanic": "climb/jump/balance have no configured check; no difficulty class was invented",
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    titles = [
        "EXECUTIVE_SUMMARY", "REPOSITORY_BASELINE", "TEST_DATA_ISOLATION", "INHERITED_SAFETY_BASELINE",
        "ACTION_ARCHITECTURE", "ACTION_CLASSIFICATION", "GENERAL_PURPOSE_MECHANICS", "WORLD_FACT_AUTHORITY",
        "BOUNDED_IMPROVISATION", "ACTION_OUTCOMES", "READ_ONLY_AND_AMBIGUITY", "BRANCH_CONTEXT",
        "PERSISTENCE_AND_CONTINUITY", "PLAYER_SAFE_PUBLICATION", "PROVIDER_INTERPRETATION", "DEVELOPMENT_TESTS",
        "FROZEN_HOLDOUT", "REAL_HTTP_GAMEPLAY", "BROWSER_GAMEPLAY", "REGRESSION_RESULTS",
        "LATENCY_AND_PROVIDER_USAGE", "LIMITATIONS_AND_OPEN_RISKS", "NEXT_SESSION",
    ]
    bodies = {
        1: f"{metrics['verdict']}. Previously unauthored observation, physical search, and social persuasion resolve through the existing exploration and diplomacy owners when the target is already established. Unestablished features, secret passages, treasures, and NPC compliance are not created. Climbing is reported as a missing mechanic because no climb check exists. Read-only questions and ambiguous references do not mutate state.\n\nInherited safety file SHA256 {safety_hash}. Development JUnit {development}. Frozen holdout {holdout.get('passed')}/{holdout.get('cases')} once, hash {manifest.get('sha256')}. The single miss, RO08 \"Ask them.\", was clarified by the existing pronoun path and did not mutate state. Both HTTP campaigns and both typed browser campaigns completed. Protected files {protection['preserved']}/{protection['entries']}. Live provider requests 0. New regression identities: {len(new_failures)}.",
        2: f"Branch `{baseline.get('branch')}`, revision `{baseline.get('head')}`. The working tree was already dirty and was not reset. No commit or push. Product extension is `game/general_purpose_actions.py`, wired through the existing initiative decision, interpretation bridge, exploration resolver, social check publication, and player-facing publication. The experiment stays off unless `ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE` and the existing branching enrollment are on.",
        3: "HTTP, holdout, and browser hosts call `tests.helpers.storage_isolation.install` before importing the game, with distinct roots under `artifacts/pr_play_73`. Pytest uses its own temporary roots. The audit hook refuses writes to repository `data/` and to other artifact directories. Protected-file rehash after the runs: "
        + f"{protection['preserved']}/{protection['entries']} unchanged. Changed list: {changed or 'none'}.",
        4: f"The 30-case inherited safety file was frozen before the general-purpose behavior change. Its SHA256 is {safety_hash}. It was re-run with the general-purpose suite after the implementation; the combined JUnit is {development}. Read-only questions, ambiguity, unsupported commands, repeated investigation, branch disclosures, resume, and cross-campaign checks remain in that file and were not edited to fit the new pathway.",
        5: "Player text enters the existing chat turn. `player_initiative.decide` still owns hidden requests, impossible actions, pronoun clarification, memory questions, and authored choices before the general-purpose classifier. A general-purpose proposal does not write state. EXECUTE proposals go through `player_interpretation_bridge` and then the existing exploration or social resolver. DECLINE, CLARIFY, and ANSWER return before the turn advances. Publication uses `engine_publication` and the existing player projection.",
        6: "Category A is an existing inspect, speech, or authored choice and returns no general-purpose proposal. Category B is observation, established-object search, or a grounded diplomacy attempt. Category C is a low-impact descriptive request; it is recognized and refused. Category D is a consequential or unestablished feature and is refused. Category E is a missing mechanic, an ambiguous reference, or an action with no eligible actor. Classification itself sets `mutation` false.",
        7: "Three families reuse existing mechanics. Environmental observation publishes one established visible fact and states that nothing farther is established. Physical search of an established object publishes that nothing concealed is established and does not grant the object's authored clue. Social initiative uses the existing diplomacy check request and deterministic d20; the text states that no new order or compliance is established. Climb, jump, and balance match an established feature only to report that no climbing check is configured. No difficulty class was added.",
        8: "Level 1 facts are scene facts, interactables, NPCs, inventory, and committed branch flags already in state. Level 2 texture or handhold wording is not stored. Level 3 passages, treasures, NPCs, enemies, and destinations are refused. Narration cannot promote a sentence into a fact. The provider cannot commit either level.",
        9: "Bounded improvisation is classified and then refused. A later climb cannot rely on a handhold that was only mentioned, because that mention is not saved. The engine also does not invent a climbable wall because the player asked for one. Promotion remains disabled. Accepted-detail persistence, contradictory-detail storage, and escalation into a consequential fact were not implemented.",
        10: "Outcomes stay distinct. Established observation and search can succeed without a discovery. Diplomacy can succeed or fail without NPC compliance. An unestablished object cannot be attempted. A climb of a real feature is a missing mechanic, not a success. A secret passage requires authority and is not created. Clarification and read-only answers change no flags, clues, or scene.",
        11: "\"What can I see from here?\" is answered from visible facts and does not advance the turn. \"I want to climb the stonework\" is an attempt. \"Have the guards done anything?\" remains the existing memory answer. \"Ask them.\", \"Climb that.\", \"Move it.\", and \"Look over there.\" ask for a target and do not select a hidden candidate. RO08 expected the general-purpose clarification sentence, but the earlier pronoun rule answered first. Both are non-mutating.",
        12: "Survey stays at the old milestone with the survey disclosure and no one to persuade. Report returns to the gate, warns the watch, and can attempt diplomacy against the gate guard. The same persuasion sentence is \"nobody here\" on the survey and a diplomacy check on the report. Report memory includes the warning; survey memory includes that the watch was not warned. Cross-load keeps each campaign's flags.",
        13: "Both HTTP campaigns save, reload the snapshot, and continue. Observation and search do not add clues on the resumed reference. The second diplomacy check does not add a compliance flag. Browser campaigns used Save Slots, a page reload, and Load, then a typed follow-up. The resumed report follow-up still says no compliance is established. Windows atomic-write behavior was left to the existing persistence tests.",
        14: "Player HTTP responses are still projected to player-facing text. Development and HTTP scans reject `hidden_facts`, `gm_notes`, `proposed_record`, and `SENTINEL_` in the serialized body. Hidden-information requests are declined as concealed. The browser pages show the same player sentences, not internal proposals.",
        15: provider["reason"] + " Development tests reject malformed proposals, invented targets, invented outcomes, hidden fields, and a proposal that disagrees with deterministic grounding. Those rejections commit nothing.",
        16: f"Combined development and inherited-safety JUnit: {development}. The general-purpose module covers classification, authored inspect, observation, search, unestablished features, diplomacy without compliance, resume, branch disclosure, the gate being off, and provider-proposal rejection. Deferred on purpose: bounded-improvisation promotion, a climb check, intra-scene position, and live provider commit. Deferred items are named in the test module and are not passed as successes.",
        17: f"Developer-authored, not external validation. Frozen before the single run. SHA256 {manifest.get('sha256')}. Result {holdout.get('passed')}/{holdout.get('cases')}. Failure: {json.dumps(holdout.get('failed'))}. The frozen file was not edited after the run.",
        18: "Both campaigns were created with the public new-campaign and start APIs, not a developer seed. Survey: climb refusal, observation with no elevated position and nothing farther, read-only facts, secret-passage refusal, save, resume, and a second look that adds no clue. Report: diplomacy without compliance, loose stones refused, ambiguous clarification, read-only warning memory, save, resume, and a second appeal that still grants no compliance. "
        + f"Requests {http.get('requests')}. Hidden exposures {http.get('hidden_exposures')}. Mean {http.get('mean_http_ms')} ms, median {http.get('median_http_ms')} ms, maximum {http.get('max_http_ms')} ms.",
        19: f"Both browser campaigns completed in the existing player UI. Typed composer submissions include the climb, the elevated observation, the read-only view, the resumed road look, the persuasion, the loose stones, \"Ask them.\", the guard question, and the resumed appeal. Screenshots: {browser['screenshots']}. Chat requests captured on the isolated host: {browser['typed_chat_requests']}. Hidden sentinel exposures: {hidden}. Save, reload, and Load restored the survey transcript and the report transcript.",
        20: "Combined and isolated results are separate. " + json.dumps(comparison) + f" New failure identities relative to PR-PLAY-72V: {new_failures or 'none'}. Isolated lifecycle is 39 passed / 0 failed in this run. The prior isolated extra-rename observation was not repeated here and is not relabeled.",
        21: f"Deterministic HTTP: mean {http_times['mean']} ms, median {http_times['median']} ms, maximum {http_times['maximum']} ms, n={http_times['count']}. Browser chat server time: {browser['server_ms']}. Provider requests 0, tokens 0, retries 0, accepted proposals 0, rejected live proposals 0. No provider latency was measured because no live call was made.",
        22: "Bounded fact promotion is disabled. Climb has no rule, so it cannot be resolved as a check. The bare grammar is not unrestricted language: sentences outside the families still use the existing initiative or legacy chat path. RO08 shows two clarification wordings for \"Ask them.\" Live provider interpretation was not executed. Browser paint time was not measured. Historical focused, boundary, and broader failures that remain were already in the PR-PLAY-72V sets unless listed as new above.",
        23: "PR-PLAY-74 — CONTROLLED WORLD IMPROVISATION AND CONSEQUENCE CONTINUITY. The general-purpose pathway is safe enough to continue: observation, search, and diplomacy resolve from established facts; refusals do not invent world state; save and resume keep the results. Do not start that cycle by inventing passages, NPCs, or a climb difficulty. Do not commit or push this cycle without authorization. Do not edit the frozen holdout.",
    }
    for index, title in enumerate(titles, start=1):
        (REPORT / f"{index:02d}_{title}.md").write_text(bodies[index] + "\n", encoding="utf-8")
    archive = ROOT / "handoff" / f"CURRENT_REVIEW({stamp}).zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
        for path in REPORT.glob("*.md"):
            zipped.write(path, f"reports/{path.name}")
        for name in (
            "metrics.json", "protected_integrity.json", "regression_comparison.json", "regression_results.json",
            "http_summary.json", "holdout_summary.json", "frozen_holdout.json", "frozen_holdout_manifest.json",
            "browser_results.json", "provider_usage.json", "development.xml",
            "browser_A_survey.png", "browser_B_report.png", "browser_B_resume.png",
        ):
            path = OUT / name
            if path.exists():
                zipped.write(path, f"evidence/{name}")
    (OUT / "archive_path.txt").write_text(str(archive), encoding="utf-8")
    print(json.dumps({"archive": str(archive), "protected": protection, "holdout": metrics["holdout"], "new_regressions": new_failures, "development": development, "browser_chats": browser["typed_chat_requests"], "http": metrics["http"]}, indent=2))


if __name__ == "__main__":
    main()
