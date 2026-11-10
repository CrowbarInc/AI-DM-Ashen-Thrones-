# Provider usage

- Provider requests: **0**.
- Input tokens: **0**; output tokens: **0**; total provider tokens: **0**.
- Live gameplay turns: **0**; campaign initialization/start/chat POSTs: **0**.
- Provider/SDK/host retries: **0**. Readiness retries: **0**.

Evidence: isolated diagnostics/provider_usage.jsonl contains accounting initialization only; budget_snapshot.json has zero dispatches, zero tokens and no attempt records. Deterministic mode uses placeholder credentials, synthetic transport and external socket denial; diagnostic additionally forbids provider admission and every non-state HTTP request. Stdlib process reproductions and regression probe workers import no provider SDK. Gameplay source hashes are unchanged. Actual loading/saving of bootstrap session data by the state endpoint is disclosed; turn zero and campaign_started=false are verified. No live gameplay experiment or subsequent PR was initiated.
