"""Publisher-inclusive PR66 regressions; saved historical candidate, no live provider."""
import copy,json,os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from game import api,storage
from game import integrated_investigation_narration as i, quarantined_investigation_narration as q
from tests.test_pr_play_52_quarantined_integration import _seed,_forbid_provider,PRINT_CLUE
from tests.helpers.turn_pipeline_http_fixtures import _gm_response

NAMES=['accepted','rejected','empty','malformed','unavailable','timeout','FAIL','REVIEW_REQUIRED','VALIDATION_ERROR',
'legacy_stub','legacy_refusal','legacy_unknown','legacy_empty','missing','multiple','context','no_new','hidden',
'persistent','inventory','death','route','contradiction','duplicate','unsupported','resolution_failure','init_failure',
'flag_disabled','flag_enabled','continuity','state','cross_campaign','cross_session','schema','serialization',
'historical','accepted_publish','fast_path','one_call','no_loop','helper_exception','serialization_exception',
'interruption','invariant_recovery','stale_evidence']
ROWS=[]
@pytest.fixture(autouse=True)
def cleanup(monkeypatch):
    q.clear_evidence();q._PUBLICATION.set(None)
    yield
    q.clear_evidence();q._PUBLICATION.set(None)

def setup(tmp_path,monkeypatch):
    _forbid_provider(monkeypatch)
    _seed(tmp_path,monkeypatch,'old_milestone')
    monkeypatch.setenv(q.GATE_ENV,'1');monkeypatch.setenv(q.MODE_ENV,'integrated')
    monkeypatch.setenv(q.PUBLICATION_ENV,'1');monkeypatch.setenv(i.DISCLOSURE_ENV,'1')
    monkeypatch.setenv(q.PUBLICATION_SESSION_ENV,storage.load_session()['campaign_run_id'])
    monkeypatch.setenv(q.EVIDENCE_ENV,str(tmp_path/'evidence'))
    monkeypatch.setattr(api,'call_gpt',lambda *a,**k:_gm_response('I cannot provide a validated response to that request.'))

@pytest.mark.parametrize('name',NAMES)
def test_publication_http(tmp_path,monkeypatch,name):
    setup(tmp_path,monkeypatch)
    text='I examine the weathered milestone.';raw='You examine the weathered milestone.';fault='';decision=None
    if name in {'rejected','persistent'}:raw='The gate is permanently open.'
    if name=='empty':raw=''
    if name=='malformed':raw={}
    if name=='missing':raw=None
    if name=='unavailable':fault='provider_error'
    if name=='timeout':fault='timeout'
    if name in {'FAIL','REVIEW_REQUIRED','VALIDATION_ERROR'}:decision=name
    if name=='hidden':raw='CANARY_HIDDEN_DESTINATION is behind the gate.'
    if name=='inventory':raw='You acquire a silver key.'
    if name=='death':raw='The guard captain dies where he stands.'
    if name=='route':raw='You discover a second patrol route.'
    if name=='contradiction':raw='Three prints lead southeast from the milestone.'
    if name=='duplicate':raw=PRINT_CLUE
    legacy={'legacy_stub':'Provider calls are disabled for this run, so no live narration was generated.',
        'legacy_refusal':'I cannot provide a validated response to that request.',
        'legacy_unknown':'Some new unrecognized refusal.', 'legacy_empty':''}
    if name in legacy:raw=None
    if name in legacy:monkeypatch.setattr(api,'call_gpt',lambda *a,**k:_gm_response(legacy[name]))
    if name=='historical':
        from artifacts.pr_play_66 import harness
        h=harness.historical()
        storage.save_session(copy.deepcopy(h['state_before']['session']))
        storage._save_json(storage.CHARACTER_PATH,h['state_before']['character'])
        monkeypatch.setenv(q.PUBLICATION_SESSION_ENV,storage.load_session()['campaign_run_id'])
        raw=h['full_trace']['raw_provider_text'];text=h['input']
    if name=='context':
        session=storage.load_session();session.setdefault('runtime_scene_overlays',{}).setdefault('frontier_gate',{})['discovered_clues']=['The missing patrol was last seen taking the northwest mud track past the crates.'];storage.save_session(session)
    if name=='multiple':
        original_build=q.build_hook_input
        def build(**kw):
            h=original_build(**kw)
            if h.get('eligible'):
                h['resolution']['discovered_clues'].append('The missing patrol was last seen taking the northwest mud track past the crates.')
            return h
        monkeypatch.setattr(q,'build_hook_input',build)
    calls=[];state_guards=[];original=i.run_integrated_hook
    def run(h,**kw):
        before=[storage.load_session(),storage.load_world(),storage.load_character(),storage.load_combat()]
        gen=q._Replay(raw,fault)
        if name=='fast_path' and h['resolution']['state_changes'].get('already_searched'):
            row=original(h);calls.append(row['generator_calls'])
        else:
            row=original(h,generator=gen);calls.append(gen.calls)
        state_guards.append(before==[storage.load_session(),storage.load_world(),storage.load_character(),storage.load_combat()])
        if decision:row.update(validation={'decision':decision},used_fallback=True)
        return row
    monkeypatch.setattr(i,'run_integrated_hook',run)
    if name=='flag_disabled':monkeypatch.delenv(i.DISCLOSURE_ENV)
    if name in {'cross_campaign','cross_session'}:monkeypatch.setenv(q.PUBLICATION_SESSION_ENV,'other-session')
    if name=='unsupported':text='I travel to the invented crystal palace.'
    if name=='resolution_failure':
        def fail(*a,**k):raise RuntimeError('injected resolution failure')
        monkeypatch.setattr(api,'_resolve_engine_noncombat_seam',fail)
    if name=='init_failure':
        def fail(*a,**k):raise RuntimeError('injected initialization failure')
        monkeypatch.setattr(api,'load_campaign',fail)
    if name=='helper_exception':
        def fail(*a,**k):raise RuntimeError('injected publisher failure')
        monkeypatch.setattr(api,'_publish_experimental_integrated_narration',fail)
    if name=='invariant_recovery':
        monkeypatch.setattr(api,'_publish_experimental_integrated_narration',lambda *a,**k:None)
    if name=='serialization_exception':
        from starlette.responses import JSONResponse
        def fail(*a,**k):raise TypeError('injected serialization failure')
        monkeypatch.setattr(JSONResponse,'render',fail)
    if name=='fast_path':
        # Existing provider-free repeat branch is exercised without any provider call.
        monkeypatch.setenv('ASHEN_INTEGRATED_REPEAT_FAST_PATH','1')
        monkeypatch.setenv(q.LIVE_ENV,'1')
        monkeypatch.setattr(q,'live_provider_enabled',lambda:True)
    before=copy.deepcopy(storage.load_session())
    with TestClient(api.app,raise_server_exceptions=name not in {'resolution_failure','init_failure','serialization_exception'}) as client:
        if name in {'no_new','continuity','fast_path'}:
            first=client.post('/api/chat?ui_mode=player',json={'text':text});assert first.status_code==200
            text='I examine the weathered milestone again.';q.clear_evidence();calls.clear()
        response=client.post('/api/chat?ui_mode=player',json={'text':text})
        if name in {'resolution_failure','init_failure','serialization_exception'}:
            assert response.status_code>=400
            ROWS.append(dict(name=name,status=response.status_code,body=response.text,state_unchanged=before==storage.load_session(),publication_success=False));return
        assert response.status_code==200,response.text
        body=response.json();facing=body['gm_output']['player_facing_text']
        trace=copy.deepcopy(q.evidence_records()[-1]) if q.evidence_records() else {}
        isolated=name in {'flag_disabled','cross_campaign','cross_session','unsupported'}
        if not isolated:
            req=trace['authorized_outcome_contract']
            assert all(f['text'] in facing for f in req['must_communicate'])
            assert trace['publication']['invariant']=='PASS'
            assert all(state_guards)
            if name in {'accepted','accepted_publish'}:assert trace['publication']['decision']=='published'
            if name in {'helper_exception','invariant_recovery'}:assert trace['publication']['recovery_reason']
            if name not in {'accepted','accepted_publish','context','multiple','schema','serialization','state','flag_enabled','one_call','no_loop','interruption','stale_evidence','no_new','continuity'}:assert trace['publication']['decision']=='fallback',name
            if name=='context':assert 'northwest' not in facing
            assert sum(calls)<=1
            if name=='fast_path':assert trace['deterministic_fast_path'] and sum(calls)==0
        else:assert not trace.get('publication')
        assert not any(s in facing for s in ['CANARY_','silver key','permanently open','dies where','Three prints','second patrol'])
        if name in {'continuity','interruption'}:
            # TestClient proves construction. A dropped client is tested separately over TCP.
            follow=client.post('/api/chat?ui_mode=player',json={'text':'I examine the weathered milestone again.'})
            assert follow.status_code==200 and storage.load_session()['active_scene_id']=='old_milestone'
        if name=='stale_evidence':
            assert q.prepare_authoritative_publication({},storage.load_session()['campaign_run_id'],text) is None
        ROWS.append(dict(name=name,status=response.status_code,request={'text':text},body=body,
            trace=trace,state_before=before,state_after=storage.load_session(),narration_state_unchanged=all(state_guards),generator_calls=sum(calls)))

@pytest.fixture(scope='session',autouse=True)
def export():
    yield
    target=os.environ.get('PR66_MATRIX_OUTPUT')
    if target:Path(target).write_text(json.dumps(ROWS,indent=2,ensure_ascii=False),encoding='utf-8')
