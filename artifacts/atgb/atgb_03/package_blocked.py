"""Prepare factual evidence for the rejected live command; never contact a provider."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.atgb.fixtures import load_corpus
from tools.atgb.results import blank_judgment
from tools.atgb.worksheet import build_worksheet, context_for_turn, render_worksheet

OUT = Path(__file__).parent
def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

provenance = json.loads((OUT / 'configuration_and_provenance.json').read_text())
loaded = load_corpus(ROOT)
preflight = json.loads((OUT / 'preflight/result.json').read_text())
status = []
for scenario in loaded['scenarios']:
    sid = scenario['scenario_id']
    status.append({'scenario_id': sid, 'expected_turns': len(scenario['turns']),
        'execution_status': 'not_attempted', 'cause': 'automatic_approval_review_rejected_live_export',
        'live_turns_captured': 0, 'conversational_evaluation': 'not_evaluated',
        'interpretation': 'not_evaluated', 'response': 'not_evaluated', 'authority': 'not_evaluated',
        'human_review_status': 'pending_no_live_transcript',
        'preflight_ok': next(s['preflight']['ok'] for s in preflight['scenario_records'] if s['scenario_id'] == sid),
        'opening_context_delivery': {'status': 'not_evaluated', 'delivered': None} if sid in {'S07', 'S09'} else None})
write(OUT / 'scenario_status.json', status)
rejection = {'stage': 'A', 'command_started': False, 'live_provider_calls': 0,
    'action': '.venv/Scripts/python.exe artifacts/atgb/atgb_03/execute.py A',
    'destination': 'OpenAI https://api.openai.com/v1',
    'reason': 'Automatic approval review rejected live provider calls because benchmark/gameplay payload export to OpenAI requires explicit user authorization for that destination.',
    'next_action': 'Obtain explicit approval to send the frozen benchmark inputs, authored world/scenario context and isolated conversation history to OpenAI under the declared ceilings. Do not bypass the rejection.',
    'stage_a_acceptance': 'not_evaluated', 'stage_b': 'not_started', 'human_review': 'pending_no_live_transcripts'}
write(OUT / 'execution_blocker.json', rejection)
write(OUT / 'stage_a_acceptance.json', {'accepted': False, 'status': 'blocked_before_execution', 'reason': rejection['reason']})
changes = {group: [p for p, h in provenance[key].items() if not (ROOT / p).is_file() or sha(ROOT / p) != h]
    for group, key in [('execution_sources', 'source_sha256'), ('canonical_campaign_data', 'canonical_data_sha256')]}
write(OUT / 'preservation_checks.json', {'changed_files': changes, 'preserved': not any(changes.values())})
assert not any(changes.values())
test_root = ET.parse(OUT / 'focused_host.xml').getroot()
suites = list(test_root.iter('testsuite'))
tests = {k: sum(int(s.get(k, '0')) for s in suites) for k in ['tests', 'failures', 'errors', 'skipped']}
write(OUT / 'validation_results.json', {'focused_provider_disabled': tests,
    'all_ten_preflights_ok': all(s['preflight']['ok'] for s in preflight['scenario_records']),
    'starting_state_sha256': sorted({s['preflight']['starting_state_sha256'] for s in preflight['scenario_records']}),
    'approved_sources_unchanged': provenance['all_approved_sources_unchanged'],
    'canonical_campaign_data_unchanged': not changes['canonical_campaign_data'],
    'live_provider_calls': 0, 'live_tokens': 'not_measured', 'live_latency': 'not_measured',
    'live_cost': 'not_measured', 'gameplay_performance_claim': False,
    'attempt_limitations': ['First test command failed on missing pytest basetemp parent (5 passed, 19 setup errors); parent then created.',
        'Sandboxed readiness retry stalled; provider-disabled host check and complete suite run outside sandbox separately. See attempt logs.']})

# Build the existing worksheet structure, explicitly labelled as an UNEXECUTED template.
template_turns = []
scenario_records = []
for scenario in loaded['scenarios']:
    from tools.atgb.fixtures import authoritative_context
    scenario_records.append({**scenario, 'authoritative_context': authoritative_context(scenario, loaded['manifest'])})
    for spec in scenario['turns']:
        template_turns.append({**spec, 'scenario_id': scenario['scenario_id'], 'partition': scenario['partition'],
            'response_text': '', 'response_origin': 'not_executed', 'simulated': False,
            'judgment': blank_judgment(), 'state_evidence': None,
            'turn_context': context_for_turn(scenario, spec, loaded['manifest'])})
sheet = build_worksheet({'execution_mode': 'not_executed', 'benchmark_version': 'ATGB-02',
    'rubric_version': 'atgb-rubric-01', 'evidence_distinction': 'not_evaluated',
    'turns': template_turns, 'scenario_records': scenario_records}, loaded['manifest'])
sheet['banner'] = 'UNEXECUTED TEMPLATE. No live AI-DM responses exist. All judgments are pending. Blank responses are not conversational failures. Do not score until an actual transcript is attached. Keep interpretation, response adequacy and authority separate; severity remains unscored.'
write(OUT / 'worksheet_template.json', sheet)
(OUT / 'worksheet_template.md').write_text(render_worksheet(sheet), encoding='utf-8')
history = ROOT / 'handoff/history/atgb_03_predecessor_readiness'
history.mkdir(parents=True, exist_ok=True)
for name in ['CURRENT_REVIEW.md', 'REVIEW_MANIFEST.json', 'CURRENT_REVIEW.zip']:
    target = history / name
    if not target.exists():
        shutil.copyfile(ROOT / 'handoff' / name, target)

report = '''# ATGB-03 — Initial live conversational baseline execution report

Date: 2026-10-18. Status: BLOCKED BEFORE LIVE EXECUTION. This is an incomplete evaluation campaign, not an established baseline or a scored gameplay result.

## Outcome and blocker

The S01 live command was rejected by automatic approval review before process creation. The stated reason was that benchmark/gameplay payloads would be exported to OpenAI and explicit authorization for that data export and destination was required. No live provider requests were issued by this campaign. Do not bypass the rejection. Explicit approval for transmission to OpenAI is needed before the prepared command can run.

Stage A was not executed, so its acceptance criteria are not evaluated. Stage B was not started. There are no live transcripts, live responses, token measurements, retries, response latencies or gameplay scores. All ten scenarios and all 37 turns are NOT EVALUATED. Human judgments remain pending; no capability has an evaluated zero-failure result.

## Authority and configuration

Reviewed the Development Constitution, Validation Evidence Standard, ATGB design/rubric, scenario catalog, implementation specification, execution instructions, ATGB-02A readiness report and standard review handoff requirements. The explicit ATGB-03 request supersedes the prior orientation's instruction to await the request before live execution; the separate automatic approval rejection remains binding.

Benchmark ATGB-02; scenario ATGB-01; partition ATGB-02-s07-held-out; rubric atgb-rubric-01; frozen baseline frontier-gate-v1. Partition counts: 25 visible, 4 related, 8 held-out. Repository HEAD: b012c3d7e5887fdfb09d10bb9cc0f0220de09df9. The worktree was already extensively dirty and untracked. HEAD alone does not identify running bytes: configuration_and_provenance.json records 240 execution/input hashes, and initial_git_status.txt records the initial worktree. Do not commit or revert pre-existing work.

OpenAI is the configured provider (https://api.openai.com/v1); all default, high-precision and retry-escalation model roles are gpt-4.1-mini, with existing routing enabled. Production uses OpenAI SDK Responses and chat-completion paths. Required API-key availability was checked as a boolean; no key was recorded or modified. Provider-disable flags were unset in the live process environment. No sampling or model settings were changed. The harness reports sampling as uncontrolled; individual production owners may set their own parameters.

## Readiness and validation

All 31 checked approved harness/corpus files match ATGB-02A source hashes or its preserved review ZIP. The pinned manifest and all seven frozen input files validate. Ten provider-disabled preflights pass, with the same normalized starting-state hash as ATGB-02A: c12cb0dfe6a31980b4ecc00a59cc359a143a76452e517a36ad76753a6145561a. The existing production chat regression passed outside the sandbox with providers disabled. Full focused readiness/infrastructure checks: TEST_COUNTS. No full repository suite or gameplay evaluation was run.

The first test attempt used a missing parent for the pytest basetemp directory: 5 tests passed and 19 failed at setup. The parent was created and the attempt preserved. The sandboxed retry stalled on the known host-chat environment boundary; the separately authorized provider-disabled checks outside the sandbox passed. These are execution-environment findings, not conversational failures.

Canonical campaign data and all 240 execution/input sources remain byte-identical to the recorded initial state. Scenario stores use the approved isolated data path and reset. The provider-disabled checks do not establish live isolation success; that remains a Stage A acceptance requirement.

## Prepared execution bounds

Prepared campaign wrapper execute.py calls the approved harness without changing its code. Planned total ceiling: 80 application-level provider requests and 1800 elapsed seconds, including the S01 smoke subset of 12 requests and 300 seconds. Each scenario has an independent isolated store. The existing provider accounting guards the per-process request ceiling and writes provider records. The parent passes the remaining campaign allowance between scenarios. Campaign evidence retains stores, raw worker/job JSON, state slices and provider accounting. No failed live attempt is retried automatically.

Cost is unavailable without reliable complete token accounting and a price table; no expenditure estimate is invented. Conservative request/time limits therefore apply. Existing provider accounting also checks token availability; configured high token guardrails prevent its small manual-run defaults from silently truncating this benchmark. Actual token counts would still come only from provider records. SDK-internal transport retries are not independently measured by application-level counters; the elapsed timeout bounds a stalled worker. Usage from an interrupted request may be unavailable. These limitations must remain visible in any resumed live report.

## Scenario status and opening context

scenario_status.json lists every scenario as not attempted due to the approval blocker, with its passing machine preflight separately recorded. S07 and S09 required opening-context delivery is NOT EVALUATED: no player-facing live conversation ran. The silent reset establishes authored seeds, not delivery. No narrative context was injected and no missing setup was scored as conversational failure.

## Human review and evidence

worksheet_template.md/.json use the existing worksheet generator for all 37 expected turns, explicitly labelled UNEXECUTED TEMPLATE. There are no responses to score. Interpretation, response adequacy and authority remain separate; severity, clarification and continuity remain unscored. Conversation-level qualitative fields remain blank. After execution, generate actual worksheets from each live result using the existing harness. Reviewers must distinguish pass, fail, uncertain, unchecked/not evaluated, and infrastructure/setup failure, and preserve minor/major/critical severity. Fluency and authorized content do not establish response adequacy.

Raw preflight result/report/worksheets are preserved as infrastructure evidence only. Their legacy diagnostic zero counts do not establish zero conversational failures. The campaign status and template explicitly say NOT EVALUATED; no live report requiring a reporting-code correction was produced. No success/failure examples, severity judgments, or unscored conversational observations can be supplied without live exchanges. There is no gameplay-performance or improvement claim.

## Comparability and unresolved issues

Held-out scenarios were previously exposed in ATGB-01 and cannot establish fully independent generalization. This is one environment, no repeated live trial, and no human scoring. Dirty-worktree hashes are needed alongside HEAD. S07/S09 delivery remains unresolved. Existing PR-BL versus later PR-EG session-orientation history remains outside scope. No semantic interpreter, routing, fallback, NPC knowledge, scenario expectations, model configuration or production gameplay was changed.

## Next action

Obtain explicit approval to send the frozen benchmark inputs, authored world/scenario context and isolated conversation history to OpenAI at https://api.openai.com/v1 under the stated limits. Then recheck readiness/source hashes and configuration, execute S01 once, inspect actual provider evidence and isolation, and proceed only if infrastructure acceptance succeeds. Do not repair gameplay. Stop after live execution and review-package preparation; scoring requires an authorized human reviewer.
'''.replace('TEST_COUNTS', ', '.join(f'{v} {k}' for k, v in tests.items()))
(ROOT / 'development/reports/atgb_03_initial_live_baseline.md').write_text(report, encoding='utf-8')
previous = json.loads((ROOT / 'data/validation/review_handoffs/atgb_02a_baseline_readiness.json').read_text())
config = {k: previous[k] for k in ['changes', 'testing', 'known_problems']}
config.update({'campaign_id': 'atgb_03_initial_live_baseline', 'campaign_name': 'ATGB-03 Initial Live Conversational Baseline',
    'campaign_date': '2026-10-18', 'purpose': 'Observe existing behavior with the approved live benchmark; blocked before first provider call.',
    'objective_status': 'BLOCKED BEFORE LIVE EXECUTION; NO GAMEPLAY SCORE',
    'executive_summary': 'S01 live execution was rejected by automatic approval review before process creation because explicit benchmark data-export approval to OpenAI is required. All ten preflights and approved-source checks pass; existing chat works with providers disabled. All 37 live turns are not evaluated. No live transcripts or human judgments exist. No production changes.',
    'changes': {'production': ['None; execution sources and canonical campaign data preserved.'], 'validation': [str(tests)], 'tooling': ['Campaign wrapper and provenance/blocked-package scripts only; approved harness unchanged.'], 'documentation': ['Blocked execution report and concise NEXT_SESSION orientation.'], 'generated_artifacts': ['Preflight, source/configuration hashes, all-scenario status, unexecuted scoring templates and approval blocker.']},
    'testing': {'focused': str(tests), 'broader': 'Separate existing provider-disabled chat regression passed.', 'full_suite': 'Not run.', 'runtime_validation': 'All ten preflights pass; hash matches readiness.', 'model_runtime_boundary': 'No live model invocation; automatic approval rejection before execution.', 'new_regressions': 'None observed in focused checks.', 'pre_existing_failures': 'Sandbox host-chat boundary; initial missing pytest basetemp parent preserved.'},
    'decisions_requiring_human_review': ['Approve transmitting the frozen benchmark/gameplay payloads and isolated history to OpenAI (https://api.openai.com/v1), using unchanged gpt-4.1-mini configuration, at most 80 application requests and 30 minutes; S01 at most 12 requests and 5 minutes. Human gameplay scoring follows actual execution.'],
    'known_problems': {'campaign_specific': ['Automatic approval review rejected S01 live export; no live baseline exists.', 'All 37 conversational turns not evaluated; S07/S09 opening delivery not evaluated.'], 'pre_existing': ['Previously exposed held-out content.', 'Dirty worktree; source hashes required.', 'Sandbox host-chat limitation.']},
    'missing_concepts': ['Actual live transcripts and authorized human scoring.'],
    'does_not_prove': ['Any gameplay performance, improvement, authority compliance or conversational competence.', 'S07/S09 opening delivery.', 'Independent generalization or full-suite safety.'],
    'recommended_next_step': 'Obtain explicit OpenAI benchmark payload-export approval, recheck configuration/provenance, run S01, validate infrastructure, then remaining scenarios and human review. No gameplay repairs.',
    'primary_report': 'development/reports/atgb_03_initial_live_baseline.md', 'evidence_packets': [],
    'supporting_files': [],
    'self_contained_review_test': 'Bundle includes blocker, configuration/provenance, all-scenario statuses, preflight, unexecuted worksheet templates, approved baseline/corpus/rubric and execution code. No live exchanges or gameplay judgments exist.'})
paths = [p for p in OUT.rglob('*') if p.is_file() and p.suffix in {'.json', '.jsonl', '.md', '.py', '.txt', '.xml'} and '__pycache__' not in p.parts and p.name not in {'handoff_build.json', 'bundle_verification.json'}]
paths += [ROOT / 'docs/DEVELOPMENT_CONSTITUTION.md', ROOT / 'docs/validation_evidence_standard.md', ROOT / 'docs/review_handoff_standard.md', ROOT / 'docs/NEXT_SESSION.md', ROOT / 'development/reports/atgb_02a_readiness.md', ROOT / 'artifacts/atgb/atgb_02a/validation_results.json']
paths += [ROOT / item['path'] for item in previous['supporting_files'] if item['path'].startswith(('data/validation/atgb/', 'tools/atgb/', 'tools/run_atgb', 'development/reports/atgb_'))]
for p in sorted(set(paths)):
    config['supporting_files'].append({'path': p.relative_to(ROOT).as_posix(), 'role': 'blocked_execution_support', 'why': 'Independent review of blocker, unchanged setup, intended execution and pending scoring.', 'behavioral_evidence': False, 'human_review_required': False})
write(ROOT / 'data/validation/review_handoffs/atgb_03_initial_live_baseline.json', config)
print(json.dumps({'focused': tests, 'scenario_count': len(status), 'worksheet_turns': len(template_turns), 'preserved': True}))
