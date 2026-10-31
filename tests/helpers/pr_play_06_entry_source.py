"""Pytest plugin for the five known failures against saved entry GM source."""
from pathlib import Path


def pytest_configure(config):
    import game.gm as gm
    path=Path('artifacts/pr_play_06/entry/gm.py')
    exec(compile(path.read_text(encoding='utf-8-sig'),str(path),'exec'),gm.__dict__)
