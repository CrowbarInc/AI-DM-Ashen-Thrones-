"""Capture entry state and freeze developer-authored holdout before implementation."""
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
from tests.test_pr_play_57_integrated_narration import hook, ROUTE
from tests.pr_play_58_development import PRINTS
def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if (OUT/'baseline.json').exists(): raise SystemExit('Already frozen')
sources = ['game/integrated_investigation_narration.py', 'game/quarantined_investigation_narration.py']
protected = [p for root in ['data', 'artifacts/atgb'] for p in (ROOT/root).rglob('*') if p.is_file()]
save('baseline.json', {'commit': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
    'status': subprocess.check_output(['git','status','--short'], text=True),
    'protected_hashes': {p.relative_to(ROOT).as_posix():sha(p) for p in protected},
    'known_failures': json.loads((ROOT/'artifacts/pr_play_64/regression_summary_final.json').read_text())})
(OUT/'entry_source').mkdir(exist_ok=True)
for n in sources: (OUT/'entry_source'/Path(n).name).write_bytes((ROOT/n).read_bytes())
rows=[]
def add(group, text, expected='ai', h=None, fault=''):
    rows.append(dict(id=f'H{len(rows)+1:02}', group=group, hook=h or hook(), candidate=text,
        fault=fault, expected_publication=expected, expected_coverage='PASS', expected_state='unchanged'))
for t in ['You examine the notice board.', 'Rain falls around the notice board.',
          'You study the notice board carefully.', '', ROUTE,
          'You examine the notice board. '+ROUTE, 'You focus on the notice board.',
          'You inspect the notice board.', 'You examine the evidence carefully.',
          'You study the notice board.']:
    add('delivery',t,'fallback' if not t or ROUTE in t else 'ai')
for t in ['You discover a second patrol route.', 'You acquire a silver key.',
          'The gate is permanently open.', 'The guard captain dies where he stands.',
          'You find a hidden passage.', 'You gain 10 gold coins.',
          'You discover a hidden cache of weapons.', 'You take the iron key.',
          'You discover a red ribbon beneath the board.', 'SECRET is behind the gate.']:
    add('unauthorized',t,'fallback')
for t in [ROUTE.replace('northwest','southeast'), ROUTE.replace('last seen','not last seen'),
          'The patrol definitely reached the old milestone.',
          'The missing patrol is certainly on the northwest track now.',
          'The patrol took a second route beyond the crates.']:
    add('contradiction',t,'fallback')
for t in ['You examine the rain barrel.', 'Rain falls around the notice board.',
          'You study the notice board.', 'You inspect the evidence.', 'You focus on the notice board.']:
    add('history',t,h=hook(kind='investigate',clues=[],known=(ROUTE,)))
for t,f in [(None,'provider_error'),(None,'timeout'),({},''),('', ''),('unfinished','')]:
    add('provider',t,'fallback',fault=f)
for kind in ['already_searched','investigate','observe','already_searched','investigate']:
    add('continuity', 'You examine the notice board again; nothing new is established.',
        h=hook(kind=kind,clues=[],known=(ROUTE,)))
save('frozen_holdout.json',rows)
save('frozen_holdout_manifest.json',dict(cases=len(rows),sha256=sha(OUT/'frozen_holdout.json'),
    frozen_before_implementation=True, limitations='Developer-authored, not independent blind validation. Gameplay transition not yet proven; five continuity cases replace transition assumptions. One execution only after source freeze.'))
print('Frozen',len(rows),'cases')
