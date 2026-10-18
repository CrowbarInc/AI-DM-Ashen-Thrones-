"""Durable referent production HTTP qualification in disposable persisted state."""
from __future__ import annotations
import copy
import importlib.util
import json
import os
import sys
import time
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'artifacts/pr_eg_r6_r2_r1'


def specifications():
    from tools.qualify_pr_eg_r6 import npc, topic
    cast = [npc('tavi', 'Tavi', 'warden', [
        topic('copper', 'The miller keeps the copper reliquary.'),
        topic('road', 'Oren says the north road is flooded.'),
        topic('ferry', 'The ferry leaves at dawn.'),
        topic('quay', 'Mara guards the east quay.'),
        topic('jade', 'The artisan maintains the jade compass.'),
        topic('ivory', 'The miller keeps the ivory compass.'),
        topic('roster', 'Someone keeps the roster.'),
        topic('secret', 'The sealed countersign is sword.', 'secret'),
    ], aliases=['warden']), npc('mara', 'Mara', 'warden', [topic('road', 'Oren says the north road is flooded.')], aliases=['warden']),
        npc('oren', 'Oren', 'clerk', [topic('road', 'The north road is called the Crown Way.')])]
    sequences = [
      ['Tavi, who keeps the amber reliquary?', 'I meant the copper reliquary.', 'Who told you?',
       'Tavi, what is the aqueduct called?', 'Who told you?', 'Tavi, who keeps the bell?',
       "I wasn\'t asking about the bell. I meant the north road.", 'Mara, what did Oren say about the road?',
       'Tavi, who keeps the roster?', 'How do you know?', 'Tavi, when does the ferry leave?', 'Who told you?',
       'Warden, who guards the east quay?', 'Tavi, what is the sealed countersign?', 'Tavi, who keeps the copper reliquary?'],
      ['Tavi, who guards the east quay?', 'No, who owns it?', 'Why?', 'Tavi, who keeps the copper reliquary?',
       'What about tomorrow?', 'What did you mean?', 'Tavi, who keeps the roster?', 'Who told you?',
       'Tavi, what did Mara tell Oren?', 'I meant what Oren told Mara.', 'Mara, what did Oren say about the north road?',
       'How do you know?', 'Oren, what is the north road called?', 'Who told you?', 'Tavi, what is the sealed countersign?'],
      ['Tavi, who maintains the jade compass?', 'I meant the ivory compass.', 'How do you know?',
       'Tavi, who keeps the copper reliquary?', 'I meant the ivory compass.', 'Why?',
       'Tavi, what is the aqueduct called?', 'What did you mean?', 'Tavi, when does the ferry leave?',
       'What about tomorrow?', 'Who told you?', 'Tavi, who guards the east quay?', 'And the other one?',
       'Mara, what did Oren say about the road?', 'Tavi, what is the sealed countersign?'],
      ['Tavi, who keeps the copper reliquary?', 'Tavi, when does the ferry leave?', 'Who told you?',
       'Tavi, who keeps the roster?', 'Why?', 'Tavi, who guards the east quay?', 'No, who owns it?',
       'Oren, what is the north road called?', 'How do you know?', 'Mara, what did Oren say about the road?',
       'I meant the bridge.', 'Tavi, what is the aqueduct called?', 'Who told you?',
       'Warden, who keeps the compass?', 'Tavi, what is the sealed countersign?'],
    ]
    specs = [{'id':f'continuity_{i}', 'npcs':copy.deepcopy(cast), 'turns':[(q, {'reload': j in {1, 4, 9}}) for j,q in enumerate(seq)], 'source':'matched_continuity'} for i,seq in enumerate(sequences)]
    cases=json.loads((OUT/'frozen_holdouts.json').read_text())['cases']
    for i in range(2):
        turns=[]
        for c in cases[i*5:i*5+5]:
            for j,q in enumerate(c['turns']):
                turns.append((q, {'holdout_id':c['id'],'expected':c['expected'], 'reload':c.get('reload_before')==j}))
        # Additional distinct questions continue the same saved conversation.
        fill=['Tavi, what is the cistern called?', 'Who told you?', 'Mara, what did Oren say about the bridge?',
              'Tavi, who maintains the jade compass?', 'What about tomorrow?', 'Tavi, who keeps the roster?',
              'Why?', 'Tavi, who guards the east quay?', 'No, who owns it?', 'Tavi, what is the sealed countersign?']
        turns=(turns+[(q,{}) for q in fill])[:15]
        specs.append({'id':f'new_holdouts_{i}','npcs':copy.deepcopy(cast),'turns':turns,'source':'frozen_new'})
    from tools import qualify_pr_eg_r6_r2 as previous
    specs.extend(previous.specifications()[-2:])
    return specs


def run(chosen, target):
    """Production endpoint, real provider, disk reload and complete turn evidence."""
    target.mkdir(exist_ok=True)
    os.environ.update(ASHEN_DATA_DIR=str(target/'state/import'), ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1',
        ASHEN_UNIFIED_SEMANTIC_PLANNING='1', ASHEN_DISABLE_PROVIDER_CALLS='0',
        ASHEN_DISABLE_LIVE_INTERPRETATION='0', ASHEN_DISABLE_EXPRESSION_GENERATION='0',
        ASHEN_PROVIDER_REQUEST_LIMIT='1000', ASHEN_PROVIDER_INPUT_TOKEN_LIMIT='3000000',
        ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT='500000', ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT='3500000',
        ASHEN_PROVIDER_TIMEOUT_SECONDS='30', ASHEN_PROVIDER_USAGE_PATH=str(target/'live_usage.jsonl'),
        ASHEN_SEMANTIC_TRACE_PATH=str(target/'semantic_traces.jsonl'))
    import pytest
    from fastapi.testclient import TestClient
    from game import api, storage
    from game.provider_budget import snapshot
    from game.conversational_referents import state
    from game.immutable_valid_response import verify_delivery_record
    from tests.test_pr_ef_gm_authority import seed_scene
    from tools.qualify_pr_eg_r6 import canonical_view
    from tools.qualify_pr_eg_r6_r1_r1 import contains_secret_value
    # Importing test fixtures sets offline defaults. Explicitly restore live mode.
    os.environ.update(ASHEN_DISABLE_PROVIDER_CALLS='0', ASHEN_DISABLE_LIVE_INTERPRETATION='0', ASHEN_DISABLE_EXPRESSION_GENERATION='0')
    def dump(name, obj):
        (target/name).write_text(json.dumps(obj,indent=2,default=str),encoding='utf-8')
    sources=['game/unified_semantic_planning.py','game/conversational_referents.py','game/conversational_continuity.py','game/semantic_correspondence.py']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in sources}
    dump('qualification_plan.json',chosen);dump('starting_source_hashes.json',hashes)
    (target/'live_turns.jsonl').write_text('')
    rows=[]
    for spec in chosen:
        with pytest.MonkeyPatch.context() as mp:
            seed_scene(target/'state'/spec['id'],mp)
            def set_cast(cast, reset=False):
                world=storage.load_world();world.update(npcs=copy.deepcopy(cast),factions=[]);storage.save_world(world)
                scene=storage.load_active_scene();scene['scene'].update(summary='A quiet public office. '+', '.join(n['name'] for n in cast)+' can answer questions.',
                    visible_facts=[],discoverable_clues=[],addressables=[{'id':n['id'],'name':n['name'],'kind':'npc','aliases':n.get('aliases',[])} for n in cast]);storage.save_scene(scene)
                if reset:
                    session=storage.load_session();session['conversational_context']={};storage.save_session(session)
            set_cast(spec['npcs']); client=TestClient(api.app)
            for turn,(player,expect) in enumerate(spec['turns'],1):
                if expect.get('reset_cast'):set_cast(expect['reset_cast'],True)
                before={'world':storage.load_world(),'character':storage.load_character(),'combat':storage.load_combat(),'session':storage.load_session()}
                reload_ok=None
                if expect.get('reload'):
                    expected=copy.deepcopy(state(before['session']));storage.save_session(before['session'])
                    reload_ok=state(storage.load_session())==expected
                cursor=len(snapshot()['records']);start=time.perf_counter()
                response=client.post('/api/chat?ui_mode=player',json={'text':player,'ui_mode':'player'})
                elapsed=(time.perf_counter()-start)*1000;data=response.json()
                after={'world':storage.load_world(),'character':storage.load_character(),'combat':storage.load_combat(),'session':storage.load_session()}
                gm=data.get('gm_output') or {};text=gm.get('player_facing_text') or '';accepted=(gm.get('metadata') or {}).get('accepted_response') or {}
                history=((after['session'].get('conversational_context') or {}).get('delivered_exchanges') or [])
                resolution=data.get('resolution') or {}
                plan=(resolution.get('social') or {}).get('unified_semantic_plan') or (((resolution.get('metadata') or {}).get('conversational_decision') or {}).get('authorization') or {}).get('unified_semantic_plan') or (history[-1].get('unified_semantic_plan') if history else {}) or {}
                checks={'http':response.status_code==200, 'no_secret':not contains_secret_value(text),
                    'sealed':bool(accepted and verify_delivery_record(accepted)), 'exact':bool(accepted and accepted.get('text')==text),
                    'history_exact':bool(history and history[-1].get('delivered_text')==text),
                    'canonical':canonical_view(before['world'],before['character'],before['combat'])==canonical_view(after['world'],after['character'],after['combat']),
                    'no_secret_clue':not contains_secret_value(json.dumps(after['session'].get('clue_knowledge') or {})),
                    'reload':reload_ok is not False}
                row={'conversation':spec['id'],'turn':turn,'source':spec['source'],'player':player,
                    'expect':{k:v for k,v in expect.items() if k!='reset_cast'},'text':text,'plan':plan,
                    'accepted_response':accepted,'history':history[-1:], 'resolution':resolution,
                    'prior_referents':state(before['session']),'persisted_referents':state(after['session']),
                    'prior_clue_knowledge':before['session'].get('clue_knowledge'), 'clue_knowledge':after['session'].get('clue_knowledge'),
                    'provider_calls':snapshot()['records'][cursor:],'latency_ms':elapsed,'checks':checks}
                with (target/'live_turns.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,default=str)+'\n')
                rows.append(row)
                print(spec['id'],turn,plan.get('response_kind'),plan.get('reason'),checks,text[:110],flush=True)
                if not all(checks.values()):
                    dump('live_status.json',{'status':'STOP','checks':checks,'turns':len(rows),'conversation':spec['id']});return
    dump('live_status.json',{'status':'completed','turns':len(rows),'conversations':len(chosen),
        'source_sha256':hashes,'source_unchanged':all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==v for f,v in hashes.items())})


if __name__ == '__main__':
    baseline='--baseline' in sys.argv
    if baseline:
        spec=importlib.util.spec_from_file_location('game.unified_semantic_planning', OUT/'baseline_sources/game/unified_semantic_planning.py')
        mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
        import game
        game.unified_semantic_planning=mod
    from tools import qualify_pr_eg_r6_r2 as runner
    chosen=specifications()
    if baseline:
        chosen=chosen[:2]
    pilot='--development-pilot' in sys.argv
    predecessor='--predecessor-holdouts' in sys.argv
    if pilot:
        chosen=chosen[:1]; chosen[0]['turns']=chosen[0]['turns'][:12]
    if predecessor:
        chosen=runner.specifications()[4:6]
        for item in chosen:
            item['id']='r6r2_'+item['id']
            item['source']='frozen_predecessor_r6r2'
    target=OUT/('baseline' if baseline else 'pilot' if pilot else 'predecessor_holdouts' if predecessor else 'final'); target.mkdir(exist_ok=True)
    run(chosen, target)
