"""Read-only R5 analysis and isolated probes; no proposed runtime implementation."""
from pathlib import Path
import ast, copy, hashlib, json, os, subprocess, sys

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
def load(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
def protected():
    paths=[p for folder in ['game','data','tests','experiments','artifacts/pr_eg_r4','artifacts/pr_eg_r4_r1'] for p in (ROOT/folder).rglob('*') if p.is_file() and not any(s in p.parts for s in ['__pycache__','.pytest_cache'])]
    return {p.relative_to(ROOT).as_posix():digest(p) for p in paths}

def main():
    OUT.mkdir(exist_ok=True)
    if not (OUT/'baseline.json').exists():
        write('baseline.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),protected=protected(),python=sys.executable))
        (OUT/'initial_git_status.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),encoding='utf-8')
    inventory=[]
    for folder in ['game','experiments/pr_do','experiments/pr_dp','experiments/pr_dr']:
        for p in (ROOT/folder).glob('*.py'):
            tree=ast.parse(p.read_text(encoding='utf-8-sig'))
            inventory.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=digest(p),lines=len(p.read_text(encoding='utf-8-sig').splitlines()),functions=[dict(name=n.name,line=n.lineno,end=n.end_lineno,branches=sum(isinstance(x,(ast.If,ast.IfExp,ast.Match,ast.ExceptHandler)) for x in ast.walk(n))) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]))
    write('source_inventory.json',inventory)
    r4=[json.loads(l) for l in (ROOT/'artifacts/pr_eg_r4/turns.jsonl').read_text(encoding='utf-8').splitlines()]
    r1=load('artifacts/pr_eg_r4_r1/live_turns.json')
    selected=[('R4',r4[i]) for i in [3,28,43,48,55,60,61,66,68]]+[('R4-R1',r1[i]) for i in [4,5,11,19]]
    traces=[]
    for era,row in selected:
        res=row['response'].get('resolution') or {}; md=res.get('metadata') or {}; gm=row['response'].get('gm_output') or {}
        player=row['player']; player=player.get('player') if isinstance(player,dict) else player
        traces.append(dict(era=era,conversation=row['conversation'],turn=row['turn'],player=player,delivered=row['text'],resolution_kind=res.get('kind'),metadata=md,social=res.get('social'),gm_metadata=gm.get('metadata'),engine_calls=row.get('engine_calls',row.get('provider_calls')),before_conversation=(row.get('before',{}).get('session') or {}).get('conversational_context')))
    write('historical_trace_extracts.json',traces)
    os.environ.update(ASHEN_DISABLE_LIVE_INTERPRETATION='1',ASHEN_DISABLE_EXPRESSION_GENERATION='1',ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1',ASHEN_PROVIDER_REQUEST_LIMIT='0',ASHEN_DATA_DIR=str(OUT/'isolated_data'))
    from game.dialogue_authority import requested_information,subject_phrase,classify_answer_sufficiency,build_dialogue_authority
    from game.social import authored_topic_relevant_to_question,authored_answer_sufficient_for_question
    from game.conversational_continuity import _best_exchange,continuity_directive,bounded_personal_line
    probes=[]
    for q,f in [
        ('Who manages ferry schedules?','The bell beside the ferry is called the harbor bell.'),
        ('Who assigns shifts at the orchard?','The orchard has a bronze sundial.'),
        ('Why is the orchard closed?','The orchard closes at dusk.'),
        ('Is the eastern gate ever unattended?','Guards watch the eastern gate throughout the night.'),
        ('What is the ferry bell called?','The bell beside the ferry is called the harbor bell.')]:
        rec=dict(id='probe',text=f)
        probes.append(dict(type='predicate',question=q,fact=f,requested=requested_information(q),subject=subject_phrase(q),relevant=authored_topic_relevant_to_question(q,rec),sufficient=authored_answer_sufficient_for_question(q,rec),relation=classify_answer_sufficiency(q,f)))
    for idx in [5,11]:
        row=r1[idx];before=copy.deepcopy(row['before']);session=before['session'];world=before['world']; sid=session.get('scene_id') or 'waystation_courtyard'
        scene=load('artifacts/pr_eg_r4_r1/live_state/primary/data/scenes/waystation_courtyard.json')
        q=row['player']; rows=session.get('conversational_context',{}).get('delivered_exchanges',[])
        best=_best_exchange(q,rows,'')
        probes.append(dict(type='historical_memory',turn=row['turn'],question=q,best=best,directive=continuity_directive(q,session=session,scene=scene,world=world),bounded_fallback=bounded_personal_line('Tavern Runner','tavern_runner','opinion'),source_social=row['response'].get('resolution',{}).get('social')))
    write('controlled_probes.json',dict(evidence_class='C-local production-function probes, not HTTP and not provider experiments',provider_calls=0,input_tokens=0,output_tokens=0,probes=probes))
    print(json.dumps(dict(inventory_modules=len(inventory),historical_traces=len(traces),probes=len(probes))))

if __name__=='__main__':main()
