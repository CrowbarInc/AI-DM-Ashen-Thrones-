"""Offline evidence extraction and report packaging; never imports gameplay owners."""
from __future__ import annotations
import ast
import collections
import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'artifacts/atgb/atgb_r2_01'
REPORTS = ROOT / 'development/reports/atgb_r2_01'

def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8', errors='replace')

def initialize():
    REPORTS.mkdir(parents=True, exist_ok=True)
    (OUT/'repository_status_before.txt').write_text(git('status','--short','--untracked-files=all'),encoding='utf-8')
    dump('repository_identity.json', {'head':git('rev-parse','HEAD').strip(),'branch':git('branch','--show-current').strip(), 'mode':'offline read-only investigation; report/export writes only', 'provider_calls':0})
    (OUT/'NEXT_SESSION_before.md').write_bytes((ROOT/'docs/NEXT_SESSION.md').read_bytes())
    protected = {}
    for folder in ['game','data','tests','experiments','artifacts/atgb','artifacts/pr_eg_r6_r5','development/reports']:
        for p in (ROOT/folder).rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts or '.pytest_cache' in p.parts:
                continue
            if OUT in p.parents or REPORTS in p.parents:
                continue
            protected[p.relative_to(ROOT).as_posix()] = digest(p)
    dump('entry_hashes.json',protected)

def extract():
    selected = {'S01':[4], 'S02':[1,2,3,4], 'S03':[1,2,3,4,5], 'S05':[1,2,3,4], 'S07':[1,2], 'S08':[1,2,3]}
    traces=[]
    for scenario, numbers in selected.items():
        run='atgb_03' if scenario in {'S01','S02','S03'} else 'atgb_03c'
        base=f'artifacts/atgb/{run}/{scenario}'
        result=read(base+'/result.json')
        logpath=next((ROOT/base/'stores').rglob('session_log.jsonl'))
        logs=[json.loads(x) for x in logpath.read_text(encoding='utf-8').splitlines() if x.strip()]
        for number in numbers:
            t=next(x for x in result['turns'] if x['turn_id']==f'{scenario}.{number}')
            log=next(x for x in logs if x.get('player_input')==t['player_input'])
            md=log['resolution'].get('metadata',{})
            live=md.get('live_chat_interpretation') or {}
            raw=live.get('raw_interpretation')
            try: raw=json.loads(raw) if isinstance(raw,str) else raw
            except ValueError: raw={'unparsed':raw}
            traces.append({'turn_id':t['turn_id'],'trial':result['trial_number'],'partition':t['partition'],
                'input_classification':'representative_player_behavior', 'classification_basis':'Authored ATGB corpus; not human-captured; some turns are boundary-shaped.',
                'source':base+'/result.json','source_sha256':digest(ROOT/base/'result.json'),
                'log_source':logpath.relative_to(ROOT).as_posix(), 'log_sha256':digest(logpath),
                'player_input':t['player_input'], 'preceding_conversation':[{'turn_id':x['turn_id'],'player':x['player_input'],'gm':x['response_text']} for x in result['turns'] if x['order']<t['order']],
                'available_context_caveat':'Corpus turn_context is evaluation ground truth, not proof of provider request content. Original request messages not retained here.',
                'expected_behavior':t['turn_context'], 'state_evidence':t['state_evidence'],
                'model_interpretation':raw,'adapted_interpretation':live.get('record'),
                'interpretation_status':{k:live.get(k) for k in ['status','reason','eligibility_disposition']},
                'host_decision':md.get('conversational_decision') or t['conversational_decision'],
                'final_player_facing_response':t['response_text'],
                'resolution_kind':t['resolution_kind'],'telemetry':t['telemetry'],
                'narration_invoked':md.get('narration_invoked'), 'runtime_validity':t['capture_status'],
                'human_review_status':'UNREVIEWED; historical AI-assisted judgments separate',
                'historical_rubric':next(x for x in read('artifacts/atgb/atgb_05a/assessment/ATGB_04_review_judgments.json')['turns'] if x['review_id'].startswith(t['turn_id']+'/'))})
    dump('representative_traces.json',traces)
    judgments=read('artifacts/atgb/atgb_05a/assessment/ATGB_04_review_judgments.json')
    counts={k:dict(collections.Counter(t[k] for t in judgments['turns'])) for k in ['interpretation','response','authority']}
    assert counts=={'interpretation':{'pass':18,'fail':16,'uncertain':3},'response':{'pass':10,'fail':25,'uncertain':2},'authority':{'pass':35,'uncertain':2}}
    baseline=[json.loads(x) for x in (ROOT/'artifacts/pr_eg_r6_r5/baseline.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    assert len(baseline)==164 and sum(x['score']['player_facing_success'] for x in baseline)==59
    corrections=[x for x in baseline if 'correction' in x['tags']]
    assert len(corrections)==25 and sum(x['score']['player_facing_success'] for x in corrections)==0
    dump('baseline_verification.json',{'atgb_turns':len(judgments['turns']),'counts':counts,'human_review_attestation':judgments['human_review_attestation'],'pr_eg_turns':len(baseline),'pr_eg_successes':59,'pr_eg_corrections':25,'pr_eg_correction_successes':0,'note':'Recomputed historical figures, not post-repair measurements.'})
    dump('pr_eg_representative_rows.json',[x for x in baseline if x['turn_id'] in {'c06t03','c07t02','c06t07','c01t14'}])
    # Evaluate only isolated, unmodified syntax helpers. No module imports, gameplay, IO, inference, or repair.
    source=(ROOT/'game/interaction_completion.py').read_text(encoding='utf-8')
    names={'_VOCATIVE_RE','_SPEECH_ADDRESS_RE','_TELL_RE','_QUESTION_NOMINAL_RE','_INTERJECTION_RE','_NOT_A_VOCATIVE','_COMPLEMENT_RE','_clean','_nominal_chunk','_complement_cut','addressed_person_nominal'}
    tree=ast.parse(source); nodes=[]
    for node in tree.body:
        named={x.id for x in node.targets if isinstance(x,ast.Name)} if isinstance(node,ast.Assign) else {node.name} if isinstance(node,ast.FunctionDef) else set()
        if named & names: nodes.append(node)
    namespace={'re':re}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'isolated_unmodified_interaction_completion_helpers','exec'),namespace)
    probes=[]
    for line in ['If I ask you again later, will you still tell me that same thing?', 'Tell me more about that.','Who told you that?']:
        nominal=namespace['addressed_person_nominal'](line)
        probes.append({'player_input':line,'extracted_nominal':nominal,'content_words':re.findall(r"[a-z0-9']+",nominal.lower())})
    dump('nominal_extraction_probe.json',{'evidence_scope':'structural_only','semantic_behavioral_evidence':False,'method':'AST-selected unmodified pure regex helpers; no gameplay modules imported','source':'game/interaction_completion.py','source_sha256':digest(ROOT/'game/interaction_completion.py'),'results':probes})
    print(json.dumps(probes))

if __name__=='__main__':
    if sys.argv[-1]=='initialize': initialize();extract()
