"""Package the completed offline review; verify state, sources and archive hashes."""
from datetime import datetime, timedelta, timezone
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import zipfile

from run_regression import ROOT, OUT, WORK, hashes

SOURCES = ['game/controlled_investigation_renderer.py',
           'tests/test_pr_play_47_controlled_renderer.py',
           'artifacts/pr_play_47/run_regression.py', 'artifacts/pr_play_47/evaluate.py',
           'artifacts/pr_play_47/package_review.py']


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name, data):
    (OUT/name).write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')


def results(name):
    return {c.attrib['classname']+'::'+c.attrib['name']:
            'failed' if c.find('failure') is not None else
            'error' if c.find('error') is not None else
            'skipped' if c.find('skipped') is not None else 'passed'
            for c in ET.parse(OUT/name).iter('testcase')}


def main():
    before, after = results('baseline.xml'), results('final.xml')
    def counts(rows):
        return {'collected': len(rows), **{s: list(rows.values()).count(s)
                for s in ('passed', 'failed', 'error', 'skipped')}}
    regressions = [k for k in before if before[k] != after.get(k)]
    new = {k:v for k,v in after.items() if k not in before}
    comparison = {'baseline': counts(before), 'final': counts(after),
        'changed_existing_results': regressions, 'new_regressions': [k for k in regressions if before[k]=='passed'],
        'preexisting_failures': [k for k,v in before.items() if v=='failed'],
        'final_failures': [k for k,v in after.items() if v=='failed'], 'new_tests': new}
    dump('regression_comparison.json', comparison)
    assert not regressions and len(new) == 58 and set(new.values()) == {'passed'}
    assert counts(before) == {'collected':640, 'passed':617, 'failed':23, 'error':0, 'skipped':0}
    old_data = json.loads((OUT/'data_before.json').read_text())
    current_data = hashes(ROOT/'data')
    integrity = {'unchanged': old_data == current_data, 'before_count': len(old_data),
        'after_count': len(current_data), 'changed': [k for k in old_data if old_data[k] != current_data.get(k)],
        'added': sorted(set(current_data)-set(old_data)), 'after_hashes': current_data,
        'method': 'SHA256 of every data file before task execution and after regression verification; Python caches excluded.'}
    dump('user_campaign_integrity.json', integrity)
    assert integrity['unchanged']
    source_integrity = {}
    for dirname in ('game', 'tests'):
        original, isolated = hashes(ROOT/dirname), hashes(WORK/dirname)
        excluded = {'controlled_investigation_renderer.py', 'test_pr_play_47_controlled_renderer.py'}
        differences = [k for k,v in original.items() if k not in excluded and isolated.get(k) != v]
        source_integrity[dirname] = {'existing_files_compared': len(set(original)-excluded),
                                    'differences': differences}
        assert not differences
    dump('existing_source_integrity.json', source_integrity)
    dump('state_integrity.json', {'campaign_data_unchanged': True,
        'existing_source_unchanged': True,
        'tests': {k:v for k,v in new.items() if any(s in k for s in ('matrix','proposal','mutation','detached','effects','fallback'))},
        'scope': 'Read-only preview. Legacy update sinks instrumented but no production integration is implemented.'})
    dump('provider_usage.json', {'real_provider_requests':0, 'real_provider_tokens':0,
        'live_gameplay_experiments':0, 'provider_retries':0,
        'preflight_skip_before_imports':True, 'model_changes':False, 'budget_increases':False,
        'transport_guard':'tests/conftest.py and tests/helpers/live_model_guard.py',
        'mode':'Deterministic offline selectors only; no live adapter', 'github_pushes':0})
    baseline = OUT/'baseline_46'; baseline.mkdir(exist_ok=True)
    for name in ('PR_PLAY_46_REPORT.md','BASELINE.md','metrics.json','corpus.json',
                 'corpus_before.json','corpus_after.json','residual_failures.json','regression_comparison.json'):
        shutil.copy2(ROOT/'artifacts/pr_play_46'/name, baseline/name)
    shutil.copy2(ROOT/'tests/helpers/live_model_guard.py', OUT/'live_model_guard.py')
    changes = {}; diff = []
    for name in SOURCES:
        path = ROOT/name
        snapshot = OUT/'source_after'/name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, snapshot)
        changes[name] = {'change':'new file', 'before_sha256':None, 'after_sha256':sha(path),
                         'bytes':path.stat().st_size, 'lines':len(path.read_text(encoding='utf-8').splitlines())}
        diff.extend(difflib.unified_diff([], path.read_text(encoding='utf-8').splitlines(True),
                                        fromfile='/dev/null', tofile=name))
    dump('source_change_manifest.json', changes)
    (OUT/'changes.diff').write_text(''.join(diff), encoding='utf-8')
    # Refresh report timings from the final measured run, retaining noisy tails.
    perf = json.loads((OUT/'evidence_performance.json').read_text())
    report = (OUT/'PR_PLAY_47_REPORT.md').read_text(encoding='utf-8')
    import re
    replacements = {
        'Validation median / p95': f"{perf['validate']['median_us']} / {perf['validate']['p95_us']} microseconds",
        'Rendering including validation median / p95': f"{perf['render']['median_us']} / {perf['render']['p95_us']} microseconds",
        'Fallback including selection-payload/stub overhead median / p95': f"{perf['fallback_end_to_end']['median_us']} microseconds / {perf['fallback_end_to_end']['p95_us']/1000} ms",
        'Accepted preview median / p95': f"{perf['preview_end_to_end']['median_us']} microseconds / {perf['preview_end_to_end']['p95_us']/1000} ms",
        'Traced allocation peak / retained after 100 calls': f"{perf['traced_peak_bytes']:,} / {perf['traced_retained_bytes']:,} bytes",
    }
    for key, value in replacements.items():
        report = re.sub(r'\| '+re.escape(key)+r' \|[^\n]*', '| '+key+' | '+value+' |', report)
    (OUT/'PR_PLAY_47_REPORT.md').write_text(report, encoding='utf-8')
    quality = json.loads((OUT/'quality_comparison.json').read_text())
    dump('summary.json', {'verdict':'B — PARTIAL', 'new_tests':len(new),
        'regression_counts':comparison['final'], 'new_regressions':[], 'provider_requests':0,
        'campaign_data_unchanged':True, 'matrix_cases':10, 'synthetic_scenarios':8,
        'matrix_renderings':30, 'stress_renderings':10, 'quality_means':quality['means'],
        'next_step':'Further bounded offline quality evaluation; defer live-provider trial.',
        'limitation':'Three recognizable structural families; no evidence of live creativity or player preference.'})
    now = datetime.now(timezone(timedelta(hours=-5)))
    archive = ROOT/'handoff'/f'CURRENT_REVIEW({now:%Y%m%d-%H%M%S}).zip'
    (OUT/'archive_path.txt').write_text(str(archive)+'\n', encoding='utf-8')
    excluded = {'MANIFEST.json', 'archive_verification.json', 'credential_scan.json'}
    included = [p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts
                and 'predecessor' not in p.parts and p.name not in excluded]
    # Only inspect environment values for matches; never emit credential data.
    from dotenv import dotenv_values
    import os
    env = {**dotenv_values(ROOT/'.env'), **os.environ}
    credentials = [v.encode() for k,v in env.items() if isinstance(v,str) and len(v)>8 and
                   any(s in k.lower() for s in ('key','token','secret','password','credential'))]
    hits = [p.relative_to(OUT).as_posix() for p in included if any(v in p.read_bytes() for v in credentials)]
    dump('credential_scan.json', {'files_scanned':len(included), 'credential_hits':hits, 'passed':not hits})
    assert not hits, 'Credential match; archive creation stopped'
    included.append(OUT/'credential_scan.json')
    dump('MANIFEST.json', {p.relative_to(OUT).as_posix(): {'sha256':sha(p), 'bytes':p.stat().st_size} for p in included})
    included.append(OUT/'MANIFEST.json')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for p in included: z.write(p, p.relative_to(OUT).as_posix())
        z.writestr('CURRENT_REVIEW.md', report)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest = json.loads(z.read('MANIFEST.json'))
        assert all(hashlib.sha256(z.read(k)).hexdigest() == v['sha256'] for k,v in manifest.items())
    # Windows may memory-map the current ZIP in a preview. Replace the directory
    # entry atomically rather than truncating the mapped destination in place.
    pending = ROOT/'handoff/CURRENT_REVIEW_PR_PLAY_47_pending.zip'
    shutil.copy2(archive, pending)
    pending.replace(ROOT/'handoff/CURRENT_REVIEW.zip')
    pending_report = ROOT/'handoff/CURRENT_REVIEW_PR_PLAY_47_pending.md'
    pending_report.write_text(report, encoding='utf-8')
    pending_report.replace(ROOT/'handoff/CURRENT_REVIEW.md')
    dump('archive_verification.json', {'path':str(archive), 'sha256':sha(archive),
        'stable_archive_matches':sha(archive)==sha(ROOT/'handoff/CURRENT_REVIEW.zip'),
        'zip_integrity_verified':True, 'manifest_hashes_verified':True,
        'files':len(included)+1, 'bytes':archive.stat().st_size})
    print(json.dumps({'archive':str(archive), 'bytes':archive.stat().st_size,
                      'campaign_files_unchanged':len(current_data), 'regressions':comparison['final']}, indent=2))

if __name__ == '__main__': main()
