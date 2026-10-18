# 24 — Provider Evidence

Official primary evidence: 176 A calls and 176 C calls; B makes none. Secondary: 22 unhinted A interpretation calls and 22 fresh C calls. Supplemental: 35 A calls and 35 C calls. Total **466 logical provider calls**. SDK retry behavior is not instrumented separately. Per-record model/settings, input/output usage, latency, raw JSON output and exact payload are retained in primary.jsonl, secondary.jsonl, supplemental_results.jsonl and paraphrase_results.jsonl.

Invalid first execution records: 264 in invalid_initial_attempts.jsonl, excluded from architecture scoring. That file includes connection failures and interrupted adapter errors; paid responses lost before the KeyError was surfaced are not recoverable. Those attempts cannot be counted as successful official evidence or assigned zero billing. Both initial and corrected adapter hashes are preserved.

No mock-only provider success claim. Prompt C is versioned in engine.VERSION/C_PROMPT, A by production hash; schemas are frozen code. Configured model gpt-4.1-mini, temperature 0, max output 1800.
