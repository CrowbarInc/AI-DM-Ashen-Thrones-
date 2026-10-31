"""Package observed ATGB-03 execution without scoring or repairing the product."""
import collections
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.atgb.fixtures import load_corpus
from tools.atgb.worksheet import build_worksheet, render_worksheet

OUT = Path(__file__).parent
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

history = OUT / 'pre_execution_blocked'
history.mkdir(exist_ok=True)
for name in ['execution_blocker.json', 'scenario_status.json', 'validation_results.json', 'bundle_verification.json']:
    if (OUT / name).exists() and not (history / name).exists():
        shutil.copyfile(OUT / name, history / name)
for name, source in [('report.md', ROOT / 'development/reports/atgb_03_initial_live_baseline.md'), ('review_config.json', ROOT / 'data/validation/review_handoffs/atgb_03_initial_live_baseline.json')]:
    if not (history / name).exists():
        shutil.copyfile(source, history / name)

corpus = load_corpus(ROOT)
provenance = read(OUT / 'configuration_and_provenance.json')
results = {p.parent.name: read(p) for p in sorted(OUT.glob('S*/result.json'))}
turns = [t for result in results.values() for t in result['turns']]
providers = []
scenario_status = []
for scenario in corpus['scenarios']:
    sid = scenario['scenario_id']
    result = results.get(sid)
    target = OUT / sid
    usage_path = target / 'provider_usage.jsonl'
    usage = [json.loads(line) for line in usage_path.read_text().splitlines()] if usage_path.exists() else []
    providers += [{'scenario_id': sid, **r} for r in usage]
    worker_paths = list((target / 'stores').glob('*/atgb-worker.json')) if target.exists() else []
    worker = read(worker_paths[0]) if worker_paths else None
    captured = result['turns'] if result else []
    status = {'scenario_id': sid, 'expected_turns': len(scenario['turns']), 'captured_turns': len(captured),
        'execution_status': 'completed' if result and not result['stop_reason'] and len(captured) == len(scenario['turns']) else 'infrastructure_stop' if result else 'not_attempted_after_infrastructure_stop',
        'stop_reason': result['stop_reason'] if result else 'earlier_S04_accounting_stop',
        'human_review_status': 'pending' if captured else 'not_evaluated_no_transcript',
        'conversational_scores': 'not_evaluated',
        'preflight_ok': worker['preflight']['ok'] if worker else 'not_rerun_live; preparation preflight passed',
        'opening_context_delivery': {'status': 'not_evaluated_scenario_not_executed', 'delivered': None} if sid in {'S07', 'S09'} else None}
    scenario_status.append(status)
    if result:
        lines = [f'# {sid} live transcript', '', 'Human scoring pending. Live-provider mode can produce host-owned replies; provider activity is separately recorded.', '', f"Initial reset state: `{json.dumps(worker['scene_after_reset'])}`", '', f"Preflight passed: {worker['preflight']['ok']}. Stop reason: {result['stop_reason'] or 'none'}.", '']
        for turn in captured:
            lines += [f"## {turn['turn_id']}", '', f"Player: {turn['player_input']}", '', f"AI-DM: {turn['response_text']}", '', f"Capture: {turn['capture_status']}; resolution: {turn['resolution_kind']}.", '', f"State: `{json.dumps(turn['state_evidence'])}`", '', f"Host telemetry: `{json.dumps(turn['telemetry'])}`", '']
        if result['stop_reason']:
            lines += ['Remaining scenario turns were not submitted. They have no conversational score.', '']
        (target / 'transcript.md').write_text('\n'.join(lines), encoding='utf-8')

write(OUT / 'scenario_status.json', scenario_status)
write(OUT / 'provider_telemetry.json', {'records': providers, 'application_requests_recorded_sent': sum(bool(r.get('sent')) for r in providers),
    'input_tokens_recorded': sum(r.get('input_tokens') or 0 for r in providers if r.get('sent')),
    'output_tokens_recorded': sum(r.get('output_tokens') or 0 for r in providers if r.get('sent')),
    'usage_consistent_for_all_records': all(r.get('usage_consistent') for r in providers),
    'purpose_counts': dict(collections.Counter(r['purpose'] for r in providers if r.get('sent'))),
    'observed_models': sorted({r.get('model') for r in providers if r.get('model')}),
    'cost': {'status': 'unavailable', 'value': None, 'reason': 'no_verified_complete_cost_telemetry_or_price_table'},
    'note': 'Ledger and raw host telemetry are separate observations. Missing host counters remain unavailable. SDK-internal retries are not separately observed.'})
write(OUT / 'turn_telemetry.json', [{'turn_id': t['turn_id'], 'telemetry': t['telemetry']} for t in turns])

combined = {**next(iter(results.values())), 'turns': turns,
    'scenario_records': [s for r in results.values() for s in r['scenario_records']],
    'conversations': [c for r in results.values() for c in r['conversations']], 'gameplay_performance_claim': False}
sheet = build_worksheet(combined, corpus['manifest'])
sheet['banner'] += ' All captured turns are pending authorized human review. S04 ended at an infrastructure/accounting stop. S04.3–S10.2 not captured must not receive conversational failure scores. See scenario_status.json for the complete roster. Live-provider mode does not mean every reply was model-generated.'
sheet['scenario_execution_status'] = scenario_status
write(OUT / 'worksheet.json', sheet)
(OUT / 'worksheet.md').write_text(render_worksheet(sheet), encoding='utf-8')
write(OUT / 'evaluation_status.json', {'captured_turns_pending_human_review': len(turns),
    'uncaptured_turns_not_evaluated': 37-len(turns), 'evaluated_successes': None, 'evaluated_failures': None,
    'uncertain_judgments': None, 'gameplay_performance_claim': False,
    'states': {'evaluated_success': 'Only an authorized human pass is success.', 'evaluated_failure': 'Only an authorized human fail is conversational failure.', 'uncertain': 'Available to reviewers when evidence is insufficient.', 'not_evaluated': 'All judgments here; no human scores supplied.', 'infrastructure_setup_failure': 'S04 accounting stop; unsubmitted turns and unattempted scenarios are not conversational failures.'},
    'capability_status': {cap: {'pending_captured_turns': sum(t['primary_capability'] == cap for t in turns), 'planned_turns': sum(t['primary_capability'] == cap for s in corpus['scenarios'] for t in s['turns']), 'evaluated_failures': None} for cap in sorted({t['primary_capability'] for s in corpus['scenarios'] for t in s['turns']})}})
preserved = {key: [n for n,h in provenance[source].items() if not (ROOT/n).exists() or sha(ROOT/n) != h] for key,source in [('execution_sources','source_sha256'),('canonical_campaign_data','canonical_data_sha256')]}
assert not any(preserved.values()), preserved
write(OUT / 'preservation_checks.json', {'preserved': True, 'changed_files': preserved})
write(OUT / 'execution_blocker.json', {'stage': 'B', 'scenario': 'S04', 'after_turn': 'S04.2',
    'reason': 'provider_call_ceiling_not_observable', 'approval_blocker_resolved': True,
    'detail': 'The turn response was captured but resolution metadata had no performance object. Provider-call count remained unavailable; the approved harness stopped before S04.3. The campaign wrapper stopped before S05. No accounting substitution, automatic retry, or gameplay repair was performed.',
    'missing_host_performance_not_a_conversational_failure': True})

ledger = read(OUT / 'provider_telemetry.json')
latencies = [t['telemetry']['elapsed_ms']['value'] for t in turns if t['telemetry']['elapsed_ms']['status'] == 'recorded']
host_calls = sum(t['telemetry']['provider_call_count']['value'] for t in turns if t['telemetry']['provider_call_count']['status'] == 'recorded')
wall = sum(read(p)['elapsed_seconds'] for p in OUT.glob('S*/wall_clock.json'))
summary = {'captured_turns':len(turns),'planned_turns':37,'provider_requests_recorded':ledger['application_requests_recorded_sent'],
    'ledger_input_tokens':ledger['input_tokens_recorded'],'ledger_output_tokens':ledger['output_tokens_recorded'],
    'host_call_known_subtotal':host_calls,'turn_latency_observed':len(latencies),'latency_min_ms':min(latencies),'latency_max_ms':max(latencies),
    'scenario_wall_seconds':wall,'human_review_complete':False,'gameplay_performance_claim':False}
write(OUT / 'execution_summary.json', summary)
validation = read(history / 'validation_results.json')
validation.update({'live_provider_calls': ledger['application_requests_recorded_sent'], 'live_tokens': {'input': ledger['input_tokens_recorded'], 'output': ledger['output_tokens_recorded'], 'source': 'provider ledger'}, 'live_latency': {'observed_turns': len(latencies), 'unavailable_turns': len(turns)-len(latencies)}, 'live_cost': 'unavailable_no_verified_price_table', 'captured_turns': len(turns), 'human_review_status': 'pending', 'execution_status': 'partial; infrastructure stop at S04'})
write(OUT / 'validation_results.json', validation)

# Correct presentation only. Keep raw reports/result objects unchanged as source evidence.
for sid,result in results.items():
    lines = [f'# {sid}: execution evidence, human review pending', '', f"Captured {len(result['turns'])} turns. Infrastructure stop: {result['stop_reason'] or 'none'}.", '', 'Interpretation, response adequacy, authority compliance, severity, clarification and continuity are NOT EVALUATED. No gameplay failure count or aggregate score is established. See worksheet.json/.md and transcript.md. Raw legacy report.md/result.json counters are unreviewed diagnostic placeholders, not measured zero failures.', '']
    (OUT/sid/'review_status.md').write_text('\n'.join(lines),encoding='utf-8')

rows = '\n'.join(f"| {s['scenario_id']} | {s['captured_turns']}/{s['expected_turns']} | {s['execution_status']} |" for s in scenario_status)
report = f'''# ATGB-03 — Initial live conversational baseline execution report

Date: 2026-10-18. Status: PARTIAL LIVE EXECUTION; STOPPED BY INFRASTRUCTURE ACCOUNTING; HUMAN REVIEW PENDING.

## Outcome

S01 passed its live infrastructure gate. S02 and S03 completed. S04 captured two turns, then the approved harness stopped with `provider_call_ceiling_not_observable` before S04.3. The campaign stopped there; S05–S10 were not attempted. Fifteen of 37 turns were captured. There is no aggregate gameplay score and no claim that gameplay improved. All three human judgments remain pending for every captured turn; the other 22 turns are not evaluated.

| Scenario | Captured/planned turns | Execution status |
| --- | --- | --- |
{rows}

## Versions, authority and provenance

Benchmark ATGB-02; scenario ATGB-01; rubric atgb-rubric-01; partition ATGB-02-s07-held-out (25 visible / 4 related / 8 held-out). Frozen baseline frontier-gate-v1, pinned manifest SHA-256 4197114379ba9c406d9b2135085eb605d8235fd9a34dcebe852b95451ef41ae9. Repository HEAD b012c3d7e5887fdfb09d10bb9cc0f0220de09df9, with extensive pre-existing dirty/untracked work. `initial_git_status.txt` and `configuration_and_provenance.json` record that state and 240 execution/input hashes. The Development Constitution, Validation Evidence Standard, ATGB specification, design/rubric/catalog, execution instructions, readiness report and review-handoff standard governed this evaluation.

Preparation checked 31 approved harness/corpus files against readiness evidence and its preserved review ZIP. All ten provider-disabled preflights reproduced ATGB-02A's normalized state hash c12cb0dfe6a31980b4ecc00a59cc359a143a76452e517a36ad76753a6145561a. Existing focused checks: 24 passed outside the sandbox; separate existing provider-disabled chat check also passed. First setup-directory errors and the terminated sandbox retry are retained as environmental attempts. No broad/full-suite claim is made.

The first live command was rejected before process creation by automatic approval review. The user then explicitly approved resumption and the OpenAI data export. `resume_checks.json` records that approval and a fresh unchanged-source/configuration check. Historical blocked records remain under `pre_execution_blocked/`; they describe the earlier state, not the final outcome.

## Execution configuration and limits

Provider: OpenAI, https://api.openai.com/v1. All configured model roles remained gpt-4.1-mini; all recorded returned model ids are gpt-4.1-mini-2025-04-14. Existing model routing stayed enabled. No model, provider credential, production prompt or sampling setting was changed. Credentials were checked for availability without recording values. The production chat route POST /api/chat was invoked with the existing player-mode request through the approved TestClient worker. This is API conversation evidence, not browser-rendered UI validation.

Ceilings were 80 application provider requests and 1800 seconds overall, with S01 limited to 12 and 300. Scenario workers also had at most 300 seconds each within the remaining overall deadline. Existing provider accounting enforced its request guard and wrote raw usage records. No live attempt was retried by this campaign. Recorded scenario wall time: {wall:.3f} seconds. No ceiling was exhausted; execution stopped because a count became unavailable. SDK-internal transport retries are not independently observable; application requests and elapsed limits are the stated bounds.

Every attempted scenario used a distinct frozen-baseline store, fresh reset and empty transcript. Live preflights passed for S01–S04. S01 reset evidence shows no selected interlocutor, discoveries, flags or prior transcript; all four expected responses were captured without an infrastructure error. Its four real OpenAI interpretation requests establish intended provider use, and isolation checks and canonical-file hashes establish that the player campaign was not used as a write store. Stage A acceptance is infrastructure acceptance only. Conversational mistakes did not trigger repair or block Stage B.

## Usage and latency

The raw provider ledger records {ledger['application_requests_recorded_sent']} sent application requests: {json.dumps(ledger['purpose_counts'])}. Every recorded request has consistent provider-reported token fields. Ledger token subtotal: {ledger['input_tokens_recorded']} input and {ledger['output_tokens_recorded']} output. These are observed usage for recorded requests only. Provider returned ids, latency and usage are preserved in provider_usage.jsonl and consolidated provider_telemetry.json.

The host turn summaries contain a known provider-call subtotal of {host_calls}, plus one unavailable turn count. They omit S03.2's expression request even though that request appears in the raw provider ledger (156 input / 9 output tokens). The two telemetry sources therefore do not agree in scope and must not be substituted silently. S04.2 has no performance object: call count, tokens, retries and response latency are unavailable, while its detail counters say zero interpretation/narration/retries. Missing performance data was not converted to zero or inferred from those detail counters.

Host response latencies were captured for {len(latencies)} of 15 turns: range {min(latencies)}–{max(latencies)} ms. S04.2 latency is unavailable. Per-turn host telemetry is preserved unchanged in turn_telemetry.json and the raw results. Recorded host retry counters are zero where present; the missing counter remains unavailable. Dollar cost is unavailable because no verified complete pricing/cost telemetry was supplied. Conservative call/time ceilings were used; no token estimate is represented as measured usage and no expenditure is invented.

## Infrastructure failure and setup limitations

S04.2 returned HTTP success and a captured response, but lacked resolution.metadata.performance. Before S04.3, the approved benchmark could no longer observe its configured call ceiling, so it refused further turns. This is an evaluation/infrastructure accounting limitation, not an assigned conversational failure. The earliest established instrumentation problem is the missing performance object on the captured turn; no gameplay cause is inferred or repaired. Actual text and log metadata remain available for independent review.

S07/S09 were not executed. Required opening-context delivery is NOT EVALUATED (delivered=null), not confirmed absent or successful. Preparation verifies authored opening seeds only. No extra narrative was inserted to satisfy either scenario. No missing starting condition received a conversational failure score. S04.3–S04.4 and every S05–S10 turn have no captured response and no conversational score.

## Unscored conversational observations

These are factual quotations and provenance notes, not rubric judgments. S01.2 answered “That has not been established in the information available to you.” S01.3 answered “I cannot tell who that is addressed to. Nothing has been attempted.” S03.3 asked “Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted.” S04.1 delivered the serjeant route-change sentence. S04.2 replied “I can't interpret that from the current scene without using information you have not been shown.” Whether each interpretation, response and authority choice satisfies the approved criteria is pending human review.

There were no narration-purpose requests in the recorded ledger. Most player-facing text was host-owned; one expression request was made. Live-provider mode does not imply every reply was model-generated. The report measures the existing combined production path and makes no claim of unconstrained generative narration quality.

## Human review package and reporting discipline

Raw per-scenario result.json, report.md, worksheet.md/.json, provider usage, worker/job JSON, complete isolated final state and session logs are preserved. S01/transcript.md is the smoke transcript; S02–S04/transcript.md preserve subsequent complete/partial conversations. Combined worksheet.md/.json uses the existing worksheet generator for the 15 captured turns and retains separate interpretation, response adequacy, authority, minor/major/critical severity, clarification, continuity and conversation-quality fields. No human judgments have been entered.

The campaign reporting mechanism writes evaluation_status.json and per-scenario review_status.md to distinguish pending judgments, uncaptured/not evaluated turns and the infrastructure stop. Evaluated-success, evaluated-failure and uncertain counts are null until supplied by an authorized human. The original report's diagnostic zeros for unreviewed failure categories are retained as raw evidence but must not be read as measured zero failures. This presentation correction changes only campaign reporting, not execution, scoring rules, expectations or production behavior. No exact prose matching was used.

## Preservation and comparability

All recorded execution/input sources and canonical campaign data remain byte-identical to the initial snapshot. No interpreter, routing, fallback, NPC knowledge, scenario expectation, scoring rubric, production behavior or model configuration was modified. There was no Product Realization repair campaign. Held-out content was previously exposed in ATGB-01, and no held-out scenario ran here; independent generalization is not measured. The partial single-trial, single-environment result does not establish the full live baseline. Existing PR-BL versus later PR-EG orientation history remains out of scope.

## Recommended next action

Review this partial evidence and the benchmark accounting limitation. A separately reviewed infrastructure correction/readiness check is needed before another baseline attempt; do not weaken the stop guard or modify gameplay to improve outcomes. An authorized human may score only captured, sufficiently supported turns, using uncertain or not evaluated when appropriate. The first baseline is not fully executed or fully scored. Stop this observation pass after preparing the standard review ZIP.
'''
(ROOT/'development/reports/atgb_03_initial_live_baseline.md').write_text(report,encoding='utf-8')

config = read(history/'review_config.json')
config.update({'objective_status':'PARTIAL LIVE BASELINE; INFRASTRUCTURE STOP AT S04; HUMAN REVIEW PENDING',
    'executive_summary': f'S01–S03 completed; S04 stopped after two turns because its provider-call counter became unavailable. Captured 15/37 turns, {ledger["application_requests_recorded_sent"]} provider requests. S05–S10 not attempted. All human judgments pending; no gameplay score or production change. Explicit OpenAI approval was supplied after the initial rejected command.',
    'purpose':'Observe existing player–AI-DM behavior through the approved benchmark and preserve a partial run after its accounting guard stopped execution.',
    'changes':{'production':['None; canonical campaign and all recorded execution sources unchanged.'],'validation':['Existing 24 focused provider-disabled tests passed; four live starting preflights passed.'],'tooling':['Campaign wrapper only; approved harness unchanged.'],'documentation':['Partial execution report and current NEXT_SESSION orientation.'],'generated_artifacts':['15 raw captured exchanges, independent provider ledger, state/log evidence, existing human worksheets and explicit pending/not-evaluated reporting.']},
    'testing':{'focused':'24 passed in preparation.','broader':'Separate existing provider-disabled production chat test passed.','full_suite':'Not run.','runtime_validation':'S01 passed live infrastructure acceptance; S02/S03 complete; S04 stopped before third turn.','model_runtime_boundary':f'OpenAI gpt-4.1-mini; {ledger["application_requests_recorded_sent"]} recorded requests, no narration requests; host-owned replies preserved.','new_regressions':'No code change; missing runtime accounting is an observed infrastructure limitation.','pre_existing_failures':'Sandbox startup limitations and initial pytest-directory setup attempt preserved separately.'},
    'decisions_requiring_human_review':['Review partial transcripts using separate interpretation, response adequacy and authority judgments; no scores supplied.','Review missing performance accounting and expression-call underreporting before a separately reviewed readiness correction/new live baseline. Do not repair gameplay during evaluation.'],
    'known_problems':{'campaign_specific':['S04.2 lacks performance metadata; approved harness stopped before S04.3.','Provider ledger includes S03.2 expression request missing from host turn counter.','22 turns unsubmitted; S07/S09 opening delivery not evaluated.'],'pre_existing':['Previously exposed held-out corpus.','Dirty worktree means HEAD alone is insufficient provenance.','No browser-rendered UI validation.']},
    'missing_concepts':['Complete live execution and authorized human scoring.','Reliable benchmark accounting across all existing response paths.'],
    'does_not_prove':['Full baseline completion, gameplay improvement or any aggregate gameplay score.','Unscored semantic adequacy or authority compliance.','S07/S09 opening delivery or held-out/independent generalization.','Complete cost telemetry or SDK-internal retry counts.'],
    'recommended_next_step':'Review the partial evidence and accounting blocker. Require separately reviewed infrastructure readiness before another live attempt. Human-score only captured turns with sufficient evidence; leave others not evaluated. No gameplay repair.',
    'self_contained_review_test':'ZIP includes exact captured conversations, per-turn context/rubric worksheets, isolated state/logs, provider ledger, missing-counter evidence, status roster, hashes and the pending-human-review boundary.', 'supporting_files':[]})
existing = read(history/'review_config.json')['supporting_files']
paths = [ROOT/item['path'] for item in existing if not item['path'].startswith('artifacts/atgb/atgb_03/')]
paths += [p for p in OUT.rglob('*') if p.is_file() and p.suffix in {'.json','.jsonl','.md','.txt','.xml','.py'} and '__pycache__' not in p.parts and 'pre_execution_blocked' not in p.parts and p.name not in {'handoff_build.json','bundle_verification.json','worksheet_template.md','worksheet_template.json','package_blocked.py'}]
for path in sorted(set(paths)):
    rel=path.relative_to(ROOT).as_posix()
    config['supporting_files'].append({'path':rel,'role':'partial_live_evaluation_evidence','why':'Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments.','behavioral_evidence': '/S0' in rel and path.name in {'transcript.md','session_log.jsonl','result.json'},'human_review_required':path.name in {'transcript.md','worksheet.md','worksheet.json'}})
write(ROOT/'data/validation/review_handoffs/atgb_03_initial_live_baseline.json',config)
print(json.dumps(summary))
