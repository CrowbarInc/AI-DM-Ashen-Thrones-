from pathlib import Path
import subprocess,json,sys
h=Path('artifacts/pr_eg_r2c_r2');files=json.loads((h/'regression_selection.json').read_text())+['tests/test_pr_eg_r2c_r2_reference_eligibility.py']
p=subprocess.run([sys.executable,'-m','pytest',*files,'--tb=short','--junitxml='+str(h/'final.xml'),'--basetemp='+str(h/'final_tmp')],stdout=(h/'final_console.txt').open('w'),stderr=subprocess.STDOUT)
print('final exit',p.returncode)
