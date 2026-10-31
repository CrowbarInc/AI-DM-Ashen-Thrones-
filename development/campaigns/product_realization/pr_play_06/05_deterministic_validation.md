# 05 — Deterministic Validation

PR-PLAY-06 · 2026-10-28 America/New_York · evidence_scope: structural_only.

58 focused checks pass: 19 new + all 18 PR-PLAY-04 + 21 PR-PLAY-05. SDK/network
provider access is synthetic or blocked by the existing live-model guard.

| Control | Result/evidence |
|---|---|
| B1 minimal | market three-declaration opening accepted; measurements/minimal.json |
| B2 typical | existing gate opening accepted; measurements/typical.json |
| B3 rich | full existing declaration representation accepted; measurements/rich.json |
| B4 former-ceiling excess | 3726 chars/~932 estimated tokens accepted under requested 3000; synthetic usage only |
| B5 ordinary | accounting 600; no-accounting absent-cap compatibility; explicit opening override 2800 tested |
| B6 incomplete at ceiling | valid JSON with incomplete/max_output_tokens rejected; content_filter also rejected; truncated JSON rejected |
| B7 invalid JSON | malformed/missing/incomplete/empty shapes rejected with rollback |
| B8 provider exception | one dispatch failure, no gameplay commit; later user retry succeeds once |
| B9 aggregate exhaustion | 1000 aggregate output ceiling refuses 3000 reservation, HTTP 409, zero admissions/dispatch, state equal |
| B10 failed then successful | retained failure/failure/success and exception/success tests commit once |

The response fixture over_600 uses existing full declaration fields, without added
lore or whitespace inflation. Its token size is estimated; neither estimated SDK
usage nor host acceptance proves a live model can finish within 3000.

Retained PR-PLAY-04 controls cover accepted opening exactly one turn/time/faction
increment, rejected opening no progression, retryability, repeated Start 409,
concurrent Start serialization (one 200/one 409), chat-start parity, pre-dispatch,
pipeline and save exceptions. PR-PLAY-05 controls compare persisted JSON values and
file inventory. Existing saved_at/last_saved_at, addressability debug traces and
empty session_log materialization are bookkeeping; byte identity is not claimed.
Raw before/after gameplay snapshots and lifecycle/diagnostic rows accompany the
new fixture cases, aggregate refusal, incomplete statuses, repeated/retry/concurrent
controls and retained diagnostic negative controls.

Prompt integrity: unchanged producer/contracts plus before/after component sizes
on gate and market fixtures; zero reductions. Hidden-protection strings and
authorized claim IDs remain in their established request owners. No broad gameplay
quality or independent generalization claim. Frozen benchmark was not rerun.

Provider budget controls: one dispatch per synthetic initial generation; no extra
provider operations, admission ceilings, six-request concurrency and SDK max_retries
0 remain enforced. Aggregate usage uses completed lifecycle rows only; diagnostic
copies are not summed. Existing PR-PLAY-05 ledger reconciliation assertions pass.
Opening ceiling 3000 is visible in request, completed record and diagnostics.
Complete JSON on incomplete status retains JSON/envelope observations but fails
final host acceptance/commit; no automatic retry. Historical rich unsupported
claims continue to fail rather than gaining authority from a larger allowance.
