"""Bounded validation harness. No production source edits, prompt edits, or stubs."""
from pathlib import Path
import copy, dataclasses, enum, hashlib, json, os, sys, time
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'artifacts/atgb/atgb_r1_03'
trial = sys.argv[1]
assert trial in ['L1', 'L2', 'L3', 'L4']
dest = OUT / trial
dest.mkdir(exist_ok=False)
from tools.atgb.isolation import prepare_isolated_store, assert_imported_data_dir
store = prepare_isolated_store(dest / 'store', scenario_id=trial, repo=ROOT, player_campaign_dir=ROOT/'data')
os.environ.update(ASHEN_DATA_DIR=str(store), ASHEN_PROVIDER_REQUEST_LIMIT='2',
    ASHEN_PROVIDER_USAGE_PATH=str(dest/'provider_usage.jsonl'),
    ASHEN_DISABLE_PROVIDER_RETRIES='1', ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1')
from game import storage
assert_imported_data_dir(storage.DATA_DIR, store, repo=ROOT, player_campaign_dir=ROOT/'data')
from game.campaign_reset import apply_new_campaign_hard_reset
apply_new_campaign_hard_reset()
from game.config import DEFAULT_MODEL_NAME, HIGH_PRECISION_MODEL_NAME, RETRY_ESCALATION_MODEL_NAME
assert {DEFAULT_MODEL_NAME,HIGH_PRECISION_MODEL_NAME,RETRY_ESCALATION_MODEL_NAME} == {'gpt-4.1-mini'}
from game.provider_budget import initialize_accounting, snapshot
initialize_accounting()
# Bound SDK transport retries in this validation process, retaining real requests.
import openai
RealOpenAI = openai.OpenAI
sdk_clients = []
def bounded_client(*args, **kwargs):
    kwargs['max_retries'] = 0
    client = RealOpenAI(*args, **kwargs)
    sdk_clients.append({'max_retries':client.max_retries})
    return client
openai.OpenAI = bounded_client
from game.api import chat
from game.models import ChatRequest
historical = json.loads((ROOT/'artifacts/atgb/atgb_03c/S08/result.json').read_text(encoding='utf-8'))
first = historical['turns'][0]
setup = {'source':'frozen frontier-gate-v1 plus exact original first delivered log',
         'prior_player':first['player_input'], 'prior_gm':first['response_text']}
if trial != 'L4':
    oldstore = ROOT/'artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0'
    entry = json.loads((oldstore/'session_log.jsonl').read_text(encoding='utf-8').splitlines()[0])
    storage.SESSION_LOG_PATH.write_text(json.dumps(entry,ensure_ascii=False)+'\n', encoding='utf-8')
    session = storage.load_session()
    from game.conversational_continuity import record_delivered_exchange
    record_delivered_exchange(session, player_text=first['player_input'], delivered_text=first['response_text'],
        scene_id='frontier_gate', turn=0, ownership='gm', adoption=None, social=None)
    session.setdefault('conversational_context', {})['last_gm_exchange'] = {
        'category':'ANSWER','owner':'GM','purpose':'QUESTION','subject':first['player_input'],
        'response':first['response_text'][:1200], 'refusal_reason':None,'scene_id':'frontier_gate'}
    storage.save_session(session)
    player = 'No, I was asking about the people, not the weather.' if trial=='L3' else 'I meant the people, not the weather.'
else:
    # Exact existing frozen authorization control; no invented movement state.
    import pytest
    from tests.test_pr_ef_gm_authority import seed_scene
    from tests.test_pr_ef_r4_authorization import _prepare, CASE_BY_ID
    mp = pytest.MonkeyPatch()
    seed_scene(dest/'fixture', mp)
    case = CASE_BY_ID['correction_pending']
    _prepare(case)
    player = case['player']
    setup = {'source':'tests/test_pr_ef_r4_authorization.py::_prepare and seed_scene',
             'fixture':case, 'limitation':'Existing ASK revision control used; no frozen movement/attack world fixture selected.'}
def clean(x):
    if dataclasses.is_dataclass(x): return clean(dataclasses.asdict(x))
    if isinstance(x, enum.Enum): return x.value
    if isinstance(x, dict): return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [clean(v) for v in x]
    if isinstance(x,(str,int,float,bool)) or x is None: return x
    return str(type(x).__name__)
def write(name, value):
    (dest/name).write_text(json.dumps(clean(value), indent=2, ensure_ascii=False)+'\n',encoding='utf-8')
def state():
    return copy.deepcopy({'session':storage.load_session(),'world':storage.load_world(),
        'character':storage.load_character(),'combat':storage.load_combat(),
        'scene':storage.load_active_scene(),'log':storage.load_log()})
write('before.json', state())
write('setup.json', {**setup,'player_input':player,'data_dir':str(storage.DATA_DIR)})
events=[]
selected = {'public_conversation_evidence','request_interpretation','interpret_production_turn',
    'decision_from_interpretation_record','_communication_decision','_pending_revision_decision',
    'is_migrated_information_turn','authorize_information_turn','_nonmutating_conversational_decision_response'}
def observer(frame,event,arg):
    name=frame.f_code.co_name
    if event=='return' and name in selected and str(ROOT/'game') in frame.f_code.co_filename:
        local=frame.f_locals
        keys={'request_interpretation':['messages','estimated_input'],
              'interpret_production_turn':['player_text','evidence','parsed','communication','adapted','record'],
              '_pending_revision_decision':['text','purpose','components','pending','executed'],
              '_communication_decision':['record','text','answer','owner','purpose'],
              'decision_from_interpretation_record':['record','player_text']}.get(name,[])
        events.append({'function':name,'file':str(Path(frame.f_code.co_filename).relative_to(ROOT)),
            'line':frame.f_code.co_firstlineno,'inputs_or_locals':clean({k:local[k] for k in keys if k in local}),
            'return':clean(arg)})
    return observer
started=time.perf_counter()
sys.setprofile(observer)
try:
    result=chat(ChatRequest(text=player,ui_mode='player'))
except Exception as exc:
    result={'ok':False,'error_type':type(exc).__name__}
finally:
    sys.setprofile(None)
    latency=round((time.perf_counter()-started)*1000,3)
    write('trace.json', events)
    write('after.json',state())
    write('response.json',result)
    write('accounting.json',{'snapshot':snapshot(),'end_to_end_ms':latency,'sdk_clients':sdk_clients,
        'max_application_admissions':2,'sdk_transport_retries':0,'cost':None,'cost_reason':'No configured price table; measured usage only.'})
print(json.dumps({'trial':trial,'ok':result.get('ok'),'text':result.get('gm_output',{}).get('player_facing_text'),
    'admissions':snapshot()['requests'],'latency_ms':latency},ensure_ascii=False))
