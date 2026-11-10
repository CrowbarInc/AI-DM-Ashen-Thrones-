"""Assemble and verify the offline review artifact; no application imports."""
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
SOURCES = ['game/mechanical_claims.py', 'game/narration_authorization.py',
           'tests/test_pr_play_46_mechanical_boundary.py']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def results(name):
    return {c.attrib['classname']+'::'+c.attrib['name']:
            'failed' if c.find('failure') is not None or c.find('error') is not None else
            'skipped' if c.find('skipped') is not None else 'passed'
            for c in ET.parse(OUT/name).iter('testcase')}


def main():
    before, after = results('baseline.xml'), results('final.xml')
    count = lambda rows: {'collected': len(rows), **{s:list(rows.values()).count(s) for s in ('passed','failed','skipped')}}
    comparison = {'baseline':count(before), 'final':count(after),
        'new_regressions':[k for k in before if before[k]=='passed' and after.get(k)!='passed'],
        'changed_existing_results':[k for k in before if before[k]!=after.get(k)],
        'preexisting_failures':[k for k,v in before.items() if v=='failed'],
        'final_failures':[k for k,v in after.items() if v=='failed'],
        'new_tests':{k:v for k,v in after.items() if k not in before}}
    dump('regression_comparison.json', comparison)
    assert not comparison['new_regressions']
    assert len(comparison['new_tests']) == 25
    assert all(v=='passed' for v in comparison['new_tests'].values())
    data_before = json.loads((OUT/'data_before.json').read_text())
    data_after = {str(p.relative_to(ROOT/'data')):sha(p) for p in (ROOT/'data').rglob('*')
                  if p.is_file() and '__pycache__' not in p.parts}
    integrity = {'files_before':len(data_before), 'files_after':len(data_after),
        'unchanged':data_before==data_after,
        'changed':[k for k in data_before if data_before[k]!=data_after.get(k)],
        'added':sorted(set(data_after)-set(data_before)),
        'after_sha256':hashlib.sha256(json.dumps(data_after,sort_keys=True).encode()).hexdigest(),
        'method':'Fresh task-start/task-end SHA256 of every file under data, excluding Python cache.'}
    dump('user_campaign_integrity.json', integrity)
    assert integrity['unchanged']
    state = {k:v for k,v in after.items() if any(t in k for t in
        ('synthetic_transaction','production_damage','contradictory_discovery_draft','originals_fallback','envelope_is_read_only'))}
    dump('state_integrity.json', {'tests':state,'campaign_data_unchanged':integrity['unchanged'],
        'scope':'Exercised read-only projection/validation/finalization; legacy adoption channels not certified.'})
    dump('provider_usage.json', {'real_provider_requests':0, 'real_provider_tokens':0,
        'live_gameplay_turns':0,'preflight':'ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1 before imports',
        'isolation':'Established tests/helpers/live_model_guard.py; deterministic inputs only',
        'provider_model_changes':False,'token_budget_increases':False,'pushes':0})
    manifest={}; diff=[]
    for name in SOURCES:
        src=ROOT/name; old=OUT/'source_before'/name; dest=OUT/'source_after'/name
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
        manifest[name]={'before_sha256':sha(old) if old.exists() else None,
                        'after_sha256':sha(src),'bytes':src.stat().st_size}
        diff.extend(difflib.unified_diff(old.read_text(encoding='utf-8').splitlines(True) if old.exists() else [],
            src.read_text(encoding='utf-8').splitlines(True),fromfile='before/'+name,tofile='after/'+name))
    dump('source_change_manifest.json',manifest)
    (OUT/'repair.diff').write_text(''.join(diff),encoding='utf-8')
    predecessor=OUT/'predecessor';predecessor.mkdir(exist_ok=True)
    for name in ['CURRENT_REVIEW.md','CURRENT_REVIEW.zip']:
        if (ROOT/'handoff'/name).exists() and not (predecessor/name).exists():
            shutil.copyfile(ROOT/'handoff'/name,predecessor/name)
    evidence=OUT/'predecessor_evidence';evidence.mkdir(exist_ok=True)
    for name in ['residual_adversarial.json','PR_PLAY_45_REPORT.md','transaction_integrity.json']:
        shutil.copyfile(ROOT/'artifacts/pr_play_45'/name,evidence/name)
    shutil.copyfile(ROOT/'tests/helpers/live_model_guard.py',evidence/'live_model_guard.py')
    metrics=json.loads((OUT/'metrics.json').read_text())
    corpus=json.loads((OUT/'corpus_after.json').read_text())
    dump('cross_scenarios.json', {k:v for k,v in after.items() if 'pr_play_46_' in k and 'test_cross_scenario' in k})
    dump('narrative_freedom.json',[r for r in corpus if r['group'] in ('harmless','ambiguous')])
    dump('residual_failures.json',[r for r in corpus if r['id'] in
        metrics['after']['false_negatives']+metrics['after']['false_positives']])
    lines=['# Category results','', 'Positive means clearly unsupported assertion; ambiguous excluded from headline metrics.','',
           '| Category | Group | Cases | Rejected | Accepted |','|---|---|---:|---:|---:|']
    for category,groups in metrics['after']['by_category'].items():
        for group,row in groups.items():
            lines.append(f"| {category} | {group} | {row['total']} | {row['rejected']} | {row['total']-row['rejected']} |")
    (OUT/'CATEGORY_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    summary={'verdict':'C — FAIL','bounded_patch_original_cases_pass':True,'corpus_size':len(corpus),
        'metrics':metrics['after'],'regressions':comparison,'campaign_data_unchanged':integrity['unchanged'],
        'next_step':'Offline opt-in engine-controlled renderer prototype; no follow-up initiated.'}
    dump('summary.json',summary)
    review=ROOT/'handoff/CURRENT_REVIEW.md'
    shutil.copyfile(OUT/'PR_PLAY_46_REPORT.md',review)
    excluded={'MANIFEST.json','archive_verification.json','archive_path.txt'}
    included=[p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and
              'predecessor' not in p.parts and p.name not in excluded]
    from dotenv import dotenv_values
    env={**dotenv_values(ROOT/'.env'),**os.environ}
    secrets=[v.encode() for k,v in env.items() if isinstance(v,str) and len(v)>8 and
             any(w in k.lower() for w in ('key','token','secret','password','credential'))]
    hits=[p.relative_to(OUT).as_posix() for p in included if any(s in p.read_bytes() for s in secrets)]
    dump('credential_scan.json',{'files_scanned':len(included),'credential_hits':hits,'passed':not hits})
    assert not hits, 'Credential scan failed; nothing packaged'
    if OUT/'credential_scan.json' not in included: included.append(OUT/'credential_scan.json')
    dump('MANIFEST.json',{p.relative_to(OUT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in included})
    included.append(OUT/'MANIFEST.json')
    # America/New_York is UTC-5 on the client date, 2026-11-02.
    now=datetime.now(timezone(timedelta(hours=-5)))
    archive=ROOT/'handoff'/f'CURRENT_REVIEW({now:%Y%m%d-%H%M%S}).zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in included:z.write(p,p.relative_to(OUT).as_posix())
        z.write(review,'CURRENT_REVIEW.md')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        m=json.loads(z.read('MANIFEST.json'))
        assert all(hashlib.sha256(z.read(k)).hexdigest()==v['sha256'] for k,v in m.items())
    shutil.copyfile(archive,ROOT/'handoff/CURRENT_REVIEW.zip')
    dump('archive_verification.json',{'path':str(archive),'sha256':sha(archive),
         'manifest_hashes_verified':True,'testzip':None,'files':len(included)+1})
    (OUT/'archive_path.txt').write_text(str(archive),encoding='utf-8')
    print(json.dumps({'verdict':summary['verdict'],'regression_counts':comparison['final'],
        'new_regressions':comparison['new_regressions'],'data_unchanged':integrity['unchanged'],
        'archive':str(archive)},indent=2))


if __name__=='__main__':main()
