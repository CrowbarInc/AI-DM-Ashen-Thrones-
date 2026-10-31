from pathlib import Path
import json,shutil,subprocess,sys
h=Path('artifacts/pr_eg_r2c_r2');h.mkdir(exist_ok=True)
for name in ['live_chat_interpretation.py','player_interpretation_bridge.py']:
 p=h/'before_sources/game'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(Path('game')/name,p)
(h/'working_tree_before.txt').write_text(subprocess.check_output(['git','status','--short'],text=True))
(h/'environment.json').write_text(json.dumps(dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),python=sys.version)))
files=json.loads(Path('artifacts/pr_eg_r2c/regression_selection.json').read_text())+['tests/test_pr_eg_r2c_speech_adoption.py','tests/test_social_question_relevance_answer_selection.py','tests/test_social_exchange_emission.py','tests/test_strict_social_emergency_fallback_dialogue.py','tests/test_referential_clarity_strict_social_local_repair.py','tests/test_by3_strict_social_semantic_mutation.py']
(h/'regression_selection.json').write_text(json.dumps(files,indent=2))
p=subprocess.run([sys.executable,'-m','pytest',*files,'--tb=short','--junitxml='+str(h/'baseline.xml'),'--basetemp='+str(h/'baseline_tmp')],stdout=(h/'baseline_console.txt').open('w'),stderr=subprocess.STDOUT)
print('baseline exit',p.returncode)
