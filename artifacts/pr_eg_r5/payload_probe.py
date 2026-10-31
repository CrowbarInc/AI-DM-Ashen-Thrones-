"""Capture actual interpretation prompts without transmitting a request."""
import os,sys,json,copy,statistics
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
os.environ.update(ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1',ASHEN_DISABLE_LIVE_INTERPRETATION='1',ASHEN_DISABLE_EXPRESSION_GENERATION='1',ASHEN_DATA_DIR=str(OUT/'payload_import_state'))
from game import live_chat_interpretation as live
rows=json.loads((ROOT/'artifacts/pr_eg_r4_r1/live_turns.json').read_text(encoding='utf-8'))
scene=json.loads((ROOT/'artifacts/pr_eg_r4_r1/live_state/primary/data/scenes/waystation_courtyard.json').read_text(encoding='utf-8'))
captures=[]
for player in ['I meant the orchard shift coordinator, not the sundial.','What did she mean by that?','Your preference is morning; why is that your choice?']:
    row=rows[5]; before=copy.deepcopy(row['before']); logs=[dict(player_input=x['player'],player_facing_text=x['text']) for x in rows[:5]]
    def capture(messages,**kwargs):
        captures.append(dict(utterance=player,messages=copy.deepcopy(messages),schema=live.production_interpretation_schema(),estimate=kwargs,evidence_class='C: prompt-construction probe, provider stubbed, no provider judgment'))
        return dict(ok=False,sent=False,text='',error='R5_CAPTURE_ONLY')
    with patch.object(live,'production_live_interpretation_enabled',return_value=True),patch.object(live,'request_interpretation',side_effect=capture):
        result=live.interpret_production_turn(player_text=player,mode='AUTO',scene=scene,world=before['world'],log=logs,session=before['session'])
        captures[-1]['outcome']=result
(OUT/'payload_captures.json').write_text(json.dumps(dict(provider_calls=0,input_tokens=0,output_tokens=0,captures=captures),indent=2),encoding='utf-8')
usage={}
for era,path in [('R4','artifacts/pr_eg_r4/engine_usage.jsonl'),('R4-R1','artifacts/pr_eg_r4_r1/live_usage_final.jsonl')]:
    records=[json.loads(l) for l in (ROOT/path).read_text(encoding='utf-8').splitlines() if l.strip()]
    groups={}
    for purpose in sorted({r['purpose'] for r in records if r.get('sent')}):
        rs=[r for r in records if r.get('sent') and r['purpose']==purpose];values=[r['input_tokens'] for r in rs]
        groups[purpose]=dict(calls=len(rs),input_tokens=sum(values),output_tokens=sum(r['output_tokens'] for r in rs),min_input=min(values),median_input=statistics.median(values),max_input=max(values))
    usage[era]=groups
(OUT/'provider_usage_analysis.json').write_text(json.dumps(usage,indent=2),encoding='utf-8')
print(json.dumps(dict(captures=len(captures),estimated=[c['estimate'] for c in captures],historical_usage=usage)))
