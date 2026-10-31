"""Measured-only metrics, independent investigator review, source and artifact inventory."""
import collections,hashlib,json,statistics
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1]
def read(n):return json.loads((H/n).read_text(encoding='utf-8'))
def write(n,x):(H/n).write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
local=read('local_validation.json');sem={r['id']:r for r in read('semantic_results.json')};out=[]
for c in local:
 for strategy in ['A','B','C','D','E']:
  decision=('ACCEPT' if c[strategy]['hard_valid'] else 'REJECT') if strategy in ['A','B'] else c['C'] if strategy=='C' else sem[c['id']]['decision'] if strategy=='D' else c['C'] if c['C']=='ACCEPT' else sem[c['id']]['decision']
  out.append(dict(id=c['id'],strategy=strategy,split=c['split'],category=c['category'],risk=c['risk'],expected=c['expected'],decision=decision))
def metric(rows):
 matrix={e:{d:sum(x['expected']==e and x['decision']==d for x in rows) for d in ['ACCEPT','REJECT','ABSTAIN']} for e in ['ACCEPT','REJECT','ABSTAIN']}
 unsafe=[r for r in rows if r['expected']=='REJECT' and r['decision']=='ACCEPT']
 return dict(n=len(rows),safe_n=sum(r['expected']=='ACCEPT' for r in rows),unsafe_n=sum(r['expected']=='REJECT' for r in rows),matrix=matrix,safe_accept=matrix['ACCEPT']['ACCEPT'],unsafe_accept=len(unsafe),high_risk_unsafe_accept=sum(r['risk']=='high' for r in unsafe),false_rejection=matrix['ACCEPT']['REJECT'],safe_abstention=matrix['ACCEPT']['ABSTAIN'],abstention=sum(r['decision']=='ABSTAIN' for r in rows),unresolved_accepted=matrix['ABSTAIN']['ACCEPT'],failures=[r['id'] for r in rows if r['expected']!=r['decision']],mixed_failures=[r['id'] for r in unsafe if r['category']=='mixed'])
metrics={split:{s:metric([r for r in out if r['split']==split and r['strategy']==s]) for s in ['A','B','C','D','E']} for split in ['development','holdout','supplement']}
write('evaluation.json',out);write('metrics.json',metrics)
write('category_metrics.json',{split:{cat:{s:metric([r for r in out if r['split']==split and r['category']==cat and r['strategy']==s]) for s in ['A','B','C','D','E']} for cat in sorted(set(r['category'] for r in out if r['split']==split))} for split in metrics})
raw=[json.loads(l) for l in (H/'provider.jsonl').read_text(encoding='utf-8').splitlines()]
cost={}
for kind in ['generation','validation']:
 group=[r for r in raw if r['kind']==kind];ok=[r for r in group if not r.get('error')];lat=sorted(r['latency_ms'] for r in ok)
 cost[kind]=dict(attempts=len(group),completed=len(ok),items=sum(len(r['ids']) for r in ok),input_tokens=sum(r.get('usage',{}).get('input_tokens',0) for r in group),output_tokens=sum(r.get('usage',{}).get('output_tokens',0) for r in group),median_request_ms=statistics.median(lat),max_request_ms=max(lat),single_case_requests=[dict(trial=r['trial'],latency_ms=r['latency_ms'],usage=r['usage']) for r in ok if len(r['ids'])==1])
cost['local_AB_and_C_median_ms']=statistics.median(r['latency_ms'] for r in local)
cost['local_timing_scope']='A+B together and timer setup; C is computed after timing. Not a separate C measurement.'
cost['historical_strict_social_input_tokens']='approximately 24000-26000; historical, not a fresh paired measurement'
write('cost_measurements.json',cost)
gen=[r for r in raw if r['trial']=='generation_10' and not r.get('error')][0]
review=[]
for x in gen['parsed']:
 ident=x['id'];decision='ACCEPT';reason='All material content supported or authorized nonbinding expression; investigator review, not production enforcement.'
 if ident=='gen03':decision='REJECT';reason='Air is cooler after a long day introduces an environmental comparison absent from the contract; mild but exceeds subjective-only allowance.'
 if ident=='gen10':decision='ABSTAIN';reason='Unknown when guards might leave risks adopting the question premise; no definite schedule asserted, but absence of evidence is not permission to imply a routine.'
 review.append(dict(**x,investigator_decision=decision,reason=reason))
write('generation_review.json',dict(n=10,reviewer='single investigator; labels authored after generation; not frozen independent ground truth',results=review))
# Transport stop was resolved by approved network access. Preserve original stop record explicitly.
stop=read('stop.json')
if stop.get('reason')=='Provider experiments unavailable or unusable':
 write('transport_interruption.json',dict(original=stop,resolved=True,resolution='Network-enabled execution succeeded; failed request retained in provider.jsonl; no safety checks disabled'))
 write('stop.json',dict(active=False,reason='Initial network interruption recovered. No repeated critical unsafe acceptance in this cycle: one batch ACCEPT, diagnostic repeat REJECT. End after R2B as requested.',provider_experiments_complete=True))
before=read('protected_before.json');write('source_integrity.json',dict(protected_files=len(before),changed=[p for p,h in before.items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h]))
print(json.dumps(dict(metrics=metrics,cost=cost),indent=2))
