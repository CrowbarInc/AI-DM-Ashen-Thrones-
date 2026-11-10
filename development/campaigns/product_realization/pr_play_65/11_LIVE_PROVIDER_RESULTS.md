# LIVE PROVIDER RESULTS

Existing OpenAI adapter, model `gpt-4.1-mini-2025-04-14`. Four real requests, 1658 input + 88 output = 1746 tokens. Zero retries. Budget 6 requests / 12,000 tokens respected. All four candidates duplicated engine-owned outcomes; no accepted/published AI presentation. No favorable-result retries after failure. Provider responses, latency and usage are preserved in gameplay_actions.json, quarantine_evidence and provider ledger.

- I examine the notice board.: raw `You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.`; REVIEW_REQUIRED; published `You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.`.
- I examine the rain barrel.: raw `You examine the rain barrel. No new clue is established by this examination.`; REVIEW_REQUIRED; published `You examine the rain barrel; no new clue is established.`.
- I examine the notice board again.: raw `You examine the notice board again. The examination adds nothing new to what you already know.`; REVIEW_REQUIRED; published `You examine the notice board again; nothing new is established.`.
- I examine the weathered milestone.: raw `You examine the weathered milestone. Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.`; REVIEW_REQUIRED; published `I cannot provide a validated response to that request.`.

No broad comparison with PR64: categories differ, and publication failed. Preflight skipped explicitly by the established isolated harness; actual adapter sent/usage records substantiate only these four live calls.
