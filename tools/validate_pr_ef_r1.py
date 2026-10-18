"""PR-EF-R1 bounded fresh semantic and production HTTP qualification.

Uses only the existing disposable authored scene. Holdout behavior replays its
fresh isolated interpretation (explicitly recorded-provider); conversations use
fresh interpretation AND narration through /api/chat with no replay/stubs.
"""
from __future__ import annotations
import argparse, copy, json, os, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/pr_ef_r1'

def main():
 p=argparse.ArgumentParser(); p.add_argument('--mode',choices=['holdouts','conversation'],required=True); p.add_argument('--variant',type=int,default=1); p.add_argument('--replay',type=Path); a=p.parse_args()
 name=f'{a.mode}_{a.variant}'; usage=OUT/f'{name}.usage.jsonl'
 prior=[]
 for f in OUT.glob('*.usage.jsonl'):
  prior.extend(json.loads(s) for s in f.read_text().splitlines() if s.strip())
 used=sum(r.get('sent') is True for r in prior)
 ceiling=json.loads((OUT/"budget.json").read_text())["maximum_requests"]
 remaining=ceiling-used
 if remaining<=0 or usage.exists(): raise RuntimeError('Budget exhausted or output already exists')
 os.environ.update(ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1', ASHEN_DISABLE_PROVIDER_CALLS='0', ASHEN_DISABLE_LIVE_INTERPRETATION='0', ASHEN_PROVIDER_REQUEST_LIMIT=str(min(24 if a.mode=='holdouts' else 19,remaining)), ASHEN_PROVIDER_INPUT_TOKEN_LIMIT=str(430000-sum(r.get('input_tokens') or 0 for r in prior)), ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT=str(22000-sum(r.get('output_tokens') or 0 for r in prior)), ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT=str(452000-sum(r.get('total_tokens') or 0 for r in prior)), ASHEN_PROVIDER_TIMEOUT_SECONDS='25', ASHEN_NARRATION_MAX_OUTPUT_TOKENS='1600', ASHEN_PROVIDER_USAGE_PATH=str(usage))
 import pytest
 from fastapi.testclient import TestClient
 from game import storage
 from game.api import app
 from game import live_chat_interpretation as interp
 from game.provider_budget import snapshot
 from tests.test_pr_ef_gm_authority import seed_scene, TEN_TURNS
 from tests.test_pr_du_player_pipeline import _fake_gm_for_resolution
 from game.conversational_orchestration import deterministic_conversational_decision
 frozen=json.loads((ROOT/'artifacts/pr_ef_gm_authority/holdouts.json').read_text())
 independent=json.loads((OUT/'independent_holdouts.json').read_text())
 second=['Give me a description of the courtyard.', 'What is already visible on the lamp?', 'What can I infer from Mara watching the road?', 'I ask Mara where the road outside the gate goes.', 'Which road are you referring to?', 'As GM, explain what the sergeant has told me.', 'I examine the courtyard lantern closely.', 'How did my examination reveal the mark?', 'Drop any outstanding request; keep what already happened.', 'I make for the courtyard gate.']
 expressions=frozen+independent if a.mode=='holdouts' else [(s,None) for s in (TEN_TURNS if a.variant in [1,3,5] else second)]
 rows=[]
 captured=json.loads(a.replay.read_text(encoding='utf-8'))['rows'] if a.replay else None
 def write():
  (OUT/f'{name}.json').write_text(json.dumps({'mode':a.mode,'fresh_provider':not bool(a.replay),'replay_source':str(a.replay) if a.replay else None,'behavior_transport':'recorded fresh isolated interpretation via HTTP' if a.mode=='holdouts' else 'production /api/chat; fresh interpretation/narration; no reset between turns','rows':rows,'provider':snapshot(),'prior_calls':used,'budget_maximum_calls':ceiling},indent=2,ensure_ascii=False),encoding='utf-8')
 with tempfile.TemporaryDirectory(prefix='pr_ef_r1_',dir=ROOT/'development/tmp') as temp, pytest.MonkeyPatch.context() as mp:
  def reset():
   seed_scene(Path(temp),mp); os.environ['ASHEN_DISABLE_LIVE_INTERPRETATION']='0'
  reset(); client=TestClient(app)
  for i,(text,expected) in enumerate(expressions,1):
   if a.mode=='holdouts': reset()
   start=time.perf_counter(); count=snapshot()['requests']; isolated=None; wire=[]; real=interp.request_interpretation
   if a.mode=='holdouts':
    if captured:
     mp.setattr(interp,'request_interpretation',lambda *args,**kw: {'ok':True,'sent':False,'text':captured[i-1]['isolated_interpretation']['raw_interpretation']})
    isolated=interp.interpret_production_turn(player_text=text,mode='AUTO',scene=storage.load_active_scene(),world=storage.load_world(),session=storage.load_session(),log=[])
    raw=isolated.get('raw_interpretation','')
    if expected=='CONFIRMATION':
     with pytest.MonkeyPatch.context() as setup:
      setup.setattr('game.api.call_gpt',_fake_gm_for_resolution)
      client.post('/api/chat',json={'text':'I inspect the courtyard lantern, then I walk through the courtyard gate.'})
    def replay(messages,**kwargs):
     wire.append(raw); return {'ok':True,'sent':False,'text':raw}
    mp.setattr(interp,'request_interpretation',replay); mp.setattr('game.api.call_gpt',_fake_gm_for_resolution)
   else:
    def capture(messages,**kwargs):
     r=real(messages,**kwargs); wire.append(copy.deepcopy(r)); return r
    mp.setattr(interp,'request_interpretation',capture)
   before={'session':copy.deepcopy(storage.load_session()),'world':copy.deepcopy(storage.load_world()),'character':copy.deepcopy(storage.load_character()),'combat':copy.deepcopy(storage.load_combat())}
   deterministic=deterministic_conversational_decision(player_text=text,scene=storage.load_active_scene(),world=before['world'],session=before['session'],log=storage.load_log())
   response=client.post('/api/chat?ui_mode=player',json={'text':text,'ui_mode':'player'})
   data=response.json(); res=data.get('resolution') or {}; md=res.get('metadata') or {}; dec=md.get('conversational_decision') or {}; answer=(data.get('gm_output') or {}).get('player_facing_text','')
   after={'session':storage.load_session(),'world':storage.load_world(),'character':storage.load_character(),'combat':storage.load_combat()}
   changes={domain:{k:{'before':before[domain].get(k),'after':after[domain].get(k)} for k in set(before[domain])|set(after[domain]) if before[domain].get(k)!=after[domain].get(k)} for domain in before}
   nonmutation=all(before[d]==after[d] for d in ['world','character','combat']) and before['session'].get('turn_counter')==after['session'].get('turn_counter') and before['session'].get('active_scene_id')==after['session'].get('active_scene_id')
   if a.mode=='holdouts':
    comm=(isolated.get('record') or {}).get('communication') or {}; actual=comm.get('purpose') if expected in ['CONFIRMATION','CORRECTION','WITHDRAWAL'] else comm.get('recipient')
    if expected in ['GM','SESSION']: passed=nonmutation and not res.get('social') and bool(answer) and res.get('kind')!='conversational_clarify'
    elif expected in ['CORRECTION','WITHDRAWAL']: passed=nonmutation and dec.get('communication_purpose')==expected
    elif expected=='CONFIRMATION': passed=res.get('action_id')=='courtyard_lantern' and after['session'].get('turn_counter')==before['session'].get('turn_counter')+1
    elif expected=='NPC': passed=(res.get('social') or {}).get('npc_id')=='sergeant_mara'
    elif expected=='CHARACTER': passed=res.get('kind')=='scene_transition' and after['session'].get('active_scene_id')=='waystation_street'
    elif expected=='MIXED': passed=nonmutation and dec.get('communication_owner')=='MIXED' and bool(dec.get('secondary_intentions'))
    else: passed=nonmutation and dec.get('category')=='CLARIFY'
    strict=actual==expected
   else:
    strict=None; actual=None
    if i in [1,2,3,6,8,9]: passed=nonmutation and bool(answer) and res.get('kind')!='conversational_clarify'
    elif i in [4,5]: passed=(res.get('social') or {}).get('npc_id')=='sergeant_mara' and 'north road' in answer.lower() and 'no one here' not in answer.lower()
    elif i==7: passed=res.get('kind')=='discover_clue' and res.get('action_id')=='courtyard_lantern' and 'lantern_mark' in json.dumps(after['session']) and 'mark' in answer.lower()
    else: passed=res.get('kind')=='scene_transition' and after['session'].get('active_scene_id')=='waystation_street'
   critical=(expected in ['GM','SESSION','CORRECTION','WITHDRAWAL','AMBIGUOUS','MIXED'] or (a.mode=='conversation' and i in [1,2,3,6,8,9])) and not nonmutation
   records=snapshot().get('records',[])
   row={'turn':i,'player':text,'expected':expected,'actual':actual,'strict_pass':strict,'behavior_pass':bool(passed and response.status_code==200),'critical':critical,'http_status':response.status_code,'isolated_interpretation':isolated,'wire':wire,'deterministic_decision':deterministic.to_public_dict() if deterministic else None,'resolution':res,'response':answer,'state_before':before,'state_after':after,'state_changes':changes,'nonmutating':nonmutation,'elapsed_ms':round((time.perf_counter()-start)*1000,3),'provider_calls':snapshot()['requests']-count}
   if i==6 and a.mode=='conversation':
    storage.save_session(copy.deepcopy(after['session'])); row['save_load_context_equal']=storage.load_session().get('conversational_context')==after['session'].get('conversational_context')
   rows.append(row); write(); mp.setattr(interp,'request_interpretation',real)
   print(json.dumps({'turn':i,'strict':strict,'pass':row['behavior_pass'],'critical':critical,'response':answer,'calls':row['provider_calls']}),flush=True)
 write()
if __name__=='__main__': main()
