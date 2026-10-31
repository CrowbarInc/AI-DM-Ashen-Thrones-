from pathlib import Path
import copy, hashlib, json, subprocess, sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/atgb/atgb_r1_03'
REPORTS=ROOT/'development/reports/atgb_r1_03'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,x): p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def report(name,text): (REPORTS/name).write_text(text.strip()+'\n',encoding='utf-8')
trials=[]
for name in ['L1','L2','L3','L4']:
    p=OUT/name
    b,a=read(p/'before.json'),read(p/'after.json')
    response=read(p/'response.json'); accounting=read(p/'accounting.json'); trace=read(p/'trace.json')
    sdk=accounting['snapshot']
    changed=[k for k in b if b[k]!=a[k]]
    ctxkeys=['pending_intention','pending_clarification','last_executed_intention']
    pending={k:{'before':b['session'].get('conversational_context',{}).get(k),
                'after':a['session'].get('conversational_context',{}).get(k)} for k in ctxkeys}
    result={'trial':name,'player_input':read(p/'setup.json')['player_input'],
        'final_response':response.get('gm_output',{}).get('player_facing_text'),
        'application_admissions':sdk['requests'],'dispatched':sdk['dispatched_requests'],
        'completed_provider_responses':sum(r['completion_status']=='completed' for r in sdk['records']),
        'failed_dispatches':sum(r['completion_status']=='failed' for r in sdk['records']),
        'input_tokens':sdk['input_tokens'],'output_tokens':sdk['output_tokens'],'total_tokens':sdk['total_tokens'],
        'end_to_end_ms':accounting['end_to_end_ms'],'estimated_cost':None,
        'routing':'INDETERMINATE','interpretation':'INDETERMINATE','evidence_selection':'INDETERMINATE',
        'response_adequacy':'FAIL','authority':'PASS' if name!='L4' else 'FAIL (invalid live-control setup)',
        'authority_scope':'Exact attempted isolated execution only; not broad assurance.',
        'changed_domains':changed,'session_changed_keys':[k for k in sorted(set(a['session'])|set(b['session'])) if a['session'].get(k)!=b['session'].get(k)],
        'world_changed_keys':[k for k in sorted(set(a['world'])|set(b['world'])) if a['world'].get(k)!=b['world'].get(k)],
        'pending_intentions':pending,'turn_counter_before':b['session'].get('turn_counter'),
        'turn_counter_after':a['session'].get('turn_counter'),
        'clocks_before':b['session'].get('clocks'),'clocks_after':a['session'].get('clocks'),
        'trace_functions':[e['function'] for e in trace]}
    if name=='L3':
        result.update(interpretation='PASS (correct subject; unnecessary clarification posture)',evidence_selection='FAIL',
            note='GM/CLARIFICATION, evidence_refs=[], no unresolved references. Bridge NEEDS_CLARIFICATION stops before revision gate. No mechanical misrouting observed, but repaired seam not exercised.')
    elif name=='L4':
        result.update(note='INVALID LIVE CONTROL: fixture import activated experiments/pr_dq/__init__.py environment defaults. Live interpretation skipped; generic resolution consumed a turn, cleared pending intention and updated factions. Narration refused before admission by existing input-token ceiling.',
            interpretation='INDETERMINATE (no model interpretation)',evidence_selection='INDETERMINATE (no live selection)',routing='FAIL in disabled-interpretation fallback; live control INDETERMINATE')
    else:
        result['note']='Provider failure before model interpretation: '+('APIConnectionError' if name=='L1' else 'InternalServerError')+'. Host fallback inadequate for the request; not evidence of a conversational model defect.'
    trials.append(result)
write(OUT/'normalized_results.json',trials)
known=[t for t in trials if t['completed_provider_responses']]
aggregate={'attempted_designated_trials':4,'valid_completed_live_trials':1,
    'failed_provider_trials':['L1','L2'],'invalid_live_control':'L4',
    'application_admissions':sum(t['application_admissions'] for t in trials),
    'application_dispatches':sum(t['dispatched'] for t in trials),
    'successful_provider_responses':sum(t['completed_provider_responses'] for t in trials),
    'failed_provider_dispatches':sum(t['failed_dispatches'] for t in trials),
    'known_input_tokens':sum(t['input_tokens'] for t in known),
    'known_output_tokens':sum(t['output_tokens'] for t in known),
    'known_total_tokens':sum(t['total_tokens'] for t in known),
    'all_trial_token_totals':None,'all_trial_cost':None,
    'missing_usage_trials':['L1','L2'],'sdk_transport_retries':0,'intentional_trial_retries':0,
    'continuations':0,'hard_admission_limit':8,'budget_compliant':True,
    'note':'Known token subtotal is L3 only; not total billing. L4 zero admissions, one pre-admission narration refusal. Counters in response metadata are not billable-call counts.'}
write(OUT/'provider_accounting.json',aggregate)
entry=read(OUT/'entry_hashes.json')
prior=read(ROOT/'artifacts/atgb/atgb_r1_02/baseline_hashes.json')
def changes(inv): return [p for p,h in inv.items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
integrity={'entry_files_checked':len(entry),'entry_changed_or_missing':changes(entry),
    'predecessor_protected_files_checked':len(prior),'predecessor_changed_or_missing':changes(prior)}
assert not integrity['entry_changed_or_missing'] and not integrity['predecessor_changed_or_missing'],integrity
write(OUT/'integrity.json',integrity)
transcript=['# ATGB-R1-03 live/attempted transcripts','AI-assisted evaluation; authenticated human review UNREVIEWED.']
for t in trials:
    setup=read(OUT/t['trial']/'setup.json')
    transcript.extend(['',f"## {t['trial']}",setup.get('source',''),'',
        'Prior player: '+setup.get('prior_player','Existing pending ASK fixture.'),
        'Prior AI-DM: '+setup.get('prior_gm','No invented prior utterance; structured pending fixture.'),
        '', 'Player: '+t['player_input'],'','AI-DM: '+t['final_response'],'',t['note']])
(OUT/'transcripts.md').write_text('\n'.join(transcript)+'\n',encoding='utf-8')
table='| Trial | Routing | Subject interpretation | Evidence | Response | Authority | Admissions | ms |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n'
for t in trials:
    table+='| '+' | '.join(str(t[k]) for k in ['trial','routing','interpretation','evidence_selection','response_adequacy','authority','application_admissions','end_to_end_ms'])+' |\n'
details=[]
for t in trials:
    details += [f"## {t['trial']}",f"Player: {t['player_input']}",f"AI-DM: {t['final_response']}",t['note'],
        f"Measured tokens input/output/total: {t['input_tokens']}/{t['output_tokens']}/{t['total_tokens']}; end-to-end {t['end_to_end_ms']} ms. Cost unavailable. See setup.json, trace.json, response.json, before.json, after.json and accounting.json under artifacts/atgb/atgb_r1_03/{t['trial']}/."]
report('02_live_trial_results.md', '# 02 — Live Trial Results\n\n'+table+'\n\n'+'\n\n'.join(details)+'''

All six dimensions are graded independently; no automated gameplay scorer was run. These are provisional AI-assisted judgments, not authenticated human review. L1/L2 response FAIL describes the delivered failure fallback, not model semantic quality. L3 correctly identifies people, so subject interpretation passes; choosing clarification and no evidence still fails adequacy. Routing is indeterminate because the interpretation bridge stops before the repaired gate. L4 has an observed unauthorized mutation relative to the fixture's revise-without-execution contract, but is excluded from live regression conclusions because its environment was invalid. No original trial successfully reached the repaired seam. Four designated attempts, only one valid completed live trial; no reruns.
''')
report('03_execution_traces.md','''# 03 — Execution Traces

Each L1–L4 directory preserves exact setup, full pre/post state (session, world, scene, character, combat, log), production response, function trace, admission ledger and accounting snapshot. trace.json records full interpretation messages, raw model text when returned, parsed/adapted interpretation, public candidate evidence, bridge eligibility, reconciliation and selected record evidence where available. normalized_results.json is a compact cross-trial index. transcripts.md contains exact inputs, preceding response and final delivered outputs.

L1/L2: public candidate evidence and exact production messages were available; request failed before a model response. No raw/parsed interpretation, selected evidence, authorized conversation plan, or repaired-gate outcome exists. L3: raw and parsed interpretation and available/selected evidence captured; eligibility NEEDS_CLARIFICATION yields the model clarification sentence. L4: interpretation explicitly skipped, no raw model response; response metadata captures generic-resolution and budget-refusal fallback. Its existing test setup was imported without interpretation stubs, but that import activated test environment defaults; this is a harness defect.

Observed functions are selected existing returns through a Python profile callback, not new production instrumentation. API-level resolution metadata and pre/post snapshots supplement missing function events. No dedicated scored referent candidates, confidence probabilities, per-candidate semantic rejection reasons or rejected alternate model plans exist in this pathway. Entity catalog and reference_reconciliation are preserved where available, not relabeled as a confidence score. Final player-facing text/plan provenance and provider metadata are retained in response.json. A missing event is not automatically a successful decision.

The route callable game.api.chat(ChatRequest) ran directly, including interpretation, authorization/routing and emission. HTTP transport and rendered UI were not exercised. SDK transport max_retries=0 was enforced only in the isolated process and recorded. Production source, prompts and model configuration were untouched. There is no trace of PR-EG bind/witness invocation in L3.
''')
report('04_s08_2_historical_comparison.md','''# 04 — S08.2 Historical Comparison

Historical baseline is immutable ATGB-03C S08 trial 1: ATGB-01 scenario / ATGB-02 corpus, related_variation, frontier-gate-v1. Exact original S08.1 and response are in transcripts.md and original transcript included in the ZIP. No separate opening was omitted. World facts include visible serjeant, runner, watchers and refugees. Initially no interlocutor, pending intention, discovered clue or world flag. S08.2 should correct the descriptive focus toward those people.

| Dimension | Historical S08.2 | L1 | L2 |
| --- | --- | --- | --- |
| Response | I don't have an unexecuted intention to revise. What do you want to change? | Interpretation failure fallback | Interpretation failure fallback |
| Mechanical route | no_pending_intention; demonstrated wrong entry | Not reached | Not reached |
| Interpretation | Raw provider interpretation unavailable; provisional fail from output | Unavailable | Unavailable |
| Evidence selection | Original raw selected refs not retained | Candidate public facts available, no model selection | Same |
| Adequacy | FAIL | FAIL fallback | FAIL fallback |
| Authority | Historical provisional PASS | PASS for attempted execution | PASS for attempted execution |
| Admissions | 1 interpretation, 0 narration | 1 failed dispatch | 1 failed dispatch |
| Tokens in/out | 2004 / 210 | Unavailable | Unavailable |
| Latency | Historical host 1850 ms | See measured accounting; different timing boundary | See measured accounting; different timing boundary |

Configured model remains gpt-4.1-mini; historical actual gpt-4.1-mini-2025-04-14. L1/L2 have no returned model identifier. L3 returns that same dated model but is only the paraphrase, not an original-wording reproduction. SDK retry policy now explicitly zero; historical SDK retry bounds were not established. Replay uses exact preceding text/log plus fresh reset and current memory construction, rather than an unavailable original intermediate session snapshot. These limitations preclude strict before/after equivalence. Historical timing and current wall-clock timing are not a controlled latency comparison; no repair cost delta is established.

1. Original mechanical failure eliminated live: NOT DEMONSTRATED (gate not reached).
2. Original conversational interpretation improved: INDETERMINATE.
3. Original evidence selection improved: INDETERMINATE.
4. Original response adequacy improved: NOT DEMONSTRATED.
5. Authority: preserved in L1/L2 attempted execution; invalid L4 fallback violated its revision contract in isolated state.
6. Performance costs: current measurements retained; no reliable repair-attributable delta.

Outcome C — Repair not reliably demonstrated, because execution evidence is insufficient. This is not a finding that the repaired regex failed. L3 recognizes the people subject but asks redundant confirmation and supplies none of the available people facts. It cannot replace either missing original trial or establish independent generalization.
''')
report('05_failure_localization.md','''# 05 — Failure Localization

L1: earliest observed blocker is provider dispatch in game/live_chat_interpretation.py:214 / :241; request_interpretation returns provider_failure / APIConnectionError. No model output exists. Observed cause: request failed, high confidence. Likely cause: restricted execution network, medium confidence; no transport diagnostics establish more. Context contains the full prior response and relevant people evidence. No claim about semantic binding is possible.

L2: same boundary returns provider_failure / InternalServerError despite explicit network/payload approval. Observed cause: upstream request failed, high confidence. Provider service failure is likely; exact server root cause unavailable. Do not equate missing token usage with zero cost or a parser rejection.

L3: earliest demonstrably incorrect semantic choice is the returned model interpretation, game/live_chat_interpretation.py:214. It states the correct subject but chooses communication_mode CLARIFICATION and asks whether the player wants exactly what the player already requested. evidence_refs is empty although public visible:1/:2/:3 explicitly describe the people and reply:0 contains the full prior answer. No unresolved referents are reported. Observed cause: unnecessary clarification posture plus empty evidence selection, high confidence. Bridge adaptation yields NEEDS_CLARIFICATION, and interpret_production_turn returns clarification_required; it does not call the repaired _pending_revision_decision at game/conversational_orchestration.py:391. Host fallback realizes the supplied redundant question. This is a semantic failure, not evidence of PR-EG bind/witness rejection. Why the model selected that posture is a hypothesis; schema descriptions defining CORRECTION as pending-intent revision may influence it but no prompt intervention tested that explanation. No repair implemented.

L4: earliest incorrect validation setup decision is importing reusable pytest fixture modules in execute_trial.py before checking effective live flags. The import chain reaches experiments/pr_dq/__init__.py:11 and forces ASHEN_DISABLE_LIVE_INTERPRETATION=1. The production trace directly confirms live_interpretation_disabled. Observed cause: invalid harness environment, high confidence; fixture content itself is from the frozen control. Subsequent generic resolution is not an execution of the repaired live revision seam. Narration admission is refused on the existing input-token ceiling. Before/after state proves turn 0→1, time_pressure 0→1, pending_intention cleared, last_executed_intention created, factions/event_log changed. These violate the control's no-execution contract but cannot establish a new regression caused by R1-02. No live-control authority PASS is assigned. This is separate from L3's semantic defect and L1/L2's provider failures.

Offline HTTP regression attempt stopped after hanging at the Windows TestClient/socket boundary; it never produced a completed suite result. It was interrupted. A non-HTTP slice then completed: 102 passed, three API tests deselected, exit 0. The frozen authorization tests remain available and were green in the predecessor; no fresh full-module result is claimed. No full suite, broad benchmark, model comparison, prompt optimization or exploratory live scenario was run.

Unresolved: exact-wording production correction with successful provider response; whether it reaches repaired gate; adequate selection of people facts; valid live pending-action control; server failure cause and failed-request billing. These require separately reviewed follow-up, not an inferred PASS.
''')
state_lines=['# 06 — Authority and State Integrity','',
    'Snapshots are taken after isolated setup, immediately before the player request, and after it. Canonical player data and all entry-hashed production/fixtures/experiments are unchanged. Fresh identities and delivered conversational memory are permitted setup metadata; they do not authorize world facts.']
for t in trials:
    state_lines += ['',f"## {t['trial']} — {t['authority']}",
        f"Changed domains: {t['changed_domains']}; session keys: {t['session_changed_keys']}; world keys: {t['world_changed_keys']}.",
        f"Turn {t['turn_counter_before']}→{t['turn_counter_after']}; clocks before {t['clocks_before']}; after {t['clocks_after']}.",
        'Pending-intention fields are fully listed in normalized_results.json and raw snapshots.']
state_lines += ['', 'L1/L2: session and gameplay domains unchanged; only failure-log entry appended. L3: gameplay domains unchanged; only delivered-memory and save timestamp change. No pending intention created or revised. Its question contains public people/location concepts and no restricted facts. L1/L2 generic fallback contains no restricted facts. Exact observed-output disclosure check passes within these narrow executions; no claim of exhaustive security testing.',
    'L4: unexpected isolated mutation observed; pending_intention becomes null and last_executed_intention is marked executed. Pending clarification remains. World factions and event_log change; character/combat/scene template do not. This violates the intended control authority contract. It followed a disabled-interpretation fallback caused by test environment leakage, so the live control is INVALID and live authority preservation is not established. The statement “no unauthorized state mutations” cannot be confirmed for this pass. Canonical player state was not affected.',
    f"Integrity: {integrity['entry_files_checked']} entry hashes and all {len(prior)} predecessor-protected files match. Production code unchanged; frozen baseline unchanged; no experimental candidates merged; no commit or push."]
report('06_authority_and_state_integrity.md','\n\n'.join(state_lines))
report('07_provider_accounting.md', '# 07 — Provider Accounting\n\n'+json.dumps(aggregate,indent=2)+'''

All three admissions use OpenAI configured gpt-4.1-mini, owner live_chat_interpretation.request_interpretation. Only L3 returns actual model gpt-4.1-mini-2025-04-14. L1/L2 model values in ledger are configured fallbacks, not observed provider IDs. Provider request IDs are preserved when returned; absent on failed requests. One SDK client per L1/L2/L3 records max_retries=0. No continuation, retry or escalation call occurred. L4 creates no SDK client and admits no request; an attempted narration is refused before admission for input-token ceiling. Its host narration counter must not be mistaken for a billable request.

The global static accounting manifest remains stale only for the reviewed routing repair. Seven dispatch sites and budget hash match; details in accounting_readiness.json. No global PASS or manifest update is claimed. Existing durable admission accounting bounds every dispatched application request. Three admissions are below eight; four designated attempts and one valid completed live trial are below the maximum four completed live trials. L1/L2 failures are retained, never retried. L2–L4 received explicit user approval of campaign payload and OpenAI destination after automatic review initially rejected L2. The rejection itself caused zero dispatches. No workaround bypass was used.

Measured per-trial end-to-end and provider dispatch latencies are in normalized_results.json and accounting.json. L3 known input/output/total is 2008/212/2220. Total billed tokens/cost are unavailable because failed calls returned no usage; zero is not inferred. No configured price table, no fabricated estimates, no pricing lookup/provider experiment. Three failed/successful dispatches exhaust this pass's chosen work; no additional live scenarios or calls follow.
''')
report('08_final_verdict.md','''# 08 — Final Verdict

**D — Inconclusive.** The original-wording trials both failed before producing a model interpretation, and the pending-action live control was invalidated by test-environment leakage. The repaired production revision gate therefore was not validated live. Deterministic checks alone do not upgrade that conclusion.

The one valid completed live paraphrase trial identified the intended people subject but asked redundant confirmation, selected no relevant evidence and failed response adequacy. It preserved gameplay state and disclosed no restricted information. This is an observed semantic failure in live interpretation/evidence selection before the repaired revision gate, not proof that PR-EG bind/witness is causal. The invalid L4 fallback advanced isolated state and violated its no-execution contract; no unconditional authority-preservation confirmation is possible.

Claims: production code unchanged; frozen ATGB baseline and historical transcript unchanged; no experimental candidates merged; provider budget respected (3/8 admissions, 1 valid completed live trial, 4 designated attempts, zero retries/continuations); no secrets included in selected artifacts after content verification. Unexpected mutation exists only in the isolated invalid L4 execution. Canonical player data unchanged. No commits/pushes. Authenticated human review remains pending.

Recommended single bounded ATGB-R1-04 scope: validation-readiness recovery followed, only after external review and renewed bounded live authorization, by the missing original-wording replication and a valid pending-action control. Eliminate test-import environment leakage in the validation harness and assert effective provider/live flags before admission; preserve production code, prompts, model and baseline. Diagnose provider availability without exploratory paid calls. Any proposed semantic repair for L3 is outside that scope and must be separately authorized from the preserved trace. No ATGB-R1-04 implementation or live work performed here.

Stop after producing the review ZIP. Await external review.
''')
index='# ATGB-R1-03 — Controlled Live Conversational Validation\n\n**D — Inconclusive.** Three provider admissions: two failed, one paraphrase response inadequate. Pending-action control invalid due to test-environment leakage; isolated state mutation observed. No production edits.\n\n'
index+='\n'.join(f'- [{p.stem.replace("_"," ")}]({"atgb_r1_03/"+p.name})' for p in sorted(REPORTS.glob('*.md')))
index+='\n\nRaw and normalized evidence: artifacts/atgb/atgb_r1_03/. Behavioral Evidence: artifacts/validation_evidence/atgb_r1_03/. Four designated attempts, one valid completed live trial; human review UNREVIEWED. No benchmark performance or broad improvement claim.\n'
(ROOT/'development/reports/atgb_r1_03_controlled_live_validation.md').write_text(index,encoding='utf-8')
# Standard evidence packet, preserving failures and invalid control rather than inventing success.
from tools.validation_evidence import build_packet, write_packet
examples=[]
for t in trials:
    setup=read(OUT/t['trial']/'setup.json')
    examples.append({'example_id':t['trial'],'scenario_run_id':t['trial'],'turn_index':2 if t['trial']!='L4' else 1,
        'player_input':t['player_input'],'player_input_classification':['representative_player_behavior','boundary_case'] if t['trial']!='L4' else ['synthetic_positive_control','boundary_case'],
        'simulated_player_rationale':'Exact authorized controlled correction or existing frozen pending-ASK control; no simulated model response.',
        'prior_player_context':setup.get('prior_player','Frozen pending ambiguous ASK fixture.'),
        'prior_gm_context':setup.get('prior_gm','No historical spoken exchange supplied by fixture.'),
        'exact_gm_output':t['final_response'],'historical_result':'Original S08.2 mechanical misrouting; provisional AI-assisted FAIL, not authenticated human review.',
        'semantic_result':'FAIL','mandatory_gates':{k:{'status':t[k]} for k in ['routing','interpretation','evidence_selection','response_adequacy','authority']},
        'diagnostic_result':t,'automated_evaluation':{'method':'AI-assisted independent six-dimension assessment over retained traces; no gameplay scorer.'},
        'runtime_validity':'VALID live completed paraphrase' if t['trial']=='L3' else 'INCOMPLETE provider failure' if t['trial'] in ['L1','L2'] else 'INVALID live control; test environment leakage',
        'final_emission_metadata':{'source':f'artifacts/atgb/atgb_r1_03/{t["trial"]}/response.json'},
        'continuation_action':'Stop; no retry or next pass.', 'source_artifact_path':f'artifacts/atgb/atgb_r1_03/{t["trial"]}/response.json',
        'human_review':{'status':'UNREVIEWED','rationale':'External review pending; AI-assisted assessment only.'},
        'evaluator_disagreement_history':[],'calibration_reference':None})
packet=build_packet(campaign={'campaign_id':'atgb_r1_03','what_was_tested':'Original S08.2, independent repeat, specified paraphrase and pending-action control attempt.',
    'runtime_path':'game.api.chat(ChatRequest); production live interpretation and emission; direct callable, not HTTP.',
    'gm_boundary':'Actual provider calls for L1-L3; L4 invalid disabled interpretation.',
    'player_input_mode':'Fixed authorized existing inputs; no exploratory scenarios.',
    'run_count':4,'turn_count':4,'automated_conclusion':'D inconclusive: two provider failures, one inadequate live paraphrase, one invalid mutated control.'},
    claim_types=['runtime_evidence','semantic_behavioral_evidence'],examples=examples,
    missing_concepts=[],limitations=['No successful original-wording live reproduction.','No valid live mechanical control.','One related paraphrase is not independent generalization.','L4 mutation prevents unconditional authority claim.','Human review pending.'],evidence_scope='controlled_live_attempts')
write_packet(ROOT/'artifacts/validation_evidence/atgb_r1_03',packet)
# Concise canonical handoff update; detailed findings remain in reports.
nextpath=ROOT/'docs/NEXT_SESSION.md'
old=nextpath.read_text(encoding='utf-8')
start=old.index('ATGB-R1-02 implemented the bounded mechanical revision-entry repair')
end=old.index('ATGB-05A remains the assessment-import closeout.',start)
replacement='''ATGB-R1-03 controlled live validation completed on 2026-10-19 with **D — Inconclusive**.
Report: `development/reports/atgb_r1_03_controlled_live_validation.md`; eight reports
under `development/reports/atgb_r1_03/`; raw/normalized traces and accounting under
`artifacts/atgb/atgb_r1_03/`. Production R1-02 repair matches its reviewed ZIP;
3,564 protected hashes unchanged. Current non-HTTP boundary tests: 102 passed,
three API tests deselected; initial HTTP slice interrupted at environment boundary.

L1 APIConnectionError and L2 InternalServerError prevented original-wording model
results. L3 paraphrase recognized people but selected no evidence and asked
redundant confirmation; repaired gate was not reached. L4 live control INVALID:
fixture imports activated test defaults disabling interpretation; generic fallback
advanced isolated time/turn/factions and cleared pending intention. No live
authority-preservation or repair-regression conclusion from L4. Canonical player
state unchanged. Three admissions, one valid completed live trial, no retries or
continuations, failed-call usage unavailable. Production/prompts/models unchanged.

ATGB-R1-02 remains a deterministic routing repair, not demonstrated live adequacy.
No experimental integration. External review required before ATGB-R1-04. Proposed
R1-04 is bounded validation-readiness recovery and missing original/control trials
only after renewed live authorization; no semantic repair authorized here.

'''
old=old[:start]+replacement+old[end:]
old=old.replace('Updated 2026-10-18 / ATGB-R1-02.','Updated 2026-10-19 / ATGB-R1-03.')
old=old.replace('Stop for external review: ATGB-R1-02 changed only mechanical revision routing.\nNo live provider call, frozen-baseline edit, added model authority, commit or push.\nDo not begin ATGB-R1-03 until external review.', 'Stop for external review of ATGB-R1-03. This pass changed evidence/documentation\nonly. No frozen-baseline edit, added model authority, commit or push. Do not begin\nATGB-R1-04 without external review and renewed bounded live authorization.')
nextpath.write_text(old,encoding='utf-8')
(OUT/'repository_status_after.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),encoding='utf-8')
write(OUT/'validation_commands.json',{
    'initial':'pytest tests/test_atgb_r1_02_revision_boundary.py tests/test_pr_ef_r4_authorization.py -q --tb=short; interrupted after 72 dots at HTTP boundary, exit 1',
    'completed':'pytest tests/test_atgb_r1_02_revision_boundary.py -k not api_nonmutating -q --tb=short',
    'result':'102 passed, 3 deselected, exit 0; one Starlette deprecation warning',
    'live':'execute_trial.py L1 sandbox; L2-L4 network escalation after explicit payload/destination approval',
    'trial_retry_count':0,'full_suite':'not run'})
base=read(ROOT/'data/validation/review_handoffs/atgb_r1_02_mechanical_revision_boundary.json')
base.update(campaign_id='atgb_r1_03_controlled_live_validation',campaign_name='ATGB-R1-03 Controlled Live Conversational Validation',campaign_date='2026-10-19',
    purpose='Bounded validation only; no implementation authority.',objective_status='D — INCONCLUSIVE; EXTERNAL REVIEW REQUIRED',
    executive_summary='Original-wording L1/L2 failed upstream before interpretation. L3 correctly identified people but selected no evidence and asked redundant confirmation. L4 control invalid due to test-import environment leakage; generic fallback mutated isolated state. Repaired gate not demonstrated live. Three admissions of eight maximum; one valid completed live trial. Production and all protected baseline/experimental files unchanged. No secrets packaged; no commit/push. Stop for external review.',
    changes={'production':['None. Reviewed R1-02 source unchanged.'],'validation':['Controlled designated attempts and AI-assisted six-dimension judgments; no scorer/expectation edits.'],'tooling':['Campaign-local observer, bounded SDK transport constructor and reporting/export scripts only.'],'documentation':['Eight reports, index and canonical session handoff.'],'generated_artifacts':['Raw and normalized traces, transcripts, accounting, state snapshots, hashes and standard review export.']},
    testing={'focused':'102 non-HTTP boundary tests passed, 3 API tests deselected, exit 0.','broader':'Initial 133-test HTTP slice interrupted at Windows TestClient boundary; no completed result.','full_suite':'Not run.','runtime_validation':'Four designated attempts: two upstream failures, one inadequate live paraphrase, one invalid live control.','model_runtime_boundary':'OpenAI gpt-4.1-mini; only L3 returned actual gpt-4.1-mini-2025-04-14; SDK retries zero.','new_regressions':'No production change; L4 invalid harness cannot establish a new production regression.','pre_existing_failures':'Global accounting source manifest stale solely for the reviewed routing repair; dispatch fingerprints unchanged.'},
    known_problems={'campaign_specific':['Missing successful original-wording trials.','L3 redundant clarification and ignored available people evidence.','L4 fixture import disabled interpretation and isolated fallback mutated state.','Failed-call token usage/billing unavailable.'],'pre_existing':['Human ATGB review remains unattested.','Extensive dirty worktree preserved.','PR-EG integration ban remains.']},
    decisions_requiring_human_review=['Review D inconclusive verdict and invalid-control authority evidence.','Decide whether to authorize bounded ATGB-R1-04 validation-readiness recovery; no implementation follows automatically.'],
    missing_concepts=['No new semantic subsystem or authority proposed.'],
    does_not_prove=['Original repair reproduced live, valid mechanical control, broad conversation quality, independent generalization, full-suite green, unconditional authority preservation or exact total cost.'],
    recommended_next_step='External review, then separately authorized bounded validation-readiness recovery and missing original/control trials in ATGB-R1-04. Do not implement semantic repairs.',
    primary_report='development/reports/atgb_r1_03_controlled_live_validation.md',evidence_packets=['artifacts/validation_evidence/atgb_r1_03'],
    self_contained_review_test='ZIP contains all eight reports, exact exchanges, raw/normalized traces, full pre/post state, accounting and status; source hashes and CRC verified.',
    configuration_source='data/validation/review_handoffs/atgb_r1_03_controlled_live_validation.json')
files=list(REPORTS.glob('*.md'))+list(OUT.glob('*.json'))+list(OUT.glob('*.txt'))+[OUT/'transcripts.md',OUT/'execute_trial.py',OUT/'prepare_review.py',
    ROOT/'game/conversational_orchestration.py',ROOT/'game/live_chat_interpretation.py',ROOT/'tests/conftest.py',
    ROOT/'tests/test_atgb_r1_02_revision_boundary.py',ROOT/'tests/test_pr_ef_r4_authorization.py',ROOT/'tests/fixtures/pr_ef_r4_holdouts.json',
    ROOT/'artifacts/atgb/atgb_03c/S08/transcript.md',ROOT/'data/validation/atgb/visible/S08.json',ROOT/'docs/NEXT_SESSION.md']
for t in trials: files+=list((OUT/t['trial']).glob('*.json'))+list((OUT/t['trial']).glob('*.jsonl'))
# Explicit selection: no store trees, local env, credentials, caches or historical ZIPs.
base['supporting_files']=[{'path':p.relative_to(ROOT).as_posix(),'role':'validation_evidence','why':'Required controlled trial, authority, accounting or baseline evidence.','behavioral_evidence':True,'human_review_required':True} for p in files]
write(ROOT/'data/validation/review_handoffs/atgb_r1_03_controlled_live_validation.json',base)
print(json.dumps({'reports':len(list(REPORTS.glob('*.md'))),'integrity':integrity,'accounting':aggregate},indent=2))
