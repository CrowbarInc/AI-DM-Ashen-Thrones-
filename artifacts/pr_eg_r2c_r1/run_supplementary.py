from pathlib import Path
import subprocess,sys
h=Path('artifacts/pr_eg_r2c_r1');files=['tests/test_social_question_relevance_answer_selection.py','tests/test_social_exchange_emission.py','tests/test_strict_social_emergency_fallback_dialogue.py','tests/test_referential_clarity_strict_social_local_repair.py','tests/test_by3_strict_social_semantic_mutation.py']
for stage in ['baseline','final']:
 args=[sys.executable,'-u']
 if stage=='baseline':args+=['-c','import sys;sys.path.insert(0,sys.argv.pop(1));import game;import pytest;raise SystemExit(pytest.main(sys.argv[1:]))',str((h/'baseline_overlay').resolve())]
 else:args+=['-m','pytest']
 args += [*files,'-q','--tb=short','--junitxml='+str(h/('supplementary_'+stage+'.xml')),'--basetemp='+str(h/('supplementary_'+stage+'_tmp'))]
 p=subprocess.run(args,stdout=(h/('supplementary_'+stage+'_console.txt')).open('w'),stderr=subprocess.STDOUT,timeout=180);print(stage,p.returncode,flush=True)
