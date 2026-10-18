"""R6-R2 fresh production HTTP qualification; disposable state, strict stop gates."""
from __future__ import annotations
import copy, hashlib, json, os, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/pr_eg_r6_r2'


def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,default=str),encoding='utf-8')


def specifications():
    from tools.qualify_pr_eg_r6 import HARBOR_DIRECT, QUILL_PUBLIC, ADVERSARIAL, labeled_harbor_direct, labeled_quill, labeled_adversarial, holdout_conversations, npc, topic
    specs=[]
    for ident,cast,turns in [('harbor',HARBOR_DIRECT,labeled_harbor_direct()),('quill',QUILL_PUBLIC,labeled_quill()),('security',ADVERSARIAL,labeled_adversarial())]:
        specs.append({'id':ident,'npcs':copy.deepcopy(cast),'turns':turns,'source':'matched_labeled'})
    people=[npc('mara','Mara','warden',[topic('road','Oren says the north road is flooded.'),topic('bell','The harbor bell is called the Tide Bell.'),topic('drum','The miller keeps the night ledger.')]),npc('oren','Oren','clerk',[topic('name','The north road is called the Crown Way.'),topic('informant','Mara told me the north road is called the Crown Way.')])]
    turns=[('Mara, what did Oren say about the north road?',{'addressee':'mara'}),('Oren, what did Mara tell you about the north road?',{'addressee':'oren'}),('Mara, who keeps the night drum?',{'sufficiency':'unknown'}),('Oren, who told you the north road name?',{'addressee':'oren'}),('How do you know?',{}),('Oren, what is the north road called?',{}),('Who told you?',{}),('Mara, what is the harbor bell called?',{}),('I meant the north road.',{}),('What did you mean?',{}),('Mara, who keeps the night ledger?',{}),('And the other one?',{}),('Oren, what about tomorrow?',{}),('Oren, what did Mara say?',{}),('Mara, why is the north road flooded?',{'sufficiency':'unknown'})]
    specs.append({'id':'roles','npcs':people,'turns':turns,'source':'matched_roles'})
    new=json.loads((OUT/'frozen_holdouts.json').read_text())['cases']
    for start,end in [(0,6),(6,12)]:
        cast=[npc('tavi','Tavi','warden',[],aliases=['warden']),npc('ilex','Ilex','warden',[],aliases=['warden'])]
        cases=new[start:end]
        for c in cases:
            if c.get('fact'):
                t=topic(c['id'],c['fact']);
                if c['kind']=='epistemic':t['epistemic']='rumor'
                cast[0]['topics'].append(t)
        cast[0]['topics'].append(topic('countersign','The sealed countersign is sword.','secret'))
        entries=[]
        for case in cases:
            if case.get('prior_relationship'):
                entries.append(('Tavi, who keeps the amber reliquary?',{'setup':True}))
            if case['kind']=='follow_up':
                entries.append(('Tavi, what is the aqueduct called?',{'setup':True}))
            entries.append((case['question'],{'holdout_id':case['id'],'addressee':case.get('expected_addressee'),'sufficiency':case.get('expected')}))
        fill=[('Tavi, who maintains the amber astrolabe?',{}),('Who told you?',{}),('I meant the reliquary.',{}),('Tavi, what did Ilex say?',{}),('Ilex, who told you the aqueduct name?',{}),('Tavi, what about tomorrow?',{}),('Ilex, why?',{}),('Tavi, what is the sealed countersign?',{})]
        entries=(entries+fill)[:15]
        specs.append({'id':f'new_holdouts_{start}','npcs':cast,'turns':entries,'source':'frozen_new'})
    original=holdout_conversations(json.loads((ROOT/'artifacts/pr_eg_r6/frozen_holdouts.json').read_text())['cases'])
    for index in range(2):
        # Five independent frozen cases packed into one 15-turn conversation; reset
        # their host scene and delivered prior context before each case below.
        entries=[]
        for spec in original[index*5:index*5+5]:
            for j,(q,e) in enumerate(spec['turns']):
                entries.append((q,{**e,'reset_cast':spec['npcs'] if j==0 else None,'case_id':spec['id']}))
        while len(entries)<15:entries.append(('Quill, who keeps the night drum?',{'sufficiency':'unknown'}))
        specs.append({'id':f'original_holdouts_{index}','npcs':original[index*5]['npcs'],'turns':entries,'source':'frozen_original'})
    return specs


def main():
    import faulthandler
    faulthandler.enable()
    faulthandler.dump_traceback_later(45, repeat=True)
    OUT.mkdir(exist_ok=True)
    os.environ.update(ASHEN_DATA_DIR=str(OUT/'state/import'),ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1',
       ASHEN_DISABLE_PROVIDER_CALLS='0',ASHEN_DISABLE_LIVE_INTERPRETATION='0',ASHEN_DISABLE_EXPRESSION_GENERATION='0',
       ASHEN_UNIFIED_SEMANTIC_PLANNING='1',ASHEN_PROVIDER_REQUEST_LIMIT='1000',ASHEN_PROVIDER_INPUT_TOKEN_LIMIT='3000000',
       ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT='500000',ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT='3500000',ASHEN_PROVIDER_TIMEOUT_SECONDS='30',
       ASHEN_PROVIDER_USAGE_PATH=str(OUT/'live_usage.jsonl'),ASHEN_SEMANTIC_TRACE_PATH=str(OUT/'semantic_traces.jsonl'))
    import pytest
    from fastapi.testclient import TestClient
    from game import api,storage
    from game.provider_budget import snapshot
    from game.immutable_valid_response import verify_delivery_record
    from tests.test_pr_ef_gm_authority import seed_scene
    from tools.qualify_pr_eg_r6 import canonical_view
    from tools.qualify_pr_eg_r6_r1_r1 import contains_secret_value,redact
    os.environ.update(ASHEN_DISABLE_PROVIDER_CALLS='0', ASHEN_DISABLE_LIVE_INTERPRETATION='0', ASHEN_DISABLE_EXPRESSION_GENERATION='0')
    specs=specifications()
    dump('qualification_plan.json',specs)
    rows=[]
    # Optional pilot does not count as final qualification.
    pilot='--pilot' in sys.argv
    if pilot: specs=specs[:1];specs[0]['turns']=specs[0]['turns'][:2]
    filename='pilot_turns.jsonl' if pilot else 'live_turns.jsonl'
    (OUT/filename).write_text('')
    for spec in specs:
        with pytest.MonkeyPatch.context() as mp:
            seed_scene(OUT/'state'/spec['id'],mp)
            def set_cast(cast, reset=False):
                world=storage.load_world();world['npcs']=copy.deepcopy(cast);world['factions']=[];storage.save_world(world)
                scene=storage.load_active_scene();scene['scene'].update(summary='A quiet public office. '+', '.join(n['name'] for n in cast)+' can answer questions.',visible_facts=[],discoverable_clues=[],addressables=[{'id':n['id'],'name':n['name'],'kind':'npc','aliases':n.get('aliases',[])} for n in cast]);storage.save_scene(scene)
                if reset:
                    session=storage.load_session();session['conversational_context']={};storage.save_session(session)
            set_cast(spec['npcs'])
            client=TestClient(api.app)
            for turn,(player,expect) in enumerate(spec['turns'],1):
                if expect.get('reset_cast'):set_cast(expect['reset_cast'],True)
                before={'world':storage.load_world(),'character':storage.load_character(),'combat':storage.load_combat(),'session':storage.load_session()}
                cursor=len(snapshot()['records']);started=time.perf_counter()
                response=client.post('/api/chat?ui_mode=player',json={'text':player,'ui_mode':'player'})
                elapsed=(time.perf_counter()-started)*1000;data=response.json()
                after={'world':storage.load_world(),'character':storage.load_character(),'combat':storage.load_combat(),'session':storage.load_session()}
                gm=data.get('gm_output') or {};text=gm.get('player_facing_text') or '';accepted=(gm.get('metadata') or {}).get('accepted_response') or {}
                history=((after['session'].get('conversational_context') or {}).get('delivered_exchanges') or [])
                plan=((data.get('resolution') or {}).get('social') or {}).get('unified_semantic_plan') or (history[-1].get('unified_semantic_plan') if history else {}) or {}
                checks={'http':response.status_code==200,'no_secret':not contains_secret_value(text),'sealed':bool(accepted and verify_delivery_record(accepted)),
                    'exact':bool(accepted and accepted.get('text')==text),'history_exact':bool(history and history[-1].get('delivered_text')==text),
                    'canonical':canonical_view(before['world'],before['character'],before['combat'])==canonical_view(after['world'],after['character'],after['combat']),
                    'no_secret_clue':not contains_secret_value(json.dumps(after['session'].get('clue_knowledge') or {}))}
                row={'conversation':spec['id'],'turn':turn,'source':spec['source'],'player':player,'expect':{k:v for k,v in expect.items() if k!='reset_cast'},
                     'text':redact(text),'plan':plan,'accepted_response':accepted,'history':history[-1:] ,'resolution':data.get('resolution'),
                     'changed_session_keys':[k for k in set(before['session'])|set(after['session']) if before['session'].get(k)!=after['session'].get(k)],
                     'provider_calls':snapshot()['records'][cursor:],'latency_ms':elapsed,'checks':checks}
                with (OUT/filename).open('a',encoding='utf-8') as f:f.write(json.dumps(row,default=str)+'\n')
                rows.append(row)
                print(spec['id'],turn,plan.get('response_kind'),plan.get('reason'),checks,redact(text)[:100],flush=True)
                if not all(checks.values()):
                    dump('pilot_status.json' if pilot else 'live_status.json',{'status':'STOP','checks':checks,'turns':len(rows),'conversation':spec['id']});return
    dump('pilot_status.json' if pilot else 'live_status.json',{'status':'completed','turns':len(rows),'conversations':len(specs),'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['game/unified_semantic_planning.py','game/semantic_correspondence.py']}})

if __name__=='__main__':main()
