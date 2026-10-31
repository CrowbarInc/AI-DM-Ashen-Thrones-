"""Summarize retained offline/historical evidence without contacting providers."""
import ast
import hashlib
import json
import math
import statistics
import time
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from measure_pr_play_06 import size, write


def analyze():
    root=Path('artifacts/pr_play_06')
    inventory=[]
    for name in ['minimal','declarations']:
        request=json.loads((root/'requests'/f'{name}.json').read_text())
        before=json.loads((root/'requests_before'/f'{name}.json').read_text())
        messages=request['input']; payload=json.loads(messages[-1]['content'])
        components=[]
        conditional={'combat','clues','discoverable_hinting','active_interlocutor','active_topic_anchor',
                     'social_context','recent_log','selected_conversational_memory','interaction_continuity',
                     'interlocutor_lead_context','interlocutor_lead_behavior_hints','lead_context','follow_up_pressure'}
        uncertain={'dialogue_social_plan','world','world_state','turn_packet','narrative_plan',
                   'decision_facing_answer_recipe','response_policy','session','turn_summary'}
        for key,value in payload.items():
            text=json.dumps(value,ensure_ascii=False)
            components.append({'component':key,**size(text),
                               'class':'B' if key in conditional else 'E' if key in uncertain else 'A',
                               'action':'retain; no reduction established safe'})
        components.sort(key=lambda r:-r['characters'])
        # Find exact repeats for investigation only: identical fields need not be redundant instructions.
        repeats=[]
        def walk(value,path):
            if isinstance(value,dict):
                for k,v in value.items(): yield from walk(v,path+'.'+k)
            elif isinstance(value,list):
                for i,v in enumerate(value): yield from walk(v,path+f'[{i}]')
            elif isinstance(value,str) and len(value)>80:
                yield value,path
        seen={}
        for value,path in walk(payload,'user'):
            if value in seen: repeats.append({'first':seen[value],'repeated':path,'characters':len(value),
                                             'class':'C','action':'retain; semantic location may carry independent authority'})
            else: seen[value]=path
        inventory.append({'fixture':name,'source':'current production request captured at SDK stub',
                          'system':size(messages[0]['content']),'user':size(messages[-1]['content']),
                          'before_system':size(before['input'][0]['content']),
                          'before_user':size(before['input'][-1]['content']),
                          'components':components,'exact_repeated_string_candidates':repeats,
                          'reduction_characters':0,'reduction_tokens':0})
    write('prompt_inventory.json',inventory)
    old=ast.parse((root/'entry/gm.py').read_text(encoding='utf-8-sig'))
    new=ast.parse(Path('game/gm.py').read_text(encoding='utf-8-sig'))
    prompt_names=['build_messages','collect_narration_context_call_kwargs','_provider_response_contract_from_payload',
                  '_provider_response_contract_from_messages','_safe_json']
    checks=[]
    for name in prompt_names:
        get=lambda tree: ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name))
        checks.append({'function':name,'unchanged':get(old)==get(new)})
    old_constants=[ast.dump(n) for n in old.body if isinstance(n,(ast.Assign,ast.AnnAssign))]
    new_constants=[ast.dump(n) for n in new.body if isinstance(n,(ast.Assign,ast.AnnAssign))]
    checks.append({'function':'all top-level assignments (including system/response contracts)',
                   'unchanged':old_constants==new_constants})
    assert all(c['unchanged'] for c in checks)
    write('prompt_integrity.json',{'evidence_scope':'structural_only','source_checks':checks,
          'fixtures':['market_quarter','frontier_gate'],
          'matrix':{k:'preserved; unchanged prompt producer and captured request components'
                    for k in ['scene identity','character identity','NPC context','authorized visible facts',
                              'hidden-fact protection','structured declarations','gameplay authority','opening instructions']},
          'reductions':[]})
    historical=Path('artifacts/pr_play_05/manual-20261028-214900')
    def read_state(name):
        raw=(historical/name).read_bytes()
        try: text=raw.decode('utf-8-sig')
        except UnicodeDecodeError: text=raw.decode('cp1252')
        return json.loads(text)
    ledger=[json.loads(line) for line in (historical/'provider_usage.jsonl').read_text().splitlines()]
    write('historical_evidence.json',{'source':historical.as_posix(),
          'ledger_sha256':hashlib.sha256((historical/'provider_usage.jsonl').read_bytes()).hexdigest(),
          'state_decoding':'UTF-8 with Windows cp1252 fallback for historical PowerShell capture',
          'rows':ledger,'before_state':read_state('before_state.json'),
          'after_state':read_state('after_state.json')})
    protected=json.loads((root/'protected_entry.json').read_text())
    changed=[p for p,digest in protected.items() if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=digest]
    added=[str(p).replace('\\','/') for base in ['data','experiments'] for p in Path(base).rglob('*')
           if p.is_file() and '__pycache__' not in p.parts and str(p).replace('\\','/') not in protected]
    write('protected_integrity.json',{'count':len(protected),'changed':changed,'added':added})
    assert not changed and not added
    from game.gm import _requested_response_type_from_messages, _opening_max_output_tokens
    messages=json.loads((root/'requests/declarations.json').read_text())['input']
    times=[]
    for _ in range(200):
        started=time.perf_counter()
        _requested_response_type_from_messages(messages); _opening_max_output_tokens()
        times.append((time.perf_counter()-started)*1000)
    write('performance.json',{'scope':'new response-type parse and opening setting selection only; no network',
          'iterations':len(times),'median_ms':statistics.median(times),'max_ms':max(times),
          'prompt_reduction_characters':0})


if __name__=='__main__': analyze()
