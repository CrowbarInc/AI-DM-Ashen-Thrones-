"""Whole-request admission prevents fragment execution through ordinary HTTP."""
import copy
import pytest
from fastapi.testclient import TestClient
from game import storage
from game.api import app
from game.integrated_play import _LANES
from game.provider_budget import snapshot
from game.conversational_orchestration import actionable_coverage, compound_action_assessment
from tests.pr_play_79df3_harness import seed_gate
from tests.test_grounded_marking_removal import _ready


def authority():
    s=storage.load_session()
    return copy.deepcopy([storage.load_character(),storage.load_world(),storage.load_active_scene(),
                          storage.load_combat(),*[s.get(k) for k in ('turn_counter','clocks','active_scene_id','clue_knowledge')]])


@pytest.mark.parametrize('text',[
    'I drop my coat and enter Cinderwatch.',
    'I enter Cinderwatch and drop my coat.',
    'I examine my coat and enter Cinderwatch.',
    'I enter Cinderwatch, then examine my coat.',
    'I read the notice and take the northwest road.',
    'I take the northwest road and read the notice.',
    'I speak to the guard and enter Cinderwatch.',
    'I mark the gate and enter Cinderwatch.',
    'I copy the warning onto my sleeve using the available mud and enter Cinderwatch.',
    'I enter Cinderwatch and copy the warning onto my sleeve using the available mud.',
    'I try to copy the warning onto my sleeve with mud and enter Cinderwatch.',
    'I use mud to copy the warning onto my sleeve and enter Cinderwatch.',
    'I search my pockets and travel north.',
    'I drop my coat and read the notice and enter Cinderwatch.',
    'I enter Cinderwatch or take the northwest road.',
    "When the guard returns, I'll head north.",
    'Would inspecting the notice before leaving help?',
    "If you can't drop the coat, just enter Cinderwatch.",
])
def test_http_whole_request_no_partial_commit(tmp_path,monkeypatch,text):
    seed_gate(tmp_path,monkeypatch);_LANES.clear();_ready()
    for key in ('ASHEN_DISABLE_PROVIDER_CALLS','ASHEN_DISABLE_LIVE_INTERPRETATION','ASHEN_DISABLE_EXPRESSION_GENERATION','ASHEN_DISABLE_PROVIDER_RETRIES'):
        monkeypatch.setenv(key,'1')
    monkeypatch.delenv('ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION',raising=False)
    before=authority();n=len(snapshot()['records'])
    with TestClient(app) as client:
        payload={'text':text,'client_request_id':'compound-guard'}
        first=client.post('/api/chat?ui_mode=player',json=payload)
        duplicate=client.post('/api/chat?ui_mode=player',json=payload)
        assert first.status_code==duplicate.status_code==200
        assert first.json()==duplicate.json()
        assert authority()==before
        _LANES.clear()
        assert authority()==before
        assert len(snapshot()['records'])==n
        assert 'Nothing has been attempted' in first.json()['gm_output']['player_facing_text']
        travel=client.post('/api/chat?ui_mode=player',json={'text':'I enter Cinderwatch.','client_request_id':'single-recovery'})
        assert travel.status_code==200
        assert storage.load_session()['active_scene_id']=='market_quarter'
        assert storage.load_session()['turn_counter']==before[4]+1


@pytest.mark.parametrize('text',[
    'I carefully enter Cinderwatch.',
    'I slowly examine the notice.',
    'I quietly ask the guard about the patrol.',
    'I walk toward the gate with my coat over my shoulder.',
    'Knowing the patrol is missing, I enter Cinderwatch.',
    'After hearing about the road, I head north.',
    'Because the guard warned me, I inspect the notice.',
    'With the route in mind, I travel toward Old Milestone.',
    "I don't wait; I enter Cinderwatch.",
    'I inspect the taxes and curfew rules.',
    'I thank the guard and enter Cinderwatch.',
])
def test_modifiers_context_and_incidental_are_not_compound(text):
    assert not compound_action_assessment(text,scene=None)['unsupported_compound']
    assert actionable_coverage(text, scene=None)['classification'] == 'COMPLETE'


@pytest.mark.parametrize('text,classification', [
    ('I throw my coat onto the ground and enter Cinderwatch.', 'UNCERTAIN'),
    ('I put my coat down and enter Cinderwatch.', 'INCOMPLETE'),
    ('I drop my coat and my bag and enter Cinderwatch.', 'INCOMPLETE'),
    ('I enter Cinderwatch. I drop my coat.', 'INCOMPLETE'),
    ('I drop my coat and enter Cinderwatch.', 'INCOMPLETE'),
    ('I handle my belongings and enter Cinderwatch.', 'UNCERTAIN'),
    ('I carefully walk through the gate into Cinderwatch.', 'COMPLETE'),
    ("I don't wait; I enter Cinderwatch.", 'COMPLETE'),
    ('I enter Cinderwatch while carrying my coat.', 'COMPLETE'),
    ("I won't drop my coat, but I will enter Cinderwatch.", 'COMPLETE'),
    ('Can I put my coat down before entering Cinderwatch?', 'NON_EXECUTION'),
    ("I'll enter Cinderwatch tomorrow.", 'NON_EXECUTION'),
    ('I abandon the patrol inquiry and ask the Tavern Runner about stew.', 'COMPLETE'),
    ('I abandon buying stew and return to the patrol question.', 'NON_EXECUTION'),
    ('I return to the patrol question.', 'COMPLETE'),
    ('I return to Cinderwatch.', 'COMPLETE'),
    ('I put my coat down and return to Cinderwatch.', 'INCOMPLETE'),
    ('I drop my coat and enter Cinderwatch.', 'INCOMPLETE'),
])
def test_actionable_coverage_classification(text, classification):
    record = actionable_coverage(text, scene=None)
    assert record['classification'] == classification
    assert record['admission'] == ('proceed' if classification == 'COMPLETE' else 'withhold_execution' if classification in {'INCOMPLETE', 'UNCERTAIN'} else 'nonexecution')
    if classification in {'INCOMPLETE', 'UNCERTAIN'}:
        assert record['remaining_actionable']
