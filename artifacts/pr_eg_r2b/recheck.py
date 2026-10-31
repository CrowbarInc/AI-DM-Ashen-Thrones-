"""Fixed diagnostic repeat and single-candidate latency; no prompt or labels tuned."""
import json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
from experiment import call,contract,read,write
from game.config import get_openai_api_key
from game.model_routing import resolve_model_route
from openai import OpenAI
plan=dict(ids=['paraphrase01','commitment04'],purpose='One single-case safe false-rejection and one critical unsafe-acceptance repeat; identical locked prompt; stop on repeated critical acceptance')
write('diagnostic_plan.json',plan)
client=OpenAI(api_key=get_openai_api_key(),base_url='https://api.openai.com/v1',timeout=45,max_retries=0);model=resolve_model_route(purpose='strict_social').selected_model
out=[]
for ident in plan['ids']:
 c=next(x for x in read('corpus.json') if x['id']==ident)
 row=call(client,model,'validation',[dict(id=c['id'],contract=contract(c),candidate=c['candidate'])],'single_repeat_'+ident);out.append(row)
 if row.get('error'):write('stop.json',dict(reason='Provider unavailable during diagnostic',trial=row['trial']));break
 if ident=='commitment04' and row['parsed'][0]['decision']=='ACCEPT':
  write('stop.json',dict(reason='Repeated critical unauthorized acceptance of captain-permission rule; no further provider experiments',trial=row['trial'],first_trial='development_10',scope='All planned 112 initial cases already completed before diagnostic repeat'));break
write('diagnostic_results.json',out)
