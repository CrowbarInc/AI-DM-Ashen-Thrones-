# 07 — Compatibility and Regression

Legacy mode remains the default. `tests/test_pr_play_04_opening_integrity.py` and `tests/test_pr_play_11_claim_authority.py` passed with the flag unset. Ordinary turn messages are not rewritten into a presentation plan.

Shared edits outside the opening branch:

- `call_gpt` reads the response type before the provider-disabled return so an invalid opening flag fails closed. With the flag disabled, the opening guidance string is the previous text.
- Generation diagnostics recognize an `opening_presentation` envelope only when that contract is active.
- The playtest runner retries a transient Windows read of `ready.json`. This is not a provider retry.
- Ready and run configuration include the renderer mode so the selection is observable. The default value is disabled.

## PR-PLAY-12 selection

The same PR-PLAY-11 lane files were executed with the flag removed from the environment.

| Batch | Count |
| --- | --- |
| Passed | 871 |
| Failed | 19 |
| Errors | 2 |
| Executions | 892 |

Fourteen failures match the PR-PLAY-12 preexisting set: provider readiness, immutable-boundary chat stub, three start-campaign API cases, ATGB accounting readiness, claim-control false positive, realization provenance, and six investigation-provenance cases.

Seven other batch outcomes were Windows file-access races. Isolated reruns passed:

- Five-turn G12, G22, and G25, after the startup read retry.
- Diagnostic matrix D6, opening fixture `over_600`, and semantic matrix including S8.
- `test_provider_disabled_host_uses_chat_and_isolates_state`.

No relevant new regression remains. Unrelated preexisting failures were not repaired. Frozen ATGB judgments and attestations were not edited. The five-turn renderer run is new evidence under `artifacts/atgb/automated_playtests/` and does not replace a frozen score.
