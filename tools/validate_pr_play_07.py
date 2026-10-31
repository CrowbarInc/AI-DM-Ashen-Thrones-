"""Bounded offline regression; no live authority. Reuses established lane selection."""
from pathlib import Path
import subprocess,sys,json,time,os,concurrent.futures
from tools.validate_pr_play_06 import GROUPS
O=Path('artifacts/pr_play_07')
GROUPS['entry_accounting']=['test_provider_accounting_integrity.py::test_readiness_acceptance_is_not_live_execution']
def run(name):
 Path('development/tmp/pr_play_07').mkdir(parents=True,exist_ok=True)
 group=name.removesuffix('_direct').removesuffix('_final')
 paths=GROUPS[group] if group!='focused' else ['test_pr_play_07_semantic_acceptance','test_pr_play_04_opening_integrity','test_pr_play_05_diagnostics','test_pr_play_06_opening_budget','test_frontend_ui_mode_hardening_objective15']
 if name=='ordinary_direct': paths=['test_gm_retry','test_social_interaction_authority','test_pr_ef_r2_social_authority']
 if name=='opening_direct': paths=['test_scene_canon_hygiene']
 command=[sys.executable,'-m','pytest',*['tests/'+p+('' if '::' in p else '.py') for p in paths],'-q','--tb=short','--basetemp=development/tmp/pr_play_07/'+name,'--junitxml='+str(O/(name+'.xml'))]
 if name in {'focused_direct','focused_final'}:command+=['-k','not invalid_placeholder_over_http']
 if name=='structured_direct':command+=['-k','not raw_chat_stub']
 if name=='ordinary_direct':command+=['-k','not original_captured_failures and not possessive_body_part']
 if name in {'entry_failures','entry_accounting'}:command+=['-p','tests.helpers.pr_play_07_entry_source']
 env=dict(os.environ,PR_PLAY_DIAGNOSTIC_OUT='artifacts/pr_play_07/diagnostics')
 start=time.monotonic()
 with (O/(name+'.txt')).open('w',encoding='utf-8') as log:
  try:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=90,env=env);code=r.returncode
  except subprocess.TimeoutExpired:code='timeout'
 (O/(name+'_run.json')).write_text(json.dumps({'command':command,'exit':code,'seconds':time.monotonic()-start},indent=2))
 print(name,code,flush=True)
if __name__=='__main__':
 # Existing tests have fixed historical evidence sinks. Preserve those artifacts.
 backup={p:p.read_bytes() for root in ['artifacts/pr_play_05','artifacts/pr_play_06'] for p in Path(root).rglob('*') if p.is_file()}
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,sys.argv[1:] or ['focused','provider','structured','ordinary','opening','world','export']))
 finally:
  for p,data in backup.items():
   if p.read_bytes()!=data:p.write_bytes(data)
