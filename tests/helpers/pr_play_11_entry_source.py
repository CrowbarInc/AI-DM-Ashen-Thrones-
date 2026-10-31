"""Reproduce expanded-lane failures against hash-preserved dirty entry GM source."""
from pathlib import Path


def pytest_configure(config):
    import game.gm as gm
    path = Path('artifacts/pr_play_11/entry_sources/game/gm.py')
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), gm.__dict__)
