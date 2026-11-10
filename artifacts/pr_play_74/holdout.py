import sys,json,hashlib,time,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).parent
from tests.helpers.storage_isolation import install
install(OUT/'holdout_data')
from game.bounded_improvisation import validate_world_fact
files=['game/bounded_improvisation.py','game/player_initiative.py','game/player_interpretation_bridge.py','game/exploration.py']
(OUT/'final_source.json').write_text(json.dumps({f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},indent=2))
start=OUT/'holdout_started.json'
if start.exists():raise SystemExit('Holdout already executed; refusing rerun')
manifest=json.loads((OUT/'frozen_holdout_manifest.json').read_text());payload=(OUT/'frozen_holdout.json').read_bytes()
assert hashlib.sha256(payload).hexdigest()==manifest['sha256']
start.write_text(json.dumps({'time':time.time(),'source_freeze':'final_source.json'}))
rows=[]
for case in json.loads(payload):
    before=copy.deepcopy(case)
    t=time.perf_counter();verdict=validate_world_fact(case['proposal'],session=case['session'],scene=case['scene'],world=case['world'])
    rows.append({'id':case['id'],'passed':verdict['accepted']==case['expected']['accepted'] and verdict['reason']==case['expected']['reason'] and case==before,'validation':verdict,'validation_ms':(time.perf_counter()-t)*1000})
(OUT/'holdout_results.json').write_text(json.dumps(rows,indent=2))
(OUT/'holdout_summary.json').write_text(json.dumps({'passed':sum(r['passed'] for r in rows),'total':len(rows),'note':'Structural validation only. Persistence expectations require separate lifecycle evidence.'},indent=2))
print(sum(r['passed'] for r in rows), '/',len(rows))
