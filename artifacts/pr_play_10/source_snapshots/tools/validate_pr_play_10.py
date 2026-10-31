"""Offline regression lanes with preserved prior evidence sinks."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from tools.validate_pr_play_09 import LANES as PRIOR_LANES, protected_hashes
from tools.playtest.runner import stop_owned

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/pr_play_10'
LANES = dict(PRIOR_LANES)
LANES['overlay'] = ['test_pr_play_10_overlays', 'test_post_gm_adoption_gateway',
                    'test_world_updates_and_clue_normalization', 'test_save_load',
                    'test_unparsed_movement_state_narration_integrity']
LANES['hidden_faction'] = ['test_narrative_authority_rules', 'test_bounded_improvisation_authority',
                          'test_validation_journal_affordances', 'test_state_authority']


def main():
    backup = {p: p.read_bytes() for n in range(4, 10) for p in (ROOT/f'artifacts/pr_play_{n:02}').rglob('*') if p.is_file()}
    before = protected_hashes()
    env = dict(os.environ, PR_PLAY_DIAGNOSTIC_OUT=str(OUT/'regression_diagnostics'))
    env['PYTHONPATH'] = os.pathsep.join([str(ROOT), *[p for p in sys.path if 'site-packages' in p]])
    runs = json.loads((OUT/'regression_runs.json').read_text()) if (OUT/'regression_runs.json').exists() else {}
    try:
        for lane in sys.argv[1:] or LANES:
            cmd = [getattr(sys, '_base_executable', sys.executable), '-u', '-m', 'pytest',
                   *['tests/'+s+'.py' for s in LANES[lane]], '-q', '--tb=short',
                   '--basetemp='+str(ROOT/'development/tmp'/('pr_play_10_'+lane+'_'+str(time.time_ns()))),
                   '--junitxml='+str(OUT/(lane+'_regression.xml'))]
            start = time.monotonic()
            with (OUT/(lane+'_regression.txt')).open('w', encoding='utf-8') as log:
                proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                timeout = False
                try:
                    code = proc.wait(timeout=150)
                except subprocess.TimeoutExpired:
                    timeout = True
                    stop_owned(proc, 5)
                    code = None
            runs[lane] = dict(command=cmd, exit=code, timeout=timeout, seconds=round(time.monotonic()-start, 3))
            (OUT/'regression_runs.json').write_text(json.dumps(runs, indent=2))
            print(lane, code, 'timeout='+str(timeout), flush=True)
    finally:
        for p, content in backup.items():
            if not p.exists() or p.read_bytes() != content:
                p.write_bytes(content)
        (OUT/'validation_protected_integrity.json').write_text(json.dumps(dict(unchanged=before == protected_hashes(), files=len(before)), indent=2))


if __name__ == '__main__':
    main()
