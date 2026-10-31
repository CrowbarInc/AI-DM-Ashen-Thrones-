"""Offline R1-08 analysis and packaging; never dispatches a provider request."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
REPORT = ROOT / 'development/reports/atgb_r1_08'
REPORT.mkdir(exist_ok=True)

def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

trial = OUT / 'L1'
before = read(trial / 'before.json')
after = read(trial / 'after.json')
traces = read(trial / 'traces.json')
accounting = read(trial / 'accounting.json')
response = read(trial / 'response.json')
timing = read(trial / 'timing.json')
setup = read(trial / 'setup.json')
messages = next(t['locals']['messages'] for t in traces if t['function'] == 'request_interpretation')
evidence = next(t['return'] for t in traces if t['function'] == 'public_conversation_evidence')
call = next(t['return'] for t in traces if t['function'] == 'request_interpretation')
final = response['gm_output']['player_facing_text']
assert accounting['requests'] == 1 and accounting['stopped'] and call['error'] == 'APIConnectionError'
assert not any((OUT / label).exists() for label in ('L2','L3','L4'))
assert timing['sdk_clients'] == [{'max_retries': 0}]
assert all(before[k] == after[k] for k in ('world','scene','character','combat','session'))
assert after['log'][:-1] == before['log']
entry = read(OUT / 'entry_hashes.json')
changed = [p for p,h in entry.items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest() != h]
assert not changed
write(OUT / 'integrity.json', {'protected_entry_files':len(entry),'changed_files':changed,
    'frozen_corpus_unchanged':True,'production_and_prompts_unchanged':True,
    'prior_artifacts_unchanged':True,'session_unchanged':True,'log_appended_rows':1,
    'prior_log_prefix_unchanged':True,'canonical_gameplay_data_unchanged':True})
write(trial / 'request_messages.json', messages)
write(trial / 'evidence_selection.json', {'available_public_evidence':evidence,
    'relevant_people_refs':['visible:1','visible:2','visible:3'],
    'selection':None,'selection_status':'UNAVAILABLE: no model response; not an empty model selection',
    'authorization':'Existing production public_conversation_evidence; passages already delivered in S08.1.'})
write(trial / 'transcript.md', '# L1 — exact conversation\n\nPrior player:\n\n> '+setup['prior_player']+'\n\nPrior GM:\n\n> '+setup['prior_gm']+'\n\nMeasured player:\n\n> '+setup['player_input']+'\n\nFinal GM:\n\n> '+final+'\n\nProvider: APIConnectionError; no model interpretation.\n')
write(OUT / 'provider_accounting.json', {'measured_admission_budget':4,'admissions':1,
    'dispatch_attempts':1,'successful_provider_responses':0,'failed_dispatches':1,
    'input_tokens':None,'output_tokens':None,'total_tokens':None,'estimated_cost':None,
    'unknown_usage_reason':'APIConnectionError; no response usage returned. Unknown is not zero.',
    'sdk_retries':0,'application_retries':0,'automatic_reruns':0,'setup_admissions':0,
    'response_generation_admissions':0,'returned_model':None,'configured_model':'gpt-4.1-mini',
    'end_to_end_ms':timing['end_to_end_ms'],'stop':'Provider failure and unknown usage; L2/L3/L4 not attempted.'})
write(OUT / 'trial_disposition.json', {label:{'input':text,'status':status} for label,text,status in [
    ('L1','I meant the people, not the weather.','FAILED_DISPATCH; semantic assessment unavailable'),
    ('L2','I meant the people, not the weather.','NOT_RUN: mandatory stop'),
    ('L3','No, I was asking about the people, not the weather.','NOT_RUN: mandatory stop'),
    ('L4','Instead, make that a question about the lamp.','NOT_RUN: mandatory stop')]})

reports = {
'01_baseline_and_readiness.md': '''# 01 — Baseline and Readiness

HEAD b012c3d7e5887fdfb09d10bb9cc0f0220de09df9, branch feature/product-realization. Extensive dirty/untracked work predates this validation; entry status and protected hashes are included. No AGENTS.md found in repository search or immediate parent. The requested support/docs/NEXT_SESSION.md does not exist; canonical docs/NEXT_SESSION.md was read, alongside DEVELOPMENT_CONSTITUTION, validation_evidence_standard, product_realization_validation and review_handoff_standard. Reviewed R1-03 results, R1-04 readiness/control, R1-05 live runner/results/accounting, R1-06 causal/evidence findings, and all eight R1-07 reports plus source diff and verification evidence.

Both R1-07 production owners exactly match support/game files in CURRENT_REVIEW(20261019-062339).zip. All 1,047 R1-07 protected hashes match at entry; frozen corpus has 20 files. No material baseline discrepancy. Baseline.json records the comparison. Entry-relative integrity.json verifies production, data, experiments, validation infrastructure and prior artifacts after this pass.

Started from tools/atgb/readiness.py. Validation-only run_trial.py derives from corrected R1-05 runner, not invalid R1-03 runner. L1 was a fresh process and isolated S08 store with new runtime identities. Storage was bound before gameplay imports; canonical gameplay stores were untouched. No test/experimental fixtures imported. Prior S08.1 state/log reconstructed from preserved R1-03 before.json; semantic prior context retained exactly, not a fresh live S08.1 result. Authored opening is preserved in packaged visible/S08.json and baseline scene; current request messages are captured separately. Historical opening-delivery equivalence is reconstructed rather than bit-identical.

L1 preflight: READY, no failed assertions; requested/effective live true; provider configured; all routed model names gpt-4.1-mini; retries disabled; selected experimental flags absent; import flags unchanged; fixture/store equality and isolated store pass; fresh durable ledger; one admission available. SDK constructed with max_retries=0. No pending/executed action in L1. Later trials did not reach setup/preflight after mandatory stop, so their readiness is NOT EVALUATED.

OpenAI Responses endpoint, temperature 0, existing production output cap 320, same configured model/settings as R1-05. Per-trial admission cap intentionally tightened from 2 to 1, matching this request. Token ceilings remain 16000/2000/18000; these are aggregate safety ceilings, not changed generation settings. No returned model version is available. Reachability was deliberately unprobed before the single measured call. No new deterministic test run or full-suite claim: source was unchanged and stop-case evidence was directly inspected.
''',
'02_live_trial_results.md': f'''# 02 — Live Trial Results

| Trial | Exact input | Execution | Interpretation | Evidence selection | Response adequacy | Authority |
|---|---|---|---|---|---|---|
| L1 | I meant the people, not the weather. | APIConnectionError | INDETERMINATE | INDETERMINATE | FAIL: delivered fallback | PASS within observed failed-call scope |
| L2 | I meant the people, not the weather. | NOT RUN: stop | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED |
| L3 | No, I was asking about the people, not the weather. | NOT RUN: stop | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED |
| L4 | Instead, make that a question about the lamp. | NOT RUN: stop | NOT EVALUATED | NOT APPLICABLE/NOT EVALUATED | NOT EVALUATED | NOT EVALUATED |

L1 prior player: {setup['prior_player']}

L1 prior GM (exact): {setup['prior_gm']}

Active topic: immediately visible scene, corrected toward people. No active NPC interlocutor or pending gameplay intention. Catalog includes gate_guard, gate_serjeant, tavern_runner and notice_board. Public evidence visible:1–3 describes serjeant, runner, watchers/refugees; full prior reply is reply:0.

L1 final text (exact):

> {final}

No raw model response, parsed interpretation, purpose, mode, selected referents, unresolved references, evidence selection or clarification question exists. Do not confuse unavailable selection with model-returned []. Request construction and public evidence builder ran; live interpretation blocked with provider_failure/APIConnectionError. Mechanical revision and conversational answer routing were not reached after the failure. Host emitted its deterministic interpretation_rejected fallback, with no resolver/parser/narration invocation or additional provider admission.

L1 used one admission, zero successful model responses, one failed dispatch, {timing['end_to_end_ms']} ms end-to-end; token usage unknown. L2/L3/L4 were not substituted, retried or executed. All judgments are provisional AI-assisted observations; authenticated human review pending.
''',
'03_interpretation_and_evidence_analysis.md': '''# 03 — Interpretation and Evidence Analysis

The actual messages passed into production request_interpretation are saved as L1/request_messages.json and in traces.json. Their system instructions include the R1-07 distinctions: supplied correction versus GM clarification, INTERPRETED GM/CORRECTION with legacy OTHER, no action components, recover corrected underlying question, select relevant PUBLIC evidence, avoid redundant confirmation, and preserve actual pending-intention authority. Current source exactly matches reviewed R1-07, including schema descriptions. These messages are application construction evidence; no assertion of remote receipt or successful inference is possible after APIConnectionError. Complete HTTP wire serialization was not independently intercepted.

Public builder return and request contain visible:1 (gate serjeant), visible:2 (tavern runner), visible:3 (watchers/refugees), plus reply:0. These already emitted public facts suffice for the narrow people description. Availability and authorization are established; model selection is unavailable. No model classification, mode, referent choice, validation result, evidence reference or redundant-clarification decision can be judged.

Earliest observed interruption: provider dispatch failed before interpretation. This is an execution/environment blocker, not demonstrated ineffectiveness of the R1-07 contract. Underlying connection cause is unresolved; sandbox/network restrictions are a possible hypothesis only, not proven. No retry, connectivity probe or escalation was attempted after this stop. Downstream: host blocked interpretation and emitted a nonexecuting fallback; semantic dimensions remain indeterminate.

R1-05 redundant CLARIFICATION/empty evidence and R1-03 L3's same outcome remain historical facts. This pass supplies no new comparable interpretation, so it cannot establish persistence or correction of that defect. The special clarification/empty-selection failure-localization branches are inapplicable without model output. No fixes implemented.
''',
'04_response_adequacy_and_naturalness.md': f'''# 04 — Response Adequacy and Naturalness

Only L1 produced a new final player-facing response:

> {final}

Response adequacy FAIL for answering the correction: it supplies neither acknowledgment of the corrected subject nor people information despite available public passages. This is the host's provider-failure fallback, not evidence that the model chose a poor conversational answer. No correction acknowledgment was applied; no evidence was realized; no redundant clarification was asked. The fallback explains the operational failure plainly and asserts no world facts, but interrupts the conversational thread and cannot test the naturalness of the intended repaired continuation.

Naturalness of a correction answer is NOT EVALUATED. No quantitative naturalness score is invented. L2/L3/L4 have no final text. Completeness, generalization and pending-action revision meaning remain unmeasured. Exact prior and final text is in L1/transcript.md; the full response and metadata are in response.json. No response-generation call occurred.
''',
'05_mechanical_revision_and_authority.md': '''# 05 — Mechanical Revision and Authority

L4 was NOT RUN because L1 triggered mandatory stop. Its setup was not invoked, and no pending intention was created in this pass. R1-04's validated deterministic pathway remains available: seed copied control content with pending context cleared; send “I ask one of them what happened.” through production chat with a deterministic setup interpretation; production ambiguity handling creates an unexecuted ASK with Sergeant Mara/Corporal Bren choices. Only then could the measured live lamp revision run. No substituted measured interpretation is presented here. Revision preservation, unresolved target handling and nonexecution under successful live revision remain NOT EVALUATED now.

L1 before.json and after.json show identical world (including factions/events), scene, character, combat and entire session. Consequently simulation date/time, clocks, turn, pending/executed intention and conversational session state are identical. There is no pending intention before or after; no fabrication, rollback or premature action observed. Log differs only by one appended failure exchange; prior rows are unchanged. This is permitted transcript recording, not a simulation/world event. Host metadata confirms authoritative_mutation=false, resolver_invoked=false, gameplay_parser_invoked=false, narration_invoked=false and no state_changes.

Disclosure: the final fallback supplies no scene facts or restricted information. Request evidence came from the unchanged public-evidence projection; no new disclosure authority introduced. Canonical gameplay data and prior artifacts match entry hashes. No unauthorized state mutation or restricted player disclosure observed in L1. Authority PASS applies narrowly to this failed-dispatch path; it is not successful live correction/revision authority validation. L2/L3/L4 authority is NOT EVALUATED.
''',
'06_historical_comparison.md': '''# 06 — Historical Comparison

| Dimension | R1-05 L1/L2 historical | R1-08 L1 | R1-08 L2 |
|---|---|---|---|
| Correction routing | repaired guard abstains | not reached after provider failure | not run |
| Subject recognition | correct people/weather contrast | unavailable | not run |
| Mode/purpose | redundant CLARIFICATION | unavailable | not run |
| Evidence | [] despite visible:1–3 | unavailable, not [] | not run |
| Response adequacy | failed redundant confirmation | failed operational fallback | not run |
| Authority | preserved in tested controls | preserved failed-call state | not run |
| Usage | 2215 / 2214 tokens | unknown after admitted failed dispatch | no admission |

R1-03 L3 historical: “Do you want a description of the people present at the gate district instead of the weather?” GM/CLARIFICATION, no evidence selected. R1-06 corrected the older trace summary: raw L3 does reach _pending_revision_decision, returning null. Historical reports/records remain unchanged. New L3 was not run; no paraphrase comparison possible.

R1-05 L4 historical: live revision preserved pending status and original NPC choices without executing; topic/recipient conflation remains a documented limitation. New L4 was not run, so neither preservation nor regression can be claimed.

Configured model gpt-4.1-mini, temperature 0, production output cap 320 and SDK retries 0 match historical settings. Historical returned model was gpt-4.1-mini-2025-04-14; new returned model unknown. Per-trial admission allowance tightened to one; no generation setting changed. Same preserved S08.1 reconstruction, fresh identities and isolated process/store. L1 failure resembles R1-03's connection failure but does not establish the same root cause. No live improvement, regression, broad reliability, independent generalization or benchmark score is established.
''',
'07_provider_accounting.md': f'''# 07 — Provider Accounting

| Trial | Admissions | Dispatches | Responses | Failures | Input tokens | Output tokens | Total tokens | End-to-end ms |
|---|---:|---:|---:|---:|---|---|---|---|
| L1 | 1 | 1 | 0 | 1 | unknown | unknown | unknown | {timing['end_to_end_ms']} |
| L2 | 0 | 0 | 0 | 0 | not applicable | not applicable | not applicable | not run |
| L3 | 0 | 0 | 0 | 0 | not applicable | not applicable | not applicable | not run |
| L4 | 0 | 0 | 0 | 0 | not applicable | not applicable | not applicable | not run |

Budget compliance: 1/4 admissions used. One admission and dispatch marker are durably recorded before the failed SDK request; completion is failed. SDK max_retries=0 observed on the actual single client. Zero SDK retries, application retries, reruns, setup provider calls, exploratory calls, model switches or response-generation admissions. Unused allowance was not spent. No further trials after failure/unknown usage.

APIConnectionError is captured by request_interpretation and response resolution metadata. Ledger error is generic provider_error; stopped reason provider usage accounting unavailable. Tokens and estimated cost are UNKNOWN, never zero. No request ID or returned model version. Application admission is certain; remote receipt/processing/billing is unknown. Recorded dispatch latency {accounting['records'][0]['latency_ms']} ms excludes local setup/client construction; end-to-end {timing['end_to_end_ms']} ms includes preflight/host. No performance improvement judgment.

Important telemetry discrepancy: response metadata provider_calls.interpretation_requests and performance.provider_call_count report 0 because failure returns no provider_requests. Durable provider_budget accounting and request_interpretation.sent=true prove ONE actual application admission/dispatch. This report uses the durable ledger, not the zero completion-path counter. The prior-turn log includes historical provider records; those are reconstructed context, not new admissions. Per-process measured ledger is the accounting authority. No production telemetry fix authorized or implemented.
''',
'08_final_verdict.md': '''# 08 — Final Verdict

**D — Inconclusive.** L1 passed readiness and included the R1-07 correction/evidence instructions and sufficient public people evidence. Its single dispatch failed with APIConnectionError before a model interpretation became available; token usage is unknown. Mandatory stop prevented L2/L3/L4. The live effect of R1-07 remains unmeasured.

Do not accept the bounded S08.2 live repair on this evidence. This is withholding live acceptance, not rejection of the reviewed deterministic implementation. No conversational ineffectiveness or authority regression is demonstrated. L1 delivered an inadequate but nonexecuting failure fallback; observed gameplay snapshots are unchanged. L4 mechanical revision preservation is not evaluated in this pass. Historical deterministic and live results retain their original scope.

Remaining uncertainty: provider connection cause, remote receipt/billing, returned model version, live classification/evidence selection, correction-answer adequacy/naturalness, repeat consistency, paraphrase behavior and live pending-action preservation. Assessment is AI-assisted and UNREVIEWED by an authenticated human. No full-suite or full benchmark result; no broad reliability claim.

Further S08.2 validation is justified, but no semantic fix is supported by this failed dispatch. One recommended next step: external review of this packet, followed by a separately authorized validation pass in a verified provider-capable environment with a fresh explicit budget. Do not resume or retry this pass automatically, and do not implement another repair from this evidence.

Confirmations: no production code changes; no prompt/schema/model-setting changes; no unauthorized provider calls; one authorized failed admission, with zero SDK retries; no PR-EG candidates merged; frozen ATGB and canonical gameplay data unchanged; no unauthorized gameplay mutation or restricted player disclosure observed; no commits/pushes. Explicit payload selection and supplementary secret-pattern scan exclude credentials/local configuration from the review. Stop after ZIP generation and await external review.
'''
}
for name, content in reports.items():
    write(REPORT / name, content)

from tools.validation_evidence import build_packet, write_packet
packet = build_packet(campaign={'campaign_id':'atgb_r1_08','what_was_tested':'One attempted S08.2 live correction; mandatory stop after provider failure.',
    'runtime_path':'Direct game.api.chat with R1-04 readiness and isolated S08 store',
    'gm_boundary':'One failed gpt-4.1-mini interpretation dispatch; deterministic host fallback',
    'player_input_mode':'Frozen representative correction', 'run_count':1,'turn_count':1,
    'automated_conclusion':'D — Inconclusive; model semantics unavailable.'},
    claim_types=['runtime_evidence'],examples=[{'example_id':'ATGB-R1-08-L1','scenario_run_id':'L1/S08','turn_index':2,
    'player_input':setup['player_input'],'player_input_classification':['representative_player_behavior'],
    'relevant_prior_context':{'player':setup['prior_player'],'gm':setup['prior_gm']},
    'exact_gm_output':final,'semantic_result':'FAIL','historical_result':'New operational fallback; no model semantic judgment',
    'mandatory_gates':{'interpretation':{'status':'INDETERMINATE'},'evidence':{'status':'INDETERMINATE'},'authority':{'status':'PASS','scope':'failed-call path only'}},
    'diagnostic_result':{'result':'APIConnectionError; response inadequacy is fallback-only'},
    'automated_evaluation':{'status':'No gameplay scorer run; AI-assisted independent dimensions in reports'},
    'runtime_validity':{'preflight':'READY','model_response':False,'failure':'APIConnectionError'},
    'final_emission_metadata':response['resolution']['metadata'],
    'continuation_decision':{'continue':False,'reason':'Mandatory stop: provider failure and unknown usage'},
    'source_artifact_path':'artifacts/atgb/atgb_r1_08/L1/response.json',
    'human_review':{'status':'UNREVIEWED','rationale':'Provisional AI-assisted analysis; no authenticated human review'},
    'evaluator_disagreement':{'present':False},'evaluator_disagreement_history':[],'calibration_reference':None}],
    missing_concepts=[],limitations=['One failed dispatch, no successful live interpretation; three trials not run.',
    'FAIL describes fallback response adequacy, not model correction quality.',
    'No benchmark score, generalization, successful L4 control or authenticated human review.'])
write_packet(ROOT/'artifacts/validation_evidence/atgb_r1_08', packet)

handoff = (OUT/'NEXT_SESSION_before.md').read_text(encoding='utf-8')
position = handoff.index('## Current position')
intro = '''## Latest validation — ATGB-R1-08

2026-10-19: **D — Inconclusive**. Reports: development/reports/atgb_r1_08/;
evidence: artifacts/atgb/atgb_r1_08/; packet: artifacts/validation_evidence/atgb_r1_08/.
R1-07 production files match reviewed ZIP; all 1,047 prior protected hashes match.
L1 fresh isolated S08 readiness passed with one-admission cap and zero SDK retries,
but its one dispatch failed with APIConnectionError. Tokens/cost/returned version
unknown. Mandatory stop: L2/L3/L4 not run; no retries or further live authority.
Actual messages include R1-07 instructions and relevant public evidence. No model
interpretation exists; no repair-effect or mechanical-control result. World, scene,
character, combat and full session unchanged; only failure transcript appended.
Durable ledger counts one admission despite response completion counters showing zero.
No production/prompt/schema/frozen corpus/experiment/gameplay-data changes.
Review: handoff/CURRENT_REVIEW.md and timestamped ZIP. Withhold live S08.2 acceptance;
external review, then separately authorize a new pass in a provider-capable environment.
Do not retry this pass automatically or implement a fix from the connection failure.
The older conditional implementation and historical stop language below is preserved.

'''
write(ROOT/'docs/NEXT_SESSION.md', handoff[:position]+intro+handoff[position:])
write(OUT/'repository_status_after.txt', subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True))
write(OUT/'commands.json', [{'command':'.venv/Scripts/python.exe artifacts/atgb/atgb_r1_08/run_trial.py L1','exit_code':0,'provider_outcome':'APIConnectionError; one admission; mandatory stop'},
    {'command':'.venv/Scripts/python.exe artifacts/atgb/atgb_r1_08/package_review.py','purpose':'offline analysis, reports, integrity and review export', 'initial_attempt':'Offline generation reached standard ZIP, then failed timestamp step: tzdata unavailable. Corrected with explicit EDT UTC-04 offset for 2026-10-19; rerun performs no live calls.'}])

support = list(REPORT.glob('*.md'))
support += [p for p in OUT.rglob('*') if p.is_file() and 'store' not in p.relative_to(OUT).parts and p.name not in ('review_config.json','package_result.json','zip_verification.json')]
support += [ROOT/p for p in ['docs/NEXT_SESSION.md','docs/DEVELOPMENT_CONSTITUTION.md','docs/validation_evidence_standard.md','docs/product_realization_validation.md',
    'game/live_chat_interpretation.py','game/conversational_orchestration.py','tools/atgb/readiness.py',
    'data/validation/atgb/visible/S08.json','data/validation/atgb/baselines/frontier-gate-v1/scenes/frontier_gate.json',
    'development/reports/atgb_r1_05/02_live_trial_results.md','development/reports/atgb_r1_05/07_provider_accounting.md',
    'development/reports/atgb_r1_03/02_live_trial_results.md','development/reports/atgb_r1_04/05_pending_action_control.md',
    'development/reports/atgb_r1_06/04_evidence_selection_analysis.md','development/reports/atgb_r1_07/08_final_verdict.md']]
config={'campaign_id':'atgb_r1_08','campaign_name':'ATGB-R1-08 Live Conversational Correction Validation','campaign_date':'2026-10-19',
    'purpose':'Bounded live validation only; mandatory stop after provider failure.',
    'objective_status':'D — Inconclusive; await external review',
    'executive_summary':'L1 passed readiness but one admitted dispatch failed with APIConnectionError; usage unknown. L2/L3/L4 not run. Live repair effect remains unmeasured; gameplay state unchanged.',
    'changes':{'production':[],'validation':['One authorized measured admission, failed before model response.'],
    'tooling':['Validation-only adaptation of corrected R1-05 runner; offline packaging.'],
    'documentation':['Eight reports and canonical NEXT_SESSION update.'],'generated_artifacts':['Complete available request/host/state/accounting evidence.']},
    'testing':{'focused':'Reviewed prior deterministic evidence; no new pytest run.','broader':'Not run.','full_suite':'Not run.',
    'runtime_validation':'Direct production chat; one failed interpretation dispatch.','model_runtime_boundary':'Configured gpt-4.1-mini; returned version unavailable; retries zero.',
    'new_regressions':'None demonstrated; semantic behavior unmeasured.','pre_existing_failures':'Known historical conversational inadequacy remains untested by this failed call.'},
    'known_problems':{'campaign_specific':['APIConnectionError; unknown usage; L2/L3/L4 not evaluated.','Response completion counters report zero; durable ledger records one actual admission.'],
    'pre_existing':['Broad conversational competence and authenticated human assessment remain unestablished.']},
    'decisions_requiring_human_review':['Review inconclusive result; live repair acceptance withheld. Any next live pass needs separate authorization.'],
    'missing_concepts':[],'does_not_prove':['Live repair improvement/ineffectiveness, L4 preservation, broad reliability, independent generalization or benchmark performance.'],
    'recommended_next_step':'External review, then separately authorize validation in a verified provider-capable environment with a new explicit budget. No automatic retry or implementation.',
    'primary_report':'development/reports/atgb_r1_08/08_final_verdict.md','evidence_packets':['artifacts/validation_evidence/atgb_r1_08'],
    'self_contained_review_test':'Eight reports; full available transcript/messages/traces/before-after snapshots/ledger; historical comparison; protected hashes and explicit unknowns included.',
    'configuration_source':'artifacts/atgb/atgb_r1_08/review_config.json',
    'supporting_files':[{'path':p.relative_to(ROOT).as_posix(),'role':'validation_evidence','why':'Explicit scope-relevant review source.','behavioral_evidence':p.name in ('transcript.md','traces.json','response.json'),'human_review_required':True} for p in support]}
config['supporting_files'].append({'path':'artifacts/atgb/atgb_r1_08/review_config.json','role':'configuration_provenance','why':'Explicit bundle selection.'})
write(OUT/'review_config.json',config)
for p in support + [OUT/'review_config.json']:
    assert not any(re.search(pattern,p.read_bytes()) for pattern in [rb'\bsk-[A-Za-z0-9_-]{16,}',rb'Bearer\s+[A-Za-z0-9_.-]{16,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']), 'Potential secret; inspect locally without printing.'
from tools.build_review_handoff import build_handoff
result=build_handoff(config, root=ROOT, output_dir=ROOT/'handoff', archive_history=True)
# Client date is 2026-10-19, within Eastern daylight time (UTC-04).
timestamp=datetime.now(timezone(timedelta(hours=-4))).strftime('%Y%m%d-%H%M%S')
target=ROOT/'handoff'/f'CURRENT_REVIEW({timestamp}).zip'
shutil.copyfile(result['zip_path'],target)
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
    verified=0
    for row in manifest['included_files']:
        if row['sha256'] is not None:
            assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
            verified+=1
    assert len([n for n in z.namelist() if n.startswith('support/development/reports/atgb_r1_08/') and n.endswith('.md')])==8
    assert 'support/artifacts/atgb/atgb_r1_08/L1/traces.json' in z.namelist()
    assert 'support/artifacts/atgb/atgb_r1_08/L1/provider_usage.jsonl' in z.namelist()
    assert 'support/artifacts/atgb/atgb_r1_08/L1/before.json' in z.namelist()
    assert 'support/artifacts/atgb/atgb_r1_08/L1/after.json' in z.namelist()
    assert not any(any(re.search(pattern,z.read(name)) for pattern in [rb'\bsk-[A-Za-z0-9_-]{16,}',rb'Bearer\s+[A-Za-z0-9_.-]{16,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']) for name in z.namelist())
verification={'zip':str(target),'crc_valid':True,'payload_hashes_verified':verified,'report_count':8,
    'supplementary_secret_scan_findings':0,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
    'verdict':'D — Inconclusive','provider_admissions':1,'live_execution_stopped':True}
write(OUT/'zip_verification.json',verification)
print(json.dumps(verification,indent=2))
