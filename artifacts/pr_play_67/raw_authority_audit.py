"""Compare raw in-memory authority, before any evidence redaction."""
import sys,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from artifacts.pr_play_67.http_harness import *
from artifacts.pr_play_67.integration import ACTIONS,checked
def authority(state):
    s=state['session']
    return {**{k:state[k] for k in ['world','character','combat']},'scene':s['active_scene_id'],
            'visited':s['visited_scene_ids'],'overlays':s.get('runtime_scene_overlays'),'runtime':s.get('scene_runtime'),
            'clocks':s.get('clocks'),'turn_counter':s.get('turn_counter'),'gm_notes':s.get('gm_notes')}
sequences=[]
for enabled in [False,True]:
    with seed('raw_authority_'+str(enabled),enabled),server() as request:
        states=[]
        for text in ACTIONS:
            checked(request('/api/chat',{'text':text}));states.append(authority(snapshot()))
        sequences.append(states)
rows=[dict(action=i+1,equal_before_redaction=sequences[0][i]==sequences[1][i]) for i in range(5)]
save('raw_authority_audit.json',dict(per_action=rows,passed=all(r['equal_before_redaction'] for r in rows),
     raw_values_published=False,snapshots=redact(sequences)))
print(rows)
