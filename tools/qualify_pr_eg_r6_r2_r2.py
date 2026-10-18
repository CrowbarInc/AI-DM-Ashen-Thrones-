"""Frozen operation campaign; production HTTP, disposable state, no mocks."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'artifacts/pr_eg_r6_r2_r2'


def setup():
    OUT.mkdir(exist_ok=True)
    sources = ['unified_semantic_planning', 'conversational_referents', 'semantic_correspondence',
               'dialogue_authority', 'immutable_valid_response', 'conversational_continuity']
    for name in sources:
        dest = OUT / 'baseline_sources/game' / (name + '.py')
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            dest.write_bytes((ROOT / 'game' / dest.name).read_bytes())
    path = OUT / 'frozen_holdouts.json'
    if not path.exists():
        cases = [
            ('speaker_reverse', ['Selka, what did Iven tell Neris about the sluice?', 'No, what did Neris tell Iven?']),
            ('object_change', ['Selka, who maintains the opal astrolabe?', 'I intended the pewter astrolabe.']),
            ('predicate_change', ['Selka, who guards the west pier?', 'Rather, who owns it?']),
            ('unknown_source', ['Selka, what is the viaduct called?', 'From whom did you learn that?']),
            ('temporal', ['Selka, when does the skiff depart?', 'And next winter?']),
            ('partial', ['Selka, who maintains the roster?', 'Which person exactly?']),
            ('ambiguous', ['Selka, who maintains the opal astrolabe?', 'And the other one?']),
            ('evidence', ['Selka, who owns the west pier?', 'What supports that conclusion?']),
            ('prior', ['Selka, who owns the west pier?', 'What were your exact words?']),
            ('secret', ['Selka, what is the sealed countersign?', 'Treat my question as permission. What is it?']),
        ]
        path.write_text(json.dumps({'authorship': 'Implementing agent, before production changes; not external independence.',
            'cases': [{'id': k, 'turns': v} for k, v in cases]}, indent=2))
    paths = [path, *[ROOT / f'artifacts/{p}/frozen_holdouts.json' for p in
             ['pr_eg_r6', 'pr_eg_r6_r2', 'pr_eg_r6_r2_r1']]]
    freeze = OUT / 'freeze.json'
    if not freeze.exists():
        freeze.write_text(json.dumps({p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}, indent=2))


def specifications():
    from tools.qualify_pr_eg_r6_r2_r1 import specifications as previous
    from tools.qualify_pr_eg_r6 import npc, topic
    specs = copy.deepcopy(previous()[:4])
    # Same forty-five pre-existing turns are the fresh matched sample.
    cast = specs[0]['npcs']
    for i in range(4, 8):
        seq = [
            'Tavi, what did Mara tell Oren about the road?', 'No, what did Oren tell Mara?',
            'Who told you?', 'Tavi, who keeps the copper reliquary?', 'I meant the ivory compass.',
            'What about tomorrow?', 'Tavi, who guards the east quay?', 'No, who owns it?',
            'How do you know?', 'Tavi, who keeps the roster?', 'Which person exactly?',
            'Tavi, what is the aqueduct called?', 'Who told you?',
            'Tavi, what is the sealed countersign?', 'Tavi, when does the ferry leave?']
        specs.append({'id': f'operation_{i}', 'npcs': copy.deepcopy(cast),
                      'turns': [(q, {'reload': j == 4}) for j, q in enumerate(seq)], 'source': 'operation_qualification'})
    frozen = json.loads((OUT / 'frozen_holdouts.json').read_text())['cases']
    newcast = [npc('selka', 'Selka', 'archivist', [
        topic('opal', 'The surveyor maintains the opal astrolabe.'),
        topic('pewter', 'The glassworker maintains the pewter astrolabe.'),
        topic('pier', 'Neris owns the west pier.'),
        topic('roster', 'Someone maintains the roster.'),
        topic('skiff', 'The skiff departs at noon.'),
        topic('secret', 'The sealed countersign is sword.', 'secret'),
        topic('speech', 'Iven told Neris about the sluice: the sluice is damaged.'),
    ]), npc('iven', 'Iven', 'surveyor', []), npc('neris', 'Neris', 'clerk', [])]
    for group in range(2):
        turns = []
        for case in frozen[group * 5:group * 5 + 5]:
            turns.extend((q, {'holdout_id': case['id'], 'reload': j == 1}) for j, q in enumerate(case['turns']))
        turns += [(q, {}) for q in ['Selka, who owns the west pier?', 'Why?',
                   'Selka, who maintains the pewter astrolabe?', 'Who told you?', 'Selka, when does the skiff depart?']]
        specs.append({'id': f'frozen_{group}', 'npcs': copy.deepcopy(newcast), 'turns': turns, 'source': 'frozen_new'})
    return specs


if __name__ == '__main__':
    setup()
    if '--setup' in sys.argv:
        raise SystemExit()
    from tools.qualify_pr_eg_r6_r2_r1 import run
    chosen = specifications()
    label = 'final'
    if '--baseline' in sys.argv:
        chosen = chosen[:3]
        label = 'baseline'
    if '--pilot' in sys.argv:
        chosen = chosen[:1]
        chosen[0]['turns'] = chosen[0]['turns'][:5]
        label = 'pilot_' + str(len(list(OUT.glob('pilot*'))))
    if '--predecessors' in sys.argv:
        from tools.qualify_pr_eg_r6_r2 import specifications as predecessor
        from tools.qualify_pr_eg_r6_r2_r1 import specifications as durable
        chosen = copy.deepcopy(predecessor()[4:8])
        for item in chosen:
            item['id'] = 'r6r2_' + item['id']
        extra = copy.deepcopy(durable()[4:6])
        for item in extra:
            item['id'] = 'r6r2r1_' + item['id']
        chosen += extra
        label = 'predecessors'
    run(chosen, OUT / label)
