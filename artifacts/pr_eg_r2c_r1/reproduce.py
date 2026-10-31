"""Cycle evidence probes; deterministic owner seams, never fresh provider evidence."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from game.conversational_continuity import record_delivered_exchange, supplied_clarification, continuity_directive
from game.social import _next_topic_to_reveal
from tests.test_pr_eg_r2c_speech_adoption import resolution,adopt
H=Path(__file__).parent
social=dict(npc_id='sergeant_mara',npc_name='Sergeant Mara')
road='The street beyond the gate is the north road.';guard='Guards watch the north gate throughout the night.'
def record(s,q,t):return record_delivered_exchange(s,player_text=q,delivered_text='Sergeant Mara says, "'+t+'"',social=social)
def main():
 s={};record(s,'What is the road called?',road)
 rows=[]
 for id,q in [('A','Can you repeat that?'),('B','Can you repeat that in simpler words?')]:
  res=resolution(q,session=s);out=adopt(res,q,'The password is Winter.',s)
  rows.append(dict(id=id,text=out['player_facing_text'],pass_=road in out['player_facing_text'],authority=res['social']['dialogue_authority']))
 npc=dict(id='sergeant_mara',name='Sergeant Mara',topics=[dict(id='road',text=road),dict(id='watch',text=guard)])
 q='I ask Sergeant Mara about the north road again.';r=_next_topic_to_reveal(npc,dict(revealed_topics=['road']),player_text=q,allow_revealed=True)
 rows.append(dict(id='C',selected=r,pass_=bool(r and r['id']=='road')))
 record(s,'Who made the lantern?',"I couldn't tell you.")
 world=dict(npcs=[dict(id='sergeant_mara',name='Sergeant Mara',location='courtyard')]);scene=dict(scene=dict(id='courtyard'))
 s['interaction_context']=dict(active_interaction_target_id='sergeant_mara',active_interaction_kind='social')
 for id,q in [('D','GM, what did Mara say about the road?'),('F','GM, repeat what Mara said about the road.')]:
  if id=='F':record(s,'Do you prefer morning?', 'I prefer the morning.')
  d=continuity_directive(q,session=s,scene=scene,world=world)
  rows.append(dict(id=id,directive=d,pass_=bool(d and road in d['line'])))
 for id,q in [('E','I ask Sergeant Mara whether guards watch the north gate at night.'),('G','Do guards watch the north gate at night?')]:
  r=_next_topic_to_reveal(npc,{},player_text=q);rows.append(dict(id=id,selected=r,pass_=bool(r and r['id']=='watch')))
 q='What do you personally enjoy about the evening?';res=resolution(q);out=adopt(res,q,'I prefer evening because the guards leave the north gate unattended.',{})
 rows.append(dict(id='H',text=out['player_facing_text'],pass_='unattended' not in out['player_facing_text'],adoption=out['metadata']['accepted_response']))
 (H/(sys.argv[1]+'_reproduction.json')).write_text(json.dumps(rows,indent=2));print([(r['id'],r['pass_']) for r in rows])
if __name__=='__main__':main()
