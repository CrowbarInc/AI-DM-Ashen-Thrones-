"""One execution of the 50-case developer-authored PR72V frozen holdout."""
import os
os.environ['PR72V_STORAGE']='holdout_data';os.environ['PR72V_NETWORK']='holdout_network.jsonl'
from runtime import *
from artifacts.pr_play_67.http_harness import server
import hashlib,statistics

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 manifest=json.loads((OUT/'frozen_holdout_manifest.json').read_text())
 assert digest(OUT/'frozen_holdout.json')==manifest['sha256']
 assert digest(OUT/'frozen_start_states.json')==manifest['states_sha256']
 with (OUT/'holdout_started.json').open('x') as f:json.dump({'executions':1,'time':time.time(),'final_source':{str(p):digest(p) for p in [ROOT/'game/player_initiative.py',ROOT/'game/exploration.py']}},f)
 cases=json.loads((OUT/'frozen_holdout.json').read_text());slots=json.loads((OUT/'holdout_slots.json').read_text())
 starts=json.loads((OUT/'frozen_start_states.json').read_text()); results=[]
 with server() as request:
  for case in cases:
   loaded=request('/api/snapshots/load',{'snapshot_id':slots[case['branch']]}); assert loaded['status']==200
   before=snapshot(); oldlog=storage.load_log(); row=request('/api/chat',{'text':case['text']});after=snapshot(); log=storage.load_log()[-1]
   capture=json.loads((OUT/'holdout_network.jsonl').read_text().splitlines()[-1]);d=capture['stages'].get('interpretation') or {}; r=log.get('resolution') or {}
   e=case['expected']; published=row['body'].get('gm_output',{}).get('player_facing_text','')
   checks=dict(http=row['status']==200,category=d.get('category')==e['category'],target=d.get('proposed_target')==e['target'],publication=bool(published),hidden_safe=not row['hidden_exposures'],projection_safe=all(x not in row['serialized_body'] for x in ['"gm_notes"','"proposed_record"','"action_outcome"','"hidden_facts"']),state=before==after if e['category']!='EXECUTE' else True,transcript_once=len(storage.load_log())==len(oldlog)+1)
   if case['repeat']:
    checks.update(resolver=r.get('kind')=='already_searched',completed=r.get('success') is True,no_discovery=not r.get('discovered_clues') and not r.get('clue_id'),no_effect=not r.get('world_updates') and before['world']['world_state']['flags']==after['world']['world_state']['flags'],journal=before['session'].get('discovered_clues')==after['session'].get('discovered_clues'),actual_publication=any(t in published.lower() for t in ['nothing new','no new','already','again']))
   if case['group']=='resume':
    saved=request('/api/snapshots',{'label':case['id']})['body']['snapshot']['id']; transcript=request('/api/log')['body'];request('/api/snapshots/load',{'snapshot_id':saved})
    checks['resume']=request('/api/log')['body']==transcript and snapshot()['world']==after['world'] and snapshot()['session']['campaign_run_id']==after['session']['campaign_run_id']
   results.append(dict(case=case,checks=checks,passed=all(checks.values()),interpretation=d,resolution=r,before=before,after=after,response=row['body'],http_ms=row['http_ms'],stages=capture['stages']))
   (OUT/'holdout_results.json').write_text(json.dumps(results,indent=2))
 summary=dict(cases=len(results),passed=sum(r['passed'] for r in results),failed=[dict(id=r['case']['id'],text=r['case']['text'],checks=[k for k,v in r['checks'].items() if not v]) for r in results if not r['passed']],executions=1,manifest_sha256=manifest['sha256'],authorship=manifest['authorship'])
 (OUT/'holdout_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
