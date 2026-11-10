"""Package explicit cycle evidence and independently reopen the review archive."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ID = 'pr_play_preseal_authority'
RP = 'development/campaigns/product_realization/'+ID+'/'
AP = 'artifacts/'+ID+'/'
REPORTS = ['SUMMARY.md', 'IMPLEMENTATION.md', 'THREE_CASE_COMPARISON.md', 'PRECEDENCE_VERIFICATION.md',
           'REGRESSION_RESULTS.md', 'TWELVE_TURN_COMPARISON.md', 'PERFORMANCE.md', 'NEXT_STEP_DECISION.md', 'INTEGRITY.md']
EXTERNAL = {'archive_verification.json', 'archive_contents.txt', 'archive_sha256.txt',
            'files_created.json', 'final_git_status.txt', 'handoff_generation_output.txt'}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))


def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2), encoding='utf-8')


def check_source():
    before = read(OUT/'before_source_manifest.json')
    after = read(OUT/'after_source_manifest.json')
    assert all(sha(ROOT/p) == h for p, h in after.items())
    changes = [p for p in before if before[p] != after[p]]
    assert sorted(changes) == ['game/immutable_valid_response.py', 'game/referenced_surface.py']
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == 'd40f1ed198236c604085f1c842ead267a8104ce2'
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'feature/product-realization'
    return changes


if sys.argv[1] == 'prepare':
    check_source()
    save('prior_dated_archives.json', {p.relative_to(ROOT).as_posix(): sha(p) for p in (ROOT/'handoff').glob('CURRENT_REVIEW(*).zip')})
    if not (OUT/'before/entry_review.md').exists():
        (OUT/'before/entry_review.md').write_bytes((ROOT/'handoff/CURRENT_REVIEW.md').read_bytes())
    sources = [
        'game/immutable_valid_response.py', 'game/referenced_surface.py', 'game/perception_grounding.py',
        'tests/test_pr_play_preseal_authority.py', 'tests/test_referenced_surface_grounding_inspection_resolution.py',
        'tests/test_pr_play_post_npc_handoff.py', 'docs/NEXT_SESSION.md', 'docs/DEVELOPMENT_CONSTITUTION.md',
        'docs/review_handoff_standard.md',
        'development/campaigns/product_realization/pr_play_claim_acceptance_audit/SUMMARY.md',
        'development/campaigns/product_realization/pr_play_claim_acceptance_audit/IMPLEMENTATION_OPTIONS.md',
        'development/campaigns/product_realization/pr_play_claim_acceptance_audit/NEXT_STEP_DECISION.md']
    artifacts = []
    for p in OUT.rglob('*'):
        if not p.is_file() or 'review_export' in p.parts or 'run_data' in p.parts or '__pycache__' in p.parts:
            continue
        if p.name in EXTERNAL or p.name in {'evidence_manifest.json', 'review_handoff.json'}:
            continue
        artifacts.append(p.relative_to(ROOT).as_posix())
    supports = sorted(set([RP+n for n in REPORTS] + artifacts + sources + [AP+'evidence_manifest.json', AP+'review_handoff.json']))
    config = {
        'campaign_id': ID, 'campaign_name': 'PR-PLAY Pre-Seal Closed-Surface Authority Repair',
        'campaign_date': '2026-11-08', 'purpose': 'Enforce existing closed inspection authority before immutable acceptance.',
        'objective_status': 'A/PASS',
        'executive_summary': 'All three unchanged HTTP publication defects corrected before normal validation and sealing. Existing 381 tests: 361 passed / 20 known failures (before 358/23); 17 added tests pass, no new failure. Twelve-turn publication/scene outcomes unchanged. Hidden authority and precedence preserved; zero live provider calls.',
        'changes': {'production': ['game/immutable_valid_response.py', 'game/referenced_surface.py'],
                    'validation': ['17 new provider-free tests and unchanged historical regression selections'],
                    'tooling': ['Cycle-owned guarded runners and trace comparison/seal scripts'],
                    'documentation': ['Nine reports and prepended NEXT_SESSION, preserving historical bytes'],
                    'generated_artifacts': ['Before/after source and test/publication evidence; fresh review export']},
        'testing': {'focused': '17/17 added; all three unchanged HTTP reproductions pass.',
                    'broader': '356: 333/23 to 336/20; 381: 358/23 to 361/20; with additions 398: 378/20.',
                    'full_suite': 'Not run', 'runtime_validation': 'Seven conversational HTTP controls pass; twelve-turn strings/scenes identical.',
                    'model_runtime_boundary': '0 live provider calls; external network blocked; isolated storage.',
                    'new_regressions': 'None; twenty unchanged assertion identities and normalized failures verified.',
                    'pre_existing_failures': 'Twelve obsolete public-resolution assertions, stew mismatch, four refusal/publication nodes including portal exception, three KeyErrors.'},
        'decisions_requiring_human_review': [],
        'known_problems': {'campaign_specific': ['Guarantee limited to explicitly classified closed inspection; unmapped authority preserved.'],
                           'pre_existing': ['T05 stock jab, physical completion, generic responses, trading, mixed refusal/publication controls and unrelated failures remain.']},
        'missing_concepts': ['No general English fact checker or new gameplay system introduced.'],
        'does_not_prove': ['Broad playability, full-suite acceptance, held-out generalization, live-model frequency or end-to-end loot persistence.'],
        'recommended_next_step': 'Exactly one proposed next action: remove the unrelated stock jab after authorized notice-board clue publication; do not begin automatically.',
        'self_contained_review_test': 'Reopen dated and stable archive; verify milestone, nine reports, comparison, regressions, source/evidence hashes, NEXT_SESSION/historical suffix, frozen inputs and old dated archives.',
        'primary_report': RP+'SUMMARY.md',
        'supporting_files': [{'path': p, 'role': 'repair_evidence' if p.startswith('artifacts/') else 'source_or_authority',
                              'why': 'Supports the bounded repair, regression comparison, authority precedence or integrity.',
                              'behavioral_evidence': p.endswith(('three_case_comparison.json', 'test_results.json', 'precedence_results.json', 'twelve_turn_comparison.json')),
                              'human_review_required': False} for p in supports if p != RP+'SUMMARY.md'],
        'max_file_bytes': 50*1024*1024,
    }
    save('review_handoff.json', config)
    entries = [{'path': p, 'sha256': sha(ROOT/p), 'bytes': (ROOT/p).stat().st_size, 'packaged': True}
               for p in supports if p != AP+'evidence_manifest.json']
    save('evidence_manifest.json', {'milestone': ID, 'entries': entries,
         'self_excluded_for_no_circular_hash': True, 'external_final_seal_files': sorted(EXTERNAL),
         'excluded_runtime_test_storage': 'before/after twelve_turn/run_data; requests/state/results already in turns.json and raw HTTP captures'})
    print(json.dumps({'prepared': True, 'selected_paths': len(supports)}))
    sys.exit()

check_source()
export = OUT/'review_export'
for name in ('CURRENT_REVIEW.md', 'REVIEW_MANIFEST.json', 'CURRENT_REVIEW.zip'):
    temp = ROOT/'handoff'/(ID+'_'+name+'.tmp')
    shutil.copyfile(export/name, temp)
    try:
        os.replace(temp, ROOT/'handoff'/name)
    except PermissionError:
        # Windows readers may allow writing but deny replacing an open ZIP.
        # This is only the explicitly authorized generated stable review export.
        shutil.copyfile(temp, ROOT/'handoff'/name)
        temp.unlink()
# Date the export in the user's New York timezone, currently EST (November).
stamp = datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
archive = ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
assert not archive.exists()
shutil.copyfile(ROOT/'handoff/CURRENT_REVIEW.zip', archive)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    names = z.namelist()
    summary = z.read('CURRENT_REVIEW.md').decode('utf-8')
    assert 'Identifier: `'+ID+'`' in summary and '361 passed' in summary
    assert all('support/'+RP+n in names for n in REPORTS)
    manifest = json.loads(z.read('REVIEW_MANIFEST.json'))
    assert manifest['campaign_id'] == ID
    assert all(row['reason'].startswith('duplicate content of ') for row in manifest['omitted_artifacts']), manifest['omitted_artifacts']
    canonical = []
    for row in manifest['included_files']:
        data = z.read(row['bundle_path'])
        if row.get('sha256'):
            assert hashlib.sha256(data).hexdigest() == row['sha256']
        if row.get('canonical_source_path'):
            assert data == (ROOT/row['canonical_source_path']).read_bytes()
            canonical.append(row['canonical_source_path'])
    em = json.loads(z.read('support/'+AP+'evidence_manifest.json'))
    assert em['milestone'] == ID
    for row in em['entries']:
        assert sha(ROOT/row['path']) == row['sha256']
        member = 'support/'+row['path']
        if member in names:
            assert hashlib.sha256(z.read(member)).hexdigest() == row['sha256']
        else:
            assert any(o.get('sha256') == row['sha256'] and o['reason'].startswith('duplicate content of ') for o in manifest['omitted_artifacts'])
    handoff = z.read('support/docs/NEXT_SESSION.md')
    assert handoff == (ROOT/'docs/NEXT_SESSION.md').read_bytes()
    assert handoff.endswith((OUT/'before/docs/NEXT_SESSION.md').read_bytes())
    assert ID.encode() in handoff[:500]
    comparison = json.loads(z.read('support/'+AP+'three_case_comparison.json'))
    assert all(c['original_test_after'] == 'passed' and not c['unsupported_claim_published'] and c['digest_verified'] for c in comparison['cases'])
    results = json.loads(z.read('support/'+AP+'test_results.json'))
    assert results['expanded_after'] == {'tests': 381, 'passed': 361, 'failed': 20, 'error': 0, 'skipped': 0}
    assert not results['newly_failing'] and len(results['resolved']) == 3
    assert results['added_tests_final']['passed'] == 17
    assert z.read('CURRENT_REVIEW.md').decode().replace('\r\n', '\n') == (ROOT/'handoff/CURRENT_REVIEW.md').read_text(encoding='utf-8')
    assert json.loads(z.read('REVIEW_MANIFEST.json')) == read(ROOT/'handoff/REVIEW_MANIFEST.json')
    assert not any('/.git/' in n.lower() or '/.env' in n.lower() or n.lower().endswith('.zip') for n in names)
with zipfile.ZipFile(ROOT/'handoff/CURRENT_REVIEW.zip') as z:
    assert z.testzip() is None and z.namelist() == names
assert sha(archive) == sha(ROOT/'handoff/CURRENT_REVIEW.zip')
for p, digest in read(OUT/'prior_dated_archives.json').items():
    assert sha(ROOT/p) == digest
changes = check_source()
assert read(OUT/'frozen_integrity.json')['changed'] == []
for directory in ['before', 'before/authority', 'after', 'after/authority', 'focused_final']:
    integrity = read(OUT/directory/'execution_integrity.json')
    assert integrity['changed'] == [] and integrity['network_attempts_blocked'] == [] and integrity['live_provider_calls'] == 0
digest = sha(archive)
save('archive_verification.json', {'status': 'PASS', 'milestone': ID, 'archive_path': str(archive), 'archive_sha256': digest,
     'stable_dated_equal': True, 'zip_crc': True, 'canonical_member_hashes_checked': len(canonical),
     'required_reports': 9, 'three_cases_verified': 3, 'regression_comparison_verified': True,
     'handoff_history_preserved': True, 'source_changes': changes, 'frozen_unchanged': read(OUT/'frozen_integrity.json')['checked'],
     'old_dated_archives_preserved': True, 'live_provider_calls': 0, 'external_seal_avoids_circular_hash': True})
(OUT/'archive_sha256.txt').write_text(str(archive)+'\nSHA-256: '+digest+'\n', encoding='utf-8')
(OUT/'archive_contents.txt').write_text('\n'.join(names)+'\n', encoding='utf-8')
(OUT/'final_git_status.txt').write_bytes(subprocess.check_output(['git', 'status', '--short'], cwd=ROOT))
save('files_created.json', {'reports': [RP+n for n in REPORTS], 'test': 'tests/test_pr_play_preseal_authority.py',
     'evidence': [p.relative_to(ROOT).as_posix() for p in OUT.rglob('*') if p.is_file() and 'review_export' not in p.parts and 'run_data' not in p.parts],
     'archive': str(archive)})
print(json.dumps({'status': 'PASS', 'archive': str(archive), 'sha256': digest, 'canonical_members': len(canonical)}))
