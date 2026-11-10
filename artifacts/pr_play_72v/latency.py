import os
os.environ['PR72V_STORAGE']='latency_data';os.environ['PR72V_NETWORK']='latency_network.jsonl'
from runtime import *
from artifacts.pr_play_67.http_harness import server
import statistics
instrument(api,'normalized_action_from_interpretation','grounding_validation_mapping_ms')
instrument(api,'append_log','log_append_ms')
rows=[]
with server() as request:
 for p in ['/api/new_campaign','/api/start_campaign']:
  assert request(p,{})['status']==200
 for label,text in [('initial','I examine the notice board.'),('repeat','Read the notice board again.'),('information','What have I learned?'),('clarification','Ask them about it.'),('unsupported','Order the guards to search immediately.')]:
  before=snapshot();r=request('/api/chat',{'text':text});after=snapshot();assert r['status']==200
  capture=json.loads((OUT/'latency_network.jsonl').read_text().splitlines()[-1]);rows.append(dict(label=label,text=text,http_ms=r['http_ms'],stages=capture['stages'],response=r['body'],before=before,after=after,resolution=storage.load_log()[-1].get('resolution')))
(OUT/'latency_samples.json').write_text(json.dumps(rows,indent=2));print('Five normal HTTP timing samples completed; provider requests/tokens/retries 0.')
