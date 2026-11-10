# Development tests

`tests/test_pr_play_79c_publication.py` contains 82 tests. They passed in the implementation run, and they passed again in the rerun after the repeat-examination wording change. The rerun's failure list does not include any of those 82 tests.

Coverage includes host speech that survives a narration stub, uncertainty wording, hidden-route rejection, physical step-back outcomes, narration relevance, publication-contract skip, and provider-row accounting.

The tests use the isolated store and a patched expression function. They do not call the live provider.
