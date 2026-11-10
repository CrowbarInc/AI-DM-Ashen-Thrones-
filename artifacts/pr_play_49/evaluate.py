"""Evidence analysis only. No application imports or provider requests."""
import os
os.environ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'] = '1'
import ast
import hashlib
import json
from pathlib import Path
import statistics
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'artifacts/pr_play_49'


def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))


def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def junit(name):
    rows = {}
    for t in ET.parse(OUT/name).iter('testcase'):
        status = ('failed' if t.find('failure') is not None else
                  'error' if t.find('error') is not None else
                  'skipped' if t.find('skipped') is not None else 'passed')
        rows[t.get('classname')+'::'+t.get('name')] = status
    return rows


def main():
    before, after = junit('baseline.xml'), junit('final.xml')
    extra = junit('final_focused.xml')
    combined = {**after, **extra}
    changes = {k: [v, combined.get(k)] for k,v in before.items() if combined.get(k) != v}
    counts = lambda rows: {'collected':len(rows), **{
        s:sum(v==s for v in rows.values()) for s in ('passed','failed','error','skipped')}}
    regression = {'baseline': counts(before), 'final_full':counts(after),
                  'final_focused':counts(extra), 'combined_unique':counts(combined),
                  'changed_existing_results':changes,
                  'pre_existing_failures':[k for k,v in before.items() if v=='failed'],
                  'new_test_results':{k:v for k,v in combined.items() if k not in before},
                  'initial_integration_failure':'PR47 static isolation disallowed importing its renderer. Fixed by extracting unchanged read-only functions into shared offline helper. Test expectations unchanged. initial_final.xml/txt preserved.',
                  'initial_focused_failure':'Saved engine summary uses discovered_clues rather than clue_text. Fixed evidence reader; focused.xml preserves development failure.'}
    assert not changes
    assert all(v=='passed' for k,v in combined.items() if k not in before)
    write('regression_comparison.json', regression)
    corpus = [json.loads(p.read_text()) for p in sorted(OUT.glob('evidence_corpus_*.json'))]
    unsafe = [r for r in corpus if not r['expected_safe']]
    safe = [r for r in corpus if r['expected_safe']]
    metrics = {'cases':len(corpus), 'unsafe':len(unsafe), 'safe':len(safe),
               'true_rejects':sum(r['output']['used_fallback'] for r in unsafe),
               'false_accepts':sum(r['false_accept'] for r in corpus),
               'true_accepts':sum(not r['output']['used_fallback'] for r in safe),
               'false_rejects':sum(r['false_reject'] for r in corpus),
               'coverage':'authored corpus only; not population accuracy or semantic proof',
               'false_accept_cases':[r['case'] for r in corpus if r['false_accept']],
               'false_reject_cases':[r['case'] for r in corpus if r['false_reject']],
               'raw_existing_validator_false_accepts':sum(r['raw_existing_validator']['hard_valid'] for r in unsafe)}
    write('semantic_metrics.json', metrics)
    write('adversarial_corpus.json', corpus)
    write('residual_failures.json', [r for r in corpus if r['false_accept'] or r['false_reject']])
    matrix = [json.loads(p.read_text()) for p in sorted(OUT.glob('evidence_fixture_*.json'))]
    write('scenario_matrix.json', matrix)
    expressions = {json.loads(p.read_text())['style']:json.loads(p.read_text())
                   for p in OUT.glob('evidence_expression_*.json')}
    families = {
        'direct_action':['concise'],
        'setting_contrast_to_attention':['atmospheric','sensory'],
        'fragment_led_cadence':['tense','fast_paced'],
        'ordered_close_reading':['observational','methodical'],
        'gesture_framed_examination':['character_focused'],
        'reflection_then_action':['reflective'],
        'negative_emphasis_then_quiet_turn':['understated'],
    }
    controlled = read('evidence_controlled_fixed_comparator.json')
    expressive = {'candidate_count':len(expressions), 'unique_texts':len({r['candidate'] for r in expressions.values()}),
                 'recognizable_structural_families':len(families), 'family_assignments':families,
                 'controlled_families':len({r['family'] for r in controlled}),
                 'controlled_same_outcome_outputs':controlled,
                 'assessment':{
                     'sentence_structure':'Seven conservative rhetorical families; fragment styles, ordered searches and setting contrasts are merged, not counted independently.',
                     'pacing':'Brief direct action, staccato fragments, sequential reading, and longer contrast/reflection paragraphs.',
                     'information_order':'All discoveries remain last by design; order within the descriptive prelude varies. No claim of unlimited plot ordering.',
                     'sensory_detail':'Rain and crowd sound draw on the public scene; gesture and attention remain incidental.',
                     'cohesion':'All lead into the same clue. The fixed paragraph break remains audible, particularly after the reflective and understated openings.',
                     'repetition':'Shared board/patrol references remain; generic neutral matrix prelude is deliberately repetitive and shows no expressive gain.',
                     'naturalness':'Editorially broader than enum templates; fragments may feel mannered, and hand selection favors the prototype.',
                     'mechanical_consistency':'All ten reviewed examples retain exact discovery and add no consequences.',
                 },
                 'origin':'New illustrative prose authored by implementing agent, not provider output',
                 'provisional':True}
    assert expressive['candidate_count']==10 and len(families)>=6
    write('expressive_range.json', expressive)
    categories = ['information_completeness','mechanical_consistency','naturalness',
                  'expressive_range','atmosphere','investigative_clarity','repetition','cohesion']
    # Explicit editorial ratings, not a computed classifier or independent panel.
    anchored_scores = {
        'concise':[2,2,2,2,0,2,2,2],
        'atmospheric':[2,2,2,2,2,2,2,2],
        'tense':[2,2,1,2,1,2,2,1],
        'observational':[2,2,2,2,0,2,1,2],
        'methodical':[2,2,2,2,0,2,1,2],
        'character_focused':[2,2,2,2,1,2,2,2],
        'sensory':[2,2,2,2,2,2,2,2],
        'reflective':[2,2,1,2,1,2,2,1],
        'fast_paced':[2,2,1,2,1,2,1,2],
        'understated':[2,2,2,2,0,2,2,1],
    }
    notice = next(r for r in matrix if r['id']=='frontier_gate')
    def rating(text, scores, reason):
        return {'text':text,'scores':dict(zip(categories,scores)),
                'total_of_16':sum(scores), 'mechanical_correctness_of_2':scores[1],
                'narrative_of_12':sum(scores[2:]), 'reason':reason}
    comparison = {
        'same_outcome':'frontier_gate notice_board; identical engine discovery',
        'rubric':'0=absent/incorrect or strongly weak; 1=adequate/limited; 2=complete/strong. Expressive range rates the approach corpus, not uniqueness of one string. Repetition 2 means little avoidable repetition.',
        'rater':'Unblinded implementing-agent editorial assessment; provisional, not player preference or actual model quality.',
        'host':[rating(notice['host']['text'],[2,2,1,0,0,2,1,2],
                       'Complete and clear; inspect notice board reads mechanically; no atmosphere or generated variation.')],
        'controlled':[rating(r['narration'], [2,2,1,1,0 if r['plan']['detail']=='lean' else 1,2,
                                             1 if r['plan']['detail']=='lean' else 0,
                                             2 if r['plan']['detail']=='lean' else 1],
                        'Exact clue and approved variation; repeated attention/pause language and generic whole-to-detail phrasing limit voice.')
                      for r in controlled],
        'anchored':[rating(expressions[style]['output']['preview_text'], scores,
                       'Handcrafted variation; see structural grouping. Sparse variants lack atmosphere; fragment/reflection variants can sound mannered. Exact engine clue preserved.')
                    for style,scores in anchored_scores.items()],
    }
    comparison['means'] = {k:{'total_of_16':statistics.mean(r['total_of_16'] for r in comparison[k]),
                            'mechanical_of_2':statistics.mean(r['mechanical_correctness_of_2'] for r in comparison[k]),
                            'narrative_of_12':statistics.mean(r['narrative_of_12'] for r in comparison[k])}
                           for k in ('host','controlled','anchored')}
    write('quality_comparison.json', comparison)
    data_after = {p.relative_to(ROOT/'data').as_posix():sha(p)
                  for p in (ROOT/'data').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    assert data_after == read('data_before.json')
    original = ROOT/'artifacts/pr_play_48/source_reviewed/game/controlled_investigation_renderer.py'
    old_tree = ast.parse(original.read_text())
    shared_tree = ast.parse((ROOT/'game/offline_investigation_projection.py').read_text())
    controlled_tree = ast.parse((ROOT/'game/controlled_investigation_renderer.py').read_text())
    def definitions(tree):
        return {n.name:ast.dump(n) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    old, shared, retained = definitions(old_tree),definitions(shared_tree),definitions(controlled_tree)
    assert all(old[k]==v for k,v in shared.items())
    assert all(old[k]==v for k,v in retained.items())
    write('state_integrity.json', {'all_campaign_data_hashes_unchanged':True,
          'files_checked':len(data_after), 'projection_and_fallback_ast_unchanged':list(shared),
          'retained_controlled_renderer_definitions_ast_unchanged':list(retained),
          'existing_tests_modified':False, 'state_sinks':read('evidence_isolation.json'),
          'scope':'Existing code definitions identical before/after extraction; all tests run with provider guards, broad suites in disposable workspace.'})
    source_names = ['game/anchored_investigation_narration.py', 'game/offline_investigation_projection.py',
                    'game/controlled_investigation_renderer.py','tests/test_pr_play_49_anchored_narration.py',
                    'artifacts/pr_play_49/run_regression.py','artifacts/pr_play_49/evaluate.py',
                    'artifacts/pr_play_49/package_review.py']
    write('source_change_manifest.json', {n:{'sha256':sha(ROOT/n), 'bytes':(ROOT/n).stat().st_size,
          'change':'extracted existing read-only definitions, re-exported same symbols; renderer unchanged' if n.endswith('/controlled_investigation_renderer.py') else 'new file'} for n in source_names})
    write('provider_usage.json', {'real_provider_requests':0,'real_provider_input_tokens':0,
          'real_provider_output_tokens':0,'provider_retries':0, 'live_gameplay':0,
          'preflight_skip_before_application_imports':True, 'models_or_budgets_changed':False,
          'enforcement':'tests/conftest.py autouse live_model_guard blocks constructors and live entry points; renderer has no transport; runners set skip environment before imports.'})
    write('summary.json', {'verdict':'A — PASS / GO for quarantined saved-outcome provider experiment only',
          'go':True, 'mechanical_authority':'structural read-only isolation',
          'authorized_anchors':'preserved in 8 fixtures and 10 expressive variants, failures and fallback',
          'hidden_provider_inputs':'explicit final allowlist; trusted public authoring',
          'semantic_safety':'not guaranteed; 17/30 unsafe cases heuristically pass and require rejection by review',
          'semantic_metrics':metrics,'structural_families':len(families),
          'quality_means':comparison['means'],'regression':regression['combined_unique'],
          'new_regressions':changes,'provider_requests':0,'provider_tokens':0})
    print(json.dumps({'regression':regression['combined_unique'],'metrics':metrics,'quality':comparison['means']},indent=2))


if __name__=='__main__': main()
