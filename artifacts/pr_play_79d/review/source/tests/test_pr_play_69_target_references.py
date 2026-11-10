"""PR69 finite target frames, provenance, repeats and HTTP publication."""
import copy,json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from game import api,storage
from game import integrated_investigation_narration as i, quarantined_investigation_narration as q
from tests.test_pr_play_66_publication import setup
from tests.test_pr_play_68_structured_publication import action_payload

ROOT=Path(__file__).resolve().parents[1]
HISTORY=ROOT/'artifacts/pr_play_69/historical_reproduction.json'
SAFE=['You examine the mud prints.','You take a moment to examine the mud prints.',
      'Your attention returns to the mud prints.','You take another look at the mud prints.',
      'You look over the mud prints.']
UNSAFE=['The mud prints belong to six riders.','The tracks lead east.',
    'The milestone contains a hidden compartment.','The notice board identifies the traitor.',
    'The tracks reveal a secret route.','You collect a valuable artifact.',
    'The gate is permanently opened.','The patrol is now dead.',
    'Your investigation unlocks a new destination.','The guards abandon their post.',
    'The prints seem important.','The tracks look unusual.','The milestone may hide something.',
    'The marks suggest a larger group.','Something about the board seems wrong.',
    'The prints are fresh.','The stone has been moved recently.',
    'CANARY_HIDDEN_DESTINATION lies beneath the milestone.']

def historical_hook():
    saved=json.loads(HISTORY.read_text(encoding='utf-8'))
    scene=json.loads((ROOT/'data/scenes/old_milestone.json').read_text(encoding='utf-8'))
    hook=q.build_hook_input(resolution=saved['hook']['resolution'],scene=scene,
        known_clue_texts=[x['text'] for x in saved['hook']['narration_payload']['scene']['discovered_clues']],
        player_text=saved['input'])
    return hook

def evaluate(raw,hook=None):
    contract,request=i.outcome_contract(hook or historical_hook())
    before=copy.deepcopy((contract,request))
    result,text=i.compose_authoritative(contract,request,raw,i.trusted_disclosure(request))
    assert before==(contract,request)
    return result,text

@pytest.mark.parametrize('raw',SAFE)
def test_safe_current_target(raw):
    audit,text=evaluate(raw)
    assert audit['decision']=='PASS'
    assert text==raw+' '+json.loads(HISTORY.read_text(encoding='utf-8'))['hook']['resolution']['clue_text']

@pytest.mark.parametrize('raw',UNSAFE)
@pytest.mark.parametrize('mixed',[False,True])
def test_unsafe_and_mixed(raw,mixed):
    audit,text=evaluate(('You examine the mud prints. ' if mixed else '')+raw)
    assert audit['decision']!='PASS' and text is None

@pytest.mark.parametrize('mode',['hidden','gated','invisible','invented','other_scene','failed','wrong_id'])
def test_target_provenance(mode):
    h=historical_hook();scene=json.loads((ROOT/'data/scenes/old_milestone.json').read_text())
    resolution=copy.deepcopy(h['resolution']);action=h['player_text']
    if mode=='hidden':scene['scene']['interactables'][1]['hidden']=True
    if mode=='gated':scene['scene']['interactables'][1]['requires']={'flag':'secret'}
    if mode=='invisible':scene['scene']['interactables'][1]['visible']=False
    if mode=='invented':action='I examine the crystal vault.'
    if mode=='other_scene':scene=json.loads((ROOT/'data/scenes/frontier_gate.json').read_text())
    if mode=='failed':resolution['success']=False
    if mode=='wrong_id':resolution['interactable_id']='milestone'
    current=q.build_hook_input(resolution=resolution,scene=scene,known_clue_texts=[],player_text=action)
    if mode!='failed':assert current['target_label'] is None
    audit,text=evaluate('You examine the mud prints.',current)
    assert audit['decision']!='PASS' and text is None

@pytest.mark.parametrize('target,raw',[
    ('weathered milestone','You study the weathered milestone.'),
    ('weathered stone','You take another look at the weathered stone.'),
    ('mud track','Your attention returns to the mud track.')])
def test_other_authored_names(target,raw):
    hook=historical_hook();scene=json.loads((ROOT/'data/scenes/old_milestone.json').read_text())
    resolution=hook['resolution'];resolution.update(interactable_id='prints' if target=='mud track' else 'milestone')
    hook=q.build_hook_input(resolution=resolution,scene=scene,known_clue_texts=[],player_text=f'I examine the {target}.')
    audit,text=evaluate(raw,hook)
    assert audit['decision']=='PASS'

@pytest.mark.parametrize('path',['structured','chat'])
def test_repeat_sequence(tmp_path,monkeypatch,path):
    setup(tmp_path,monkeypatch);original=i.run_integrated_hook;calls=[];resolutions=[]
    resolve=api._resolve_engine_noncombat_seam
    def resolve_once(*a,**kw):
        result=resolve(*a,**kw);resolutions.append(copy.deepcopy(result));return result
    monkeypatch.setattr(api,'_resolve_engine_noncombat_seam',resolve_once)
    def run(h,**kw):
        before=[storage.load_session(),storage.load_world(),storage.load_character(),storage.load_combat()]
        gen=q._Replay('', '');result=original(h,generator=gen);calls.append(gen.calls)
        assert before==[storage.load_session(),storage.load_world(),storage.load_character(),storage.load_combat()]
        return result
    monkeypatch.setattr(i,'run_integrated_hook',run)
    rows=[]
    with TestClient(api.app) as client:
        for text in ['I examine the weathered milestone.','I examine the weathered milestone again.',
                     'I examine the weathered milestone again.','I examine the mud prints.']:
            payload=action_payload(text,'weathered milestone') if path=='structured' else {'text':text}
            response=client.post('/api/action' if path=='structured' else '/api/chat',json=payload)
            assert response.status_code==200 and 'CANARY_' not in response.text
            rows.append(response.json())
    assert rows[0]['journal']['discovered_clues']==rows[-1]['journal']['discovered_clues']
    for row in rows[1:3]:
        text=row['gm_output']['player_facing_text']
        assert text.startswith('You examine the weathered milestone again.')
        assert 'nothing new' in text
        # Source-bound recall must retain the same disclosed clue, without
        # adding a discovery or accepting the empty provider candidate.
        assert all(clue in text for clue in rows[0]['journal']['discovered_clues'])
    assert calls==[1,1,1,1] and len(resolutions)==4

@pytest.mark.parametrize('path',['structured','chat'])
def test_mud_prints_http_publication(tmp_path,monkeypatch,path):
    setup(tmp_path,monkeypatch);original=i.run_integrated_hook
    monkeypatch.setattr(i,'run_integrated_hook',lambda h,**kw:original(h,generator=q._Replay(SAFE[1],'')))
    with TestClient(api.app) as client:
        text='I examine the mud prints.'
        payload=action_payload(text,'mud prints') if path=='structured' else {'text':text}
        r=client.post('/api/action' if path=='structured' else '/api/chat',json=payload)
    trace=q.evidence_records()[-1]
    assert trace['publication']['decision']=='published'
    assert trace['publication']['invariant']=='PASS'
    assert r.json()['gm_output']['player_facing_text'].startswith(SAFE[1])
    assert 'CANARY_' not in r.text
