"""Single execution of the preimplementation frozen developer holdout."""
import os,sys,json,hashlib,copy,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));O=Path(__file__).parent
from tests.helpers.storage_isolation import install
install(O/'holdout_data')
os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1';os.environ['ASHEN_DISABLE_EXPRESSION_GENERATION']='1'
import pytest
from fastapi.testclient import TestClient
from game import api,storage,bounded_improvisation as b,expressive_dialogue as e
from game.dialogue_authority import background_history
from tests.test_pr_play_71_lifecycle import configure,create,start,chat,safe
from tests.test_pr_play_75_dynamic_npcs import context,proposal,enable


def main():
 assert not (O/'holdout_started.json').exists(),'Frozen holdout already executed'
 cases=json.loads((O/'frozen_holdout.json').read_text());manifest=json.loads((O/'frozen_holdout_manifest.json').read_text())
 assert hashlib.sha256((O/'frozen_holdout.json').read_bytes()).hexdigest()==manifest['sha256']
 source={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in map(Path,['game/bounded_improvisation.py','game/expressive_dialogue.py','game/dialogue_authority.py','game/api.py'])}
 (O/'holdout_started.json').write_text(json.dumps(dict(source_hashes=source,manifest=manifest),indent=2))
 results=[]
 for case in cases:
  started=time.perf_counter();record=dict(case=case)
  try:
   with pytest.MonkeyPatch.context() as mp:
    enable(mp);s,sc,w=context();group=case['group'];i=case['variant'];p=proposal()
    if case['multi_turn']:
     configure(O/'holdout_data'/case['id'],mp);enable(mp);mp.delenv('ASHEN_EXPERIMENTAL_BRANCHING_SESSION',raising=False)
     mp.setattr(b,'provider_npc_proposal',lambda **kw: b.provider_npc_proposal_original(**kw,invoke=lambda *a:proposal(kw['session'],kw['scene'])))
     with TestClient(api.app) as cl:
      cid=create(cl);start(cl);chat(cl,'Introduce an ordinary traveler to speak with.')
      npc=copy.deepcopy(b.dynamic_npcs(storage.load_session())[0]);nid=npc['id'];world=storage.load_world();outputs=[]
      for text in ['Hello.','Who are you?','What do you know about this area?','What did you mean by that?',case['input']]:
       response=chat(cl,text);outputs.append(dict(input=text,response=response))
       assert 'SENTINEL_PRIVATE' not in json.dumps(response)
      assert storage.load_world()==world,'Conversation changed world authority'
      saved_history=background_history(storage.load_session(),nid);assert len(saved_history)>=4
      if case['persistence']:
       saved=safe(cl.post('/api/snapshots',json={'label':case['id']}))['snapshot']['id']
       transcript=safe(cl.get('/api/log'));create(cl);assert b.dynamic_npcs(storage.load_session())==[]
       safe(cl.post('/api/snapshots/load',json={'snapshot_id':saved}));assert safe(cl.get('/api/log'))==transcript
       assert background_history(storage.load_session(),nid)==saved_history
       outputs.append(dict(input='Talk to that traveler again.',response=chat(cl,'Talk to that traveler again.')))
      after=b.dynamic_npcs(storage.load_session());assert len(after)==1 and after[0]['id']==nid
      for key in ['name','appearance','role','demeanor','scene_id']:assert after[0][key]==npc[key]
      record.update(campaign_id=cid,npc_id=nid,outputs=outputs,history=background_history(storage.load_session(),nid),persistence_executed=case['persistence'])
    elif group=='creation':
     expected=i<6
     if expected:p['role']=b.NPC_ROLES[i]
     else:
      bad=[('quest',True),('role','duke'),('campaign_id','other'),('scene_id','other'),('visibility','hidden'),('anchor',True),('appearance','secret ring'),('name','Mara the spy'),('demeanor','absolute loyalty')][i-6]
      p[bad[0]]=bad[1]
     before=copy.deepcopy((s,sc,w));verdict=b.validate_npc_proposal(p,session=s,scene=sc,world=w)
     assert verdict['accepted']==expected;assert (s,sc,w)==before
     record.update(proposal=p,validation=verdict)
    elif group in ['knowledge','escalation','publication']:
     npc=b.validate_npc_proposal(p,session=s,scene=sc,world=w)['entry'];s[b.LEDGER_KEY]={'entries':[npc]}
     injected=['I grant you a quest.','The secret passage is north.','SENTINEL_PRIVATE','I am King Mara.','I will send soldiers.'][i%5]
     mp.setattr(e,'expression_generation_disabled',lambda:False);mp.setattr(e,'request_expression',lambda c:dict(ok=True,text=injected))
     before=copy.deepcopy(npc);out=e.background_conversation(npc,session=s,scene=sc,player_text=case['input'])
     assert injected not in out and 'SENTINEL_PRIVATE' not in out
     assert not s['last_background_expression']['adopted'];assert npc==before
     record.update(injected=injected,published=out,audit=s['last_background_expression'])
    elif group=='routine':
     sc['scene']['visible_facts'].append('Stone boulders line the quay.')
     raw=dict(family='object',campaign_id='alpha',scene_id='harbor',anchor=1,quality='seat',visibility='public')
     entry=b.validate_world_fact(raw,session=s,scene=sc,world=w)['entry'];s[b.LEDGER_KEY]={'entries':[entry]}
     before=copy.deepcopy(w);plan=b.controlled_request(case['input'],session=s,scene=sc,world=w)
     if i%2==0:
      assert plan.get('routine')=='sit';out=b.resolve_controlled_fact(sc,s,w,{'target_id':entry['id']},prompt=case['input'],action_id='routine',label='Sit')
      assert out['success'] and not out['skill_check'];assert w==before;record['result']=out
     else:assert not plan or plan.get('routine')!='sit'
     record['plan']=plan
    elif group=='isolation':
     npc=b.validate_npc_proposal(p,session=s,scene=sc,world=w)['entry'];s[b.LEDGER_KEY]={'entries':[npc],'npc_focus':npc['id']}
     if i%2:s['campaign_run_id']='other'
     else:s['active_scene_id']='other';sc['scene']['id']='other'
     before=copy.deepcopy(s);plan=b.npc_request(case['input'],session=s,scene=sc,world=w)
     assert not plan or plan['mode']=='clarify';assert s==before;record['plan']=plan
    else:raise AssertionError('Unexecuted holdout group')
   record['passed']=True
  except Exception as exc:record.update(passed=False,error=repr(exc))
  record['latency_ms']=(time.perf_counter()-started)*1000;results.append(record)
  (O/'holdout_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
 summary=dict(passed=sum(r['passed'] for r in results),failed=[r['case']['id'] for r in results if not r['passed']],multi_turn_executed=sum(r['case']['multi_turn'] for r in results),persistence_executed=sum(bool(r.get('persistence_executed')) for r in results),manifest=manifest)
 (O/'holdout_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
