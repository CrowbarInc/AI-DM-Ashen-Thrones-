import pathlib,sys,importlib,pytest
p=pathlib.Path('artifacts/pr_play_28');sys.path.insert(0,str(pathlib.Path.cwd()))
mode=sys.argv[1]
if mode=='before':
 for name in ['game.social','tools.playtest.overlays','tools.playtest.gameplay']:
  module=importlib.import_module(name);source=p/'source_before'/pathlib.Path(*name.split('.')).with_suffix('.py');exec(compile(source.read_text(encoding='utf-8'),str(source),'exec'),module.__dict__)
raise SystemExit(pytest.main(['tests/test_by3_strict_social_semantic_mutation.py::test_by3_generate_repo_artifacts','tests/test_turn_pipeline_shared.py::test_chat_active_target_direct_command_routes_to_social_exchange','-q','--tb=short','--basetemp=development/tmp/pr_play_28_env_'+mode,'--junitxml='+str(p/('environment_'+mode+'.xml'))]))
