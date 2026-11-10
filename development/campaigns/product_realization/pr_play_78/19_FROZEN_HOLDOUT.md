# Frozen holdout

This is a developer-authored holdout. It is not external validation.

- File: `tests/fixtures/pr_play_78_holdout.json`
- SHA256: `5a9d2d003ba91a311edff0006a99e91a7c5d9b1b9e8ff5f5d1be4d68339c46a0`
- 120 cases. Groups: mixed 20, continuity 40, narration 15, dialogue 15, concurrency 10, readonly 10, isolation 5, publication 5.
- The file asserts at least 40 multi-turn cases and at least 20 save cases. Continuity supplies those 40, and 20 of them save.
- Narration, dialogue, readonly, and publication cases repeat a small set of templates. That limits how much the holdout can say about open play.

The fixture was frozen before the later scene-scope and speech-regex repairs and was not edited afterward.

First execution: 119/120. H098 failed because the harness reused the request key `same` and the lane `holdout-dup`, so the completed-id cache made the next duplicate case return immediately. That was a harness collision, not a product change. The fixture was not retuned.

After the harness keyed locks and request ids by case id, the frozen file passed. The closure pytest run, which includes `test_frozen_holdout_once` and `test_holdout_file_is_frozen`, passed with `failed == []`.

Results file: `artifacts/pr_play_78/holdout_results.json`. Pytest itself cannot write that file; the isolation hook refuses `artifacts/` writes from tests. The file was written by the closure script.
