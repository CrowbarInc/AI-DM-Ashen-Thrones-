"""Final bounded reruns after copied-fixture/environment issues were identified."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
from dotenv import dotenv_values
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'artifacts/pr_play_12'; DST=OUT/'sandbox'
for folder in ['artifacts/pr_bv_turn_operation_projection_micro_live/evidence','artifacts/pr_bt_selective_epistemic_restoration_final_micro_live/evidence','artifacts/validation_evidence/reactive_adversarial','development/reports']:
    shutil.copytree(ROOT/folder,DST/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.zip'))
lanes=json.loads((ROOT/'artifacts/pr_play_11/regression_runs.json').read_text())
existing=dotenv_values(ROOT/'.env')
projected={k:str(os.environ.get(k) or existing[k]) for k in ['MODEL_NAME','DEFAULT_MODEL_NAME','HIGH_PRECISION_MODEL_NAME','RETRY_ESCALATION_MODEL_NAME'] if os.environ.get(k) or existing.get(k)}
(OUT/'test_environment_provenance.json').write_text(json.dumps(dict(model_configuration='Existing repository values projected without modification into synthetic test subprocesses; .env not copied',projected_names=list(projected),credential='offline-placeholder only',production_configuration_modified=False),indent=2))
results={}
requested=sys.argv[1:]
suffix='short' if requested else 'final'
for name in (requested or ['provider','diagnostics','structured','world','export_atgb','claim_authority']):
    row=lanes[name]; files=[x for x in row['command'] if x.startswith('tests/')]
    temp=(ROOT/'development/tmp'/('p12_'+name[:5])) if requested else OUT/('tmp_final_'+name)
    cmd=[sys.executable,'-m','pytest',*files,'-q','--tb=short','--basetemp='+str(temp),'--junitxml='+str(OUT/(name+'_'+suffix+'.xml'))]
    env={**os.environ,**projected,'OPENAI_API_KEY':'offline-placeholder','ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT':'1','ASHEN_DISABLE_PROVIDER_RETRIES':'1','ASHEN_PLAYTEST_DISABLE_SDK_RETRIES':'1'}
    started=time.monotonic()
    with (OUT/(name+'_'+suffix+'.txt')).open('wb') as log:
        try:
            p=subprocess.run(cmd,cwd=DST,stdout=log,stderr=subprocess.STDOUT,timeout=100,env=env)
            results[name]=dict(command=cmd,exit=p.returncode,seconds=round(time.monotonic()-started,2))
        except subprocess.TimeoutExpired: results[name]=dict(command=cmd,timeout=True,seconds=100)
    (OUT/('regression_'+suffix+'_runs.json')).write_text(json.dumps(results,indent=2)); print(name,results[name].get('exit','timeout'),flush=True)
