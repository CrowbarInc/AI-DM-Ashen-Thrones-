"""Matched-operation control versus the saved live-provider sequence."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
from artifacts.pr_play_67 import http_harness as h
h.OUT=OUT
def authority(state):
    s=state['session']
    return {**{k:state[k] for k in ['world','character','combat']},'scene':s['active_scene_id'],'visited':s['visited_scene_ids'],'overlays':s.get('runtime_scene_overlays'),'runtime':s.get('scene_runtime'),'clocks':s.get('clocks'),'turn_counter':s.get('turn_counter'),'gm_notes':s.get('gm_notes')}
live=json.loads((OUT/'live_results.json').read_text(encoding='utf-8'))['rows'];rows=[]
with h.seed('authority_control',False),h.server() as request:
    for saved in live:
        r=request(saved['request']['path'],saved['request']['json'])
        rows.append(dict(input=saved['input'],equal_before_redaction=authority(h.snapshot())==authority(saved['authority_after']),control=r))
(OUT/'state_integrity.json').write_text(json.dumps(dict(passed=all(r['equal_before_redaction'] for r in rows),rows=rows),indent=2),encoding='utf-8')
