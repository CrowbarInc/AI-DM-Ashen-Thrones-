import json,pathlib,xml.etree.ElementTree as ET
p=pathlib.Path('artifacts/pr_play_28')
def cases(path):
 out={}
 for t in ET.parse(path).iter('testcase'):
  children=[e for e in t if e.tag in ('failure','error','skipped')]
  out[t.get('classname')+'::'+t.get('name')]={'status':children[0].tag if children else 'passed','message':children[0].get('message','') if children else '', 'details':children[0].text if children else ''}
 return out
baseline,current=cases(p/'baseline.xml'),cases(p/'existing.xml')
def counts(c):return {k:sum(x['status']==k for x in c.values()) for k in ['passed','failure','error','skipped']}
rows=[]
for key in sorted(baseline.keys()|current.keys()):
 b,c=baseline.get(key),current.get(key)
 if not b or not c: label='unclassified_failure'
 elif b['status']=='passed' and c['status'] in ('failure','error'):label='newly_introduced_regression'
 elif b['status'] in ('failure','error') and c['status']=='passed':label='resolved_preexisting_failure'
 elif c['status'] in ('failure','error'):label='preexisting_failure'
 else:label='unchanged_pass_or_skip'
 rows.append(dict(test_id=key,classification=label,baseline=b,current=c))
result=dict(baseline=counts(baseline),current=counts(current),exact_ids_equal=baseline.keys()==current.keys(),new_regressions=[r['test_id'] for r in rows if r['classification']=='newly_introduced_regression'],resolved=[r['test_id'] for r in rows if r['classification']=='resolved_preexisting_failure'],rows=rows)
(p/'test_comparison.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
