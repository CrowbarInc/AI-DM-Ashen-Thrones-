"""Capture entry provenance and freeze developer-authored cases before repair."""
import hashlib, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, value): (OUT/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
if __name__ == '__main__':
    assert not (OUT/'baseline.json').exists()
    sources=['game/api.py','game/api_ui_mode.py','game/state_channels.py','static/app.js','docs/NEXT_SESSION.md']
    (OUT/'entry_source').mkdir(exist_ok=True)
    for name in sources: (OUT/'entry_source'/Path(name).name).write_bytes((ROOT/name).read_bytes())
    roots=['data','artifacts/atgb','artifacts/pr_play_66']
    save('baseline.json',dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        status=subprocess.check_output(['git','status','--short'],text=True),
        protected={p.relative_to(ROOT).as_posix():sha(p) for r in roots for p in (ROOT/r).rglob('*') if p.is_file() and '__pycache__' not in p.parts}))
    cases=[]
    paths=[['session','gm_notes'],['world','gm_only'],['scene','scene','discoverable_clues'],['scene','scene','gm_notes'],['scene','scene','private_notes'],['campaign','character_secret'],['session','hidden_objectives'],['world','npcs'],['world','unvisited_locations'],['world','event_triggers'],['resolution','metadata'],['gm_output','provider_prompt'],['gm_output','validation'],['resolution','state_changes'],['session','future_content'],
        ['character','inventory',0,'metadata'],['character','inventory',0,'description'],['ui','affordances',0,'metadata','hidden'],['ui','scene_npcs',0,'motivation'],['journal','active_leads',0,'private_notes'],['scene','scene','summary'],['character','hp','unknown'],['ui','clues','known',0,'unknown'],['snapshots',0,'internal'],['world','projects',0,'summary']]
    for path in paths:
        cases.append(dict(id=f'H{len(cases)+1:02}',group='hidden' if len(cases)<15 else 'nested',path=path,value='HOLDOUT_SENTINEL_'+str(len(cases)+1),expected='absent'))
    for group, names in [('discovery',['unknown_clue','known_clue','new_clue','repeat','public_context']),('error',['exception','validation_input','error_metadata','fallback','malformed']),('frontend',['scene','character','inventory','affordances','session']),('isolation',['disabled','enabled','wrong_session','author','debug']),('preservation',['pure','session','world','scene','reload'])]:
        for name in names: cases.append(dict(id=f'H{len(cases)+1:02}',group=group,name=name,expected='safe_response_and_unchanged_authority'))
    save('frozen_holdout.json',cases)
    save('frozen_holdout_manifest.json',dict(cases=50,sha256=sha(OUT/'frozen_holdout.json'),developer_authored=True,independent_external_validation=False,frozen_before_implementation=True))
    print('Entry captured; 50 cases frozen.')
