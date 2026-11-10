"""Disabled authority controls for the same five supported actions."""
import sys,copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from artifacts.pr_play_66 import harness as h
from game import storage
rows=json.loads((h.OUT/'http_gameplay.json').read_text(encoding='utf-8'));h.seed('tcp_disabled_controls');h.base.disable_publication();controls=[]
for r in rows:
    h.candidate(None,'provider_error');controls.append(h.post(r['request']['json']['text']))
def projection(row):
    s=row['state_after']['session'];return dict(scene=s.get('active_scene_id'),visited=s.get('visited_scene_ids'),overlays=s.get('runtime_scene_overlays'),runtime=s.get('scene_runtime'),character=row['state_after']['character'],world=row['state_after']['world'],combat=row['state_after']['combat'])
results=[dict(action=r['request']['json']['text'],authority_equal=projection(r)==projection(c),resolution_equal=h.base.mechanical(r['body'])==h.base.mechanical(c['body'])) for r,c in zip(rows,controls)]
h.save('disabled_sequence_controls.json',controls);h.save('state_integrity.json',dict(per_action=results,passed=all(r['authority_equal'] and r['resolution_equal'] for r in results)))
print(results)
