# AT-FG-05-EXEC-R2 offline functional validation

**Cleanup regression check PASS.** The corrected R1 isolated wrapper ran the same selected tests before and after R2 with provider calls disabled, independent owned workspaces, disabled plugin autoload, and a disabled pytest cache.

| Run | Cases | Passed | Known failures | Other errors |
|---|---:|---:|---:|---:|
| Before | 37 | 32 | 5 | 0 |
| After | 37 | 32 | 5 | 0 |

The scope covered AT-OPT-04 mixed-key policy and its redirected measurement output, review handoff integrity, the R1 historical-refusal invariant, and PR-PLAY-72V unsupported objectives. The retained current campaign review archive also matched its published SHA-256 and passed CRC verification. The pre- and post-run wrappers recorded 0 protected-path or Git changes.

| PR-PLAY-72V case | Expected | Baseline actual | R2 actual |
|---|---|---|---|
| `test_unsupported_objectives_readonly[Can the trail be followed?-survey]` | `DECLINE` | `ANSWER` | `ANSWER` |
| `test_unsupported_objectives_readonly[Can the trail be followed?-report]` | `DECLINE` | `ANSWER` | `ANSWER` |
| `test_unsupported_objectives_readonly[Can I follow the trail?-survey]` | `DECLINE` | `ANSWER` | `ANSWER` |
| `test_unsupported_objectives_readonly[Can I follow the trail?-report]` | `DECLINE` | `ANSWER` | `ANSWER` |
| `test_unsupported_objectives_readonly[Follow the trail to its source.-survey]` | `DECLINE` | `EXECUTE` | `EXECUTE` |

Provider calls were disabled. The five known assertions account for pytest exit code 1 in the baseline. The cleanup gate compares the failure identities and returned categories.
