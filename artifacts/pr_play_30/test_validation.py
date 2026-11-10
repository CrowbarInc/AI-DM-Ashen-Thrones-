"""PR-PLAY-30 observation harness. All provider surfaces are mocked; no repairs."""
import copy
import json
import shutil
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from game import api, storage as st
from tests.test_pr_play_04_opening_integrity import opening_world
from tests.test_pr_play_25_public_fact_dialogue import _transport, plan_selecting_required, _enable_live, _install_interpretation, state
from tools.atgb.baseline import load_baseline
from tools.playtest import gameplay as g
from tests.test_five_turn_gameplay import action

OUT=Path(__file__).parent
def save(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,default=str),encoding='utf-8')

def captured(n):
    p=Path('artifacts/atgb/pr_play_29/live/diagnostics')/f'response_{n:02}.json'
    d=json.loads(p.read_text())['response']
    return json.loads(next(c['text'] for o in d['output'] for c in o.get('content',[]) if c.get('type')=='output_text'))

def test_conversation_to_investigation(opening_world,monkeypatch):
    started=time.perf_counter()
    root,manifest=load_baseline(Path.cwd())
    for name in manifest['files']:
        dest=st.DATA_DIR/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/name,dest)
    monkeypatch.setenv('ASHEN_OPENING_RENDERER','1')
    opening_calls=[]
    _transport(monkeypatch,opening_calls,lambda kw:plan_selecting_required(kw['input']))
    rows=[];calls=[];expressions=[];traces=[]
    import game.exploration as ex
    original=ex.resolve_exploration_action
    def observe(*a,**kw):
        result=original(*a,**kw)
        traces.append(dict(args=copy.deepcopy(a),kwargs=copy.deepcopy(kw),result=copy.deepcopy(result)))
        return result
    monkeypatch.setattr(ex,'resolve_exploration_action',observe)
    if hasattr(api,'resolve_exploration_action'):monkeypatch.setattr(api,'resolve_exploration_action',observe)
    with TestClient(api.app) as client:
        initial=state()
        t=time.perf_counter();reply=client.post('/api/start_campaign?ui_mode=player')
        save('opening.json',dict(status=reply.status_code,response=reply.json(),before=initial,after=state(),mock_requests=opening_calls,latency_seconds=time.perf_counter()-t))
        assert reply.status_code==200
        _enable_live(monkeypatch)
        monkeypatch.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION','0')
        monkeypatch.setattr(api,'call_gpt',lambda *a,**kw:pytest.fail('unexpected narration provider call'))
        def expression(c):
            expressions.append(c)
            return dict(ok=True,sent=True,text="I've got hot stew and rumors to share.",usage={},latency_ms=0)
        monkeypatch.setattr('game.expressive_dialogue.request_expression',expression)
        texts=["I approach the tavern runner and ask what they're offering.",'What sort of rumors have you heard?', 'I head northwest of the crates to investigate the muddy footprints.']
        for i,text in enumerate(texts,1):
            if i<3:record=captured(2 if i==1 else 4)
            else:
                # Conservative deterministic interpretation: preserve both attempted actions,
                # and do not invent ids for the unrepresented local area or remote evidence.
                record=dict(communication=dict(recipient='CHARACTER',purpose='ACTION',subject='Investigate the muddy footprints learned from the runner',evidence_refs=[]),communication_mode='IN_WORLD_ACTION',interpretation_status='INTERPRETED',player_intent=dict(summary=text),asserted_premises=[],requested_outcomes=[dict(text='Examine the muddy footprints')],action_components=[dict(order=1,description='Head northwest of the crates',target_ref=None,operation_class='MOVE'),dict(order=2,description='Investigate the muddy footprints',target_ref=None,operation_class='INSPECT')],references=dict(permitted_entity_ids=[],unresolved_references=['northwest of the crates','muddy footprints']),clarification_question='',correction=dict(subject='NONE',note=''))
            _install_interpretation(monkeypatch,record,calls)
            before=state();logs_before=st.load_log();scene=st.load_active_scene()
            t=time.perf_counter();reply=client.post('/api/chat?ui_mode=player',json={'text':text});elapsed=time.perf_counter()-t
            after=state();logs_after=st.load_log();internal=logs_after[-1]
            def docs(s,logs):return {**{k+'.json':v for k,v in s.items()},'session_log.jsonl':logs,'scenes/frontier_gate.json':scene}
            a=action();a.update(player_input=text,subject_terms=['stew','rumors','patrol'],requires_substantive_answer=True,interaction_category='interaction' if i<3 else 'investigate')
            evaluation=g.evaluate(a,reply.status_code,reply.json(),docs(before,logs_before),docs(after,logs_after),[])
            rows.append(dict(turn=i,player=text,mock_interpretation=record,interpretation_request=calls[-1] if len(calls)>=i else None,status=reply.status_code,response=reply.json(),internal=internal,before=before,after=after,state_diff=g.diff(docs(before,logs_before),docs(after,logs_after)),evaluation=evaluation,classification=g.classify_turn(reply.status_code,reply.json(),[]),latency_seconds=elapsed))
            save('offline_run.json',dict(turns=rows,expressions=expressions,resolver_traces=traces,elapsed_seconds=time.perf_counter()-started,live_provider_requests=0))
            assert reply.status_code==200
            if i<3:assert not evaluation['stop'],evaluation
        assert rows[1]['internal']['resolution']['social']['topic_revealed']['id']=='patrol_rumor'
        assert 'muddy_footprints_northwest' in json.dumps(rows[1]['after']['session'])
        assert not rows[2]['classification']['gameplay_completed']
        assert rows[2]['before']['session']['turn_counter']==rows[2]['after']['session']['turn_counter']
        assert rows[2]['before']['character']==rows[2]['after']['character']
        save('offline_summary.json',dict(conversation_reproduced=True,investigation_completed=False,live_go=False,live_provider_requests=0,elapsed_seconds=time.perf_counter()-started))
