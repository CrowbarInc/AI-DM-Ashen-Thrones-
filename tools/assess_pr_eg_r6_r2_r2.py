"""Separately prompted, blinded provider transcript grading, never used for tuning."""
import json
import hashlib
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'artifacts/pr_eg_r6_r2_r2'


def main():
    from openai import OpenAI
    from game.config import get_openai_api_key, DEFAULT_MODEL_NAME
    from game.semantic_correspondence import object_schema
    groups = []
    mapping = {}
    for label in (['baseline'] if '--baseline-only' in sys.argv else ['baseline', 'final', 'predecessors']):
        file = OUT / label / 'live_turns.jsonl'
        if not file.exists():
            continue
        rows = [json.loads(l) for l in file.read_text().splitlines() if l.strip()]
        for conv in dict.fromkeys(r['conversation'] for r in rows):
            chosen = [r for r in rows if r['conversation'] == conv]
            specs = json.loads((OUT / label / 'qualification_plan.json').read_text())
            spec = next(s for s in specs if s['id'] == conv)
            if '--completed-only' in sys.argv and len(chosen) != len(spec['turns']):
                continue
            token = f'packet_{list(dict.fromkeys(r["conversation"] for r in rows)).index(conv):02}' if label == 'baseline' else hashlib.sha256((label + ':' + conv).encode()).hexdigest()[:12]
            mapping[token] = {'run': label, 'conversation': conv}
            assert [r['player'] for r in chosen] == [q for q, _ in spec['turns']], 'Non-scripted input: do not export.'
            groups.append({'id': token, 'initial_npcs': spec['npcs'], 'turns': [
                {'turn': r['turn'], 'player': r['player'], 'speech': r['text'],
                 'fixture_reset': spec['turns'][r['turn']-1][1].get('reset_cast'),
                 'accepted_act': r['plan'].get('conversational_act'),
                 'accepted_proposition': r['plan'].get('request_proposition'),
                 'answer_status': r['plan'].get('response_kind'),
                 'bound_target': r['plan'].get('bound_referent_id'),
                 'prior_active': (r.get('prior_referents') or {}).get('active_id'),
                 'resulting_active': (r.get('persisted_referents') or {}).get('active_id')}
                for r in chosen]})
    random.Random(917).shuffle(groups)
    fields = ['operation_correct', 'referent_correct', 'roles_preserved', 'correction_success',
              'follow_up_success', 'focus_preserved', 'false_clarification', 'genuine_clarification_correct',
              'relevant', 'sufficient']
    row_schema = object_schema({'turn': {'type': 'integer'},
        **{k: {'type': ['boolean', 'null']} for k in fields},
        'quality': {'type': 'integer', 'minimum': 0, 'maximum': 3},
        'playability': {'type': 'integer', 'minimum': 0, 'maximum': 3},
        'expected': {'type': 'string'}, 'reason': {'type': 'string'},
        'failure_boundary': {'type': 'string'}})
    schema = object_schema({'grades': {'type': 'array', 'items': row_schema}})
    criteria = ('Grade conversational semantic operations independently. Packet run/version identity is hidden. '
        'Judge every turn in context from player intent, actual delivered speech and fixture facts. '
        'Provider proposals are not facts. Missing knowledge warrants uncertainty, not clarification. '
        'A relevant unknown is acceptable only if the NPC lacks a permitted answer. Someone is not a supplied identity. '
        'Communication speaker/recipient/topic/content are distinct. Corrections must preserve unchanged roles. '
        'A source attribution asks for the informant of the proposition, not its subject or name. '
        'Restricted source text never authorizes disclosure. Do not award success merely for structural validity. '
        'Mark operation_correct, roles_preserved, focus_preserved, relevant and sufficient on every turn. '
        'Use null for referent_correct unless dependent on earlier conversation; null for correction_success '
        'unless an intended correction; null for follow_up_success unless an intended followup; '
        'false_clarification is true only when clarification was unnecessary. '
        'genuine_clarification_correct is null unless player intent is genuinely ambiguous. '
        'quality and playability: 0 broken/unhelpful, 1 flawed, 2 usable, 3 natural and fully effective. '
        'For every failure give exact expected behavior, actual issue and boundary: classification, binding, '
        'roles, transformation, grounding, source_matching, sufficiency, clarification, expression, persistence, other. '
        'This is evaluation only. Do not suggest implementation fixes. Return one grade for every input turn.')
    (OUT / 'grading_criteria.txt').write_text(criteria)
    (OUT / 'grading_blind_map.json').write_text(json.dumps(mapping, indent=2))
    (OUT / 'grading_payloads.json').write_text(json.dumps(groups, indent=2))
    if '--prepare-only' in sys.argv:
        print('Prepared fixture-only payloads locally; no network call performed.')
        return
    target = OUT / 'independent_grades.jsonl'
    completed = {json.loads(l)['packet'] for l in target.read_text().splitlines()} if target.exists() else set()
    client = OpenAI(api_key=get_openai_api_key(), timeout=90)
    for packet in groups:
        if packet['id'] in completed:
            continue
        response = client.responses.create(model=DEFAULT_MODEL_NAME, temperature=0, max_output_tokens=7000,
            input=[{'role': 'system', 'content': criteria}, {'role': 'user', 'content': json.dumps(packet)}],
            text={'format': {'type': 'json_schema', 'name': 'transcript_grades', 'strict': True, 'schema': schema}})
        result = json.loads(response.output_text)
        if sorted(g['turn'] for g in result['grades']) != sorted(t['turn'] for t in packet['turns']):
            raise ValueError('Incomplete grading packet; preserve raw evidence and do not silently score.')
        with target.open('a') as f:
            f.write(json.dumps({'packet': packet['id'], 'model': response.model,
                'usage': response.usage.model_dump(), 'input': packet, 'output': result}) + '\n')
        print(packet['id'], 'graded', len(result['grades']), flush=True)


if __name__ == '__main__':
    main()
