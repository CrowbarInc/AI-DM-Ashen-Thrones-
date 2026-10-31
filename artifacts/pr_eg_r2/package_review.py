"""Package R2 with the existing review workflow, retaining predecessor archives."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tools.build_review_handoff import build_handoff
excluded={'local_dependencies','tokenizer_cache','disposable_state','pytest_tmp','pytest_local','__pycache__'}
include=[p for p in HERE.rglob('*') if p.is_file() and not excluded.intersection(p.relative_to(HERE).parts)
 and p.name not in {'handoff_config.json','bundle_verification.json','09_TOKEN_COST_ATTRIBUTION.md'}]
config={
 'campaign_id':'pr_eg_r2_generative_dialogue_boundary_20261016',
 'campaign_name':'PR-EG-R2 — Generative Dialogue Boundary Investigation',
 'campaign_date':'2026-10-16',
 'purpose':'Investigate compact dialogue provider capability, authority enforcement, cost and integration feasibility. No production implementation.',
 'objective_status':'D — FURTHER INVESTIGATION REQUIRED',
 'executive_summary':(HERE/'01_EXECUTIVE_SUMMARY.md').read_text(encoding='utf-8'),
 'changes':{'production':['None. All 316 protected game/source and active-data files unchanged.'],
  'validation':['Existing validator/preseal functions exercised on all 130 provider outputs and 18 labeled controls; no production validation changes.'],
  'tooling':['Isolated synthetic provider, prompt-capture, local tokenizer, persistence and report scripts under artifacts/pr_eg_r2.'],
  'documentation':['Twenty-one required reports, source snapshots, retained predecessor evidence and exact prompts/outputs.'],
  'generated_artifacts':['130 A–G matrix responses, one access response, one failed transport attempt, source hashes, 71-pass focused junit, local prompt attribution.']},
 'testing':{'focused':'71 existing tests passed in 3.71s (focused_local_junit.xml). Initial sandbox temp/socket failures retained and classified.',
  'broader':'Historical R1 family 393 passed / 19 failed; not rerun.',
  'full_suite':'Not run; no production edits.',
  'runtime_validation':'130 isolated provider matrix responses, eight continuous transcripts (34 turns), plus one access probe. No production compact-generation qualification.',
  'model_runtime_boundary':'gpt-4.1-mini, returned gpt-4.1-mini-2025-04-14. Explicit OpenAI Responses endpoint, default sampling parameters, 500 output cap, SDK retries disabled.',
  'new_regressions':'No new failure in 71 focused tests. Full family not measured.',
  'pre_existing_failures':'Nineteen historical R1 family failures, not independently re-established.'},
 'known_problems':{'campaign_specific':['Repeated consequential provider claims under speculation and personal elaboration.',
   'Validator false acceptance and false rejection; preseal sometimes destroys harmless wording and sometimes retains unsafe speech.',
   'No safe minimum context or full-chain compact qualification established.',
   'Fresh full-prompt baseline requests blocked by automatic approval review; local tokenizer and historical measurements used.'],
  'pre_existing':['Large first social prompt, rigid reuse and inherited regression debt.']},
 'missing_concepts':['Semantic per-claim authorization for quoted/hedged consequential statements.',
  'Explicit per-turn topic and transaction roles without a second authority system.',
  'Stable incidental commitment identity/contradiction handling.'],
 'decisions_requiring_human_review':['Review D — further investigation required.',
  'Do not implement R3 or begin PR-EH from this package.',
  'Optional approval question covers the exact two synthetic full-prompt baseline payloads; it is not required for the local R2 findings.'],
 'does_not_prove':['That compact generation is safe in production.',
  'That direct validator/preseal results are complete final-emission outcomes.',
  'That hidden-information tests with secret bodies excluded prove arbitrary disclosure resistance.',
  'That measured small synthetic prompts yield the same savings or latency in a qualified production path.',
  'That all inherited full-family regression failures are unchanged.'],
 'recommended_next_step':'External review of R2. Further bounded enforcement/context investigation only if separately authorized. Stop; no automatic PR-EG-R3 or PR-EH.',
 'primary_report':'artifacts/pr_eg_r2/01_EXECUTIVE_SUMMARY.md',
 'max_file_bytes':5*1024*1024,'evidence_packets':[],
 'supporting_files':[{'path':p.relative_to(ROOT).as_posix(),'role':'production_source_snapshot' if 'sources' in p.parts else 'evidence',
  'why':'R2 exact source, report, experiment or explicitly labeled historical evidence.',
  'behavioral_evidence':p.suffix in {'.json','.jsonl','.xml'},'human_review_required':p.suffix=='.md'} for p in sorted(include)],
 'self_contained_review_test':'21 numbered reports, all prompts/outputs, controls and measurements, source snapshots/hashes, predecessor context. Credentials, active saves, dependencies and disposable temp trees excluded.'}
(HERE/'handoff_config.json').write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')
result=build_handoff(config,root=ROOT,output_dir=ROOT/'handoff',archive_history=True)
print(json.dumps({k:result[k] for k in ['summary_path','zip_path','file_count','zip_size_bytes','warning']}))
print(json.dumps({'omitted_count':len(result['omitted']),'nonduplicate_omissions':[r for r in result['omitted'] if not r['reason'].startswith('duplicate content')]}))
