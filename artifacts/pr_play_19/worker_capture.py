"""PR-PLAY-19 observation wrapper; production worker and SDK remain in use."""
import json
import os
from pathlib import Path
import runpy
import sys
import time
from datetime import datetime, timezone

run = Path(sys.argv[1])
folder = run / 'diagnostics'
secrets = [v for k, v in os.environ.items() if v and len(v) > 6 and
           any(s in k.lower() for s in ('key', 'secret', 'password', 'credential', 'token'))]

def save(name, value):
    encoded = json.dumps(value, indent=2, ensure_ascii=True)
    for secret in secrets:
        encoded = encoded.replace(secret, '[REDACTED]')
    (folder/name).write_text(encoded+'\n', encoding='utf-8')

from game import provider_budget as budget
from game import opening_presentation_renderer as renderer
original_dispatch = budget.RequestAttempt.dispatch
original_prepare = renderer.prepare_opening_renderer
original_realize = renderer.realize_opening_provider_text

def prepare(messages):
    result = original_prepare(messages)
    save('prepared_public_catalog.json', result)
    return result

def realize(raw, catalog):
    result = original_realize(raw, catalog)
    save('renderer_result.json', result)
    return result

renderer.prepare_opening_renderer = prepare
renderer.realize_opening_provider_text = realize
count = 0

def dispatch(self, invoke, **kwargs):
    global count
    count += 1
    save('actual_assembled_request.json', {'capture_boundary': 'RequestAttempt.dispatch immediately before original dispatch',
         'timestamp': datetime.now(timezone.utc).isoformat(), 'request_sequence': count,
         'admission_sequence': self.sequence, 'purpose': self.purpose, 'owner': self.owner,
         'attempt_id': self.attempt_id, 'request': kwargs})
    fmt = kwargs.get('text', {}).get('format', {})
    schema = fmt.get('schema', {})
    save('exact_schema.json', schema)
    # Fail closed before SDK dispatch. These are scope/contract guards, not repairs.
    assert count == 1 and kwargs['model'] == 'gpt-4.1-mini'
    assert os.environ.get('ASHEN_OPENING_RENDERER') == '1'
    assert int(os.environ['ASHEN_PROVIDER_REQUEST_LIMIT']) == 1
    assert budget.sdk_retry_options() == {'max_retries': 0} and budget.provider_retries_disabled()
    assert fmt['type'] == 'json_schema' and fmt['name'] == 'opening_presentation' and fmt['strict'] is True
    assert schema['required'] == ['selected_entries'] and schema['additionalProperties'] is False
    assert set(schema['properties']) == {'selected_entries'}
    assert [m['role'] for m in kwargs['input']] == ['system', 'user']
    assert kwargs['input'][0]['content'].startswith('OPENING PRESENTATION PLAN:')
    user = json.loads(kwargs['input'][1]['content'])
    assert set(user) == {'response_type_contract', 'opening_public_choices'}
    for choice in schema['properties']['selected_entries']['items']['anyOf']:
        assert choice['additionalProperties'] is False
        assert choice['required'] == ['catalog_id', 'variant_id']
    save('predispatch_contract_check.json', {'passed': True, 'unchanged_kwargs_forwarded': True,
         'model': kwargs['model'], 'purpose': self.purpose, 'sequence': count})
    def observed_invoke(**actual):
        started = time.perf_counter()
        try:
            response = invoke(**actual)
        except Exception as exc:
            body = getattr(exc, 'body', None)
            save('provider_error.json', {'type': type(exc).__name__, 'http_status': getattr(exc, 'status_code', None),
                 'body': body, 'latency_seconds': time.perf_counter()-started})
            raise
        save('provider_response.json', {'latency_seconds': time.perf_counter()-started,
             'response': response.model_dump(mode='json'), 'sdk_request_id': getattr(response, '_request_id', None)})
        return response
    return original_dispatch(self, observed_invoke, **kwargs)

budget.RequestAttempt.dispatch = dispatch

# Observe real SDK HTTP status and serialized body without headers or credentials.
import httpx
original_send = httpx.Client.send
def send(self, request, *args, **kwargs):
    if request.url.path.endswith('/responses'):
        save('sdk_serialized_request.json', json.loads(request.content))
        response = original_send(self, request, *args, **kwargs)
        save('provider_http.json', {'status_code': response.status_code,
             'request_id': response.headers.get('x-request-id'), 'method': request.method,
             'path': request.url.path, 'transport': 'real SDK HTTP'})
        return response
    return original_send(self, request, *args, **kwargs)
httpx.Client.send = send
runpy.run_module('tools.playtest.worker', run_name='__main__')
