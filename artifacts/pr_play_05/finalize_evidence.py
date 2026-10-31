import ast
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/pr_play_05'
entry=json.loads((OUT/'entry_hashes.json').read_text())
changes={name:{'before':digest,'after':hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).is_file() else None}
         for name,digest in entry.items()
         if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest}
protected=[name for name in entry if name.startswith(('data/','experiments/'))]
integrity={'protected_count':len(protected),'protected_changed':[n for n in protected if n in changes],
           'entry_files':len(entry),'changes':changes,'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
assert not integrity['protected_changed'],integrity['protected_changed']
(OUT/'integrity.json').write_text(json.dumps(integrity,indent=2))
files=['game/api.py','game/gm.py','game/provider_budget.py','tools/atgb/accounting.py','tests/test_start_campaign_api.py','docs/NEXT_SESSION.md']
delta=''
for name in files:
    a=(OUT/'entry'/name).read_text(encoding='utf-8');b=(ROOT/name).read_text(encoding='utf-8')
    delta+=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='entry/'+name,tofile='final/'+name))
for name in ['tests/test_pr_play_05_diagnostics.py','tests/test_pr_play_05_emission_evidence.py','tests/helpers/pr_play_05_http_capture.py']:
    b=(ROOT/name).read_text()
    delta+=''.join(difflib.unified_diff([],b.splitlines(True),fromfile='/dev/null',tofile='final/'+name))
(OUT/'source.diff').write_text(delta,encoding='utf-8')
(OUT/'status_after.txt').write_bytes(subprocess.check_output(['git','status','--short'],cwd=ROOT))
def constants(path):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    return {ast.dump(node.targets[0]):ast.dump(node.value) for node in tree.body
            if isinstance(node,ast.Assign) and isinstance(node.value,(ast.Constant,ast.Dict,ast.List,ast.Tuple))}
assert constants(OUT/'entry/game/gm.py')==constants(ROOT/'game/gm.py')
(OUT/'scope_verification.json').write_text(json.dumps({
    'gm_top_level_constants_and_prompt_literals_unchanged':True,
    'provider_request_parameters':'Existing model/input and accounting-only max_output_tokens construction retained; production tests assert 600 and unchanged dispatch keys.',
    'provider_operations_added':0,'live_provider_calls':0,'connectivity_diagnostics':0,
    'frozen_data_and_experiments_changed':False,'commit_or_push':False},indent=2))
results={}
for label in ['regression_http','provider_final','regression_structured','regression_ordinary','regression_export','integrated','emission','emission_pre04']:
    path=OUT/(label+'.txt')
    text=path.read_text(encoding='utf-8',errors='replace')
    counts={}
    for line in text.splitlines():
        if re.fullmatch(r'[.FEsyx]+\s+\[\s*\d+%\]',line):
            for symbol in line.split()[0]:counts[symbol]=counts.get(symbol,0)+1
    results[label]=counts
(OUT/'test_totals.json').write_text(json.dumps(results,indent=2))
boundary={}
for variant in ['emission','emission_pre04']:
    boundary[variant]={}
    for path in (OUT/variant).glob('*.json'):
        data=json.loads(path.read_text())
        last=data['boundaries'][-1]
        boundary[variant][path.stem]={'fixture_length':len(data['fixture']['player_facing_text']),
            'prepared_fixture_length':len((data['fixture'].get('upstream_prepared_emission')or{}).get('prepared_scene_opening_text','')),
            'boundaries':[{k:r[k] for k in ['stage','length']} for r in data['boundaries']],
            'debug_counts':{k:v for k,v in (last.get('debug')or{}).items() if k.endswith('_len')}}
(OUT/'emission_comparison.json').write_text(json.dumps(boundary,indent=2))
