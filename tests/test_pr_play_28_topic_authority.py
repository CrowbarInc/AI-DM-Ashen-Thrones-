"""PR-PLAY-28 deterministic topic discovery, authority and real HTTP integration."""
import copy,json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from game import api,storage as st
from game.social import _next_topic_to_reveal
from game.dialogue_authority import authorize_npc_disclosure
from tools.playtest import gameplay as g
from tools.playtest.overlays import compare_overlays
from tests.test_five_turn_gameplay import action
from tests.test_pr_play_04_opening_integrity import opening_world
from tests.test_pr_play_25_public_fact_dialogue import _transport,plan_selecting_required,_enable_live,_install_interpretation,raw_captured,TEXT,state
E=Path('artifacts/pr_play_28')

@pytest.mark.parametrize('restricted,followup',[(False,'What sort of rumors have you heard?'),(False,'What have you heard about the patrol?'),(True,'What sort of rumors have you heard?')])
def test_integration(opening_world,monkeypatch,restricted,followup):
    candidate="I've got hot stew and rumors to share."
    monkeypatch.setenv('ASHEN_OPENING_RENDERER','1')
    _transport(monkeypatch,[],lambda kw: plan_selecting_required(kw['input']))
    # Restore the established PR-PLAY-26 campaign fact/topic fixtures.
    root=Path('artifacts/pr_play_26/live/baseline/persistent')
    scene=st.load_active_scene(); captured=json.loads((root/'scenes/frontier_gate.json').read_text())
    scene['scene']['visible_facts']=captured['scene']['visible_facts']; st._save_json(st.scene_path(scene['scene']['id']),scene)
    world=st.load_world(); original=json.loads((root/'world.json').read_text())
    runner=next(n for n in world['npcs'] if n['id']=='tavern_runner')
    runner['topics']=next(n for n in original['npcs'] if n['id']=='tavern_runner')['topics']
    configured=json.loads(Path('data/validation/atgb/baselines/frontier-gate-v1/world.json').read_text())
    authored=next(n for n in configured['npcs'] if n['id']=='tavern_runner')['topics'][0]
    assert authored['text']==runner['topics'][0]['text']
    assert authored['clue_id']==runner['topics'][0]['clue_id']
    runner['topics'][0]['discovery_categories']=authored['discovery_categories']
    if restricted: runner['topics'][0]['disclosure']='requires_quest'
    st.save_world(world)
    rows=[]; expressions=[]; calls=[]
    with TestClient(api.app) as client:
        opening=client.post('/api/start_campaign?ui_mode=player')
        assert opening.status_code==200
        _enable_live(monkeypatch); monkeypatch.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION','0')
        monkeypatch.setattr(api,'call_gpt',lambda *a,**kw: pytest.fail('unexpected narration call'))
        monkeypatch.setattr('game.expressive_dialogue.request_expression',lambda c: expressions.append(c) or dict(ok=True,sent=True,text=candidate,usage={},latency_ms=0))
        record=raw_captured(); _install_interpretation(monkeypatch,record,calls)
        for index,text in enumerate([TEXT,followup]):
            if index:
                record=raw_captured(); record['action_components']=record['action_components'][1:]
                record['action_components'][0]['description']=text
                record['communication']['subject']='rumors'; record['communication']['evidence_refs']=[]
                record['player_intent']['summary']=text; record['requested_outcomes']=[{'text':text}]
                _install_interpretation(monkeypatch,record,calls)
            before=state(); before_logs=st.load_log(); reply=client.post('/api/chat?ui_mode=player',json={'text':text}); after=state(); after_logs=st.load_log(); internal=after_logs[-1]
            classification=g.classify_turn(reply.status_code,internal)
            a=action(); a['requires_substantive_answer']=True
            a['player_input']=text; a['subject_terms']=['rumors','stew','patrol']
            def docs(snapshot): return {'scenes/frontier_gate.json':copy.deepcopy(scene), **{key+'.json':value for key,value in snapshot.items()}, 'session_log.jsonl':before_logs if snapshot is before else after_logs}
            evaluation=g.evaluate(a,reply.status_code,internal,docs(before),docs(after),[])
            public_evaluation=g.evaluate(a,reply.status_code,reply.json(),docs(before),docs(after),[])
            if not (restricted and index): assert not public_evaluation['stop'],public_evaluation['findings']
            classification=evaluation['completion']
            from game.social import broad_topic_discovery_category,topic_discoverable_in_category
            person=next(n for n in before['world']['npcs'] if n['id']=='tavern_runner')
            category=broad_topic_discovery_category(text)
            diagnostics=[dict(id=t['id'],category=category,discoverable=bool(category and topic_discoverable_in_category(person,t,category)),disclosure=authorize_npc_disclosure(person,t)) for t in person['topics']]
            rows.append(dict(topic_eligibility=diagnostics,authored_scene=copy.deepcopy(scene),public_evaluation=public_evaluation,player=text,response=reply.json(),internal=internal,before=before,after=after,classification=classification,evaluation=evaluation))
            for key in ('character','campaign','combat','conditions'): assert before[key]==after[key]
            from game.world import advance_world_tick
            expected=copy.deepcopy(before['world']); advance_world_tick(expected,before['campaign'])
            if index and not restricted:
                # Authored disclosure records clue events; the expression cannot
                # alter any other world field or invent an extra clue.
                actual=copy.deepcopy(after['world'])
                events=actual.pop('event_log'); prior_events=expected.pop('event_log')
                assert events[:len(prior_events)]==prior_events
                additions=events[len(prior_events):]
                assert len(additions)==2 and {e.get('type') for e in additions}=={'social_lead_revealed','social_extracted_lead'}
                assert {e.get('clue_id') for e in additions}=={'muddy_footprints_northwest','lead_frontier_gate_old_trading_crossroads'}
                assert actual==expected
            else:
                assert after['world']==expected
    evidence=dict(opening=opening.json(),turns=rows,live_provider_requests=0)
    (E/('integration_'+('restricted' if restricted else 'explicit' if 'patrol' in followup else 'broad')+'.json')).write_text(json.dumps(evidence,indent=2,default=str))
    assert all(r['internal']['resolution']['social']['npc_id']=='tavern_runner' for r in rows)
    assert not rows[0]['evaluation']['stop']
    assert rows[0]['internal']['resolution']['social']['dialogue_authority']['public_fact_source']
    second=rows[1]
    if restricted:
        assert second['internal']['resolution']['social']['topic_revealed'] is None
        assert second['before']['session']['runtime_scene_overlays']==second['after']['session']['runtime_scene_overlays']
        assert "couldn't tell you" in second['response']['gm_output']['player_facing_text']
    else:
        assert second['internal']['resolution']['social']['topic_revealed']['id']=='patrol_rumor'
        assert not second['evaluation']['stop'],second['evaluation']['findings']
        assert second['evaluation']['overlay_comparison']['integrity']


def npc(topics=None,ident='seller'):
    return dict(id=ident,name='Seller',location='square',topics=topics if topics is not None else [dict(id='patrol_rumor',text='I heard the patrol went north.',clue_id='trail',discovery_categories=['rumor'])])

@pytest.mark.parametrize('question',["What sort of rumors have you heard?","Have you heard any rumors?","What's the latest gossip?","Any rumors?","What rumors have you heard?","What have you heard about the patrol?"])
def test_inquiry(question):
    n=npc();result=_next_topic_to_reveal(n,{},player_text=question)
    assert result and result['id']=='patrol_rumor'
    assert authorize_npc_disclosure(n,result)['permission']

@pytest.mark.parametrize('patch',[dict(disclosure='secret'),dict(hidden=True),dict(secret=True),dict(disclosure='requires_quest'),dict(disclosure='requires_relationship'),dict(knowledge_status='unknown'),dict(known=False)])
def test_restricted(patch):
    n=npc();n['topics'][0].update(patch)
    assert _next_topic_to_reveal(n,{},player_text='Any rumors?') is None

@pytest.mark.parametrize('topics',[[],[dict(id='prices',text='I sell bread.')],[dict(id='rumor_secret',text='I heard a rumor.')],[dict(id='patrol_rumor',text='I heard a rumor.',discovery_categories='rumor')]])
def test_no_discoverable_category(topics):
    assert _next_topic_to_reveal(npc(topics),{},player_text='What rumors have you heard?') is None

@pytest.mark.parametrize('question',["Any rumors about the merchant?","What news have you heard?","Anything interesting happening around here?"])
def test_distinct_requests(question):
    assert _next_topic_to_reveal(npc(),{},player_text=question) is None

@pytest.mark.parametrize('reverse',[False,True])
def test_multiple_and_other_npc(reverse):
    rows=[dict(id=i,text='I heard a rumor about '+i,discovery_categories=['rumor']) for i in ['z','a','hidden']]
    rows[-1]['hidden']=True
    n=npc(list(reversed(rows)) if reverse else rows,ident='ferryman');selection={}
    r=_next_topic_to_reveal(n,{},player_text="What's the latest gossip?",selection=selection)
    assert r['id']=='a'
    assert selection['selected_source']=='npc:ferryman:a'
    assert len(selection['candidate_sources'])==2


def saved_turn():
    data=json.loads((E/'two_turn_accepted_explicit.json').read_text());row=data['turns'][1]
    def docs(snapshot):
        d={k+'.json':v for k,v in snapshot.items()}
        d['scenes/frontier_gate.json']=copy.deepcopy(row['authored_scene'])
        d['session_log.jsonl']=[data['turns'][0]['internal']]
        if snapshot is row['after']: d['session_log.jsonl'].append(row['internal'])
        return d
    a=action();a['player_input']=row['player']
    return docs(row['before']),docs(row['after']),a,row['internal']

@pytest.mark.parametrize('corruption',['none','action','topic_policy','unsupported_clue','wrong_npc','source_missing','event','unrelated_overlay','lifecycle','missing_log','response_id','denied_grant','invented_hook','unrelated_inventory','missing_action_id','missing_topic_grant','missing_action','malformed_counter'])
def test_authority_controls(corruption):
    before,after,a,response=saved_turn()
    if corruption=='missing_action_id':after['session_log.jsonl'][-1]['resolution'].pop('action_id')
    if corruption=='missing_topic_grant':after['session_log.jsonl'][-1]['resolution']['social']['topic_revealed'].pop('disclosure_authorization')
    if corruption=='missing_action':a.pop('player_input')
    if corruption=='malformed_counter':before['session.json']['turn_counter']='bad'
    if corruption=='action':a['player_input']='A different action.'
    if corruption=='topic_policy':next(n for n in before['world.json']['npcs'] if n['id']=='tavern_runner')['topics'][0]['disclosure']='restricted'
    if corruption=='unsupported_clue':after['session_log.jsonl'][-1]['resolution']['clue_id']='unsupported'
    if corruption=='wrong_npc':after['session_log.jsonl'][-1]['resolution']['social']['npc_id']='guard_captain'
    if corruption=='source_missing':del before['scenes/frontier_gate.json']
    if corruption=='event':after['world.json']['event_log'][-1]['clue_id']='unsupported'
    if corruption=='unrelated_overlay':after['session.json']['runtime_scene_overlays']['frontier_gate']['visible_facts_add'].append('Invented fact')
    if corruption=='lifecycle':before['session.json']['campaign_started']=False
    if corruption=='missing_log':after['session_log.jsonl']=[]
    if corruption=='denied_grant':after['session_log.jsonl'][-1]['resolution']['social']['topic_revealed']['disclosure_authorization']['permission']=False
    if corruption=='invented_hook':after['session_log.jsonl'][-1]['resolution']['social']['topic_revealed']['leads_to_scene']='secret_place'
    if corruption=='unrelated_inventory':
        after['character.json']['inventory']=['Invented item']
        result=g.evaluate(a,200,response,before,after,[])
        assert any(f['category']=='unauthorized_state_mutation' for f in result['findings'])
        return
    if corruption=='response_id':response=copy.deepcopy(response);response['resolution']['action_id']='unbound'
    result=compare_overlays(before,after,ordinary_action=a,turn_response=response)
    assert result['integrity'] is (corruption=='none'),result


def test_unchanged_ordinary_overlay():
    before,after,a,response=saved_turn()
    after['session.json']['runtime_scene_overlays']=copy.deepcopy(before['session.json']['runtime_scene_overlays'])
    assert compare_overlays(before,after)['integrity']

