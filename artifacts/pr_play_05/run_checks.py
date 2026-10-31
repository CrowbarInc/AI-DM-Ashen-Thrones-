"""Bounded offline evidence runner. No provider connectivity operations."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/pr_play_05'
FIVE = [
    'test_start_campaign_emits_opening_and_sets_started',
    'test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text',
    'test_start_campaign_promotes_valid_upstream_prepared_scene_opening',
    'test_start_campaign_frontier_gate_uses_journal_seed_facts_when_opening_seed_absent',
    'test_start_campaign_opening_fallback_basis_uses_journal_seed_not_visible_facts',
]

def capture(label, args, cwd=ROOT, timeout=55):
    env = dict(os.environ, ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1',
               ASHEN_DISABLE_LIVE_INTERPRETATION='1', ASHEN_DISABLE_EXPRESSION_GENERATION='1')
    env['PR_PLAY_05_HTTP_CAPTURE_DIR']=str(OUT/'http'/label)
    command = [sys.executable, '-m', 'pytest', '-p', 'tests.helpers.pr_play_05_http_capture', *args, '--tb=short', '-q',
               '--basetemp=' + str(ROOT / 'development/tmp/pr_play_05' / label)]
    try:
        p = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=timeout)
        result = {'command': command, 'cwd': str(cwd), 'exit': p.returncode, 'timeout': False}
        output = p.stdout + p.stderr
    except subprocess.TimeoutExpired as e:
        result = {'command': command, 'cwd': str(cwd), 'exit': None, 'timeout': True}
        output = (e.stdout or b'') + (e.stderr or b'')
    (OUT / (label + '.txt')).write_bytes(output)
    (OUT / (label + '.json')).write_text(json.dumps(result, indent=2))
    print(label, result['exit'], 'TIMEOUT' if result['timeout'] else '', flush=True)

if __name__ == '__main__':
    if sys.argv[1] == 'baseline':
        for command, name in [(['git','status','--short'],'status_before.txt'),
                              (['git','rev-parse','HEAD'],'head.txt')]:
            (OUT / name).write_bytes(subprocess.check_output(command, cwd=ROOT))
        paths = list((ROOT/'game').rglob('*.py')) + list((ROOT/'tests').rglob('*.py'))
        paths += list((ROOT/'data').rglob('*')) + list((ROOT/'experiments').rglob('*'))
        paths += [ROOT/'docs/NEXT_SESSION.md']
        hashes = {}
        for p in paths:
            if p.is_file():
                rel = p.relative_to(ROOT).as_posix()
                hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
                if rel in ['game/api.py','game/gm.py','game/provider_budget.py',
                           'tests/test_start_campaign_api.py','docs/NEXT_SESSION.md']:
                    dst = OUT/'entry'/rel
                    dst.parent.mkdir(parents=True,exist_ok=True)
                    dst.write_bytes(p.read_bytes())
        (OUT/'entry_hashes.json').write_text(json.dumps(hashes,indent=2))
    if sys.argv[1] in {'baseline','repeat','pre04','fixed','entry'}:
        cwd = Path(sys.argv[2]) if len(sys.argv)>2 else ROOT
        for i, name in enumerate(FIVE, 1):
            capture(sys.argv[1] + '_' + str(i), ['tests/test_start_campaign_api.py::'+name], cwd)
