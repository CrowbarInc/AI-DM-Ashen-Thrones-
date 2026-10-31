"""Isolated PR12 experiments. Copy into sandbox/tests before running."""
import copy
import json
import socket
from pathlib import Path
import pytest
from tests.test_pr_play_04_opening_integrity import opening_world, _start, _snap

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'results'
RUNS=ROOT/'artifacts/atgb/automated_playtests'
LATEST='20261031T170523Z-92cd9d058c92'
HISTORY=['20261030T183848Z-5fe421902485','20261030T191257Z-ecc1b6062bdc','20261031T015747Z-5a6c03c902e3',LATEST]

@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def denied(*a,**k): raise AssertionError('PR12 forbids external network')
    monkeypatch.setattr(socket.socket,'connect',denied)
    OUT.mkdir(parents=True,exist_ok=True)

def install(opening_world,monkeypatch,run=LATEST):
    import game.storage as st
    import game.api as api
    import game.immutable_valid_response as ivr
    src=RUNS/run
    docs=json.loads((src/'baseline/documents.json').read_text())
    for rel,value in docs.items():
        path=st.DATA_DIR/rel
        if rel.endswith('.jsonl'):
            path.write_text(''.join(json.dumps(r)+'\n' for r in value) if isinstance(value,list) else str(value or ''),encoding='utf-8')
        else: st._save_json(path,value)
    api.compose_state()
    parsed=json.loads(next((src/'opening_response_evidence').glob('*.json')).read_text())['parsed_response']
    opening_world['state']['text']=json.dumps(parsed)
    traces=[]
    original=ivr.validate_generated_response
    def observe(text,**kwargs):
        result=original(text,**kwargs)
        traces.append(copy.deepcopy(dict(text=text,inputs=kwargs,result=result)))
        return result
    monkeypatch.setattr(ivr,'validate_generated_response',observe)
    return parsed,traces

def disk():
    import game.storage as st
    return {str(p.relative_to(st.DATA_DIR)):p.read_text(encoding='utf-8') for p in st.DATA_DIR.rglob('*') if p.is_file() and (p.suffix in {'.json','.jsonl'}) and 'diagnostic' not in str(p)}

def gameplay(files):
    out={}
    for key,text in files.items():
        if key.endswith('.jsonl'): out[key]=text; continue
        obj=json.loads(text)
        if isinstance(obj,dict) and 'persistence_version' in obj: obj=obj['payload']
        obj=copy.deepcopy(obj)
        if isinstance(obj,dict):
            for field in ('last_saved_at','debug_traces','__turn_start_active_interaction_target_id'):
                obj.pop(field,None)
        out[key]=obj
    return out

@pytest.mark.parametrize('run',HISTORY)
def test_history(opening_world,monkeypatch,run):
    parsed,traces=install(opening_world,monkeypatch,run)
    before=disk(); snap=_snap()
    response,status=_start()
    after=disk()
    row=dict(run=run,status=status,traces=traces,response=response,before=snap,after=_snap(),persistent_before=before,persistent_after=after,synthetic_calls=len(opening_world['calls']),live_calls=0)
    (OUT/(run+'_replay.json')).write_text(json.dumps(row,indent=2))
    assert status==(200 if run in HISTORY[:2] else 422)
    assert len(opening_world['calls'])==1
    assert traces and traces[0]['inputs']['declared_claims']==parsed['declared_claims']
    if status==422:
        assert 'unauthorized_resolution_decision_fact' in traces[0]['result']['reasons']
        assert _snap()==snap
        assert gameplay(before)==gameplay(after)
    else:
        assert _snap()['turn_counter']==snap['turn_counter']+1
        assert _start()[1]==409

def corpus(parsed):
    claims=parsed['declared_claims']
    texts={c['source_claim_id']:c['text'] for c in claims}
    runner=texts['rc_3b26b521977b']; notice=texts['rc_a83c5bcfc65e']
    rows=[
      ('E1',runner,'supported','Exact authored statement.'),
      ('E2','Near the rain barrel, a tavern runner trades hot stew and rumors.','supported','Word order preserves actor, exchange, location.'),
      ('E3','A tavern runner trades hot stew and gossip near the rain barrel.','supported','Gossip is used for informal rumors; no reliability assertion.'),
      ('E4','The notice board lists taxes, curfew rules, and a warning about a patrol that has gone missing.','supported','Present perfect missing status preserves posting and patrol status.'),
      ('E5',runner+' Rain patters on the gate stones.','incidental','Turn-local sensory rain grounded by wet gate scene; no transition.'),
      ('E6','A second gate stands open behind the guards.','unsupported','New navigable topology and opening status; beyond sensory permission.'),
      ('E7','The gate serjeant secretly accepts bribes from the smugglers.','unsupported','New NPC corruption and hidden transaction.'),
      ('E8','You automatically succeed at the persuasion check.','unsupported','No player action or resolver success exists.'),
      ('E9','You kill the gate serjeant with a single blow.','unsupported','New death without combat adjudication.'),
      ('E10','You pass the guards and enter the city.','unsupported','Arrival requires transition authority.'),
      ('E11','The threadbare watcher is waiting on a coordinated signal from someone already past the checkpoint.','hidden','Exact scene hidden fact, no reveal receipt.'),
      ('E12','You have rescued the missing patrol and completed the quest.','unsupported','Unresolved hook turned into completion.'),
      ('E13','The eastern gate is abandoned; no guards remain.','contradiction','Contradicts active authored guards.'),
      ('E14','The tavern runner sells reliable intelligence about the missing patrol.','ambiguous','Rumors become reliable and patrol specific; do not accept as equivalence.'),
      ('E15',runner+' The guards award you 100 gold.','unsupported','Supported fact plus unauthorized resource change.'),
      ('E16','A tavern runner trades hot stew and rumors near the rain barrel, while a gate serjeant manages the crowd and keeps one eye on the roster board.','supported','Conjoins two separate supported statements, no causality.'),
      ('E17','Rain patters on a worn cloak.','omission','Omits all claimed MUST_STATE facts; test obligation enforcement, not invented fact.'),
      ('E18',runner+' '+runner,'supported','Duplication adds no authority.'),
      ('E19','The notice board names Varek as the murderer.','false_provenance','New declaration with forged authored provenance, no source match.'),
      ('E20','The guards award you 100 gold.','unsupported','Unmodified valid declarations with unsupported resource prose.'),
    ]
    return [dict(id=i,text=t,interpretation=v,rationale=r) for i,t,v,r in rows]

@pytest.mark.parametrize('case_id',['E'+str(i) for i in range(1,21)])
def test_corpus(opening_world,monkeypatch,case_id):
    parsed,traces=install(opening_world,monkeypatch)
    row=next(r for r in corpus(parsed) if r['id']==case_id)
    parsed['narration']=parsed['player_facing_text']=row['text']
    if case_id=='E19':
        parsed['declared_claims'].append(dict(parsed['declared_claims'][0],declaration_id='forged',source_claim_id=None,text=row['text']))
    opening_world['state']['text']=json.dumps(parsed)
    before=disk(); response,status=_start()
    after=disk()
    gb,ga=gameplay(before),gameplay(after)
    invariant_files=['character.json','combat.json','conditions.json','campaign.json']
    state_protection={key:gb.get(key)==ga.get(key) for key in invariant_files}
    state_protection['npc_state']=gb['world.json'].get('npcs')==ga['world.json'].get('npcs')
    state_protection['active_scene']=gb['session.json'].get('active_scene_id')==ga['session.json'].get('active_scene_id')
    result=dict(**row,status=status,traces=traces,response=response,rollback_equal=(gb==ga),raw_bytes_equal=(before==after),state_protection=state_protection,synthetic_calls=len(opening_world['calls']))
    (OUT/(case_id+'.json')).write_text(json.dumps(result,indent=2))
    assert status in {200,422}
    assert len(opening_world['calls'])==1
    assert all(state_protection.values())
    if status==422: assert result['rollback_equal']

def test_span_causal_controls(opening_world,monkeypatch):
    parsed,traces=install(opening_world,monkeypatch)
    assert _start()[1]==422
    from game.immutable_valid_response import validate_generated_response
    from game import gm_resolution_decision as gd
    context=traces[0]['inputs']; audit=traces[0]['result']['gm_resolution_decision_audit']
    rows=[]
    for violation in audit['violations']:
        text=violation['text']
        candidates=sorted(parsed['declared_claims'],key=lambda c:len(gd._token_set(text)&gd._token_set(c['text'])),reverse=True)
        c=candidates[0]; source=c['text']
        fixed=parsed['narration'].replace(text,source)
        rows.append(dict(violation=violation,candidate=c,extra_tokens=sorted(gd._token_set(text)-gd._token_set(source)),coverage=gd._empty_identity_covers(text,source),restates=gd._proposition_restates_statement(text,source),single_replacement_result=validate_generated_response(fixed,**context)))
    fixed=parsed['narration']
    for r in rows: fixed=fixed.replace(r['violation']['text'],r['candidate']['text'])
    all_fixed=validate_generated_response(fixed,**context)
    (OUT/'spans.json').write_text(json.dumps(dict(rows=rows,all_fixed_result=all_fixed,context=context),indent=2))
    assert all_fixed['hard_valid']
    assert audit['declaration_validation']['hard_valid']

def test_single_word_replacement_through_normal_commit(opening_world,monkeypatch):
    parsed,traces=install(opening_world,monkeypatch)
    original='Threadbare watchers and refugees cluster tightly along the muddy gate line.'
    replacement='Threadbare watchers and refugees cluster along the muddy gate line.'
    for field in ('narration','player_facing_text'):
        assert original in parsed[field]
        parsed[field]=parsed[field].replace(original,replacement)
    opening_world['state']['text']=json.dumps(parsed)
    before=_snap(); response,status=_start()
    (OUT/'single_word_commit.json').write_text(json.dumps(dict(status=status,before=before,after=_snap(),traces=traces,response=response),indent=2))
    assert status==200
    assert _snap()['turn_counter']==before['turn_counter']+1
    assert _start()[1]==409
    assert len(opening_world['calls'])==1

def test_prototype_matrix_and_input_immutability():
    from prototypes_pr12 import experiment
    context=json.loads((OUT/'spans.json').read_text())['context']
    rows=[json.loads((OUT/('E'+str(i)+'.json')).read_text()) for i in range(1,21)]
    before=copy.deepcopy(context)
    result=experiment(context,rows)
    assert len(result['corpus'])==20 and len(result['attack_controls'])==4
    assert context==before
    assert not any(r['C'].get('state_mutations') for r in result['corpus'])
    (OUT.parent/'prototype_results.json').write_text(json.dumps(result,indent=2))
