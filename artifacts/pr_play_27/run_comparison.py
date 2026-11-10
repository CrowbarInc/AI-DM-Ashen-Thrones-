"""Exact on-disk pre/post comparison with isolated pytest roots; always restore repair."""
import json,pathlib,subprocess,sys,time
p=pathlib.Path('artifacts/pr_play_27')
files=json.loads((p/'test_files.json').read_text())
pairs=[('game/expressive_dialogue.py','expressive_dialogue.before.py'),('tools/playtest/gameplay.py','gameplay.before.py'),('tools/playtest/runner.py','runner.before.py')]
for source,before in pairs:
 target=p/'source_snapshot'/source;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(pathlib.Path(source).read_bytes())
while not (p/'existing.xml').exists():
 print('Waiting for preliminary regression run to release source files.',flush=True);time.sleep(20)
try:
 for source,before in pairs: pathlib.Path(source).write_bytes((p/before).read_bytes())
 print('Exact baseline started',flush=True)
 with (p/'baseline_exact.txt').open('w',encoding='utf8') as log:
  r=subprocess.run([sys.executable,'-m','pytest',*files,'-q','--tb=short','--basetemp=development/tmp/pr_play_27_baseline_exact','--junitxml='+str(p/'baseline_exact.xml')],stdout=log,stderr=subprocess.STDOUT)
 print('Exact baseline exit',r.returncode,flush=True)
finally:
 for source,before in pairs: pathlib.Path(source).write_bytes((p/'source_snapshot'/source).read_bytes())
print('Repaired regression started',flush=True)
with (p/'existing_final.txt').open('w',encoding='utf8') as log:
 r=subprocess.run([sys.executable,'-m','pytest',*files,'-q','--tb=short','--basetemp=development/tmp/pr_play_27_existing_final','--junitxml='+str(p/'existing_final.xml')],stdout=log,stderr=subprocess.STDOUT)
print('Repaired regression exit',r.returncode,flush=True)
