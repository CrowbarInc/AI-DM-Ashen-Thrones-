"""Offline replay in a disposable copy; never overwrite predecessor evidence."""
import os
os.environ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'] = '1'
os.environ['ASHEN_DISABLE_LIVE_INTERPRETATION'] = '1'
os.environ['ASHEN_DISABLE_EXPRESSION_GENERATION'] = '1'
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/pr_play_49'
WORK = ROOT / 'development/tmp/pr_play_49_workspace'

def hashes(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts}

def main():
    phase = sys.argv[1]
    if phase == 'baseline' and not WORK.exists():
        OUT.mkdir(exist_ok=True)
        (OUT/'data_before.json').write_text(json.dumps(hashes(ROOT/'data'), indent=2))
        predecessor = OUT/'predecessor'
        predecessor.mkdir(exist_ok=True)
        for name in ('CURRENT_REVIEW.md', 'CURRENT_REVIEW.zip'):
            shutil.copy2(ROOT/'handoff'/name, predecessor/name)
        for name in ('game', 'tests', 'data', 'static', 'tools'):
            shutil.copytree(ROOT/name, WORK/name, ignore=shutil.ignore_patterns('__pycache__'))
        for name in ('pytest.ini', 'requirements.txt'):
            shutil.copy2(ROOT/name, WORK/name)
        # Existing tests read these saved fixtures and write their own evidence.
        for name in ('pr_play_44', 'pr_play_45', 'pr_play_46', 'pr_play_47', 'atgb/pr_play_43'):
            shutil.copytree(ROOT/'artifacts'/name, WORK/'artifacts'/name)
        for p in (ROOT/'artifacts').iterdir():
            if p.is_dir(): (WORK/'artifacts'/p.name).mkdir(exist_ok=True)
    elif phase != 'baseline':
        for name in ('offline_investigation_projection.py', 'controlled_investigation_renderer.py'):
            shutil.copy2(ROOT/'game'/name, WORK/'game'/name)
        shutil.copy2(ROOT/'game/anchored_investigation_narration.py', WORK/'game/anchored_investigation_narration.py')
        shutil.copy2(ROOT/'tests/test_pr_play_49_anchored_narration.py', WORK/'tests/test_pr_play_49_anchored_narration.py')
        shutil.copytree(OUT, WORK/'artifacts/pr_play_49', dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('predecessor', 'source_after', 'supporting'))
    for p in ROOT.iterdir():
        if p.is_file() and p.suffix in {'.json', '.md'}: shutil.copy2(p, WORK/p.name)
    (WORK/'development/tmp').mkdir(parents=True, exist_ok=True)
    (WORK/'artifacts/pr_play_43').mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/'artifacts/pr_play_43/live_result.json', WORK/'artifacts/pr_play_43/live_result.json')
    for name in ('atgb/pr_play_35', 'atgb/pr_play_38', 'atgb/pr_play_41', 'atgb/atgb_r2_01',
                 'pr_bv_turn_operation_projection_micro_live', 'pr_co_gameplay_viability',
                 'pr_cq_live_finalization', 'pr_bt_selective_epistemic_restoration_final_micro_live'):
        if not (WORK/'artifacts'/name).exists() or not any((WORK/'artifacts'/name).iterdir()):
            shutil.copytree(ROOT/'artifacts'/name, WORK/'artifacts'/name, dirs_exist_ok=True)
    args0 = json.loads((ROOT/'artifacts/pr_play_46/final_command.json').read_text())
    suites = [a for a in args0 if a.startswith('tests/')]
    suites.append('tests/test_pr_play_47_controlled_renderer.py')
    if phase != 'baseline': suites.append('tests/test_pr_play_49_anchored_narration.py')
    if phase == 'final_focused': suites = ['tests/test_pr_play_49_anchored_narration.py']
    args = [sys.executable, '-m', 'pytest', *suites, '--tb=short',
            '--basetemp=development/tmp/pr_play_49_'+phase,
            '--junitxml='+str(OUT/(phase+'.xml'))]
    (OUT/(phase+'_command.json')).write_text(json.dumps(args, indent=2))
    with (OUT/(phase+'.txt')).open('w', encoding='utf-8') as log:
        run = subprocess.run(args, cwd=WORK, stdout=log, stderr=subprocess.STDOUT)
    print((OUT/(phase+'.txt')).read_text(encoding='utf-8')[-2800:])
    print('Exit:', run.returncode)
    if phase != 'baseline':
        for p in (WORK/'artifacts/pr_play_49').glob('*.json'):
            if p.name.startswith('evidence_'): shutil.copy2(p, OUT/p.name)
    return run.returncode

if __name__ == '__main__': sys.exit(main())
