"""Separate audit of raw comparison differences; preserves original evidence."""
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
rows=json.loads((OUT/'gameplay_replay.json').read_text())
def authoritative(state):
    s=state['session']
    return dict(scene=s.get('active_scene_id'),visited=s.get('visited_scene_ids'),
                overlays=s.get('runtime_scene_overlays'),runtime=s.get('scene_runtime'),
                character=state['character'],world=state['world'],combat=state['combat'])
def differences(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        return [d for k in a.keys()|b.keys() for d in differences(a.get(k),b.get(k),path+'/'+k)]
    if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in differences(x,y,path+'/'+str(i))]
    return [] if a==b else [path]
result=[dict(action=i+1,authoritative_equal=authoritative(rows[0][i]['state_after'])==authoritative(rows[1][i]['state_after']),
             raw_difference_paths=differences(rows[0][i]['state_after'],rows[1][i]['state_after'])) for i in range(5)]
(OUT/'state_equivalence_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
