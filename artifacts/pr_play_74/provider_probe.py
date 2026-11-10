import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).parent
from tests.helpers.storage_isolation import install
install(OUT/'provider_data')
os.environ['ASHEN_PROVIDER_REQUEST_LIMIT']='2'
os.environ['ASHEN_PROVIDER_INPUT_TOKEN_LIMIT']='15000'
os.environ['ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT']='1000'
os.environ['ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT']='20000'
os.environ['ASHEN_DISABLE_PROVIDER_RETRIES']='1'
os.environ.pop('ASHEN_DISABLE_PROVIDER_CALLS',None)
from game.bounded_improvisation import provider_world_fact_proposal
from game.provider_budget import snapshot
session={'campaign_run_id':'provider_probe','active_scene_id':'isolated_road','turn_counter':1}
scene={'scene':{'id':'isolated_road','visible_facts':['Stone boulders border a country road.']}}
rows=[provider_world_fact_proposal(session=session,scene=scene,world={},family=family) for family in ['environment','object']]
(OUT/'provider_results.json').write_text(json.dumps({'rows':rows,'usage':snapshot()},indent=2))
print(json.dumps({'results':[r['validation']['reason'] for r in rows],'usage':snapshot()},indent=2))
