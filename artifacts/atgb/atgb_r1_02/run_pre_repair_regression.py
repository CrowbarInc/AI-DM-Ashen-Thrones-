"""Load saved pre-repair source in memory; never replace a production file."""
import importlib.util
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import game
spec = importlib.util.spec_from_file_location('game.conversational_orchestration', Path(__file__).with_name('orchestration_before.py'))
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
game.conversational_orchestration = module
import pytest
raise SystemExit(pytest.main(sys.argv[1:]))
