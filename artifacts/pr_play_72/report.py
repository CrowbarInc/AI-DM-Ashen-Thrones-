"""Build factual PR72 reports from retained machine evidence; no gameplay imports."""
import hashlib
import json
from pathlib import Path
import statistics
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REPORT = ROOT / "development/campaigns/product_realization/pr_play_72"


def read(name, default=None):
    p = OUT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def junit(name):
    p = OUT / name
    if not p.exists(): return {"status": "not completed"}
    cases = list(ET.parse(p).getroot().iter("testcase"))
    failed = [c for c in cases if c.find("failure") is not None or c.find("error") is not None]
    return dict(cases=len(cases), passed=len(cases)-len(failed), failed=len(failed), failures=[c.get("classname", "") + "::" + c.get("name", "") for c in failed])


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    baseline = read("baseline.json"); isolation = read("final_isolation_result.json", read("isolation_result.json"))
    protected = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() if (ROOT/p).is_file() else None for p in baseline["protected"]}
    changed = [p for p,h in baseline["protected"].items() if protected[p] != h]
    integrity = dict(entries=len(protected), preserved=len(protected)-len(changed), changed=changed,
                     session_log=protected["data/session_log.jsonl"], hashes=protected,
                     historical_original_recovered=False)
    (OUT / "protected_integrity.json").write_text(json.dumps(integrity, indent=2))
    frozen = read("final_source.json")
    freeze_ok = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p,h in frozen.items()}
    (OUT / "freeze_integrity.json").write_text(json.dumps(freeze_ok, indent=2))
    http = read("http_summary.json", {})
    holdout = read("holdout_summary.json", {})
    regressions = read("regression_results.json", {})
    development = junit("repaired_development.xml")
    supplemental = junit("supplemental_final.xml")
    post_regression = junit("post_repair_regression.xml")
    output_isolation = junit("report_output_isolation.xml")
    publication = junit("final_publication.xml")
    social_publication = junit("social_disclosure_final.xml")
    browser = read("browser_results.json")
    traces = read("http_traces.json", [])
    durations = [r["http_ms"] for r in traces]
    natural = [r["http_ms"] for r in traces if r["request"]["path"] == "/api/chat"]
    structured = [r["http_ms"] for r in traces if r["request"]["path"] == "/api/action"]
    leakage = []
    for r in traces:
        raw = r["serialized_body"]
        forbidden = [s for s in ('SENTINEL_PR72_PRIVATE', '"gm_notes"', '"hidden_facts"', '"proposed_record"', '"world_state"') if s in raw]
        if forbidden: leakage.append(dict(request=r["request"], matches=forbidden))
    (OUT / "complete_payload_leakage_scan.json").write_text(json.dumps(dict(responses=len(traces), violations=leakage), indent=2))
    def stats(values):
        return dict(mean=statistics.mean(values), median=statistics.median(values), maximum=max(values)) if values else None
    stages = {}
    for name in ("interpretation_ms", "resolver_ms", "atomic_write_ms", "publication_ms"):
        values = [sum(r.get("stages", {}).get(name, [])) for r in traces if r.get("stages", {}).get(name)]
        stages[name] = stats(values)
    metrics = dict(verdict="B — PARTIAL / DETERMINISTIC INITIATIVE WITH VERIFICATION LIMITATIONS", head=baseline["head"], branch=baseline["branch"],
                   protected=integrity, isolation=isolation, development=development, holdout=holdout, regression=regressions,
                   http=http, browser=browser, provider_requests=0, provider_tokens=0, retries=0, timeouts=0,
                   supplemental=supplemental,
                   post_repair_regression=post_regression, report_output_isolation=output_isolation,
                   final_publication=publication,
                   final_social_disclosure=social_publication,
                   cold_resume=read("cold_resume_summary.json", {}),
                   mandatory_disclosure=read("mandatory_disclosure_scan.json", {}),
                   same_action_latency=read("latency_comparison.json", {}),
                   regression_assessment=read("regression_assessment.json", {}),
                   latency_ms=stats(durations), natural_chat_ms=stats(natural), structured_choice_ms=stats(structured), stages_ms=stages,
                   latency_limits="Natural/structured lifecycle aggregates are different actions; use latency_comparison.json for the same investigation if present. Function durations overlap total request time. No browser rendering or exact interstage intervals measured.",
                   complete_payload_exposures=len(leakage), source_freeze_preserved=all(freeze_ok.values()),
                   next_step="PR-PLAY-72 verification closure: complete both normal typed-browser campaign lifecycles against this frozen implementation.")
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
    def pretty(value): return "```json\n" + json.dumps(value, indent=2) + "\n```\n"
    architecture = """```text
PLAYER TEXT (static/app.js → POST /api/chat)
  → game.api._chat_turn / communication mode
  → conversational_orchestration.deterministic_conversational_decision
  → player_initiative.decide (explicit gate + identity binding; read-only)
  → existing ConversationalDecision / operation record
  → player_interpretation_bridge.normalized_action_from_interpretation
  → contextual target / scene / prerequisite validation
  → existing exploration / social resolver, authored_consequences.resolve
  → existing world updates + runtime_commit_scope / storage persistence
  → mandatory disclosure / deterministic fallback
  → optional existing validated AI presentation
  → player_http_projection allowlist → frontend
```
Information, clarification and refusals use the existing nonmutating conversation response. Their transcript is appended; PR72 deliberately avoids updating session conversation context or calling expression generation. All four gameplay documents remain equal before/after those requests. Publication selection in the existing lifecycle happens after authority saves and before log append; the endpoint commit scope rolls back failures. No second store, resolver, knowledge database, provider dependency or persistent clarification schema was added.
"""
    reports = {
      "01_EXECUTIVE_SUMMARY": metrics["verdict"] + "\n\nThe feature is deterministic and default off. Browser verification is blocked; live AI interpretation is not claimed. Read every machine result as scoped evidence, not a full-suite or external-validation claim.\n\n" + pretty(dict(development=development, holdout=holdout, http=http)),
      "02_REPOSITORY_BASELINE": pretty({k:v for k,v in baseline.items() if k != "protected"}) + "\nThe baseline had 716 status entries. Existing user changes were retained; no commit, push, Git checkout, reset or historical-log restoration was performed. See baseline_status.txt and baseline.json for exact paths and 150 protected data hashes. The implementation diff includes inherited changes and is labelled accordingly.",
      "03_TEST_DATA_ISOLATION": pretty(isolation) + "\nStorage is configured before game import through tests/helpers/storage_isolation.py and tests/conftest.py. Existing ASHEN_DATA_DIR and ASHEN_PROVIDER_USAGE_PATH select disposable storage. A Python audit guard rejects writes/removes/renames to repository data, including explicit stale constants. This is test tooling, not a replacement persistence system. Snapshot paths derive from the configured root; fixtures may select further temporary roots. HTTP and holdout roots are under artifacts/pr_play_72. Browser host root was isolated before attachment.\n\nConservative line inventories in test_write_inventory.json cover campaigns, sessions, chat/log, saves, provider logs and import/lifespan risk. This lexical inventory identifies possible writers rather than proving a complete static call graph. No uncontrolled native writers or unguarded provider experiments were used.\n\nOriginal expected session-log SHA256: b4706f3bb214861c34f7b9304ba39f4e51b72a7d8ef9e093cc83256311a33b13. Current bytes were copied before tests. Read-only repository file/archive searches found no exact match; no recovery is claimed.\n\n" + pretty({k:v for k,v in integrity.items() if k != "hashes"}),
      "04_INTENT_ARCHITECTURE": architecture,
      "05_INTENT_CONTRACT": "The existing frozen ConversationalDecision carries category, intention, operation, target, confidence, ambiguity and missing information. Its existing operation record crosses the bridge. It is internal evidence and never returned as raw player metadata. No separate intent schema was added.\n\nINSPECT and ASK reuse current visible-target mapping. CUSTOM extends the existing bridge for finite authored choices: the bridge recomputes a proposal from original player text and the current scene, checks the same target, enrollment and prerequisites, then passes only the server definition's id/type/label/prompt. Effects still come exclusively from authored_consequences.resolve. A narrow API exception bypasses NPC addressing only after this bridge accepts an authored choice. Provider proposals cannot grant this exception by naming an invented action.\n\nThe interpreter never saves, applies world updates, adds inventory or discovers clues.",
      "06_SUPPORTED_INTENTIONS": "Supported scope: inspection of public current-scene interactables by names/aliases; natural questions from current journal knowledge and committed branch disclosures; interaction proposals to current known NPCs; finite authored survey/report/record choices; existing movement outside this leaf. The mechanism recognizes verbs, grammatical wrappers and public target aliases, with small lexical equivalences for tracks/prints, ground/mud and notices. It is not an exact six-sentence table or unrestricted NLU.\n\nNPC interaction still crosses the existing addressee gate and may require clarification even when the initial alias matcher proposes an NPC. Recognition is not authoritative success. See actual resolution logs in HTTP traces; no interaction success is inferred from classification alone.",
      "07_BRANCH_CONTEXT": "Independent normal campaigns use patrol_survey/patrol_survey_recorded or patrol_report/patrol_guards_warned. Existing branch exclusivity and conditions remain authoritative. Information responses append only consequence disclosures whose committed effects are true; they do not infer a branch from the question's wording. Existing journal/clue knowledge supplies discoveries. No guard search, destination or new encounter is created.\n\n" + pretty(http.get("campaigns", [])),
      "08_AMBIGUITY_HANDLING": "Ambiguous pronouns, multiple public aliases, unknown targets, negated attempts, and qualified/multiple action requests produce concise clarification without invoking a resolver. No persistent PR72 clarification state is introduced. Existing clarification handling remains outside this opt-in leaf. Tests compare session, world, character and combat for exact equality on PR72 non-executing turns; transcript writes are expected. Unknown or hidden target names are not echoed as established entities.",
      "09_UNSUPPORTED_INTENTIONS": "Unsupported pursuit explains that no onward route has been established and offers accessible evidence/known routes. NPC deployment requests decline command authority without inventing an NPC decision. Impossible abilities/routes and hidden-information requests receive distinct explanations. Inaccessible evidence requires returning through a known route. Unavailable authored choices give a generic current-choice limitation without leaking their hidden conditions. Unknown and ambiguous targets ask for clarification. No refusal grants inventory, travel, discoveries or flags.",
      "10_INFORMATION_REQUESTS": "Questions use build_player_journal on a detached session copy plus the existing authored disclosures for actually committed effects. Only journal discovered_clues and known_facts are published; raw world flags, private NPC topics and hidden templates are excluded. Questions about guard activity state that no further activity is established. They never turn a player's presupposition into a search-party fact. The original player text and answer remain in the existing transcript. No live provider or optional expression request is needed.",
      "11_AUTHORITATIVE_RESOLUTION": architecture + "\nThe bridge proposes only existing targets. The resolver checks authoritative current conditions and supplies actual updates. CUSTOM choices use their server-authored one-time excludes_flags conditions. Repeated attempts cannot repeat committed effects. Information/refusal/clarification leaves the four gameplay documents unchanged; transcript persistence is intentional. Runtime rollback and Windows atomic replacement code are unchanged.",
      "12_PLAYER_SAFE_PUBLICATION": "The existing player_http_projection allowlists remain in force. Unknown fields are dropped. Public responses contain narration and permitted state, never internal ConversationalDecision, proposed records, raw resolution metadata, hidden flags or provider traces. Hidden sentinels were added only to disposable holdout scene metadata. Read complete_payload_leakage_scan.json and frozen holdout constraints for actual serialized-response checks.\n\nOne social discovery omission was observed after the grounding repair: resolution committed the existing route-change topic, while the offline presentation returned unrelated opening prose. The trace and failed complete-response scan remain in mandatory_disclosure_before_repair.json and http_before_social_disclosure_* evidence. The enrolled publication seam now requires success, target_resolved, and exact membership of the current topic text in current discovered_clues, then uses the existing social fact formatter. It never reads an undiscovered topic. Thus optional narration cannot suppress the current social fact. Final checks and the complete-payload scan report the repaired result separately; do not erase the one earlier omission from cycle totals.\n\n" + pretty(dict(publication_and_lifecycle=publication, corrected_social_assertion=social_publication, final_disclosure_scan=read("mandatory_disclosure_scan.json", {}))) + "\nThe publication lane was 56/57: its remaining assertion was case-sensitive while the existing formatter lowercases the initial article inside a quotation. The case-insensitive full-sentence check passed in a separate fresh process, 1/1, and all five final HTTP discovery disclosures are present. No product change followed that assertion correction. No published AI prose is claimed.",
      "13_PERSISTENCE_AND_RESUME": "Normal /api/snapshots and /api/snapshots/load save and restore both branch identities, world, journal, transcript and continuations. A newly created campaign separates save/resume checks; HTTP also cross-loads two campaign slots. A separate fresh Python process subsequently resumed both final HTTP save slots and passed six natural read-only/ambiguous/unsupported continuations with exact gameplay-document equality. Existing last_saved_at and narration resume markers are expected storage metadata changes. Byte-rollback and transient/permanent Windows rename checks passed in the clean 39-case lifecycle lane. No alternate session state was introduced.\n\n" + pretty(read("cold_resume_summary.json", {})),
      "14_GENERALIZATION": "The developer-authored preimplementation holdout includes 15 supported intentions, 10 paraphrases, 10 branch cases, 10 unsupported/ambiguous cases, five information requests, five projection cases and five resume cases. Cases vary verbs, questions, first-person intentions, short imperatives and scene/branch context. All fixed inputs, starting-state recipes, expectations, publication constraints and hashes are retained. This is bounded English phrase recognition; unseen arbitrary syntax and arbitrary world actions remain outside scope.\n\n" + pretty(holdout),
      "15_DEVELOPMENT_TESTS": pretty(dict(repaired_combined=development, corrected_final_supplemental=supplemental, owner_and_compatibility=post_regression, output_isolation=output_isolation)) + "\nThe repaired combined development run was 59/60: the remaining assertion read the NPC id from the wrong result field. It was corrected to existing state_changes.npc_id while that process was already running, then verified in the separate final supplemental run, 4/4. All six separate unknown-subject/exact-name repair cases passed in the repaired combined run. These are separate runs, not a claim that a final combined 60/60 run occurred.\n\nEarlier failed attempts remain intact: a false leakage check against initiative_bonus, fixture/live-call-guard lifetime errors, legitimate snapshot saved-at metadata, one MemoryError during snapshot restore, and report-addressing interception. Original fault tests incorrectly expected an exception rather than the sanitized HTTP 500; corrected tests check exact rollback bytes. See retained TXT/XML and post_holdout_changes.json.",
      "16_FROZEN_HOLDOUT": pretty(holdout) + "\nManifest SHA256 was checked immediately before the one-shot execution. holdout_started.json is opened exclusively, preventing accidental rerun. Cases and results remain unchanged. Seven failures require success=True for correctly already-searched targets; H38 incorrectly classified an ambiguous request as a safe read-only answer. No tuning against these failures was performed. Separate development checks outside the holdout subsequently repaired unknown choice subjects and exact-name NPC grounding; therefore this holdout is evidence for the pre-repair product, not a fresh final-source holdout. The pre-repair source and freeze are retained. No replacement holdout was run and B remains the verdict. This is developer-authored, not external independent validation.",
      "17_FAILURE_INJECTION": "tests/test_pr_play_72_failures.py covers malformed records, unsupported operations, invented targets, stale scene targets, stale branch follow-ups, missing provider access on read-only turns, invalid HTTP schemas, unknown publication fields, and append-log persistence faults with exact byte rollback. Repeated one-time choices, hidden targets, negated/multiple requests and cross-campaign restoration are in the initiative suite. Existing regression suites cover rejected optional narration and Windows replacement faults. Provider unavailable/timeout cases establish that the deterministic information path makes no call; they do not claim a real live provider timed out. No network timeout experiment or live provider interpretation is claimed.\n\n" + pretty(development),
      "18_REAL_HTTP_GAMEPLAY": "Real TCP requests use the normal application HTTP endpoints. Campaign state is created by New Campaign/Start, investigation, movement, choice and follow-up; no developer runtime-seeding API is used. Rich opening text is an offline deterministic fixture. Both branches submit original natural text, known-information queries, unsupported pursuit/deployment, clarification, save/load and resumed questions. Full before/after authority, actual committed log resolutions, complete player responses and timings are retained. Replayed interpretation is labelled separately; actual server-stage interpretation is in stages.\n\n" + pretty(http),
      "19_BROWSER_GAMEPLAY": pretty(browser) + "\nNo typed browser gameplay, screenshot, browser network trace or browser-visible response latency is claimed. The isolated host was prepared, attachment was attempted early, recovery was bounded, and UI automation stopped when Computer Use could not enforce its browser policy. Existing historical screenshots are not substituted for this cycle.",
      "20_PROVIDER_USAGE": "Live provider requests: 0. Live provider tokens: 0. Provider-assisted interpretations: 0. Shadow calls: 0. Accepted provider interpretations: 0. Published provider narration: 0. Live provider retries: 0. The demonstrated interpretation and presentation are deterministic; opening fixture text is not live AI. ASHEN_DISABLE_PROVIDER_CALLS, ASHEN_DISABLE_LIVE_INTERPRETATION, expression disabling and pytest's live-client guard enforce the offline boundary. The six-request/12,000-token discretionary budget was not used.",
      "21_LATENCY": pretty(dict(http_ms=stats(durations), natural_chat_ms=stats(natural), structured_choice_ms=stats(structured), instrumented_function_ms=stages)) + "\nIndividual request timings are retained in http_traces.json. Lifecycle aggregates compare different actions and are not equivalent-action speed claims. Same-action comparison is separately labelled if available. Diagnostic middleware and evidence capture add overhead. Function timing sums are observations, not exact disjoint A–F intervals. Submission-to-interpretation offsets, exact persistence-to-publication gap, browser rendering and total browser-visible latency were not instrumented. No browser-visible number is inferred from HTTP time.",
      "22_REGRESSION_RESULTS": pretty(regressions) + "\nCombined focused: 1064 passed / 21 failed. The prior 20 failed identities remain, with one additional corpus timing assertion. That timing assertion passed in the fresh post-repair process; it is not labelled historical. Boundary 101/6 and broader 0/9 match prior failed-node sets. Clean lifecycle/persistence: 39/39. Additional post-repair owner/compatibility lane: 42 passed / 12 failed. The same 12 failures reproduce with the preserved pre-repair owner loaded in memory (37 passed / 12 failed across its 49 cases); this is a targeted comparison, not a full entry-tree replay. Most expect internal resolution data omitted by the existing player projection. See regression_assessment.json for both messages and comparison provenance. No confirmed new product regression remains in these executed lanes; no full-suite or official ATGB claim.\n\nEarly combined regression regenerated some legacy analysis report outputs. Later collection hooks redirect their OUT paths, and the write guard protects prior artifact roots. Entry hashes were recorded for production-like data, not every earlier analysis report: preservation of those regenerated reports is not claimed. See final_isolation_result.json and historical_evidence_guard_integrity.json.",
      "23_LIMITATIONS_AND_OPEN_RISKS": "Verdict B. Browser typed-input verification is blocked. Deterministic English recognition is deliberately narrow; live provider interpretation/narration is unverified. Some NPC aliases remain ambiguous at the canonical addressee gate; inspect the actual HTTP outcome rather than initial proposed mapping. Exact interstage and browser-visible timing is incomplete. Historical original session-log bytes were not recovered. Initial development runs included a transient MemoryError and fixture/harness defects; retained logs disclose them. Combined-suite cache failures must be assessed independently from clean-process passes. The Python audit guard covers Python persistence operations in these processes; it is not an OS sandbox for arbitrary native subprocesses. No such data-writing subprocess was introduced.",
      "24_NEXT_SESSION": metrics["next_step"] + "\n\nKeep the implementation and holdout frozen. Do not rerun or tune the frozen holdout. Read final_development.xml, holdout_summary.json, http_summary.json, regression_results.json, protected_integrity.json and browser_results.json before drawing conclusions. Preserve the copied current log and recovery-search evidence. Do not implement PR-PLAY-73, commit or push automatically.",
    }
    assert len(reports) == 24
    for name, body in reports.items(): (REPORT / (name + ".md")).write_text("# PR-PLAY-72 — " + name.replace("_", " ") + "\n\n" + body + "\n", encoding="utf-8")
    print(metrics["verdict"], "reports", len(reports), "protected", integrity["preserved"], "/", integrity["entries"])


if __name__ == "__main__": main()
