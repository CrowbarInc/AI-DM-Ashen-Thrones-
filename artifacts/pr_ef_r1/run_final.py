import json, subprocess, os
from pathlib import Path
args=json.loads(Path('artifacts/pr_ef_r1/baseline_command.json').read_text())
args=[a.replace('pr_ef_r1_baseline','pr_ef_r1_final').replace('baseline_junit.xml','final_junit.xml') for a in args]
args.insert(args.index('--tb=line'),'tests/test_pr_ef_r1_semantic_handoff.py')
Path('artifacts/pr_ef_r1/final_command.json').write_text(json.dumps(args,indent=2))
os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1'
with Path('artifacts/pr_ef_r1/final_output.txt').open('w') as f:
 r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT)
print(r.returncode)
