import pathlib,json,subprocess,sys
p=pathlib.Path('artifacts/pr_play_28'); files=json.loads(pathlib.Path('artifacts/pr_play_27/test_files.json').read_text()); (p/'test_files.json').write_text(json.dumps(files,indent=2))
for f in ['game/social.py','tools/playtest/overlays.py','tools/playtest/gameplay.py']:
 q=p/'source_before'/f;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(pathlib.Path(f).read_bytes())
with (p/'baseline.txt').open('w') as log:
 r=subprocess.run([sys.executable,'-m','pytest',*files,'-q','--tb=short','--basetemp=development/tmp/pr_play_28_baseline','--junitxml='+str(p/'baseline.xml')],stdout=log,stderr=subprocess.STDOUT)
print(r.returncode)
