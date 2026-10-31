"""Record adversarial reconciliation at the production bridge, without provider calls."""
from pathlib import Path
import sys,json,copy
sys.path.insert(0,str(Path.cwd()))
import pytest
from tests.test_pr_eg_r2c_r2_reference_eligibility import record, Q, FACT
from tests.test_pr_ef_gm_authority import seed_scene
from game import storage
from game.player_interpretation_bridge import reconcile_reference_annotations, normalized_action_from_interpretation
H=Path(__file__).parent
cases=[
 ('A_false_subject',Q,['north gate'],'sergeant_mara'),
 ('B_false_addressee',Q,['Sergeant Mara'],'sergeant_mara'),
 ('C_correct_subject','I ask Sergeant Mara about that place.',['that place'],'sergeant_mara'),
 ('D_correct_addressee','I ask one of them about the north gate.',['one of them'],'sergeant_mara'),
 ('E_multiple',Q,['Sergeant Mara','north gate'],'sergeant_mara'),
 ('F_wrong_entity',Q,['obsidian palace'],'sergeant_mara'),
 ('G_irrelevant_noun',Q,['weather'],'sergeant_mara'),
 ('H_unknown_answer','I ask Sergeant Mara who made the north gate.',['north gate'],'sergeant_mara'),
 ('I_hidden_answer','I ask Sergeant Mara what the north gate password is.',['north gate'],'sergeant_mara'),
 ('J_tempting_default','I ask one of them about that place.',['one of them','that place'],'sergeant_mara'),
 ('K_subject_conflict',Q,['south tower'],'sergeant_mara'),
 ('L_unauthorized_npc',Q,['north gate'],'corporal_bren'),
]
rows=[]
with pytest.MonkeyPatch.context() as mp:
 seed_scene(H/'adversarial_state',mp)
 w=storage.load_world();npc=next(n for n in w['npcs'] if n['id']=='sergeant_mara');npc['topics'].append(dict(id='night_watch',text=FACT))
 other=copy.deepcopy(npc);other.update(id='corporal_bren',name='Corporal Bren');w['npcs'].append(other)
 s=storage.load_active_scene();ss=storage.load_session()
 for name,q,refs,target in cases:
  raw=record(refs,target);raw['communication']['subject']='south tower' if name.startswith('K') else 'provider-supplied subject'
  before=copy.deepcopy((raw,s,w,ss));out,e=reconcile_reference_annotations(raw,player_text=q,scene=s,world=w,session=ss)
  action,meta=normalized_action_from_interpretation(out,player_text=q,scene=s,world=w,session=ss)
  assert (raw,s,w,ss)==before
  expected_allowed=name[0] in 'ABEFGHIKL'
  passed=bool(action)==expected_allowed
  if action:passed=passed and action['target_id']=='sergeant_mara'
  rows.append(dict(id=name,player=q,raw_record=raw,reconciled_record=out,decisions=e,normalized_action=action,bridge=meta,expected_allowed=expected_allowed,passed=passed))
(H/'adversarial_annotations.json').write_text(json.dumps(rows,indent=2))
print([(r['id'],r['passed']) for r in rows])
