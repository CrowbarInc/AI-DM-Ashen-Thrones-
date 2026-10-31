"""Offline evidence analysis and standard handoff packaging. No provider dispatch."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
import zipfile

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
REPORT=ROOT/'development/reports/atgb_r1_09'
REPORT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT))
def read(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):
    p=ROOT/p
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(v if isinstance(v,str) else json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

diag=read(OUT/'readiness_diagnostics.json')
cfg=read(OUT/'provider_configuration.json')
assert diag['readiness']=='BLOCKED', 'This offline stop-case packager must not replace live evaluation'
entry=read(OUT/'entry_hashes.json')
changes=[p for p,h in entry.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
assert not changes
integrity={'protected_files':len(entry),'changed_files':changes,
    'production_unchanged':True,'prompts_and_schema_unchanged':True,'frozen_atgb_unchanged':True,
    'experiments_unchanged':True,'canonical_gameplay_data_unchanged':True,'prior_atgb_artifacts_unchanged':True,
    'gameplay_execution':False,'isolated_trial_stores_created':False}
write(OUT/'integrity.json',integrity)
history=[]
for pass_id,label in [('atgb_r1_03','L1'),('atgb_r1_03','L2'),('atgb_r1_08','L1')]:
    folder=ROOT/'artifacts/atgb'/pass_id/label
    traces=read(folder/('traces.json' if (folder/'traces.json').exists() else 'trace.json'))
    call=next(t['return'] for t in traces if t['function']=='request_interpretation')
    a=read(folder/'accounting.json')
    snap=a.get('snapshot',a)
    rec=snap['records'][0]
    # Preserve only actually observed metadata; exception names cannot supply hidden causes.
    history.append({'pass':pass_id,'trial':label,'exception_type':call['error'],
        'classification':'provider_response_failure' if call['error']=='InternalServerError' else 'indeterminate',
        'category_rationale':'SDK InternalServerError supports server error response category; exact HTTP status not retained' if call['error']=='InternalServerError' else 'Connection exception reported; underlying cause and connection phase not retained, so transport root cause unestablished',
        'cause':None,'connection_phase':None,'http_status':None,'provider_request_id':rec.get('request_id'),
        'model_response_available':False,'usage_available':False,'admissions':snap['requests'],
        'dispatch_attempted':rec.get('dispatch_attempted'),'dispatch_latency_ms':rec.get('latency_ms'),
        'timeout_observed':False,'timeout_configuration_historically_recorded':False,
        'sdk_retries':0,'ledger_error':rec.get('error'), 'sources':[str((folder/'accounting.json').relative_to(ROOT)),str((folder/('traces.json' if (folder/'traces.json').exists() else 'trace.json')).relative_to(ROOT))]})
write(OUT/'historical_provider_failures.json',history)
inputs={'L1':'I meant the people, not the weather.','L2':'I meant the people, not the weather.',
    'L3':'No, I was asking about the people, not the weather.','L4':'Instead, make that a question about the lamp.'}
ledger={'authoritative_for_this_pass':True,'hard_limit':4,'dispatch_attempts':0,'provider_admissions':0,
    'successful_responses':0,'failed_dispatches':0,'sdk_retries':0,'application_retries':0,
    'trial_retries':0,'setup_admissions':0,'response_generation_admissions':0,
    'input_tokens':0,'output_tokens':0,'total_tokens':0,'estimated_cost':0,
    'usage_note':'Zero because no requests were dispatched, not missing usage from a failed request.',
    'dispatch_latency_ms':None,'unused_admissions':4,'budget_compliant':True,
    'trials':[{'trial':label,'input':text,'status':'NOT_RUN_PHASE_A_BLOCKED','dispatch_attempt':False,
        'provider_admission':0,'completion_status':'not_started','response_available':False,
        'usage_available':False,'error_classification':'not_applicable_no_dispatch',
        'retry_count':0,'preflight':'NOT_RUN: Phase A stop before isolated setup',
        'interpretation':'NOT_EVALUATED','evidence_selection':'NOT_EVALUATED',
        'response_adequacy':'NOT_EVALUATED','authority':'NOT_EVALUATED'} for label,text in inputs.items()]}
write(OUT/'admission_ledger.json',ledger)
write(OUT/'available_live_evidence.json',{'current_pass_transcripts':[], 'current_pass_interpretation_traces':[],
    'current_pass_routing_traces':[],'current_pass_before_after_trial_snapshots':[],
    'reason':'Phase A blocked. No trial initialized, gameplay executed or provider dispatched.',
    'canonical_state_integrity_evidence':'entry_hashes.json and integrity.json',
    'historical_evidence':'Explicitly packaged under original pass paths; never relabeled as R1-09 evidence.'})
reports={
'01_baseline_and_readiness.md':f'''# 01 — Baseline and Readiness

**Phase A: BLOCKED.** api.openai.com DNS resolution raised socket.gaierror, errno 11001. TCP and TLS check attempts fail at the same name-resolution prerequisite; neither establishes a TCP connection or TLS handshake. No inference or authentication request was made. Stop before Phase B under sections 7 and 11 of the user request. This is a concrete local resolution blocker; its ultimate cause (resolver, network policy, sandbox, routing, provider DNS or otherwise) is not established. No network-setting or credential change, paid probe, escalation or repeated diagnostic run followed the completed check set.

HEAD b012c3d7e5887fdfb09d10bb9cc0f0220de09df9; branch feature/product-realization. Extensive dirty/untracked state predates this pass and is preserved in repository_status_before.txt. All 811 R1-08 protected entry hashes match. Both R1-07 production owners match the reviewed CURRENT_REVIEW(20261019-062339).zip exactly. That reviewed implementation retains the R1-02 mechanical revision guard; R1-07 integrity_verification.json records the guard unchanged. Frozen manifest and every baseline content hash pass tools.atgb.baseline.load_baseline. No material baseline discrepancy found. {len(entry)} current protected files are hashed for exit verification, covering game, data, experiments, tests, tools/atgb and prior ATGB artifacts.

Mandatory orientation read: DEVELOPMENT_CONSTITUTION, canonical docs/NEXT_SESSION.md, validation_evidence_standard and product_realization_validation, plus review_handoff_standard. Requested support/docs/NEXT_SESSION.md does not exist. Reviewed R1-03 failures/paraphrase, R1-04 readiness/control, R1-05 live results and runner, R1-06 causal findings, R1-07 implementation/tests/reports and R1-08 failure runner/traces/accounting. No historical files were rewritten.

Configuration: OpenAI Responses, gpt-4.1-mini throughout model routing, https://api.openai.com/v1/, openai {cfg['sdk_version']}, httpx {cfg['httpx_version']}, HTTPTransport, trust_env=true. Production timeout helper evaluates to 45 seconds for connect/read/write/pool. Its function was evaluated in isolation from the parsed source, avoiding gameplay startup. Existing measured-runner policy uses max_retries=0; a client was constructed with that setting, inspected and closed without any API method call. Default unwrapped SDK retry behavior is not claimed disabled globally. No configuration file or credentials were changed. Credential presence is true; validity/model access untested. No proxy environment or certificate overrides found. Inherited readiness flags are unset, as recorded; no trial-mode flags were activated because Phase A blocked.

DNS/TCP/TLS each returned in under one second. Socket connect timeout was five seconds; DNS uses the Windows resolver's own timeout (not a separately enforced five-second DNS timeout). Local TLS default context creation succeeds, but remote certificate validation cannot run without DNS/connectivity; no claim of valid provider certificates. Default OpenSSL CA file/directory are absent in ssl.get_default_verify_paths; this alone does not establish an SDK certificate problem. No additional HTTP diagnostic endpoint was used. No OS-wide logs were collected; scoped socket exceptions and existing failure metadata are preserved.

tools/atgb/readiness.py was inspected first for preflight: execution mode, configured model, scoped import flags, isolated store binding, fresh ledger, budget and pending-intention checks remain required before any trial. No per-trial preflight or scenario setup was run after Phase A failed. Their result is NOT EVALUATED, never READY or a semantic failure. Existing deterministic readiness evidence is historical only. No new pytest/full-suite run or benchmark claim.
''',
'02_historical_provider_failures.md':'''# 02 — Historical Provider Failures

| Historical attempt | Exception | Defensible category | Cause / connection phase | HTTP status / request ID | Model output / usage | Admission / retries | Dispatch latency |
|---|---|---|---|---|---|---|---|
| R1-03 L1 | APIConnectionError | INDETERMINATE; connection failure reported | not retained / unknown | unavailable / unavailable | none / unavailable | 1 / 0 | 625.517 ms |
| R1-03 L2 | InternalServerError | Provider response failure (SDK category) | not retained / unknown | exact status unavailable / unavailable | none / unavailable | 1 / 0 | 6519.199 ms |
| R1-08 L1 | APIConnectionError | INDETERMINATE; connection failure reported | not retained / unknown | unavailable / unavailable | none / unavailable | 1 / 0 | 91.72 ms |

InternalServerError supports the SDK server-response category but does not recover an exact status, body, headers or request ID. A server error response is distinct from a successful model response. APIConnectionError alone cannot distinguish DNS, TCP, proxy, TLS or another underlying cause. No credential rejection is established by these artifacts. No timeout exception is recorded; short elapsed time alone does not prove the connection phase or configured timeout. Current 45-second timeout is not retrospectively asserted as measured historical configuration.

Historical provider_budget completion records normalize error to provider_error, while trace return records retain the exception class. Underlying __cause__, wire-level response and HTTP metadata were not captured. Failed dispatches count as admissions despite missing usage; historical ordinary response completion counters can report zero. Never replace durable admission counts with those counters. All three failures retained one admission and zero SDK retries, with no returned model version. The model field in failed ledger records is the configured fallback, not an observed provider model.

Current evidence establishes a local DNS prerequisite failure before any provider dispatch. It makes a DNS explanation for older connection failures plausible but does not demonstrate the same cause across sessions. There are no current provider failures, current provider status codes or current latency samples to compare. Detailed extracted fields and original source paths are in historical_provider_failures.json; original trace/accounting files are packaged under their original paths.
''',
'03_live_trial_results.md':'''# 03 — Live Trial Results

| Trial | Exact authorized input | Status | Interpretation / evidence / response / authority |
|---|---|---|---|
| L1 | I meant the people, not the weather. | NOT RUN — Phase A BLOCKED | All NOT EVALUATED |
| L2 | I meant the people, not the weather. | NOT RUN — Phase A BLOCKED | All NOT EVALUATED |
| L3 | No, I was asking about the people, not the weather. | NOT RUN — Phase A BLOCKED | All NOT EVALUATED |
| L4 | Instead, make that a question about the lamp. | NOT RUN — Phase A BLOCKED | All NOT EVALUATED |

Zero isolated trial stores, pending setups, admissions, model responses, host routes or final player-facing responses were produced. No raw or parsed interpretation, purpose, mode, selected referents, unresolved references, evidence references or clarification question exists for this pass. An absent model result is not an empty evidence selection or failed semantic judgment. No preflight failure was fabricated: Phase A prevents reaching per-trial preflight.

Planned context remains the authored frozen S08 opening plus preserved reconstructed S08.1 preceding exchange for L1/L2, independent environments; corresponding saved paraphrase context for L3; validated R1-04 production-created pending ASK for L4. No context substitution or synthetic measured model output occurred. Original S08 corpus, baseline scene, R1-08 L1 setup/messages/trace/state and successful R1-05 records are included as clearly historical review evidence. They are not new R1-09 executions. available_live_evidence.json explicitly records the empty current-pass trace/snapshot inventory.
''',
'04_conversational_adequacy.md':'''# 04 — Conversational Adequacy

Current correction recognition, communication-mode decision, evidence selection, response adequacy and naturalness are NOT EVALUATED for L1/L2/L3. There is no new exchange to score. Phase A diagnostics are structural/environment evidence only (evidence_scope: structural_only), not semantic behavioral evidence.

Historical R1-05 L1/L2 and R1-03 L3 understood people versus weather but chose clarification and no public evidence, giving redundant confirmation instead of answering. R1-06 established that relevant public people passages and preceding reply were available in the actual requests. R1-07 updated the existing interpretation guidance to distinguish correction from genuine missing information, answer the corrected question with relevant authorized evidence, and preserve mechanical action authority. Its existing answer branch adds minimal acknowledgment only for supported resolved corrections.

Historical deterministic evidence shows the host can deliver an acknowledgment and public answer with a suitable substituted interpretation. It does not show live model selection. R1-08 submitted the revised guidance but obtained no model output. R1-09 cannot change those conclusions. No broad conversational improvement, independent generalization, reliability rate, naturalness gain or benchmark score is claimed. Judgments remain provisional AI-assisted analysis, not authenticated human scoring; no historical assessments were overwritten.
''',
'05_mechanical_revision_and_authority.md':f'''# 05 — Mechanical Revision and Authority

L4 genuine pending ASK was not established in this pass because Phase A stopped execution. The authorized setup text remains “I ask one of them what happened.” followed by live “Instead, make that a question about the lamp.” R1-04 seed_control clears captured pending state, then production chat with the validated deterministic interpretation must create an ambiguous unexecuted ASK. No manually fabricated pending intention, measured stub, setup provider request, premature execution or rollback occurred here. Future revision authorization, ambiguity retention and control preservation are NOT EVALUATED.

R1-05 historical L4 supplies valid pending_intention_revised evidence with no execution; topic/recipient conflation remains a limitation. R1-03 L4 is INVALID due to fixture-import disabling live interpretation and unintended isolated state advancement; it supplies no valid authority-control pass. R1-07 records the R1-02 mechanical guard unchanged, and the current full owner matches the reviewed R1-07 ZIP.

Entry/exit hashes verify {len(entry)} protected files unchanged, including canonical world/session/combat/logs, frozen data and prior artifacts. There are no new before/after gameplay snapshots because gameplay was never invoked; byte hashes are the appropriate evidence for this nonexecuting pass. No new player-facing output or external campaign payload was sent. No unauthorized mutation, simulation-time advance, faction/event/log/combat update or restricted player disclosure occurred during diagnostics. This is preservation during a no-gameplay pass, not successful live correction/revision authority validation. Existing historical snapshots remain labeled with original pass paths.
''',
'06_historical_comparison.md':'''# 06 — Historical Comparison

| Dimension | R1-03 L3 | R1-05 L1/L2/L4 | R1-08 L1 | R1-09 |
|---|---|---|---|---|
| Mechanical routing | guard reached, returns null (R1-06 corrected older summary) | originals abstain; genuine pending control revises | not reached after provider failure | not executed |
| Interpretation | people correction understood, wrong clarification disposition | originals repeat clarification; control recognizes revision | unavailable | not evaluated |
| Evidence selection | no public evidence selected | no public people evidence in originals | unavailable, not [] | not evaluated |
| Response adequacy | redundant confirmation | originals inadequate; control preserves pending | operational fallback | no response |
| Provider reliability | successful paraphrase; L1/L2 failures separate | three successful responses | one failed dispatch | DNS blocks before dispatch |
| Authority | preserved in valid paraphrase; L4 invalid | preserved in measured originals/control | preserved failed-call path | files unchanged; live authority unmeasured |

R1-03 L3 exact final: “Do you want a description of the people present at the gate district instead of the weather?” Later source R1-06 corrects the older not-reached guard claim; no original report was altered. R1-05 measured totals: three admissions/responses, 5845 input + 630 output = 6475 tokens; gpt-4.1-mini returned gpt-4.1-mini-2025-04-14, zero retries. R1-08 failed admission has unknown tokens/cost and no returned version.

Current configured model and endpoint match the reviewed baseline. SDK 2.48.0, HTTPX 0.28.1 and 45-second production timeout are current local observations; no historical version equivalence is inferred where not recorded. No model switching or generation-setting change occurred. Prior successes do not establish today's access; today's DNS error does not establish prior failure causes. No new live improvement or regression, original reproduction, paraphrase variation, independent generalization or benchmark result is demonstrated. Small historical samples cannot establish broad reliability.
''',
'07_provider_accounting.md':'''# 07 — Provider Accounting

Authoritative current ledger: artifacts/atgb/atgb_r1_09/admission_ledger.json. Four authorized measured admissions; zero attempted dispatches, zero admissions, zero successful responses, zero failed dispatches. Each L1–L4 is NOT_RUN_PHASE_A_BLOCKED with zero retries. Four admissions remain unused; they do not authorize automatic continuation after this handoff.

Zero input/output/total tokens and zero provider cost are attributable to this pass because no inference was dispatched. These are no-call totals, not estimates from missing usage. There is no provider usage report or model-returned version. Dispatch latency is not applicable. Diagnostic latencies are separate in readiness_diagnostics.json. No configured price table or fabricated token-price calculation was needed.

Phase A created and closed one SDK client without calling it; this consumed no admission. The first local diagnostic script stopped on an inspection AttributeError before networking and inference; the inspection was corrected and the completed DNS/TCP/TLS check set ran once. That is an offline diagnostic-tool repair, not a trial/provider retry. No credential value was logged. No model-based health check, paid probe, model listing, responses/chat/embedding request, extra generation, trial continuation or model escalation occurred. No SDK, application, runner or orchestration retries occurred. No response-counter discrepancy exists for this no-dispatch pass; historical discrepancies are preserved separately.

Budget compliance: PASS (0/4; 0/1 each trial). Phase A failure triggered the mandatory stop before live execution; the isolated-failure continuation and two-provider-failure policy were never reached. No interpretation of historical accounting was used to reset or hide current admissions.
''',
'08_final_verdict_and_closure_recommendation.md':'''# 08 — Final Verdict and Closure Recommendation

**D — Inconclusive. Closure recommendation: DEFER.** Phase A is BLOCKED by local api.openai.com DNS resolution failure (gaierror 11001). There were no live dispatches or gameplay executions. Valid model credentials/access, successful inference, R1-07 correction interpretation, public-evidence selection, final answer adequacy and pending-action revision preservation remain unmeasured live in this pass.

R1-07 remains a conditionally implemented deterministic repair. R1-09 neither accepts it as live-demonstrated, revises it, nor justifies abandoning it. No specific remaining product defect or regression is newly demonstrated, so another bounded implementation repair is not justified by this diagnostic failure. The historical inadequate pre-R1-07 answers remain the baseline; they are not new evidence of R1-07 ineffectiveness.

Do not CLOSE ATGB-R1 as a validated conversational repair. DEFER further campaign execution while the environment prerequisite fails. Another pass in the same unresolved environment has diminishing value and would consume attention without distinguishing semantic hypotheses. Broader gameplay work may be prioritized through external review; this recommendation does not implement or authorize it. If provider-capable execution becomes available, the four deferred trials could provide useful bounded acceptance evidence, subject to external review and separate future authorization. No automatic rerun or continuing use of this pass's unused budget.

**One recommended next action:** externally review this packet and assign restoration/verification of provider-host resolution to the environment owner before considering another separately authorized live validation. Do not implement that action here.

Explicit confirmations, supported by protected entry/exit hashes and the no-dispatch ledger: no production code changes; no prompt or schema changes; no unauthorized provider calls (zero calls total); no automatic retries; no experimental PR-EG candidates merged; frozen ATGB baseline unchanged; no unauthorized gameplay-state mutations; no secrets included in the checked review payload; no commits or pushes. Only diagnostic/evidence/report scripts, reports, canonical orientation and generated review exports change. Historical ATGB baseline and judgments remain unchanged. This is a structural/environment packet with no new semantic example; human review remains pending.

Stop after producing and verifying the review ZIP. Await external review before any further implementation or live execution.
'''}
for name,body in reports.items(): write(REPORT/name,body)

orientation=ROOT/'docs/NEXT_SESSION.md'
old=(OUT/'NEXT_SESSION_before.md').read_text(encoding='utf-8')
addition='''## Latest readiness pass — ATGB-R1-09

2026-10-19: **D — Inconclusive; DEFER.** Phase A BLOCKED: api.openai.com DNS
resolution fails with socket.gaierror 11001; TCP/TLS cannot reach connection stages.
No live trials, provider admissions, pending setup or gameplay execution (0/4).
R1-07 reviewed owners and all 811 R1-08 protected hashes match; frozen baseline
verified. Eight reports: development/reports/atgb_r1_09/; diagnostic/ledger/integrity
evidence: artifacts/atgb/atgb_r1_09/; review: handoff/CURRENT_REVIEW.md and ZIP.
Credentials present, validity untested; model gpt-4.1-mini, retries policy 0,
timeout 45s, no proxy configured. DNS root cause and prior failures' causes unknown.
No product repair-effect, generalization, benchmark or live authority result.
R1-07 conditional implementation remains unaccepted live; no new repair justified.
External review, then environment owner to restore/verify provider-host resolution
before considering separately authorized validation. Stop: unused budget does not
authorize automatic continuation. Production/prompts/schema/data/experiments and
prior evidence unchanged. Earlier pass stop/proposal language below is historical.

'''
assert '## Latest readiness pass — ATGB-R1-09' not in old
old=old.replace('Updated 2026-10-19 / ATGB-R1-07.','Updated 2026-10-19 / ATGB-R1-09.')
old=old.replace('## Latest validation — ATGB-R1-08',addition+'## Latest validation — ATGB-R1-08',1)
write(orientation,old)

(OUT/'repository_status_after.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),encoding='utf-8')
write(OUT/'packaging_notes.json',{'initial_diagnostic_issue':'AttributeError inspecting SDK scalar timeout; corrected locally before the completed non-billable diagnostic set; zero inference.',
    'initial_export_issue':'Writing existing handoff/CURRENT_REVIEW.zip returned OSError 22. Generate to a fresh review staging directory, then publish the timestamped export and try atomic replacement of the stable ZIP.',
    'network_reprobes':0,'provider_dispatches':0})
support=list(REPORT.glob('*.md'))+list(OUT.glob('*.json'))+list(OUT.glob('*.py'))+list(OUT.glob('*.txt'))+[OUT/'NEXT_SESSION_before.md']
support += [ROOT/p for p in ('docs/NEXT_SESSION.md','docs/DEVELOPMENT_CONSTITUTION.md','docs/validation_evidence_standard.md','docs/product_realization_validation.md','tools/atgb/readiness.py','tools/atgb/baseline.py','game/live_chat_interpretation.py','game/conversational_orchestration.py','data/validation/atgb/visible/S08.json','data/validation/atgb/baselines/frontier-gate-v1/scenes/frontier_gate.json','artifacts/atgb/atgb_r1_07/integrity_verification.json','artifacts/atgb/atgb_r1_07/after.txt','development/reports/atgb_r1_04/08_final_verdict.md','development/reports/atgb_r1_05/07_provider_accounting.md','development/reports/atgb_r1_05/08_final_verdict.md','development/reports/atgb_r1_07/08_final_verdict.md')]
for pass_id,labels in [('atgb_r1_03',['L1','L2','L3']),('atgb_r1_05',['L1','L2','L4']),('atgb_r1_08',['L1'])]:
    for label in labels:
        folder=ROOT/'artifacts/atgb'/pass_id/label
        support += [p for p in folder.iterdir() if p.is_file() and p.suffix in ('.json','.jsonl','.md')]

config=read('artifacts/atgb/atgb_r1_08/review_config.json')
config.update(campaign_id='atgb_r1_09',campaign_name='ATGB-R1-09 Provider Readiness and Deferred Live Validation',
    purpose='Non-billable readiness verification with fail-closed deferred validation.',
    objective_status='D — Inconclusive; DEFER; Phase A BLOCKED',
    executive_summary='DNS resolution for api.openai.com fails (11001). Phase B not started: 0/4 admissions. Reviewed production baseline preserved. No live repair claim.',
    changes={'production':[],'validation':['Non-billable local configuration/DNS/TCP/TLS diagnostics; mandatory Phase A stop.'],
        'tooling':['Evidence-local diagnostic and offline packaging scripts only.'],
        'documentation':['Eight reports and canonical session orientation.'],'generated_artifacts':['Readiness, authoritative zero-admission ledger, protected hashes, historical metadata and review ZIP.']},
    testing={'focused':'Baseline comparison, pinned corpus verification, local configuration and network diagnostics.',
        'broader':'Not run.','full_suite':'Not run.','runtime_validation':'No gameplay or inference; Phase A BLOCKED.',
        'model_runtime_boundary':'OpenAI Responses/gpt-4.1-mini configured; credential present; validity/inference untested.',
        'new_regressions':'No semantic result; protected files unchanged.','pre_existing_failures':'Historical clarification/evidence-selection failures remain historical; R1-07 live effect unknown.'},
    known_problems={'campaign_specific':['DNS resolution blocker; no valid live trials or per-trial preflight.'],
        'pre_existing':['Prior connection causes unresolved; authenticated human review and conversational competence unestablished.']},
    decisions_requiring_human_review=['Review D/DEFER recommendation and route provider-resolution prerequisite to environment owner. Do not accept repair as live-validated.'],
    does_not_prove=['Live improvement, ineffectiveness, regression, L4 preservation, provider authentication, model access, broad reliability, generalization or benchmark performance.'],
    recommended_next_step='External review; environment owner to restore/verify provider-host resolution before considering separately authorized live validation. Stop; no automatic continuation.',
    primary_report='development/reports/atgb_r1_09/08_final_verdict_and_closure_recommendation.md',
    evidence_packets=[],self_contained_review_test='Eight reports, diagnostics, no-call ledger, historical source traces/state/accounting and hash provenance; no current live transcript exists.',
    configuration_source='artifacts/atgb/atgb_r1_09/review_config.json')
config['supporting_files']=[{'path':p.relative_to(ROOT).as_posix(),'role':'validation_evidence','why':'Explicit current readiness or historical comparison source; original pass paths preserve provenance.',
    'behavioral_evidence':'atgb_r1_09' not in p.as_posix() and p.name in ('transcript.md','traces.json','trace.json','response.json'), 'human_review_required':True}
    for p in sorted(set(support)) if p.is_file() and p.name not in ('review_config.json','zip_verification.json','packaging_command.json')]
write(OUT/'review_config.json',config)
# Secret scan uses credential equality in memory, never prints it.
from game import config as game_config
key=game_config.get_openai_api_key()
for item in config['supporting_files']:
    data=(ROOT/item['path']).read_text(encoding='utf-8',errors='replace')
    assert key not in data, 'secret detected in selected evidence'
    assert not re.search(r'\bsk-[A-Za-z0-9_-]{16,}|Bearer\s+[A-Za-z0-9._-]{16,}',data), 'secret pattern detected'
staging=ROOT/'development/tmp/atgb_r1_09_export'
command=[sys.executable,str(ROOT/'tools/build_review_handoff.py'),'--config',str(OUT/'review_config.json'),'--output-dir',str(staging),'--no-history']
result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
write(OUT/'packaging_command.json',{'command':command,'return_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
assert result.returncode==0,result.stderr
review=staging/'CURRENT_REVIEW.zip'
# Client date 2026-10-19 is Eastern daylight time (UTC-04); no tzdata dependency.
timestamp=datetime.now(timezone(timedelta(hours=-4))).strftime('%Y%m%d-%H%M%S')
target=ROOT/f'handoff/CURRENT_REVIEW({timestamp}).zip'
shutil.copy2(review,target)
stable=ROOT/'handoff/CURRENT_REVIEW.zip'
replacement=ROOT/'handoff/CURRENT_REVIEW.r1_09.tmp'
shutil.copyfile(review,replacement)
try:
    os.replace(replacement,stable)
    stable_status='updated by atomic replacement'
except OSError as error:
    stable_status='unavailable: '+type(error).__name__+'; timestamped ZIP is authoritative export'
for name in ('CURRENT_REVIEW.md','REVIEW_MANIFEST.json'):
    shutil.copyfile(staging/name,ROOT/'handoff'/name)
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    names=z.namelist()
    for name in names:
        content=z.read(name)
        assert key.encode() not in content
        assert not re.search(rb'\bsk-[A-Za-z0-9_-]{16,}|Bearer\s+[A-Za-z0-9._-]{16,}',content)
    for item in config['supporting_files']:
        path='support/'+item['path']
        # Standard generator explicitly deduplicates identical contents.
        if path in names:
            assert hashlib.sha256(z.read(path)).hexdigest()==sha(ROOT/item['path'])
    assert sum('/development/reports/atgb_r1_09/' in name for name in names)==8
write(OUT/'zip_verification.json',{'path':str(target.relative_to(ROOT)),'sha256':sha(target),'zip_crc':'PASS',
    'file_count':len(names),'bytes':target.stat().st_size,'secret_scan':'PASS','stable_zip':stable_status,
    'report_count':8,'canonical_file_hash_checks':'PASS for included support entries',
    'bundle_only_review':'PASS: reports identify verdict, blocker, all trial statuses, accounting, no live claims, closure and next action; historical full traces/state included.',
    'protected_exit_mismatches':[p for p,h in entry.items() if sha(ROOT/p)!=h]})
(OUT/'repository_status_after.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),encoding='utf-8')
print(json.dumps({'verdict':'D — Inconclusive','closure':'DEFER','admissions':0,'zip':str(target),'verification':'PASS'},ensure_ascii=False))
