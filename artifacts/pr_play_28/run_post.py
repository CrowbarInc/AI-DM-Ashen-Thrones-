import pathlib,json,sys,subprocess
p=pathlib.Path('artifacts/pr_play_28')
focused=['tests/test_pr_play_28_topic_authority.py','tests/test_pr_play_28_baseline_reproduction.py','tests/test_pr_play_27_expression_recovery.py','tests/test_pr_play_25_public_fact_dialogue.py','tests/test_pr_play_10_overlays.py','tests/test_clue_idempotence.py','tests/test_social_lead_landing.py','tests/test_clue_knowledge.py','tests/test_social_question_relevance_answer_selection.py']
(p/'focused_files.json').write_text(json.dumps(focused,indent=2))
with (p/'focused.txt').open('w') as log:
 r=subprocess.run([sys.executable,'-m','pytest',*focused,'-q','--tb=short','--basetemp=development/tmp/pr_play_28_focused','--junitxml='+str(p/'focused.xml')],stdout=log,stderr=subprocess.STDOUT)
print('focused',r.returncode,flush=True)
files=json.loads((p/'test_files.json').read_text())
with (p/'existing.txt').open('w') as log:
 r=subprocess.run([sys.executable,'-m','pytest',*files,'-q','--tb=short','--basetemp=development/tmp/pr_play_28_existing','--junitxml='+str(p/'existing.xml')],stdout=log,stderr=subprocess.STDOUT)
print('existing',r.returncode)
