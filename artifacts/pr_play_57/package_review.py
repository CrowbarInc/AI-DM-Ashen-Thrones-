"""Use the repository handoff builder, scan payloads and verify the final ZIP."""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import zipfile
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/pr_play_57'
sys.path.insert(0, str(ROOT))
from tools.build_review_handoff import build_handoff


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    final = json.loads((OUT / 'final_results.json').read_text(encoding='utf-8'))
    assessments = json.loads((OUT / 'provisional_assessments.json').read_text(encoding='utf-8'))
    examples = []
    for r in final['results']:
        t = r['turns'][-1]
        q = t['quarantine']
        examples.append({'example_id': r['label'], 'campaign': 'PR-PLAY-57',
            'run_id': r['label'], 'turn_index': t['turn'], 'player_input': t['player_text'],
            'player_input_classification': ['representative_player_behavior'],
            'simulated_player_rationale': 'Existing deterministic fixture action; no synthetic dialogue model.',
            'prior_context': 'Same board examined on first turn.' if r['label'].startswith('C') else 'Fresh isolated scene.',
            'authorized_context': q['authorized_outcome_contract'], 'exact_gm_output': q['raw_provider_text'],
            'publication': 'quarantined candidate only; actual player response is deterministic',
            'semantic_result': q['diagnostic'], 'human_review': {'status': 'PENDING', 'rationale': 'Provisional automated assessment only.'},
            'evaluator_disagreement': {'present': q['diagnostic'] != 'PASS',
                'reason': assessments[r['label']]['evidence']},
            'source_artifact_path': 'artifacts/pr_play_57/final_results.json',
            'source_sha256': sha((OUT / 'final_results.json').read_bytes())})
    write('evidence_manifest.json', {'campaign': {'campaign_id': 'pr_play_57', 'run_count': 8,
        'turn_count': 10, 'gm_boundary': 'Real provider after authoritative resolution; prose quarantined.'},
        'evidence_scope': 'runtime_and_provisional_semantic_behavioral_evidence',
        'human_confirmed': False, 'examples': examples,
        'selected_evidence': {'representative_success': {'example_id': 'A2'},
            'representative_failure': {'example_id': 'A1'},
            'evaluator_disagreement': {'example_id': 'D1'},
            'unexpected_unclassified': {'example_id': 'B2'}}})
    (OUT / 'evidence_summary.md').write_text(
        '# Behavioral evidence\n\nEight quarantined real-provider candidates; ten API turns including two repeat-search setup turns. '
        'No human-confirmed assessment. Complete raw samples, authorizations, deterministic player responses and provisional disagreements are in evidence_manifest.json. '
        'No ATGB score or general player-facing PASS is claimed.\n', encoding='utf-8')
    excluded = {'tmp_runs', '__pycache__', '.pytest_cache', 'export_stage'}
    excluded_names = {'archive_path.txt', 'archive_verification.json', 'export_scan.json', 'review_config.json', 'test_pr_play_49_after_allowlist.py'}
    paths = [p for p in OUT.rglob('*') if p.is_file() and not any(x in excluded for x in p.parts)
             and p.name not in excluded_names and p.suffix != '.pyc']
    source_paths = [ROOT / p for p in (
        'game/quarantined_investigation_narration.py', 'game/integrated_investigation_narration.py',
        'game/anchored_investigation_narration.py', 'game/offline_investigation_projection.py',
        'game/consequential_narration_validation.py', 'game/immutable_valid_response.py',
        'game/expressive_dialogue.py', 'game/provider_budget.py',
        'tests/test_pr_play_49_anchored_narration.py', 'tests/test_pr_play_57_integrated_narration.py')]
    paths += source_paths
    # Scan exact export payloads without printing or storing any secret values.
    secrets = []
    for line in (ROOT / '.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' not in line or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        value = value.strip().strip('"\'')
        if len(value) > 8 and any(s in key.lower() for s in ('key', 'secret', 'token', 'password')):
            secrets.append(value.encode())
    secrets += [v.encode() for k, v in os.environ.items()
                if len(v) > 8 and k in {'OPENAI_API_KEY', 'API_KEY', 'OPENAI_TOKEN'}]
    hits = [str(p.relative_to(ROOT)) for p in paths if any(s in p.read_bytes() for s in secrets)
            or re.search(br'sk-[A-Za-z0-9]{12,}', p.read_bytes())]
    assert not hits, 'secret material found in export; stop'
    write('export_scan.json', {'passed': True, 'files_scanned': len(paths), 'hits': []})
    paths.append(OUT / 'export_scan.json')
    summary = (OUT / '01_EXECUTIVE_SUMMARY.md').read_text(encoding='utf-8')
    config = {'campaign_id': 'pr_play_57', 'campaign_name': 'PR-PLAY-57 — Integrated Authoritative Outcome Narration',
        'campaign_date': '2026-11-03', 'purpose': 'Evaluate completed-outcome narration inside quarantine.',
        'objective_status': 'B — PARTIAL / FURTHER INVESTIGATION REQUIRED', 'executive_summary': summary,
        'primary_report': 'artifacts/pr_play_57/01_EXECUTIVE_SUMMARY.md',
        'evidence_packets': ['artifacts/pr_play_57'], 'max_file_bytes': 32 * 1024 * 1024,
        'changes': {'production': ['Opt-in integrated narration adapter and small quarantine transport extension. Default deterministic behavior preserved.'],
            'validation': ['Narrow conservative mandatory-outcome check; PR55 unchanged. 28 integrated tests and updated quarantine architecture assertion.'],
            'tooling': ['Three decreasing-budget durable accounting shards; state-stop diagnostics preserved.'],
            'documentation': ['Seventeen requested campaign reports and provisional review worksheets.'],
            'generated_artifacts': ['Explicit evidence export with raw provider captures and source diffs.']},
        'testing': {'focused': '557 passed, 3 known failures; final 28-case module counted once.',
            'broader': 'Nine known hard_validation_attempt_1 failures reproduced; holdout wrapper passed.',
            'full_suite': 'Not executed.', 'runtime_validation': '8/8 successful real requests; all state/quarantine/fallback checks pass.',
            'model_runtime_boundary': 'Engine resolves first; prose never reaches ordinary player response or authoritative storage.',
            'new_regressions': 'None after updating architecture assertion for the new quarantined module.',
            'pre_existing_failures': 'Same three focused and nine broader metadata failures.'},
        'decisions_requiring_human_review': ['Review the eight provisional semantic worksheets; no human confirmation claimed. No player-facing promotion authorized.'],
        'known_problems': {'campaign_specific': ['Four candidates conservatively flagged for coverage, including faithful cross-sentence/wording paraphrases. A1 also rejected by PR55.'],
            'pre_existing': ['Known gold-gain phrase missed by PR55 and rejected by the preserved legacy gate; three focused and nine broader test failures.']},
        'missing_concepts': ['Deterministic failed skill-check fixture; consequences outside disclosure-only investigations.'],
        'does_not_prove': ['Human-confirmed quality, semantic completeness, broad gameplay, or safe player-facing narration.'],
        'recommended_next_step': 'Improve integrated outcome coverage using a bounded reviewed paraphrase set while preserving quarantine.',
        'self_contained_review_test': 'ZIP CRC, included-file SHA-256 and secret scan verified by package_review.py.',
        'supporting_files': [{'path': p.relative_to(ROOT).as_posix(), 'role': 'source' if p in source_paths else 'campaign_evidence',
                              'why': 'Explicit PR-PLAY-57 implementation or execution evidence.',
                              'human_review_required': True, 'behavioral_evidence': p.suffix in {'.json', '.jsonl'}} for p in sorted(paths)]}
    config['supporting_files'].append({'path': 'artifacts/pr_play_57/review_config.json', 'role': 'export_configuration', 'why': 'Reproduce the exact repository handoff selection.'})
    write('review_config.json', config)
    config['configuration_source'] = 'artifacts/pr_play_57/review_config.json'
    # Stage and replace: direct writes to the stable Windows handoff files can
    # fail while the desktop preview has an open handle. The export is identical.
    stage = OUT / 'export_stage'
    result = build_handoff(config, root=ROOT, output_dir=stage, archive_history=False)
    for name in ('CURRENT_REVIEW.md', 'REVIEW_MANIFEST.json', 'CURRENT_REVIEW.zip'):
        pending = ROOT / 'handoff' / ('PR_PLAY_57_pending_' + name)
        pending.write_bytes((stage / name).read_bytes())
        pending.replace(ROOT / 'handoff' / name)
    stable = ROOT / 'handoff/CURRENT_REVIEW.zip'
    try:
        local_zone = ZoneInfo('America/New_York')
    except ZoneInfoNotFoundError:
        # This Nov 3, 2026 cycle is after the Nov 1 transition to EST. Windows
        # Python in this environment has no tzdata; no dependency install needed.
        local_zone = timezone(timedelta(hours=-5))
    timestamp = datetime.now(local_zone).strftime('%Y%m%d-%H%M%S')
    archive = ROOT / 'handoff' / f'CURRENT_REVIEW({timestamp}).zip'
    with archive.open('xb') as handle:
        handle.write(stable.read_bytes())
    with zipfile.ZipFile(archive) as handle:
        assert handle.testzip() is None
        manifest = json.loads(handle.read('REVIEW_MANIFEST.json'))
        for row in manifest['included_files']:
            if row.get('sha256'):
                assert sha(handle.read(row['bundle_path'])) == row['sha256']
        assert len([n for n in handle.namelist() if re.search(r'/\d\d_[A-Z_]+\.md$', n)]) == 17
        assert all(not any(secret in handle.read(n) for secret in secrets) for n in handle.namelist())
    assert archive.read_bytes() == stable.read_bytes()
    write('archive_verification.json', {'archive': str(archive), 'sha256': sha(archive.read_bytes()),
        'stable_archive_matches': True, 'crc_valid': True, 'manifest_hashes_valid': True,
        'secrets_absent': True, 'entries': len(manifest['included_files']), 'bytes': archive.stat().st_size,
        'omitted': result['omitted']})
    (OUT / 'archive_path.txt').write_text(str(archive) + '\n', encoding='utf-8')
    print(json.dumps({'archive': str(archive), 'entries': len(manifest['included_files']),
                      'bytes': archive.stat().st_size, 'omitted': len(result['omitted'])}))


if __name__ == '__main__':
    main()
