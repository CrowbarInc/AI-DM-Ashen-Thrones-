"""PR-PLAY-03 explicit review selection, evidence packet and integrity checks."""
from pathlib import Path
import json,sys,hashlib,subprocess,os,shutil
from datetime import datetime,timezone,timedelta
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));O=R/'artifacts/pr_play_03'
from tools.validation_evidence import build_packet,write_packet
from tools.build_review_handoff import build_handoff
def write(name,obj):(O/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
rs=json.loads((O/'reproduction_outputs.json').read_text());hist=json.loads((O/'historical_excerpt.json').read_text())
examples=[]
def example(id,source,player,text,classes,result,validity,meta,prior='Fresh initialized campaign; no previous transcript row.'):
 return {'example_id':id,'scenario_run_id':id,'turn_index':1,'player_input':player,'player_input_classification':classes,
 'player_input_context':'Start Campaign button; empty player_input is intentional, not missing dialogue.',
 'simulated_player_rationale':None,'prior_context':prior,'exact_gm_output':text,'historical_result':result,
 'mandatory_gates':{'availability':'No historical semantic scorer retained; no gameplay PASS asserted.'},
 'diagnostic_result':{'finding':'opening success and text meaning examined separately'},'automated_evaluation':meta,
 'runtime_validity':validity,'final_emission_metadata':meta,'continuation_decision':'Stop for external review',
 'source_artifact_path':source,'human_review':{'status':'UNREVIEWED','rationale':'AI-assisted investigation; no authenticated human scorer. User reports original opening inadequate.'},
 'evaluator_disagreement':{'present':id=='historical_start','history':'Original trace successful=true but user-reported and source-inspected output does not establish an opening.' if id=='historical_start' else 'No independent semantic evaluation.'},
 'semantic_result':'FAIL' if id=='historical_start' else 'UNAVAILABLE'}
examples.append(example('historical_start','artifacts/pr_play_02/manual-20261026-201939.zip::data/session_log.jsonl','',hist['player_facing_text'],['human_captured','representative_player_behavior','runtime_discovered'],'Host successful=true; original output retained',{'saved_response':True,'rendered_ui':'unknown'},hist['metadata']))
for r in rs:
 g=r.get('response',{}).get('gm_output')
 if not g:continue
 examples.append(example(r['case'],f'artifacts/pr_play_03/{r["case"]}_output.json','',g['player_facing_text'],[r['classification']],
 'Exact synthetic provider narration delivered' if r['case']=='valid_structured' else 'Existing failure behavior reproduced',
 {'endpoint_function':True,'http_transport':False,'sdk':'synthetic','live_calls':0},g.get('metadata',{})))
packet=build_packet(campaign={'campaign_id':'pr_play_03','what_was_tested':'Historical failed opening and six offline host controls; no repair.',
 'runtime_path':'Production start_campaign endpoint function through SDK stub and real disposable stores; original saved session inspected.',
 'gm_boundary':'One historical live call; zero new live calls. Synthetic response/control outputs explicitly labeled.',
 'player_input_mode':'Captured Start button, empty input; synthetic SDK controls.',
 'run_count':7,'turn_count':6,'initial_start_attempts':7,'repeat_start_attempts_offline':6,
 'counting_note':'One historical run plus six isolated offline cases. Six total delivered transcript rows; pipeline-exception case commits none. Each offline case also attempts one repeat.',
 'automated_conclusion':'27 host assertions and 38 existing tests pass; semantic opening failure remains; no repair-effect claim.'},
 claim_types=['structural_evidence','runtime_evidence','semantic_behavioral_evidence'],examples=examples,
 missing_concepts=[],limitations=['Original raw provider output/request and provider finish details missing.','No rendered UI, independent generalization, gameplay benchmark or repair validation.','Original successful=true is runtime telemetry, not a semantic evaluator PASS.'])
write_packet(R/'artifacts/validation_evidence/pr_play_03',packet)
baseline=json.loads((O/'baseline.json').read_text());changed=[]
for name,old in baseline['hashes'].items():
 p=R/name
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=old:changed.append(name)
assert not changed,changed
nowfiles=set()
for root in ['game','static','data','experiments','tests']:
 nowfiles|={p.relative_to(R).as_posix() for p in (R/root).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
oldfiles={p for p in baseline['hashes'] if p not in ['run.py','requirements.txt']}
assert nowfiles==oldfiles, sorted(nowfiles^oldfiles)
write('integrity.json',{'protected_file_count':len(baseline['hashes']),'all_hashes_unchanged':True,'protected_inventory_unchanged':True,
 'production_prompt_schema_tests_data_frozen_atgb_experiments_unchanged':True,'historical_zip_sha256':json.loads((O/'historical_inventory.json').read_text())['zip_sha256'],
 'live_calls':0,'connectivity_diagnostics':0,'commits':0,'pushes':0,'disposable_saves_only':'development/tmp/pr_play_03',
 'head_unchanged':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==baseline['head']})
status=subprocess.check_output(['git','status','--short'],cwd=R,text=True)
(O/'final_status.txt').write_text(status,encoding='utf-8')
entry=(O/'entry_status.txt').read_text();entrylines=set(entry.splitlines());finallines=set(status.splitlines())
write('status_delta.json',{'added_status_lines':sorted(finallines-entrylines),'removed_status_lines':sorted(entrylines-finallines),
 'note':'Already-dirty docs/NEXT_SESSION and generated handoff files may retain identical status labels; content changes limited to report/evidence/orientation/review exports.'})
write('commands.json',{'reproduction':'.venv/Scripts/python.exe artifacts/pr_play_03/reproduce.py',
 'analysis':'.venv/Scripts/python.exe artifacts/pr_play_03/analyze.py',
 'existing_tests':'ASHEN_DISABLE_PROVIDER_CALLS=1; ASHEN_DATA_DIR=development/tmp/pr_play_03/pytest_data; .venv/Scripts/python.exe -m pytest tests/test_pr_br_structured_realization_envelope.py tests/test_pr_bw_narration_only_envelope.py tests/test_pr_by_narration_only_retry_contract.py -q --tb=short --basetemp development/tmp/pr_play_03/pytest --junitxml artifacts/pr_play_03/existing_tests.xml',
 'packaging':'.venv/Scripts/python.exe artifacts/pr_play_03/package.py'})
write('state_transition_findings.json',[{'case':r['case'],'before':{k:v for k,v in r['before'].items() if k!='world'},'after':{k:v for k,v in r['after'].items() if k!='world'},
 'factions_before':r['before']['world'].get('factions'),'factions_after':r['after']['world'].get('factions'),
 'repeat':r.get('repeated_start',{}).get('status_code'),'repeated_pipeline_failure':r.get('repeated_pipeline_failure')} for r in rs])
reports=sorted((R/'development/campaigns/product_realization/pr_play_03').glob('*.md'))
selected_names=['baseline.json','entry_status.txt','final_status.txt','status_delta.json','historical_inventory.json','historical_excerpt.json','historical_provider_usage.jsonl',
 'performance_analysis.json','source_excerpts.md','source_index.json','reproduce.py','analyze.py','package.py','reproduction_outputs.json','reproduction_console.txt',
 'parser_controls.json','deterministic_checks.json','existing_tests.txt','existing_tests.xml','integrity.json','commands.json','state_transition_findings.json']
selected=[O/n for n in selected_names]+sorted(O.glob('*_output.json'))+sorted(O.glob('*_requests.json'))+reports
selected += [O/'review_config.json',R/'docs/NEXT_SESSION.md',R/'development/reports/pr_play_01/08_final_verdict_and_handoff.md',R/'development/reports/pr_play_02/08_final_verdict_and_handoff.md',R/'development/reports/pr_play_02/PR_PLAY_02_LIVE_PLAYTEST.txt']
config={'campaign_id':'pr_play_03','campaign_name':'PR-PLAY-03 — Campaign Opening Contract and Recovery Investigation','campaign_date':'2026-10-26',
 'purpose':'Offline bounded diagnosis; implementation/live authority NONE; stop after review ZIP.',
 'objective_status':'C — Missing provider evidence; independent bounded recovery/commit repair justified',
 'executive_summary':'Original provider text and finish evidence missing; no model/parser attribution claimed. Historical host failure reproduced exactly with synthetic SDK output. Opening enters generic unresolved/answer completion, seals safe_nonresolution and marks started. Engine-owned ticks are code-authorized, but success latch is misleading; pipeline exceptions permit repeated pressure. Recommend one reviewed PR-PLAY-04 opening acceptance/commit repair, preserving initialization. No production/prompt/schema/live-provider/state/frozen/experiment changes; no secrets, commit or push.',
 'primary_report':'development/campaigns/product_realization/pr_play_03/08_final_verdict_and_handoff.md',
 'supporting_files':[{'path':str(p.relative_to(R)).replace('\\','/'),'role':'investigation_evidence','why':'Explicit PR-PLAY-03 report, original excerpt, controlled input/output, source provenance or integrity evidence.'} for p in selected if p.name!='08_final_verdict_and_handoff.md' or p.parent.name!='pr_play_03'],
 'evidence_packets':['artifacts/validation_evidence/pr_play_03'],
 'changes':{'production':['None; protected hashes and inventories unchanged.'],'validation':['Disposable SDK-stub control harness and 27 assertions; 38 existing tests, no test-source changes.'],
 'tooling':['Campaign-local evidence/packaging scripts only.'],'documentation':['Eight reports, source ownership map, canonical session orientation.'],'generated_artifacts':['Historical excerpts, exact controls/messages, state/performance findings, integrity and review export.']},
 'testing':{'focused':'27 assertions pass across six controls; 38 existing focused tests pass in 3.072s.',
 'broader':'Not run; read-only scoped investigation.','full_suite':'Not run.','runtime_validation':'Direct production endpoint functions, real disposable saves, mocked SDK; no ASGI transport/UI.',
 'model_runtime_boundary':'Historical ledger only. New live calls 0; socket operations denied in reproduction.',
 'new_regressions':'No production change; existing defect controls are not product PASS.','pre_existing_failures':'Known HTTP gap not rerun. Rich structured synthetic fixture fails authority; captured separately, not concealed.'},
 'decisions_requiring_human_review':['Review verdict C and approve only the proposed PR-PLAY-04 opening acceptance/commit policy, separately from any provider investigation or live test.'],
 'known_problems':{'campaign_specific':['Original raw response/request/finish data unavailable. Generic answer adoption marks opening complete. Exception rollback retains pressure.'],
 'pre_existing':['Extensive dirty worktree retained. Frozen ATGB/PR-EG/R1/R2 authorities unchanged.']},
 'missing_concepts':[],
 'does_not_prove':['Original generation failure cause, output truncation, live repair effect, broad gameplay quality, independent generalization, updated benchmark, full regression, concurrent/crash-safe starts.'],
 'recommended_next_step':'After external review, authorize one PR-PLAY-04 opening failure acceptance and commit-integrity repair in existing API owner; no implementation performed now.',
 'self_contained_review_test':'Eight reports and map answer timeline, cause limits, recovery, state authority, controls and one next action. Package verification checks CRC, source hashes, explicit selection and sensitive-content exclusions.'}
write('review_config.json',config)
stage=R/'development/tmp/pr_play_03/review_stage'
result=build_handoff(config,root=R,output_dir=stage,archive_history=False)
prior_result=O/'build_result.json'
stamp=(Path(json.loads(prior_result.read_text())['timestamped_zip']).stem.removeprefix('CURRENT_REVIEW(').removesuffix(')')
       if prior_result.exists() else datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-4))).strftime('%Y%m%d-%H%M%S'))  # New York, 2026-10-26 EDT
timestamped=R/f'handoff/CURRENT_REVIEW({stamp}).zip'
shutil.copyfile(stage/'CURRENT_REVIEW.zip',timestamped)
for name in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json']:
    shutil.copyfile(stage/name,R/'handoff'/name)
history=R/'handoff/history/pr_play_03';history.mkdir(parents=True,exist_ok=True)
for src,dst in [('CURRENT_REVIEW.md','REVIEW.md'),('REVIEW_MANIFEST.json','REVIEW_MANIFEST.json'),('CURRENT_REVIEW.zip','REVIEW.zip')]:
    shutil.copyfile(stage/src,history/dst)
try:
    replacement=R/'handoff/PR_PLAY_03_review_replace.zip'
    shutil.copyfile(stage/'CURRENT_REVIEW.zip',replacement)
    os.replace(replacement,R/'handoff/CURRENT_REVIEW.zip')
    result['stable_zip_updated']=True
except OSError as e:
    result['stable_zip_updated']=False
    result['stable_zip_error']=str(e)
result['timestamped_zip']=str(timestamped)
write('build_result.json',result)
print(json.dumps({k:result[k] for k in ['file_count','zip_size_bytes','stable_zip_updated','timestamped_zip']}))
