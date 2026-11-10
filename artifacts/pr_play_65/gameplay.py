"""Existing FastAPI HTTP route, isolated copies, actual bounded provider calls."""
import copy,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
from artifacts.pr_play_61 import run_experiment as base
base.OUT=OUT
os.environ['ASHEN_PROVIDER_USAGE_PATH']=str(OUT/'provider_usage.jsonl')
os.environ['ASHEN_PROVIDER_REQUEST_LIMIT']='6'
os.environ['ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT']='12000'
os.environ['ASHEN_PROVIDER_INPUT_TOKEN_LIMIT']='10000'
os.environ['ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT']='2000'
from game import api,storage
from game import integrated_investigation_narration as i
from game import quarantined_investigation_narration as q
from game.provider_budget import snapshot
from tests.helpers.turn_pipeline_http_fixtures import _gm_response
api.call_gpt=lambda *a,**k:_gm_response('Provider calls are disabled for this run, so no live narration was generated.')
resolution_times=[]
resolve_original=api._resolve_engine_noncombat_seam
def timed_resolution(*a,**k):
    start=time.perf_counter()
    try:return resolve_original(*a,**k)
    finally:resolution_times.append(round((time.perf_counter()-start)*1000,3))
api._resolve_engine_noncombat_seam=timed_resolution
def save(n,v):(OUT/n).write_text(json.dumps(base.redact(v),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def state():return dict(authority=base.authority(),session=storage.load_session(),character=storage.load_character())
def post(text):
    before=state();q.clear_evidence();resolution_times.clear();r=base.post_all([text])[0]
    r.update(state_before=before,state_after=state(),full_trace=copy.deepcopy(q.evidence_records()[-1]) if q.evidence_records() else None)
    r['deterministic_resolution_ms']=list(resolution_times)
    return r
def scrub(a):return {k:v for k,v in a.items() if k!='campaign_run_id'}
original=i.run_integrated_hook
if '--probe' in sys.argv:
    base.disable_publication();base._seed(OUT/'transition_probe',base._Patch(),'frontier_gate')
    actions=[base.NOTICE,'I follow the missing patrol rumor.','I examine the weathered milestone.']
    rows=[post(t) for t in actions]
    save('transition_probe.json',rows)
    print([(r['mechanical']['kind'],r['authority']['scene'],r['facing'][:100]) for r in rows])
    raise SystemExit()
assert not (OUT/'gameplay_actions.json').exists(),'No repeat live run'
# Three requested provider categories, then existing authored exit + examination.
actions=[base.NOTICE,base.BARREL,base.REPEAT,'I follow the missing patrol rumor.','I examine the weathered milestone.']
base.disable_publication();base._seed(OUT/'control_session',base._Patch(),'frontier_gate')
control=[post(t) for t in actions];save('control.json',control)
base._seed(OUT/'live_session',base._Patch(),'frontier_gate')
base.enable_publication(storage.load_session()['campaign_run_id'],live=base.key_present())
os.environ[i.DISCLOSURE_ENV]='1';os.environ[q.LABEL_ENV]='pr_play_65_live'
os.environ.pop('ASHEN_INTEGRATED_REPEAT_FAST_PATH',None)
q.reset_live_budget();rows=[]
for text in actions:
    r=post(text);rows.append(r);save('gameplay_actions.json',rows)
    print(text,r['status_code'],r['published_marker'],r['authority']['scene'],flush=True)
save('provider_snapshot.json',snapshot())
save('state_integrity.json',dict(per_action=[dict(action=a['input'],authority_equal=scrub(a['authority'])==scrub(b['authority']),resolution_equal=a['mechanical']==b['mechanical']) for a,b in zip(rows,control)]))
save('isolation.json',base.isolation_check('different-bound-session'))
base.disable_publication();os.environ.pop(i.DISCLOSURE_ENV,None)
save('live_summary.json',dict(provider_available=base.key_present(),pathway='FastAPI TestClient HTTP /api/chat?ui_mode=player; no browser/TCP client',
    gameplay_actions=len(rows),live_provider_requests=sum(int((r['full_trace'] or {}).get('provider_requests') or 0) for r in rows),
    validated_ai=sum((r['full_trace'] or {}).get('used_fallback') is False for r in rows),
    published_ai=sum(r['published_marker']=='published' for r in rows),
    fallbacks=sum((r['full_trace'] or {}).get('used_fallback') is True for r in rows),
    http_latency_ms=[r['http_ms'] for r in rows]))
