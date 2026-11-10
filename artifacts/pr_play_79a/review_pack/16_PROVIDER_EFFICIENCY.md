# Provider efficiency

Compared with PR-PLAY-79 (13 requests, 144,968 tokens, 0 published live dialogue, 0 accepted narration rewrites, 17 turns, 6 clarifications).

This run:

- Completed provider requests: 21
- Input tokens: 81,239
- Output tokens: 5,367
- Total tokens: 86,606
- Suggested ceiling: 30 requests and 60,000 tokens
- The ceiling was exceeded. No further provider calls were made after the script finished.
- Meaningful chat turns measured for latency: 17
- Clarifications in those turns: 1
- Mean turn latency: 1,968.0 ms
- Median: 1,730.5 ms
- P95: 5,584.0 ms
- Maximum: 7,158.0 ms
- Opening turns were about 12 to 14 seconds and are excluded from the gameplay latency figures above; they are in the transcript.

Tokens per published live response are not a single clean ratio. 86,606 tokens covered 7 accepted dialogue turns and 8 narration wrappers, including two openings of about 27,000 tokens each. Excluding openings, the remaining cost is about 32,000 tokens.

Requests per meaningful chat turn: 21 completed requests across 17 chat turns plus 2 openings, so many chat turns issued more than one call (expression plus narration).
