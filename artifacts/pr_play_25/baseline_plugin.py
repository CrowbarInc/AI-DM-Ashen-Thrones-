"""Load the exact pre-PR-PLAY-25 modules before test collection; disk is unchanged."""
import importlib.util
from pathlib import Path
import sys


def pytest_configure(config):
    import game
    for name in ('dialogue_authority', 'expressive_dialogue'):
        full = 'game.' + name
        spec = importlib.util.spec_from_file_location(full, Path(__file__).with_name(name + '.before.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[full] = module
        setattr(game, name, module)
        spec.loader.exec_module(module)
