"""Prepare, verify and export PR12. Timestamped archive is written last."""
import difflib,hashlib,json,os,shutil,subprocess,sys,zipfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
from dotenv import dotenv_values
from build_evidence import table
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'artifacts/pr_play_12'
REPORTS=ROOT/'development/campaigns/product_realization/pr_play_12'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
    before=json.loads((OUT/'protected_before.json').read_text()); changed=[p for p,h in before.items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
    # NEXT_SESSION is the sole planned edit to an entry-hashed file.
    assert not set(changed)-{'docs/NEXT_SESSION.md'}, changed
    entry=OUT/'entry_sources'; entry.mkdir(exist_ok=True)
    for name in ['CURRENT_REVIEW.md','CURRENT_REVIEW.zip','REVIEW_MANIFEST.json']:
        dest=entry/('handoff_'+name)
        if not dest.exists(): shutil.copy2(ROOT/'handoff'/name,dest)
    oldpath=entry/'NEXT_SESSION.md'
    if not oldpath.exists(): shutil.copy2(ROOT/'docs/NEXT_SESSION.md',oldpath)
    summary=json.loads((OUT/'regression_summary.json').read_text())
    h=summary['headline']
    assert h['regression_passed']==878 and h['regression_failed']==14
    assert h['focused_passed']==h['focused_total']==27
    assert h['failure_classification']['preexisting failure']==14
    nexttext='''## Latest narrative architecture assessment — PR-PLAY-12

2026-10-31: **B — Conditionally ready; external review only.** Diagnostics and
isolated prototypes; no production validator/gameplay/configuration changes.
Latest local run 20261031T170523Z-92cd9d058c92 (26714/1784 tokens, nine declarations)
replays 422 through production parsing, semantics, final acceptance and rollback.
All declarations pass. Sole violation: watchers “cluster tightly” sentence passes
one-token lexical coverage then fails stricter restatement in the undeclared
consequential check. Reported runner/census paraphrases are not the rejected spans.
Removing only “tightly” commits once in a normal synthetic replay.

Four historical captures replay (two accepted, two rejected). E1–E20 reveal two
supported-wording rejection candidates and six delivered unsupported-outcome
candidates; exact hidden disclosure and NPC bribery are replaced downstream.
Character/combat/conditions/campaign/NPC/location checks hold across the corpus.
State integrity alone does not prove publication integrity. Do not remove prose
guards or treat claim IDs as semantic proof. Existing ID/text binding and legacy
observe-only adoption remain limitations; no unrelated repair was attempted.

Recommend C-led bounded hybrid: opt-in opening-only public-catalog rendering plan,
engine-authored facts/outcomes and finite presentation selectors; no arbitrary
text/update channel, no new truth owner/store/judge. Shared policy, explicit
engine-selected operation capabilities. Public catalog/required-anchor policy and
sealing integration need bounded implementation review. Ordinary turns remain on
current authority policy. Do not implement this recommendation during PR12.

Validation: 27 new focused tests pass; consolidated same-case PR11 selection
878 pass / the same 14 preexisting failures. Initial incomplete-copy, localhost and
Windows file-access failures are retained; targeted unchanged-original-source
controls resolve the environment cases without rewriting historical outcomes.
No full-suite, live-quality, hidden-paraphrase completeness or ATGB-score claim.

Minimum read: reports 02, 05, 07, 08, 09, 10 under
development/campaigns/product_realization/pr_play_12/;
artifacts/pr_play_12/span_diagnostics.json, corpus.json,
prototype_results.json, regression_summary.json, entry_to_exit_integrity.json.
All ten reports and timestamped review ZIP retain original parsed captures,
historical baselines, source maps/snapshots, scoped diff and replay evidence.
Existing dirty work is preserved. No live/connectivity calls, model/config/budget
change, enabled retries, authority relaxation, persistent gameplay structures,
PR-EG integration, frozen ATGB edit, commit or push. Next action: external review
of the archive; do not execute the implementation or a live test.

'''
    old=oldpath.read_text(encoding='utf-8')
    old=old.replace('Updated 2026-10-30 / PR-PLAY-11.','Updated 2026-10-31 / PR-PLAY-12.',1)
    marker='## Latest opening authority reconciliation — PR-PLAY-11'
    assert marker in old
    (ROOT/'docs/NEXT_SESSION.md').write_text(old.replace(marker,nexttext+marker,1),encoding='utf-8')
    from build_reports import main as build_reports
    build_reports()
    regtable=table(['Lane','Selected pass','Fail','PR11 pass / fail','Same-case supplement'],[[n,r.get('passed'),r.get('failed'),str(r.get('baseline_passed'))+' / '+str(r.get('baseline_failures')),r.get('successful_same_case_supplement',[])] for n,r in summary['lanes'].items()])
    (OUT/'regression_results.md').write_text('# Consolidated final results\n\n'+regtable+'\nThese are final selected case outcomes, not a sum of every rerun. Initial and superseded attempts remain in the raw logs. Same-case original-source controls use the same unchanged production source and no live providers. Four world cases, two diagnostic setups and one provider-disabled export case are resolved this way. Fourteen failing IDs match the baseline exactly.\n\n'+table(['Failure','Classification'],[[r['test'],r['classification']] for r in summary['failures']]),encoding='utf-8')
    final=REPORTS/'10_FINAL_VERDICT_AND_HANDOFF.md'
    final.write_text(final.read_text(encoding='utf-8')+'\n## Consolidated regression selection\n\n'+regtable+'\nFull attempt history is retained. Seven initially failing same cases were resolved with passing unchanged-original-source controls; they are not counted twice. No full-suite or statistical reliability claim.\n',encoding='utf-8')
    # Actual HTTP example through the same normal pipeline, retained before copy cleanup.
    runs=OUT/'sandbox/artifacts/atgb/automated_playtests'
    examples=[]
    for p in runs.glob('*/reports/result.json'):
        r=json.loads(p.read_text(encoding='utf-8'))
        if r.get('completed_turns')==4 and (r.get('provider_usage') or {}).get('dispatched_requests')==6: examples.append(p.parent.parent)
    if examples:
        src=sorted(examples)[-1]
        shutil.copytree(src,OUT/'http_example',dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.zip','__pycache__'))
        (OUT/'http_example_source.json').write_text(json.dumps(dict(source=str(src.relative_to(ROOT)),scope='synthetic HTTP opening/T1-T4, six requests, T5 budget stop; no live test'),indent=2))
    examples=[]
    for name in ['E2','E20','E11']:
        r=json.loads((OUT/'results'/(name+'.json')).read_text())
        examples.append(dict(example_id=name,player_input='[Synthetic campaign opening; no player action]',player_input_classification=['synthetic_positive_control' if name=='E2' else 'synthetic_negative_control','boundary_case'],exact_gm_output=(r['response'].get('gm_output') or {}).get('player_facing_text'),semantic_result='Opening '+str(r['status'])+'; requested prose: '+r['text'],human_review=dict(status='PENDING_EXTERNAL_REVIEW',rationale='Agent interpretation only; no authenticated human judgment or gameplay-quality score'),evaluator_disagreement=dict(present=False),source_artifact_path='artifacts/pr_play_12/results/'+name+'.json'))
    packet=dict(schema_version='pr_play_12.synthetic_evidence.v1',campaign=dict(campaign_id='pr_play_12',run_count=24,turn_count=0,gm_boundary='Historical parsed response and synthetic corpus; no live inference'),evidence_scope='structural/runtime and provisional synthetic semantic diagnostics; not broad gameplay quality',examples=examples,selected_evidence=dict(representative_success=dict(example_id='E2'),representative_failure=dict(example_id='E20'),stress_probe=dict(example_id='E11')))
    (OUT/'evidence_manifest.json').write_text(json.dumps(packet,indent=2))
    (OUT/'evidence_summary.md').write_text('''# PR12 synthetic evidence

No player action or live model inference was performed. Four historical parsed
captures and twenty authored narration controls run through production opening
owners. E2 preserves a supported location/actor exchange and is emitted. E20
asserts 100 gold despite unchanged engine resources and is emitted: a baseline
publication gap, not a passed safety claim. E11 exact hidden fact passes early
semantics but final visibility replaces it. Full exact outputs and audits are in
results/. Interpretations remain provisional until external human review. No
ATGB score, independent generalization or broad gameplay-quality result.
''',encoding='utf-8')
    historical=json.loads((OUT/'capture_inventory.json').read_text())
    captures_ok=all(sha(ROOT/r['source'])==r['sha256'] and sha(OUT/'historical'/r['run']/'capture.json')==r['sha256'] for r in historical)
    finalchanges=[p for p,hsh in before.items() if not (ROOT/p).exists() or sha(ROOT/p)!=hsh]
    assert finalchanges==['docs/NEXT_SESSION.md'] or set(finalchanges)=={'docs/NEXT_SESSION.md'},finalchanges
    integrity=dict(entry_hashed_files=len(before),changed_entry_files=finalchanges,allowed_change='docs/NEXT_SESSION.md only; new PR12 reports/artifacts and generated handoff are separately scoped',production_game_data_static_experiments_tests_tools_scripts_unchanged=True,frozen_data_validation_atgb_unchanged=all(sha(ROOT/p)==hh for p,hh in before.items() if p.startswith('data/validation/atgb/')),original_captures_and_preserved_copies_equal=captures_ok,live_calls=0,provider_connectivity_tests=0,production_validator_changes=0,production_gameplay_changes=0,production_provider_configuration_changes=0,model_changes=0,output_budget_increases=0,enabled_automatic_retries=0,unauthorized_claim_acceptance_enabled=False,hidden_information_relaxation=False,state_authority_relaxation=False,new_persistent_gameplay_structures=False,PR_EG_integration=False,commit_or_push=False)
    assert captures_ok
    (OUT/'entry_to_exit_integrity.json').write_text(json.dumps(integrity,indent=2))
    # Incremental source diff: only the task's new code/reports and the saved entry handoff.
    pieces=list(difflib.unified_diff(oldpath.read_text(encoding='utf-8').splitlines(True),(ROOT/'docs/NEXT_SESSION.md').read_text(encoding='utf-8').splitlines(True),fromfile='entry/docs/NEXT_SESSION.md',tofile='current/docs/NEXT_SESSION.md'))
    for p in sorted(list(OUT.glob('*.py'))+list(REPORTS.glob('*.md'))):
        pieces.extend(difflib.unified_diff([],p.read_text(encoding='utf-8').splitlines(True),fromfile='/dev/null',tofile=p.relative_to(ROOT).as_posix()))
    (OUT/'source_diff.patch').write_text(''.join(pieces),encoding='utf-8')
    (OUT/'production_diff.txt').write_text('No incremental production source changes relative to the dirty entry baseline. See entry_to_exit_integrity.json and source_snapshot_hashes.json.\n')
    (OUT/'exit_status.txt').write_bytes(subprocess.check_output(['git','status','--short'],cwd=ROOT))
    # Select only this pass, not the disposable checkout or prior review ZIPs.
    paths=list(REPORTS.glob('*.md'))+list(OUT.glob('*'))
    selected=[p for p in paths if p.is_file() and p.suffix in {'.py','.md','.json','.xml','.txt','.patch'}]
    for folder in ['historical','results','source_snapshots','http_example']:
        selected.extend(p for p in (OUT/folder).rglob('*') if p.is_file() and p.suffix in {'.py','.md','.json','.jsonl','.log','.txt'})
    selected.extend([ROOT/'docs/NEXT_SESSION.md',ROOT/'docs/state_authority_model.md',ROOT/'docs/validation_layer_separation.md',ROOT/'docs/DEVELOPMENT_CONSTITUTION.md',ROOT/'docs/validation_evidence_standard.md'])
    # Include exact relevant unchanged tests, not the entire disposable checkout.
    lanes=json.loads((ROOT/'artifacts/pr_play_11/regression_runs.json').read_text())
    selected.extend(ROOT/f for row in lanes.values() for f in row['command'] if f.startswith('tests/'))
    selected=sorted(set(selected))
    config=dict(campaign_id='pr_play_12',campaign_name='PR-PLAY-12 — Narrative Realization and Authority Boundary Assessment',campaign_date='2026-10-31',purpose='Architectural assessment, deterministic experimentation and bounded planning only',objective_status='B — Conditionally ready; external review only',executive_summary='Latest nine-declaration rejection is the watchers sentence with tightly, not the reported runner/census paraphrases. A closed engine-owned opening rendering plan is recommended conditionally. 27 focused tests pass; consolidated regression 878 pass / 14 matching preexisting failures. No production or live-provider changes.',primary_report=str(final.relative_to(ROOT)),evidence_packets=['artifacts/pr_play_12'],supporting_files=[dict(path=p.relative_to(ROOT).as_posix(),role='source' if p.suffix=='.py' else 'evidence',why='Explicit PR12 report, diagnostic, source snapshot or deterministic regression evidence') for p in selected if p.name!='review_config.json'],changes=dict(production=['None'],tooling=['Isolated assessment, replay/export and finite rendering prototypes'],validation=['Four historical replays, E1–E20, prototype hostile plans and same PR11 regression selections'],documentation=['Ten reports and canonical session handoff']),testing=dict(focused='27 passed',broader='878 passed / the same 14 preexisting failures; consolidated same-case outcomes, raw reruns retained',full_suite='Not run',runtime_validation='Production parser/semantic/final gate/acceptance/rollback via synthetic SDK; localhost HTTP example through T4',model_runtime_boundary='No live inference or provider connectivity probes',new_regressions='None demonstrated; 14 failure IDs match PR11',pre_existing_failures='See regression_summary.json; all 14 retained'),decisions_requiring_human_review=['Review the operation/publication/required-anchor boundary and authorize a separate opt-in opening implementation only if satisfied'],known_problems=dict(campaign_specific=['Finite renderer choices, public catalog/obligation/sealing integration unproved; original wire bytes/full live request unavailable'],pre_existing=['Six corpus cases deliver unsupported outcomes; permissive source-ID text binding; legacy semantic adoption observe-only; fourteen regression failures']),does_not_prove=['Arbitrary paraphrase entailment, complete hidden-paraphrase safety, live adequacy, full-five feasibility, crash atomicity, broad gameplay improvement or ATGB score'],recommended_next_step='External review of this package only; do not implement or execute a live test',deferred_work=['Opt-in opening-only public-catalog rendering plan and renderer, subject to external review'],validation_evidence=dict(evidence_scope='synthetic deterministic diagnostics; no broad gameplay-quality claim'),configuration_source='artifacts/pr_play_12/review_config.json',max_file_bytes=8*1024*1024)
    (OUT/'review_config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    # Check known configured secret bytes without printing them or copying .env.
    secrets=[str(v).encode() for k,v in dotenv_values(ROOT/'.env').items() if v and len(str(v))>=8 and any(x in k.upper() for x in ['SECRET','KEY','TOKEN','PASSWORD'])]
    hits=[str(p.relative_to(ROOT)) for p in selected if any(s in p.read_bytes() for s in secrets)]
    assert not hits,'Configured secret found in selected artifact; archive not generated'
    (OUT/'redaction_verification.json').write_text(json.dumps(dict(selected_files_checked=len(selected),configured_secret_match_count=len(hits),dotenv_or_credentials_included=False,canonical_historical_responses_modified=False),indent=2))
    print(json.dumps(dict(stage='prepared',reports=len(list(REPORTS.glob('*.md'))),protected_files=len(before),original_captures_equal=captures_ok,headline=h),indent=2))

def archive():
    sys.path.insert(0,str(ROOT))
    from tools.build_review_handoff import build_handoff
    cfg=json.loads((OUT/'review_config.json').read_text())
    # Include this final verification artifact without recursively selecting ZIPs.
    for name in ['review_config.json','redaction_verification.json']:
        cfg['supporting_files'].append(dict(path='artifacts/pr_play_12/'+name,role='evidence',why='Final explicit export configuration or secret-byte verification'))
    built=build_handoff(cfg,root=ROOT,output_dir=ROOT/'handoff',archive_history=True)
    zpath=Path(built['zip_path'])
    with zipfile.ZipFile(zpath) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('REVIEW_MANIFEST.json'))
        names=z.namelist()
        assert len([n for n in names if n.startswith('support/development/campaigns/product_realization/pr_play_12/') and n.endswith('.md')])==10
        for row in manifest['included_files']:
            if row.get('sha256'): assert hashlib.sha256(z.read(row['bundle_path'])).hexdigest()==row['sha256']
        assert not any('/.env' in n or '/sandbox/' in n for n in names)
    omissions=[r for r in built['omitted'] if 'duplicate' not in str(r).lower()]
    assert not omissions,omissions
    stamp=datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-4))).strftime('%Y%m%d-%H%M%S')
    target=ROOT/'handoff'/('CURRENT_REVIEW('+stamp+').zip')
    shutil.copy2(zpath,target)
    print(json.dumps(dict(archive=str(target),bytes=target.stat().st_size,sha256=sha(target),files=built['file_count'],reports=10,verified=True,stop='External review; no implementation or live action'),indent=2))
if __name__=='__main__':
    if '--archive' in sys.argv: archive()
    else: prepare()
