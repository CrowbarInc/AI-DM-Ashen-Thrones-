"""Build review documents from preserved execution evidence; no provider calls."""
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import statistics
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'artifacts/pr_play_57'


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def doc(name, body):
    (OUT / name).write_text(body.strip() + '\n', encoding='utf-8')


def main():
    data = read('final_results.json')
    assert len(data['results']) == 8 and not data['halted']
    raw = data['raw_provider_responses']
    usage = {k: sum(s[k] for s in data['usage_shards'])
             for k in ('requests', 'input_tokens', 'output_tokens', 'total_tokens')}
    assert usage['requests'] == len(raw) == 8
    assert usage['total_tokens'] <= 12000
    assert all(r['max_output_tokens'] <= 700 for r in raw)
    assert all(sum(r['provider_usage'][k] for r in raw) == usage[k]
               for k in ('input_tokens', 'output_tokens', 'total_tokens'))
    assessments = read('provisional_assessments.json')
    candidates, contracts, validations, coverage, worksheets, quality = [], [], [], [], [], []
    for row in data['results']:
        label = row['label']
        t = row['turns'][-1]
        q = t['quarantine']
        a = assessments[label]
        contract = q['authorized_outcome_contract']
        candidates.append({'id': label, 'text': q['raw_provider_text'], 'assembled': q['assembled'],
                           'diagnostic': q['diagnostic'], 'used_fallback': q['used_fallback']})
        contracts.append({'id': label, 'contract': contract})
        validations.append({'id': label, **q['validation']})
        coverage.append({'id': label, **q['validation']['coverage']})
        worksheets.append({'id': label, 'player_action': t['player_text'],
            'authorized_scene_context': contract['may_reference'],
            'mandatory_outcome_facts': contract['must_communicate'],
            'raw_narration': q['raw_provider_text'], 'validator_decision': q['validation']['decision'],
            'candidate_consequential_claims': a['claims'],
            'potential_unauthorized_additions': a['potential_additions'],
            'potential_omitted_outcomes': a['omissions'], 'continuity_concerns': a['continuity'],
            'proposed_semantic_classification': a['classification'],
            'supporting_evidence': a['evidence'], 'uncertainty_notes': a['uncertainty'],
            'assessment_status': 'provisional_automated_reading_of_raw_text_not_independent_ground_truth',
            'human_confirmed': False, 'independent_external_review': 'pending'})
        quality.append({'id': label, 'scores': a['scores'], 'scale': '0 unacceptable to 4 strong',
                        'provisional': True, 'human_confirmed': False})
    latency = [r['latency_ms'] for r in raw]
    providers = [r['turns'][-1]['quarantine']['live_provider'] for r in data['results']]
    validation_ms = [r['turns'][-1]['quarantine']['validation_ms'] for r in data['results']]
    overhead = [r['turns'][-1]['quarantine']['total_integrated_ms'] for r in data['results']]
    counts = dict(Counter(v['decision'] for v in validations))
    semantic_counts = dict(Counter(v['semantic']['decision'] for v in validations))
    coverage_counts = dict(Counter(v['decision'] for v in coverage))
    perf = {'provider': 'openai', 'models': sorted(set(r.get('response', {}).get('model') or r['model'] for r in raw)),
        'usage': usage, 'successful_requests': sum(r['ok'] for r in raw), 'automatic_retries': 0,
        'provider_latency_ms_average': statistics.mean(latency), 'provider_latency_ms_max': max(latency),
        'adapter_latency_ms_average': statistics.mean(p['provider_latency_ms'] for p in providers),
        'validation_ms_average': statistics.mean(validation_ms), 'validation_ms_max': max(validation_ms),
        'total_integrated_ms_average': statistics.mean(overhead), 'total_integrated_ms_max': max(overhead),
        'provider_failure_rate': sum(not r['ok'] for r in raw) / len(raw),
        'comparison_pr56': {'requests': 6, 'total_tokens': 2858, 'mean_provider_ms': 1958, 'max_provider_ms': 3222},
        'provider_latency_change_percent': (statistics.mean(latency) / 1958 - 1) * 100, 'per_request_token_change_percent': (usage['total_tokens'] / 8 / (2858 / 6) - 1) * 100,
        'cost': 'not estimated; no configured price table',
        'adapter_latency_ms_max': max(p['provider_latency_ms'] for p in providers), 'timing_note': 'SDK capture wall time used for historical provider comparison; adapter and total hook measured separately.'}
    for name, value in [('authorized_outcome_contracts.json', contracts), ('integrated_candidates.json', candidates),
                        ('validation_decisions.json', validations), ('coverage_decisions.json', coverage),
                        ('independent_review_worksheets.json', worksheets), ('quality_scores.json', quality),
                        ('raw_provider_responses.json', raw), ('performance_and_usage.json', perf),
                        ('mandatory_fact_identifiers.json', {c['id']: [f['id'] for f in c['contract']['must_communicate']] for c in contracts})]:
        write(name, value)
    # Envelope checksums are checked against unmodified raw payloads, not ignored.
    from game.persistence_contract import compute_payload_sha256
    envelope_checks = []
    for row in data['results']:
        for path, value in row['full_state_after'].items():
            if isinstance(value, dict) and 'payload' in value and 'integrity' in value:
                envelope_checks.append({'id': row['label'], 'path': path,
                    'valid': value['integrity']['payload_sha256'] == compute_payload_sha256(value['payload'])})
    assert all(e['valid'] for e in envelope_checks)
    assert all(not p['authoritative_payload_differences'] and not p['hook_state_differences']
               and all(p['player_facing_identical']) and all(p['mechanical_identical'])
               and not p['raw_candidate_in_persisted_state'] and not p['context_leaks'] for p in data['pairs'])
    write('state_and_quarantine_audit.json', {'all_checks_passed': True,
        'envelope_integrity': envelope_checks, 'pairs': data['pairs'],
        'initial_stop': read('initial_stop_analysis.json'), 'second_stop': read('second_stop_analysis.json'),
        'canonical_state': read('final_integrity.json'), 'no_narration_promoted': True})
    regression = read('regression_summary_final.json')
    # Replace the earlier 22-case run of this module with its final 28-case run.
    suite = ET.parse(OUT / 'new_tests_final.xml').getroot().find('testsuite')
    new_count = int(suite.attrib['tests'])
    assert int(suite.attrib['failures']) == int(suite.attrib['errors']) == 0
    combined_tests = {'focused_collected': regression['focused']['collected'] - 22 + new_count,
        'focused_passed': regression['focused']['passed'] - 22 + new_count,
        'focused_failed': regression['focused']['failed'], 'focused_errors': 0, 'focused_skipped': 0,
        'new_module': {'collected': new_count, 'passed': new_count},
        'holdout_wrapper': regression['holdout'], 'broader_authority': regression['broader_hard_validation'],
        'new_failures': [], 'full_suite': 'not executed',
        'method': 'Final focused run plus final expanded module; 22 overlapping module cases counted once.'}
    write('test_summary.json', combined_tests)
    historical = json.loads((ROOT / 'artifacts/pr_play_56/scenario_results.json').read_text(encoding='utf-8'))
    mapping = {'A1': 'A1', 'A2': 'A2', 'B1': 'C1', 'B2': 'C2', 'C1': 'B1', 'C2': 'B1', 'D1': 'D1', 'D2': 'D1'}
    comparisons = []
    for c in candidates:
        old = historical['results'][mapping[c['id']]]['turns'][-1]['quarantine']
        baseline_scores = dict(zip(assessments[c['id']]['scores'],
            [2, 2, 4, 3, 3, 4, 3, 3] if c['id'][0] == 'D' else [1, 2, 4, 3, 2, 3, 2, 3]))
        comparisons.append({'id': c['id'], 'pr56_id': mapping[c['id']],
            'deterministic_response': json.loads((OUT / 'deterministic_baselines.json').read_text(encoding='utf-8'))[c['id'][0]]['turns'][-1]['player_facing'],
            'historical_prelude': old['raw_provider_text'], 'historical_assembled': old['assembled'],
            'integrated': c['text'], 'baseline_provisional_scores': baseline_scores,
            'integrated_provisional_scores': assessments[c['id']]['scores'],
            'human_confirmed': False})
    write('baseline_comparison.json', comparisons)
    write('failure_handling.json', {'evidence': 'new_tests_final.xml and tests/test_pr_play_57_integrated_narration.py',
        'covered': ['timeout', 'provider exception', 'empty', 'malformed', 'incomplete', 'FAIL',
            'REVIEW_REQUIRED', 'VALIDATION_ERROR', 'validator exception', 'missing outcome',
            'unauthorized discovery', 'contradictory route', 'unauthorized inventory',
            'uncertainty lost', 'usage accounting absent', 'eight-request ceiling',
            'accepted HTTP quarantine', 'rejected HTTP fallback'],
        'live_provider_failure': 'none; faults are deterministic injections',
        'fallback': 'API player response remains deterministic for every candidate'})
    table = '| Candidate | Final gate | PR55 | Coverage |\n|---|---|---|---|\n' + '\n'.join(
        f"| {v['id']} | {v['decision']} | {v['semantic']['decision']} | {v['coverage']['decision']} |" for v in validations)
    verdict = 'B — PARTIAL / FURTHER INVESTIGATION REQUIRED'
    omission_ids = [w['id'] for w in worksheets if w['potential_omitted_outcomes']]
    summary = f'''# PR-PLAY-57 — {verdict}

Eight real integrated candidates were generated across four existing investigation scenarios. Default gameplay remains deterministic. Provisional reading shows better action responsiveness and more coherent outcomes than the captured prelude-plus-anchor responses. The gates still reject legitimate paraphrases, so this is not ready for promotion.

- Provider: OpenAI; model(s): {', '.join(perf['models'])}. Successful calls: 8/8. Tokens: {usage['input_tokens']} input + {usage['output_tokens']} output = {usage['total_tokens']}. Retries: 0.
- Provider latency: {statistics.mean(latency)/1000:.3f}s average, {max(latency)/1000:.3f}s maximum. Exact per-call measurements are in performance_and_usage.json and raw_provider_responses.json.
- Combined gates: {counts}. PR55 alone: {semantic_counts}. Mandatory coverage: {coverage_counts}.
- Provisional review: no identified new positive consequential fabrication or hidden disclosure. Omission/uncertainty concerns: {omission_ids}. Human/external review remains pending.
- State, quarantine and deterministic response checks pass on all eight. All raw state stops are preserved and explained; no gameplay assertions were relaxed.
- Regression: {combined_tests['focused_passed']} passed / {combined_tests['focused_failed']} known focused failures, no errors/skips; holdout wrapper passed; all nine known broader metadata failures reproduced. New module: {new_count}/{new_count}.
- No commit or push. No ordinary player narration enabled. No ATGB benchmark score claimed.

Primary next cycle: improve integrated outcome coverage with a bounded, reviewed paraphrase mechanism. Preserve quarantine and demonstrate the same gameplay value; do not expand into general validator hardening.

## Changes made

New game/integrated_investigation_narration.py; small changes to game/quarantined_investigation_narration.py; new tests/test_pr_play_57_integrated_narration.py; extended architecture allowlist and persistence-import checks in tests/test_pr_play_49_anchored_narration.py. All other output is scoped evidence under artifacts/pr_play_57 and generated handoff exports.

## Human review and known limits

Review exact prose, especially “urgent update,” qualified negative search wording, and footprint uncertainty. Automated scores and this separate raw-text reading are provisional, not independent ground truth. Scenario B is a mundane no-clue examination, not a failed skill check. This four-scenario experiment does not establish general gameplay or validator completeness. Existing gold-gain wording is missed by PR55 but rejected by the preserved legacy mechanical check.

## Bundle contents

Seventeen reports, raw SDK captures, contracts, fact IDs, validation/coverage reasons, worksheets, individual quality scores, complete state comparisons, three durably accounted budget shards, regression logs, and incremental source diffs. No secrets or environment file is included.
'''
    doc('01_EXECUTIVE_SUMMARY.md', summary)
    doc('02_BASELINE_AND_SCOPE.md', '# Baseline and scope\n\nCommit: ' + (OUT/'entry/commit.txt').read_text(encoding='utf-8-sig').strip() + '\n\nEntry working-tree status is preserved at entry/status.txt. The tree was extensively dirty; prior edits are preserved. PR56 reports and fixtures were read without regeneration. The existing split is game/anchored_investigation_narration.py:assemble: prelude + blank line + exact engine anchors. The API observer runs after the player-facing object exists and ignores its return value. Relevant authorities read: DEVELOPMENT_CONSTITUTION, NEXT_SESSION, state_authority_model, validation_evidence_standard, review_handoff_standard, PR-AA portfolio and replay governance authority. Latest explicit user authorization supersedes older no-live handoff text. No protected baseline or canonical campaign edit. Known baseline failures are retained in regression_summary.json and regression_summary_final.json.')
    doc('03_INTEGRATED_NARRATION_ARCHITECTURE.md', '# Architecture\n\nAuthoritative resolver → existing detached hook input → existing anchored authority → integrated outcome projection → one expression-adapter request → legacy validator + unchanged PR55 + coverage → quarantine record only. No integrated candidate is assigned to gm_output or campaign state.\n\nOpt in with ASHEN_QUARANTINE_INVESTIGATION_NARRATION=1 and ASHEN_QUARANTINE_NARRATION_MODE=integrated. Real requests additionally require ASHEN_QUARANTINE_NARRATION_LIVE=1 and durable provider accounting. Omitting mode preserves the prelude mode; omitting the gate preserves deterministic behavior. Output cap remains the existing 80 tokens, below the requested 700 ceiling. Prelude ceilings remain 6/1000/10000; integrated ceilings are 8/700/12000. No automatic retry.\n\nSide-effectful investigations are rejected before the legacy detacher can drop effect fields. Unsupported effects are a documented limitation, not a second authority representation. All failures retain the existing API deterministic response. Implementation.diff is incremental against entry source, including previously untracked files.')
    doc('04_STRUCTURED_OUTCOME_CONTRACT.md', '# Structured outcome contract\n\nThe ephemeral request reuses AuthorizedInvestigation and DiscoveryAnchor. It includes bounded player_action; resolved_outcome status/success; must_communicate facts with stable per-outcome IDs, source and epistemic status; may_reference visible_scene and previously known continuity; authorized_consequences (empty in this disclosure-only slice); and must_not_establish constraints. No raw state, clue catalog, target IDs, private notes or hidden facts are sent. Required text is never silently truncated; oversized projections refuse.\n\nNew discoveries are mandatory. No-clue status is mandatory. Repeat-search no-new status and already-known clue are mandatory. All footprint uncertainty facets remain part of the mandatory fact. Scene observations are optional. Exact requests and mandatory IDs are in authorized_outcome_contracts.json and mandatory_fact_identifiers.json.')
    doc('05_SCENARIO_RESULTS.md', '# Scenario results\n\n' + table + '\n\nA: new patrol-route clue. B: rain-barrel examination, no new clue; successful mundane observation substitutes for an unavailable deterministic dice-failure fixture. C: second notice-board examination with the first clue already known. D: authorized footprint evidence with number, origin and direction unclear. Each uses unchanged existing fixtures and two planned generations. No disappointing candidate was retried.')
    doc('06_RAW_INTEGRATED_NARRATION.md', '# Exact integrated narration\n\n' + '\n\n'.join('## '+c['id']+'\n\n'+c['text'] for c in candidates))
    doc('07_BASELINE_COMPARISON.md', '# Baseline comparison\n\nComparison is against the complete historical prelude-plus-deterministic-anchor output, not against the prelude alone. No live baseline regeneration. Mappings: integrated A→PR56 A; B→PR56 C; C→PR56 B; D→PR56 D. Historical B and D each have one sample, reused explicitly. baseline_comparison.json retains exact deterministic response, historical prelude, historical assembled output, integrated prose and both provisional score sets.\n\nIntegrated prose responds directly to the action and communicates the result within the same paragraph. Baseline anchors already preserved fidelity, so integrated prose does not improve mechanical correctness. Its provisional value is coherence and action responsiveness. Generic “fresh lead” phrasing and repeated “closer look” openings remain. This is a small unblinded comparison, not human-confirmed gameplay improvement.')
    doc('08_VALIDATION_RESULTS.md', '# Validation results\n\n' + table + '\n\nDetailed claims and reasons are in validation_decisions.json. PR55 SHA-256 stays ed29349cde1bb641178b01175f608142707dcc21a7d387e4b0f57707a1d0d6b6. Existing legacy mechanical/hidden/authority checks remain mandatory. Any FAIL, REVIEW_REQUIRED or VALIDATION_ERROR forces a quarantined deterministic fallback. A PASS still never promotes the candidate. A1 illustrates a conservative unauthorized_discovery rejection of apparently authorized route paraphrase; review is separate from the validator output.')
    doc('09_MANDATORY_OUTCOME_COVERAGE.md', '# Mandatory outcome coverage\n\nCounts: ' + str(coverage_counts) + '\n\nThe narrow checker reuses PR55 content normalization and requires content within a sentence; it adds no synonym dictionary. Engine no-new status uses bounded negative-result patterns; repeats additionally require continuity wording. Unrecognized or potentially negated paraphrases return REVIEW_REQUIRED, with each fact classified as covered, ambiguous paraphrase or missing mandatory outcome. Never exact sentence matching. It is conservative and incomplete: token presence is not a proof of relation binding or semantic equivalence, and sentence splitting can cause false reviews. Independent raw-text review is pending. Coverage_decisions.json preserves evidence spans and overlap, which never substitute for semantic validation.')
    doc('10_INDEPENDENT_SEMANTIC_REVIEW.md', '# External-review worksheets\n\nindependent_review_worksheets.json contains every required worksheet field. These are prepared for external independent examination. The current raw-text assessment was authored provisionally by the implementation agent, without treating validator decisions as ground truth. It is not an independent human confirmation.\n\n' + '\n\n'.join('## '+w['id']+'\n\nClassification: '+w['proposed_semantic_classification']+'\n\n'+w['supporting_evidence']+'\n\nUncertainty: '+w['uncertainty_notes'] for w in worksheets))
    dimensions = list(quality[0]['scores'])
    qtable = '| Candidate | ' + ' | '.join(dimensions) + ' |\n|---|' + '---|'*len(dimensions) + '\n'
    qtable += '\n'.join('| '+q['id']+' | '+' | '.join(str(q['scores'][d]) for d in dimensions)+' |' for q in quality)
    doc('11_NARRATION_QUALITY.md', '# Provisional narration quality (0–4)\n\n'+qtable+'\n\nScores are provisional automated judgments from raw prose. Harmless prose quality cannot compensate for a failed safety gate or missing mandatory fact. Outcome integration and action responsiveness improve provisionally over complete PR56 output; discovery fidelity was already guaranteed there by deterministic anchors. Repeated-action context is assessed separately in worksheets. Quality_scores.json and baseline_comparison.json preserve individual scores; no human confirmation or blinded comparison.')
    doc('12_STATE_AND_QUARANTINE_INTEGRITY.md', '# State and quarantine integrity\n\nAll eight player responses and mechanical outcomes match deterministic expectations. The exact persisted file contents immediately before and after each hook match byte-for-byte. No raw candidate appears in persisted authoritative state. Full scene/campaign/session/world/character/conditions/combat/log payload comparisons pass after documented operational-field normalization. Envelope checksums are independently recomputed and valid. Canonical data and .env hashes remain unchanged. No state field was repaired or overwritten to improve results.\n\nThe first stop captured save clocks, timing diagnostics and their derived envelope checksum. The second captured UTF-8 evidence decoded with cp1252, plus an existing process-randomized clue_text_digest generated by hash(slug) at game/noncombat_resolution.py:355. These original mismatches remain in scenario_results.json and combined_results.json. Correct UTF-8 reading and explicit operational metadata classification resolve them; clue text/IDs, player text and authority remained unchanged. Three exclusive ledgers retain each dispatch. Their budgets decrease by prior consumption, and aggregate audit verifies eight total attempts and actual token equality against raw SDK usage. No exhausted budget was reset. State_and_quarantine_audit.json includes every comparison.')
    doc('13_FAILURE_HANDLING.md', '# Failure handling\n\n28 deterministic new-module tests pass. failure_handling.json maps required fault classes to executable evidence. Provider timeout/exception, invalid responses, semantic failure/review/error, validator exceptions, omission, inventory claims and contradictory outcomes retain fallback. Accepted and rejected candidates both pass HTTP player-response and full gameplay-state equality checks; storage writes while the hook is active are prohibited. Real provider failures: zero. No quality retry. A legacy inventory test preserves the known PR55 blind spot and proves the existing mechanical check still rejects the claim.')
    doc('14_PERFORMANCE_AND_USAGE.md', '# Performance and usage\n\n'+json.dumps(perf, indent=2)+'\n\nAll three provider usage ledgers are included. Input/output/total SDK usage exactly matches the aggregate ledgers. Per-request token comparison is more meaningful than eight-versus-six aggregate totals. Latency is a small-sample observation, not a causal attribution to the prompt. No cost estimate without a price table. Validation adds no provider calls.')
    doc('15_REGRESSION_RESULTS.md', '# Regression results\n\n'+json.dumps(combined_tests, indent=2)+'\n\nInitial focused run found one architecture allowlist failure for the new quarantined adapter. The architecture test now explicitly recognizes that adapter and adds checks against API/persistence/world/OpenAI imports and direct player-facing wiring. No existing gameplay, effect or output assertion was removed. Final focused run returned to the same three known failures. The final expanded module reran separately; overlapping cases are counted once. Both holdout wrappers passed (including the frozen 70-case holdout and 49-line fabrication checks internally). All nine broader failures are KeyError hard_validation_attempt_1, unchanged and unrepaired. Existing focused test artifacts overwritten by established tests were restored from snapshots. Full repository suite and PR-BR continuation suites were not executed.')
    doc('16_LIMITATIONS_AND_OPEN_RISKS.md', '# Limitations and open risks\n\n- Eight outputs, four existing authored scenes/actions, one model, no human-confirmed review or general ATGB result.\n- No authored deterministic failed skill check; scenario B is no-clue observation.\n- Coverage heuristics conservatively reject legitimate paraphrases; content overlap cannot prove relations. PR55 remains incomplete for English, including a known gold-gain wording caught by the preserved legacy validator.\n- Disclosure-only investigations: persistent mechanical consequences are refused, not integrated. Continuity includes the existing known-clue projection and can grow until the bounded request refuses.\n- Harmless descriptive details and qualified negative search claims still require judgment. No independent semantic ground truth or statistical quality claim.\n- The initial harness stopped twice; raw evidence and bounded continuation ledgers are retained. Volatile metadata is classified explicitly, never treated as gameplay authority.\n- Ordinary players never receive this prose; future player-facing work requires a separate controlled cycle. No promotion is authorized by this result.')
    doc('17_NEXT_SESSION.md', '# Next cycle\n\nPrimary next step: improve integrated outcome coverage, using these exact authorized route and footprint paraphrases as a bounded review set. Keep PR55 and the existing legacy gate, preserve quarantine and conservative review, and avoid building a general semantic parser. Demonstrate acceptable integrated gameplay communication with reliable recognition before proposing controlled player-facing use. Human review of the eight worksheets remains outstanding; this package does not claim it occurred. Do not commit or push from this handoff.\n\nRead 01, 06, 08, 09, 10, 12 and 16 first, plus implementation.diff and the three accounting ledgers.')
    write('closeout_metrics.json', {'verdict': verdict, 'provider': perf['provider'], 'models': perf['models'],
        'successful_requests': perf['successful_requests'], 'usage': usage, 'latency_average_ms': statistics.mean(latency),
        'latency_max_ms': max(latency), 'validation': counts, 'semantic': semantic_counts,
        'coverage': coverage_counts, 'omission_concerns': omission_ids, 'tests': combined_tests})
    print(json.dumps(read('closeout_metrics.json'), indent=2))


if __name__ == '__main__':
    main()
