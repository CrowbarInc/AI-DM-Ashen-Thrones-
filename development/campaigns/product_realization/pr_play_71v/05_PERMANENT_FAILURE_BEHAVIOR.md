# 05 — Permanent failure behavior

When all four replace attempts raise WinError 5, `_atomic_write_bytes` raises `PermissionError`. It does not convert that into a successful response.

Checked behavior:

1. The operation reports failure.
2. HTTP chat does not return a successful committed turn.
3. The existing target file remains the prior bytes.
4. The temporary file is removed.
5. `runtime_commit_scope` restores the pre-turn runtime files, so a partial turn does not become authoritative.
6. The gameplay function and the provider stub run once.
7. Branch flags are not applied twice.
8. Player responses use the existing generic safe error and do not include GM notes or hidden facts.
9. A later write with a working replace succeeds.
10. The exception remains visible to the test and to server diagnostics.

The retry budget is the three delays plus the final attempt. It does not grow.
