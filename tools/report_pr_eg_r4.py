"""Build the evidence-backed PR-EG-R4 review; never changes game behavior."""
from __future__ import annotations
import hashlib
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/pr_eg_r4"
sys.path.insert(0, str(ROOT))


def read(name, default=None):
    p = OUT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def lines(name):
    p = OUT / name
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()] if p.exists() else []


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def md(number, title, body):
    p = OUT / f"{number:02}_{title.upper().replace(' ', '_').replace('-', '_')}.md"
    p.write_text(f"# {number:02} — {title}\n\n{body.strip()}\n", encoding="utf-8")
    return p


def block(value):
    return "```json\n" + json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n```"


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"] +
        ["| " + " | ".join(str(x).replace("|", "/").replace("\n", " ") for x in row) + " |" for row in rows])


def percent(n, d):
    return f"{n}/{d} ({100*n/d:.1f}%)" if d else "0/0 — not observed"


def junit(path):
    if not path.exists():
        return {}
    return {case.attrib["classname"] + "::" + case.attrib["name"]:
        "failed" if case.find("failure") is not None else "error" if case.find("error") is not None else
        "skipped" if case.find("skipped") is not None else "passed" for case in ET.parse(path).iter("testcase")}


def summary(rows):
    q = [r["score"]["quality"] for r in rows if r.get("score")]
    p = [r["score"]["playability"] for r in rows if r.get("score")]
    latencies = sorted(r["elapsed_ms"] for r in rows)
    calls = [c for r in rows for c in r["engine_calls"] if c.get("sent")]
    return dict(turns=len(rows), scored=len(q), quality_mean=round(statistics.mean(q), 3) if q else None,
        quality_median=statistics.median(q) if q else None, quality_distribution=dict(Counter(q)),
        quality_pass=sum(x>=2 for x in q), playability_mean=round(statistics.mean(p), 3) if p else None,
        playability_median=statistics.median(p) if p else None, playability_distribution=dict(Counter(p)),
        playability_pass=sum(x>=2 for x in p), engine_calls=len(calls),
        purposes=dict(Counter(c.get("purpose") for c in calls)),
        input_tokens=sum(c.get("input_tokens") or 0 for c in calls), output_tokens=sum(c.get("output_tokens") or 0 for c in calls),
        latency_mean_ms=round(statistics.mean(latencies), 2) if latencies else None,
        latency_median_ms=statistics.median(latencies) if latencies else None,
        latency_p95_ms=latencies[max(0, __import__('math').ceil(len(latencies)*.95)-1)] if latencies else None,
        latency_max_ms=max(latencies) if latencies else None)


def main():
    protocol = read("protocol.json")
    env = read("environment.json")
    turns = lines("turns.jsonl")
    scores = {(s["conversation"], s["turn"]): s for s in lines("scores.jsonl")}
    audit = read("agent_audit.json", {})
    overrides = {(s["conversation"], s["turn"]): s for s in audit.get("overrides", [])}
    for row in turns:
        key = (row["conversation"], row["turn"])
        row["score"] = dict(scores.get(key) or {})
        if key in overrides:
            row["score"].update(overrides[key]["score"])
    conversations = defaultdict(list)
    for row in turns:
        conversations[row["conversation"]].append(row)
    total = summary(turns)
    grouped = {dimension: {value: summary([r for r in turns if
        (r["player"].get("category", "unclassified") if dimension == "category" else r[dimension]) == value]) for value in
        sorted({r["player"].get("category", "unclassified") if dimension == "category" else r[dimension] for r in turns})}
        for dimension in ("scene", "profile", "category")}
    grouped["outcome"] = {"successful": summary([r for r in turns if r.get("score", {}).get("quality", -1)>=2]),
                           "failed": summary([r for r in turns if r.get("score") and r["score"]["quality"]<2])}
    save("metrics.json", dict(overall=total, groups=grouped))
    reg = junit(OUT / "relevant_junit.xml")
    prior = junit(ROOT / "artifacts/pr_eg_r3_r1/final_relevant_junit_confirm.xml")
    failed = {k for k,v in reg.items() if v in {"failed", "error"}}
    prior_failed = {k for k,v in prior.items() if v in {"failed", "error"}}
    regression = dict(counts=dict(Counter(reg.values())), prior_counts=dict(Counter(prior.values())),
        inherited=sorted(failed & prior_failed), new=sorted(failed-prior_failed), resolved=sorted(prior_failed-failed))
    save("regression_comparison.json", regression)
    failure_counts = Counter(f for r in turns for f in r.get("score", {}).get("failures", []))
    save("failure_counts.json", dict(failure_counts))
    continuity = [r for r in turns if r.get("score", {}).get("continuity", {}).get("applicable")]
    continuity_ok = sum(r["score"]["continuity"].get("correct", False) for r in continuity)
    all_recoveries = audit.get("recoveries", [])
    recoveries = [r for r in all_recoveries if r.get("eligible", True)]
    recovery_success = sum(r.get("success_within_two", False) for r in recoveries)
    exact_repeated = 0
    spans = []
    reformulations = sum(bool(r.get("score", {}).get("reformulation")) for r in turns)
    clarifications = sum(bool(r.get("score", {}).get("clarification_requested")) for r in turns)
    for cid, rows in conversations.items():
        span = 0
        for idx, row in enumerate(rows):
            if idx and row["text"].strip().lower() == rows[idx-1]["text"].strip().lower():
                exact_repeated += 1
            if row.get("score", {}).get("playability", -1)>=2:
                span += 1
            elif span:
                spans.append(span)
                span = 0
        if span:
            spans.append(span)
    play_metrics = dict(reformulations=reformulations, clarification_responses=clarifications,
        adjacent_exact_repetitions=exact_repeated, unproductive_turns=sum(r.get("score", {}).get("quality", 3)<2 for r in turns),
        uninterrupted_span_count=len(spans), mean_uninterrupted_adequate_span=round(statistics.mean(spans),3) if spans else 0,
        longest_adequate_span=max(spans) if spans else 0, continuity_success=continuity_ok, continuity_denominator=len(continuity),
        recovery_success=recovery_success, recovery_denominator=len(recoveries))
    play_metrics.update(reformulation_frequency=percent(reformulations,len(turns)),
        clarification_frequency=percent(clarifications,len(turns)),
        repeated_response_frequency=percent(exact_repeated,len(turns)-len(conversations)),
        unproductive_frequency=percent(play_metrics['unproductive_turns'],len(turns)))
    save("playability_metrics.json", play_metrics)
    stop = read("stop.json") if not read("completion.json") else None
    integrity_critical = [r for r in turns if r.get("score", {}).get("integrity", {}).get("critical")]
    integrity_critical += audit.get("critical_findings", [])
    state_fail = [dict(conversation=r["conversation"], turn=r["turn"], checks=r["checks"]) for r in turns if
        not r["checks"].get("no_unauthorized_canonical_changes", False) or (not r["checks"]["history_matches"] and bool(r["session_changes"])) or
        not r["checks"]["accepted_text_matches"] or r["checks"]["rejected_candidate_delivered"]]
    canonical_fail = [r for r in turns if not r['checks'].get('no_unauthorized_canonical_changes',False)]
    characterized = audit.get("distinct_characterized_npcs", [])
    beyond = [r for r in turns if r.get("score", {}).get("useful_beyond_authored")]
    fresh_complete = len(turns)>=180 and len([rows for rows in conversations.values() if len(rows)>=15])>=12
    q_gate = total["scored"]>0 and total["quality_pass"]/total["scored"]>=.85
    p_gate = total["scored"]>0 and total["playability_pass"]/total["scored"]>=.80
    gates = [
        dict(gate=1, name="Information integrity", status="FAIL" if integrity_critical else "PASS (observed sample)" if turns else "UNVERIFIED", evidence=f"{len(integrity_critical)} unauthorized consequential disclosure findings / {len(turns)} delivered turns; hidden probes not reached; separate adoption blocker"),
        dict(gate=2, name="Conversational relevance", status="PASS" if q_gate else "FAIL" if total["scored"] else "UNVERIFIED", evidence=percent(total["quality_pass"], total["scored"])+"; target 85%"),
        dict(gate=3, name="Playability", status="PASS" if p_gate else "FAIL" if total["scored"] else "UNVERIFIED", evidence=percent(total["playability_pass"], total["scored"])+"; target 80%"),
        dict(gate=4, name="Recovery", status="PASS" if recoveries and recovery_success/len(recoveries)>=.75 else "FAIL" if recoveries else "UNVERIFIED", evidence=percent(recovery_success, len(recoveries))+"; target 75% within two additional player turns"),
        dict(gate=5, name="Continuity", status="PASS" if continuity and continuity_ok/len(continuity)>=.9 else "FAIL" if continuity else "UNVERIFIED", evidence=percent(continuity_ok, len(continuity))+"; target 90%"),
        dict(gate=6, name="Characterization", status="PASS" if len(characterized)>=3 else "FAIL" if fresh_complete else "UNVERIFIED", evidence=f"{len(characterized)}/3 required recognizably distinct NPCs"),
        dict(gate=7, name="Player freedom", status="PASS" if fresh_complete and beyond else "FAIL" if fresh_complete else "UNVERIFIED", evidence=f"{len(beyond)}/{total['scored']} turns assessed useful beyond authored topic prompts; incomplete coverage, see report 15"),
        dict(gate=8, name="Performance", status=audit.get("performance_gate", "UNVERIFIED"), evidence="Engine calls, retries, latency and per-turn prompt sizes in report 16"),
        dict(gate=9, name="State integrity", status="FAIL" if canonical_fail else "PASS (observed sample)" if turns else "UNVERIFIED", evidence=f"{len(canonical_fail)}/{len(turns)} unauthorized canonical mutations; separate adoption/history blocker, authorized discovery events retained"),
        dict(gate=10, name="Evidence quality", status="PASS" if fresh_complete and audit.get("completed") and total["scored"]==len(turns) else "UNVERIFIED", evidence=f"{len(turns)}/180 turns; {sum(len(r)>=15 for r in conversations.values())}/12 sustained conversations; separate provider scoring and root-agent audit"),
    ]
    if integrity_critical or state_fail:
        verdict = "D — CRITICAL ARCHITECTURAL OR INTEGRITY BLOCKER"
    elif not fresh_complete or not audit.get("completed"):
        verdict = "UNVERIFIED — INSUFFICIENT EVIDENCE"
    elif any(g["status"] == "FAIL" for g in gates):
        verdict = "C — PLAYABILITY BELOW ACCEPTANCE STANDARD"
    elif any(g["status"] == "UNVERIFIED" for g in gates):
        verdict = "UNVERIFIED — INSUFFICIENT EVIDENCE"
    else:
        verdict = "B — QUALIFIED WITH DOCUMENTED LIMITATIONS"
    save("acceptance_gates.json", dict(verdict=verdict, gates=gates, stop=stop, critical_adoption_findings=state_fail,
        note="The D verdict is the post-rejection adoption/history stop condition, not an assertion of a new consequential disclosure or unauthorized canonical-world mutation."))
    recommendation = audit.get("recommendation", "Complete missing evidence before qualification; no production repair is authorized in R4. Stop and await external review.")
    executive = f"**{verdict}.**\n\nObserved {len(turns)} qualification turns in {len(conversations)} conversations; {sum(len(r)>=15 for r in conversations.values())} reached 15 turns. Dialogue quality ≥2: {percent(total['quality_pass'],total['scored'])}. Playability ≥2: {percent(total['playability_pass'],total['scored'])}.\n\n" + audit.get("assessment", "Evidence remains incomplete.") + "\n\n" + recommendation
    reports = []
    reports.append(md(1, "Executive Summary", executive))
    reports.append(md(2, "Baseline and Environment", f"Revision: `{env['revision']}`. Pre-existing dirty tree: `initial_git_status.txt`. Hashes of game, tests and campaign saves are in `environment.json`; preservation comparison is in `preservation_check.json`. A Git revision alone does not reproduce this working tree.\n\nPython: {env['python']}; {env['platform']}. Installed dependency versions: `dependency_versions.json`.\n\nSafe configuration:\n\n{block(env['configuration'])}\n\nProvider: OpenAI Responses API. Engine configured gpt-4.1-mini; exact returned model IDs and request IDs preserved in usage logs. Player: gpt-4.1-mini; independent provider evaluator: gpt-4.1. No credentials included.\n\nLive subprocess: provider/interpretation/expression enabled, upstream startup preflight skipped, timeout 45 seconds, explicit token/request ceilings, ASHEN_DATA_DIR points to disposable import state. SDK and production retry behavior unchanged. Narration routing uses current production configuration. Test defaults disable live calls.\n\nThree new fixture overlays use the existing PR-EF/PR-DU courtyard seed; no active factions, avoiding unrelated passive agendas. Each independent conversation is seeded anew. Midpoint persistence and client recreation are recorded, not a full process-restart test.\n\nRelevant baseline:\n\n{block(regression)}"))
    reports.append(md(3, "Evaluation Methodology", "Evaluation-only tooling. Frozen protocol, prompts, fixtures, profile allocation and budgets precede provider evidence. Production /api/chat?ui_mode=player is called through FastAPI TestClient, with real configured provider calls and no dialogue-generation helper substitutes. Only storage paths are patched by the inherited setup helper.\n\nA fresh model player produces one utterance from the actual public transcript, then the production endpoint responds, raw evidence and before/after state are durably written, and a separate evaluator scores delivery. Engine metadata never substitutes for player experience. Scores are independently reviewed by the root agent.\n\nSampling is purposive, not statistical: one stochastic adaptive conversation per allocated scene/profile pair; no certainty or population claim. Exact denominators are shown. Stressors are observed categories, not a fixed question script.\n\nInterrupted attempts and monitor correction: see `evaluation_events.json`. No production code, prompt or regression expectation was changed. Authorized authored-topic discovery events are explicitly checked against the fixture; all other canonical changes stop the run. No rejected candidate is assumed safe merely because the validator accepted another sentence."))
    reports.append(md(4, "Scene Definitions", "Three fixture overlays; each includes at least two present NPCs. Hidden affiliation uses existing NPC affiliation data; no secret is inserted into public topics. Unknown and restricted lists are evaluation authority, not player input.\n\n"+block(protocol["scenes"])))
    reports.append(md(5, "Simulated Player Profiles", block(protocol["profiles"])+"\n\nAllocation:\n\n"+table(["Scene", "Profiles"], [(sid, ", ".join(scene["profiles"])) for sid,scene in protocol["scenes"].items()])))
    reports.append(md(6, "Player Generation Method", "One provider call per next action. Exact request payloads are in `player_inputs/`; they contain only visible scene, objective, behavioral profile and previous delivered transcript. They contain no authorized answer list, secret, resolver internals or score. Intent/category are player-reported aims and later reviewed for scoring.\n\nFrozen player prompt:\n\n"+protocol["player_prompt"]+"\n\nNo full script was generated in advance. `auxiliary_calls.jsonl` preserves raw provider text, exact model, request ID, latency and usage. `protocol.json` is protected by `freeze.json`."))
    inventory=[]
    for sid,scene in protocol['scenes'].items():
        for profile in scene['profiles']:
            cid=sid+'_'+profile
            inventory.append((cid,sid,profile,len(conversations.get(cid,[])),f'states/{cid}_initial.json' if cid in conversations else 'Not started: critical stop'))
    reports.append(md(7, "Conversation Inventory", table(["Conversation", "Scene", "Profile", "Turns", "Initial state"], inventory)+"\n\nEvery started conversation begins from its documented independent initial save. Complete state after each delivered turn is retained; no cross-conversation history is reused. The separate interrupted monitor attempt contains three additional preserved turns, excluded from target coverage. Scene C and the seven unstarted conversations have fixture definitions but no runtime results. Actual stressor coverage is recorded in stressor_coverage.json."))
    transcript_body = []
    for cid, rows in conversations.items():
        transcript_body.append("## " + cid + "\n")
        for r in rows:
            transcript_body.append(f"### Turn {r['turn']}\n\nPlayer: {r['player']['player']}\n\nGM: {r['text']}\n")
    reports.append(md(8, "Complete Conversation Transcripts", "Exact player-facing outputs; raw provider candidates are separately retained in `turns.jsonl`, and never treated as delivered unless actually present.\n\n"+"\n".join(transcript_body)))
    score_rows = []
    for r in turns:
        s = r.get("score") or {}
        score_rows.append((r["conversation"],r["turn"],r["player"].get("category"),s.get("quality","UNSCORED"),s.get("playability","UNSCORED"),",".join(s.get("failures",[])),s.get("reason","")))
    reports.append(md(9, "Turn Level Scoring", "All 0–3 judgments refer to final delivery. Raw engine metadata, selected addressee/subject, resolver, authorized source, candidate, validator, adopted speech, HTTP response, state delta and provider records: `turns.jsonl`. Previous visible context is embedded on every row. Unavailable candidate fields remain absent, never reconstructed as raw output.\n\nScores below include the documented root-agent adjudications; raw independent scores are retained unchanged.\n\n"+table(["Conversation","Turn","Player category","Quality","Playability","Failures","Rationale"],score_rows)+"\n\nQuality overall and by scene/profile/category/outcome:\n\n"+block(dict(overall=total,groups=grouped))))
    reports.append(md(10, "Playability Scoring", "0 blocked; 1 repeated reformulation/workaround; 2 usable with occasional friction; 3 natural flow.\n\n"+block(play_metrics)+"\n\nUnproductive is operationalized as quality <2. Reformulation/clarification are root-reviewed annotations, with raw provider annotations retained. Adjacent repetition compares exact consecutive delivered strings within each conversation, with 64 within-conversation transition opportunities. Span is a maximal run of turns with playability ≥2, interrupted by a lower score or conversation end. These measures describe this corpus.\n\n"+block({k:v for k,v in grouped.items() if k in {"scene","profile","category"}})))
    reports.append(md(11, "Conversational Recovery Analysis", "Root-agent audited recovery episodes are in `agent_audit.json`. Each begins after a poor response and requires a reasonable attempt to resolve the same intent. A topic change or acceptance of an unrelated answer is not recovery. A successful repair must occur on the first recovery request or within the next two player turns; overlapping attempts in the same unresolved episode are not counted as independent successes. One episode at conversation end is right-censored and excluded from the gate denominator.\n\nSuccess: "+percent(recovery_success,len(recoveries))+".\n\n"+block(all_recoveries)))
    reports.append(md(12, "Information Integrity Audit", "Every scored delivered statement receives a separate claim audit against the fixture and prior delivered statements; validator ACCEPT does not establish truth. Claims distinguish authored disclosure, rumor, NPC belief, harmless characterization, uncertainty and unsupported assertion. Raw claim judgments: `scores.jsonl`; root-agent review: `agent_audit.json`. Canonical before/after state and delivered history are preserved in `states/`.\n\nCritical findings: "+str(len(integrity_critical))+".\n\n"+audit.get("integrity_assessment","Not fully independently audited.")+"\n\n"+block([dict(conversation=r['conversation'],turn=r['turn'],audit=r.get('score',{}).get('integrity')) for r in turns])))
    reports.append(md(13, "Continuity Audit", "Correct evaluated references: "+percent(continuity_ok,len(continuity))+". Reference denominator includes evaluator-marked context-dependent questions, excluding simple new questions. Correct ambiguity handling can count when ambiguity is real; unnecessary clarification is a failure.\n\n"+audit.get("continuity_assessment","Independent review incomplete.")+"\n\nSave/load checks:\n\n"+block(lines("reload_checks.jsonl"))+"\n\nThese checks round-trip persisted conversational context and recreate the HTTP client at turn 8; they do not establish process-restart equivalence.\n\n"+table(["Conversation","Turn","Correct","Reason"],[(r['conversation'],r['turn'],r['score']['continuity']['correct'],r['score']['continuity']['reason']) for r in continuity])))
    reports.append(md(14, "Characterization Assessment", audit.get("characterization_assessment","Independent assessment incomplete.")+"\n\nDistinct characterized NPCs meeting the gate: "+str(characterized)+". Different names, roles or a choice between two canned preferences alone do not establish three recognizable personalities.\n\n"+table(["Conversation","Turn","Observation"],[(r['conversation'],r['turn'],r.get('score',{}).get('characterization','')) for r in turns if r.get('score',{}).get('characterization')])))
    reports.append(md(15, "Player Freedom Assessment", audit.get("freedom_assessment","Independent assessment incomplete.")+f"\n\nUseful beyond-authored annotations: {len(beyond)}/{total['scored']}. These are useful interactions outside explicit authored topic prompts, not evidence of unrestricted world improvisation.\n\n"+table(["Conversation","Turn","Input","Delivered"],[(r['conversation'],r['turn'],r['player']['player'],r['text']) for r in beyond])))
    aux = lines("auxiliary_calls.jsonl")
    reports.append(md(16, "Provider Performance", "Engine-only per-turn latency excludes player/evaluator calls. Provider-call latency is separately preserved. Usage is provider-reported; null is unavailable, never zero. Costs are not priced because no price schedule was captured. Engine narration/retry purposes are taken from actual usage records.\n\n"+block(dict(overall=total,breakdown=grouped,auxiliary=read("auxiliary_usage_totals.json"),auxiliary_models=sorted({r['model'] for r in aux}),engine_models=sorted({c.get('model','') for r in turns for c in r['engine_calls']})))+"\n\n"+audit.get("performance_assessment","Performance gate not yet independently assessed.")+"\n\n`auxiliary_calls.jsonl` separates player generation and independent evaluation from gameplay costs. Failed sandbox connection and interrupted monitor attempt are excluded from target-corpus metrics and retained separately. Total campaign usage must include them; see `campaign_usage.json`."))
    reports.append(md(17, "Regression Baseline", "Unchanged predecessor relevant family, including R3, R3-R1 and R2C-R2 reference eligibility. No test expectations were modified. Exact command: `regression_run.json`; complete output: `regression_output.txt`; identities/results: `relevant_junit.xml`.\n\n"+block(regression)+"\n\nHistorical tests can write repository artifacts. 62,082 pre-existing files were temporarily backed up, then compared byte-for-byte after the tests; zero required restoration (`regression_restored_outputs.json`). The temporary duplicate backup was removed after verification. Game, tests and player saves also match the initial hash inventory. This suite is not a substitute for playability evidence. Full repository suite not run."))
    reports.append(md(18, "Independent Evaluation Method", "Player generation and engine use gpt-4.1-mini, while a separate evaluator uses gpt-4.1 at temperature 0, in a separate call after durable delivery. The evaluator receives fixture authority and the public history, but no engine validator result or resolver explanation. The root Codex agent performs a separate transcript/state review. The last stopped turn receives a root-agent score only: no evaluator provider call occurred after the integrity stop. This is not a human evaluation and the models share a vendor.\n\nExact evaluator prompt:\n\n"+protocol["judge_prompt"]+"\n\nRoot-agent audit instructions: read each complete player-facing conversation; audit every delivered factual statement against fixture and historical speech; independently assess relevance, ability to continue, recovery, speaker identity, continuity, and gate evidence; record disagreements without rewriting raw scores.\n\nEvaluator disagreements/adjudications:\n\n"+block(audit.get("overrides",[]))+"\n\n"+audit.get("evaluation_limitations","Independent review is incomplete.")))
    reports.append(md(19, "Failure Taxonomy Results", "Multi-label counts; denominators are scored turns, not total labels. A failure code does not independently determine the numeric score.\n\n"+table(["Failure","Count","Denominator"],[(f,failure_counts.get(f,0),total['scored']) for f in [f'F{i:02}' for i in range(1,22)]])))
    reports.append(md(20, "Failure Clustering", block(audit.get("clusters",[]))+"\n\nClusters are hypotheses supported by symptoms and source inspection, not experimentally proven repairs. Several symptoms can share the same mechanism."))
    reports.append(md(21, "Severity and Priority Ranking", block(audit.get("priorities",[]))+"\n\nRank accounts for frequency, severity, player impact, recoverability, architectural significance and estimated repair scope. No implementation was started."))
    reports.append(md(22, "Conversation Level Assessments", "Each assessment covers objective support, coherence, friction, recovery, personality, information safety, freedom and willingness to continue. Mean scores do not replace these judgments.\n\n"+block(audit.get("conversations",[]))))
    reports.append(md(23, "Acceptance Gate Results", table(["Gate","Name","Result","Evidence"],[(g['gate'],g['name'],g['status'],g['evidence']) for g in gates])+f"\n\nAdditional critical stop condition: {len(state_fail)}/{len(turns)} turns bypassed speech adoption/history integrity. The D verdict follows this observed post-rejection delivery, even though the bell fact itself is authored and no unauthorized canonical-world mutation or secret disclosure was observed. See critical_stop_evidence.json.\n\nNo statistical confidence is asserted. PASS on integrity means no violation observed under that specific gate criterion in this corpus, not a proof of global safety."))
    reports.append(md(24, "Root Cause Hypotheses", audit.get("root_cause_assessment","Source-level investigation incomplete.")+"\n\nSource locations/hashes are retained for audit. No root cause is asserted solely because a response was safe or a validator passed."))
    reports.append(md(25, "Recommended Next Action", recommendation+"\n\nSTOP after PR-EG-R4. Await external review. Do not begin PR-EH or automatically implement a repair."))
    reports.append(md(26, "Final Verdict", executive+"\n\nAcceptance gates: report 23. Evidence limitations: reports 03, 18 and 27. Relevant regression success does not establish conversational qualification."))
    reports.append(md(27, "Source and Evidence Inventory", "Canonical evidence: supplied `request.txt`; frozen `protocol.json` and SHA-256 `freeze.json`; environment and initial Git status; exact raw provider auxiliary calls; raw production `turns.jsonl`; independent `scores.jsonl`; complete delivered transcripts; initial and per-turn saved world/session/character/combat; reload checks; engine usage; regression JUnit and comparison; root-agent disagreements/recovery audit; metrics/gates; source copies; tooling.\n\n`interrupted_monitor_run/` preserves the false-positive monitor stop; it is not silently counted as a sustained conversation. `evaluation_events.json` records sandbox failure, automatic approval rejection, subsequent explicit user approval and the monitor correction. Temporary inherited-artifact preservation copies were verified and removed; they were never included in the ZIP. No credentials, .env, caches, old review ZIPs or unrelated campaign saves are packaged. Identical state/player-input bytes may be deduplicated by the established bundler; omitted_artifacts records the identical canonical source for every such path. The duplicated A_playful turn-6 state is itself evidence of the missing product-history entry, while the distinct HTTP transcript is retained.\n\nFinal bundle verification checks every included byte hash and the 27 report files; see the local `bundle_verification.json`. Complete source provenance is in REVIEW_MANIFEST.json. Large raw files are included with an explicit per-file limit, not silently omitted."))
    raw_score_turns = [dict(r, score=scores.get((r['conversation'],r['turn']),{})) for r in turns]
    save("scorer_comparison.json", dict(raw=summary(raw_score_turns), adjudicated=total, annotation_adjudications=len(overrides),
        numeric_quality_disagreements=sum(1 for key,item in overrides.items() if key in scores and 'quality' in item['score'] and item['score']['quality'] != scores[key]['quality']),
        root_only_final_turn="B_skeptical:9"))
    # The exact current production sources make the dirty-tree qualification reviewable.
    sources = ["game/api.py", "game/api_turn_support.py", "game/noncombat_resolution.py", "game/social.py", "game/dialogue_authority.py", "game/conversational_continuity.py", "game/conversational_orchestration.py", "game/expressive_dialogue.py", "game/ordinary_semantic_ownership.py", "game/interaction_completion.py", "game/immutable_valid_response.py", "game/interpretation_proposal.py", "game/live_chat_interpretation.py", "game/storage.py", "game/provider_budget.py"]
    support = []
    for p in OUT.rglob("*"):
        relative = p.relative_to(OUT)
        if not p.is_file() or any(x in relative.parts for x in ("preserved_before_tests", "pytest_tmp", "disposable_state", "import_state", "__pycache__")) or p.name in {"handoff_config.json", "bundle_verification.json"}:
            continue
        support.append(dict(path=p.relative_to(ROOT).as_posix(), role="qualification_evidence", why="PR-EG-R4 evaluation, provenance or transcript evidence", behavioral_evidence=False, human_review_required=True))
    for source in sources + ["tools/qualify_pr_eg_r4.py", "tools/report_pr_eg_r4.py", "tests/test_pr_ef_gm_authority.py", "tests/test_pr_du_player_pipeline.py", "tests/helpers/turn_pipeline_http_fixtures.py", "experiments/pr_dq/world.py"]:
        if (ROOT/source).exists():
            support.append(dict(path=source,role="source",why="Evaluated production path or evaluation setup source",human_review_required=True))
    config = dict(campaign_id="pr_eg_r4_conversational_playability_20261017",campaign_name="PR-EG-R4 — Conversational Playability Qualification",campaign_date="2026-10-17",
        purpose="Evaluate integrated adaptive NPC conversation without changing production behavior; stop after R4.",
        executive_summary=executive,objective_status=verdict,
        changes=dict(production=[],validation=["Unchanged relevant regression baseline; adaptive fresh-provider evaluation."],tooling=["Evaluation runner and evidence report builder."],documentation=["27 required reports and CURRENT_REVIEW."],generated_artifacts=["Frozen protocol, transcripts, per-turn state, scores, metrics, audits and source provenance."]),
        testing=dict(focused="No regression expectations changed.",broader=str(regression['counts']),full_suite="Not run; relevant historical family only.",runtime_validation=f"{len(turns)} fresh adaptive production HTTP turns.",model_runtime_boundary="Fresh OpenAI Responses API; separate gpt-4.1 evaluator; exact returned model IDs in logs.",new_regressions=str(regression['new']),pre_existing_failures=f"{len(regression['inherited'])} inherited identities."),
        known_problems=dict(campaign_specific=[audit.get("assessment","Incomplete evidence")],pre_existing=["25 predecessor relevant-suite failures."]),
        decisions_requiring_human_review=["Review R4 evidence and recommended next cycle before proceeding."],
        missing_concepts=["Any broader architecture review requires separate authorization after external review."],
        does_not_prove=["Population-wide reliability or statistical certainty.","Full repository regression success.","Unrestricted improvisation or full process-restart continuity."],
        recommended_next_step=recommendation+" Stop after PR-EG-R4 and await external review.",primary_report=reports[0].relative_to(ROOT).as_posix(),
        supporting_files=support,max_file_bytes=80*1024*1024,warn_bundle_bytes=20*1024*1024,
        self_contained_review_test="Manifest hashes and all 27 reports verified in bundle_verification.json; inherited backup and credentials excluded.")
    save("handoff_config.json",config)
    from tools.build_review_handoff import build_handoff
    # The desktop may keep the existing ZIP open for preview. Build with the
    # established workflow in a fresh directory, then atomically replace each
    # stable handoff file rather than truncating an open ZIP in place.
    import os
    import shutil
    import tempfile
    handoff=ROOT/'handoff'
    with tempfile.TemporaryDirectory(prefix='pr_eg_r4_build_',dir=handoff) as temporary:
        stage=Path(temporary)
        result=build_handoff(config,root=ROOT,output_dir=stage,archive_history=False)
        import zipfile
        # Keep the stable text surfaces byte-identical to their ZIP entries
        # instead of Windows newline translation changing their hashes.
        with zipfile.ZipFile(stage/'CURRENT_REVIEW.zip') as generated:
            for filename in ('CURRENT_REVIEW.md','REVIEW_MANIFEST.json'):
                (stage/filename).write_bytes(generated.read(filename))
        for filename in ('CURRENT_REVIEW.zip','CURRENT_REVIEW.md','REVIEW_MANIFEST.json'):
            os.replace(stage/filename,handoff/filename)
    history=handoff/'history'/config['campaign_id']
    history.mkdir(parents=True,exist_ok=True)
    for source,destination in [('CURRENT_REVIEW.zip','REVIEW.zip'),('CURRENT_REVIEW.md','REVIEW.md'),('REVIEW_MANIFEST.json','REVIEW_MANIFEST.json')]:
        staged=history/(destination+'.new')
        shutil.copyfile(handoff/source,staged)
        os.replace(staged,history/destination)
    import zipfile
    with zipfile.ZipFile(ROOT/"handoff/CURRENT_REVIEW.zip") as archive:
        manifest=json.loads(archive.read("REVIEW_MANIFEST.json"))
        failures=[]
        for item in manifest['included_files']:
            if item.get('sha256') and hashlib.sha256(archive.read(item['bundle_path'])).hexdigest()!=item['sha256']:
                failures.append(item['bundle_path'])
        report_count=sum(1 for name in archive.namelist() if name.startswith('support/artifacts/pr_eg_r4/') and Path(name).name[:2].isdigit() and name.endswith('.md'))
        save("bundle_verification.json",dict(hash_failures=failures,report_count=report_count,files=len(archive.namelist()),zip_bytes=(ROOT/'handoff/CURRENT_REVIEW.zip').stat().st_size,omitted=manifest.get('omitted_artifacts',[])))
        assert not failures and report_count==27
    print(verdict, total, flush=True)


if __name__ == "__main__":
    main()
