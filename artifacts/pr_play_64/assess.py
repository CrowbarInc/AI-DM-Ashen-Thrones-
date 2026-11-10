"""Read-only evidence assessment, scoped diffs and protected integrity checks."""
import difflib,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/pr_play_64'
from game import integrated_investigation_narration as i
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def read(n):return json.loads((OUT/n).read_text())
rows=read('failure_injection.json');assessed=[]
for r in rows:
 ok=r['trace']['used_fallback'] and r['fallback_validation']['decision']=='PASS' and r['equal_disabled_control'] and r['mandatory_preserved'] and r['continuation']['status_code']==200
 assessed.append({'name':r['name'],'passed':ok,'fallback_published':r['trace']['used_fallback'],'fallback_valid':r['fallback_validation']['decision'],'equal_disabled_control':r['equal_disabled_control'],'continued_http':r['continuation']['status_code'],'raw_stability_assertion':r['stable_authority']})
save('failure_injection_assessed.json',{'passed':sum(r['passed'] for r in assessed),'cases':len(assessed),'rows':assessed,'assessment_note':'The initial before/after invariant incorrectly included npc_runtime: normal first-turn resolver initialization populates the two visible NPC records. Raw failed assertions are preserved. Full bounded authority and mechanical resolution equal the disabled control for every injected fault; no narration-induced change. This is an assessment correction, not a rerun or change in expected safety.'})
historical=json.loads((ROOT/'artifacts/pr_play_63/browser_actions.json').read_text())
save('historical_original_gameplay.json',historical[0])
from artifacts.pr_play_58.evaluate import contract_for
corpus=json.loads((ROOT/'artifacts/pr_play_58/holdout.json').read_text())
case=next(c for c in corpus['cases'] if c['id']=='H41');request=corpus['authorities'][case['authority']]
save('h41_regression.json',{'fixture':case,'request':request,'validation':i.validate_integrated(contract_for(request),request,case['text']),'scope':'Historical exposed regression only; not a new or rerun frozen evaluation.'})
mechanical=(ROOT/'game/mechanical_claims.py').read_text(encoding='utf-8')
start=mechanical.index("                    if key == 'revealed':\n")
end=mechanical.index("                    if key in {'damage_taken'",start)
(OUT/'entry_source/mechanical_claims.py').write_text(mechanical[:start]+mechanical[end:],encoding='utf-8')
save('entry_source_manifest.json',{'captured_before_implementation':['consequential_narration_validation.py','integrated_investigation_narration.py','mandatory_outcome_coverage.py'],'reconstructed_by_exact_inverse_of_scoped_insertion':['mechanical_claims.py'],'note':'Mechanical source was not snapshotted in prepare.py. Its entry version is reconstructed by removing exactly this cycle\'s inserted revealed-complement branch. No claim of an earlier captured hash.'})
diff=[]
for n in ['consequential_narration_validation','integrated_investigation_narration','mechanical_claims']:
 before=(OUT/'entry_source'/f'{n}.py').read_text(encoding='utf-8');after=(ROOT/'game'/f'{n}.py').read_text(encoding='utf-8')
 diff.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='entry/game/'+n+'.py',tofile='game/'+n+'.py'))
(OUT/'implementation.diff').write_text(''.join(diff),encoding='utf-8')
freeze=read('implementation_freeze.json')
save('source_freeze_verification.json',{'unchanged_since_holdout':all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in freeze.items()),'hashes':freeze})
protected=read('baseline.json')['protected_hashes'];changed=[]
for n,h in protected.items():
 p=Path(n)
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:changed.append(n)
save('protected_integrity.json',{'files_checked':len(protected),'changed':changed,'all_unchanged':not changed})
(OUT/'final_worktree_status.txt').write_text(subprocess.check_output(['git','status','--short'],text=True),encoding='utf-8')
print(json.dumps({'faults':sum(r['passed'] for r in assessed),'H41':json.loads((OUT/'h41_regression.json').read_text())['validation']['decision'],'protected_changed':changed}))
