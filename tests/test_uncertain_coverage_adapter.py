"""Exercise the real prompt, parser and adapter with a transport-free response stub."""
import copy
import json
import pytest
from fastapi.testclient import TestClient
from game import api, storage, live_chat_interpretation as live
from tests.test_uncertain_coverage_interpretation_boundary import setup, A4, B1, record, state, assert_integrity, evidence

@pytest.mark.parametrize('case',['A4','B1','invalid_json','invalid_schema','fabricated_id','budget','timeout','missing_context','context_leak'])
def test_real_adapter(setup,monkeypatch,case):
    text=B1 if case in {'B1','fabricated_id'} else A4
    payload=record(text==B1)
    payload.pop('incidental_context')
    payload.update(asserted_premises=[],requested_outcomes=[],references={'permitted_entity_ids':['guard_captain'] if text==B1 else [],'unresolved_references':[]},clarification_question='',correction={'subject':'NONE','note':''})
    for c in payload['action_components']:c['order']=1
    if case=='fabricated_id':
        payload['references']['permitted_entity_ids']=['invented_officer'];payload['action_components'][0]['target_ref']='invented_officer'
    raw='{' if case=='invalid_json' else '{}' if case=='invalid_schema' else json.dumps(payload)
    messages=[]
    def response(msg,**kw):
        messages.append(copy.deepcopy(msg))
        if case in {'budget','timeout'}:return {'ok':False,'sent':False,'reason':'request ceiling' if case=='budget' else 'provider_failure','error':'TimeoutError' if case=='timeout' else 'budget refused'}
        return {'ok':True,'sent':False,'text':raw}
    monkeypatch.setattr(live,'production_live_interpretation_enabled',lambda:True)
    monkeypatch.setattr(live,'request_interpretation',response)
    if case=='context_leak':
        contract=list(live._contract());contract[2]=lambda *a:['CANARY_GM_NOTE'];monkeypatch.setattr(live,'_CONTRACT',tuple(contract))
    if case=='missing_context':
        # An empty authoritative prepared list cannot be filled by model text.
        ch=storage.load_character();ch.pop('spells',None);storage.save_character(ch)
    before=state()
    with TestClient(api.app) as c:r=c.post('/api/chat?ui_mode=player',json={'text':text,'client_request_id':case})
    assert r.status_code==200;assert_integrity(before,state())
    d=storage.load_log()[-1]['resolution']['metadata']['conversational_decision']
    visible=r.json()['gm_output']['player_facing_text']
    assert d['authorization']['coverage']['classification']=='UNCERTAIN'
    if case=='A4':assert 'has these spells prepared' in visible and 'hypothetical' in visible
    elif case=='missing_context':assert 'does not list any prepared spells' in visible
    else:assert d['category']=='CLARIFY'
    if messages:
        assert text in json.dumps(messages)
        assert 'Host coverage restriction:' in messages[0][1]['content']
        assert 'unrecognized_agentive_predicate' in messages[0][1]['content']
    else:assert case=='context_leak'
    evidence('adapter_'+case,{'request':text,'stub_raw':raw,'prompt_messages':messages,'decision':d,'response':r.json(),'integrity':True,'live_provider_calls':0})
