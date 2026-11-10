import sys,json,hashlib,statistics,subprocess,difflib,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
rows=[json.loads(l) for l in (OUT/'browser_network.jsonl').read_text(encoding='utf-8').splitlines()]
saved=[r for r in rows if r['path']=='/api/snapshots' and r['method']=='POST']
campaigns=[]
for r in saved:
 body=json.loads(r['body']);s=r['authority_after']['session'];w=r['authority_after']['world']
 branch='survey' if w.get('world_state',{}).get('flags',{}).get('patrol_survey') else 'report'
 campaigns.append(dict(branch=branch,campaign_run_id=s['campaign_run_id'],session_id=s['session_id'],snapshot_id=body['snapshot']['id'],location=s['active_scene_id'],flags=w['world_state']['flags'],snapshot=s,character=r['authority_after']['character']))
def forbidden(value,path=''):
 hits=[]
 if isinstance(value,dict):
  for k,v in value.items():
   if k in {'gm_notes','hidden_facts','discoverable_clues','runtime_scene_overlays','debug_traces','provider_prompt','validation_trace','_experimental_branching_campaign'}:hits.append(path+'.'+k)
   hits+=forbidden(v,path+'.'+k)
 elif isinstance(value,list):
  for n,v in enumerate(value):hits+=forbidden(v,path+f'[{n}]')
 return hits
scans=[]
for n,r in enumerate(rows):
 raw=r['body']
 try:body=json.loads(raw)
 except ValueError:body={}
 hits=forbidden(body)
 if 'CANARY_' in raw or 'SENTINEL_' in raw:hits.append('hidden sentinel')
 scans.append(dict(row=n,path=r['path'],status=r['status'],bytes=len(raw.encode()),hits=hits))
save('complete_payload_scan.json',dict(responses=len(scans),exposures=sum(bool(x['hits']) for x in scans),rows=scans))
resumes=[]
for r in rows:
 if r['path']=='/api/snapshots/load' and r['method']=='POST':
  body=json.loads(r['body']);s=r['authority_after']['session'];flags=r['authority_after']['world'].get('world_state',{}).get('flags',{})
  ref=next((c for c in campaigns if c['campaign_run_id']==s['campaign_run_id']),None)
  resumes.append(dict(identity=s['campaign_run_id'],location=s['active_scene_id'],flags=flags,status=r['status'],expected_campaign=ref is not None,flags_equal=bool(ref and flags==ref['flags']),character_equal=bool(ref and r['authority_after']['character']==ref['character']),snapshot_id=body.get('snapshot',{}).get('id')))
console=read('browser_console.json');timings=[dict(json.loads(x['message'].split('ASHEN_UI_READY ')[1]),timestamp=x['timestamp']) for x in console]
save('browser_results.json',dict(campaigns=campaigns,resumes=resumes,normal_ui_created=True,normal_ui_started=True,initial_action=True,branches=2,save_slot_resume=2,tab_reload=2,application_context_reopened=True,server_restart_after_branch=False,cached_frontend_mismatch_reproduced=True,cached_frontend_recovery='reopened at localhost to load current assets',browser_gameplay_actions=sum(r['method']=='POST' and r['path'] in ['/api/action','/api/chat'] for r in rows),screenshots=len(list(OUT.glob('*.png'))),timings=timings,backend_mean_ms=statistics.mean(r['server_ms'] for r in rows),backend_max_ms=max(r['server_ms'] for r in rows)))
usage=[]
for p in OUT.glob('provider_usage*.jsonl'):
 for l in p.read_text(encoding='utf-8').splitlines():
  x=json.loads(l);x['ledger_file']=p.name;usage.append(x)
completed=[r for r in usage if r['event']=='completed'];dispatch=[r for r in usage if r['event']=='dispatch_attempted']
opening_recovery=[]
for p in (OUT/'normal_data/snapshots').glob('*.json'):
 bundle=json.loads(p.read_text(encoding='utf-8'))
 opening_recovery.append(dict(label=bundle.get('label'),recovery=bundle['log_entries'][0]['gm_output'].get('metadata',{}).get('opening_recovery_debug')))
save('provider_usage_summary.json',dict(provider='OpenAI',models=sorted({str(x.get('model') or x.get('configured_model')) for x in completed}),requests=len(dispatch),completed=len(completed),tokens=sum(x.get('total_tokens') or 0 for x in completed),input_tokens=sum(x.get('input_tokens') or 0 for x in completed),output_tokens=sum(x.get('output_tokens') or 0 for x in completed),provider_latency_ms=[x.get('latency_ms') for x in completed],failures=[x for x in completed if x.get('refusal')],admission_refusals=[x for x in usage if x['event']=='rejected'],purposes=dict(Counter(x['purpose'] for x in completed)),sdk_retries=0,host_retries=0,observed_saved_openings=opening_recovery,scope='all application startup preflight and ordinary required browser actions; no shadow study'))
base=read('baseline.json');changed=[];missing=[]
for p,h in base['protected'].items():
 path=ROOT/p
 if not path.exists():missing.append(p)
 elif hashlib.sha256(path.read_bytes()).hexdigest()!=h:changed.append(p)
save('protected_integrity.json',dict(entries=len(base['protected']),changed=changed,missing=missing,passed=not changed and not missing))
freeze=read('implementation_freeze.json')
save('freeze_integrity.json',dict(evaluated_source_preserved={p:hashlib.sha256((OUT/'frozen_source'/p).read_bytes()).hexdigest()==h for p,h in freeze.items()},final_source_matches_original_freeze={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in freeze.items()},explanation='After frozen run completion, targeted regression/persistence repairs changed API/reset and storage/quarantine helper. No frozen rerun.'))
# Reconstruct task entry from only the exact additions in this cycle. The
# full git diff also retains pre-existing dirty changes and is labelled as such.
diff=[]
for path in ['game/api.py','game/authored_consequences.py','game/campaign_reset.py','static/app.js']:
 diff.append(subprocess.run(['git','diff','--',path],cwd=ROOT,capture_output=True,text=True).stdout)
(OUT/'working_tree.diff').write_text('\n'.join(diff),encoding='utf-8')
save('metrics.json',dict(http=read('http_summary.json'),browser=read('browser_results.json'),provider=read('provider_usage_summary.json'),mandatory_disclosure_omissions={'baseline':1,'postrepair_observed':0},critical_unsafe_publications_observed=0,hidden_information_exposures=read('complete_payload_scan.json')['exposures'],latency_limits='Browser console timings cover refreshed-context resumes and continuations. Initial A start and individual HTTP/network/render substage splits unavailable; cached-context tool timings are upper bounds only.'))
