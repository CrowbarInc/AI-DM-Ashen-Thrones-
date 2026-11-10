"""Offline entry-source comparison for the browser-discovered action refusal."""
import sys,json,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from artifacts.pr_play_67.http_harness import *
from game.models import ChatRequest,ActionRequest
spec=importlib.util.spec_from_file_location('game.pr67_entry_api',OUT/'entry_source/api.py')
entry=importlib.util.module_from_spec(spec);sys.modules[spec.name]=entry;spec.loader.exec_module(entry)
# Preserve the real owner's name for the unmodified domain guards. This module
# is an isolated entry-source instance of game.api, not a new state mutator.
entry.__dict__['__name__']='game.api'
rows=[]
for label,module in [('entry_source',entry),('repaired_source',api)]:
    with seed('browser_comparison_'+label,True) as mp:
        mp.setattr(module,'call_gpt',api.call_gpt)
        module.chat(ChatRequest(text='I examine the Notice board.'))
        module.chat(ChatRequest(text='I follow the missing patrol rumor.'))
        affordance=next(a for a in module.compose_state()['ui']['affordances'] if 'weathered milestone' in a['label'].lower())
        prompt=affordance.get('prompt') or affordance['metadata']['prompt']
        req=ActionRequest(action_type='exploration',intent=prompt,exploration_action={
            'id':affordance['id'],'label':affordance['label'],'type':affordance['type'],
            'targetSceneId':affordance.get('target_scene_id'),'targetEntityId':affordance.get('target_id'),
            'targetLocationId':affordance.get('target_location_id'),'prompt':prompt,'metadata':affordance.get('metadata',{})})
        result=module.action(req)
        rows.append(dict(source=label,request=req.model_dump(),narration=result['gm_output']['player_facing_text'],
                         journal=result['journal']['discovered_clues'],scene=storage.load_session()['active_scene_id']))
save('browser_entry_comparison.json',dict(rows=rows,same_narration=rows[0]['narration']==rows[1]['narration'],
     transport='offline Python action call; no unsafe entry-source HTTP pathway was reopened'))
print([r['narration'] for r in rows])
