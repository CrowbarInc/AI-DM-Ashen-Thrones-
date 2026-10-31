"""Read-only verification of protected state, frozen labels, metrics and packaged evidence."""
import hashlib,json,re,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1]
def read(n):return json.loads((H/n).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
problems=[];before=read('protected_before.json');changed=[p for p,h in before.items() if sha(R/p)!=h];problems.extend(changed)
for name,key in [('corpus.json','corpus_sha256'),('supplement.json','supplement_sha256')]:
 if sha(H/name)!=read('freeze.json')[key]:problems.append('frozen hash '+name)
if (H/'corpus.json').read_bytes()!=(H/'predecessor/corpus.json').read_bytes():problems.append('historical labels changed')
assert len(read('corpus.json'))==102 and len(read('semantic_results.json'))==112
assert len(read('adoption_probes.json'))==10
raw=[json.loads(l) for l in (H/'provider.jsonl').read_text(encoding='utf-8').splitlines()]
for row in raw:
 if row.get('usage') and row['usage']['input_tokens']+row['usage']['output_tokens']!=row['usage']['total_tokens']:problems.append('usage '+row['trial'])
 if any('"expected"' in m['content'] or '"rationale"' in m['content'] for m in row['messages']):problems.append('label leakage '+row['trial'])
exact=read('exact_reconstruction.json');unsafe=exact['trials'][1]
if not exact['final_worlds_equal']:problems.append('matched world control')
if 'north gate unattended' not in unsafe['response']['gm_output']['player_facing_text']:problems.append('leak not reproduced')
if 'north gate unattended' not in json.dumps(unsafe['saved_context']):problems.append('history evidence missing')
manifest=json.loads((R/'handoff/REVIEW_MANIFEST.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(R/'handoff/CURRENT_REVIEW.zip') as archive:
 if archive.testzip():problems.append('CRC')
 names=archive.namelist()
 for item in manifest['included_files']:
  p=item['bundle_path']
  if p not in names:problems.append('missing '+p)
  elif item.get('sha256') and hashlib.sha256(archive.read(p)).hexdigest()!=item['sha256']:problems.append('hash '+p)
 reports=[n for n in names if re.search(r'support/artifacts/pr_eg_r2b/\d\d_[^/]+\.md$',n)]
 if len(reports)!=24:problems.append('report count '+str(len(reports)))
 if any('/disposable_state/' in n or '/pytest_tmp/' in n or '/.env' in n for n in names):problems.append('excluded material')
 for n in ['provider.jsonl','corpus.json','supplement.json','metrics.json','exact_reconstruction.json','adoption_probes.json','interactive_latency.json','focused_junit.xml']:
  if 'support/artifacts/pr_eg_r2b/'+n not in names:problems.append('missing evidence '+n)
result=dict(campaign=manifest['campaign_id'],reports=len(reports),protected_files=len(before),changed=changed,provider_attempts=len(raw),provider_complete=sum(not r.get('error') for r in raw),zip_files=len(names),problems=problems)
(H/'bundle_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));raise SystemExit(bool(problems))
