"""New-process continuation from a copy of final qualification's saved session."""
import copy
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/pr_eg_r6_r2_r1'
target=OUT/'restart';target.mkdir(exist_ok=True)
shutil.copytree(OUT/'final/state/continuity_0/data',target/'state',dirs_exist_ok=True)
os.environ.update(ASHEN_DATA_DIR=str(target/'state'),ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1',
    ASHEN_UNIFIED_SEMANTIC_PLANNING='1',ASHEN_DISABLE_PROVIDER_CALLS='0',ASHEN_DISABLE_LIVE_INTERPRETATION='0',
    ASHEN_DISABLE_EXPRESSION_GENERATION='0',ASHEN_PROVIDER_REQUEST_LIMIT='20',ASHEN_PROVIDER_INPUT_TOKEN_LIMIT='100000',
    ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT='20000',ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT='120000',
    ASHEN_PROVIDER_USAGE_PATH=str(target/'usage.jsonl'),ASHEN_SEMANTIC_TRACE_PATH=str(target/'semantic_traces.jsonl'))
from fastapi.testclient import TestClient
from game import api,storage
from game.conversational_referents import state,active
from game.immutable_valid_response import verify_delivery_record
from game.provider_budget import snapshot

saved=json.loads((OUT/'final/state/continuity_0/data/session.json').read_text())['payload']
before=storage.load_session();old=active(before);started=time.perf_counter()
response=TestClient(api.app).post('/api/chat?ui_mode=player',json={'text':'I meant the amber reliquary.','ui_mode':'player'})
after=storage.load_session();new=active(after);gm=response.json().get('gm_output') or {};adoption=(gm.get('metadata') or {}).get('accepted_response') or {}
checks={'loaded_identity':state(saved)==state(before), 'http':response.status_code==200,
    'parent':new.get('parent_referent_id')==old.get('referent_id'), 'revision':new.get('revision')==old.get('revision',0)+1,
    'subject':new.get('request_proposition',{}).get('object')=='amber reliquary',
    'sealed':verify_delivery_record(adoption), 'history_exact':after['conversational_context']['delivered_exchanges'][-1]['delivered_text']==adoption.get('text')==gm.get('player_facing_text')}
result={'separate_process':True,'checks':checks,'prior_referents':state(before),'persisted_referents':state(after),
    'provider_calls':snapshot()['records'],'latency_ms':(time.perf_counter()-started)*1000,'response':response.json()}
(target/'result.json').write_text(json.dumps(result,indent=2,default=str))
print(json.dumps(checks),gm.get('player_facing_text'))
