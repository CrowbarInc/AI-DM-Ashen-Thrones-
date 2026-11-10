import os
os.environ['PR72V_STORAGE']='holdout_data'; os.environ['PR72V_NETWORK']='freeze_network.jsonl'
from runtime import *
from artifacts.pr_play_67.http_harness import server
from tests.test_pr_play_71_lifecycle import byid
import hashlib
with server() as request:
 def call(p,d=None):
  r=request(p,d); assert r['status']==200,r; return r['body']
 def chat(t): return call('/api/chat',{'text':t})
 states={}; slots={}
 for branch in ['survey','report']:
  call('/api/new_campaign',{}); call('/api/start_campaign',{})
  chat('I examine the notice board.');chat('I follow the missing patrol rumor.');chat('I examine the weathered milestone.')
  a=byid('patrol_'+branch);call('/api/action',{'action_type':'exploration','intent':a['label'],'exploration_action':{'id':a['id'],'type':'custom','label':a['label']}})
  if branch=='report':chat('I return to Cinderwatch Gate.')
  chat('Please record my survey.' if branch=='survey' else 'Please give the watch my patrol report.')
  if branch=='survey':chat('Examine the tracks.')
  states[branch]=dict(authority=snapshot(),log=storage.load_log())
  slots[branch]=call('/api/snapshots',{'label':'72V frozen '+branch})['snapshot']['id']
 (OUT/'frozen_start_states.json').write_text(json.dumps(states,indent=2))
 (OUT/'holdout_slots.json').write_text(json.dumps(slots,indent=2))
 m=json.loads((OUT/'frozen_holdout_manifest.json').read_text()); m['states_sha256']=hashlib.sha256((OUT/'frozen_start_states.json').read_bytes()).hexdigest()
 m['source_at_freeze']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'game/player_initiative.py',ROOT/'game/exploration.py']}
 (OUT/'frozen_holdout_manifest.json').write_text(json.dumps(m,indent=2));print('Frozen 50 cases and exact starting authority states before repairs.')
