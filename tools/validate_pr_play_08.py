"""Bounded deterministic regression, composing established PR-PLAY selections.

Runs real owned interpreter PIDs (no Windows venv redirector), restores prior
fixed evidence sinks, and records command/exit/timeout for every selected lane.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

from tools.validate_pr_play_06 import GROUPS
from tools.playtest.runner import stop_owned

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/pr_play_08'
LANES = {
    'harness': ['test_automated_playtest', 'test_validation_coverage_registry'],
    'provider': GROUPS['provider'],
    'diagnostics': ['test_pr_play_04_opening_integrity', 'test_pr_play_05_diagnostics', 'test_pr_play_06_opening_budget', 'test_pr_play_07_semantic_acceptance'],
    'structured': GROUPS['structured'],
    'opening': GROUPS['opening'],
    'world': GROUPS['world'],
    'export_atgb': ['test_review_handoff', 'test_atgb_infrastructure', 'test_atgb_accounting', 'test_atgb_readiness'],
}


def protected_hashes():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for name in ('data', 'experiments', 'game', 'static') for p in (ROOT/name).rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    temp = ROOT/'development/tmp/pr_play_08'
    temp.mkdir(parents=True, exist_ok=True)
    before = protected_hashes()
    write = lambda path, data: path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    write(OUT/'protected_before.json', before)
    # Historical tests write fixed diagnostic sinks. Restore their existing bytes.
    backup = {p: p.read_bytes() for name in ('pr_play_04', 'pr_play_05', 'pr_play_06', 'pr_play_07')
              for p in (ROOT/'artifacts'/name).rglob('*') if p.is_file()}
    results = json.loads((OUT/'regression_runs.json').read_text(encoding='utf-8')) if (OUT/'regression_runs.json').exists() else {}
    env = dict(os.environ, PR_PLAY_DIAGNOSTIC_OUT=str(OUT/'regression_diagnostics'))
    env['PYTHONPATH'] = os.pathsep.join([str(ROOT), *[p for p in sys.path if 'site-packages' in p]])
    try:
        for lane in sys.argv[1:] or LANES:
            command = [getattr(sys, '_base_executable', sys.executable), '-u', '-m', 'pytest',
                       *['tests/'+n+'.py' for n in LANES[lane]], '--tb=short',
                       '--basetemp='+str(temp/(lane+'_'+str(time.time_ns()))),
                       '--junitxml='+str(OUT/(lane+'_regression.xml'))]
            started = time.monotonic()
            with (OUT/(lane+'_regression.txt')).open('w', encoding='utf-8') as log:
                proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                timeout = False
                try:
                    code = proc.wait(timeout=120)
                except subprocess.TimeoutExpired:
                    timeout = True
                    stop_owned(proc, 5)
                    code = None
            results[lane] = {'command': command, 'exit': code, 'timeout': timeout,
                             'seconds': round(time.monotonic()-started, 3)}
            write(OUT/'regression_runs.json', results)
            print(lane, code, 'timeout='+str(timeout), flush=True)
    finally:
        for p, content in backup.items():
            if not p.exists() or p.read_bytes() != content:
                p.write_bytes(content)
        after = protected_hashes()
        write(OUT/'protected_integrity.json', {'files': len(before), 'unchanged': before == after,
              'changed': [k for k in before if before[k] != after.get(k)],
              'added': sorted(set(after)-set(before)), 'after': after})


if __name__ == '__main__':
    main()
