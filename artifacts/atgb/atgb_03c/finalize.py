"""Package ATGB-03C observations; never assign human judgments."""
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent
OLD = ROOT / 'artifacts/atgb/atgb_03'
sys.path.insert(0, str(ROOT))
from tools.atgb.accounting import live_accounting_readiness, inspect_ledger
from tools.atgb.fixtures import load_corpus
from tools.atgb.worksheet import build_worksheet, render_worksheet
from tools.validation_evidence import build_packet, write_packet

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def write(p, value):
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def rel(p):
    return p.relative_to(ROOT).as_posix()

assert (OUT / 'campaign_usage.json').exists(), 'Execution must stop before packaging'
corpus = load_corpus(ROOT)
before = read(OUT / 'provenance_before.json')
checks = {p: (ROOT / p).is_file() and sha(ROOT / p) == h for p, h in before['source_sha256'].items()}
preservation = {'all_unchanged': all(checks.values()), 'file_count': len(checks), 'changed': [p for p, ok in checks.items() if not ok],
    'original_atgb_03_unchanged': all(ok for p, ok in checks.items() if p.startswith('artifacts/atgb/atgb_03/')),
    'canonical_campaign_unchanged': all(ok for p, ok in checks.items() if p.startswith('data/') and not p.startswith('data/validation/')),
    'corpus_and_baseline_unchanged': all(ok for p, ok in checks.items() if p.startswith('data/validation/atgb/')),
    'reviewed_production_and_harness_unchanged': all(ok for p, ok in checks.items() if p.startswith(('game/', 'tools/atgb/')))}
write(OUT / 'preservation_checks.json', preservation)
assert preservation['all_unchanged']
write(OUT / 'accounting_readiness_final.json', live_accounting_readiness(ROOT))

results = [read(OUT / f'S{i:02}/result.json') for i in range(4, 11) if (OUT / f'S{i:02}/result.json').exists()]
historical = [read(OLD / f'S{i:02}/result.json') for i in range(1, 4)]
combined = copy.deepcopy(historical[0])
combined.update(turns=[], scenario_records=[], conversations=[], run_id='ATGB-03-plus-03C-coverage', human_review_complete=False, gameplay_performance_claim=False)
continuation = copy.deepcopy(combined)
accounting, readiness, roster, latency, opening = [], [], [], [], []
scene = read(ROOT / 'data/validation/atgb/baselines/frontier-gate-v1/scenes/frontier_gate.json')['scene']
for result in historical + results:
    is_new = result in results
    target_doc = continuation if is_new else None
    sid = result['scenario_ids'][0]
    origin = 'ATGB-03C' if is_new else 'ATGB-03'
    trial = result['trial_number']
    directory = OUT / sid if is_new else OLD / sid
    for doc in [combined] + ([target_doc] if target_doc is not None else []):
        doc['turns'].extend(copy.deepcopy(result['turns']))
        doc['scenario_records'].extend(copy.deepcopy(result['scenario_records']))
        doc['conversations'].extend(copy.deepcopy(result['conversations']))
    for doc in [combined] + ([target_doc] if target_doc is not None else []):
        for turn in doc['turns'][-len(result['turns']):] if result['turns'] else []:
            turn['execution_provenance'] = {'campaign': origin, 'trial': trial, 'source': rel(directory / 'result.json'),
                'accounting': 'ATGB-03B-1_admissions' if is_new else 'historical_completion_only'}
            turn['evidence_references'].extend([rel(directory / 'transcript.md'), rel(directory / 'result.json')])
    if not is_new:
        continue
    workers = list((directory / 'stores').glob('*/atgb-worker.json'))
    worker = read(workers[0]) if len(workers) == 1 else {}
    events = [json.loads(line) for line in (directory / 'provider_usage.jsonl').read_text().splitlines()] if (directory / 'provider_usage.jsonl').exists() else []
    completed = [e for e in events if e.get('event') == 'completed']
    snapshots = [t['provider_accounting']['process_snapshot'] for t in result['turns'] if t.get('provider_accounting')]
    final_snapshot = snapshots[-1] if snapshots else None
    reconciliation = inspect_ledger(directory / 'provider_usage.jsonl', final_snapshot) if final_snapshot else {'status': 'unavailable'}
    tokens_known = all(e.get('usage_consistent') is True for e in completed if e.get('sent'))
    host_count = [t['telemetry']['provider_call_count'].get('value') for t in result['turns']]
    admitted = sum(e.get('event') == 'admitted' for e in events)
    dispatched = sum(e.get('event') == 'dispatch_attempted' for e in events)
    failures = [e for e in completed if e.get('completion_status') != 'completed']
    pending = admitted - len(completed)
    row = {'scenario_id': sid, 'trial': trial, 'accounting_version': 'ATGB-03B-1',
        'admitted': admitted, 'dispatched': dispatched, 'completed': len(completed), 'failed_or_interrupted': len(failures), 'pending': pending,
        'input_tokens': sum(e.get('input_tokens') or 0 for e in completed), 'output_tokens': sum(e.get('output_tokens') or 0 for e in completed),
        'token_totals_complete': tokens_known and not pending, 'unknown_usage': len([e for e in completed if e.get('sent') and e.get('usage_consistent') is not True]) + pending,
        'purposes': dict(Counter(e['purpose'] for e in completed)), 'returned_models': sorted(set(e.get('model') for e in completed if e.get('model'))),
        'host_performance': [{'turn_id': t['turn_id'], **t['telemetry']} for t in result['turns']],
        'host_count_subtotal': sum(v for v in host_count if isinstance(v, int)), 'host_count_unavailable_turns': sum(v is None for v in host_count),
        'host_scope_discrepancy': 'Host counters have different scope; retain independently, including expression requests.',
        'ledger_reconciliation': reconciliation, 'ledger': rel(directory / 'provider_usage.jsonl'), 'process_snapshot': final_snapshot}
    accounting.append(row)
    expected = 2 if sid in ('S09', 'S10') else 4
    ok = len(result['turns']) == expected and not result['stop_reason'] and all(t['capture_status'] == 'captured' for t in result['turns'])
    roster.append({'scenario_id': sid, 'trial': trial, 'captured': len(result['turns']), 'planned': expected,
        'execution_status': 'completed' if ok else 'infrastructure_stop', 'stop_reason': result['stop_reason'],
        'human_review_status': 'pending', 'opening_delivery_limitation': sid in ('S07', 'S09'),
        'score_eligibility': 'review_with_setup_delivery_caveat' if sid in ('S07', 'S09') else 'pending_human_review'})
    readiness.append({'scenario_id': sid, 'isolation': result['scenario_records'][0]['isolation'],
        'preflight': result['scenario_records'][0].get('preflight'), 'scene_after_reset': worker.get('scene_after_reset'),
        'worker_source': rel(workers[0]) if workers else None, 'model_configuration': result['model_configuration']})
    lines = [f'# {sid} — ATGB-03C, trial {trial}', '', f'Captured {len(result["turns"])}/{expected}; stop: {result["stop_reason"] or "none"}. Human judgments pending.', '',
        'This uses the live-enabled production API path; individual replies may be host-owned. Technical completion is not gameplay success.', '']
    if sid in ('S07', 'S09'):
        context = {'scenario_id': sid, 'context_present_in_world_state': True,
            'world_state_evidence': 'Live preflight verifies authored opening/journal seeds and addressables against the frozen scene.',
            'opening_seed_facts': scene['opening_seed_facts'], 'journal_seed_facts': scene['journal_seed_facts'],
            'opening_delivered_before_first_player_turn': False,
            'delivery_evidence': 'Approved worker silently resets, verifies empty log/history, then posts only the fixture player turns. No start_campaign/opening/GET state or journal output was delivered as conversation.',
            'context_inferred_by_fixture': corpus['scenarios'][int(sid[1:]) - 1]['initial_context'],
            'unavailable_or_unverified': ['Browser-rendered state or journal visibility', 'Any opening delivery outside captured API sequence'],
            'classification': 'setup_delivery_limitation', 'extra_context_injected': False,
            'scoring_constraint': 'S07 opening-dependent naturalness and banner assumptions are not a valid fully established setup. S09 explicit named addressee question can be reviewed, but posture delivery cannot be assumed. Keep unsupported criteria uncertain/not evaluated; no gameplay failure assigned for missing opening.'}
        opening.append(context)
        lines += ['Opening delivery limitation: no opening was delivered before the first player turn. See opening_context.json; do not assume fixture context reached the player.', '']
    for turn in result['turns']:
        lines += [f'## {turn["turn_id"]}', '', f'Player: {turn["player_input"]}', '', f'AI-DM: {turn["response_text"]}', '',
            f'Capture: {turn["capture_status"]}; resolution: {turn["resolution_kind"]}.', '',
            f'State evidence: `{json.dumps(turn["state_evidence"], ensure_ascii=False)}`', '',
            f'Host telemetry: `{json.dumps(turn["telemetry"] )}`', '', f'Accounting: see result.json → provider_accounting and provider_usage.jsonl.', '']
        latency.append({'turn_id': turn['turn_id'], 'host_elapsed_ms': turn['telemetry']['elapsed_ms'],
            'host_retry_count': turn['telemetry']['retry_count']})
    (directory / 'transcript.md').write_text('\n'.join(lines), encoding='utf-8')
    (directory / 'review_status.md').write_text('Human review pending. Interpretation, response adequacy, authority, severity, clarification, continuity and naturalness are unmeasured. Raw report diagnostic zeros do not establish zero failures.\n', encoding='utf-8')

for name, doc in [('continuation', continuation), ('combined_baseline', combined)]:
    doc['scenario_ids'] = [r['scenario_id'] for r in doc['scenario_records']]
    doc['accounting_boundary'] = 'ATGB-03 historical completion-only ledger; ATGB-03C ATGB-03B-1 durable admissions. Do not sum as identical request metrics.'
    doc['report'] = 'Review source assembled for human worksheets, not an aggregate automated performance report. See baseline_coverage.json and the ATGB-03C execution report.'
    doc['trial_number'] = 'per_scenario_see_execution_provenance'
    write(OUT / f'{name}_review_source.json', doc)
    sheet = build_worksheet(doc, corpus['manifest'])
    sheet['banner'] += ' All judgments pending. ATGB-03C S04 is full trial 2; original partial trial 1 is separate. S07/S09 lack delivered opening context; review with setup caveats from opening_context.json. No measured zero failures or score is established.'
    sheet['execution_provenance'] = [{'scenario_id': r['scenario_ids'][0], 'trial': r['trial_number'], 'source': 'ATGB-03C' if r in results else 'ATGB-03'} for r in (results if name == 'continuation' else historical + results)]
    write(OUT / f'{name}_worksheet.json', sheet)
    (OUT / f'{name}_worksheet.md').write_text(render_worksheet(sheet), encoding='utf-8')
write(OUT / 'opening_context.json', opening)
write(OUT / 'scenario_readiness.json', readiness)
write(OUT / 'provider_accounting.json', {'version': 'ATGB-03B-1', 'scenarios': accounting, 'historical_records_included': False})
write(OUT / 'turn_latency.json', latency)
total_turns = sum(len(r['turns']) for r in results)
totals = {k: sum(a[k] for a in accounting) for k in ('admitted', 'dispatched', 'completed', 'failed_or_interrupted', 'pending', 'input_tokens', 'output_tokens', 'unknown_usage')}
coverage = {'continuation_scenarios': roster, 'continuation_captured_turns': total_turns,
    'continuation_planned_turns': 24, 'continuation_reviewable_observations': total_turns,
    'opening_context_limited_turns': sum(r['captured'] for r in roster if r['opening_delivery_limitation']),
    'original_completed_scenarios': ['S01', 'S02', 'S03'], 'original_complete_scenario_turns': 13,
    'original_partial_S04_trial_1': {'turns': 2, 'source': 'artifacts/atgb/atgb_03/S04', 'included_in_baseline_set': False, 'human_review': 'pending'},
    'combined_baseline_unique_turns_captured': 13 + total_turns, 'combined_baseline_planned_unique_turns': 37,
    'total_observations_including_historical_partial': 15 + total_turns,
    'human_review': 'pending_all_judgments', 'review_complete': False, 'gameplay_performance_claim': False,
    'new_accounting_totals': totals, 'original_provider_usage': {'metric': 'historical_completion_only_observed_subtotal', 'requests': 12, 'input_tokens': 21531, 'output_tokens': 2190},
    'full_baseline_measurement_complete': False, 'setup_limitations': 'S07/S09 opening delivery absent in captured API sequence; criteria dependent on it remain uncertain/not evaluated.'}
write(OUT / 'baseline_coverage.json', coverage)
validation = []
for filename in ('focused_unsandboxed.xml', 'reset_retry.xml'):
    suites = list(ET.parse(OUT / filename).getroot().iter('testsuite'))
    validation.append({'artifact': filename, **{k: sum(int(s.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}})
write(OUT / 'validation_results.json', {'attempts': validation, 'preflight_final': '10/10; zero chat turns; no provider calls',
    'sandbox_attempt': 'Interrupted because host TestClient/setup was blocked; no completed JUnit. Console preserved.',
    'setup_attempts': 'Sandbox preflight failed S01 session save; unsandboxed preflight failed S07 combat save; targeted bundled-runtime reset reproducibility and final ten-scenario preflight passed.',
    'full_suite': 'not run; evaluation only, no production source change'})
packet = build_packet(campaign={
    'campaign_id': 'atgb_03c_live_baseline_continuation',
    'what_was_tested': 'S04 full trial 2 and S05-S10 trial 1; 24 fixture turns; all conversational outcomes unscored',
    'runtime_path': 'Production POST /api/chat through approved TestClient worker in fresh isolated frozen-baseline stores',
    'gm_boundary': 'Live-enabled OpenAI gpt-4.1-mini with existing host-owned replies and model roles; no browser UI validation',
    'player_input_mode': 'Approved fixed benchmark lines; previously exposed held-out scenarios remain labeled',
    'run_count': len(results), 'turn_count': total_turns,
    'automated_conclusion': 'Runtime capture only. No evaluator or human success/failure classifications were made. Empty selected outcome categories mean unmeasured, not zero gameplay failures.'},
    claim_types=['runtime_evidence'],
    examples=[{'example_id': 'ATGB-03C-' + t['turn_id'], 'scenario_run_id': r['run_id'],
        'turn_index': t['order'], 'player_input': t['player_input'],
        'player_input_classification': ['representative_player_behavior'], 'exact_gm_output': t['response_text'],
        'runtime_validity': {'capture': t['capture_status'], 'setup_delivery_limitation': t['scenario_id'] in ('S07', 'S09')},
        'source_artifact_path': rel(OUT / t['scenario_id'] / 'result.json'),
        'semantic_result': None, 'automated_evaluation': None,
        'human_review': {'status': 'UNREVIEWED', 'rationale': 'Await authorized human judgments; no automated gameplay scorer.', 'review_date': None, 'semantic_policy_changed': False, 'calibration_case_id': None},
        'evaluator_disagreement': {'present': False, 'status': 'not_evaluated'},
        'judgments': t['judgment'], 'partition': t['partition'], 'evidence_status': t['evidence_status'],
        'state_evidence': t['state_evidence'], 'telemetry': t['telemetry']}
        for r in results for t in r['turns']],
    missing_concepts=[{'name': 'Opening context delivery', 'evidence': 'Approved silent-reset worker does not deliver authored opening before fixture turns; S07/S09 carry setup limitations.', 'status': 'Recorded; no behavioral change'}],
    limitations=['All human judgments pending; no gameplay score or measured success/failure counts.',
        'Opening-dependent criteria require uncertain/not evaluated when unsupported.',
        'No independent generalization, conversational improvement, rendered UI or SDK transport retry claim.'])
write_packet(OUT / 'behavioral_evidence', packet)
ms = [l['host_elapsed_ms']['value'] for l in latency if l['host_elapsed_ms']['status'] == 'recorded']
clock = read(OUT / 'campaign_usage.json')
table = '\n'.join(f'| {r["scenario_id"]} | {r["trial"]} | {r["captured"]}/{r["planned"]} | {r["execution_status"]} | {"opening delivery limited" if r["opening_delivery_limitation"] else "pending review"} |' for r in roster)
usage_table = '\n'.join(f'| {a["scenario_id"]} | {a["admitted"]} | {a["dispatched"]} | {a["completed"]} | {a["host_count_subtotal"]} | {a["host_count_unavailable_turns"]} | {a["input_tokens"]} / {a["output_tokens"]} |' for a in accounting)
report = f'''# ATGB-03C — Initial live conversational baseline continuation

Date: 2026-10-18. Evaluation only. Human review pending.

Captured {total_turns}/24 continuation turns. Combined with the 13 original S01–S03 turns, the baseline set contains {13 + total_turns}/37 unique turns. Original S04 trial 1 remains a separate two-turn historical trial; total observations including it: {15 + total_turns}. No conversational score, evaluated successes/failures, or improvement claim is established.

| Scenario | Trial | Captured/planned | Infrastructure | Review qualification |
| --- | ---: | ---: | --- | --- |
{table}

## Readiness and preservation

Read the current Constitution, validation/handoff authorities, ATGB-01 design and rubric, adopted ATGB-02 specification/implementation/execution instructions, frozen ATGB-02A readiness, and ATGB-03/03A/03B reports. Current readiness passes all seven reviewed guarded dispatch owners and the pinned application source surface. Thirteen selected source files match the preserved ATGB-03B review ZIP. Corpus/baseline match original ATGB-03 hashes. All {len(checks)} protected snapshot files remain byte-identical, including original results, provider ledgers, reports, partial S04, production/harness sources and canonical campaign data. HEAD: `{before['revision']}`; extensive pre-existing dirty/untracked worktree retained. No commit made. Hashes and full initial status identify actual running bytes.

Frozen baseline: frontier-gate-v1, manifest 4197114379ba9c406d9b2135085eb605d8235fd9a34dcebe852b95451ef41ae9. Ten final provider-disabled preflights pass. Each attempted live scenario has its own fresh frozen-baseline store and live preflight, empty initial history and frontier_gate starting scene. See scenario_readiness.json and retained worker/job/state files. No canonical campaign store or previous conversation was reused.

## Execution and provider evidence

The unchanged production `POST /api/chat` TestClient path received approved fixture lines. This establishes API conversation evidence; browser-rendered UI was not tested. All configured roles remain gpt-4.1-mini with routing enabled and uncontrolled sampling. Credentials were verified available without exposing values. Returned model ids: {sorted(set(m for a in accounting for m in a['returned_models']))}.

Fresh limits: 48 application admissions, 900 elapsed seconds overall, at most 180 seconds per scenario worker, 120,000 total tokens (100,000 input / 20,000 output). Workers receive remaining campaign allowances and deadlines. Actual elapsed: {clock['elapsed_seconds']:.3f} seconds. No live scenario retries or accounting safeguards bypassed. SDK transport retries remain unchanged and are not separately counted or absolutely bounded by application admissions. Input reservation uses the reviewed estimates; output caps and post-response usage checks remain active. Expenditure is unavailable without a verified pinned price; no dollar limit was fabricated.

Continuation accounting ATGB-03B-1: {totals['admitted']} admitted, {totals['dispatched']} dispatched, {totals['completed']} completed, {totals['failed_or_interrupted']} failed/interrupted completions, {totals['pending']} pending, {totals['unknown_usage']} unknown usage. Available tokens: {totals['input_tokens']} input / {totals['output_tokens']} output. Per-scenario raw lifecycle ledgers, response ids, returned model, provider latency, final process snapshots and reconciliation are preserved. Host metadata is independent in result.json and provider_accounting.json; do not replace it with ledger totals. Host latency available on {len(ms)}/{total_turns} captured turns, range {min(ms) if ms else 'unavailable'}–{max(ms) if ms else 'unavailable'} ms. See turn_latency.json for retries and individual values.

| Scenario | Admitted | Dispatched | Completed | Host count subtotal | Missing host-count turns | Input / output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{usage_table}

S04/S05 each include one contract-interpretation and one expression request beyond the host subtotal; S06 includes one expression request beyond its known host subtotal. S06 has two unavailable host-performance records. S04.2 early-return performance is now present, but original S04.2 remains untouched and unavailable. Ledger completeness does not fill missing host latency or change its scope.

The original ATGB-03 ledger is completion-only: 12 observed requests, 21,531 input / 2,190 output tokens. It is an observed historical subtotal, not a certified admission upper bound. Those metrics are not merged with the new admission counts. The accounting version boundary is explicit even though both passes share HEAD. Accounting changes support observability; they do not establish conversational improvement.

## Infrastructure and setup limitations

Provider-disabled preparation retained a sandbox S01 session-save WinError 5, an unsandboxed S07 combat-save WinError 5, and one failing reset reproducibility check (103/104 focused checks passed). The isolated reset check passed with the bundled runtime; a final ten-scenario preparation passed. These are setup/environment failures, never assigned gameplay failures. The interrupted sandbox test attempt is also retained. No source repair or weakened expectation was used. Initial live dispatch was rejected before process creation by automatic approval review; the user explicitly approved the stated payload/destination/limits, recorded in export_authorization.json, and the authorized command then ran.

S07/S09 opening delivery is a setup/delivery limitation. Authored rain, banners, hawking and posture cues exist in the validated world/scene seeds. The fixture assumes availability. The approved worker silently resets and submits only the scenario lines, without delivering an opening to the player before the first turn. Thus world-state presence is verified; conversational opening delivery is absent in this API sequence; browser/journal visibility is unverified. No extra context was injected. S07's opening-dependent naturalness/banner criteria cannot support a fully valid scenario measurement under the assumed setup. S09's explicitly named ambiguity can be reviewed, but posture delivery cannot be presumed. Human reviewers must mark unsupported criteria uncertain/not evaluated instead of scoring missing setup as failed gameplay. See opening_context.json and exact transcripts.

## Human review and coverage

The approved generator produced continuation_worksheet.md/.json for {total_turns} new observations and combined_baseline_worksheet.md/.json for {13 + total_turns} unique baseline turns. Original partial S04 has its own untouched worksheet/result and remains reviewable separately. Every judgment is pending: interpretation, response adequacy, authority, severity, clarification, continuity and conversation-level naturalness. {total_turns} continuation observations are available for human inspection; six S07/S09 observations carry opening-context caveats, so evidence availability is not unconditional criterion eligibility. No raw technical-completion count is a gameplay success. Diagnostic zeros in raw harness reports are unreviewed placeholders, not measured absence of failures. The standard behavioral evidence packet at artifacts/atgb/atgb_03c/behavioral_evidence contains every exact continuation exchange, labeled runtime evidence with all judgments unreviewed; outcome-category selections are unmeasured rather than invented successes/failures.

Benchmarks/versions remain ATGB-02 / ATGB-01 / atgb-rubric-01 / ATGB-02-s07-held-out. Related and previously exposed held-out partitions stay separate. Independent generalization is not demonstrated; single trial, single environment, uncontrolled sampling, opening delivery and API-only observation limit comparability. No gameplay behavior, fixture expectation, rubric, architecture, provider payload, model configuration or production source was changed. Focused infrastructure/dispatch checks and real live API exchanges were run; no full-suite or broad regression claim is made.

## Stop and review

Execution is stopped after this capture/package pass. Review transcripts and setup limitations, then enter authorized human judgments using uncertain/not evaluated where needed. The live evidence capture does not make this a completed gameplay-performance measurement. No conversational repair or Product Realization campaign is initiated. Standard review: handoff/CURRENT_REVIEW.md and handoff/CURRENT_REVIEW.zip.
'''
(ROOT / 'development/reports/atgb_03c_live_baseline_continuation.md').write_text(report, encoding='utf-8')
(OUT / 'baseline_coverage.md').write_text(report.split('## Readiness')[0] + '\nDetailed accounting, limitations and review instructions: development/reports/atgb_03c_live_baseline_continuation.md.\n', encoding='utf-8')

config = {'campaign_id': 'atgb_03c_live_baseline_continuation', 'campaign_name': 'ATGB-03C Initial Live Conversational Baseline Continuation', 'campaign_date': '2026-10-18',
    'purpose': 'Capture the remaining approved live conversations using verified ATGB-03B accounting without changing gameplay.',
    'objective_status': f'{total_turns}/24 CONTINUATION TURNS CAPTURED; HUMAN REVIEW PENDING; OPENING DELIVERY LIMITED',
    'executive_summary': f'{total_turns} new turns; {13 + total_turns}/37 unique baseline turns available. S04 full trial 2 is separate from original partial trial 1. {totals["admitted"]} admissions reconciled. S07/S09 opening delivery absent before first turn; inspect setup caveats before scoring. All judgments pending; no gameplay-performance result or improvement claim.',
    'changes': {'production': [], 'validation': ['No criteria or rubric changes. Provider-disabled readiness and dispatch-owner tests rerun.'], 'tooling': ['Campaign-only preparation/execution/packaging wrappers under artifacts/atgb/atgb_03c; reviewed harness unchanged.'], 'documentation': ['Execution report, coverage summary, current session orientation.'], 'generated_artifacts': ['Seven scenario evidence packages, raw ledgers, isolation/preflight evidence, opening context analysis, approved scoring worksheets and review ZIP.']},
    'testing': {'focused': '104 checks: 103 pass, 1 Windows reset failure; targeted reset reproducibility retry passes. All evidence retained.', 'broader': 'No broad regression rerun; production source unchanged.', 'full_suite': 'Not run.', 'runtime_validation': f'{total_turns} live API player turns; ten final provider-disabled preflights; per-live-scenario preflights.', 'model_runtime_boundary': 'OpenAI gpt-4.1-mini; unchanged model routing; TestClient production API, no browser render check.', 'new_regressions': 'No production change. Opening setup limitations are exposed, not repaired.', 'pre_existing_failures': 'Historical unrelated regression failures unchanged; Windows reset denial retained.'},
    'known_problems': {'campaign_specific': ['S07/S09 authored opening context was not delivered before fixture turns; dependent outcomes unmeasured.', 'Every human judgment remains pending.', 'Dollar expenditure and SDK transport retry counts unavailable.'], 'pre_existing': ['Original S04 partial telemetry remains unavailable and completion-only historical ledger cannot certify admissions.', 'Extensive pre-existing dirty worktree and transient Windows reset write denials.']},
    'decisions_requiring_human_review': ['Review exact exchanges and opening setup limitations; assign interpretation, response and authority separately with uncertain/not evaluated where unsupported.', 'Do not treat this captured baseline as completed gameplay-performance measurement before human review. No repair campaign authorized.'],
    'missing_concepts': ['Delivered opening context is not part of the approved silent-reset chat worker. No new opening injection implemented.'],
    'does_not_prove': ['Conversational improvement, judged gameplay success, independent held-out generalization, multi-environment performance, full regression, browser rendering or absolute SDK transport request bounds.'],
    'recommended_next_step': 'Stop and await human review. Score only supported criteria; retain original/continuation version provenance and separate historical partial S04.',
    'primary_report': 'development/reports/atgb_03c_live_baseline_continuation.md', 'evidence_packets': ['artifacts/atgb/atgb_03c/behavioral_evidence'],
    'self_contained_review_test': 'Bundle verification checks required review sections, every packaged canonical hash, exact approved lines and order, 24 new and 37 unique worksheet rows with no human judgments, original partial S04 separation, lifecycle reconciliation, starting-state evidence and all seven transcripts.',
    'configuration_source': 'artifacts/atgb/atgb_03c/provenance_before.json', 'supporting_files': []}
support = set()
for directory in (OUT, ROOT / 'data/validation/atgb', ROOT / 'tools/atgb'):
    for p in directory.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.name not in ('handoff_build.txt', 'bundle_verification.json') and p.suffix in ('.json', '.jsonl', '.md', '.py', '.txt', '.xml'):
            support.add(p)
for sid in ('S01', 'S02', 'S03', 'S04'):
    support.update(OLD / sid / name for name in ('result.json', 'transcript.md', 'provider_usage.jsonl', 'worksheet.json', 'worksheet.md'))
support.update(ROOT / p for p in ('development/reports/atgb_03_initial_live_baseline.md', 'development/reports/atgb_03b_provider_accounting_integrity.md', 'development/reports/atgb_02_benchmark_specification.md', 'development/reports/atgb_02_execution.md', 'development/reports/atgb_01_conversational_benchmark_design.md', 'docs/NEXT_SESSION.md', 'docs/DEVELOPMENT_CONSTITUTION.md', 'docs/validation_evidence_standard.md', 'tools/run_atgb.py'))
for p in sorted(support):
    config['supporting_files'].append({'path': rel(p), 'role': 'live_conversation_review_evidence', 'why': 'Review capture, provenance, safeguards, setup limitations and pending human judgments.', 'behavioral_evidence': p.name in ('transcript.md', 'result.json', 'session_log.jsonl'), 'human_review_required': 'worksheet' in p.name or p.name == 'transcript.md'})
write(ROOT / 'data/validation/review_handoffs/atgb_03c_live_baseline_continuation.json', config)
print(json.dumps({'turns': total_turns, 'totals': totals, 'preservation': preservation, 'support_files': len(support)}))
