"""Synthetic SDK responses through real generation, parsing, validation and commit."""
import json
from pathlib import Path
from types import SimpleNamespace as NS

import openai
import pytest

import game.api as api
import game.gm as gm
from game import provider_budget as budget
from tests.helpers.live_model_guard import production_call_gpt
from tests.test_pr_play_04_opening_integrity import (
    opening_world, _start, _snap, _envelope, VALID_NARRATION,
)


@pytest.fixture
def diagnostic_world(opening_world, monkeypatch, tmp_path):
    for name, value in {
        '_REQUESTS': 0, '_RECORDS': [], '_EVENTS': [], '_ATTEMPTS': {},
        '_INPUT': 0, '_OUTPUT': 0, '_RESERVED_INPUT': 0, '_RESERVED_OUTPUT': 0,
        '_USAGE_KNOWN': True, '_STOPPED': False, '_STOP_REASON': '',
        '_INITIALIZED': False, '_LEDGER_PATH': None,
    }.items():
        monkeypatch.setattr(budget, name, value)
    monkeypatch.setenv('ASHEN_GENERATION_DIAGNOSTICS', '1')
    monkeypatch.setenv('ASHEN_PROVIDER_USAGE_PATH', str(tmp_path/'provider_usage.jsonl'))
    monkeypatch.setenv('ASHEN_PROVIDER_REQUEST_LIMIT', '6')
    for name in ['INPUT','OUTPUT','TOTAL']:
        monkeypatch.setenv('ASHEN_PROVIDER_'+name+'_TOKEN_LIMIT','1000000')
    return opening_world


@pytest.mark.parametrize('case,category,accepted', [
    ('D1','accepted_structured_response',True),
    ('D2','missing_structured_envelope',False),
    ('D3','json_parse_failure',False),
    ('D4','empty_provider_content',False),
    ('D5','accepted_structured_response',True),
    ('D6','json_parse_failure',False),
    ('D7','provider_error',False),
    ('D8','accepted_structured_response',True),
    ('D9','accepted_structured_response',True),
    ('D10','missing_structured_envelope',False),
    ('extraction','extraction_failure',False),
    ('validation','structured_validation_failure',False),
    ('placeholder','json_parse_failure',False),
])
def test_production_diagnostic_matrix(diagnostic_world, monkeypatch, case, category, accepted):
    calls = diagnostic_world['calls']
    text = _envelope(VALID_NARRATION)
    if case == 'D2': text = '{"ordinary": true}'
    if case == 'D3': text = '{broken'
    if case == 'D4': text = ''
    if case == 'D6': text = '{"declared_claims": [], "narration": "You stand'
    if case == 'D10': text = '{"ordinary": true}'
    if case == 'validation': text = '{"declared_claims": null, "narration": "You stand at the gate."}'
    if case == 'placeholder': text = '[Narration]'
    response = NS(output_text=text, model='offline-stub', id='synthetic-response',
                  usage=NS(input_tokens=20, output_tokens=10, total_tokens=30), status='completed')
    if case == 'D5':
        del response.output_text
        response.output = [NS(type='message',content=[NS(type='output_text',text=text)])]
    if case == 'D6':
        response.status='incomplete'
        response.incomplete_details=NS(reason='max_output_tokens')
        response.usage=NS(input_tokens=20,output_tokens=600,total_tokens=620)
    if case == 'D8': del response.usage
    if case == 'D9': del response.status
    if case == 'D10': response.usage=NS(input_tokens=20,output_tokens=600,total_tokens=620)
    if case == 'extraction':
        del response.output_text
        response.output=[NS(type='message',content=[NS(type='refusal',refusal='private sentinel')])]
    def create(**kwargs):
        calls.append({'keys': sorted(kwargs)})
        assert kwargs['max_output_tokens']==600
        assert 'text' not in kwargs  # No new provider response-format setting.
        if case == 'D7': raise RuntimeError('private provider exception sentinel')
        return response
    monkeypatch.setattr(openai,'OpenAI',lambda **_k: NS(responses=NS(create=create)))
    # Materialize initialization defaults before measuring gameplay persistence.
    import game.storage as storage
    storage.load_campaign()
    storage.load_character()
    storage.load_conditions()
    session=storage.load_session()
    api.snapshot_turn_start_interlocutor(session)
    api.synchronize_scene_addressability(session,storage.load_active_scene(),storage.load_world())
    storage.save_session(session)
    before = _snap()
    # Full persisted files, not merely the public projection.
    files_before = {p.relative_to(storage.DATA_DIR).as_posix():p.read_bytes()
                    for p in storage.DATA_DIR.rglob('*') if p.is_file()}
    body,status = _start()
    assert status == (200 if accepted else 422), body
    assert len(calls)==1
    assert budget.snapshot()['request_upper_bound']==1
    if accepted:
        assert body['gm_output']['player_facing_text']==VALID_NARRATION
        assert _snap()['campaign_started'] is True
        assert _snap()['turn_counter']==1 and _snap()['time_pressure']==1
        assert [r['agenda_progress'] for r in _snap()['factions']]==[1,1,1]
    else:
        assert body['gameplay_committed'] is False and body.get('gm_output') is None
        assert _snap()==before
        files_after = {p.relative_to(storage.DATA_DIR).as_posix():p.read_bytes()
                       for p in storage.DATA_DIR.rglob('*') if p.is_file()}
        # JSON serialization on rollback may change bytes, but values and file inventory must match.
        # Existing rollback creates an empty log if New Campaign removed it.
        assert set(files_after)-set(files_before) <= {'session_log.jsonl'}
        if 'session_log.jsonl' not in files_before:
            assert files_after.get('session_log.jsonl',b'')==b''
        for name in files_before:
            if name.endswith('.json'):
                after_value,before_value=json.loads(files_after[name]),json.loads(files_before[name])
                # Persistence envelope timestamps change when the existing rollback saves.
                after_value.pop('saved_at',None)
                before_value.pop('saved_at',None)
                if name=='session.json':
                    for value in [after_value,before_value]:
                        payload=value['payload']
                        payload.pop('last_saved_at',None)
                        traces=payload.pop('debug_traces',[])
                        assert all(t=={'kind':'state_mutation','domain':'scene_state',
                            'owner_module':'game.interaction_context','operation':'rebuild_active_scene_entities',
                            'changed_area':'scene_state.active_entities'} for t in traces)
                        value.pop('integrity',None)
                assert after_value==before_value, name
            else:
                assert files_after[name]==files_before[name], name
    events = budget.snapshot()['events']
    from tools.atgb.accounting import inspect_ledger
    reconciled=inspect_ledger(Path(__import__('os').environ['ASHEN_PROVIDER_USAGE_PATH']),budget.snapshot())
    assert reconciled['status']=='recorded'
    assert reconciled['request_upper_bound']==1
    diagnostic = next(r for r in events if r.get('stage')=='provider_response')
    outcome = next(r for r in events if r.get('stage')=='opening_outcome')
    assert diagnostic['classification']==category
    assert outcome['opening_accepted'] is accepted
    assert outcome['gameplay_committed'] is accepted
    assert diagnostic['opening_attempt_id']==outcome['opening_attempt_id']
    assert outcome['classification']==('accepted_structured_opening' if accepted else 'opening_rejected')
    if case == 'D2': assert diagnostic['json_parsing_succeeded'] and not diagnostic['expected_envelope_present']
    if case in {'D3','D6'}: assert diagnostic['json_parsing_succeeded'] is False
    if case == 'D6': assert diagnostic['provider_output_limit_exhausted'] is True
    if case == 'D8': assert all(diagnostic[k] is None for k in ['input_tokens','output_tokens','total_tokens'])
    if case == 'D9': assert diagnostic['provider_status'] is None and diagnostic['provider_finish_reason'] is None
    if case == 'D10':
        assert diagnostic['output_limit_reached'] is True
        assert diagnostic['possible_output_truncation'] is True
        assert diagnostic['provider_output_limit_exhausted'] is None
        assert diagnostic['classification']=='missing_structured_envelope'
    if case == 'D5': assert diagnostic['extraction_source']=='output_message_content' and diagnostic['content_segment_count']==1
    raw = Path(__import__('os').environ['ASHEN_PROVIDER_USAGE_PATH']).read_text()
    assert 'private sentinel' not in raw and 'private provider exception sentinel' not in raw
    assert VALID_NARRATION not in raw
    # Retain only structural evidence with a stable location for the review package.
    dest=Path('artifacts/pr_play_05/diagnostics')
    dest.mkdir(parents=True,exist_ok=True)
    (dest/(case+'.json')).write_text(json.dumps({'status':status,'events':events,'before':before,'after':_snap()},indent=2))


def test_diagnostics_disabled_has_no_events(diagnostic_world, monkeypatch):
    monkeypatch.delenv('ASHEN_GENERATION_DIAGNOSTICS')
    assert _start()[1]==200
    assert not any(r.get('event')=='generation_diagnostic' for r in budget.snapshot()['events'])


def test_invalid_placeholder_over_http(diagnostic_world):
    from fastapi.testclient import TestClient
    diagnostic_world['state']['text']='[Narration]'
    before=_snap()
    with TestClient(api.app) as client:
        response=client.post('/api/start_campaign')
    assert response.status_code==422
    assert response.json()['gameplay_committed'] is False
    assert _snap()==before
    assert len(diagnostic_world['calls'])==1
    Path('artifacts/pr_play_05/placeholder_http.json').write_text(json.dumps({
        'status':response.status_code,'body':response.json(),'before':before,'after':_snap(),
        'events':budget.snapshot()['events']},indent=2))


def test_sdk_extraction_does_not_stringify_objects():
    class Unusable:
        def __str__(self): raise AssertionError('SDK repr must not reach parser')
    assert gm._extract_provider_response_text(Unusable())[0]==''


def test_native_sdk_content_segments_and_request_identity():
    from openai.types.responses import Response, ResponseOutputMessage, ResponseOutputText
    message=ResponseOutputMessage.model_construct(type='message',role='assistant',status='completed',id='msg_stub',
        content=[ResponseOutputText(type='output_text',text='{"declared_claims":[],',annotations=[]),
                 ResponseOutputText(type='output_text',text='"narration":"You stand at the gate."}',annotations=[])])
    response=Response.model_construct(id='resp_stub',model='offline-stub',status='completed',output=[message],usage=None)
    response._request_id='req_stub'
    text,details=gm._extract_provider_response_text(response)
    assert details['content_segment_count']==2
    parsed=gm._safe_json(text,require_structured_claims=True)
    diag=gm._generation_response_diagnostic(response,text,details,parsed,maximum=600,contract='structured_realization')
    assert diag['structured_validation_result'] is True
    assert diag['provider_request_id']=='req_stub' and diag['provider_response_id']=='resp_stub'


@pytest.mark.parametrize('scenario', ['repeat','retry','concurrent','budget'])
def test_existing_integrity_controls_with_diagnostics(diagnostic_world,monkeypatch,tmp_path,scenario):
    from tests import test_pr_play_04_opening_integrity as original
    controls={
        'repeat':lambda:original.test_valid_opening_commits_once_and_repeat_does_not(diagnostic_world),
        'retry':lambda:original.test_failure_then_failure_then_success_commits_once(diagnostic_world),
        'concurrent':lambda:original.test_concurrent_starts_commit_one_opening(diagnostic_world,monkeypatch),
        'budget':lambda:original.test_budget_rejection_is_before_dispatch(diagnostic_world,monkeypatch,tmp_path),
    }
    controls[scenario]()
    events=budget.snapshot()['events']
    outcomes=[r for r in events if r.get('stage')=='opening_outcome']
    if scenario=='budget':
        assert any(r.get('classification')=='provider_budget_refused' for r in events)
        assert budget.snapshot()['request_upper_bound']==0
    else:
        assert sum(r['gameplay_committed'] for r in outcomes)==1
        assert len(diagnostic_world['calls'])==(3 if scenario=='retry' else 1)
        if scenario=='repeat':
            assert outcomes[-1]['rejection_reason']=='already_started'
        if scenario=='retry':
            assert [r['gameplay_committed'] for r in outcomes]==[False,False,True]
    dest=Path('artifacts/pr_play_05/diagnostics')
    dest.mkdir(parents=True,exist_ok=True)
    (dest/(scenario+'.json')).write_text(json.dumps({'events':events,'after':_snap()},indent=2))
