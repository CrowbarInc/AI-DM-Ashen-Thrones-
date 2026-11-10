"""Entry provenance and pre-implementation developer holdout freeze."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
    assert not (OUT/'baseline.json').exists()
    sources=['game/api.py','game/integrated_investigation_narration.py','docs/NEXT_SESSION.md','static/app.js']
    (OUT/'entry_source').mkdir(exist_ok=True)
    for n in sources:(OUT/'entry_source'/Path(n).name).write_bytes((ROOT/n).read_bytes())
    save('baseline.json',dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),status=subprocess.check_output(['git','status','--short'],text=True),protected={p.relative_to(ROOT).as_posix():sha(p) for r in ['data','artifacts/atgb','artifacts/pr_play_65','artifacts/pr_play_66','artifacts/pr_play_67'] for p in (ROOT/r).rglob('*') if p.is_file() and '__pycache__' not in p.parts}))
    cases=[]
    groups={
      'structured':['accepted','rejected','empty','malformed','unavailable','timeout','FAIL','REVIEW_REQUIRED','VALIDATION_ERROR','legacy_refusal'],
      'equivalence':['notice','milestone','notice_empty','milestone_empty','notice_timeout','milestone_timeout','notice_unsafe','milestone_unsafe','notice_duplicate','milestone_duplicate'],
      'safe':['You examine the weathered milestone.','You inspect the weathered milestone.','You study the weathered milestone.','You focus on the weathered milestone.','You examine the weathered milestone carefully.','You take a moment to examine the weathered milestone.','You pause to inspect the weathered milestone.','You turn your attention to the weathered milestone.','You look more closely at the weathered milestone.','You give the weathered milestone your attention.'],
      'unsafe':['The gate is permanently open.','You acquire a silver key.','The captain dies.','You discover a second patrol route.','Three prints lead southeast.','The milestone crumbles forever.','You gain ten gold.','The patrol has been killed.','A hidden passage opens.','You travel to the crystal palace.'],
      'duplicate':['exact','expanded','contradicted','historical','atmospheric'],
      'projection':['session','world','scene','unknown','nested']}
    for group,values in groups.items():
      for value in values:
        cases.append(dict(id=f'H{len(cases)+1:02}',group=group,input=value,scene='frontier_gate' if str(value).startswith('notice') else 'old_milestone',mandatory='The missing patrol was last seen taking the northwest mud track past the crates.' if str(value).startswith('notice') else 'Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.',expected_optional='published' if group=='safe' or (group=='structured' and value=='accepted') or (group=='duplicate' and value=='atmospheric') or (group=='equivalence' and value in ['notice','milestone']) else 'fallback',expected_authority='one resolution; one authorized discovery; no narration mutation',expected_response='mandatory verbatim; no hidden values; optional only if validated'))
    save('frozen_holdout.json',cases)
    save('frozen_holdout_manifest.json',dict(cases=len(cases),sha256=sha(OUT/'frozen_holdout.json'),developer_authored=True,independent_external_validation=False,frozen_before_implementation=True))
