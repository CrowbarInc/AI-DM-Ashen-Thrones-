# Provider-Assisted Planning

Live model: `gpt-4.1-mini`. Purpose: `physical_plan`. Owner: `physical_adjudication`.

| Call | Utterance | Result | Tokens | Latency |
| --- | --- | --- | --- | --- |
| 1 | Earlier door-and-look wording | Rejected, deterministic disagreement | 264 | 2253 ms |
| 2 | "I open the door and look inside." | Rejected. Proposal added approach, open, and inspect. | 264 | 1479 ms |
| 3 | "Open the door, then check inside." | Rejected for the same extra approach. | 264 | 835 ms |
| 4 | "I push the crate aside and inspect it." | Accepted. Host executed. | 245 | 1255 ms |

Totals: 4 requests, 1,037 tokens, 0 retries. Budget ceiling was 8 requests and 16,000 tokens.

Accepted publication: "You push the oak crate. It is now aside from where it was. The oak crate is aside from where it was."

`committed_by_provider` is false. The second process could not reuse the first usage ledger because admission opens that file exclusively. The accepted run used a fresh ledger at `artifacts/pr_play_77/provider_live_run`.

The browser host had provider calls disabled. Browser success is deterministic and is not counted as a live provider success.
