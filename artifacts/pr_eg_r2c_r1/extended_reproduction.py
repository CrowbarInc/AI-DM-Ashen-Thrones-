from pathlib import Path
import subprocess,sys,json
h=Path(__file__).parent;root=h.parents[1]
probe='''
import json
from game.conversational_continuity import record_delivered_exchange,continuity_directive
s={};social=dict(npc_id='sergeant_mara',npc_name='Sergeant Mara')
road='The street beyond the gate is the north road.'
record_delivered_exchange(s,player_text='What road?',delivered_text='Sergeant Mara says, "'+road+'"',social=social,turn=1)
for i in range(10):
 record_delivered_exchange(s,player_text='Who made object '+str(i)+'?',delivered_text='Sergeant Mara says, "I could not identify that maker."',social=social,turn=i+2)
s['interaction_context']=dict(active_interaction_target_id='sergeant_mara',active_interaction_kind='social')
rows=[]
for id,q in [('D','GM, what did Mara say about the road?'),('F','GM, repeat what Mara said about the road.')]:
 d=continuity_directive(q,session=s,world={'npcs':[]},scene={});rows.append(dict(id=id,directive=d,passed=bool(d and road in d['line'])))
print(json.dumps(rows))
'''
rows={}
for label,path in [('baseline',h/'baseline_overlay'),('final',root)]:
 cmd=[sys.executable,'-c','import sys;sys.path.insert(0,sys.argv[1]);exec(sys.argv[2])',str(path.resolve()),probe]
 run=subprocess.run(cmd,text=True,capture_output=True,cwd=root);rows[label]=json.loads(run.stdout)
(h/'extended_historical_reproduction.json').write_text(json.dumps(dict(evidence='DETERMINISTIC_FROZEN_BASELINE_AND_FINAL',timing='Long-history reproduction executed after repair against preserved pre-edit source; short pre-edit D/F probes passed.',results=rows),indent=2));print({k:[r['passed'] for r in v] for k,v in rows.items()})
