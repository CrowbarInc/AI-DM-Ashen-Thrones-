"""Test-only observers around the unchanged application worker and provider transport."""
import json
import os
import runpy
import sys
import time
from pathlib import Path

run = Path(sys.argv[1])
folder = run/'diagnostics'
secrets = [v for k, v in os.environ.items() if len(v) > 6 and any(s in k.lower() for s in ('key', 'secret', 'password', 'credential', 'token'))]
def save(name, value):
    raw = json.dumps(value, indent=2, default=str)
    for secret in secrets:
        raw = raw.replace(secret, '[REDACTED]')
    (folder/name).write_text(raw+'\n', encoding='utf-8')

from game import provider_budget as budget
from game import opening_presentation_renderer as renderer
original_dispatch = budget.RequestAttempt.dispatch
count = 0
failed = False
def dispatch(self, invoke, **kwargs):
    global count, failed
    assert not failed, 'Earlier provider failure; no further dispatch permitted'
    assert count < 10 and kwargs['model'] == 'gpt-4.1-mini'
    assert budget.sdk_retry_options() == {'max_retries': 0} and budget.provider_retries_disabled()
    assert int(os.environ['ASHEN_PROVIDER_REQUEST_LIMIT']) <= 10
    count += 1
    seq = count
    save(f'request_{seq:02}.json', {'sequence': seq, 'attempt_id': self.attempt_id,
         'purpose': self.purpose, 'owner': self.owner, 'request': kwargs,
         'label': 'INTERNAL DIAGNOSTIC EVIDENCE'})
    def observed(**actual):
        global failed
        started = time.perf_counter()
        try:
            response = invoke(**actual)
        except BaseException as exc:
            failed = True
            save(f'response_{seq:02}.json', {'error_type': type(exc).__name__,
                 'http_status': getattr(exc, 'status_code', None),
                 'body': getattr(exc, 'body', None), 'latency_seconds': time.perf_counter()-started})
            raise
        save(f'response_{seq:02}.json', {'latency_seconds': time.perf_counter()-started,
             'response': response.model_dump(mode='json'), 'sdk_request_id': getattr(response, '_request_id', None)})
        if getattr(response, 'status', None) != 'completed':
            failed = True
        return response
    return original_dispatch(self, observed, **kwargs)
budget.RequestAttempt.dispatch = dispatch
for name in ('prepare_opening_renderer', 'realize_opening_provider_text'):
    original = getattr(renderer, name)
    def wrapper(*args, _name=name, _original=original, **kwargs):
        result = _original(*args, **kwargs)
        save(_name+'.json', result)
        return result
    setattr(renderer, name, wrapper)

# Record native diagnostics in full, including parser/validator decisions.
original_diagnostic = budget.record_generation_diagnostic
def diagnostic(fields, attempt=None):
    with (folder/'native_diagnostics.jsonl').open('a', encoding='utf-8') as stream:
        raw = json.dumps(fields, default=str)
        for secret in secrets:
            raw = raw.replace(secret, '[REDACTED]')
        stream.write(raw+'\n')
    return original_diagnostic(fields, attempt)
budget.record_generation_diagnostic = diagnostic
# Observation wrappers preserve arguments, results, mutations and exception behavior.
import functools
from game import social, dialogue_authority, local_interaction, player_interpretation_bridge, public_fact_dialogue, expressive_dialogue
trace_count=0
def observe(module,name):
    original=getattr(module,name)
    @functools.wraps(original)
    def wrapper(*args,**kwargs):
        global trace_count
        trace_count+=1
        seq=trace_count
        save(f'trace_{seq:03}_{name}_input.json',{'function':module.__name__+'.'+name,'args':args,'kwargs':kwargs})
        result=original(*args,**kwargs)
        save(f'trace_{seq:03}_{name}_output.json',{'function':module.__name__+'.'+name,'result':result})
        return result
    setattr(module,name,wrapper)
for module,names in (
    (public_fact_dialogue,('select_public_offering',)),
    (expressive_dialogue,('validate_expression','request_expression')),
    (social,('resolve_social_action','_next_topic_to_reveal','_bounded_social_reply_plan_for_missing_topic','select_best_social_answer_candidate','realize_authored_knowledge_answer')),
    (dialogue_authority,('build_dialogue_authority','select_host_speech','authorize_npc_disclosure')),
    (local_interaction,('normalize_local_approach',)),
    (player_interpretation_bridge,('normalized_action_from_interpretation',))):
    for name in names: observe(module,name)
from game import exploration, route_authority, conversational_orchestration, scene_graph, clues
for module,names in ((exploration,('resolve_exploration_action','process_investigation_discovery')), (route_authority,('route_status',)), (scene_graph,('is_transition_valid',)), (clues,('add_clue_to_knowledge',)), (conversational_orchestration,('deterministic_conversational_decision',))):
    for name in names: observe(module,name)
runpy.run_module('tools.playtest.worker', run_name='__main__')
