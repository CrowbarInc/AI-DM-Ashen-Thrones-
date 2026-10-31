"""PR-PLAY-07 synthetic opening semantics and optional evidence, no providers."""
import json
from pathlib import Path
import pytest
import game.api as api
from game import provider_budget as budget
from tests.test_pr_play_04_opening_integrity import opening_world, _start, _snap, _envelope, VALID_NARRATION
from tests.test_pr_play_05_diagnostics import diagnostic_world

OUT=Path('artifacts/pr_play_07/matrix')

@pytest.mark.parametrize('case,accepted', [('S1',True),('S2',False),('S3',False),('S4',False),('S5',True),('S6',True),('S7',True),('S8',True),('S9',False),('S10',True),('S11',True),('S12',False)])
def test_semantic_matrix(diagnostic_world,monkeypatch,case,accepted):
    from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
    import game.gm as gm
    text=_envelope(VALID_NARRATION)
    if case=='S2': text=_envelope('No one here can answer that from what is settled here.')
    if case=='S3': text=_envelope('')
    if case=='S4': text=json.dumps({'narration': VALID_NARRATION})
    if case=='S6': text=json.dumps({'declared_claims':[], 'narration':VALID_NARRATION, 'metadata':{'fallback':True}})
    if case=='S7':
        from game.response_type_gating import derive_response_type_contract
        routed=derive_response_type_contract(segmented_turn=None, normalized_action={'type':'scene_opening'},resolution={'kind':'scene_opening'},interaction_context=None,raw_player_text='What is here?')
        assert routed.required_response_type=='scene_opening'
    if case=='S9': text=_envelope(VALID_NARRATION+' The guards give you a brass key and you gain 100 gold.')
    if case=='S12': text=_envelope(RICH_OPENING_GPT_RESPONSE['player_facing_text'])
    diagnostic_world['state']['text']=text
    if case=='S11':
        diagnostic_world['state']['text']=_envelope('No one here can answer that from what is settled here.')
        before=_snap();failed,code=_start()
        assert code==422 and _snap()==before
        diagnostic_world['state']['text']=text
    before=_snap();body,status=_start();after=_snap()
    assert status==(200 if accepted else 422),body
    assert after['turn_counter']==before['turn_counter']+(1 if accepted else 0)
    if not accepted: assert after==before
    if case=='S10':
        again,code=_start();assert code==409 and _snap()==after
    events=budget.snapshot()['events']
    provider=[r for r in events if r.get('stage')=='provider_response'][-1]
    outcome=[r for r in events if r.get('stage')=='opening_outcome' and r.get('opening_attempt_id')==provider['opening_attempt_id']][-1]
    assert outcome['gameplay_committed'] is accepted
    assert outcome['provider_attempt_id']==provider['attempt_id']
    assert outcome['structured_validation_result']==provider['structured_validation_result']
    if case=='S12':
        assert provider['classification']=='accepted_structured_response'
        assert body['opening_failure_reason']=='safe_nonresolution'
        assert outcome['semantic_reasons'] and outcome['classification_source'].endswith('._finish')
    expected_calls=2 if case=='S11' else 1
    assert len(diagnostic_world['calls'])==expected_calls
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/(case+'.json')).write_text(json.dumps({'fixture':json.loads(text),'expected_accepted':accepted,'status':status,'before':before,'after':after,'provider':provider,'outcome':outcome,'events':events,'pass':True},indent=2),encoding='utf-8')

@pytest.mark.parametrize('mode',['default','enabled','write_failure','oversize'])
def test_bounded_capture(diagnostic_world,monkeypatch,tmp_path,mode):
    import game.storage as storage
    monkeypatch.setenv('ASHEN_DATA_DIR',str(storage.DATA_DIR))
    monkeypatch.delenv('ASHEN_OPENING_RESPONSE_CAPTURE',raising=False)
    if mode!='default':monkeypatch.setenv('ASHEN_OPENING_RESPONSE_CAPTURE','1')
    folder=storage.DATA_DIR.parent/'opening_response_evidence'
    if mode=='write_failure':folder.write_text('blocked directory')
    if mode=='oversize':
        value=json.loads(diagnostic_world['state']['text']);value['debug_notes']='x'*100000
        diagnostic_world['state']['text']=json.dumps(value)
    body,status=_start()
    assert status==200 and _snap()['turn_counter']==1 and len(diagnostic_world['calls'])==1
    records=list(folder.glob('*.json')) if folder.is_dir() else []
    if mode in {'enabled','oversize'}:
        assert len(records)==1 and records[0].stat().st_size<=65536
        value=json.loads(records[0].read_text())
        assert value['sensitive_game_content'] and value['truncated']==(mode=='oversize')
        if mode=='enabled': assert value['parsed_response']==json.loads(diagnostic_world['state']['text'])
    else:assert not records
    if mode=='write_failure':assert any(r.get('classification')=='capture_failed' for r in budget.snapshot()['events'])
    ledger=Path(__import__('os').environ['ASHEN_PROVIDER_USAGE_PATH'])
    assert VALID_NARRATION not in ledger.read_text()
    from tools.atgb.accounting import inspect_ledger
    assert inspect_ledger(ledger,budget.snapshot())['status']=='recorded'


def test_authoritative_safe_metadata_remains_disqualifying():
    assert api._opening_response_rejection({'player_facing_text':VALID_NARRATION,'metadata':{'accepted_response':{'provenance':'safe_nonresolution'}}},{'kind':'scene_opening'},None)=='safe_nonresolution'


@pytest.mark.parametrize('gate',['diagnostics','sdk_retry','host_retry','data'])
def test_capture_requires_controlled_scope(diagnostic_world,monkeypatch,gate):
    import game.storage as storage
    monkeypatch.setenv('ASHEN_DATA_DIR',str(storage.DATA_DIR))
    monkeypatch.setenv('ASHEN_OPENING_RESPONSE_CAPTURE','1')
    if gate=='diagnostics':monkeypatch.delenv('ASHEN_GENERATION_DIAGNOSTICS')
    if gate=='sdk_retry':monkeypatch.delenv('ASHEN_PLAYTEST_DISABLE_SDK_RETRIES')
    if gate=='host_retry':monkeypatch.delenv('ASHEN_DISABLE_PROVIDER_RETRIES')
    if gate=='data':monkeypatch.delenv('ASHEN_DATA_DIR')
    # Exercise evidence collection directly so removing retry guards cannot dispatch.
    token=budget.begin_opening_diagnostic()
    try:budget.capture_opening_response(_envelope(VALID_NARRATION))
    finally:
        if token is not None:budget._OPENING_DIAGNOSTIC.reset(token)
    assert not (storage.DATA_DIR.parent/'opening_response_evidence').exists()

def test_optional_diagnostic_ledger_failure_does_not_reject_valid_opening(diagnostic_world,monkeypatch):
    append=budget._append
    def fail_observation(row):
        if row.get('event')=='generation_diagnostic':raise OSError('synthetic evidence write failure')
        return append(row)
    monkeypatch.setattr(budget,'_append',fail_observation)
    body,status=_start()
    assert status==200 and _snap()['turn_counter']==1 and len(diagnostic_world['calls'])==1


def test_capture_count_is_bounded(diagnostic_world,monkeypatch):
    import game.storage as storage
    monkeypatch.setenv('ASHEN_DATA_DIR',str(storage.DATA_DIR))
    monkeypatch.setenv('ASHEN_OPENING_RESPONSE_CAPTURE','1')
    token=budget.begin_opening_diagnostic()
    try:
        for _ in range(7):budget.capture_opening_response(_envelope(VALID_NARRATION))
    finally:budget._OPENING_DIAGNOSTIC.reset(token)
    files=list((storage.DATA_DIR.parent/'opening_response_evidence').glob('*.json'))
    assert len(files)==6 and all(p.stat().st_size<=65536 for p in files)
    assert budget.snapshot()['request_upper_bound']==0
