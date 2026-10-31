"""Offline regression lanes; preserve prior evidence and ordinary game stores."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from tools.validate_pr_play_10 import LANES as PRIOR
from tools.validate_pr_play_09 import protected_hashes
from tools.playtest.runner import stop_owned

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/pr_play_11'
LANES = dict(PRIOR)
LANES['claim_authority'] = ['test_pr_play_11_claim_authority',
    'test_pr_bu_narration_claim_composition', 'test_pr_br_claim_control_slice1',
    'test_pr_br_claim_control_slice2', 'test_realization_provenance',
    'test_investigation_result_provenance_non_invention']
LANES['entry_claim_authority'] = LANES['claim_authority'][1:]


def main():
    backup = {p: p.read_bytes() for n in range(4, 11)
              for p in (ROOT/f'artifacts/pr_play_{n:02}').rglob('*') if p.is_file()}
    protected = protected_hashes()
    env = dict(os.environ, PR_PLAY_DIAGNOSTIC_OUT=str(OUT/'regression_diagnostics'))
    env['PYTHONPATH'] = os.pathsep.join([str(ROOT), *[p for p in sys.path if 'site-packages' in p]])
    runs = json.loads((OUT/'regression_runs.json').read_text()) if (OUT/'regression_runs.json').exists() else {}
    try:
        for lane in sys.argv[1:] or LANES:
            command = [getattr(sys, '_base_executable', sys.executable), '-u', '-m', 'pytest',
                *['tests/'+n+'.py' for n in LANES[lane]], '-q', '--tb=short',
                '--basetemp='+str(ROOT/'development/tmp'/('pr_play_11_'+lane+'_'+str(time.time_ns()))),
                '--junitxml='+str(OUT/(lane+'_regression.xml'))]
            if lane == 'entry_claim_authority':
                command += ['-p', 'tests.helpers.pr_play_11_entry_source']
            start = time.monotonic()
            with (OUT/(lane+'_regression.txt')).open('w', encoding='utf-8') as log:
                proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log,
                    stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                timeout = False
                try:
                    code = proc.wait(timeout=180)
                except subprocess.TimeoutExpired:
                    timeout = True
                    stop_owned(proc, 5)
                    code = None
            runs[lane] = dict(command=command, exit=code, timeout=timeout, seconds=round(time.monotonic()-start, 3))
            if lane == 'gameplay':
                # Preserve this run's real HTTP continuation evidence before
                # restoring the older fixed PR09 evidence pointer.
                import shutil
                pointer = ROOT/'artifacts/pr_play_09/example_run.json'
                if pointer.exists():
                    selected = Path(json.loads(pointer.read_text())['run'])
                    dest = OUT/'gameplay_readiness'
                    dest.mkdir(exist_ok=True)
                    for rel in ('reports/result.json', 'reports/GAMEPLAY_REPORT.md', 'evidence/evidence.zip'):
                        target = dest/rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(selected/rel, target)
                    (dest/'source_run.json').write_text(json.dumps(dict(run=str(selected), command=command), indent=2))
            (OUT/'regression_runs.json').write_text(json.dumps(runs, indent=2))
            print(lane, code, 'timeout='+str(timeout), flush=True)
    finally:
        for p, data in backup.items():
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
        (OUT/'validation_integrity.json').write_text(json.dumps(dict(
            protected_unchanged=protected == protected_hashes(), files=len(protected),
            prior_evidence_restored=all(p.read_bytes() == data for p, data in backup.items())), indent=2))


if __name__ == '__main__':
    main()
