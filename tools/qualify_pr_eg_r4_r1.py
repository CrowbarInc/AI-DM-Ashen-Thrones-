"""R4-R1 isolated baseline, frozen failure replay and fresh HTTP qualification."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'artifacts/pr_eg_r4_r1'

def save(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str), encoding='utf-8')

def baseline():
    OUT.mkdir(exist_ok=True)
    save('baseline.json', dict(revision=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        status=subprocess.check_output(['git','status','--short','--untracked-files=normal'], cwd=ROOT, text=True),
        configuration={line.split('=',1)[0]: line.split('=',1)[1] for line in (ROOT/'.env').read_text().splitlines()
                       if '=' in line and any(k in line.split('=',1)[0] for k in ('MODEL','PROVIDER','ENABLE','DISABLE','TIMEOUT')) and not any(k in line.split('=',1)[0] for k in ('KEY','SECRET','TOKEN'))},
        sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'game').glob('*.py')}))
    import shutil
    for name in ('CURRENT_REVIEW.md','CURRENT_REVIEW.zip','REVIEW_MANIFEST.json'):
        dest=ROOT/'handoff/history/pr_eg_r4_before_r1'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists(): shutil.copy2(ROOT/'handoff'/name, dest)
    replay('original_reproduction.json')
    regression('baseline')

def regression(label):
    selection=json.loads((ROOT/'artifacts/pr_eg_r4/regression_selection.json').read_text())
    # Preserve all pre-existing generated outputs the historical family can touch.
    tracked=subprocess.check_output(['git','ls-files','data','artifacts','docs'],cwd=ROOT,text=True).splitlines()
    snapshots={ROOT/p:(ROOT/p).read_bytes() for p in tracked if (ROOT/p).is_file()}
    cmd=[sys.executable,'-m','pytest',*selection,'-q','--tb=short','-o','faulthandler_timeout=90',
         f'--junitxml=artifacts/pr_eg_r4_r1/{label}_junit.xml',f'--basetemp=artifacts/pr_eg_r4_r1/tmp_{label}']
    with (OUT/f'{label}_output.txt').open('w',encoding='utf-8') as log:
        env=os.environ.copy()
        env.pop('ASHEN_DISABLE_PROVIDER_CALLS',None)
        env['ASHEN_PROVIDER_REQUEST_LIMIT']='0'  # No external calls; mocked expression seam stays enabled.
        result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    restored=[]
    for p, raw in snapshots.items():
        if not p.exists() or p.read_bytes()!=raw:
            p.write_bytes(raw); restored.append(str(p.relative_to(ROOT)))
    save(f'{label}_run.json',dict(command=cmd,exit_code=result.returncode,restored=restored))
    print(label,result.returncode,flush=True)

def frozen():
    rows=[json.loads(l) for l in (ROOT/'artifacts/pr_eg_r4/turns.jsonl').read_text(encoding='utf-8').splitlines()]
    return next(r for r in rows if r['conversation']=='B_skeptical' and r['turn']==9)

def replay(name='repaired_reproduction.json'):
    os.environ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT']='1'
    os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1'
    import pytest
    from game import api, storage
    from game.immutable_valid_response import run_preserve_if_valid, accepted_record
    from game.conversational_continuity import record_delivered_exchange
    from tests.test_pr_ef_gm_authority import seed_scene
    row=frozen()
    evidence=json.loads((ROOT/'artifacts/pr_eg_r4/critical_stop_evidence.json').read_text())
    res=copy.deepcopy(row['response']['resolution'])
    state=json.loads((ROOT/'artifacts/pr_eg_r4/states/B_skeptical_08.json').read_text())
    with pytest.MonkeyPatch.context() as mp:
        seed_scene(OUT/'replay_state',mp)
        gm=run_preserve_if_valid(dict(player_facing_text=evidence['exact_rejected_candidate'],metadata={}),
            regenerate=None,resolution=res,player_text=evidence['player'],session=copy.deepcopy(state['session']),
            scene=storage.load_active_scene(),world=state['world'])
        gate=copy.deepcopy(accepted_record(gm))
        final,_=api._finalize_player_facing_for_turn(gm,resolution=res,session=copy.deepcopy(state['session']),
            world=copy.deepcopy(state['world']),scene=storage.load_active_scene())
        api._preserve_authoritative_resolution_facts_after_gate(final,resolution=res,scene=storage.load_active_scene(),world=state['world'])
        history={}
        adoption=accepted_record(final)
        delivered=record_delivered_exchange(history,player_text=evidence['player'],delivered_text=final['player_facing_text'],social=res.get('social'),
                                            adoption=adoption if adoption.get('immutable') else None)
        result=dict(candidate=evidence['exact_rejected_candidate'],gate=gate,final=final,delivered_history=delivered,
                    sequence=['run_preserve_if_valid','_finalize_player_facing_for_turn','_preserve_authoritative_resolution_facts_after_gate','record_delivered_exchange'],
                    original_source='artifacts/pr_eg_r4/turns.jsonl:B_skeptical:9')
        save(name,result)
        print(name,gate.get('provenance'),repr(gate.get('text')),'=>',repr(final['player_facing_text']),flush=True)
    return result

PLANS={
    'primary':('A',[
        'I ask Sergeant Mara what the street beyond the gate is called.',
        'I ask Tavern Runner what food is available.',
        'I ask Sergeant Mara whether guards watch the north gate at night.',
        'Say that another way.',
        'I ask Tavern Runner whether you prefer the morning or evening.',
        'Why do you prefer that time?',
        'GM, what exactly did Mara say about the north road?',
        'Do either of you manage guard schedules, or is that someone else?',
        'I ask Sergeant Mara whether the north gate is ever left unattended.',
        'I ask Sergeant Mara to promise me a reward if I help.',
        'I ask Tavern Runner who made the lantern.',
        'GM, what did Mara say about the gate?']),
    'secondary':('B',[
        'I ask Keeper Nara what the bell beside the ferry is called.',
        'I ask Clerk Oren what the street beyond the harbor gate is called.',
        'I ask Keeper Nara whether guards watch the harbor gate at night.',
        'Say that in simpler words.',
        'I ask Clerk Oren whether you prefer the morning or evening.',
        'Why do you prefer that time?',
        'GM, what exactly did Nara say about the harbor bell?',
        "I mean both of your repeated statements about the harbor bell. Could you please stop repeating that and clearly answer: do either of you manage ferry schedules and harbor coordination, or is that someone else's job?",
        'I ask Keeper Nara whether the harbor gate is ever unguarded.',
        'I ask Clerk Oren to promise me ten silver if I help.',
        'I ask Keeper Nara who owns the bell.',
        'GM, what did Oren say about the road?'])}

def live():
    os.environ.update(ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1',ASHEN_DISABLE_PROVIDER_CALLS='0',
        ASHEN_DISABLE_LIVE_INTERPRETATION='0',ASHEN_DISABLE_EXPRESSION_GENERATION='0',
        ASHEN_PROVIDER_REQUEST_LIMIT='100',ASHEN_PROVIDER_INPUT_TOKEN_LIMIT='240000',
        ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT='30000',ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT='270000',
        ASHEN_PROVIDER_TIMEOUT_SECONDS='45',ASHEN_PROVIDER_USAGE_PATH=str(OUT/'live_usage_final.jsonl'),
        ASHEN_DATA_DIR=str(OUT/'live_import_state'))
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env')
    save('live_plan.json',PLANS)
    if not os.environ.get('OPENAI_API_KEY'):
        save('live_status.json',dict(status='UNVERIFIED',reason='key_missing'));return
    import pytest
    from fastapi.testclient import TestClient
    from game import api,storage
    from game.provider_budget import snapshot
    from tests.test_pr_ef_gm_authority import seed_scene
    from tools.qualify_pr_eg_r4 import SCENES
    from tools.validate_pr_eg_r3_r1 import diff
    from game.immutable_valid_response import verify_delivery_record
    rows=[]
    for label,(scene_key,turns) in PLANS.items():
        with pytest.MonkeyPatch.context() as mp:
            seed_scene(OUT/'live_state'/label,mp)
            spec=SCENES[scene_key]
            world=storage.load_world();world['npcs']=copy.deepcopy(spec['npcs']);world['factions']=[]
            next(n for n in world['npcs'] if n['id']==spec['restricted']['holder'])['affiliation']='ash_cowl'
            storage.save_world(world)
            scene=storage.load_active_scene()
            scene['scene'].update(summary=spec['visible'],visible_facts=[spec['visible']],discoverable_clues=[])
            storage.save_scene(scene)
            client=TestClient(api.app)
            for number,player in enumerate(turns,1):
                before=dict(world=storage.load_world(),session=storage.load_session(),character=storage.load_character(),combat=storage.load_combat())
                cursor=len(snapshot()['records']);started=time.perf_counter()
                response=client.post('/api/chat?ui_mode=player',json=dict(text=player,ui_mode='player'))
                elapsed=(time.perf_counter()-started)*1000
                data=response.json()
                after=dict(world=storage.load_world(),session=storage.load_session(),character=storage.load_character(),combat=storage.load_combat())
                gm=data.get('gm_output') or {};record=(gm.get('metadata') or {}).get('accepted_response') or {}
                text=gm.get('player_facing_text','')
                history=(after['session'].get('conversational_context') or {}).get('delivered_exchanges') or []
                old_history=(before['session'].get('conversational_context') or {}).get('delivered_exchanges') or []
                checks=dict(http_ok=response.status_code==200,contract_present=bool(record),
                    exact_authorized=record.get('text')==text,valid_digest=bool(record) and verify_delivery_record(record),
                    history_exact=history!=old_history and bool(history) and history[-1].get('delivered_text')==text,
                    hidden_not_delivered='ash_cowl' not in text.lower() and 'ash cowl' not in text.lower())
                row=dict(conversation=label,turn=number,player=player,text=text,response=data,before=before,after=after,
                    checks=checks,latency_ms=elapsed,provider_calls=snapshot()['records'][cursor:],
                    canonical_changes={k:diff(before[k],after[k]) for k in ('world','character','combat')})
                if number==6:
                    saved=copy.deepcopy(storage.load_session());storage.save_session(saved)
                    row['reload_exact']=storage.load_session()==saved
                    client.close();client=TestClient(api.app)
                rows.append(row);save('live_turns.json',rows)
                print(label,number,json.dumps(checks),repr(text),flush=True)
                if not all(checks.values()):
                    save('live_status.json',dict(status='STOP',conversation=label,turn=number,checks=checks));return
    save('live_status.json',dict(status='completed',turns=len(rows),budget=snapshot()))

if __name__=='__main__':
    {'baseline':baseline,'replay':replay,'regression':lambda:regression('repaired'),'live':live}[sys.argv[1]]()
