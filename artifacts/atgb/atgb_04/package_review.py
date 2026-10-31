"""Explicit-source standard handoff preparation; entirely offline."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from tools.build_review_handoff import build_handoff


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


before = json.loads((OUT / 'preservation_before.json').read_text(encoding='utf-8'))
changed = [p for p, digest in before.items() if not (ROOT / p).is_file() or
           hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != digest]
assert not changed, changed
write(OUT / 'preservation_checks.json', {'protected_file_count': len(before), 'all_unchanged': True,
                                       'changed': changed, 'provider_requests_in_ATGB_04': 0})
write(OUT / 'validation_results.json', {
    'focused_tests': '10 passed; tests/test_atgb_human_review.py',
    'form_checks': 'Offline JavaScript DOM-stub roundtrip and exact trial checks passed; 37 articles, 222 blank selects.',
    'source_checks': '37/37 exact inputs/responses and prior same-trial exchanges; six opening flags; historical S04 separate.',
    'blank_report': 'No entered human judgments; all partition performance percentages null.',
    'preservation': f'{len(before)} pre-existing protected files unchanged.',
    'browser_preview': 'file: protocol refused by browser URL policy; no workaround attempted; rendered layout unverified.',
    'provider_requests': 0, 'gameplay_execution': 'none', 'full_suite': 'not run; offline evaluation preparation only',
    'human_evaluation': 'pending', 'gameplay_performance_claim': False})

session = ROOT / 'docs/NEXT_SESSION.md'
text = session.read_text(encoding='utf-8')
if '`ATGB-04 — Independent human evaluation preparation`' not in text:
    text = text.replace('## Last Completed Cycle\n', '''## Last Completed Cycle

`ATGB-04 — Independent human evaluation preparation`: authoritative 37-turn index,
complete conversation review document and offline HTML form, blank scoring forms,
human-judgment aggregation tool, setup qualifications and provenance prepared.
Original S01–S03; S04 full trial 2; S05–S10 trial 1. Historical partial S04 trial 1
is separate. S07/S09 opening-dependent criteria require special human review.
All judgments blank; no gameplay-performance baseline claimed. Ten focused
offline checks and form roundtrip checks passed. Production, prior evidence,
corpus/rubric/baseline and canonical data preserved; no provider requests.
Report: `development/reports/atgb_04_human_evaluation_preparation.md`.
Start: `artifacts/atgb/atgb_04/README.md` and `review.html` or
`conversational_review.md`. Standard review: `handoff/CURRENT_REVIEW.zip`.
Rendered HTML preview was blocked by the browser's local-file URL policy;
offline structure/JavaScript checks passed. Markdown review is available.
Stop and await independent human evaluation. No commit; dirty worktree retained.
The ATGB-03C and earlier entries below are preserved execution history.
''', 1)
    text = text.replace('## Current Objective\n', '''## Current Objective

ATGB-04 preparation is complete. Await independent human judgments. Extract
`handoff/CURRENT_REVIEW.zip`; review `support/artifacts/atgb/atgb_04/review.html`
or the Markdown document, save each reviewer's separate export, and aggregate
using the packaged `report_human_review.py` instructions. No live reruns,
automatic/LLM judging, gameplay repairs, criterion changes or new Product
Realization campaign. Unsupported criteria remain uncertain/not_evaluated;
do not presume opening delivery. Historical S04 trial 1 is excluded from the
37-turn reporting. No performance baseline until human review is supplied.
The ATGB-03C objective below is retained historical context.
''', 1)
    text += '\n2026-10-18 / ATGB-04: independent review package prepared; await human evaluation.\n'
    session.write_text(text, encoding='utf-8')

selected = [
    'docs/DEVELOPMENT_CONSTITUTION.md', 'docs/validation_evidence_standard.md',
    'docs/review_handoff_standard.md', 'docs/product_realization_validation.md', 'docs/NEXT_SESSION.md',
    'development/reports/atgb_01_conversational_benchmark_design.md',
    'development/reports/atgb_01_scenario_catalog.md',
    'development/reports/atgb_02_benchmark_specification.md',
    'development/reports/atgb_02a_readiness.md',
    'development/reports/atgb_03_initial_live_baseline.md',
    'development/reports/atgb_03c_live_baseline_continuation.md',
    'data/validation/atgb/corpus.json',
    'data/validation/atgb/baselines/frontier-gate-v1/manifest.json',
    'artifacts/atgb/atgb_03/configuration_and_provenance.json',
    'artifacts/atgb/atgb_03/scenario_status.json',
    'artifacts/atgb/atgb_03c/provenance_before.json',
    'artifacts/atgb/atgb_03c/scenario_readiness.json',
    'artifacts/atgb/atgb_03c/opening_context.json',
    'artifacts/atgb/atgb_03c/baseline_coverage.json',
    'artifacts/atgb/atgb_03c/provider_accounting.json',
    'artifacts/atgb/atgb_03c/combined_baseline_worksheet.json',
    'artifacts/atgb/atgb_03c/combined_baseline_worksheet.md',
    'artifacts/atgb/atgb_03c/combined_baseline_review_source.json',
    'tools/atgb/prepare_human_review.py', 'tools/atgb/report_human_review.py',
    'tests/test_atgb_human_review.py',
    'data/validation/review_handoffs/atgb_04_human_evaluation_preparation.json',
]
for n in range(1, 11):
    sid = f'S{n:02}'
    selected += [f'data/validation/atgb/{"held_out" if n in (7, 9, 10) else "visible"}/{sid}.json']
    base = f'artifacts/atgb/{"atgb_03" if n <= 3 else "atgb_03c"}/{sid}/'
    selected += [base + name for name in ('result.json', 'transcript.md', 'worksheet.json', 'provider_usage.jsonl')]
selected += ['artifacts/atgb/atgb_03/S04/' + name for name in ('result.json', 'transcript.md', 'worksheet.json')]
selected += ['artifacts/atgb/atgb_04/' + name for name in (
    'README.md', 'review.html', 'conversational_review.md', 'review_index.json', 'review_index.md',
    'blank_judgments.json', 'blank_scoring_forms.md', 'approved_rubric_excerpt.md',
    'scenario_qualifications.md', 'evidence_provenance.md', 'evidence_sources.json',
    'historical_S04_trial_1.md', 'pending_report.json', 'preservation_before.json',
    'preservation_checks.json', 'validation_results.json', 'focused_tests.txt',
    'check_form.cjs', 'package_review.py', 'verify_package.py')]
config = {
    'campaign_id': 'atgb_04_human_evaluation_preparation',
    'campaign_name': 'ATGB-04 Independent Human Evaluation Preparation',
    'campaign_date': '2026-10-18',
    'purpose': 'Prepare the preserved conversational baseline for independent human judgment without gameplay changes or provider requests.',
    'objective_status': 'REVIEW PACKAGE PREPARED; HUMAN EVALUATION PENDING',
    'executive_summary': '37 unique turns indexed exactly once: original S01–S03, S04 full trial 2, S05–S10 trial 1. Original partial S04 trial 1 remains separate. Extract the ZIP and open support/artifacts/atgb/atgb_04/README.md, then review.html or conversational_review.md. All human judgments are blank. S07/S09 opening delivery limits require special review. No gameplay-performance baseline is claimed. Existing packet empty outcome categories mean unmeasured, never zero failures.',
    'changes': {
        'production': [],
        'validation': ['No scenario, expectation, rubric, partition or benchmark version changes. Ten offline integrity/aggregation tests added.'],
        'tooling': ['Two offline review preparation/aggregation tools; no gameplay imports or provider calls.'],
        'documentation': ['ATGB-04 preparation report and current session orientation.'],
        'generated_artifacts': ['37-turn index; complete HTML/Markdown conversations; blank forms; pending report; scenario qualifications; source hashes and standard ZIP.']},
    'testing': {
        'focused': '10 tests passed. Offline JavaScript form collect/export/import and wrong-trial rejection passed. Exact source text, prior context, blank fields and null rates verified.',
        'broader': 'Not run; no gameplay code changed.', 'full_suite': 'Not run.',
        'runtime_validation': 'No new gameplay execution or provider requests. Reuses preserved 37-turn evidence. HTML browser preview blocked by file: URL policy; rendered layout unverified.',
        'model_runtime_boundary': 'Original live-enabled production API evidence, gpt-4.1-mini, sampling uncontrolled; host-owned responses possible. ATGB-04 runs offline only.',
        'new_regressions': 'No gameplay regression claim. Protected sources are byte-identical.',
        'pre_existing_failures': 'Original infrastructure stop, missing telemetry, S07/S09 opening delivery limits and extensive dirty worktree retained.'},
    'known_problems': {'campaign_specific': ['All human judgments pending; no evaluated performance rates.', 'Rendered HTML layout unverified; full Markdown review available.'],
                       'pre_existing': ['S07/S09 opening not delivered before first turn; unsupported criteria require uncertain/not_evaluated.', 'Held-out previously exposed; single environment and selected trials; bounded state evidence.']},
    'decisions_requiring_human_review': ['Independently enter interpretation, response, authority, severity, clarification, continuity and reviewer explanations. Retain separate reviewer exports and disagreements.',
                                       'Assess criterion support under S07/S09 opening limitations; never score missing setup automatically as gameplay failure.'],
    'missing_concepts': ['No opening injection, automated eligibility decision, LLM judge, new universal score or gameplay repair is implemented.'],
    'does_not_prove': ['Completed gameplay-performance baseline, gameplay improvement, independent unseen generalization, stable multi-trial performance, browser rendering, broad regression or SDK request bounds.'],
    'recommended_next_step': 'Stop and await independent human evaluation. Open support/artifacts/atgb/atgb_04/review.html or conversational_review.md, save the human export, then use the packaged reporting tool per README.md. No provider requests, reruns or new Product Realization campaign.',
    'primary_report': 'development/reports/atgb_04_human_evaluation_preparation.md',
    'evidence_packets': ['artifacts/atgb/atgb_03c/behavioral_evidence'],
    'self_contained_review_test': 'verify_package.py checks ZIP CRC, required standard sections, source hashes, exact 37-turn/trial selection, prior context, blank form structure and null rates, and executes reporting from an isolated extraction. Existing outcome categories remain unmeasured.',
    'configuration_source': 'data/validation/review_handoffs/atgb_04_human_evaluation_preparation.json',
    'supporting_files': [{'path': p, 'role': 'independent_human_review_material',
                          'why': 'Explicitly selected authority, evidence, provenance or offline human-review tool; all judgments pending.',
                          'behavioral_evidence': p.endswith(('transcript.md', 'result.json', 'review.html', 'conversational_review.md')),
                          'human_review_required': True} for p in sorted(set(selected))]}
config_path = ROOT / config['configuration_source']
write(config_path, config)
staging = OUT / 'export'
result = build_handoff(config, output_dir=staging, archive_history=False)
# Publish completed generated files by replacement, avoiding Windows in-place ZIP writes.
handoff = ROOT / 'handoff'
history = handoff / 'history' / config['campaign_id']
history.mkdir(parents=True, exist_ok=True)
for name, archived in [('CURRENT_REVIEW.md', 'REVIEW.md'),
                       ('REVIEW_MANIFEST.json', 'REVIEW_MANIFEST.json'),
                       ('CURRENT_REVIEW.zip', 'REVIEW.zip')]:
    shutil.copyfile(staging / name, history / archived)
    os.replace(staging / name, handoff / name)
print(json.dumps({'standard_handoff': 'handoff/CURRENT_REVIEW.zip',
                  'history': history.relative_to(ROOT).as_posix(),
                  'file_count': result['file_count']}, indent=2))
