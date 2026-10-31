"""Real host path with synthetic SDK output; no live-generation reliability claim."""
import json
from types import SimpleNamespace as NS

import openai
import pytest

import game.gm as gm
from game import provider_budget as budget
from tests.test_pr_play_04_opening_integrity import opening_world, _start, _snap, _envelope, VALID_NARRATION
from tests.test_pr_play_05_diagnostics import diagnostic_world
from tools.measure_pr_play_06 import opening_fixture, measure, size, write


@pytest.mark.parametrize('name', ['minimal','typical','rich','multiple_details','npc','declarations','over_600'])
def test_opening_fixtures(diagnostic_world, monkeypatch, name):
    import game.storage as storage
    if name == 'minimal':
        session = storage.load_session()
        session['active_scene_id'] = 'market_quarter'
        storage.save_session(session)
    captured = {}
    def create(**kwargs):
        captured.update(kwargs)
        payload = json.loads(kwargs['input'][-1]['content'])
        text = opening_fixture(name, payload)
        captured['fixture'] = text
        # Size is explicitly estimated, not fabricated provider tokenizer evidence.
        synthetic_usage = size(text)['estimated_tokens_chars_div_4']
        return NS(output_text=text, status='completed', model='offline-stub',
                  usage=NS(input_tokens=20, output_tokens=synthetic_usage, total_tokens=20+synthetic_usage))
    monkeypatch.setattr(openai, 'OpenAI', lambda **kw: NS(responses=NS(create=create)))
    before = _snap()
    body, status = _start()
    text = captured.pop('fixture')
    measurement = measure(name, text)
    write('measurements/'+name+'.json', {**measurement,'host_status':status,
          'before':before,'after':_snap(),'failure':body.get('opening_failure_reason'),
          'provider_usage_is_synthetic_estimate':True,'events':budget.snapshot()['events']})
    write('requests/'+name+'.json', captured)
    assert measurement['parser_valid']
    assert status == 200, body.get('opening_failure_reason')
    assert captured['max_output_tokens'] == 3000
    assert _snap()['turn_counter'] == 1
    assert len([r for r in budget.snapshot()['events'] if r.get('event')=='dispatch_attempted']) == 1
    if name == 'declarations': assert measurement['declaration_count'] > 0
    if name == 'over_600':
        assert 600 < measurement['serialized_output']['estimated_tokens_chars_div_4'] < 3000


@pytest.mark.parametrize('reason', ['max_output_tokens','content_filter'])
def test_complete_json_with_incomplete_provider_status_rejected(diagnostic_world, monkeypatch, reason):
    def create(**kwargs):
        return NS(output_text=_envelope(VALID_NARRATION), status='incomplete',
                  incomplete_details=NS(reason=reason), model='offline-stub',
                  usage=NS(input_tokens=20, output_tokens=kwargs['max_output_tokens'],
                           total_tokens=20+kwargs['max_output_tokens']))
    monkeypatch.setattr(openai, 'OpenAI', lambda **kw: NS(responses=NS(create=create)))
    before = _snap()
    body,status = _start()
    write('incomplete_'+reason+'.json', {'status':status, 'before':before, 'after':_snap(),
          'events':budget.snapshot()['events']})
    assert status == 422
    assert _snap() == before
    diagnostic = next(r for r in budget.snapshot()['events'] if r.get('stage')=='provider_response')
    assert diagnostic['classification'] == 'provider_not_completed'
    assert diagnostic['json_parsing_succeeded'] and diagnostic['structured_validation_result']


def test_aggregate_output_refusal_before_dispatch(diagnostic_world, monkeypatch):
    monkeypatch.setenv('ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT', '1000')
    before = _snap()
    body,status = _start()
    assert status == 409
    assert not diagnostic_world['calls']
    assert _snap() == before
    assert budget.snapshot()['request_upper_bound'] == 0
    write('aggregate_refusal.json', {'status':status,'before':before,'after':_snap(),
          'events':budget.snapshot()['events']})


@pytest.mark.parametrize('accounting', [True, False])
@pytest.mark.parametrize('opening', [True, False])
def test_budget_selection_and_ordinary_compatibility(diagnostic_world, monkeypatch, accounting, opening):
    from tests.helpers.live_model_guard import production_call_gpt
    if not accounting:
        monkeypatch.delenv('ASHEN_PROVIDER_REQUEST_LIMIT')
        monkeypatch.delenv('ASHEN_PROVIDER_USAGE_PATH')
    captured = {}
    def create(**kwargs):
        captured.update(kwargs)
        return NS(output_text=_envelope(VALID_NARRATION), status='completed')
    monkeypatch.setattr(openai, 'OpenAI', lambda **kw: NS(responses=NS(create=create)))
    monkeypatch.setenv('ASHEN_OPENING_MAX_OUTPUT_TOKENS','2800')
    messages = [{'role':'user','content':json.dumps({'response_type_contract':{
        'required_response_type':'scene_opening' if opening else 'answer'}})}]
    production_call_gpt()(messages)
    assert captured.get('max_output_tokens') == (2800 if opening else 600 if accounting else None)


@pytest.mark.parametrize('value', ['0','4097','-1','invalid'])
def test_opening_configuration_is_bounded(monkeypatch, value):
    monkeypatch.setenv('ASHEN_OPENING_MAX_OUTPUT_TOKENS',value)
    with pytest.raises(ValueError): gm._opening_max_output_tokens()


def test_historical_rich_fixture_still_rejected(diagnostic_world):
    from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
    text = _envelope(RICH_OPENING_GPT_RESPONSE['player_facing_text'])
    diagnostic_world['state']['text'] = text
    before = _snap()
    body,status = _start()
    write('historical_rich_rejection.json', {**measure('historical_rich',text),
          'status':status,'before':before,'after':_snap()})
    assert status == 422 and _snap() == before
