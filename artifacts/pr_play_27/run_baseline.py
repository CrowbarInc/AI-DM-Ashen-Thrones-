import json, pathlib, subprocess, sys
p=pathlib.Path('artifacts/pr_play_27')
files=sorted(set(json.loads(pathlib.Path('artifacts/pr_play_25/existing_test_files.json').read_text())+json.loads(pathlib.Path('artifacts/pr_play_25/authority_test_files.json').read_text())+['tests/test_pr_play_23_harness.py','tests/test_pr_play_23_local_interaction.py','tests/test_five_turn_gameplay.py']))
(p/'test_files.json').write_text(json.dumps(files,indent=2))
from game.expressive_dialogue import validate_expression
trace=json.loads(pathlib.Path('artifacts/pr_play_26/live/diagnostics/trace_024_validate_expression_input.json').read_text())
(p/'original_reproduction.json').write_text(json.dumps({'input':trace,'actual':validate_expression(*trace['args']),'live_provider_requests':0},indent=2))
with (p/'baseline.txt').open('w') as log:
 r=subprocess.run([sys.executable,'-m','pytest',*files,'-q','--tb=short','--junitxml='+str(p/'baseline.xml')],stdout=log,stderr=subprocess.STDOUT)
print(r.returncode)
