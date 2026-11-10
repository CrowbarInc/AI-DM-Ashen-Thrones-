# Integrity

Branch `feature/product-realization`. HEAD `d40f1ed198236c604085f1c842ead267a8104ce2` at entry and at close. No commit. No push. No reset, clean, stash, or revert. Unrelated dirty work remains.

Production files whose SHA-256 changed from the entry snapshot:

- `game/api.py`: entry `e3962e2ae0f4028c63844c42e830ffed562d0f1c4fcd2aa06997f33bb584c28b`; close `910bdeacb23973b6f1d284b83e8921bd97c096b47f834e605b5f41324fb276d3`.
- `game/marking_action.py`: new, close `59c1883a7c71be4e8f0ac5e9bdfca17ade27556e4ccaa39a63c4f4e46e0c2cc2`.

Unchanged from the entry snapshot: `game/conversational_orchestration.py`, `game/intent_parser.py`, `game/object_marking.py`, `game/object_instances.py`, `game/object_observation.py`, `game/storage.py`, `game/physical_adjudication.py`, `game/state_authority.py`, `game/immutable_valid_response.py`, `game/player_http_projection.py`, `game/narration_authorization.py`, `game/integrated_play.py`.

`git diff --stat` against HEAD also lists `game/conversational_orchestration.py` and `game/intent_parser.py` because those files were already dirty at entry. Their bytes match the entry hashes. That diff is not this cycle's edit set.

Validation files changed for the new outcome: `tests/test_grounded_marking_action.py` (new), `tests/test_pr_play_t06_persistent_manipulation.py`, `tests/test_pr_play_t04_local_action.py`, `tests/test_pr_play_post_npc_handoff.py`. The frozen T06 sentence and the frontier scene file were not modified.

Close hashes and the hash comparison are in `artifacts/pr_play_grounded_marking_action_integration/source_changes.json`.
