"""Read-only provenance checks before the ATGB-03 execution campaign."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).parent
os.chdir(ROOT)
from tools.atgb.baseline import load_baseline
from game import config

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

approved = json.loads((ROOT / 'artifacts/atgb/atgb_02a/validation_results.json').read_text())
checks = {name: sha(ROOT / name) == digest for name, digest in approved['source_sha256'].items()}
with zipfile.ZipFile(ROOT / 'handoff/CURRENT_REVIEW.zip') as archive:
    for name in archive.namelist():
        rel = name.removeprefix('support/')
        if name.startswith('support/') and (rel.startswith('data/validation/atgb/') or rel.startswith('tools/atgb/') or rel == 'tools/run_atgb.py'):
            checks[rel] = (ROOT / rel).is_file() and sha(ROOT / rel) == hashlib.sha256(archive.read(name)).hexdigest()
load_baseline(ROOT)
paths = sorted(set(p for prefix in ['game', 'tools/atgb', 'data/validation/atgb'] for p in (ROOT / prefix).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py', '.json'}))
snapshot = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
canonical = {p.relative_to(ROOT).as_posix(): sha(p) for p in (ROOT / 'data').rglob('*') if p.is_file() and 'validation' not in p.parts}
settings = {name: getattr(config, name) for name in ['DEFAULT_MODEL_NAME', 'HIGH_PRECISION_MODEL_NAME', 'RETRY_ESCALATION_MODEL_NAME', 'ENABLE_MODEL_ROUTING']}
try:
    settings['required_key_available'] = bool(config.get_openai_api_key())
except RuntimeError:
    settings['required_key_available'] = False
settings['provider'] = 'OpenAI Python client; chat completions production owners'
settings['endpoint'] = os.getenv('OPENAI_BASE_URL') or 'https://api.openai.com/v1'
settings['execution_flags'] = {k: os.getenv(k) for k in ['ASHEN_DISABLE_PROVIDER_CALLS', 'ASHEN_DISABLE_LIVE_INTERPRETATION', 'ASHEN_DISABLE_EXPRESSION_GENERATION', 'ASHEN_DISABLE_PROVIDER_RETRIES']}
record = {'readiness_source_checks': checks, 'all_approved_sources_unchanged': all(checks.values()), 'frozen_baseline_valid': True, 'configuration': settings, 'source_sha256': snapshot, 'canonical_data_sha256': canonical, 'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(), 'budget_plan': {'total_provider_calls': 80, 'elapsed_seconds': 1800, 'smoke_provider_calls': 12, 'smoke_elapsed_seconds': 300, 'cost': 'unavailable; no reliable complete cost telemetry/price table; use call and time bounds'}, 'human_review_status': 'pending'}
(OUT / 'configuration_and_provenance.json').write_text(json.dumps(record, indent=2) + '\n')
(OUT / 'initial_git_status.txt').write_text(subprocess.check_output(['git', 'status', '--porcelain'], text=True))
print(json.dumps({'approved_sources_unchanged': all(checks.values()), 'checks': len(checks), 'configuration': settings, 'source_files': len(snapshot)}))
assert all(checks.values()), 'Infrastructure drift: live execution prohibited'
