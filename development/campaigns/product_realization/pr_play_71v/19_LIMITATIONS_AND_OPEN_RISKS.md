# 19 — Limitations and open risks

- W12 is an authoring hole in a frozen case. The delay schedule is covered elsewhere. The holdout was not silently rerun.
- The publication HTTP 500 was not reproduced and is not explained.
- Combined-process HTTP 503s came from a cached preflight and did not reproduce in isolation. A long process can still block later tests until the interpreter is restarted.
- Browser-visible latency was not measured separately from server time.
- The post-resume question to the watch was not written into a new snapshot before Campaign A was loaded. The live attachment was verified; the earlier report slot does not contain that line.
- Journal lead text still concatenates the turn marker and the fact.
- Optional narration in this cycle is stubbed. Mechanical narration was not reopened.
- `data/session_log.jsonl` no longer matches its protected working-tree hash. The uncommitted log bytes from the start of the cycle were not recovered.
- No multiplayer, crash-during-fsync, or official ATGB claim is made.
- Process-crash durability beyond the atomic replace and the in-process commit scope was not tested.
