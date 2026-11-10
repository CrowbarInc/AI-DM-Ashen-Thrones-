"""Separate post-holdout safety development; never rerun the frozen cases."""
import copy
import pytest
from game import api,storage
from game.conversational_orchestration import deterministic_conversational_decision as decide
from tests.test_pr_play_72_initiative import campaigns,restore,authority,offline_turns
@pytest.mark.parametrize('branch',['survey','report'])
@pytest.mark.parametrize('text',['Have the guards searched?','Did I record the survey?','Has the watch searched the road?','Did we inspect the tracks?','Was the patrol found?','Are the guards searching?','Where is the missing patrol?','Tell me where the missing patrol is.','What was discovered?'])
def test_auxiliary_questions_readonly(campaigns,monkeypatch,branch,text):
 cl=restore(campaigns,branch);before=authority()
 def forbidden(*a,**k):raise AssertionError('Read-only inquiry must not resolve an action')
 monkeypatch.setattr(api,'_resolve_engine_noncombat_seam',forbidden)
 d=decide(player_text=text,scene=api.load_active_scene(),world=before['world'],session=before['session'])
 assert d.category.value=='ANSWER'
 r=cl.post('/api/chat',json={'text':text});assert r.status_code==200
 assert authority()==before
 assert r.json()['gm_output']['player_facing_text']
@pytest.mark.parametrize('text',['Please study that weathered stone.','Examine this weathered milestone.','Read that old milestone.'])
def test_demonstrative_named_target(campaigns,text):
 restore(campaigns,'survey');s=authority();d=decide(player_text=text,scene=api.load_active_scene(),world=s['world'],session=s['session'])
 assert d.category.value=='EXECUTE' and d.proposed_target=='milestone'
 assert authority()==s

@pytest.mark.parametrize('branch',['survey','report'])
@pytest.mark.parametrize('text',['Search the hidden camp.','Can the trail be followed?','Can I follow the trail?','Follow the trail to its source.'])
def test_unsupported_objectives_readonly(campaigns,branch,text):
 cl=restore(campaigns,branch);before=authority()
 d=decide(player_text=text,scene=api.load_active_scene(),world=before['world'],session=before['session'])
 assert d.category.value=='DECLINE'
 assert cl.post('/api/chat',json={'text':text}).status_code==200
 assert authority()==before
