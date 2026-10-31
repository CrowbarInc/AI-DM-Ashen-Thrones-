"""ATGB-03C read-only readiness and preservation snapshot."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from tools.atgb.accounting import live_accounting_readiness
from tools.atgb.baseline import load_baseline
from tools.atgb.fixtures import load_corpus
from game import config

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')

assert not (OUT / 'provenance_before.json').exists(), 'Do not overwrite provenance'
readiness = live_accounting_readiness(ROOT)
write('accounting_readiness.json', readiness)
load_baseline(ROOT)
corpus = load_corpus(ROOT)
approved = {}
with zipfile.ZipFile(ROOT / 'handoff/history/atgb_03b_provider_accounting_integrity/REVIEW.zip') as z:
    for name in z.namelist():
        rel = name.removeprefix('support/')
        if name.startswith('support/') and (rel.startswith(('game/', 'tools/atgb/', 'data/validation/atgb/')) or rel == 'tools/run_atgb.py'):
            approved[rel] = sha(ROOT / rel) == hashlib.sha256(z.read(name)).hexdigest()
original = json.loads((ROOT / 'artifacts/atgb/atgb_03/configuration_and_provenance.json').read_text())
corpus_checks = {p: sha(ROOT / p) == h for p, h in original['source_sha256'].items() if p.startswith('data/validation/atgb/')}
paths = set()
for directory in ('game', 'tools/atgb', 'data/validation/atgb', 'artifacts/atgb/atgb_03', 'artifacts/atgb/atgb_03a', 'artifacts/atgb/atgb_03b'):
    paths.update(p for p in (ROOT / directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.update(p for p in (ROOT / 'data').rglob('*') if p.is_file())
paths.update(ROOT / p for p in ('tools/run_atgb.py', 'run.py', 'development/reports/atgb_03_initial_live_baseline.md'))
settings = {k: getattr(config, k) for k in ('DEFAULT_MODEL_NAME', 'HIGH_PRECISION_MODEL_NAME', 'RETRY_ESCALATION_MODEL_NAME', 'ENABLE_MODEL_ROUTING')}
try:
    available = bool(config.get_openai_api_key())
except RuntimeError:
    available = False
settings['provider_key_available'] = available
settings['execution_flags'] = {k: os.getenv(k) for k in ('ASHEN_DISABLE_PROVIDER_CALLS', 'ASHEN_DISABLE_LIVE_INTERPRETATION', 'ASHEN_DISABLE_EXPRESSION_GENERATION', 'ASHEN_DISABLE_PROVIDER_RETRIES')}
settings['endpoint_is_default'] = not os.getenv('OPENAI_BASE_URL')
record = {'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)},
          'approved_03b_checks': approved, 'original_corpus_checks': corpus_checks,
          'frozen_baseline_valid': True, 'configuration': settings,
          'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'planned_scenarios': [f'S{i:02}' for i in range(4, 11)], 'planned_turns': 24,
          'budget': {'application_admissions': 48, 'elapsed_seconds': 900, 'worker_seconds': 180,
                     'total_tokens': 120000, 'input_token_limit': 100000, 'output_token_limit': 20000,
                     'cost': 'unavailable; no reliable pinned price supplied',
                     'sdk_transport_retries': 'unchanged and not independently counted'},
          'authorization': 'User ATGB-03C request authorizes bounded live S04 full rerun and S05-S10; prior explicit OpenAI export authorization recorded in ATGB-03 remains applicable.'}
write('provenance_before.json', record)
(OUT / 'initial_git_status.txt').write_text(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True), encoding='utf-8')
print(json.dumps({'readiness_ok': readiness['ok'], 'dispatch_paths': len(readiness['dispatch_sites']), 'approved_source_checks': len(approved), 'approved_unchanged': all(approved.values()), 'original_corpus_unchanged': all(corpus_checks.values()), 'configuration': settings, 'snapshot_files': len(paths)}))
assert readiness['ok'] and len(readiness['dispatch_sites']) == 7
assert approved and all(approved.values()) and corpus_checks and all(corpus_checks.values())
assert available and all(settings[k] == 'gpt-4.1-mini' for k in ('DEFAULT_MODEL_NAME', 'HIGH_PRECISION_MODEL_NAME', 'RETRY_ESCALATION_MODEL_NAME'))
assert settings['ENABLE_MODEL_ROUTING'] and all(v is None for v in settings['execution_flags'].values())
