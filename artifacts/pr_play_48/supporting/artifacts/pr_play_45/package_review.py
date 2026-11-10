"""Package PR-PLAY-45 offline evidence. No application imports or providers."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import difflib
import hashlib
import json
import os
import shutil
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCES = ['game/gm.py', 'game/prompt_context.py', 'game/immutable_valid_response.py',
           'game/narration_authorization.py', 'game/mechanical_claims.py',
           'tests/test_pr_play_45_narration_authority.py', 'tests/test_prompt_context.py',
           'tests/test_exploration_skill_checks.py']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def cases(name):
    return {c.attrib['classname'] + '::' + c.attrib['name']:
            ('failed' if c.find('failure') is not None or c.find('error') is not None else
             'skipped' if c.find('skipped') is not None else 'passed')
            for c in ET.parse(OUT / name).iter('testcase')}


def main():
    before, after = cases('baseline_combined.xml'), cases('final_combined_regression.xml')
    new = [k for k in before if before[k] == 'passed' and after.get(k) != 'passed']
    regressions = {'baseline_counts': {s: list(before.values()).count(s) for s in ('passed', 'failed', 'skipped')},
                   'final_counts': {s: list(after.values()).count(s) for s in ('passed', 'failed', 'skipped')},
                   'new_regressions': new,
                   'baseline_failed_now_passing': [k for k in before if before[k] == 'failed' and after.get(k) == 'passed'],
                   'repaired_original_contract_failures': [k for k in before if 'test_pr_play_44_' in k and before[k] == 'failed' and after.get(k) == 'passed'],
                   'carried_forward_failures': [k for k in before if before[k] == 'failed' and after.get(k) == 'failed']}
    dump('regression_comparison.json', regressions)
    required = {k: v for k, v in after.items() if 'test_pr_play_45_' in k and '::test_' in k and
                k.split('::test_')[1][:2] in [chr(c) + '_' for c in range(ord('A'), ord('P') + 1)]}
    cross = {k: v for k, v in after.items() if 'test_pr_play_45_' in k and 'test_cross_scenario' in k}
    dump('required_tests.json', required)
    dump('cross_scenarios.json', cross)
    manifest = {}
    diffs = []
    for name in SOURCES:
        src, old = ROOT / name, OUT / 'source_before' / name
        dest = OUT / 'source_after' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        manifest[name] = {'sha256': sha(src), 'bytes': src.stat().st_size,
                          'before_sha256': sha(old) if old.exists() else None}
        diffs.extend(difflib.unified_diff(old.read_text(encoding='utf-8').splitlines(True) if old.exists() else [],
                     src.read_text(encoding='utf-8').splitlines(True), fromfile='before/' + name, tofile='after/' + name))
    dump('source_change_manifest.json', manifest)
    (OUT / 'repair.diff').write_text(''.join(diffs), encoding='utf-8')
    # Compare the same synthetic ledger turns, rather than unrelated prompt profiles.
    old_payloads = json.loads((OUT / 'baseline_synthetic_context.json').read_text(encoding='utf-8'))['contexts']
    new_payloads = json.loads((ROOT / 'artifacts/pr_play_44/scenario_ledger.json').read_text(encoding='utf-8'))['contexts']
    sizes = []
    for i, (old, current) in enumerate(zip(old_payloads, new_payloads)):
        size = lambda value: len(json.dumps(value, ensure_ascii=False).encode('utf-8'))
        a, b = size(old), size(current)
        sizes.append({'turn': i + 1, 'before_utf8_bytes': a, 'after_utf8_bytes': b,
                      'delta_bytes': b-a, 'delta_percent': round(100*(b-a)/a, 2),
                      'tokens': None, 'note': 'serialized messages built offline, never dispatched; bytes are not measured tokens'})
    dump('context_size.json', sizes)
    shutil.copyfile(ROOT / 'artifacts/pr_play_44/scenario_ledger.json', OUT / 'after_synthetic_context.json')
    shutil.copyfile(ROOT / 'artifacts/pr_play_44/contradiction.json', OUT / 'after_original_contradiction.json')
    shutil.copyfile(ROOT / 'tests/test_pr_play_44_information_delivery.py', OUT / 'original_44_tests_unchanged.py')
    files = {}
    for path in (ROOT / 'data').rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts or path.name.startswith('.'):
            continue
        row = {'bytes': path.stat().st_size}
        if path.stat().st_size <= 2*1024*1024 and path.suffix in {'.json', '.jsonl', '.md', '.txt'}:
            row['sha256'] = sha(path)
        files[path.relative_to(ROOT / 'data').as_posix()] = row
    fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    prior = json.loads((ROOT / 'artifacts/pr_play_43/user_campaign_after.json').read_text())['fingerprint_sha256']
    dump('user_campaign_integrity.json', {'fingerprint_sha256': fingerprint, 'historical_fingerprint': prior,
         'matches_historical_pr_play_43': fingerprint == prior,
         'method': 'Existing independent PR-PLAY-43 algorithm; not misrepresented as a fresh task-start snapshot.'})
    dump('provider_usage.json', {'real_provider_requests': 0, 'real_provider_tokens': 0, 'live_gameplay_turns': 0,
         'preflight': 'ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1 before imports',
         'isolation': 'conftest live_model_guard; controlled narration, no validation model calls'})
    transaction = json.loads((OUT / 'transaction_integrity.json').read_text(encoding='utf-8'))
    dump('state_integrity.json', {'transaction_unchanged_by_narration': transaction['before_narration'] == transaction['after_narration'],
         'evidence': ['transaction_integrity.json', 'rejection_fallback.json', 'final_combined_regression.xml'],
         'production_combat_damage_test': after.get('tests.test_pr_play_45_narration_authority::test_production_damage_is_not_applied_twice'),
         'original_clue_state_unchanged_test': after.get('tests.test_pr_play_44_information_delivery::test_contradictory_discovery_draft_falls_back_without_losing_information'),
         'claims_do_not_write_state': 'projection/validation are read-only; tests deep-compare supplied authoritative objects'})
    summary = {'required_cases': len(required), 'required_passed': list(required.values()).count('passed'),
               'cross_cases': len(cross), 'cross_passed': list(cross.values()).count('passed'),
               'context_size': sizes, 'regressions': regressions, 'user_campaign_unchanged': fingerprint == prior,
               'verdict': 'B — PARTIAL', 'residual_adversarial_failures': 2}
    dump('summary.json', summary)
    review = ROOT / 'handoff/CURRENT_REVIEW.md'
    predecessor = OUT / 'predecessor'
    predecessor.mkdir(exist_ok=True)
    for name in ('CURRENT_REVIEW.md', 'CURRENT_REVIEW.zip'):
        if not (predecessor / name).exists():
            shutil.copyfile(ROOT / 'handoff' / name, predecessor / name)
    report = OUT / 'PR_PLAY_45_REPORT.md'
    review.write_text(report.read_text(encoding='utf-8'), encoding='utf-8')
    included = [p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and
                'predecessor' not in p.parts and p.name not in {'MANIFEST.json', 'archive_verification.json', 'archive_path.txt'}]
    from dotenv import dotenv_values
    env = {**dotenv_values(ROOT / '.env'), **os.environ}
    secrets = [v.encode() for k, v in env.items() if isinstance(v, str) and len(v)>8 and
               any(word in k.lower() for word in ('key', 'token', 'secret', 'password', 'credential'))]
    hits = [str(p.relative_to(OUT)) for p in included if any(s in p.read_bytes() for s in secrets)]
    dump('credential_scan.json', {'files_scanned': len(included), 'credential_hits': hits, 'passed': not hits})
    if hits:
        raise SystemExit('Credential scan failed; archive not written')
    if OUT / 'credential_scan.json' not in included:
        included.append(OUT / 'credential_scan.json')
    dump('MANIFEST.json', {p.relative_to(OUT).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in included})
    included.append(OUT / 'MANIFEST.json')
    now = datetime.now(timezone(timedelta(hours=-5)))
    archive = ROOT / 'handoff' / f'CURRENT_REVIEW({now:%Y%m%d-%H%M%S}).zip'
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for p in included:
            z.write(p, p.relative_to(OUT).as_posix())
        z.write(review, 'CURRENT_REVIEW.md')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        m = json.loads(z.read('MANIFEST.json'))
        assert all(hashlib.sha256(z.read(k)).hexdigest() == v['sha256'] for k, v in m.items())
    shutil.copyfile(archive, ROOT / 'handoff/CURRENT_REVIEW.zip')
    dump('archive_verification.json', {'path': str(archive), 'sha256': sha(archive),
         'manifest_hashes_verified': True, 'testzip': None})
    (OUT / 'archive_path.txt').write_text(str(archive), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    print(archive)


if __name__ == '__main__':
    main()
