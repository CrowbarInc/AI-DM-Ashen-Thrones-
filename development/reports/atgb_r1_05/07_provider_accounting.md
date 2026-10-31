# 07 — Provider Accounting

| Trial | Admissions | Responses | Failed | Input | Output | Total | Wall ms | Dispatch ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| L1 | 1 | 1 | 0 | 2004 | 211 | 2215 | 4199.838 | 2995.613 |
| L2 | 1 | 1 | 0 | 2004 | 210 | 2214 | 3730.975 | 2498.776 |
| L4 | 1 | 1 | 0 | 1837 | 209 | 2046 | 3670.014 | 2596.488 |

Measured total: 3 application admissions/dispatches, 3 successful responses, zero
failed dispatches, 5845 input + 630 output = 6475 tokens. All returned usage is
consistent, no pending attempt or unknown usage. Durable admission-before-dispatch
events and response IDs retained in each provider_usage.jsonl/accounting.json.
Configured OpenAI Responses gpt-4.1-mini; returned gpt-4.1-mini-2025-04-14 for all.

Per trial: one actual SDK client, max_retries 0; application retry flag disabled;
no automatic trial retry, model escalation, continuation or narration admission.
Three completed trials meet maximum three; each 1/2 admissions, aggregate 3/6.
Unused allowance is not spent. L4 setup uses stubbed interpretation at zero admissions;
the measured revision is actual live interpretation. Two offline previews and one
rejected pre-process launch make no admissions and do not count as completed trials.
No failed provider call or unknown billing is hidden in the totals.

Input/output/total tokens are provider measurements; preflight token estimates are
separate ceiling checks. Cost unavailable: no configured price table or billing
invoice; no invented dollar figure. End-to-end wall latency includes preflight,
provider construction, interpretation and host response; L4 deterministic setup is
outside measured revision timing. Dispatch latency is measured by production budget
around SDK invocation. Historical host timings are not an equivalent baseline, so
no performance success or repair-attributable cost/latency improvement is graded.

The first launch was denied by automatic approval review before execution due to
external campaign-data transfer authorization. User then explicitly approved the
named destination, context and three trials. Accepted escalated execution followed;
no bypass or hidden network retry. See authorization_and_launches.json.
