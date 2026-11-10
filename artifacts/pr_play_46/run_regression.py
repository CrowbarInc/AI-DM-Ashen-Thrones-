"""Replay the predecessor regression selection offline, preserving raw output."""
import os
os.environ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'] = '1'
os.environ['ASHEN_DISABLE_LIVE_INTERPRETATION'] = '1'
os.environ['ASHEN_DISABLE_EXPRESSION_GENERATION'] = '1'
import re
import sys
import subprocess
from pathlib import Path
root = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent
phase = sys.argv[1]
suites = re.findall(r'tests/\S+\.py', (root/'artifacts/pr_play_45/final_command.txt').read_text())
if phase == 'final':
    suites.append('tests/test_pr_play_46_mechanical_boundary.py')
args = [sys.executable, '-m', 'pytest', *suites,
        '--basetemp=development/tmp/pr_play_46_' + phase, '--tb=short',
        '--junitxml=artifacts/pr_play_46/' + phase + '.xml']
(out/(phase+'_command.json')).write_text(__import__('json').dumps(args, indent=2))
with (out/(phase+'.txt')).open('w', encoding='utf-8') as log:
    run = subprocess.run(args, cwd=root, stdout=log, stderr=subprocess.STDOUT)
print(phase, 'exit', run.returncode)
print((out/(phase+'.txt')).read_text(encoding='utf-8')[-1600:])
sys.exit(run.returncode)
