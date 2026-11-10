"""Build the offline PR-PLAY-44 review; never imports the application."""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCES = ['game/authorized_information.py', 'game/upstream_response_repairs.py',
           'game/api_turn_support.py', 'game/immutable_valid_response.py',
           'tests/test_pr_play_44_information_delivery.py']


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases(name):
    rows = {}
    for case in ET.parse(OUT / name).iter('testcase'):
        ident = case.attrib['classname'] + '::' + case.attrib['name']
        rows[ident] = 'failed' if case.find('failure') is not None or case.find('error') is not None else 'skipped' if case.find('skipped') is not None else 'passed'
    return rows


def main():
    baseline = cases('baseline_regression.xml')
    final = cases('final_regression.xml')
    test_paths = list(dict.fromkeys(key.split('::')[0].replace('.', '/') + '.py' for key in baseline))
    prefix = '& .venv/Scripts/python.exe -m pytest '
    commands = ["$env:ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1'",
        prefix + ' '.join(test_paths) + ' --tb=short --junitxml=artifacts/pr_play_44/baseline_regression.xml *> artifacts/pr_play_44/baseline_regression.txt',
        prefix + ' '.join(test_paths) + ' tests/test_pr_play_44_information_delivery.py --tb=short --junitxml=artifacts/pr_play_44/final_regression.xml *> artifacts/pr_play_44/final_regression.txt',
        '& .venv/Scripts/python.exe artifacts/pr_play_44/package_review.py']
    (OUT / 'commands.txt').write_text('\n\n'.join(commands) + '\n', encoding='utf-8')
    result = {'baseline': {key: list(baseline.values()).count(key) for key in ('passed', 'failed', 'skipped')},
              'final': {key: list(final.values()).count(key) for key in ('passed', 'failed', 'skipped')},
              'collected_baseline': len(baseline), 'collected_final': len(final),
              'new_regressions_in_existing_tests': [key for key in baseline if baseline[key] == 'passed' and final.get(key) == 'failed'],
              'resolved_existing_failures': [key for key in baseline if baseline[key] == 'failed' and final.get(key) == 'passed'],
              'remaining_existing_failures': [key for key in baseline if baseline[key] == 'failed' and final.get(key) == 'failed'],
              'new_contract_probes': {key: value for key, value in final.items() if key not in baseline}}
    dump('regression_comparison.json', result)
    files = {}
    for path in (ROOT / 'data').rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts or path.name.startswith('.'):
            continue
        row = {'bytes': path.stat().st_size}
        if path.stat().st_size <= 2 * 1024 * 1024 and path.suffix in {'.json', '.jsonl', '.md', '.txt'}:
            row['sha256'] = sha(path)
        files[path.relative_to(ROOT / 'data').as_posix()] = row
    fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    previous = json.loads((ROOT / 'artifacts/pr_play_43/user_campaign_after.json').read_text())
    dump('user_campaign_integrity.json', {'file_count': len(files), 'fingerprint_sha256': fingerprint,
        'pr_play_43_recorded_fingerprint': previous['fingerprint_sha256'],
        'matches_preexisting_pr_play_43_record': fingerprint == previous['fingerprint_sha256'],
        'method': 'PR-PLAY-43 campaign_fingerprint algorithm; historical independent baseline, not a newly invented start-of-task snapshot.'})
    before = json.loads((OUT / 'before_notice.json').read_text())
    after = json.loads((OUT / 'after_notice.json').read_text())
    keys = ['kind', 'action_id', 'success', 'resolved_transition', 'target_scene_id', 'clue_id', 'clue_text', 'discovered_clues', 'state_changes', 'skill_check', 'world_updates']
    session_keys = ['active_scene_id', 'visited_scene_ids', 'turn_counter', 'clocks', 'scene_runtime', 'inventory', 'hp']
    state = {'resolver_core_before_repair': {key: before['resolution'].get(key) for key in keys},
             'resolver_core_after_repair': {key: after['resolution'].get(key) for key in keys},
             'session_comparison': {key: {'baseline': before['after_session'].get(key), 'repaired': after['after_session'].get(key)} for key in session_keys},
             'original_response': before['response']['gm_output']['player_facing_text'],
             'corrected_response': after['response']['gm_output']['player_facing_text']}
    state['resolver_core_identical'] = state['resolver_core_before_repair'] == state['resolver_core_after_repair']
    state['mechanical_session_fields_identical'] = all(row['baseline'] == row['repaired'] for row in state['session_comparison'].values())
    dump('state_integrity.json', state)
    source_map = {}
    audit_files = SOURCES + ['game/api.py', 'game/exploration.py', 'game/social.py', 'game/gm.py',
        'game/conversational_orchestration.py', 'game/dialogue_authority.py', 'game/prompt_context.py',
        'game/final_emission_response_type.py', 'game/response_policy_enforcement.py', 'game/narration_visibility.py', 'game/state_channels.py']
    for name in audit_files:
        source_map[name] = {node.name: node.lineno for node in ast.walk(ast.parse((ROOT / name).read_text(encoding='utf-8'))) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    dump('source_locations.json', source_map)
    manifest = {name: {'sha256': sha(ROOT / name), 'purpose': purpose} for name, purpose in zip(SOURCES, [
        'Bounded resolver-selected information and conservative pre-validation supplementation.',
        'Preserve all authorized discoveries in response-policy fallback; failure must not announce stale clues.',
        'Use all selected information instead of only the first discovery in host speech.',
        'Preserve information before validation/sealing, cover retries and safe fallback, reject omissions without weakening semantic checks.',
        'Offline saved-state replay, synthetic cases, and two unsuppressed legacy contract-gap probes.'])}
    dump('change_manifest.json', manifest)
    stats = {}
    for label in ('before', 'after'):
        row = json.loads((OUT / f'{label}_notice.json').read_text())
        messages = row.get('stages', {}).get('messages')
        if messages:
            stats[label] = {'message_count': len(messages), 'serialized_utf8_bytes': len(json.dumps(messages, ensure_ascii=False).encode()),
                'characters_per_message': [len(message.get('content', '')) for message in messages],
                'token_count': None, 'note': 'Built but not dispatched. No tokenizer/provider estimate represented as measured tokens.'}
    dump('context_size.json', stats)
    dump('provider_usage.json', {'real_provider_requests': 0, 'real_provider_tokens': 0, 'live_gameplay_turns': 0,
        'preflight': 'ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1 before module imports',
        'isolation': 'tests/conftest.py autouse live_model_guard blocks OpenAI/AsyncOpenAI, narration, interpretation and expression transports; _quiet substitutes captured interpretation and controlled narration.'})
    review = ROOT / 'handoff/CURRENT_REVIEW.md'
    historical = OUT / 'PR_PLAY_43_review.md'
    if not historical.exists():
        shutil.copyfile(review, historical)
    for name in SOURCES:
        dest = OUT / 'source_snapshots' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dest)
    report = OUT / 'PR_PLAY_44_REPORT.md'
    review.write_text(report.read_text(encoding='utf-8'), encoding='utf-8')
    included = [path for path in OUT.rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.name not in {'MANIFEST.json', 'archive_verification.json', 'archive_path.txt', 'credential_scan.json'}]
    from dotenv import dotenv_values
    env = {**dotenv_values(ROOT / '.env'), **os.environ}
    secrets = [value.encode() for key, value in env.items() if isinstance(value, str) and len(value) > 8 and any(word in key.lower() for word in ('key', 'token', 'secret', 'password', 'credential'))]
    hits = [str(path.relative_to(OUT)) for path in included if any(secret in path.read_bytes() for secret in secrets)]
    dump('credential_scan.json', {'files_scanned': len(included), 'credential_hits': hits, 'passed': not hits})
    if hits:
        raise SystemExit('Credential scan failed; no archive written.')
    included.append(OUT / 'credential_scan.json')
    dump('MANIFEST.json', {path.relative_to(OUT).as_posix(): {'sha256': sha(path), 'bytes': path.stat().st_size} for path in included})
    included.append(OUT / 'MANIFEST.json')
    # The requested review date is 2026-11-02, after New York's DST end.
    # Windows' venv has no IANA tzdata; do not install dependencies to package.
    now = datetime.now(timezone(timedelta(hours=-5)))
    archive = ROOT / 'handoff' / f'CURRENT_REVIEW({now:%Y%m%d-%H%M%S}).zip'
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as bundle:
        for path in included:
            bundle.write(path, path.relative_to(OUT).as_posix())
        bundle.write(review, 'CURRENT_REVIEW.md')
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        hashes = json.loads(bundle.read('MANIFEST.json'))
        assert all(hashlib.sha256(bundle.read(name)).hexdigest() == row['sha256'] for name, row in hashes.items())
    dump('archive_verification.json', {'path': str(archive), 'sha256': sha(archive), 'bytes': archive.stat().st_size,
        'manifest_hashes_verified': True, 'testzip': None, 'verdict': 'B — PARTIAL'})
    (OUT / 'archive_path.txt').write_text(str(archive), encoding='utf-8')
    print(archive)
    print(json.dumps({'regressions': result['new_regressions_in_existing_tests'], 'user_campaign_matches': fingerprint == previous['fingerprint_sha256'], 'state_core_identical': state['resolver_core_identical'], 'session_fields_identical': state['mechanical_session_fields_identical']}))


if __name__ == '__main__':
    main()
