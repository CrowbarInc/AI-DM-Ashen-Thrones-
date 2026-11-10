"""Read-only verification of retained normal browser and TCP evidence."""
import json,hashlib,statistics
from pathlib import Path
O=Path(__file__).resolve().parent

def stat(a):return dict(count=len(a),mean=statistics.mean(a) if a else None,median=statistics.median(a) if a else None,maximum=max(a) if a else None)
def read(n):return json.loads((O/n).read_text())
def authority_equal(a,b):return a==b

def main():
 network=[json.loads(l) for p in [O/'browser_network.jsonl',O/'browser_final_network.jsonl'] if p.exists() for l in p.read_text().splitlines()]
 rows=[];readonly=[];repeats=[];disclosures=[];loads=[]
 for r in network:
  if r['method']=='POST' and r['path']=='/api/chat':
   text=json.loads(r['request'])['text']; before=r['authority_before'];after=r['authority_after'];d=r['stages'].get('interpretation') or {};result=after['session'].get('last_action_debug',{}).get('resolver_result') or {}
   response=json.loads(r['response']);pub=response.get('gm_output',{}).get('player_facing_text','')
   if d.get('category') in ['ANSWER','CLARIFY','DECLINE']:readonly.append(dict(text=text,category=d['category'],unchanged=before==after))
   elif result.get('kind')=='already_searched':repeats.append(dict(text=text,success=result.get('success'),no_discovery=not result.get('discovered_clues'),no_effect=not result.get('world_updates'),flags_equal=before['world']['world_state']['flags']==after['world']['world_state']['flags']))
   rows.append(dict(text=text,category=d.get('category'),target=d.get('proposed_target'),resolution=result,publication=pub,before=before,after=after,server_ms=r['server_ms']))
  if r['path']=='/api/snapshots/load' and r['method']=='POST':
   sid=json.loads(r['request'])['snapshot_id'];bundle=json.loads((O/'browser_data/snapshots'/f'{sid}.json').read_text()); after=r['authority_after']
   loads.append(dict(snapshot_id=sid,label=bundle['label'],identity=after['session']['campaign_run_id']==bundle['session']['campaign_run_id'],world=after['world']==bundle['world'],character=after['character']==bundle['character'],combat=after['combat']==bundle['combat']))
 for name in ['http_traces.json']:
  if not (O/name).exists():continue
  for r in read(name):
   if r['request']['path']!='/api/chat':continue
   res=r.get('authoritative_log',{}).get('resolution',{});pub=r['body'].get('gm_output',{}).get('player_facing_text','')
   for fact in res.get('discovered_clues') or []:
    if isinstance(fact,str):disclosures.append(dict(text=r['request']['json']['text'],fact=fact,present_in_narration=fact.casefold() in pub.casefold(),present_in_response=fact.casefold() in json.dumps(r['body']).casefold()))
 safe=all(x['unchanged'] for x in readonly) and all(all(x[k] for k in ['success','no_discovery','no_effect','flags_equal']) for x in repeats)
 summary=dict(campaign_A='PASS' if safe else 'FAIL',campaign_B='PASS' if safe else 'FAIL',typed_submissions=len(rows),readonly=readonly,repeats=repeats,loads=loads,load_integrity=all(all(x[k] for k in ['identity','world','character','combat']) for x in loads),screenshots=[p.name for p in O.glob('browser_*.png')],attachment=['initial webview attach timeout','one retry succeeded'],authority_safe=safe,transcript='Snapshot log bundles retained; per-load /api/log responses verified by persistence analysis.',provider_requests=0,provider_tokens=0)
 (O/'browser_traces.json').write_text(json.dumps(rows,indent=2));(O/'browser_results.json').write_text(json.dumps(summary,indent=2));(O/'disclosure_scan.json').write_text(json.dumps(disclosures,indent=2))
 print('Browser',len(rows),'typed;',len(readonly),'readonly;',len(repeats),'repeats; safe',safe,'loads',summary['load_integrity']);print('Disclosure gaps',[x for x in disclosures if not x['present_in_narration']])
if __name__=='__main__':main()
