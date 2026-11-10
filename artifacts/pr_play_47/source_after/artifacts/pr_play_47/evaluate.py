"""Aggregate measured evidence and explicit provisional editorial judgments.

Scores below are the implementing agent's review of the complete responses,
not a live model judge, automated prose metric, blinded review, or player study.
"""
from pathlib import Path
import json
import statistics

OUT = Path(__file__).resolve().parent
CATEGORIES = ['information_completeness', 'mechanical_consistency', 'naturalness',
              'expressive_range', 'atmosphere', 'investigative_clarity', 'repetition', 'cohesion']
RUBRIC = {
    'information_completeness': ['Omits the result', 'Partial result or missing relevant known information', 'Result and relevant information complete'],
    'mechanical_consistency': ['Contradicts outcome', 'Ambiguous agreement', 'Agrees without extra consequences'],
    'naturalness': ['Fragmented or incoherent', 'Readable but formulaic or awkward', 'Fluent and economical'],
    'expressive_range': ['No selectable presentation variation', 'Limited compositional variation', 'Broad, outcome-appropriate variation'],
    'atmosphere': ['Absent or distracting', 'Some useful mood or sensory attention', 'Specific and well integrated'],
    'investigative_clarity': ['Result/uncertainty unclear', 'Some ambiguity or weak focus', 'Actionable result and limits clear'],
    'repetition': ['Conspicuous repeated wording/structure across corpus', 'Some repeated scaffolding', 'Little distracting repetition'],
    'cohesion': ['Disconnected fragments', 'Understandable but loosely joined', 'Details and outcome form a unified response'],
}


def dump(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def main():
    scored = []
    matrix = []
    for path in sorted(OUT.glob('evidence_scenario_*.json')):
        row = json.loads(path.read_text(encoding='utf-8'))
        sid = row['id']
        # A/B correctness are separate from the six prose-related dimensions.
        # The same rubric applies to the host emitter/fallback and every variant.
        host = [2, 2, 1, 0, 0, 2, 1, 2]
        host_note = 'Exact clue delivered clearly; missing article in target phrase; economical but fixed scaffolding.'
        if sid == 'failed':
            host = [2, 2, 2, 0, 0, 2, 1, 2]
            host_note = 'Clear, fluent failed-result sentence; no atmosphere or selectable presentation.'
        elif sid == 'known':
            host = [1, 2, 2, 0, 0, 1, 1, 2]
            host_note = 'Clearly adds nothing new, but does not restate available prior knowledge.'
        elif sid in ('mundane', 'no_clue'):
            host = [0, 2, 0, 0, 0, 0, 1, 0]
            host_note = 'Actual visible-surface emitter returns only the target label. Weak baseline; do not generalize improvement from this artifact.'
        responses = [('host', row['host_speech'], host, host_note)]
        for v in row['variants']:
            if v['style'] == 'concise':
                scores = [2, 2, 2, 1, 0, 2, 0, 2]
                note = 'Readable and complete; generic evidence opener repeated throughout corpus; no specific atmosphere.'
                if sid == 'known':
                    scores = [2, 2, 1, 1, 0, 2, 0, 1]
                    note = 'Prior clue preserved, but the Already established label and repeated examination framing feel assembled.'
            elif v['style'] == 'atmospheric':
                scores = [2, 2, 1, 1, 1, 2, 0, 1]
                note = 'Public context adds texture; attention-and-pause clauses repeat, length delays the result, and joins feel generic.'
                if sid == 'old_milestone':
                    scores[4] = 2
                    note += ' Existing milestone/mud observations provide useful, specific investigative mood.'
            else:
                scores = [2, 2, 1, 1, 1, 2, 0, 1]
                note = 'Result-first order preserves clarity and uncertainty, but the repeated rhetorical question and later attention paragraph weaken cohesion.'
            responses.append((v['style'], v['narration'], scores, note))
        for style, text, scores, note in responses:
            scored.append({'scenario': sid, 'style': style, 'text': text,
                'scores': dict(zip(CATEGORIES, scores)), 'total_of_16': sum(scores),
                'mechanical_of_2': scores[1], 'information_of_2': scores[0],
                'narrative_of_12': sum(scores[2:]), 'editorial_reason': note})
        matrix.append({'scenario': sid, 'category': row['category'],
            'resolution_kind': row['resolution']['kind'], 'success': row['resolution'].get('success'),
            'origin': row.get('origin', 'actual resolver on unmodified campaign scene'),
            'clues': row['authorized_view']['revealed'], 'known': row['authorized_view']['known'],
            'variants': len(row['variants']), 'complete_variants': sum(v['information_complete'] for v in row['variants']),
            'valid_variants': sum(v['mechanical_validator']['hard_valid'] for v in row['variants']),
            'state_unchanged': row['state_unchanged']})
    means = {}
    for style in ('host', 'concise', 'atmospheric', 'investigative'):
        rows = [r for r in scored if r['style'] == style]
        means[style] = {key: statistics.mean(r[key] for r in rows)
                       for key in ('total_of_16', 'mechanical_of_2', 'information_of_2', 'narrative_of_12')}
        canonical = [r for r in rows if r['scenario'] in ('frontier_gate', 'old_milestone')]
        means[style]['canonical_narrative_of_12'] = statistics.mean(r['narrative_of_12'] for r in canonical)
    dump('quality_comparison.json', {'provisional': True,
        'assessor': 'Implementing agent, unblinded editorial review; scores are judgments, not measured player preference.',
        'rubric': RUBRIC, 'category_order': CATEGORIES, 'responses': scored, 'means': means,
        'limitations': ['Only ten fixed outcomes; eight synthetic', 'No live-model creativity measured',
            'Weak one-word mundane host baselines inflate aggregate improvement',
            'Expressive range scored as family capability; repetition judged across corpus',
            'No blinded independent review or player experience measurements']})
    dump('scenario_matrix.json', matrix)
    lines = ['# Full narrative comparison', '',
        'Provisional, unblinded implementing-agent editorial judgments. A/B correctness is reported separately from C-H prose quality.', '',
        'Scores: A information, B mechanics, C naturalness, D range, E atmosphere, F clarity, G repetition, H cohesion; each 0-2.', '']
    for r in scored:
        lines += [f"## {r['scenario']} / {r['style']}", '', r['text'], '',
                  'Scores A-H: '+', '.join(str(r['scores'][k]) for k in CATEGORIES)+
                  f". Total {r['total_of_16']}/16; prose {r['narrative_of_12']}/12.", '', r['editorial_reason'], '']
    (OUT/'NARRATIVE_COMPARISON.md').write_text('\n'.join(lines), encoding='utf-8')
    stress = json.loads((OUT/'evidence_stress.json').read_text())
    repeated = {phrase: sum(phrase in r['narration'] for r in stress) for phrase in
                ('evidence', 'examination', 'Your gaze moves slowly', 'What does the evidence actually establish?', 'You pause over the details.')}
    dump('expressive_range.json', {'valid_plans': len(stress), 'unique_texts': len({r['narration'] for r in stress}),
        'block_order_families': len({r['plan']['structure'] for r in stress}),
        'cadences': sorted({r['plan']['pace'] for r in stress}),
        'sensory_attention_modes': sorted({r['plan']['sensory_focus'] for r in stress}),
        'word_count_range': [min(len(r['narration'].split()) for r in stress), max(len(r['narration'].split()) for r in stress)],
        'repeated_phrase_output_counts': repeated,
        'assessment': {'structure': 'Three recognizable block permutations, not ten independent narrative structures.',
            'sentence_variety': 'Finite engine openings plus optional semicolon join; source clue sentence never changes.',
            'ordering': 'Result-first versus context-first is meaningful; known/new order is inert in this fixed result with no prior clue.',
            'pacing': 'Lean versus extended blocks and paragraph pauses vary reading pace; long generic attention clauses can drag.',
            'sensory': 'Attention to sight, texture or listening is bounded and subjective; no invented physical atmosphere.',
            'repetition': 'High recurrence of evidence/examination and the exact source clue; textual uniqueness overstates range.',
            'readability': 'Readable throughout, but rhetorical framing and generic joins are recognizably assembled.'},
        'verdict': 'Limited expressive range; insufficient evidence of worthwhile broad narrative improvement.'})
    print(json.dumps(means, indent=2))

if __name__ == '__main__': main()
