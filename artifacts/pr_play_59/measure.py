import sys,time,statistics,tracemalloc,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from artifacts.pr_play_59.evaluate import write,read,hashes
from tests.pr_play_59_development import cases
from game.consequential_narration_validation import SemanticAuthority,validate_consequential_narration
from game.persistent_consequence_claims import validate_persistent
from game.integrated_investigation_narration import validate_integrated
from tests.test_pr_play_57_integrated_narration import hook
from game.integrated_investigation_narration import outcome_contract
samples={k:[] for k in ['persistent','consequence_pipeline','combined_integrated']}
contract,request=outcome_contract(hook())
route='The missing patrol was last seen taking the northwest mud track past the crates.'
controls=[(c['text'],SemanticAuthority(**{k:tuple(v) for k,v in c['authority'].items()})) for c in cases()]
for _ in range(10):
 for text,a in controls:
  for name,fn in [('persistent',lambda:validate_persistent(text,a)),('consequence_pipeline',lambda:validate_consequential_narration(text,a)),('combined_integrated',lambda:validate_integrated(contract,request,route+' '+text))]:
   start=time.perf_counter();fn();samples[name].append((time.perf_counter()-start)*1000)
tracemalloc.start();base=tracemalloc.get_traced_memory()[0]
for text,a in controls:validate_persistent(text,a)
current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
write('performance.json',{'latency':{k:{'calls':len(v),'average_ms':statistics.fmean(v),'maximum_ms':max(v)} for k,v in samples.items()},'persistent_transient_peak_bytes':peak-base,'persistent_retained_bytes':current-base,'memory_scope':'tracemalloc Python allocations during one development pass; excludes interpreter, imports and RSS','provider_requests':0,'provider_tokens':0,'method':'10 development corpus repetitions; combined timing adds complete route fact to exercise unchanged integrated validator; holdout never repeated.'})
write('latency_samples.json',samples)
assert hashes()==read('implementation_frozen.json')
print(json.dumps(read('performance.json'),indent=2))
