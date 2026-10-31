"""Offline evidence normalization and review export; no gameplay/provider calls."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
REPORTS = ROOT / "development/reports/atgb_r1_05"
REPORTS.mkdir(exist_ok=True)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def report(name, content):
    (REPORTS / name).write_text(content.strip() + "\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


rows = []
for label in ("L1", "L2", "L4"):
    p = OUT / label
    before, after, traces = (read(p / name) for name in ("before.json", "after.json", "traces.json"))
    preflight = read(p / "preflight.json")
    assert preflight["classification"] == "ready" and not preflight["failed_assertions"]
    call = next(t for t in traces if t["function"] == "request_interpretation")
    interpretation = json.loads(call["return"]["text"])
    evidence = next(t["return"] for t in traces if t["function"] == "public_conversation_evidence")
    revision = next(t for t in traces if t["function"] == "_pending_revision_decision")
    decision = next(t["return"] for t in traces if t["function"] == "decision_from_interpretation_record")
    response = read(p / "response.json")
    accounting, timing = read(p / "accounting.json"), read(p / "timing.json")
    assert accounting["requests"] == 1 and not accounting["stopped"]
    assert accounting["pending_requests"] == 0 and accounting["total_tokens"] is not None
    assert all(c["max_retries"] == 0 for c in timing["sdk_clients"])
    assert all(before[k] == after[k] for k in ("world", "scene", "character", "combat"))
    assert all(before["session"].get(k) == after["session"].get(k) for k in ("turn_counter", "clocks", "active_scene_id", "current_date"))
    changes = [k for k in set(before["session"]) | set(after["session"]) if before["session"].get(k) != after["session"].get(k)]
    assert set(changes) <= {"conversational_context", "last_saved_at"}
    old_ctx, new_ctx = (x["session"].get("conversational_context") or {} for x in (before, after))
    if label == "L4":
        setup = read(p / "setup_before.json")
        assert all(setup[k] == before[k] for k in ("world", "scene", "character", "combat"))
        assert setup["session"]["turn_counter"] == before["session"]["turn_counter"]
        assert not (setup["session"].get("conversational_context") or {}).get("pending_intention")
        assert old_ctx["pending_intention"]["original_text"] == "I ask one of them what happened."
        assert new_ctx["pending_intention"]["status"] == "pending"
        assert new_ctx["pending_intention"]["revised_text"] == "Instead, make that a question about the lamp."
        assert not new_ctx.get("last_executed_intention")
        assert revision["return"]["reason"] == "pending_intention_revised"
    else:
        assert revision["return"] is None
        assert not new_ctx.get("pending_intention") and not new_ctx.get("last_executed_intention")
    row = dict(trial=label, player_input=read(p / "configuration.json")["input"],
        response=response["gm_output"]["player_facing_text"], raw_interpretation=call["return"]["text"],
        parsed_interpretation=interpretation, available_public_evidence=evidence,
        selected_evidence_refs=interpretation["communication"]["evidence_refs"],
        pending_revision_decision=revision["return"], host_decision=decision,
        routing="PASS", interpretation="PASS", evidence_selection="PASS" if label == "L4" else "FAIL",
        response_adequacy="PASS" if label == "L4" else "FAIL", authority="PASS",
        interpretation_qualification=("Revision recognized; topic/target conflation in ASK target_ref remains a semantic limitation; no action executed."
            if label == "L4" else "Subject change recognized, but redundant clarification posture is incorrect; passing this narrow criterion is not full interpretation adequacy."),
        session_keys_changed=sorted(changes), state_integrity=read(p / "state_integrity.json"),
        provider_accounting=accounting, timing=timing,
        measured_provider_model=accounting["records"][0]["model"],
        source_artifact_path=(p / "response.json").relative_to(ROOT).as_posix())
    rows.append(row)
    normalized = {k: v for k, v in row.items() if k != "provider_accounting"}
    write(p / "normalized.json", normalized)
    prior = (read(p / "setup.json")["prior_gm"] if label != "L4" else
             read(p / "setup_response.json")["gm_output"]["player_facing_text"])
    (p / "transcript.md").write_text(f"# {label} — ATGB-R1-05\n\nPrior AI-DM: {prior}\n\nPlayer: {row['player_input']}\n\nAI-DM: {row['response']}\n\nLive model: {row['measured_provider_model']}. One admission; zero retries.\n", encoding="utf-8")
write(OUT / "normalized_results.json", rows)

accounting = dict(application_admissions=sum(r["provider_accounting"]["requests"] for r in rows),
    successful_provider_responses=3, failed_dispatches=0, completed_trials=3,
    input_tokens=sum(r["provider_accounting"]["input_tokens"] for r in rows),
    output_tokens=sum(r["provider_accounting"]["output_tokens"] for r in rows),
    total_tokens=sum(r["provider_accounting"]["total_tokens"] for r in rows),
    sdk_transport_retries=0, application_retries=0, automatic_trial_retries=0, continuations=0,
    hard_application_admission_limit=6, hard_per_trial_limit=2,
    cost={"status": "unavailable", "reason": "no configured price table; no billing claim"},
    budget_compliant=True, provider="OpenAI Responses", configured_model="gpt-4.1-mini",
    returned_model="gpt-4.1-mini-2025-04-14", unknown_usage=False,
    offline_previews=2, preview_provider_admissions=0, rejected_launches=1,
    rejection_provider_admissions=0)
assert accounting["total_tokens"] == 6475 and accounting["application_admissions"] == 3
write(OUT / "provider_accounting.json", accounting)

write(OUT / "authorization_and_launches.json", {
    "initial_launch": "exec_command rejected before CreateProcess; zero admissions, no gameplay changes",
    "auto_review_reason": "Although L1 live execution is explicitly authorized, it sends private campaign context and player data to an unspecified external provider; the destination and complete payload are not explicitly authorized for sensitive egress.",
    "user_question": "Do you approve sending the reconstructed frozen S08 context and the R1-04 synthetic pending-ASK control (including their authored scene, public NPC facts and preceding conversation) to OpenAI's Responses API at https://api.openai.com/v1/responses using gpt-4.1-mini, solely for L1, L2 and L4 within the existing six-admission limit?",
    "user_reply": "Approve this bounded transfer",
    "subsequent_launches": "L1, L2, L4 explicitly approved through escalated exec; completed exit 0",
    "workaround": False, "trial_retries": 0,
    "offline_preview_failure": ["isolated_store", "fixture_matches_store"],
    "offline_preview_correction": "New runner restores active-player directory environment after isolated storage import. Readiness guard still validates imported store and exact loaded snapshots. Existing readiness/production unchanged.",
    "preview_classification": "local structural preparation only; neither preview counts as a live trial"})

table = "| Trial | Routing | Subject/revision recognition | Evidence | Response | Authority |\n| --- | --- | --- | --- | --- | --- |\n" + "\n".join(
    f"| {r['trial']} | PASS | PASS (qualified) | {r['evidence_selection']} | {r['response_adequacy']} | PASS |" for r in rows)

report("01_execution_readiness.md", """
# 01 — Execution Readiness

ATGB-R1-05, 2026-10-19. Controlled validation; production implementation authority NONE.
HEAD b012c3d7e5887fdfb09d10bb9cc0f0220de09df9. Extensive pre-existing dirty/untracked
work retained. Entry status and hashes are in artifacts/atgb/atgb_r1_05/.

Read Constitution, canonical docs/NEXT_SESSION.md, validation evidence standard,
product-realization validation, review standard and completed R1-01/02/03/04 evidence.
support/docs/NEXT_SESSION.md does not exist in this checkout; prior passes establish
that it is the review-bundle spelling. Used canonical docs/NEXT_SESSION.md.

All 3,996 R1-04 entry hashes match before execution. R1-02 orchestration and R1-04
readiness/control remain present. No material baseline discrepancy or experimental
integration. Frozen frontier-gate-v1 manifest also passes load_baseline verification.
Ten current import/mode safety tests pass (readiness_tests.xml); R1-04's prior
167-test result is preserved historical evidence, not a new full run. No full suite.

Each live trial runs in a new process, new exclusive store and durable ledger.
L1/L2 independently copy the same preserved pre-S08.2 reconstruction: exact S08.1
delivered log, authored scene, world, character and combat, with fresh runtime IDs.
No provider call recreates S08.1. Original intermediate historical session was not
retained: exact experimental equivalence is not claimed. No cross-trial state/cache
or environment mutations. L4 uses readiness.seed_control, clears inherited pending
state and creates pending ASK through production chat with the R1-04 setup stub.
Only the measured revision uses the live model. No tests or R1-03 runner imported.

All three live preflight.json files say ready: requested/effective live true,
provider configured, default/high-precision/escalation model gpt-4.1-mini, matching
import flags and store, zero used admissions, ledger initialized, max two admissions,
positive token caps, application retries disabled, startup probe skipped; L4 pending
checks pass. Experimental planning/candidate flags absent after configuration load.
SDK constructor wrapper enforces max_retries=0 and records each actual client.
No semantic/prompt/model changes. API callable is used directly; HTTP/browser not tested.
Input/output/total token ceilings are 16000/2000/18000 per trial; these are ceilings,
not measured usage or a price budget. No configured price table. Provider reachability
was unprobed before the authorized calls. Global accounting source-manifest staleness
from R1-02 persists; no claim that the global stale-source preflight passes.

One initial external-transfer auto-review rejection prevented process creation.
User explicitly approved the named OpenAI destination, context categories, model
and bounded trials before approved live execution. No rejection bypass occurred.
Two offline payload previews cost zero admissions: first failed closed on isolated_store
and fixture_matches_store because the new runner's ASHEN_DATA_DIR identified its own
store as active player state. Callback never ran; snapshots unchanged. Only the new
runner's binding convention was corrected, then a fresh offline preview passed and
captured the payload. Neither preview is a live trial or trial retry. All evidence retained.
""")

details = []
for r in rows:
    label = r["trial"]
    details.append(f"""
## {label}

Player: {r['player_input']}

AI-DM: {r['response']}

Communication: {json.dumps(r['parsed_interpretation']['communication'], ensure_ascii=False)}
Legacy mode: {r['parsed_interpretation']['communication_mode']}; unresolved references:
{json.dumps(r['parsed_interpretation']['references']['unresolved_references'])}.
Host reason: {r['host_decision']['reason']}; revision gate:
{'abstains (null)' if label != 'L4' else 'pending_intention_revised'}.
Interpretation qualification: {r['interpretation_qualification']}

Evidence selection: {r['evidence_selection']}. Response adequacy: {r['response_adequacy']}.
Gameplay stores, turn, date, clocks and scene unchanged; only conversation memory,
save metadata and log change. Authority PASS for this execution.
Exact context, raw/parsed records, selected/public evidence, plan and final output:
artifacts/atgb/atgb_r1_05/{label}/normalized.json, traces.json, before.json and after.json.
""")
report("02_live_trial_results.md", f"""
# 02 — Live Trial Results

Three valid live measured trials; no L3, replacement trial or automatic retry.
Judgments are provisional AI-assisted analysis, UNREVIEWED by an authenticated human.
Subject recognition alone is graded separately from useful interpretation and response.

{table}

L1/L2 context: frontier_gate, no active NPC interlocutor, no pending or executed
intention. Active topic is the visible scene; preceding player asked
“What's in front of me right now?” The exact delivered description includes the gate
serjeant, tavern runner, watchers and refugees. visible:1/2/3 and reply:0 are supplied
to the model but none selected. Model recognizes the people/weather contrast, chooses
CLARIFICATION and asks confirmation despite sufficient context and no unresolved refs.
Host consults the repaired gate, abstains, then emits the supplied clarification question.

L4 context: waystation_courtyard; ambiguous ASK generated from
“I ask one of them what happened.” Choices Sergeant Mara / Corporal Bren; original
question remains unexecuted. Live interpretation recognizes reformulation and selects
visible:0 (lantern). It also describes changing the question target from person to lamp,
using courtyard_lantern as ASK target_ref. That topic/recipient conflation is retained
as a limitation. Host uses actual pending ASK and explicit revision cue, writes only
revised_text, preserves original NPC choices and keeps status pending. No action runs.
This supports the narrow revision control, not later execution correctness.

{''.join(details)}
""")

report("03_execution_traces.md", """
# 03 — Execution Traces

Each L1/L2/L4 directory contains full response.json, before/after snapshots, preflight,
configuration, durable provider_usage.jsonl, accounting, timing, transcript.md,
observational traces.json and normalized.json. Root normalized_results.json joins
all three without changing raw artifacts. L4 also retains setup_before.json and
setup_response.json establishing production-created pending provenance. Offline
preview directories are explicitly separate and are not included in live totals.

Existing Python profiling records function returns and an allowlisted set of locals:
public_conversation_evidence; request_interpretation (complete production messages,
raw response and usage); interpret_production_turn (parsed/adapted record, disposition,
selected evidence); assess_addressee_grounding; _pending_revision_decision;
_communication_decision; decision_from_interpretation_record. Source lines and
host decision envelope preserve proposed operations, targets, execution policy,
context updates, authorization when available and player-facing response plan.
No production instrumentation or decision override was added. The SDK constructor
wrapper changes only transport retry count. The L4 setup stub is restored before
preflight/measured chat and explicitly recorded in configuration.

L1/L2: public evidence -> live request -> clarification_required /
NEEDS_CLARIFICATION -> API re-evaluates the existing record -> repaired revision
gate returns null -> communication_before_execution -> redundant model question.
Unlike the prior R1-03 report's L3 summary, current traces directly show the gate
is consulted after the blocked live outcome. Do not transfer its path claim blindly.
L4: same blocked-outcome adaptation seam -> pending_intention_revised -> host
acknowledgment and retained ambiguity. No bind call observed. A planning_decision
hook returns null; no experimental semantic plan is substituted.

Gaps: no exhaustive rejected-evidence reasons (no such model rationale supplied),
no hidden chain of thought, no separate comprehensive disclosure-check log, no
provider billing invoice/price table, no transport-level packet trace, no HTTP/browser
capture. No downstream narration input exists: each final answer is host-owned and
recorded in its decision and response metadata. Absence of a field is not a PASS.
""")

report("04_historical_comparison.md", """
# 04 — Historical Comparison

Frozen source: artifacts/atgb/atgb_03c/S08/transcript.md and result.json, S08.2.

Player: I meant the people, not the weather.

Original AI-DM: I don't have an unexecuted intention to revise. What do you want to change?

| Dimension | Historical baseline | L1 and L2 repaired live behavior |
| --- | --- | --- |
| Mechanical revision routing | Incorrect, no_pending_intention | PASS: gate consulted and abstains; communication_before_execution |
| Subject recognition | Raw interpretation unavailable | People/weather contrast recognized in both raw records |
| Evidence selection | Not established | FAIL: empty refs despite visible:1/2/3 and reply:0 |
| Response adequacy | Failed | FAIL: redundant confirmation, no description of people |
| Authority | No confirmed violation | Gameplay domains unchanged; narrow PASS |
| Performance | One interpretation; 2004 input, 210 output, 2214 total; host telemetry 1850 ms | One interpretation each; L1 2215 total / 4199.838 ms wall; L2 2214 / 3730.975 ms wall |

Historical and returned current model both gpt-4.1-mini-2025-04-14; configured
gpt-4.1-mini. Current temperature 0 and output cap 320. L1/L2 request messages are
identical to each other; scenario semantic context and preceding text match the
preserved reconstruction. Original intermediate session is unavailable, runtime IDs
and timestamps are fresh, current memory construction is inherited from the
reviewed reconstruction, SDK retry bounds were not established historically and
latency clocks differ. No exact experimental equivalence or repair-attributable
latency/cost delta is claimed. Historical provider ledger is packaged separately.

Routing improvement is now directly observed in the original wording twice.
Useful conversational improvement is not demonstrated: the mechanical demand is
replaced by a different inadequate clarification. No broad benchmark score, unseen
generalization, or historical regrading follows. Original transcript/judgments intact.
""")

report("05_failure_localization.md", """
# 05 — Failure Localization

Primary development failure class for observed L1/L2 inadequacy: semantic.

L1 and L2, independently: earliest demonstrably incorrect decision is the live
model's clarification posture and empty evidence selection, observed together in
request_interpretation raw JSON (game/live_chat_interpretation.py:214). The subject
summary correctly distinguishes people from weather, yet communication_mode and
purpose are CLARIFICATION, evidence_refs is empty, unresolved_references is empty,
and clarification_question merely restates the player's already explicit correction.
The same request contains visible:1/2/3 describing people and the full preceding
reply:0. Thus context absence is not supported by this trace.

High confidence: these observed choices prevent a meaningful answer. No ordering
inside the model between posture and evidence selection is inferable. Adapter
NEEDS_CLARIFICATION and interpret_production_turn's clarification_required return
(game/live_chat_interpretation.py:500) follow. API at game/api.py:6526 passes the
record to decision_from_interpretation_record; _pending_revision_decision at
game/conversational_orchestration.py:391 returns null; _communication_decision
at :461 uses the supplied question. Final realization preserves the deficient plan.
No mechanical regression, bind rejection, disclosure rejection, provider failure,
or generic gameplay fallback explains these new outcomes.

R1-03 L3 comparison: same observed semantic mechanism — correct people subject,
redundant clarification question, no selected evidence despite supplied people facts.
Use its preserved trace.json, response.json and report 05. Wording differs and that
single paraphrase is not independent generalization. Current paths add direct evidence
of the repaired gate's abstention; prior report's claim that its gate was not reached
is not silently extended to these traces. No historical report is rewritten.

Strong explanation: a clarification disposition with no selected facts yields the
observed redundant host answer. Unverified hypothesis: schema's pending-intention
description of CORRECTION biases the model; no prompt intervention or alternate
model was tested. No causal claim that all correction failures share this mechanism.

L4 has no failed required control criterion. Its raw ASK target_ref points to the
lamp rather than an unresolved NPC and correction.note says person-to-lamp target
change. That semantic conflation is directly observed (high confidence); whether it
would impair later authorized execution is unverified. Host preserves choices and
does not execute. No additional scenario or continuation was run to test it.

Preparation-only evaluation issue: offline preview's store self-protection failure
arose from the new runner's environment binding, before its callback, not production
semantics. Current readiness.py preflight/assert_safe_benchmark_data_dir enforced the
guard. Scope-limited runner correction and failed/ready artifacts are retained.
No production repair is implemented or proposed as part of this pass.
""")

report("06_authority_and_state_integrity.md", """
# 06 — Authority and State Integrity

All measured trials preserve world, character, combat, active scene, simulation
date, turn counter and clocks exactly. World equality includes factions and event
log; character equality covers inventory. Session changes are confined to
conversational_context and last_saved_at; logs append the measured exchange.
state_integrity.json and full before.json/after.json are included per trial.

L1/L2: no pending or executed intention before or after; no intention fabricated,
cleared or rolled back. No gameplay resolution or time advancement. Final questions
repeat only already-public people/weather concepts. Narrow authority PASS.

L4: setup_before shows cleared pending context. Production setup response asks which
NPC; before.json shows the new ambiguous ASK, two valid scene-local choices, status
pending and no last_executed_intention. Setup leaves world/scene/character/combat and
turn unchanged. Preflight pending checks pass. Live measured step copies the actual
pending record, adds revised_text, preserves original question/scene/operation/choices,
keeps pending status, and mirrors it into pending_clarification. No social resolution,
execution, rollback or time advancement. The response requests the still-unresolved
recipient. Narrow authority PASS; no later execution claim.

Information disclosure: available public evidence and selected refs are preserved.
L1/L2 select none; L4 selects the public lantern passage but final host speech only
acknowledges revision and names the pending choices. No restricted fact appears in
the observed final outputs. The full broader disclosure mechanism was not exercised
exhaustively; unavailable internal audit fields are identified in report 03.

Canonical data, production code, frozen ATGB corpus/captures/assessments, fixtures
and experiments match their entry hashes. No candidate merged. Preview setup writes
are confined to new disposable stores; failed preflight does not change its snapshot;
corrected offline payload capture appends only a preview log and advances no gameplay.
No unauthorized gameplay-state mutation observed in this pass. This is distinct from
R1-03's preserved invalid L4 mutation; that historical result is not overwritten.
""")

cost_table = "| Trial | Admissions | Responses | Failed | Input | Output | Total | Wall ms | Dispatch ms |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n" + "\n".join(
    f"| {r['trial']} | 1 | 1 | 0 | {r['provider_accounting']['input_tokens']} | {r['provider_accounting']['output_tokens']} | {r['provider_accounting']['total_tokens']} | {r['timing']['end_to_end_ms']} | {r['provider_accounting']['records'][0]['latency_ms']} |" for r in rows)
report("07_provider_accounting.md", f"""
# 07 — Provider Accounting

{cost_table}

Measured total: 3 application admissions/dispatches, 3 successful responses, zero
failed dispatches, 5845 input + 630 output = 6475 tokens. All returned usage is
consistent, no pending attempt or unknown usage. Durable admission-before-dispatch
events and response IDs retained in each provider_usage.jsonl/accounting.json.
Configured OpenAI Responses gpt-4.1-mini; returned gpt-4.1-mini-2025-04-14 for all.

Per trial: one actual SDK client, max_retries 0; application retry flag disabled;
no automatic trial retry, model escalation, continuation or narration admission.
Three completed trials meet maximum three; each 1/2 admissions, aggregate 3/6.
Unused allowance is not spent. L4 setup uses stubbed interpretation at zero admissions;
the measured revision is actual live interpretation. Two offline previews and one
rejected pre-process launch make no admissions and do not count as completed trials.
No failed provider call or unknown billing is hidden in the totals.

Input/output/total tokens are provider measurements; preflight token estimates are
separate ceiling checks. Cost unavailable: no configured price table or billing
invoice; no invented dollar figure. End-to-end wall latency includes preflight,
provider construction, interpretation and host response; L4 deterministic setup is
outside measured revision timing. Dispatch latency is measured by production budget
around SDK invocation. Historical host timings are not an equivalent baseline, so
no performance success or repair-attributable cost/latency improvement is graded.

The first launch was denied by automatic approval review before execution due to
external campaign-data transfer authorization. User then explicitly approved the
named destination, context and three trials. Accepted escalated execution followed;
no bypass or hidden network retry. See authorization_and_launches.json.
""")

report("08_final_verdict.md", """
# 08 — Final Verdict

**B — Partial. Outcome B: routing improved, conversation remains inadequate.**

L1/L2 original wording now reaches the repaired host gate and avoids mechanical
revision handling. Both recognize the people/weather contrast but select no supplied
people evidence and ask unnecessary confirmation. Response adequacy FAIL twice.
The earliest supported semantic failure is live interpretation's clarification
posture/empty evidence selection, matching the observed R1-03 L3 mechanism.

L4 supplies trustworthy live evidence of the narrow legitimate-revision control:
production-created pending ASK, successful mandatory preflight, live revision
interpretation, actual pending_intention_revised route, pending record retained,
no execution and no gameplay advancement. Model topic/recipient conflation remains
a limitation; future execution correctness is not established.

All three trials valid and independently isolated. 3/6 total admissions, 1/2 each;
three responses; zero failed dispatches, retries or continuations; 6475 measured
tokens; cost unavailable. No broad conversational reliability, full-suite green,
independent generalization or full ATGB benchmark score. Provisional AI-assisted
judgments remain UNREVIEWED; external review required.

Single bounded recommended ATGB-R1-06 scope: offline causal investigation of the
captured L1/L2 interpretation/evidence-selection defect, compared with preserved
R1-03 L3, to define a reviewable semantic contract and repair proposal. Reuse saved
payloads/records and scenario-independent authored controls; no live calls, prompt
optimization, production implementation or PR-EG integration without new authority.
Do not implement the recommendation in R1-05.

Confirmed by evidence: production code unchanged; frozen ATGB baseline and judgments
unchanged; no experimental candidate merged; provider limits respected; no unauthorized
gameplay state mutation; credentials/secrets excluded from selected review artifacts.
No commit/push. Stop after the review ZIP; await external review before ATGB-R1-06.
""")

index = ROOT / "development/reports/atgb_r1_05_controlled_live_validation.md"
index.write_text("# ATGB-R1-05 — Controlled Live Validation Continuation\n\n2026-10-19. **B — Partial / Outcome B.** Routing repair observed in two original-wording live trials; both responses inadequate. Legitimate pending ASK revision preserved in L4. Three admissions, zero retries, 6475 measured tokens. No production edits.\n\n" + "\n".join(f"- [{p.stem.replace('_', ' ')}](atgb_r1_05/{p.name})" for p in sorted(REPORTS.glob('*.md'))) + "\n\nRaw/normalized evidence: artifacts/atgb/atgb_r1_05/. Behavioral packet: artifacts/validation_evidence/atgb_r1_05/. Stop for external review before R1-06.\n", encoding="utf-8")

from tools.validation_evidence import build_packet, write_packet, validate_packet
examples = []
for r in rows:
    examples.append(dict(example_id="ATGB-R1-05-" + r["trial"], scenario_run_id=r["trial"], turn_index=2,
        player_input=r["player_input"], player_input_classification=(["synthetic_positive_control", "boundary_case"] if r["trial"] == "L4" else ["representative_player_behavior", "boundary_case"]),
        exact_gm_output=r["response"], runtime_validity={"status": "VALID", "preflight": "ready", "live_model": True},
        source_artifact_path=r["source_artifact_path"], human_review={"status": "UNREVIEWED", "rationale": "AI-assisted provisional criteria analysis; no authenticated human adjudication."},
        relevant_prior_context=r["available_public_evidence"], simulated_player_rationale="User-specified fixed reproduction/control; no generated player.",
        semantic_result="PASS" if r["trial"] == "L4" else "FAIL",
        semantic_result_basis="Provisional AI-assisted analysis of explicit pass criteria; not the playability evaluator or human scoring.",
        mandatory_gates={k: {"status": r[k]} for k in ("routing", "interpretation", "evidence_selection", "response_adequacy", "authority")},
        diagnostic_result={"status": "NOT_RUN", "reason": "No playability scorer invoked"},
        automated_evaluation={"status": "NOT_RUN", "criteria_analysis": {k: r[k] for k in ("routing", "interpretation", "evidence_selection", "response_adequacy", "authority")}},
        historical_result="Original S08.2 response inadequate" if r["trial"] != "L4" else "R1-04 deterministic control only",
        final_emission_metadata=read(ROOT / r["source_artifact_path"])["gm_output"].get("metadata"),
        continuation_decision={"action": "STOP", "reason": "Specified trial complete; no automatic continuation"},
        evaluator_disagreement={"present": False, "history": [], "calibration_reference": None},
        interpretation_qualification=r["interpretation_qualification"],
        unexpected_behavior="Model revision target/topic conflation retained; host does not execute" if r["trial"] == "L4" else None))
packet = build_packet(campaign=dict(campaign_id="ATGB-R1-05", what_was_tested="L1/L2 original S08.2 correction and L4 pending ASK revision only",
    runtime_path="game.api.chat(ChatRequest) with readiness.guarded_trial; direct callable, live OpenAI interpretation",
    gm_boundary="Production host orchestration and existing final-emission boundary", player_input_mode="Three exact user-specified inputs",
    run_count=3, turn_count=3, automated_conclusion="AI-assisted B — Partial; authenticated human review pending"),
    claim_types=["runtime_evidence", "semantic_behavioral_evidence"], examples=examples, missing_concepts=[],
    limitations=["Narrow three-trial validation, no full benchmark score or broad conversational reliability.", "No authenticated human scoring; provisional criteria analysis only.", "L4 topic/recipient conflation and later execution untested.", "Cost unavailable; no controlled performance baseline."])
assert not validate_packet(packet)
packet_dir = ROOT / "artifacts/validation_evidence/atgb_r1_05"
write_packet(packet_dir, packet)

# Preserve prior orientation before the required concise continuity update.
next_path = ROOT / "docs/NEXT_SESSION.md"
backup = OUT / "NEXT_SESSION_before.md"
if not backup.exists():
    shutil.copyfile(next_path, backup)
old = backup.read_text(encoding="utf-8")
old = old.replace("Updated 2026-10-19 / ATGB-R1-04.", "Updated 2026-10-19 / ATGB-R1-05.")
start = old.index("ATGB-R1-04 validation-readiness recovery completed:")
end = old.index("### Prior R1-03 evidence", start)
new = """ATGB-R1-05 controlled live continuation completed: **B — Partial / Outcome B**.
Report: `development/reports/atgb_r1_05_controlled_live_validation.md`; eight reports
under `development/reports/atgb_r1_05/`, raw/normalized traces and before/after state
under `artifacts/atgb/atgb_r1_05/`, behavioral packet under
`artifacts/validation_evidence/atgb_r1_05/`. Review: `handoff/CURRENT_REVIEW.zip`
and timestamped CURRENT_REVIEW(20261019-...).zip.

L1/L2 original correction now reaches the repaired revision gate, which abstains.
Both live responses still ask redundant confirmation and select no people facts;
earliest semantic failure is model clarification posture/empty evidence selection,
matching R1-03 L3. L4 valid live revision of production-created ambiguous ASK keeps
status pending and does not execute. Its model topic/recipient conflation remains
a limitation. World/character/combat/scene/time/turn/clocks unchanged in all trials.
Three responses, 3/6 admissions (1/2 each), zero retries/continuations, 6475 measured
tokens; cost unavailable. Configured gpt-4.1-mini, returned dated 2025-04-14 model.
Ten current import/mode safety tests pass; no full suite. All 3,996 predecessor
entry hashes match. Production/prompts/models/frozen baseline/experiments unchanged.
One launch approval rejection resolved by explicit user transfer approval; two local
payload previews (first fail-closed store-binding check, corrected runner passes)
made no admissions. Measured trials all preflight-ready and independently isolated.

R1-04 readiness/control remains unchanged and its 167-test deterministic result is
historical evidence. The new R1-05 runner uses its gate/control; old R1-03 runner
remains prohibited. Global source-manifest staleness and HTTP coverage limitations
persist. Judgments are provisional AI-assisted, not authenticated human scoring.

Await external review before ATGB-R1-06. Recommend only an offline causal
investigation/contract proposal for the saved L1/L2 evidence-selection and redundant
clarification defect against R1-03 L3. No semantic implementation, prompt optimization,
live calls or PR-EG integration authorized by this recommendation.

"""
old = old[:start] + new + old[end:]
old = old.replace("R1-04 recovery is now completed without live calls;\noriginal/control live trials remain deferred pending R1-05 external review and\nexplicit live authorization. No semantic repair is authorized.", "R1-04 recovery completed without live calls; R1-05 has now supplied the bounded\noriginal/control live evidence above. No semantic repair is authorized.")
tail = old.index("Stop for external review of ATGB-R1-04.")
old = old[:tail] + """Stop for external review of ATGB-R1-05. This pass changed validation-runner,
documentation and generated evidence/export files only. No production or frozen
baseline edit, experimental integration, commit or push. Do not begin ATGB-R1-06
or make further live calls without new authority.
"""
next_path.write_text(old, encoding="utf-8")

entry = read(OUT / "entry_hashes.json")
prior = read(ROOT / "artifacts/atgb/atgb_r1_04/entry_hashes.json")
assert all(Path(ROOT / p).is_file() and digest(ROOT / p) == v for p, v in entry.items())
assert all(Path(ROOT / p).is_file() and digest(ROOT / p) == v for p, v in prior.items())
write(OUT / "integrity.json", dict(entry_files_verified=len(entry), changed=[],
    predecessor_files_verified=len(prior), predecessor_changed=[], production_code_unchanged=True,
    frozen_baseline_unchanged=True, experiments_integrated=False, canonical_player_data_unchanged=True,
    unauthorized_gameplay_mutations=False, provider_limits_respected=True))
(OUT / "repository_status_after.txt").write_text(subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True), encoding="utf-8")
write(OUT / "commands.json", [
    {"command": ".venv/Scripts/python.exe -m pytest tests/test_atgb_r1_04_readiness.py -k 'fresh_import_safety or sequential_modes_and_failure_restoration or failed_import_restores_configuration' -q --tb=short --basetemp=development/tmp/atgb_r1_05 --junitxml=artifacts/atgb/atgb_r1_05/readiness_tests.xml", "exit_code": 0, "passed": 10},
    {"command": ".venv/Scripts/python.exe artifacts/atgb/atgb_r1_05/run_trial.py L1", "outcome": "initial launch rejected before process creation; later explicit user approval; approved live launch exit 0"},
    {"command": ".venv/Scripts/python.exe artifacts/atgb/atgb_r1_05/run_trial.py L1 --preview", "outcome": "two local-only previews in distinct directories; initial failed closed, corrected ready; zero admissions"},
    *[{"command": f".venv/Scripts/python.exe artifacts/atgb/atgb_r1_05/run_trial.py {label}", "exit_code": 0, "admissions": 1, "sdk_retries": 0} for label in ("L2", "L4")],
    {"command": ".venv/Scripts/python.exe artifacts/atgb/atgb_r1_05/package_review.py", "purpose": "offline evidence/report generation and review verification; no provider execution"}])

from tools.build_review_handoff import build_handoff
config = read(ROOT / "data/validation/review_handoffs/atgb_r1_04_validation_readiness_recovery.json")
config.update(campaign_id="atgb_r1_05_controlled_live_validation", campaign_name="ATGB-R1-05 Controlled Live Validation Continuation",
    campaign_date="2026-10-19", purpose="Three authorized live trials only; no production implementation authority.",
    objective_status="B — PARTIAL; EXTERNAL REVIEW REQUIRED",
    executive_summary="Two exact S08.2 trials avoid mechanical misrouting but still ask redundant confirmation with empty evidence. L4 preserves legitimate pending revision. Three successful responses, 3/6 admissions, zero retries, 6475 tokens; gameplay unchanged.",
    changes={"production": ["None; all production entry hashes unchanged."], "validation": ["Three specified live trials; ten current import/mode safety tests."], "tooling": ["Evidence-local isolated runner using unchanged R1-04 gate/control; offline packaging script."], "documentation": ["Eight reports, index, canonical NEXT_SESSION."], "generated_artifacts": ["Complete snapshots, raw/normalized traces, transcripts, ledger/accounting, behavioral packet, verified review ZIP."]},
    testing={"focused": "10 import/mode safety tests passed; three live preflights ready.", "broader": "Not rerun; prior 167-test R1-04 evidence preserved.", "full_suite": "Not run.", "runtime_validation": "L1/L2/L4 direct production chat; live interpretation in each measured step; L4 initial setup stub only.", "model_runtime_boundary": "OpenAI Responses gpt-4.1-mini -> gpt-4.1-mini-2025-04-14; temperature 0/output cap 320; no SDK retries.", "new_regressions": "No observed authority or revision-routing regression in these three trials.", "pre_existing_failures": "L1/L2 semantic failure matches R1-03 L3; global accounting manifest stale; HTTP not covered."},
    known_problems={"campaign_specific": ["L1/L2 subject recognized but evidence empty and response redundant.", "L4 model topic/recipient conflation retained; later execution untested."], "pre_existing": ["Dirty worktree, unattested human assessment, stale global accounting manifest and historical HTTP coverage limitations."]},
    decisions_requiring_human_review=["Review provisional B verdict and authorize only the proposed bounded offline ATGB-R1-06 investigation if desired. No follow-on work begins automatically."],
    missing_concepts=["No new gameplay owner or binding architecture proposed."],
    does_not_prove=["Broad conversational reliability, independent generalization, full ATGB benchmark score, full-suite green, later L4 execution correctness, price/billing or performance improvement."],
    recommended_next_step="External review, then separately authorized offline causal investigation/contract proposal for saved L1/L2 interpretation/evidence defect against R1-03 L3. No implementation or further live calls now.",
    primary_report=index.relative_to(ROOT).as_posix(), evidence_packets=[packet_dir.relative_to(ROOT).as_posix()],
    self_contained_review_test="All eight reports, exact transcripts, raw/normalized traces, snapshots, provider ledgers, source references and integrity hashes; ZIP CRC/source-hash/secret scan.",
    configuration_source="artifacts/atgb/atgb_r1_05/review_config.json")
supports = list(REPORTS.glob("*.md"))
supports += [p for p in OUT.rglob("*") if p.is_file() and p.suffix in {".json", ".jsonl", ".md", ".xml", ".txt", ".py"}
    and not any(part in p.parts for part in ("store", "control", "review_export", "__pycache__"))
    and p.name not in {"review_config.json", "package_result.json"}]
supports += [ROOT / p for p in (
    "docs/NEXT_SESSION.md", "docs/DEVELOPMENT_CONSTITUTION.md", "docs/validation_evidence_standard.md", "docs/product_realization_validation.md",
    "tools/atgb/readiness.py", "tools/atgb/isolation.py", "game/conversational_orchestration.py", "game/live_chat_interpretation.py", "game/provider_budget.py", "game/api.py",
    "tests/test_atgb_r1_04_readiness.py", "tests/fixtures/pr_ef_r4_holdouts.json",
    "development/reports/atgb_r1_01_s08_2_causal_trace.md", "development/reports/atgb_r1_02/08_final_verdict.md",
    "development/reports/atgb_r1_03/05_failure_localization.md", "development/reports/atgb_r1_04/08_final_verdict.md",
    "artifacts/atgb/atgb_r1_03/L3/trace.json", "artifacts/atgb/atgb_r1_03/L3/response.json", "artifacts/atgb/atgb_r1_03/L3/setup.json",
    "artifacts/atgb/atgb_03c/S08/transcript.md", "artifacts/atgb/atgb_03c/S08/result.json", "artifacts/atgb/atgb_03c/S08/provider_usage.jsonl")]
config["supporting_files"] = [dict(path=p.relative_to(ROOT).as_posix(), role="execution_evidence", why="R1-05 direct execution or read-only comparison provenance.", behavioral_evidence=True, human_review_required=True) for p in sorted(set(supports))]
write(OUT / "review_config.json", config)
now = datetime.now(timezone.utc)
result = build_handoff(config, root=ROOT, output_dir=OUT / "review_export", generated_at=now.isoformat())
zip_path = Path(result["zip_path"])
with zipfile.ZipFile(zip_path) as archive:
    assert archive.testzip() is None
    assert sum("/development/reports/atgb_r1_05/" in n and n.endswith(".md") for n in archive.namelist()) == 8
    manifest = json.loads(archive.read("REVIEW_MANIFEST.json"))
    for row in manifest["included_files"]:
        if row.get("canonical_source_path"):
            assert hashlib.sha256(archive.read(row["bundle_path"])).hexdigest() == row["sha256"]
    for name in archive.namelist():
        body = archive.read(name)
        assert not re.search(rb"sk-[A-Za-z0-9_-]{16,}|Bearer\s+[A-Za-z0-9._-]{12,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", body), name
        assert not any(part in {".env", ".git", ".venv"} for part in Path(name).parts)
stamp = now.astimezone(timezone(timedelta(hours=-4))).strftime("%Y%m%d-%H%M%S")
dest = ROOT / "handoff" / f"CURRENT_REVIEW({stamp}).zip"
shutil.copyfile(zip_path, dest)
# Prior R1-04 export is already preserved under its evidence owner.
for name in ("CURRENT_REVIEW.md", "REVIEW_MANIFEST.json", "CURRENT_REVIEW.zip"):
    staged = ROOT / "handoff" / (name + ".r1_05_pending")
    shutil.copyfile(OUT / "review_export" / name, staged)
    staged.replace(ROOT / "handoff" / name)
write(OUT / "package_result.json", dict(zip=str(dest), zip_sha256=digest(dest), file_count=result["file_count"],
    zip_bytes=dest.stat().st_size, verdict="B — Partial", provider_admissions=3, total_tokens=6475,
    zip_crc="PASS", source_hash_verification="PASS", secret_scan="PASS", stop="Await external review before ATGB-R1-06."))
print(json.dumps(read(OUT / "package_result.json"), indent=2))
