"""Source recall and completed-publication behavior; offline providers only."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from game import storage
from game.exploration import _source_disclosed_facts, resolve_exploration_action
from game.defaults import default_session, default_character, default_world
from game.publication_contract import narration_skip, record_completed_publication

CONDITIONS = ['known','third','reload','travel_return','conversation','other_discovery',
              'hidden','other_source','modified','removed','stale','implicit', 'contradiction',
              'partial', 'failed', 'invalid', 'cross_campaign', 'ambiguous', 'legacy', 'wrong_scene']


def recall_fixture(source, fact, condition):
    session = default_session()
    session['active_scene_id'] = 'observatory'
    entry = dict(state='discovered', presentation='explicit', source_scene='observatory',
                 source_interactable=source, text=fact)
    scene = dict(id='observatory', visible_facts=[f'A {source} is visible.'],
                 interactables=[dict(id=source, label=source, type='investigate', reveals_clue='fact')],
                 discoverable_clues=[dict(id='fact', text=fact), dict(id='hidden', text='CANARY_HIDDEN')])
    session['clue_knowledge'] = {'fact': entry}
    if condition in {'hidden','failed','cross_campaign'}: session['clue_knowledge'] = {}
    if condition == 'other_source': entry['source_interactable'] = 'different'
    if condition == 'wrong_scene': entry['source_scene'] = 'elsewhere'
    if condition in {'modified','contradiction'}: scene['discoverable_clues'][0]['text'] = 'CANARY_HIDDEN modified text'
    if condition == 'removed': scene['interactables'] = []
    if condition == 'stale': entry['stale'] = True
    if condition == 'invalid': entry['valid'] = False
    if condition == 'implicit': entry['presentation'] = 'implicit'
    if condition == 'legacy': entry.pop('source_interactable')
    if condition == 'ambiguous':
        entry.pop('source_interactable')
        scene['interactables'].append(dict(id='other', reveals_clue='fact'))
    if condition == 'other_discovery': session['clue_knowledge']['other'] = dict(entry, text='CANARY_HIDDEN unrelated')
    if condition == 'conversation': session['active_interlocutor'] = 'astronomer'
    if condition == 'travel_return': session['visited_scene_ids'] = ['observatory','garden','observatory']
    if condition == 'reload': session = json.loads(json.dumps(session))
    return scene, session


def exercise_recall(source, fact, condition):
    scene, session = recall_fixture(source, fact, condition)
    before = copy.deepcopy((scene, session))
    items = scene['interactables']
    recalled = _source_disclosed_facts(scene, session, items[0]) if items else ()
    assert (scene, session) == before
    assert 'CANARY_' not in json.dumps(recalled)
    return recalled


@pytest.mark.parametrize('source,fact', [('chart','The chart records four moons.'), ('plaque','The plaque names the mason Eda.')])
@pytest.mark.parametrize('condition', CONDITIONS)
def test_source_recall(source, fact, condition):
    expected = condition in {'known','third','reload','travel_return','conversation','other_discovery','partial','legacy'}
    assert exercise_recall(source, fact, condition) == ((fact,) if expected else ())


@pytest.mark.parametrize('kind', ['dialogue','narration','mixed','fallback','clarification','unsupported','error','rejected'])
def test_completed_record(tmp_path, monkeypatch, kind):
    path = tmp_path/'publication.jsonl'
    monkeypatch.setenv('ASHEN_PUBLICATION_TRACE_PATH', str(path))
    text = 'Aster says, "The charts are old."'
    rows = []
    if kind in {'dialogue','mixed'}: rows.append(dict(kind='dialogue',decision='accepted',text=text))
    if kind in {'narration','mixed'}: rows.append(dict(kind='narration',decision='accepted',text='You step away.'))
    if kind == 'rejected': rows.append(dict(kind='dialogue',decision='rejected',text='CANARY_HIDDEN'))
    text = ('You step away. '+text) if kind in {'narration','mixed'} else text
    body = {'gm_output': {'player_facing_text': text}}
    if kind == 'error':
        from fastapi.responses import JSONResponse
        body = JSONResponse(status_code=409, content={'error': 'Please retry.'})
    record = record_completed_publication(body, source_handler='test', presentation_rows=rows)
    saved = [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
    assert saved == [record]
    assert record['published_expression_reference'] == hashlib.sha256(record['final_player_facing_response'].encode()).hexdigest()
    assert 'CANARY_HIDDEN' not in path.read_text()
    assert bool(record['accepted_expression_references']) == (kind in {'dialogue','narration','mixed'})


def test_repeat_resolution_read_only():
    scene, session = recall_fixture('chart', 'The chart records four moons.', 'known')
    from game.storage import mark_interactable_resolved
    mark_interactable_resolved(session, 'observatory', 'chart')
    before = copy.deepcopy((scene,session))
    result = resolve_exploration_action({'scene': scene}, session, default_world(),
        dict(id='chart',target_id='chart',type='investigate',prompt='I examine the chart again.'),
        raw_player_text='I examine the chart again.', character=default_character())
    assert (scene,session) == before
    assert result['discovered_clues'] == []
    assert 'The chart records four moons.' in result['metadata']['engine_publication']
    untouched = copy.deepcopy(result)
    assert narration_skip(result)[0] == result['metadata']['engine_publication']
    assert result == untouched


def test_no_unpublished_candidate_reference(tmp_path, monkeypatch):
    monkeypatch.setenv('ASHEN_PUBLICATION_TRACE_PATH', str(tmp_path/'p.jsonl'))
    row = record_completed_publication({'gm_output': {'player_facing_text':'You find nothing new.'}},
        source_handler='test', presentation_rows=[dict(kind='dialogue', decision='accepted', text='Unpublished candidate')])
    assert row['accepted_expression_references'] == []
    assert row['validation_outcome'] == 'engine_or_grounded_fallback'


def test_alternate_dialogue_owner_provenance(tmp_path, monkeypatch):
    monkeypatch.setenv('ASHEN_PUBLICATION_TRACE_PATH', str(tmp_path/'p.jsonl'))
    text = 'The astronomer says, "I do not know."'
    context = dict(owner='bounded_improvisation.conversation', visible=text,
                   dialogue_accepted=True, dialogue_published=True)
    row = record_completed_publication({'gm_output':{'player_facing_text':text}},
        source_handler='api_chat', publication_context=context,
        provider_rows=[dict(sent=True, attempt_id='current')])
    assert row['response_category'] == 'dialogue' and row['provider_involvement']
    assert row['provider_attempt_references'] == ['current']
    assert len(row['accepted_expression_references']) == 1
    stale = record_completed_publication({'gm_output':{'player_facing_text':text}},
        source_handler='api_chat', publication_context=context)
    assert stale['accepted_expression_references'] == []


@pytest.mark.parametrize('contract,category', [('CLARIFICATION_REQUIRED','clarification'),('UNSUPPORTED_ACTION','unsupported_action'),('FAILURE','failure')])
def test_response_categories(tmp_path, monkeypatch, contract, category):
    monkeypatch.setenv('ASHEN_PUBLICATION_TRACE_PATH', str(tmp_path/'p.jsonl'))
    row = record_completed_publication({'gm_output':{'player_facing_text':'A grounded response.'}},
        source_handler='api_chat', publication_contract=contract)
    assert row['response_category'] == category


def test_http_error_publication(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from game import api
    path = tmp_path/'p.jsonl'
    monkeypatch.setenv('ASHEN_PUBLICATION_TRACE_PATH', str(path))
    with TestClient(api.app) as client:
        response = client.post('/api/chat?ui_mode=player', json={'text':{'invalid':'CANARY_HIDDEN'}})
    assert response.status_code == 422
    rows = [json.loads(s) for s in path.read_text().splitlines()]
    assert len(rows) == 1 and rows[0]['response_category'] == 'error'
    assert 'CANARY_' not in path.read_text()


@pytest.mark.parametrize('accepted', [True,False])
def test_physical_expression_is_settled_once(ready_physical, monkeypatch, accepted):
    from game import bounded_improvisation as bounded, integrated_play
    from game.publication_contract import ADJUDICATION_RESULT
    from game.physical_adjudication import plan_physical
    session, scene, world = ready_physical
    text = 'I approach the notice board.'
    calls = []
    def narrate(facts, **kwargs):
        calls.append(facts)
        return {'text':facts} if accepted else None
    monkeypatch.setattr(integrated_play, 'maybe_narrate', narrate)
    plan = bounded.controlled_request(text, session=session, scene=scene, world=world)
    assert plan and plan.get('physical')
    result = bounded.resolve_controlled_fact(scene, session, world,
        {'id':plan['id'],'target_id':plan['id']}, prompt=text, action_id=plan['id'], label='approach')
    assert result and result['metadata']['bounded_expression_attempted']
    assert narration_skip(result, scene=scene, session=session)
    assert len(calls) == 1


@pytest.fixture
def ready_physical(monkeypatch):
    from tests.test_pr_play_76_physical import enable
    from tests.test_pr_play_79a_continuity import gate
    enable(monkeypatch)
    monkeypatch.setenv('ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION','1')
    session, scene, world = gate()
    scene['scene']['interactables'] = [{'id':'notice_board','label':'Notice board','type':'investigate'}]
    return session, scene, world


def test_duplicate_chat_records_once(tmp_path, monkeypatch):
    from tests.test_pr_play_62_investigation_quality import setup_session
    from fastapi.testclient import TestClient
    from game import api
    setup_session(tmp_path, monkeypatch)
    trace = tmp_path/'completed.jsonl'
    monkeypatch.setenv('ASHEN_PUBLICATION_TRACE_PATH', str(trace))
    with TestClient(api.app) as client:
        request = {'text':'I examine the notice board.', 'client_request_id':'79d-once'}
        first = client.post('/api/chat?ui_mode=player', json=request)
        after = copy.deepcopy(storage.load_session())
        second = client.post('/api/chat?ui_mode=player', json=request)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert after == storage.load_session()
    assert len(trace.read_text().splitlines()) == 1


def test_snapshot_restores_source_knowledge(tmp_path, monkeypatch):
    from tests.test_pr_play_62_investigation_quality import setup_session
    from fastapi.testclient import TestClient
    from game import api
    setup_session(tmp_path, monkeypatch)
    monkeypatch.setattr(storage, 'SNAPSHOTS_DIR', tmp_path/'snapshots')
    with TestClient(api.app) as client:
        first = client.post('/api/chat?ui_mode=player', json={'text':'I examine the notice board.'})
        assert first.status_code == 200
        known = copy.deepcopy(storage.load_session()['clue_knowledge'])
        snapshot = storage.create_snapshot('79d recall')
        session = storage.load_session()
        session['clue_knowledge'] = {}
        storage.save_session(session)
        storage.load_snapshot(snapshot['id'])
        assert storage.load_session()['clue_knowledge'] == known
        repeated = client.post('/api/chat?ui_mode=player', json={'text':'I examine the notice board again.'})
    assert 'northwest mud track past the crates' in repeated.json()['gm_output']['player_facing_text']
    assert storage.load_session()['clue_knowledge'] == known
