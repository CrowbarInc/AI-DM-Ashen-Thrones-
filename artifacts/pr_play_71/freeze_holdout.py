import json,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent
rows=[]
groups={
'start':['normal','duplicate','new_twice','failure_retry','timeout_retry','empty_retry','malformed_retry','refresh_before','identity','safe'],
'persistence':['scene','journal','inventory','character','session','actions','followup','reload','switch','continue'],
'continuity':['choice','exclusive','followup','duplicate_choice','opposite','duplicate_followup','resume_choice','resume_followup','post_resume_opposite','post_resume_continue'],
'isolation':['identity','flags','journal','inventory','selection'],
'publication':['rejected','empty','malformed','timeout','unavailable'],
'projection':['creation','opening','gameplay','resume','invalid'],
'recovery':['missing_id','invalid_id','corrupt_snapshot','incomplete_snapshot','stale_resume']}
for group,variants in groups.items():
 for j,v in enumerate(variants):
  branch='survey' if j%2==0 else 'report'
  rows.append(dict(id=f'H{len(rows)+1:02}',group=group,variant=v,branch=branch,expected={'opening_scene':'frontier_gate','branch_flag':'patrol_'+branch,'opposite_absent':'patrol_'+('report' if branch=='survey' else 'survey'),'followup_flag':'patrol_survey_recorded' if branch=='survey' else 'patrol_guards_warned','campaign_identity':'distinct on creation; same on resume','safe':'no CANARY_ or raw hidden fields','publication':'trusted discovery and consequence text preserved','failure':'prior valid state preserved; no fabricated success'}))
raw=(json.dumps(rows,indent=2)+'\n').encode()
with (OUT/'frozen_holdout.json').open('xb') as f:f.write(raw)
(OUT/'frozen_holdout_manifest.json').write_text(json.dumps(dict(cases=len(rows),sha256=hashlib.sha256(raw).hexdigest(),authorship='developer-authored; not independent external validation',execution='once after source freeze',fixtures='normal creation and start HTTP; offline provider fixture; no runtime seeding; variants fixed before production edits'),indent=2))
