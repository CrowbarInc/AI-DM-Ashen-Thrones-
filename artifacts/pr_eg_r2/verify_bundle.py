"""Read-only archive and experimental evidence integrity checks."""
import hashlib,json,re,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
manifest=json.loads((ROOT/'handoff/REVIEW_MANIFEST.json').read_text(encoding='utf-8'))
problems=[]
with zipfile.ZipFile(ROOT/'handoff/CURRENT_REVIEW.zip') as archive:
 if archive.testzip(): problems.append('ZIP CRC error')
 names=archive.namelist()
 for row in manifest['included_files']:
  if row['bundle_path'] not in names: problems.append('missing '+row['bundle_path']);continue
  if row.get('sha256') and hashlib.sha256(archive.read(row['bundle_path'])).hexdigest()!=row['sha256']:
   problems.append('hash '+row['bundle_path'])
 reportnames=[n for n in names if re.search(r'support/artifacts/pr_eg_r2/\d\d_[^/]+\.md$',n)]
 if len(reportnames)!=21: problems.append('numbered report count '+str(len(reportnames)))
 if any('/.env' in n or '/local_dependencies/' in n or '/disposable_state/' in n for n in names): problems.append('excluded tree included')
rows=[json.loads(s) for s in (HERE/'experiments.jsonl').read_text(encoding='utf-8').splitlines()]
for row in rows:
 prompt=json.loads((HERE/'prompts'/f"{row['trial_id']}.json").read_text(encoding='utf-8'))
 digest=hashlib.sha256(json.dumps(prompt,ensure_ascii=False).encode()).hexdigest()
 if digest!=row['prompt_sha256']: problems.append('prompt hash '+row['trial_id'])
 if row.get('usage') and row['usage']['input_tokens']+row['usage']['output_tokens']!=row['usage']['total_tokens']:
  problems.append('usage '+row['trial_id'])
before=json.loads((HERE/'protected_before.json').read_text(encoding='utf-8'))
changed=[p for p,d in before.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=d]
if changed: problems.extend(changed)
result={'campaign':manifest['campaign_id'],'numbered_reports':len(reportnames),'zip_files':len(names),
 'successful_matrix_trials':sum(not r.get('error') for r in rows),'transport_failures':sum(bool(r.get('error')) for r in rows),
 'protected_files_verified':len(before),'protected_files_changed':changed,'problems':problems}
(HERE/'bundle_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result));raise SystemExit(bool(problems))
