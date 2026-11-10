import pathlib,json,subprocess,sys
p=pathlib.Path('artifacts/pr_play_27')
files=json.loads((p/'test_files.json').read_text())
with (p/'existing.txt').open('w',encoding='utf-8') as log:
 r=subprocess.run([sys.executable,'-m','pytest',*files,'-q','--tb=short','--junitxml='+str(p/'existing.xml')],stdout=log,stderr=subprocess.STDOUT)
print(r.returncode)
