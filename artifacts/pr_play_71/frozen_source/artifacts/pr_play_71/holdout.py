import sys,json,hashlib,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import pytest
from artifacts.pr_play_71.cases import run_case
OUT=Path(__file__).resolve().parent
raw=(OUT/'frozen_holdout.json').read_bytes();manifest=json.loads((OUT/'frozen_holdout_manifest.json').read_text())
assert hashlib.sha256(raw).hexdigest()==manifest['sha256']
with (OUT/'holdout_started.json').open('x') as f:json.dump({'started':time.time(),'sha256':manifest['sha256']},f)
rows=[]
for case in json.loads(raw):
    start=time.perf_counter()
    try:
        with pytest.MonkeyPatch.context() as mp:
            result=run_case(case,OUT/'holdout_data'/case['id'],mp)
        row=dict(id=case['id'],group=case['group'],passed=True,result=result)
    except Exception:
        row=dict(id=case['id'],group=case['group'],passed=False,traceback=traceback.format_exc())
    row['elapsed_ms']=(time.perf_counter()-start)*1000;rows.append(row)
    (OUT/'holdout_results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(case['id'],row['passed'],flush=True)
(OUT/'holdout_summary.json').write_text(json.dumps(dict(passed=sum(r['passed'] for r in rows),failed=sum(not r['passed'] for r in rows),cases=len(rows),sha256=manifest['sha256']),indent=2))
