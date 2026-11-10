import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent
r = json.loads((OUT/'test_results.json').read_text(encoding='utf-8'))
before = {v['nodeid']: v for run in r['runs'][:2] for v in run['failures']}
after = {v['nodeid']: v for run in r['runs'][2:4] for v in run['failures']}


def signature(failure):
    lines = failure['traceback'].splitlines()
    statements = [line.lstrip('> ').strip() for line in lines if line.startswith('>')]
    errors = [re.sub(r'0x[0-9a-fA-F]+', '0xADDR', line.strip()) for line in lines if line.startswith('E ')]
    return {'phase': failure['phase'], 'assertion_or_raise': statements[-1] if statements else '', 'errors': errors}


rows = []
for node in r['unchanged_known_failures']:
    b, a = signature(before[node]), signature(after[node])
    normalized = lambda s: re.sub(r'("turn_id": ")[0-9a-f]+', r'\1TURN_ID', json.dumps(s))
    # JSON escaping occurs in dumps: normalize the captured UUID before dumps.
    def normalize(s):
        return {**s, 'errors': [re.sub(r'("turn_id": ")[0-9a-f]+', r'\1TURN_ID', e) for e in s['errors']]}
    rows.append({'nodeid': node, 'before': b, 'after': a,
                 'same_assertion_identity': b['phase'] == a['phase'] and b['assertion_or_raise'] == a['assertion_or_raise'],
                 'same_normalized_failure': normalize(b) == normalize(a)})
assert all(v['same_assertion_identity'] and v['same_normalized_failure'] for v in rows)
(OUT/'assertion_comparison.json').write_text(json.dumps({'rows': rows,
    'normalization': 'Only hexadecimal object addresses and generated turn_id UUIDs; complete raw tracebacks retained in run failures.json.'}, indent=2), encoding='utf-8')
print(f'{len(rows)} unchanged assertion identities and normalized failures verified')
