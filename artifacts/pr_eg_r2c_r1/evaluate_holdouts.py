"""Single independent holdout evaluation after source freeze. No tuning permitted."""
import copy,hashlib,json,sys
from pathlib import Path
H=Path(__file__).parent;R=H.parents[1];sys.path.insert(0,str(R))
import pytest
from game import storage
from game.social import _next_topic_to_reveal
from game.conversational_continuity import _best_exchange,delivered_exchanges,record_delivered_exchange,supplied_clarification,continuity_directive
from tests.test_pr_eg_r2c_speech_adoption import adopt,resolution
from tests.test_pr_ef_gm_authority import seed_scene
out=[]
for file,freeze in [('frozen_holdouts.json','freeze.json'),('final_holdouts.json','final_holdouts_freeze.json'),('qualification_holdouts.json','qualification_holdouts_freeze.json')]:
 assert hashlib.sha256((H/file).read_bytes()).hexdigest()==json.loads((H/freeze).read_text())['sha256']
 cases=json.loads((H/file).read_text())
 for c in cases:
  result=dict(id=c['id'],evidence='DETERMINISTIC_OWNER_SEAM',case=c)
  try:
   s={};facts=c.get('facts') or [[c['source'],c['fact']]];nid=c['npc'];name=c['name']
   for topic,text in facts:
    record_delivered_exchange(s,player_text='Tell me about '+topic,delivered_text=f'{name} says, "{text}"',social=dict(npc_id=nid,npc_name=name,topic_revealed=dict(id=topic)),scene_id=c.get('location',''),turn=len(delivered_exchanges(s))+1)
   if c.get('save_load'):
    with pytest.MonkeyPatch.context() as mp:
     seed_scene(H/'disposable_state'/('holdout_'+c['id']),mp)
     storage.save_session(copy.deepcopy(s));loaded=storage.load_session();assert loaded['conversational_context']==s['conversational_context'];s=loaded
   q=c['question'];expected=c.get('expected_topic',c.get('source'))
   if c.get('history') or file=='frozen_holdouts.json':
    record_delivered_exchange(s,player_text='Who made the bell?',delivered_text=f'{name} says, "I could not tell you."',social=dict(npc_id=nid,npc_name=name),turn=12) if c['id'] in {'R1H2','R1H3'} else None
    found=_best_exchange(q,delivered_exchanges(s),'' if q.startswith('GM') else nid);result['selected']=found
    assert isinstance(found,dict) and found['topic_id']==expected
    if q.startswith('GM'):
     directive=continuity_directive(q,session=s,world={},scene={});result['directive']=directive
     assert directive['owner']=='gm' and dict(facts)[expected] in directive['line']
    else:
     text=supplied_clarification(q,s,nid,name);result['text']=text;assert dict(facts)[expected] in text
   else:
    npc=dict(id=nid,name=name,topics=[dict(id=t,text=text) for t,text in facts]);selection={}
    found=_next_topic_to_reveal(npc,{},player_text=q,selection=selection);result['selection']=selection
    if expected:
     assert found and found['id']==expected
     res=resolution(q,found['text'],s,nid,name)
    else:res=resolution(q,session=s,npc_id=nid,name=name)
    accepted=adopt(res,q,c['candidate'],s);result['adoption']=accepted['metadata']['accepted_response'];result['text']=accepted['player_facing_text']
    assert c['candidate'] not in result['text'] and 'treasury' not in result['text']
    if expected:assert dict(facts)[expected].lower() in result['text'].lower()
   result['passed']=True
  except Exception as e:result.update(passed=False,error=repr(e))
  out.append(result)
(H/'holdout_results.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print([(r['id'],r['passed']) for r in out])
