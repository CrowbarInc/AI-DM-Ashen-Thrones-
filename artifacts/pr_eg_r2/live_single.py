"""Single synthetic prompt only, explicit OpenAI endpoint; no campaign state."""
import json, os, time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
load_dotenv(ROOT/'.env')
messages=json.loads((HERE/'prompts/A1_compact_1.json').read_text(encoding='utf-8'))
# The exact retained prompt contains only the user's fictional north-road example.
assert len(messages)==2 and 'The street beyond the gate is called the north road.' in messages[1]['content']
start=time.perf_counter()
row={'messages':messages,'model':'gpt-4.1-mini','endpoint':'https://api.openai.com/v1','max_output_tokens':500,'sdk_max_retries':0}
try:
 client=OpenAI(api_key=os.environ['OPENAI_API_KEY'],base_url='https://api.openai.com/v1',timeout=30,max_retries=0)
 response=client.responses.create(model=row['model'],input=messages,max_output_tokens=500)
 row.update(raw_output=response.output_text,usage=response.usage.model_dump(),model_returned=response.model)
except Exception as exc:
 row.update(error_type=type(exc).__name__,error=str(exc)[:300])
row['latency_ms']=(time.perf_counter()-start)*1000
(HERE/'single_provider_access.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in row.items() if k!='messages'}))
