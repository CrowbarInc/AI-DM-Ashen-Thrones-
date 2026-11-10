"""Developer-authored oracle frozen before implementation; not external validation."""
import hashlib, json
from pathlib import Path

out = Path(__file__).resolve().parent
rows = []
for source, fact in [('tablet', 'The tablet records six jars.'), ('banner', 'The banner bears a blue heron.'),
                     ('logbook', 'The logbook dates the storm to midsummer.'), ('rubbing', 'The rubbing shows a broken circle.')]:
    for condition in ['known', 'third', 'reload', 'travel_return', 'conversation', 'other_discovery',
                      'hidden', 'other_source', 'modified', 'removed', 'stale', 'implicit']:
        rows.append({'id': f'H{len(rows)+1:03}', 'source': source, 'fact': fact,
                     'condition': condition, 'input': f'I examine the {source} again.',
                     'expected_recall': condition in {'known','third','reload','travel_return','conversation','other_discovery'},
                     'expected_resolution': 'no new discoveries', 'expected_publication': 'source-bound prior fact only',
                     'expected_trace': 'one completed publication', 'hidden_exclusion': ['CANARY_HIDDEN'],
                     'expected_mutation': False})
data = json.dumps(rows, indent=2).encode()
path = out/'holdout.json'
with path.open('xb') as handle: handle.write(data)
(out/'holdout_manifest.json').write_text(json.dumps({'cases': len(rows), 'sha256': hashlib.sha256(data).hexdigest(),
    'author': 'developer', 'frozen_before_implementation': True, 'run_policy': 'once; preserve failures; no tuning'}, indent=2))
