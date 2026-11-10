# 02 Baseline and scope

Repository commit: `d40f1ed198236c604085f1c842ead267a8104ce2`.

The worktree was already dirty, including `game/api.py`. This cycle did not revert that work. It added publication selection after the turn is saved, publication helpers on the existing quarantine module, and `tests/test_pr_play_61_player_facing.py`. `game/quarantined_investigation_narration.py` is untracked against HEAD because the prior narration work had not been committed. Canonical scene files and protected baselines were not rewritten.

PR-PLAY-60 left the investigation route restricted. This cycle stayed on that route: disclosure, repeated examination, and visible observation. It did not add inventory, combat, NPC death, or travel.

Known limits carried forward: H03 sealed-letter false rejection, H26 NPC-death false rejection, and the historical focused failures. Those were not retuned.
