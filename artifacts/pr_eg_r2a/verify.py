"""Read-only evidence checks plus verification result artifact; no provider calls."""
import hashlib,json,re,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1]
def read(n):return json.loads((H/n).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
problems=[];before=read('protected_before.json');changed=[p for p,d in before.items() if sha(R/p)!=d]
problems.extend(changed)
for name,key in [('corpus.json','corpus_sha256'),('contexts.json','contexts_sha256')]:
 if sha(H/name)!=read('freeze.json')[key]:problems.append('frozen hash '+name)
corpus=read('corpus.json');ids=[c['id'] for c in corpus]
if len(ids)!=102 or len(set(ids))!=102:problems.append('corpus uniqueness/count')
records=[json.loads(s) for s in (H/'provider.jsonl').read_text(encoding='utf-8').splitlines()]
for record in records:
 if record.get('usage') and record['usage']['input_tokens']+record['usage']['output_tokens']!=record['usage']['total_tokens']:problems.append('usage '+record['trial'])
 if record['kind']=='C' and record['trial'].startswith(('C_holdout','C_repeat','C_single')):problems.append('stopped C continued')
 for msg in record['messages']:
  if any(k in msg['content'] for k in ['expected_classification','"rationale"','"expected"']):problems.append('gold prompt contamination '+record['trial'])
if not read('state_control.json')['final_worlds_equal']:problems.append('matched world control differs')
mixed=next(r for r in read('adoption_chat.json') if r['id']=='mixed01')
if not mixed['identical'] or mixed['offered_candidate'] not in json.dumps(mixed['delivered_exchanges'],ensure_ascii=False).replace('\\"','"'):problems.append('mixed delivery evidence')
manifest=json.loads((R/'handoff/REVIEW_MANIFEST.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(R/'handoff/CURRENT_REVIEW.zip') as archive:
 if archive.testzip():problems.append('zip CRC')
 names=archive.namelist()
 for item in manifest['included_files']:
  if item['bundle_path'] not in names:problems.append('missing '+item['bundle_path']);continue
  if item.get('sha256') and hashlib.sha256(archive.read(item['bundle_path'])).hexdigest()!=item['sha256']:problems.append('bundle hash '+item['bundle_path'])
 reports=[n for n in names if re.search(r'support/artifacts/pr_eg_r2a/\d\d_[^/]+\.md$',n)]
 if len(reports)!=25:problems.append('report count '+str(len(reports)))
 if any('/.env' in n or '/disposable_state/' in n or '/pytest_tmp/' in n for n in names):problems.append('excluded material included')
 for n in ['corpus.json','provider.jsonl','evaluation_measured_only.json','stop_C.json','state_control.json']:
  if 'support/artifacts/pr_eg_r2a/'+n not in names:problems.append('missing evidence '+n)
result=dict(campaign=manifest['campaign_id'],reports=len(reports),protected_files=len(before),changed=changed,provider_requests=len(records),corpus_hash=sha(H/'corpus.json'),zip_files=len(names),problems=problems)
(H/'bundle_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));raise SystemExit(bool(problems))
