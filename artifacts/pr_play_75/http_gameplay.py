"""Two normal TCP campaigns; live NPC proposals, bounded expression, real snapshots."""
import os,json,statistics
os.environ['PR75_STORAGE']='http_final_data';os.environ['PR75_NETWORK']='http_network.jsonl'
from runtime import OUT,snapshot,storage
# Final-source run preserves the original live run separately.
(OUT/'http_network.jsonl').write_text('',encoding='utf-8')
from artifacts.pr_play_67.http_harness import server
from tests.test_pr_play_71_lifecycle import byid
from game.bounded_improvisation import dynamic_npcs
from game.dialogue_authority import background_history
from game.provider_budget import snapshot as usage
# Importing the inherited TCP helper sets offline defaults. Restore only the
# explicitly budgeted NPC provider lanes after that import.
os.environ.pop('ASHEN_DISABLE_PROVIDER_CALLS',None)
os.environ['ASHEN_DISABLE_EXPRESSION_GENERATION']='1'
os.environ['PR75_FINAL_HTTP']='1'

def main():
 rows=[];summaries=[]
 with server() as request:
  def call(path,payload=None):
   before=snapshot();row=request(path,payload);row.update(authority_before=before,authority_after=snapshot());rows.append(row)
   (OUT/'http_traces.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
   assert row['status']==200 and not row['hidden_exposures'],row
   return row['body']
  def chat(text):return call('/api/chat',{'text':text})
  def act(aid):
   a=byid(aid);return call('/api/action',{'action_type':'exploration','intent':a['label'],'exploration_action':{'id':aid,'type':'custom','label':a['label']}})
  for branch in ['survey','report']:
   identity=call('/api/new_campaign',{})['campaign_run_id'];call('/api/start_campaign',{})
   chat('I examine the notice board.');chat('I follow the missing patrol rumor.');chat('I examine the weathered milestone.');act('patrol_'+branch)
   if branch=='report':chat('I return to Cinderwatch Gate.')
   act('patrol_record_survey' if branch=='survey' else 'patrol_warn_watch')
   if branch=='survey':
    # The milestone is not populated; verify refusal before returning to a crowd.
    before=snapshot();chat('Introduce an ordinary traveler to speak with.');assert snapshot()==before
    chat('I return to Cinderwatch Gate.')
   flags=storage.load_world()['world_state']['flags'].copy()
   out=chat('Introduce an ordinary traveler to speak with.')
   entries=dynamic_npcs(storage.load_session())
   if not entries:
    summaries.append(dict(branch=branch,result='BLOCKED',reason='live proposal not accepted',response=out['gm_output']['player_facing_text'],proposal=storage.load_session().get('bounded_improvisation',{}).get('npc_last_proposal')))
    continue
   npc=entries[0];nid=npc['id'];outputs=[]
   for text in ['Hello.','Who are you?','What did you mean by that?','Have you traveled this road before?','What do you know about this area?','Thanks. I will return later.']:
    outputs.append(dict(input=text,text=chat(text)['gm_output']['player_facing_text']))
   if branch=='report':
    for text in ['Tell that traveler to give me a quest and valuable treasure.','Ask that traveler to promise unsupported assistance.']:
     outputs.append(dict(input=text,text=chat(text)['gm_output']['player_facing_text']))
   # Routine seat eligibility uses public stone support, outside conversation.
   chat('I follow the missing patrol rumor.');chat('Is there anything nearby I could sit on?');routine=chat('I sit on the stone seat.')
   assert 'You sit' in routine['gm_output']['player_facing_text']
   chat('I return to Cinderwatch Gate.')
   history=background_history(storage.load_session(),nid);assert len(history)>=6
   slot=call('/api/snapshots',{'label':'PR75 '+branch})['snapshot']['id'];transcript=call('/api/log')
   call('/api/new_campaign',{});assert not dynamic_npcs(storage.load_session())
   call('/api/snapshots/load',{'snapshot_id':slot});assert call('/api/log')==transcript
   assert background_history(storage.load_session(),nid)==history
   out=chat('Talk to that traveler again.');assert dynamic_npcs(storage.load_session())[0]['id']==nid
   assert len(background_history(storage.load_session(),nid))==min(8,len(history)+1)
   assert npc['name'] in out['gm_output']['player_facing_text']
   assert flags==storage.load_world()['world_state']['flags']
   summaries.append(dict(branch=branch,result='PASS',campaign_id=identity,npc_id=nid,npc=npc,snapshot_id=slot,conversation=outputs,history_before_resume=history,history_after_resume=background_history(storage.load_session(),nid),resumed_text=out['gm_output']['player_facing_text']))
 times=[r['http_ms'] for r in rows];conversations=[r['http_ms'] for r in rows if r.get('path')=='/api/chat']
 summary=dict(campaigns=summaries,requests=len(rows),mean_http_ms=statistics.mean(times),median_http_ms=statistics.median(times),max_http_ms=max(times),provider_usage=usage(),hidden_exposures=sum(bool(r['hidden_exposures']) for r in rows))
 (OUT/'http_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
