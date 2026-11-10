"""Offline-only failure injection after the HTTP publication stop condition."""
import copy,hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
os.environ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT']='1'
os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1'
os.environ['ASHEN_DISABLE_LIVE_INTERPRETATION']='1'
from game import integrated_investigation_narration as i
from game import quarantined_investigation_narration as q
from tests.test_pr_play_57_integrated_narration import hook, ROUTE
from game import api
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
os.environ[i.DISCLOSURE_ENV]='1';os.environ[q.PUBLICATION_ENV]='1'
cases=[('provider_unavailable',None,'provider_error'),('timeout',None,'timeout'),('empty','',''),
       ('malformed',{},''),('unauthorized_discovery','You discover a second patrol route.',''),
       ('persistent','The gate is permanently open.',''),('inventory','You acquire a silver key.',''),
       ('hidden','SECRET is behind the gate.',''),('contradiction',ROUTE.replace('northwest','southeast'),''),
       ('duplicate',ROUTE,''),('missing_ai_coverage','You examine the notice board.','')]
rows=[]
for name,text,fault in cases:
    h=hook();before=copy.deepcopy(h);r=i.run_integrated_hook(h,generator=q._Replay(text,fault))
    c,req=i.outcome_contract(h);v=i.validate_integrated(c,req,r['assembled'])
    rows.append(dict(name=name,scope='offline complete hook, not HTTP',result=r,final_validation=v,
        passed=v['decision']=='PASS' and h==before and (name=='missing_ai_coverage' or r['used_fallback']),state_unchanged=h==before))
# Unsupported travel is checked against the existing grammar without resolving it.
from game.intent_parser import parse_freeform_to_action
scene=json.loads((ROOT/'data/scenes/frontier_gate.json').read_text())
unsupported=parse_freeform_to_action('I travel to the invented crystal palace.',scene,session={})
rows.append(dict(name='unsupported_followup',scope='offline existing parser only',action=unsupported,
    passed=not bool(unsupported.get('target_scene_id') or unsupported.get('targetSceneId'))))
# Reproduce the failing publication gate using detached response objects only.
live=json.loads((OUT/'gameplay_actions.json').read_text());trace=live[-1]['full_trace']
q.clear_evidence();q._MEMORY.append(copy.deepcopy(trace))
os.environ[q.GATE_ENV]='1';os.environ[q.MODE_ENV]='integrated';os.environ[q.PUBLICATION_SESSION_ENV]='offline-bound'
gm={'player_facing_text':'I cannot provide a validated response to that request.','metadata':{}}
api._publish_experimental_integrated_narration(gm,gm,{'gm_output':gm},{'kind':'discover_clue'},
    {'campaign_run_id':'offline-bound'},trace['player_text'])
rows.append(dict(name='interrupted_or_failed_publication',scope='detached publication helper; no HTTP/provider/state write',
    passed=False, trusted=trace['trusted_disclosure'],published=gm['player_facing_text'],
    finding='Trusted fallback suppressed when incoming legacy text is not the provider-disabled stub. Existing marker is copy-only, not client acknowledgement.'))
os.environ.pop(i.DISCLOSURE_ENV,None)
r=i.run_integrated_hook(hook(),generator=q._Replay('You examine the notice board.',''))
rows.append(dict(name='flag_disabled',scope='offline legacy hook',passed='trusted_disclosure' not in r and r['used_fallback']))
save('failure_injection.json',dict(cases=len(rows),passed=sum(r['passed'] for r in rows),rows=rows,
    limitation='Publication interruption has no durable client ACK/replay queue. Reproduced suppression offline; no new experimental HTTP after stop.'))
save('critical_incident.json',dict(verdict='C — FAIL / CRITICAL DEFECT',
    classification='implementation',action=live[-1]['input'],
    mandatory=trace['trusted_disclosure'],hook_assembled=trace['assembled'],published=live[-1]['facing'],
    state_before=live[-1]['state_before'],state_after=live[-1]['state_after'],
    reason='Existing publication helper returns without fallback substitution for legacy rejection text.',
    response='Stopped experimental HTTP and provider execution; default-off flag remains unset outside isolated subprocess. No holdout tuning or source repair after freeze.'))
save('initial_offline_diagnosis.json',dict(observed_tests=39,initial_failed=2,
    accepted_unsafe_candidates=['SECRET is behind the gate.','Undisclosed milestone prints literal'],
    scope='Offline development only; no HTTP/provider/publication',
    correction='Additional finite presentation boundary; all existing gates retained. Corrected before implementation freeze and holdout execution.'))
q.clear_evidence()
for key in (i.DISCLOSURE_ENV,q.GATE_ENV,q.MODE_ENV,q.PUBLICATION_ENV,q.PUBLICATION_SESSION_ENV,q.LIVE_ENV):os.environ.pop(key,None)
baseline=json.loads((OUT/'baseline.json').read_text())
changed=[n for n,h in baseline['protected_hashes'].items() if not (ROOT/n).exists() or hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h]
save('protected_integrity.json',dict(checked=len(baseline['protected_hashes']),changed=changed,passed=not changed))
print(json.dumps(dict(faults=len(rows),passed=sum(r['passed'] for r in rows),protected_changed=changed)))
