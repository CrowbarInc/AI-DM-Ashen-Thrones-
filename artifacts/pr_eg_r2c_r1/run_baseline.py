from pathlib import Path
import shutil,json,sys,subprocess
r=Path.cwd();h=r/'artifacts/pr_eg_r2c_r1';d=h/'baseline_overlay/game';shutil.copytree(r/'game',d,ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
for p in (h/'before_sources/game').glob('*.py'):shutil.copyfile(p,d/p.name)
for name in ['storage.py','config.py']:
 p=d/name;txt=p.read_text(encoding='utf-8');txt=txt.replace('Path(__file__).resolve().parent.parent',repr(str(r)));txt=txt.replace('BASE_DIR = '+repr(str(r)), 'BASE_DIR = Path('+repr(str(r))+')').replace('ROOT_DIR = '+repr(str(r)), 'ROOT_DIR = Path('+repr(str(r))+')');p.write_text(txt,encoding='utf-8')
files=json.loads((r/'artifacts/pr_eg_r2c/regression_selection.json').read_text())+['tests/test_pr_eg_r2c_speech_adoption.py']
cmd=[sys.executable,'-u','-c','import sys; sys.path.insert(0,sys.argv.pop(1)); import game; import pytest; raise SystemExit(pytest.main(sys.argv[1:]))',str(d.parent),*files,'-k','not test_topic_grounding_and_recall_matrix and not test_grounding_multiple_owned_topics_and_speakers and not test_exact_recall_keeps_long_delivered_statement_and_uncertainty and not test_watch_fact_does_not_answer_when_watch_is_absent and not test_historical_watch_reference_does_not_discover_competing_road and not test_provider_evidence_cannot_recall_fact_for_incompatible_question','-q','--tb=short','--junitxml='+str(h/'baseline.xml'),'--basetemp='+str(h/'baseline_verified_tmp')]
p=subprocess.run(cmd,stdout=(h/'baseline_console.txt').open('w'),stderr=subprocess.STDOUT,timeout=240);print(p.returncode)
