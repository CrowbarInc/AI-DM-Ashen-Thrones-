"""PR-PLAY-32: isolated production HTTP experiment with reviewer continuation gates."""
import os, sys, json, time, socket, subprocess, threading, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.playtest import runner, gameplay as g
from tools.atgb.baseline import load_baseline, digest
from tools.atgb.isolation import prepare_isolated_store, player_campaign_dir_from_env
OUT=Path(__file__).parent
write=runner.write
run=ROOT/'artifacts/atgb/pr_play_32/live'
run.mkdir(parents=True,exist_ok=False)
for name in ('configuration','diagnostics','baseline','after','opening','reports'):(run/name).mkdir()
scenario=runner.load_scenario('FiveTurnGameplay')
scenario['provider_request_ceiling']=10
env=runner.child_environment(run,scenario,'Live','success')
env.update(ASHEN_OPENING_RENDERER='1',ASHEN_OPENING_RESPONSE_CAPTURE='1')
env['PYTHONPATH']=str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
assert env['ASHEN_PROVIDER_REQUEST_LIMIT']=='10'
assert env.get('ASHEN_DISABLE_LIVE_INTERPRETATION','0')=='0'
assert env.get('ASHEN_DISABLE_EXPRESSION_GENERATION','0')=='0'
source,manifest=load_baseline(ROOT)
write(OUT/'fixture_verification.json',dict(identifier='frontier-gate-v1',strict=True,verified=True,manifest_sha256=digest(source/'manifest.json'),manifest=manifest,content_sha256={n:digest(source/n) for n in manifest['files']}))
player=player_campaign_dir_from_env(ROOT)
prepare_isolated_store(run/'data',scenario_id='FiveTurnGameplay',repo=ROOT,player_campaign_dir=player)
write(run/'configuration/scenario.json',scenario)
write(run/'configuration/run.json',dict(scenario_id='FiveTurnGameplay',mode='Live',fixture_response='success',port=0,player_data=str(player),capture_response=True))
safe={k:env.get(k) for k in ('MODEL_NAME','DEFAULT_MODEL_NAME','HIGH_PRECISION_MODEL_NAME','RETRY_ESCALATION_MODEL_NAME','ENABLE_MODEL_ROUTING','ASHEN_PROVIDER_TIMEOUT_SECONDS')}
models={v for k,v in safe.items() if k.endswith('MODEL_NAME') and v}
assert models=={'gpt-4.1-mini'},safe
assert bool(env.get('OPENAI_API_KEY','').strip())
write(OUT/'safe_configuration.json',dict(provider='OpenAI Responses',configuration=safe,credentials_present=True,request_ceiling=10,sdk_retries=0,host_retries=0,fallback_models=0,opening_renderer=1))
subprocess.run(['git','status','--short'],cwd=ROOT,stdout=(OUT/'git_status_before.txt').open('w'),check=True)
write(OUT/'repository.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_hashes={str(p.relative_to(ROOT)):digest(p) for folder in ('game','tools/playtest','tools/atgb') for p in (ROOT/folder).glob('*.py')}))
actions=["I approach the tavern runner and ask what they're offering.",'What sort of rumors have you heard?','I head northwest of the crates to investigate the muddy footprints.','I go to Follow the missing patrol rumor.','I examine the footprints.']
result=dict(steps=[],turns=[],stop_reason=None)
process=None;started=time.monotonic();base=None
def call(method,path,body=None):
    start=time.monotonic()
    status,response=runner.request(base,method,path+'?ui_mode=player',110,body)
    row=dict(method=method,path=path,payload=body,http_status=status,response=response,api_latency_seconds=time.monotonic()-start)
    result['steps'].append(row);write(run/'reports/interactions.json',result['steps'])
    return row
def capture(label):
    folder=run/label;folder.mkdir(parents=True,exist_ok=True)
    row=call('GET','/api/state');assert row['http_status']==200
    write(folder/'public_state.json',row['response'])
    return runner.snapshot_files(run,label)
def gate(label,evidence):
    write(OUT/('awaiting_'+label+'.json'),evidence)
    deadline=time.monotonic()+1200
    decision=OUT/(label+'_decision.json')
    while not decision.exists() and time.monotonic()<deadline:time.sleep(.25)
    assert decision.exists(),'Review gate timeout'
    accepted=json.loads(decision.read_text())
    write(run/'reports'/(label+'_decision.json'),accepted)
    return accepted.get('pass') is True
try:
    process=runner.start_worker(run,env,script=OUT/'worker_capture.py')
    secrets=[v for k,v in env.items() if len(v)>6 and any(s in k.lower() for s in ('key','token','secret','password','credential'))]
    logger=threading.Thread(target=runner.bounded_log,args=(process.stdout,run/'diagnostics/application.log',secrets),daemon=True);logger.start()
    ready,base=runner.wait_for_http_ready(process,run,30)
    assert ready['sdk_retries']==ready['host_retries']==0 and ready['limits'][0]==10
    assert ready['model']=='gpt-4.1-mini' and ready['opening_renderer']['selected']
    write(OUT/'network_readiness.json',dict(http_ready=True,base=base,provider_requests=0,ready=ready))
    if not gate('preflight',dict(ready=ready,configuration=safe,fixture_verified=True)):
        result['stop_reason']='critical_preflight_failure'
    else:
        with (OUT/'live_attempt_authorized_once.json').open('x') as f:json.dump(dict(max_initializations=1,max_actions=5,max_provider_requests=10),f)
        capture('initial')
        row=call('POST','/api/new_campaign',dict(ui_mode='player'));assert row['http_status']==200
        before=capture('baseline');offset=len(g.read_events(run))
        opening=call('POST','/api/start_campaign',dict(ui_mode='player'))
        after=capture('opening')
        integrity=runner.compare(before,after,accepted=opening['http_status']==200,opening_response=opening['response'])
        write(run/'opening/integrity.json',integrity);write(run/'opening/state_diff.json',g.diff(before,after))
        result['opening']=opening;result['opening_integrity']=integrity
        if not gate('opening',dict(opening=opening,integrity=integrity,events=g.read_events(run)[offset:])):
            result['stop_reason']='opening_acceptance_failure'
        else:
            for i,text in enumerate(actions,1):
                usage=json.loads((run/'diagnostics/budget_snapshot.json').read_text())
                # Deterministic routing skips interpretation at T3/T4; T4 may narrate arrival.
                reserve={1:2,2:2,3:1,4:1,5:2}[i]
                decision=dict(turn=i,remaining=10-usage['dispatched_requests'],required_reserve=reserve,allow=not usage['stopped'] and 10-usage['dispatched_requests']>=reserve)
                write(run/'reports'/f'T{i}_budget_decision.json',decision)
                if not decision['allow']:result['stop_reason']='insufficient_budget_for_complete_action';break
                folder=f'turns/T{i}';before=capture(folder+'/before');offset=len(g.read_events(run))
                row=call('POST','/api/chat',dict(text=text,ui_mode='player'))
                after=capture(folder+'/after');events=g.read_events(run)[offset:]
                a=dict(next(a for a in scenario['actions'] if a['kind']=='player_turn'))
                a.update(step_id=f'T{i}',player_input=text,subject_terms=['stew','rumor','patrol','prints','pending'],requires_substantive_answer=i<3,interaction_category='interaction' if i<3 else 'movement' if i==4 else 'investigate',allowed_destinations=['old_milestone'] if i==4 else [])
                evaluation=g.evaluate(a,row['http_status'],row['response'],before,after,events)
                write(run/folder/'api_response.json',row);write(run/folder/'state_diff.json',g.diff(before,after));write(run/folder/'evaluation.json',evaluation);write(run/folder/'events.json',events)
                result['turns'].append(dict(turn=i,row=row,evaluation=evaluation));write(OUT/'live_result.json',result)
                if not gate(f'T{i}',dict(row=row,evaluation=evaluation)):
                    result['stop_reason']=f'T{i}_continuation_gate_failed';break
            else:result['stop_reason']='five_actions_complete'
        capture('after')
except BaseException as exc:
    result.update(error_type=type(exc).__name__,error_detail=str(exc)[:500]);result['stop_reason']=result['stop_reason'] or 'environment_or_controller_failure'
finally:
    result['cleanup']=runner.stop_owned(process,5)
    if process:logger.join(timeout=3)
    result['duration_seconds']=time.monotonic()-started
    path=run/'diagnostics/budget_snapshot.json'
    result['provider_usage']=json.loads(path.read_text()) if path.exists() else {}
    write(OUT/'live_result.json',result);write(run/'reports/result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('steps','turns','opening')}))
