"""Once-only developer holdout. Frozen cases precede implementation; no tuning."""
import sys,json,hashlib,traceback,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
import pytest
from fastapi.testclient import TestClient
from game import api,storage,authored_consequences as c
from tests.test_pr_play_70_branching import setup,DEFS,actions,act,flags,move

def main():
 fixture=OUT/'frozen_holdout.json';manifest=json.loads((OUT/'frozen_holdout_manifest.json').read_text())
 assert hashlib.sha256(fixture.read_bytes()).hexdigest()==manifest['sha256']
 (OUT/'holdout_started.json').open('x').write(json.dumps({'fixture_sha256':manifest['sha256']}))
 results=[]
 for case in json.loads(fixture.read_text())['cases']:
  row={'case':case}
  try:
   with pytest.MonkeyPatch.context() as mp:
    variant=case['variant'];group=case['group'];branch=case['branch'];idx=0 if branch=='survey' else 1
    ready=not(group=='availability' and variant<4)
    setup(OUT/'holdout_sessions'/case['id'],mp,ready=ready)
    a=DEFS['old_milestone'][idx];other=DEFS['old_milestone'][1-idx]
    if group=='availability':
     if variant in [4,5]:move('frontier_gate')
     elif variant in [6,7]:mp.setenv(c.SESSION,'another-campaign')
     expected=variant>=8
     assert (a['id'] in actions())==expected
     with TestClient(api.app) as client:body=act(client,a)
     assert bool(flags().get(a['id']))==expected
    else:
     with TestClient(api.app) as client:
      before=copy.deepcopy(flags());body=act(client,a)
      assert flags().get(a['id']) is True and not flags().get(other['id'])
      assert body['gm_output']['player_facing_text']==a['consequence']['text']
      committed=copy.deepcopy(flags())
      if group in ['resolution','persistence','isolation']:
       for attempt in [other,a,other]:act(client,attempt);assert flags()==committed
      if group in ['followup','persistence']:
       if branch=='report':move('frontier_gate')
       follow=DEFS['old_milestone'][2] if branch=='survey' else DEFS['frontier_gate'][0]
       assert follow['id'] in actions()
       body=act(client,follow);assert body['gm_output']['player_facing_text']==follow['consequence']['text']
       assert flags()[case['expected']['followup_flag']] is True
       committed=copy.deepcopy(flags());act(client,follow);assert flags()==committed
       snap=client.post('/api/snapshots',json={'label':'holdout'}).json()['snapshot']['id']
       loaded=client.post('/api/snapshots/load',json={'snapshot_id':snap})
       assert loaded.status_code==200 and flags()==committed
      if group=='publication':
       from game.exploration import resolve_exploration_action
       move('old_milestone')
       res=resolve_exploration_action(storage.load_active_scene(),storage.load_session(),storage.load_world(),a)
       raw=['Both branches occurred.','The unchosen branch occurred.','You gain a key.','CANARY_HIDDEN_DESTINATION',{}][variant]
       gm={'player_facing_text':raw};p={'gm_output':dict(gm)}
       api._finalize_investigation_publication(gm,gm,p,res,storage.load_session(),a['label'])
       assert gm['player_facing_text']==res['hint'] and flags()==committed
      if group=='isolation':
       mp.setenv(c.SESSION,'other');assert a['id'] not in actions()
       assert flags()==committed
      response=client.get('/api/state');assert 'CANARY_' not in response.text and 'consequence' not in response.text
      row['authority_flags']=flags();row['player_text']=body.get('gm_output',{}).get('player_facing_text')
    row['correct']=True
  except Exception:row.update(correct=False,error=traceback.format_exc())
  results.append(row)
  (OUT/'holdout_results.json').write_text(json.dumps(results,indent=2))
 summary={'cases':len(results),'correct':sum(r['correct'] for r in results),'failed':sum(not r['correct'] for r in results),'fixture_sha256':manifest['sha256'],'developer_authored':True,'executions':1}
 (OUT/'holdout_summary.json').write_text(json.dumps(summary,indent=2));print(summary)
if __name__=='__main__':main()
