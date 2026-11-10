import pathlib,subprocess,sys,os
p=pathlib.Path('artifacts/pr_play_28')
# Unbuffered output makes progress visible in retained logs.
files=__import__('json').loads((p/'test_files.json').read_text())
with (p/'baseline.txt').open('w') as log:
 r=subprocess.run([sys.executable,'-u','-m','pytest',*files,'-q','--tb=short','--basetemp=development/tmp/pr_play_28_baseline_complete','--junitxml='+str(p/'baseline.xml')],stdout=log,stderr=subprocess.STDOUT)
print(r.returncode)
