"""Freeze evidence before implementation. No provider access."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/pr_play_58'

def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def main():
    assert not (OUT / 'holdout.json').exists(), 'Already frozen'
    write('entry_status.json', {'commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        'status': subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True)})
    hashes = {}
    for directory in ['data', 'game', 'static', 'experiments']:
        for p in (ROOT / directory).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                hashes[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    write('entry_hashes.json', hashes)
    source = (ROOT / 'game/integrated_investigation_narration.py').read_text(encoding='utf-8')
    (OUT / 'integrated_before.py').write_text(source, encoding='utf-8')
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'mandatory_coverage')
    (OUT / 'previous_coverage.py').write_text('import re\nfrom game import consequential_narration_validation as semantic\n' + ast.get_source_segment(source, node) + '\n', encoding='utf-8')
    prior = ROOT / 'artifacts/pr_play_57'
    candidates = json.loads((prior/'integrated_candidates.json').read_text(encoding='utf-8'))
    requests = {r['id']: r['contract'] for r in json.loads((prior/'authorized_outcome_contracts.json').read_text(encoding='utf-8'))}
    decisions = json.loads((prior/'validation_decisions.json').read_text(encoding='utf-8'))
    write('previous_decisions_original.json', decisions)
    write('fixed_samples.json', [{'id': r['id'], 'text':r['text'], 'request':requests[r['id']],
        'previous_combined': r['diagnostic']} for r in candidates])
    # Raw provider artifacts are byte-preserved, never reconstructed from summaries.
    (OUT/'raw_provider_responses_original.json').write_bytes((prior/'raw_provider_responses.json').read_bytes())
    route = 'The missing patrol was last seen taking the northwest mud track past the crates.'
    prints = 'Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.'
    authorities = {'route':requests['A1'], 'prints':requests['D1'], 'repeat':requests['C1'], 'empty':requests['B1']}
    cases = []
    def add(group, authority, texts):
        for text in texts:
            cases.append({'id':f'H{len(cases)+1:02}', 'group':group, 'authority':authority,
                'expected':'PASS' if group=='legitimate' else 'REVIEW_REQUIRED' if group in ('missing','ambiguous') else 'FAIL', 'text':text})
    add('legitimate','route',[
        'The missing patrol was last spotted taking the northwest mud track beyond the crates.',
        'Beyond the crates, the missing patrol was last observed heading along the northwest muddy trail.',
        'The notices place the missing patrol on the northwest mud track, past the crates.',
        'The missing patrol was last seen following the muddy northwest path past the crates.',
        'Rain taps the paper. The missing patrol was last seen heading along the northwest mud track past the crates.',
    ])
    add('legitimate','prints',[
        'Faint overlapping footprints mark the mud around the weathered milestone. Their number, origin and direction remain uncertain.',
        'By the old milestone, faint overlapping prints are visible in the mud, but you cannot tell how many people made them, where they came from or which way they went.',
        'The mud around the old milestone bears faint overlapping footprints; their number, source and direction are unresolved.',
        'Faint overlapping prints in the mud beside the old milestone offer no evidence of their number, origin or direction.',
        'At the old milestone you see faint overlapping prints in the mud, though their number, origin and direction are doubtful.',
    ])
    add('legitimate','repeat',[
        'You return to the board; no fresh clues emerge. ' + route,
        'The board offers nothing beyond what you already know: ' + route,
        'You examine it again without learning anything new. ' + route,
    ])
    add('legitimate','empty', ['The examination yields no additional information.', 'Your inspection reveals nothing further.'])
    add('missing','route', ['Only rain meets your gaze.', 'You study the papers.', 'The patrol was last seen.',
        'The missing patrol was last seen taking the northwest track.', 'The missing patrol was last seen past the crates.'])
    add('missing','prints', ['You see footprints.', 'Faint overlapping prints mark the mud around the old milestone.',
        'Faint overlapping prints mark the mud around the old milestone, but their origin is unknown.',
        'The number, origin and direction remain unclear.', 'The mud around the old milestone is wet.'])
    add('contradictory','route', [route.replace('northwest','northeast'), route.replace('patrol','caravan'),
        route.replace('past the crates','before the crates'), route.replace('was last seen','will be seen'),
        route.replace('was last seen taking','was not last seen taking')])
    add('contradictory','prints', ['Three travelers left the prints heading east.', 'The prints lead toward the northern gate.',
        'No footprints are visible near the milestone.', 'The prints came from the smugglers camp.', 'Your investigation fails.'])
    add('expansion','route', [route+' The patrol was captured by smugglers.', route+' You acquire a silver key.',
        route+' The captain knows your secret.', route+' A hidden tunnel runs under the gate.',
        route+' You gain 10 gold coins.', route+' The gate is now permanently open.',
        route+' You discover a secret destination.', route+' You are now poisoned.'])
    add('expansion','repeat', ['For the first time, you discover this: '+route,
        'You examine the board again and discover a hidden map. '+route])
    add('ambiguous','route', ['Perhaps the missing patrol took the northwest mud track past the crates.',
        'Someone may have seen the missing patrol near the crates.', 'The northwest mud track might explain the patrol.'])
    add('ambiguous','prints', ['The marks might be prints, but who can say?', 'The mud suggests a direction, though the signs resist interpretation.'])
    write('holdout.json', {'authorities':authorities, 'cases':cases})
    write('holdout_manifest.json', {'sha256':hashlib.sha256((OUT/'holdout.json').read_bytes()).hexdigest(),
        'cases':len(cases), 'groups':{g:sum(c['group']==g for c in cases) for g in {c['group'] for c in cases}},
        'frozen_before_implementation':True, 'independence':'Authored by the same agent in this session; frozen before edits, not independent blind validation.',
        'implementation_before_sha256':hashlib.sha256(source.encode()).hexdigest()})
    print('Frozen', len(cases), 'holdout cases and eight original samples')

if __name__ == '__main__':
    main()
