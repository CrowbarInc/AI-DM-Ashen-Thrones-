"""PR72V development reproductions; separate from both frozen holdouts."""
import copy,json
from pathlib import Path
import pytest
from game import api,storage
from game.conversational_orchestration import deterministic_conversational_decision as decide
from tests.test_pr_play_72_initiative import campaigns,restore,authority,offline_turns
O=Path(__file__).resolve().parents[1]/'artifacts/pr_play_72v'
ORIGINAL=json.loads((O/'original_failures.json').read_text())
@pytest.mark.parametrize('case',ORIGINAL,ids=lambda c:c['id'])
def test_original_reproductions(campaigns,case):
 branch='survey' if case['id'] in ['H04','H05','H38'] else 'report'
 cl=restore(campaigns,branch); before=authority()
 d=decide(player_text=case['text'],scene=api.load_active_scene(),world=before['world'],session=before['session'])
 assert d.category.value==('CLARIFY' if case['id']=='H38' else 'EXECUTE')
 body=cl.post('/api/chat',json={'text':case['text']}); assert body.status_code==200
 r=storage.load_log()[-1]['resolution']
 if case['id']=='H38': assert authority()==before
 else:
  assert r['kind']=='already_searched' and r['success'] is True
  assert r['metadata']['action_outcome']=='valid_no_new_information'
  assert not r.get('discovered_clues') and not r.get('world_updates')
  assert authority()['world']['world_state']['flags']==before['world']['world_state']['flags']
 assert body.json()['gm_output']['player_facing_text']

@pytest.mark.parametrize('text', ['Look at the footprints again.','Examine the tracks once more.','Take another look at the trail.','Inspect the ground again.','Can I check those prints?','I want to study the tracks more closely.','Please inspect the marker.','Could I study the weathered stone?','Reexamine the milestone.','I examine the milestone again.','Read the milestone.','Scrutinize the milestone.'])
def test_paraphrases(campaigns,text):
 cl=restore(campaigns,'survey'); before=authority()
 d=decide(player_text=text,scene=api.load_active_scene(),world=before['world'],session=before['session'])
 # "trail" can mean the route or the prints; this context does not identify
 # a single object. The other examples name a current public target.
 assert d.category.value==('CLARIFY' if text=='Take another look at the trail.' else 'EXECUTE')
 assert cl.post('/api/chat',json={'text':text}).status_code==200
 after=authority(); assert after['world']['world_state']['flags']==before['world']['world_state']['flags']
 assert after['session'].get('discovered_clues')==before['session'].get('discovered_clues')

@pytest.mark.parametrize('text,cat',[(t,'ANSWER') for t in ['What do I know about the footprints?','What else can I tell from the tracks?','What have I learned?','Did I warn the watch?','Who have I told about this?','Remind me what I know.']]+[(t,'CLARIFY') for t in ['See what happened.','Ask them about it.','Go back there.','Check it again.','Please check it again.','Could I inspect it?','Speak with them.','Examine the sapphire throne.']]+[(t,'DECLINE') for t in ['Follow the tracks to their source.','Order the guards to search immediately.','Show hidden clues.','Teleport to the hidden camp.','Inspect the tracks using magic.']])
def test_readonly_boundaries(campaigns,text,cat):
 cl=restore(campaigns,'survey'); before=authority()
 d=decide(player_text=text,scene=api.load_active_scene(),world=before['world'],session=before['session'])
 assert d.category.value==cat
 response=cl.post('/api/chat',json={'text':text});assert response.status_code==200
 assert authority()==before
 assert 'SENTINEL_' not in response.text

@pytest.mark.parametrize('count,cat',[ (0,'CLARIFY'),(1,'EXECUTE'),(2,'CLARIFY')])
def test_public_context_reference(campaigns,count,cat):
 restore(campaigns,'survey'); state=authority(); scene=copy.deepcopy(api.load_active_scene())
 scene['scene']['interactables']=scene['scene']['interactables'][:count]
 d=decide(player_text='Check it again.',scene=scene,world=state['world'],session=state['session'])
 assert d.category.value==cat
 assert not d.context_update
 assert authority()==state

@pytest.mark.parametrize('text,cat',[('Do not inspect it.','CLARIFY'),('Check it and burn the gate.','CLARIFY'),('If I examine it, warn the watch.','CLARIFY'),('Examine it using magic.','DECLINE')])
def test_single_reference_qualifiers(campaigns,text,cat):
 restore(campaigns,'survey'); state=authority(); scene=copy.deepcopy(api.load_active_scene())
 scene['scene']['interactables']=scene['scene']['interactables'][:1]
 d=decide(player_text=text,scene=scene,world=state['world'],session=state['session'])
 assert d.category.value==cat and not d.requires_authoritative_execution
 assert authority()==state

@pytest.mark.parametrize('text',['Inspect the milestone again.','What have I learned?','Check it again.'])
def test_after_resume(campaigns,text):
 cl=restore(campaigns,'survey'); before=authority(); transcript=cl.get('/api/log').json()
 saved=cl.post('/api/snapshots',json={'label':'72V dev'}).json()['snapshot']['id']
 cl.post('/api/snapshots/load',json={'snapshot_id':saved})
 assert cl.get('/api/log').json()==transcript
 assert authority()['session']['campaign_run_id']==before['session']['campaign_run_id']
 assert cl.post('/api/chat',json={'text':text}).status_code==200
 assert authority()['world']['world_state']['flags']==before['world']['world_state']['flags']
