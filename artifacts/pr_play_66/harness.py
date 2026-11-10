import os,sys,json,copy,hashlib,subprocess,shutil,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
for k in ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT','ASHEN_DISABLE_PROVIDER_CALLS','ASHEN_DISABLE_LIVE_INTERPRETATION','ASHEN_DISABLE_EXPRESSION_GENERATION','ASHEN_DISABLE_PROVIDER_RETRIES']:os.environ[k]='1'
from artifacts.pr_play_61 import run_experiment as base
base.OUT=OUT
from game import api,storage
from game import integrated_investigation_narration as i, quarantined_investigation_narration as q
from tests.helpers.turn_pipeline_http_fixtures import _gm_response,_patch_storage
from fastapi.testclient import TestClient

def save(n,v): (OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def historical():return json.loads((ROOT/'artifacts/pr_play_65/gameplay_actions.json').read_text())[-1]
def seed(name='session',historical_state=False):
    path=OUT/name
    if historical_state:
        _patch_storage(path,base._Patch())
        shutil.copytree(ROOT/'artifacts/pr_play_65/live_session/data',storage.DATA_DIR,dirs_exist_ok=True)
        h=historical()
        storage.save_session(copy.deepcopy(h['state_before']['session']))
        storage._save_json(storage.CHARACTER_PATH,h['state_before']['character'])
    else:base._seed(path,base._Patch(),'frontier_gate')
    base.enable_publication(storage.load_session()['campaign_run_id'],live=False)
    os.environ[i.DISCLOSURE_ENV]='1';os.environ[q.LABEL_ENV]='pr_play_66'
    api.call_gpt=lambda *a,**k:_gm_response('Provider calls are disabled for this run, so no live narration was generated.')
    return path
ORIGINAL=i.run_integrated_hook

def candidate(text=None,fault='',decision=None):
    def run(hook_input,**kw):
        row=ORIGINAL(hook_input,generator=q._Replay(text,fault))
        if decision:row.update(validation={'decision':decision},used_fallback=True)
        return row
    i.run_integrated_hook=run

def post(text):
    before=dict(session=storage.load_session(),character=storage.load_character(),world=storage.load_world(),combat=storage.load_combat())
    q.clear_evidence();start=time.perf_counter()
    with TestClient(api.app) as c:r=c.post('/api/chat?ui_mode=player',json={'text':text})
    body=r.json();trace=copy.deepcopy(q.evidence_records()[-1]) if q.evidence_records() else None
    after=dict(session=storage.load_session(),character=storage.load_character(),world=storage.load_world(),combat=storage.load_combat())
    return dict(request={'method':'POST','path':'/api/chat?ui_mode=player','json':{'text':text}},status_code=r.status_code,
        body=body,facing=base.facing(body),trace=trace,state_before=before,state_after=after,http_ms=round((time.perf_counter()-start)*1000,3))

if __name__=='__main__':
    assert not (OUT/'baseline.json').exists()
    sources=['game/api.py','game/quarantined_investigation_narration.py','game/integrated_investigation_narration.py','docs/NEXT_SESSION.md']
    (OUT/'entry_source').mkdir(exist_ok=True)
    for n in sources:(OUT/'entry_source'/Path(n).name).write_bytes((ROOT/n).read_bytes())
    protected=[p for root in ['data','artifacts/atgb','artifacts/pr_play_65'] for p in (ROOT/root).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    save('baseline.json',dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),status=subprocess.check_output(['git','status','--short'],text=True),protected_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in protected}))
    h=historical();save('historical_fixture.json',h)
    seed('baseline_reproduction',True);candidate(h['full_trace']['raw_provider_text'])
    row=post(h['input']);save('baseline_reproduction.json',row)
    print('Baseline:',row['status_code'],repr(row['facing']), 'hook includes:', h['full_trace']['trusted_disclosure'] in row['trace']['assembled'])
    assert h['full_trace']['trusted_disclosure'] not in row['facing']
    assert h['full_trace']['trusted_disclosure'] in row['trace']['assembled']
    # Developer authored publisher-inclusive inputs; frozen before source repair.
    rows=[]
    def add(group,text=None,fault='',legacy=None,expected='fallback',new=True,authoritative=True):
        rows.append(dict(id=f'H{len(rows)+1:02}',group=group,candidate=text,fault=fault,legacy=legacy,expected=expected,new=new,authoritative=authoritative,expected_state='same_as_disabled_control',mandatory=[h['full_trace']['trusted_disclosure']] if new and authoritative else []))
    for t,f in [(None,'provider_error'),(None,'timeout'),('', ''),({},''),(None,''),('unfinished',''),('The gate is permanently open.',''),('You acquire a crown.',''),('SECRET is behind the gate.',''),(h['full_trace']['raw_provider_text'],'')]:add('mandatory_fallback',t,f)
    for t in ['I cannot provide a validated response to that request.','Provider calls are disabled for this run, so no live narration was generated.','Unknown rejection.','',None,'Validation failed.','Provider unavailable.','Timeout.','Review required.','Malformed narration.']:add('legacy',legacy=t)
    for t in ['You examine the weathered milestone.','You inspect the weathered milestone.','You study the weathered milestone.','You focus on the weathered milestone.','You examine the weathered milestone carefully.']:add('accepted',t,expected='published')
    for t in ['The guard captain dies.','You acquire a silver key.','The gate is permanently open.','The patrol took the southeast road.','You find a hidden passage.']:add('unsafe',t)
    for t in [None,'',{},'unfinished','You acquire a crown.']:add('no_new',t,new=False)
    for t in [None,'failure','initialization','unsupported','missing_outcome']:add('authority_failure',t,expected='unchanged',authoritative=False)
    save('frozen_holdout.json',rows);save('frozen_holdout_manifest.json',dict(cases=len(rows),sha256=sha(OUT/'frozen_holdout.json'),frozen_before_implementation=True,developer_authored=True,independent_blind=False))
