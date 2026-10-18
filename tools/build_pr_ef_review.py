"""Generate PR-EF's evidence reports and established CURRENT_REVIEW handoff."""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import shutil
import statistics
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "artifacts/pr_ef_gm_authority"


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def write(name, value):
    (OUT / name).write_text(value.strip() + "\n", encoding="utf-8")


def cases(name):
    return {c.attrib["classname"] + "::" + c.attrib["name"]: {
        "status": "failed" if c.find("failure") is not None else "passed",
        "signature": c.find("failure").attrib.get("message", "") if c.find("failure") is not None else "",
    } for c in ET.parse(OUT / name).iter("testcase")}


def normalized(text):
    return re.sub(r"0x[0-9a-fA-F]+", "<address>", text)


def main():
    from tools.build_review_handoff import build_handoff

    baseline, final = cases("baseline_junit.xml"), cases("final_junit.xml")
    oldfail = {key for key, row in baseline.items() if row["status"] == "failed"}
    newfail = {key for key, row in final.items() if row["status"] == "failed"}
    regression = {
        "baseline_total": len(baseline), "baseline_passed": len(baseline) - len(oldfail),
        "final_total": len(final), "final_passed": len(final) - len(newfail),
        "inherited": sorted(oldfail & newfail), "resolved": sorted(oldfail - newfail),
        "new_regressions": sorted(newfail - oldfail),
        "changed_failure_signatures": sorted(key for key in oldfail & newfail if normalized(baseline[key]["signature"]) != normalized(final[key]["signature"])),
        "added_tests": sorted(set(final) - set(baseline)),
        "individual_results": {key: {"baseline": baseline.get(key), "final": final.get(key)} for key in sorted(set(baseline) | set(final))},
    }
    write("regression_comparison.json", json.dumps(regression, indent=2))
    replay, live1, live2, holdouts = [read(name) for name in [
        "final_recorded_http_ten_turns.json", "live_ten_turns.json", "live_final_ten_turns.json", "live_holdouts.json"]]
    bp, fp = read("baseline_profile.json"), read("final_profile.json")
    summary = []
    for name, p in [("baseline_disabled", bp), ("final_disabled", fp)]:
        summary.append({"sample": name, "turns": len(p["turns"]),
                        "median_ms": statistics.median(r["elapsed_ms"] for r in p["turns"]),
                        "narration_function_entries": sum(r["narration_provider_calls"] for r in p["turns"]),
                        "external_provider_calls": 0,
                        "input_tokens": None, "output_tokens": None,
                        "known_retry_metadata_total": sum(r.get("retries_meta") or 0 for r in p["turns"]),
                        "turns_with_unavailable_retry_metadata": sum(r.get("retries_meta") is None for r in p["turns"])})
    for name, p in [("live_before_local_repairs", live1), ("live_before_final_recall_fix", live2), ("live_holdouts", holdouts)]:
        summary.append({"sample": name, "turns": len(p["rows"]), "median_ms": statistics.median(r["elapsed_ms"] for r in p["rows"]),
                        **{key: p["provider"][key] for key in ["requests", "input_tokens", "output_tokens", "total_tokens"]},
                        "narration_calls": sum(r.get("purpose") != "interpretation" for r in p["provider"]["records"] if r.get("sent")),
                        "retry_calls": sum("retry" in str(r.get("purpose")) for r in p["provider"]["records"] if r.get("sent"))})
    write("performance_comparison.json", json.dumps(summary, indent=2))

    reports = {}
    reports["01_EXECUTIVE_SUMMARY.md"] = """
# 01 — PR-EF Executive Summary

**C — PR-EF REQUIRES REPAIR. Do not begin PR-EG.**

Implemented an explicit communication recipient/purpose extension to the existing live interpretation call and the PR-EA decision envelope. GM answers select existing public passages rather than generated facts. Added bounded persisted facilitator context, correction/withdrawal handling, proposal eligibility checks, unsupported-singleton separation, and resolver-owned recall of an NPC's disclosed topic. Existing movement, exploration, social and final-emission owners remain in charge.

The final production HTTP replay sustains ten unchanged player messages in one campaign, with save/load at turn six. It uses captured real interpretation outputs and recorded narration; it is **not a fresh fully live success**. The two fresh ten-turn live samples both failed the NPC follow-up at turn five. The final recall repair fixes that exact recorded contract through the real social resolver and final-emission path, but was not freshly requalified after the 30-call approved budget was exhausted.

Frozen, isolated live interpreter holdouts scored **5/12** against the prespecified labels. A question about an NPC's expression became NPC ASK, so a GM question could still advance the world if that classification reaches execution. Some label failures are contained by deterministic correction/withdrawal handling or safe clarification in the full pipeline, but that does not establish broad conversational competence. The final structural mixed-intent safeguard retains the action that the provider mislabeled as part of a GM question.

The comparable regression family retains the same 30 inherited failures, with no new failing IDs. New PR-EF checks cover authority, persistence, proposal integrity, continuous HTTP routing and compound order. No new mechanics, campaign-start workflow or simulation rewrite was introduced. Review the remaining semantic ownership defect before acceptance.
"""
    reports["02_ARCHITECTURE_COMPARISON.md"] = """
# 02 — Architecture Comparison

Before: `/api/chat` -> narrow deterministic conversation checks -> operation-shaped live interpretation -> connected/incidental/unsupported partition -> executable bridge or compound clarification -> resolvers -> narration/final emission. Unsupported singleton cardinality was ignored. An active NPC could capture arbitrary questions before communication ownership was considered.

After: `/api/chat` -> structured pending/GM continuation checks -> **same live call, with communication ownership and public evidence selection** -> communication decision before executable routing -> non-mutating answer/clarification, or existing bridge -> existing authoritative resolver -> existing final emission. No second provider call is mandated. Obvious confirmations, withdrawal, known context and grounded movement remain provider-free.

GM answers: orchestration owns selection/emission of already public text. New observation: only PERCEIVE/INSPECT may pass to the existing exploration bridge. NPC dialogue: bridge binds visible NPC; social owner resolves content and rechecks recalled topic membership/disclosure. Actions: existing bridge/resolvers own all success, movement, clue disclosure and time. Session/rules: non-mutating response, with explicit uncertainty where no ruling is established. Clarification/refusal: orchestration owns text and bounded continuation state.

Final-emission validators were not removed or weakened. Early GM answers continue the PR-EA non-mutating response path; the provider supplies evidence IDs, not free-form answer prose. Resolver-backed responses, including the new NPC recall fast path, still traverse the existing narration/final-emission pipeline. The remaining interpreter ownership error is a classifier boundary defect, not permission to mutate world state from response prose.
"""
    reports["03_CONVERSATIONAL_AUTHORITY_CONTRACT.md"] = """
# 03 — Conversational Authority Contract

The production schema extends the existing PR-DO/DP object with `communication` containing recipient (GM, NPC, CHARACTER, SESSION, MIXED, AMBIGUOUS), purpose, descriptive subject, and evidence reference IDs. Purpose includes question, description, explanation, recall, rules, action, observation, correction, withdrawal, confirmation, tentative and clarification. The old adapter validates its existing object unchanged; the production wrapper separately validates the extension and attaches only engine-selected public passages. Legacy recorded envelopes remain supported.

`ConversationalDecision` adds communication owner/purpose to its existing category, execution policy, proposed record, secondary intentions and context update. GM informational responses cannot obtain a world resolver by providing an arbitrary component. New GM observation may hand off only PERCEIVE/INSPECT. A declared ACTION/in-world-mode disagreement is reconciled toward the attempt already described by the existing operation contract. Questions containing consequential movement/attack/use/follow components become MIXED; the action is retained without execution.

Invariants: interpretation describes intent, never success; evidence IDs must exist in an engine-built public projection; no private NPC topics or undiscovered clues are supplied as GM answer evidence; GM is never a world entity; confirmation requires a grounded, supported first operation; unsupported/deferred steps remain represented but unapproved; correction/withdrawal never undo committed state.

Context: `session.conversational_context.last_gm_exchange` stores bounded subject/response, category, owner/purpose, scene and refusal reason or prior operation. Existing pending clarification/proposal and active NPC remain separate fields under their established owners. No transcript or memory graph is duplicated.
"""
    reports["04_PRODUCTION_INTEGRATION_EVIDENCE.md"] = """
# 04 — Production Integration Evidence

Actual transport: FastAPI TestClient POST `/api/chat?ui_mode=player`. One disposable authored campaign includes the gate, barred side gate, concerned Sergeant Mara, lantern and reachable waystation street. Runtime fixture paths are confined to a temporary directory in `development/tmp`; no active save is used as provider context. The script restores interpretation mode after historical experiment imports disable it.

`live_ten_turns.json` and `live_final_ten_turns.json` contain real provider raw interpretations, full resolutions, response text, state differences and usage records. These are failed development runs and remain included. `final_recorded_http_ten_turns.json` replays the second run's exact raw interpretations against final code; narration is associated with the corresponding recorded turn. No stored-interpretation bypass or manual player-message rewriting is used. Adapter, orchestration, bridge, resolvers, HTTP serialization, persistence and final emission are real.

The final replay routes turns 1/2/3/6/8/9 through non-mutating conversation; 4/5 through visible-NPC ASK and social authority; 7 through inspection/discovery; 10 through authoritative movement with no redundant narration request. Turn five now uses the NPC's selected previously revealed authored topic, revalidated against the current NPC/runtime. Turn six answers with that established topic instead of attributing a new NPC utterance.

Limits: recorded-provider execution is stronger than isolated unit tests but cannot prove the final prompt/model will choose the same records on a fresh run. The remaining live holdout recipient error prevents acceptance.
"""
    transcript = ["# 05 — Continuous Ten-Turn Transcript", "", "Final-code HTTP replay of captured live interpretations. One campaign; no reset between turns; save/load at turn six. External calls in replay: zero. Full decisions, state keys, resolutions and context are in the corresponding JSON.", ""]
    for row in replay["rows"]:
        resolution = row["resolution"]
        decision = row.get("decision") or {}
        transcript += [f"## Turn {row['turn']}", "", f"Player: {row['player']}", "", f"GM: {row['response']}", "",
                       f"Decision: {decision.get('communication_owner', 'resolver')} / {decision.get('category', resolution.get('kind'))}. Resolution: {resolution.get('kind')}. Turn counter: {row['before_turn']} -> {row['after_turn']}. World changed: {row['world_changed']}. HTTP: {row['http_status']}. Replay latency: {row['elapsed_ms']} ms. Provider calls: {row['provider_calls']}.", "",
                       "Classification: PASS WITH RESPONSE LIMITATION (broad restatement of established text)." if row["turn"] in {2, 8} else "Classification: PASS for routing, authority and continuity in this recorded-input sequence.", ""]
    transcript += ["## Fresh live result", "", "Both preceding fresh live runs completed ten HTTP requests and preserved GM-turn world-state invariants, but turn five emitted 'No one here can answer that from what is settled here.' This is a behavioral FAIL despite successful HTTP delivery. The final live run correctly disclosed the lantern mark at turn seven and moved at turn ten. The final NPC recall correction was verified by replay and tests, not by a third fresh live campaign."]
    reports["05_CONTINUOUS_TEN_TURN_TRANSCRIPT.md"] = "\n".join(transcript)
    semantic = ["# 06 — Semantic Generalization Results", "", "The expressions in holdouts.json were written before production edits. No exact-match production handlers were added for holdout failures. The 12-call live test exercised the production interpreter in the same authored scene, without pending proposals or active NPC setup. It tests the interpreter contract, not complete conversational behavior.", "", "| Expression | Expected | Observed label | Result |", "|---|---|---|---|"]
    semantic += [f"| {r['player']} | {r['expected']} | {r['actual']} | {'PASS' if r['pass'] else 'FAIL'} |" for r in holdouts["rows"]]
    semantic += ["", "**Observed strict label score: 5/12.** The NPC-expression error is materially unsafe for GM/non-mutating intent. Rules-question mode was present despite a GM/QUESTION extension label. Ambiguity safely clarified despite a GM recipient label. Correction and withdrawal are intercepted before interpretation by the production continuity layer, so their standalone provider errors do not prove full-pipeline execution. Bare confirmation without pending context must clarify; its standalone ACTION label is wrong. The mixed input kept ASK+MOVE components while calling the recipient GM: the final structural safeguard now emits MIXED/CLARIFY with both components retained.", "", "Development examples are the ten-turn fixture and focused authority/proposal tests. Final-code changes made after this measurement were checked deterministically/with recorded data; these original holdouts cannot be called unseen requalification after those changes. No provider-disabled test is presented as natural-language competence. The final recommendation remains C."]
    semantic += ["", "Full production HTTP replay of those captured holdout records: **10/12 behavioral checks pass**, separately from the strict live interpreter label score. Confirmation is tested with a genuine API-created pending two-step proposal; other expressions start from the authored scene. Failures: the expression question invokes social/world progression; 'I make for the courtyard gate' reaches a deterministic execution decision but emits an unresolved result instead of completing movement. The latter did not call the wire interpreter. The replay source and full resolutions are in replay_holdouts.py and production_holdout_replay.json. These checks reuse measured expressions and are not an unseen holdout rerun."]
    reports["06_SEMANTIC_GENERALIZATION_RESULTS.md"] = "\n".join(semantic)
    reports["07_CONFIRMATION_COMPOUND_AUDIT.md"] = """
# 07 — Confirmation and Compound-Intent Audit

Removed the `len(connected) > 1 or unsupported` conflation. A singleton unsupported operation declines without a pending executable proposal or confirmation question. Unsupported interpretation status also declines directly. Genuine compounds retain the original component order and operation identity, incidental context and later intentions.

Before offering the first step, production checks the existing full bridge: connected operation, compatible visible target, resolved references and authored/known destination. Eligibility remains independent of resolver success. An unsupported first step cannot be skipped in favor of a later supported action. A supported first step with unsupported later work may be confirmed, while the response explicitly says that later work cannot be resolved as stated.

After execution, eligible remaining steps stay in the bounded pending sequence. Unsupported remainder is stored as `deferred_intentions`, not an executable proposal. A yes response to that remainder declines and clears it. Withdrawals clear pending work; corrections clear pending work and request a revised action without rolling back resolved facts. Existing PR-EC inspection-then-picking and movement tests remain in the comparison family.

The final mixed-input repair preserves independently consequential components even if the provider labels the question as GM. It asks to settle the condition and states that no action has happened; it does not automatically execute upon an unresolved condition. General-purpose revised-action referent binding remains limited: a correction safely clears and asks for the revised action rather than executing it automatically.
"""
    reports["08_AUTHORITY_PERSISTENCE_AUDIT.md"] = """
# 08 — Authority and Persistence Audit

The continuous replay records full world comparisons and per-turn session key differences. GM description, established lantern follow-up, NPC appearance question, GM clarification, explanation and withdrawal do not advance turn count or change world state. Bounded conversation context and save timestamps may change. Social exchanges may change existing NPC runtime/disclosure and clocks; inspection discloses the authored lantern mark only through the resolver; movement changes scene through the existing transition owner.

Turn six serializes and reloads the persisted context in the same campaign. Every subsequent HTTP request reloads session data. Existing save/load and runtime-persistence suites pass. Pending withdrawal after reload is tested explicitly; completed steps are removed from the remaining sequence before it is saved. Unsupported deferred work cannot be approved by a later yes. An explicit new character declaration is not blocked by expired scene-scoped clarification.

Provider evidence excludes private topics and undiscovered clues. Previously disclosed NPC topic evidence comes only from an existing resolver's logged topic payload. Social recall rechecks current speaker identity, authored topic equality, selected evidence ID and `revealed_topics` before repeating it. It cannot add a topic or cause NPC compliance.

Limit: a live holdout was incorrectly classified as NPC ASK, so the current system still cannot guarantee that every GM-intended question avoids social/world mutation. This is an unresolved PR-EF defect, not a passing authority claim. Active campaign files were not intentionally read into fixtures or written; a full active-data hash snapshot was not taken at task start, so byte-for-byte preservation is not independently claimed.
"""
    perf = ["# 09 — Performance Comparison", "", "Same PR-ED disposable ten-turn profiler before/after; provider disabled. Values are local measurements, not a latency improvement claim.", "", "| Sample | Median ms | Narration function entries | External requests |", "|---|---:|---:|---:|"]
    perf += [f"| {r['sample']} | {r['median_ms']} | {r['narration_function_entries']} | 0 |" for r in summary[:2]]
    perf += ["", "Provider-disabled input/output tokens are unavailable. Function entries count attempted narration boundaries, including disabled or discarded output; they are not external requests. Persistence and prompt estimates are retained per turn in both profile JSON files. The two samples are single runs and were collected under different surrounding machine load.", "", "| Live sample | Calls | Input tokens | Output tokens | Total tokens | Median turn ms | Retries |", "|---|---:|---:|---:|---:|---:|---:|"]
    perf += [f"| {r['sample']} | {r['requests']} | {r['input_tokens']} | {r['output_tokens']} | {r['total_tokens']} | {r['median_ms']} | {r['retry_calls']} |" for r in summary[2:]]
    perf += ["", "30 external calls were completed after explicit user approval: 9 + 9 + 12. Before approval, an aborted harness-mode attempt sent additional narration requests; its usage file is retained separately and excluded from the approved 30-call comparison. It imported an experiment that disabled interpretation; that sample is invalid for conversational acceptance. Automatic approval review initially denied the repeat; explicit payload/destination approval was then obtained. No rejection was bypassed.", "", "Production retains the 320-token interpretation cap, existing timeout helper (45 seconds by default), narration budget and PR-ED retry/movement skips. The live harness used a bounded 25-second timeout and 1600-token narration cap; these are validation settings, not new production defaults. The old profiler's `openai_sdk_default` timeout label is stale; current source is authoritative. The new NPC recall skip uses a resolver-owned already disclosed answer and still reaches final emission.", "", "Performance summaries now include interpretation tokens when available and do not label decline/clarify as conversational success. Aggregate tokens remain unavailable when multiple narration attempts cannot be reconstructed from a single final stamp; raw budget usage is the source for complete live totals. No before/after live speedup is claimed: the samples differ in code and behavior."]
    reports["09_PERFORMANCE_COMPARISON.md"] = "\n".join(perf)
    reports["10_REGRESSION_COMPARISON.md"] = f"""
# 10 — Regression Comparison

Baseline: {regression['baseline_passed']}/{len(baseline)} passed, {len(oldfail)} failed. Final: {regression['final_passed']}/{len(final)} passed, {len(newfail)} failed. Added PR-EF tests: {len(regression['added_tests'])}. New failing IDs: {len(regression['new_regressions'])}; resolved inherited IDs: {len(regression['resolved'])}; inherited failing IDs: {len(regression['inherited'])}; changed normalized failure messages: {len(regression['changed_failure_signatures'])}.

Full individual results and preserved signatures: regression_comparison.json, baseline_junit.xml and final_junit.xml. Object addresses are normalized for message comparison; no failure is suppressed. The pre-existing failures concern social/final-emission/retry behavior and four exploration chat routes. They were not repaired to make the baseline green.

The exact comparison commands are in validation_commands.json. Same 16 PR-EC/ED suite files, plus the new PR-EF test file only in the final run. This is a representative regression family, not the complete repository test suite. Windows sandbox TestClient hangs in local socketpair setup; provider-disabled HTTP runs were performed outside the sandbox. Test model guards remain enabled. A first profiler temp-directory permission failure was resolved by putting TEMP/TMP under the workspace.

Inherited failing tests:

""" + "\n".join(f"- `{key}`" for key in regression["inherited"])
    reports["11_REMAINING_ISSUES.md"] = """
# 11 — Remaining Issues

PR-EF blocking defect: live semantic ownership can still route a third-person perception question to NPC ASK. Do not claim general non-mutating GM communication safety. Strict live interpreter labels matched only 5/12 frozen expressions; full-pipeline correction/withdrawal containment does not erase those errors.

Acceptance gap: no completely successful fresh live ten-turn run exists on the final code. The final raw-record replay is coherent, including the repaired NPC follow-up, but provider behavior after the final edits is unmeasured. The approved 30-call validation budget was used; no further calls were sent.

Additional production holdout replay limitation: 'I make for the courtyard gate' is recognized as movement by orchestration but finishes with an unresolved operation rather than a transition. The same frozen-record HTTP audit passes 10/12 checks. This handoff defect and the NPC-expression recipient defect remain open; neither is hidden by the deterministic test counts.

Bounded response limitations: public evidence extraction can repeat a whole scene summary; causal explanations can restate the prior result rather than explain a rule; rules/session support remains conservative and some legacy help/OOC replies acknowledge the request instead of answering it. Revised referents require a restated action. NPC repeat emission can add the legacy 'Word is' framing to an authored answer. No unsupported fact is invented by the new GM answer path.

PR-EG dependencies: campaign-start/lifecycle workflow remains deferred, including the PR-EE transcript gate issue. No New Campaign workflow, opening generation or campaign UI work was done. Unrelated debt: the 30 inherited regression failures, narration embellishment/retry behavior, older experiment imports changing environment state, stale profiler labels and legacy schema vocabulary.

Retain the current implementation for review, but repair/requalify PR-EF before starting PR-EG. Do not treat successful HTTP delivery, a recorded-input replay or passing unit tests as product acceptance.
"""
    reports["12_FINAL_RECOMMENDATION.md"] = """
# 12 — Final Recommendation

**C — PR-EF REQUIRES REPAIR.**

The bounded architectural repairs are implemented and reviewable. The production route supports a coherent ten-turn recorded-provider interaction, supported proposals are checked before confirmation, and the comparison family has no newly failing IDs. This does not satisfy the full acceptance criteria: a known live ownership misclassification can turn GM observation talk into NPC interaction, strict semantic holdouts scored 5/12, and the final recall repair has not completed a fresh live ten-turn requalification.

Required review focus: strengthen recipient/purpose consistency in the existing interpretation contract without a phrase catalog; validate third-person GM observation versus direct NPC speech; requalify the full unchanged live sequence and a newly frozen holdout set after repairs. Keep existing resolvers and state boundaries. Stop after PR-EF and await external review. PR-EG is not started.
"""
    inventory = ["# 13 — Changed-File Inventory", "", "PR-EF additions are relative to the dirty working tree captured before implementation, not to HEAD (which predates many prior cycles). Production references below point to final source. The PR-EF-only diff compares initial snapshots where available; social/bridge initial snapshots were reconstructed by removing only the documented PR-EF insertion blocks and are labelled accordingly.", ""]
    prod = {
        "game/conversational_orchestration.py": "Ownership/purpose, public evidence, GM continuity, safe mixed communication, unsupported cardinality, proposal eligibility/order, deferred-intent handling.",
        "game/live_chat_interpretation.py": "Production schema extension and validation, public-evidence/context projection, same-call ownership, conservative mode/purpose reconciliation, accurate schema token preflight.",
        "game/player_interpretation_bridge.py": "Carry descriptive ownership and selected public-evidence metadata to the existing social resolver; execution checks retained.",
        "game/social.py": "Recall an already revealed authored topic only after rechecking speaker, payload and runtime disclosure; mark the existing resolver result.",
        "game/api.py": "Production decision context, bounded discourse persistence, resolver-owned recalled-answer skip through final emission, interpretation usage summary and decision-success distinction.",
    }
    sources = [*prod, "tests/test_pr_ef_gm_authority.py", "tools/validate_pr_ef.py", "tools/build_pr_ef_review.py"]
    for path in sources:
        inventory += [f"- `{path}` — {prod.get(path, 'Validation tests/harness/reproducible review generator.')} SHA-256: `{hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}`."]
    inventory += ["", "Additional generated changes: artifacts/pr_ef_gm_authority (13 reports, evidence, snapshots, diff and command inventory); handoff/CURRENT_REVIEW.md, REVIEW_MANIFEST.json and CURRENT_REVIEW.zip, with predecessor preserved under handoff/history/pr-ee-before-pr-ef. No formal PR-EG work was done.", "", "Relevant source references:", ""]
    for path in prod:
        for i, line in enumerate((ROOT/path).read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r"def (?:production_interpretation_schema|interpret_production_turn|public_conversation_evidence|_communication_decision|_gm_continuation_decision|_compound_clarification|decision_from_interpretation_record|normalized_action_from_interpretation|resolve_social_action|_nonmutating_conversational_decision_response|deterministic_provider_skip_line|_performance_record|chat)\(", line):
                inventory.append(f"- `{path}:{i}` — `{line.split('(')[0].removeprefix('def ')}`")
    reports["13_CHANGED_FILE_INVENTORY.md"] = "\n".join(inventory)
    for name, text in reports.items():
        write(name, text)
    write("REVIEW.md", "# PR-EF — GM Conversational Authority & Continuity\n\nRecommendation: **C — PR-EF REQUIRES REPAIR**.\n\n" + "\n".join(f"- [{name}]({name})" for name in reports) + "\n\nRaw evidence is adjacent. CURRENT_REVIEW.zip is the portable review bundle. No PR-EG work has begun.")

    diffs = []
    for path in prod:
        before = OUT / "source_before" / Path(path).name
        if before.exists():
            diffs.extend(difflib.unified_diff(before.read_text(encoding="utf-8").splitlines(True), (ROOT/path).read_text(encoding="utf-8").splitlines(True), fromfile="before/" + path, tofile="after/" + path))
    write("pr_ef_only.patch", "".join(diffs))
    files = [p for p in OUT.rglob("*") if p.is_file() and p.suffix not in {".pyc"} and "__pycache__" not in p.parts]
    config = {
        "campaign_id": "pr_ef_gm_authority_20261016", "campaign_name": "PR-EF — GM Conversational Authority & Continuity",
        "campaign_date": "2026-10-16", "purpose": "Bounded communication ownership and continuity repair; stop before PR-EG.",
        "objective_status": "REQUIRES REPAIR", "executive_summary": reports["01_EXECUTIVE_SUMMARY.md"].split("\n", 3)[-1],
        "changes": {"production": list(prod.values()), "validation": [f"{len(regression['added_tests'])} PR-EF tests plus production HTTP replay and 30 approved live calls."], "documentation": ["13 required review reports and raw failure evidence."]},
        "testing": {"focused": f"{len(regression['added_tests'])} new checks; see final_junit.xml.", "broader": f"Baseline {len(baseline)-len(oldfail)} pass / {len(oldfail)} fail; final {len(final)-len(newfail)} pass / {len(newfail)} fail.", "full_suite": "Not run.", "runtime_validation": "Final recorded-provider ten-turn HTTP replay coherent; fresh live ten-turn attempts failed NPC follow-up.", "model_runtime_boundary": "gpt-4.1-mini; 30 explicitly approved synthetic live calls; no active campaign payload.", "new_regressions": str(regression['new_regressions']), "pre_existing_failures": "30 unchanged failing IDs in the comparison family."},
        "decisions_requiring_human_review": ["Review recommendation C and the known live recipient error before any PR-EG work."],
        "known_problems": {"campaign_specific": ["Live ownership holdouts 5/12; third-person expression question became NPC ASK.", "Final NPC recall fix has recorded-input validation, not fresh live requalification."], "pre_existing": ["30 social/retry/emission/exploration failures."]},
        "missing_concepts": ["Formal campaign-start workflow deferred to PR-EG."],
        "does_not_prove": ["General natural-language conversational competence.", "A completely successful final-code fresh live ten-turn campaign.", "No regressions outside the comparison family."],
        "recommended_next_step": "External review, then PR-EF recipient/purpose repair and fresh requalification. Do not start PR-EG.",
        "primary_report": "artifacts/pr_ef_gm_authority/REVIEW.md", "evidence_packets": [],
        "supporting_files": [{"path": p.relative_to(ROOT).as_posix(), "role": "source" if p.relative_to(ROOT).as_posix() in sources else "evidence", "why": "PR-EF source, decision report, reproducible validation or raw evidence.", "behavioral_evidence": p.suffix in {".json", ".jsonl"}, "human_review_required": p.suffix == ".md"} for p in [*files, *(ROOT/p for p in sources)]],
        "self_contained_review_test": "Portable ZIP contains 13 reports, raw HTTP/live/holdout records, baseline/final JUnit, measured profiles, PR-EF-only diff and changed source/tests/tools, with SHA-256 manifest. Does not include dependencies or the full repository.",
    }
    config_path = OUT / "handoff_config.json"
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    previous = ROOT / "handoff/history/pr-ee-before-pr-ef"
    if not previous.exists():
        previous.mkdir(parents=True)
        for name in ["CURRENT_REVIEW.md", "CURRENT_REVIEW.zip", "REVIEW_MANIFEST.json"]:
            shutil.copyfile(ROOT / "handoff" / name, previous / name)
    result = build_handoff(config, root=ROOT, output_dir=ROOT/"handoff", archive_history=True)
    print(json.dumps({key: result[key] for key in ["summary_path", "zip_path", "file_count", "zip_size_bytes"]}))


if __name__ == "__main__":
    main()
