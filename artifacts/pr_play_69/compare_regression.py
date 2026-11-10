import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
current=json.loads((OUT/'regression_summary.json').read_text())
prior=json.loads((OUT.parent/'pr_play_68/regression_summary.json').read_text())
result={}
for lane in ['focused','boundary','broader']:
    now=set(current[lane]['failed_nodeids']);old=set(prior[lane]['failed_nodeids'])
    result[lane]=dict(current_passed=current[lane]['passed'],current_failures=sorted(now),
        historical_failures=sorted(old),new_failures=sorted(now-old),resolved_failures=sorted(old-now),
        errors=current[lane]['errors'],interrupted=False)
result['new_regression_count']=sum(len(r['new_failures']) for r in result.values() if isinstance(r,dict))
result['tests_not_executed']=['Full repository suite','Official ATGB','Actual browser gameplay (attachment blocked)']
(OUT/'regression_comparison.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
