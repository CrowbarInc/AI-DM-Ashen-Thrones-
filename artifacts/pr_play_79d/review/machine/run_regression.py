import json, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from artifacts.pr_play_79c import run_regression as runner
runner.OUT = Path(__file__).resolve().parent / (sys.argv[1] if len(sys.argv) > 1 else 'final_historical')
runner.OUT.mkdir(exist_ok=True)
os.environ['PYTEST_ADDOPTS'] = '-s -vv'
results = {}
for name, files in [('focused',runner.FOCUSED), ('boundary',runner.BOUNDARY), ('broader',runner.BROADER)]:
    results[name] = runner.run(name, files)
    (runner.OUT/'regression_results.json').write_text(json.dumps(results, indent=2))
    print(name, results[name]['passed'], results[name]['failed_count'], 'new', results[name]['new_vs_pr_play_78a'], flush=True)
