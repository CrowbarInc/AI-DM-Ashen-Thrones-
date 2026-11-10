# Frozen Holdout

Manifest: `artifacts/pr_play_76/frozen_holdout.json`

- Cases: 100
- SHA-256: `23376bbe834138b4f5735d1917dcff4c55bdacca6c0d88d74c4b7b77b1410026`
- Multi-turn cases: 31
- Save/resume cases: 15
- Groups: 20 routine, 15 manipulation, 15 persistence, 10 mechanical, 10 ambiguity, 10 compound, 10 save, 5 isolation, 5 publication

The manifest was hashed before the run and the test asserts that hash. It was not edited after the run.

Result: 99 passed, 1 failed.

H93, isolation, input "I sit on the bench." after the bench's campaign was no longer active. Expected category E, "not established". Actual category F, "Which seat do you mean? Nothing has been attempted." The other campaign's bench was not named and was not mutated. The miss is that zero visible seats are clarified instead of declined. The original result is preserved in `artifacts/pr_play_76/holdout_results.json`. The code was not tuned against this case.
