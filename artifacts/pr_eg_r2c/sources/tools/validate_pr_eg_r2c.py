"""Fresh provider qualification through the actual production /api/chat endpoint.

Disposable fictional campaigns only. No interpretation, narration, validation,
or resolver doubles. Failure transcripts are written after every HTTP turn.
"""
from __future__ import annotations
import copy, hashlib, json, os, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/pr_eg_r2c'
PRIMARY=[
 ('I ask Sergeant Mara what the street beyond the gate is called.','north road'),
 ('What did you mean by north road?','north road'),
 ('Can you repeat that?','north road'),
 ('I ask Sergeant Mara, do you prefer morning or evening?','prefer'),
 ('Why do you prefer the evening?','prefer'),
 ('I ask Sergeant Mara who forged the lantern.','uncertainty'),
 ('I ask Sergeant Mara whether guards watch the north gate at night.','throughout the night'),
 ('What did you mean by that?','throughout the night'),
 ('I ask Sergeant Mara when the gate is left unguarded.','uncertainty'),
 ('Promise me a reward if I carry a message for you.','nonbinding'),
 ('Swear you will pay me ten silver if I do it.','nonbinding'),
 ('I ask Sergeant Mara what secret passage bypasses the gate.','uncertainty'),
 ('I ask Sergeant Mara about the north road again.','north road'),
 ('GM, what did Mara say about the road?','north road'),
 ('I ask Sergeant Mara, do you still prefer the evening?','prefer'),
]
SECOND=[
 ('I ask Corporal Bren whether guards watch the north gate at night.','throughout the night'),
 ('What did you mean by that?','throughout the night'),
 ('I ask Corporal Bren who made the lantern.','uncertainty'),
 ('I ask Corporal Bren, do you prefer the morning or the evening?','prefer'),
 ('Why that one, then?','prefer'),
 ('I ask Corporal Bren what the street outside the gate is named.','north road'),
 ('Say that again in plainer words.','north road'),
 ('If I carry a message, will you promise me a reward?','nonbinding'),
 ('Promise me a reward if I carry a message for you.','nonbinding'),
 ('I ask Corporal Bren when the guards leave the gate unattended.','uncertainty'),
 ('I ask Corporal Bren what the password is.','uncertainty'),
 ('GM, repeat what Bren said about the road.','north road'),
]

def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2,default=str),encoding='utf-8')

def diff(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        return [r for k in sorted(set(a)|set(b)) for r in diff(a.get(k),b.get(k),path+'/'+str(k))]
    return [] if a==b else [dict(path=path,before=a,after=b)]

def failures(expected,text):
    low=text.lower(); found=[]
    if expected=='uncertainty':
        if not any(bit in low for bit in ["couldn't", "don't know", 'cannot', "can't", 'not sure']): found.append('knowledge_uncertainty_not_preserved')
    elif expected=='nonbinding':
        if not any(bit in low for bit in ["can't promise", "couldn't", "cannot promise", "won't", 'nothing has been promised']): found.append('nonbinding_refusal_not_established')
    elif expected not in low: found.append('missing_requested_answer:'+expected)
    if any(bit in low for bit in ['carry out that request','another route','trying to accomplish','who are you asking','which person are you']):found.append('unrelated_fallback')
    return found

def main():
    OUT.mkdir(exist_ok=True)
    plan=dict(primary=PRIMARY,secondary=SECOND)
    if sys.argv[-1]=='freeze':
        write('live_plan.json',plan)
        write('live_freeze.json',dict(sha256=hashlib.sha256((OUT/'live_plan.json').read_bytes()).hexdigest(),stage='before fresh provider qualification'))
        return
    assert json.loads((OUT/'live_plan.json').read_text())==json.loads(json.dumps(plan))
    os.environ.update(ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1',ASHEN_DISABLE_PROVIDER_CALLS='0',
        ASHEN_DISABLE_LIVE_INTERPRETATION='0',ASHEN_PROVIDER_REQUEST_LIMIT='90',
        ASHEN_PROVIDER_INPUT_TOKEN_LIMIT='1000000',ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT='60000',
        ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT='1060000',ASHEN_PROVIDER_TIMEOUT_SECONDS='45',
        ASHEN_PROVIDER_USAGE_PATH=str(OUT/'live_usage.jsonl'))
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env')
    if not os.environ.get('OPENAI_API_KEY'):
        write('live_status.json',dict(status='UNVERIFIED',reason='key_missing')); return
    import pytest
    from fastapi.testclient import TestClient
    from tests.test_pr_ef_gm_authority import seed_scene
    from game import storage
    from game.api import app
    from game.provider_budget import snapshot
    from tools.validate_pr_eg_r1 import calls_since
    all_rows={}
    for label,turns in plan.items():
        with pytest.MonkeyPatch.context() as mp:
            data_dir=OUT/'disposable_state'/('live_'+label)
            seed_scene(data_dir,mp)
            if label=='secondary':
                # Rename the seeded speaker and every local presence reference.
                for path in data_dir.rglob('*.json'):
                    path.write_text(path.read_text(encoding='utf-8').replace('sergeant_mara','corporal_bren').replace('Sergeant Mara','Corporal Bren'),encoding='utf-8')
            world=storage.load_world()
            target='sergeant_mara' if label=='primary' else 'corporal_bren'
            for npc in world['npcs']:
                if npc['id']==target:
                    npc.setdefault('topics',[]).append(dict(id='night_watch',text='Guards watch the north gate throughout the night.'))
            storage.save_world(world)
            mp.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0');mp.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','0')
            rows=[];all_rows[label]=rows
            client=TestClient(app)
            for n,(player,expected) in enumerate(turns,1):
                wb=copy.deepcopy(storage.load_world());sb=copy.deepcopy(storage.load_session())
                start=len(snapshot()['records']);started=time.perf_counter()
                response=client.post('/api/chat?ui_mode=player',json=dict(text=player,ui_mode='player'))
                elapsed=(time.perf_counter()-started)*1000;result=response.json()
                wa=copy.deepcopy(storage.load_world());sa=copy.deepcopy(storage.load_session())
                gm=result.get('gm_output') or {}; text=gm.get('player_facing_text') or ''
                acceptance=(gm.get('metadata') or {}).get('accepted_response') or {}
                history=(sa.get('conversational_context') or {}).get('delivered_exchanges') or []
                failed=failures(expected,text)
                if acceptance and text!=acceptance.get('text'):failed.append('adoption_text_mismatch')
                if history and history[-1]['delivered_text']!=text:failed.append('delivered_history_mismatch')
                world_diff=diff(wb,wa)
                unauthorized=[d for d in world_diff if not d['path'].startswith(('/factions','/event_log'))]
                # Resolver topic discovery/lead records can be legitimate; retain
                # complete diffs for audit rather than claiming all are forbidden.
                usage=calls_since(snapshot,start)
                row=dict(turn=n,player=player,expected=expected,http_status=response.status_code,
                    text=text,result=result,calls=usage,elapsed_ms=elapsed,adoption=acceptance,
                    history_before=(sb.get('conversational_context') or {}).get('delivered_exchanges'),
                    history_after=history,commitment_diff=diff((sb.get('conversational_context') or {}).get('dialogue_commitments'),(sa.get('conversational_context') or {}).get('dialogue_commitments')),
                    world_diff=world_diff,world_nonpassive_diff=unauthorized,
                    failures=failed,save_load=None)
                if n in {4,8,len(turns)}:
                    storage.save_session(copy.deepcopy(sa)); loaded=storage.load_session()
                    row['save_load']=dict(context_equal=loaded.get('conversational_context')==sa.get('conversational_context'))
                rows.append(row);write('live_qualification.json',all_rows)
                print(json.dumps(dict(conversation=label,turn=n,calls=usage['provider_calls'],failures=failed,text=text)),flush=True)
    write('live_status.json',dict(status='executed',turns={k:len(v) for k,v in all_rows.items()},failures={k:sum(len(r['failures']) for r in v) for k,v in all_rows.items()}))

if __name__=='__main__':main()
