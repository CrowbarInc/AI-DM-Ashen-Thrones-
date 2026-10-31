"""Controlled seam adoption with real storage round trips (not fresh provider)."""
import copy,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];sys.path.insert(0,str(R))
os.environ.update(ASHEN_DISABLE_PROVIDER_CALLS='1',ASHEN_DISABLE_LIVE_INTERPRETATION='1',ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1')
import pytest
from tests.test_pr_ef_gm_authority import seed_scene
from tests.test_pr_eg_r2c_speech_adoption import resolution,adopt
from game import storage
from game.conversational_continuity import record_delivered_exchange
from game.dialogue_authority import remember_dialogue_commitment
rows=[]
cases=[
 ('factual','What road?','The street beyond the gate is called the north road.','The north road has a secret tunnel.'),
 ('preference','Do you prefer morning or evening?','','I prefer evening because guards leave the north gate unattended.'),
 ('consequential','Do guards watch the north gate?','Guards watch the north gate throughout the night.','The guards abandon it at midnight.'),
 ('rejected_security','What do you personally enjoy about evening?','','The gate is never guarded.'),
 ('superseded','Which road?','The street beyond the gate is called the north road.','Stranger says, "I promise you a reward."'),
 ('clarification_resolution','What is the road called?','The street beyond the gate is called the north road.','The road leads to a secret vault.'),
]
for case,q,fact,candidate in cases:
 with pytest.MonkeyPatch.context() as mp:
  seed_scene(H/'disposable_state'/'persistence'/case,mp)
  world_before=copy.deepcopy(storage.load_world());session=storage.load_session()
  res=resolution(q,fact,session);out=adopt(res,q,candidate,session);accepted=out['metadata']['accepted_response']
  remember_dialogue_commitment(session,social=res['social'],player_text=q,line=out['player_facing_text'])
  record_delivered_exchange(session,player_text=q,delivered_text=out['player_facing_text'],social=res['social'],adoption=accepted)
  storage.save_session(session);loaded=storage.load_session()
  assert loaded['conversational_context']==session['conversational_context']
  assert candidate not in json.dumps(loaded['conversational_context'])
  continuation=[]
  if case=='clarification_resolution':
   for _ in range(2):
    question='What did you mean by that?';follow_res=resolution(question,session=loaded)
    follow=adopt(follow_res,question,'A secret passage.',loaded)
    assert 'north road' in follow['player_facing_text']
    record_delivered_exchange(loaded,player_text=question,delivered_text=follow['player_facing_text'],social=follow_res['social'],adoption=follow['metadata']['accepted_response'])
    storage.save_session(loaded);loaded=storage.load_session();continuation.append(follow)
  assert storage.load_world()==world_before
  rows.append(dict(id=case,evidence='controlled adoption + actual storage',candidate=candidate,adoption=accepted,context_after_load=loaded['conversational_context'],canonical_world_unchanged=True,continuation=continuation,passed=True))
(H/'persistence_results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(dict(passed=len(rows))))
