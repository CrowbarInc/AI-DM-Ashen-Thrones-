"""Structured/chat publication parity at the actual player HTTP boundary."""
import copy,json
import pytest
from fastapi.testclient import TestClient
from game import api,storage
from game import integrated_investigation_narration as i, quarantined_investigation_narration as q
from tests.test_pr_play_66_publication import setup
from tests.test_pr_play_52_quarantined_integration import _seed,PRINT_CLUE,NOTICE_CLUE

def action_payload(text, target='milestone'):
    a=next(a for a in api.compose_state()['ui']['affordances'] if target in a['label'].lower())
    return dict(action_type='exploration',intent=text,exploration_action=dict(
        id=a['id'],label=a['label'],type=a['type'],targetSceneId=a.get('target_scene_id'),
        targetEntityId=a.get('target_id'),targetLocationId=a.get('target_location_id'),prompt=text,metadata=a.get('metadata',{})))

FAULTS=['accepted','rejected','empty','malformed','unavailable','timeout','FAIL','REVIEW_REQUIRED','VALIDATION_ERROR','legacy_refusal',
        'helper_exception','helper_missing','duplicate','hidden','persistent','inventory','death','route','contradiction']

def execute(tmp_path,mp,*,fault='accepted',path='structured',scene='old_milestone',raw=None):
    setup(tmp_path,mp)
    if scene!='old_milestone':
        _seed(tmp_path,mp,scene);mp.setenv(q.PUBLICATION_SESSION_ENV,storage.load_session()['campaign_run_id'])
    target='notice board' if scene=='frontier_gate' else 'weathered milestone'
    text=f'I examine the {target}.';mandatory=NOTICE_CLUE if scene=='frontier_gate' else PRINT_CLUE
    samples=dict(rejected='The gate is permanently open.',empty='',malformed={},legacy_refusal=None,duplicate=mandatory,
        hidden='CANARY_HIDDEN_DESTINATION is behind the gate.',persistent='The gate is permanently open.',
        inventory='You acquire a silver key.',death='The guard captain dies where he stands.',
        route='You discover a second patrol route.',contradiction='Three prints lead southeast from the milestone.')
    raw=samples.get(fault,f'You examine the {target}.') if raw is None else raw
    calls=[];guards=[];resolutions=[];original=i.run_integrated_hook;resolve=api._resolve_engine_noncombat_seam
    def resolve_once(*a,**kw):
        r=resolve(*a,**kw);resolutions.append(copy.deepcopy(r));return r
    mp.setattr(api,'_resolve_engine_noncombat_seam',resolve_once)
    def run(h,**kw):
        before=[storage.load_session(),storage.load_world(),storage.load_character(),storage.load_combat()]
        gen=q._Replay(raw,'timeout' if fault=='timeout' else 'provider_error' if fault=='unavailable' else '')
        row=original(h,generator=gen);calls.append(gen.calls)
        guards.append(before==[storage.load_session(),storage.load_world(),storage.load_character(),storage.load_combat()])
        if fault in {'FAIL','REVIEW_REQUIRED','VALIDATION_ERROR'}:row.update(validation={'decision':fault},used_fallback=True)
        return row
    mp.setattr(i,'run_integrated_hook',run)
    if fault=='helper_exception':
        def fail(*a,**kw):raise RuntimeError('publisher fault')
        mp.setattr(api,'_publish_experimental_integrated_narration',fail)
    if fault=='helper_missing':mp.setattr(api,'_publish_experimental_integrated_narration',lambda *a,**kw:None)
    q.clear_evidence()
    with TestClient(api.app) as client:
        payload=action_payload(text,'notice board' if scene=='frontier_gate' else 'weathered milestone') if path=='structured' else {'text':text}
        response=client.post('/api/action' if path=='structured' else '/api/chat',json=payload)
    assert response.status_code==200,response.text
    body=response.json();facing=body['gm_output']['player_facing_text'];trace=copy.deepcopy(q.evidence_records()[-1])
    assert mandatory in facing and mandatory in body['journal']['discovered_clues']
    assert facing.count(mandatory)==1 and 'cannot provide' not in facing
    assert 'CANARY_' not in response.text and 'discoverable_clues' not in response.text
    assert all(guards) and sum(calls)==1 and len(resolutions)==1
    assert storage.load_session()['gm_notes']==['CANARY_GM_NOTE']
    assert trace['publication']['invariant']=='PASS'
    return dict(body=body,trace=trace,raw=raw,resolutions=resolutions,authority=storage.load_session(),calls=calls)

@pytest.mark.parametrize('fault',FAULTS)
@pytest.mark.parametrize('path',['structured','chat'])
def test_failure_and_publication_parity(tmp_path,monkeypatch,fault,path):
    row=execute(tmp_path,monkeypatch,fault=fault,path=path)
    assert row['trace']['publication']['decision']==('published' if fault=='accepted' else 'fallback')

@pytest.mark.parametrize('path',['structured','chat'])
def test_notice_publication(tmp_path,monkeypatch,path):
    execute(tmp_path,monkeypatch,path=path,scene='frontier_gate')

@pytest.mark.parametrize('raw',[
    'You take a moment to examine the weathered milestone.',
    'You pause to inspect the weathered milestone.',
    'You turn your attention to the weathered milestone.',
    'You look more closely at the weathered milestone.',
    'You give the weathered milestone your attention.',
])
def test_natural_attention_frames(tmp_path,monkeypatch,raw):
    row=execute(tmp_path,monkeypatch,raw=raw)
    assert row['trace']['publication']['decision']=='published'
    assert row['body']['gm_output']['player_facing_text']==raw+' '+PRINT_CLUE

@pytest.mark.parametrize('raw',[
    'You pause to inspect the weathered milestone and acquire a silver key.',
    'You turn your attention to the weathered milestone. The guard dies.',
    'You look more closely at the hidden vault.',
    'You give the weathered milestone your attention; the gate is permanently open.',
])
def test_attention_frame_cannot_smuggle_claims(tmp_path,monkeypatch,raw):
    row=execute(tmp_path,monkeypatch,raw=raw)
    assert row['trace']['publication']['decision']=='fallback'

def test_resolution_failure_is_error(tmp_path,monkeypatch):
    setup(tmp_path,monkeypatch);payload=action_payload('I examine the weathered milestone.')
    before=storage.load_session()
    def fail(*a,**k):raise RuntimeError('CANARY_RESOLVER_ERROR')
    monkeypatch.setattr(api,'_resolve_engine_noncombat_seam',fail)
    with TestClient(api.app,raise_server_exceptions=False) as client:r=client.post('/api/action',json=payload)
    assert r.status_code==500 and 'CANARY_' not in r.text
    assert before==storage.load_session()

def test_unsupported_stays_rejected(tmp_path,monkeypatch):
    setup(tmp_path,monkeypatch)
    with TestClient(api.app) as client:r=client.post('/api/action',json={'action_type':'invented'})
    assert r.status_code in {200,422}
    if r.status_code==200:assert r.json().get('ok') is False

@pytest.mark.parametrize('gate',['disabled','wrong_session'])
def test_experimental_isolation(tmp_path,monkeypatch,gate):
    setup(tmp_path,monkeypatch)
    monkeypatch.setenv(q.PUBLICATION_ENV,'0' if gate=='disabled' else '1')
    if gate=='wrong_session':monkeypatch.setenv(q.PUBLICATION_SESSION_ENV,'other-session')
    q.clear_evidence()
    with TestClient(api.app) as client:r=client.post('/api/action',json=action_payload('I examine the weathered milestone.'))
    assert r.status_code==200
    assert not any(row.get('publication') for row in q.evidence_records())
