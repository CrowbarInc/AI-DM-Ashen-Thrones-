# PR-DD Cost Model

No current provider price is stored in this repository. Costs below are formulas. Token figures are labeled as historical live usage, reconstructed estimates, or hypothetical savings.

Model name in the historical live runs: `gpt-4.1-mini`, response model `gpt-4.1-mini-2025-04-14`. This audit did not call it.

Tokenizer: `tiktoken` is not installed. Exact tokenizer counts are unavailable. Reconstructed estimates use `ceil(character_count / 4)`.

## Formula

Let `P_in` and `P_out` be configurable prices in currency per million tokens.

```
cost_per_turn = (input_tokens * P_in + output_tokens * P_out) / 1_000_000
cost_per_100_successful_turns = 100 * cost_per_turn
```

When a turn retries, add every attempt:

```
turn_tokens = sum(input_i + output_i for each provider attempt) + fallback_tokens_if_any
retry_overhead_tokens = turn_tokens - tokens_of_the_attempt_that_was_accepted
```

If no attempt is accepted, retry overhead is the entire turn.

## Actual historical usage

PR-CY, recorded provider usage:

| Turn | Attempt | Input | Output | Total | Result |
|---|---|---:|---:|---:|---|
| T1 preference | 1 | 27,442 | 109 | 27,551 | Accepted |
| T2 follow-up | 1 | 31,242 | 1,230 | 32,472 | Rejected |
| T2 follow-up | 2 | 39,262 | 331 | 39,593 | Rejected |

T2 combined: 70,504 input and 1,561 output, 72,065 total tokens, then a fallback refusal. The retry request alone was 39,593 tokens.

PR-DA follow-up, one live request, reduced context not selected:

| Attempt | Input | Output | Total | Result |
|---|---:|---:|---:|---|
| 1 | 30,166 | 116 | 30,282 | Accepted |

PR-DA also recorded a full-context serialized size of 127,336 bytes for that follow-up. This audit did not remeasure that live request.

## Reconstructed estimates from this audit

These are `ceil(chars/4)` on `build_messages` output. They are not provider usage.

| Class | Serialized bytes | Estimated input tokens |
|---|---:|---:|
| Harmless preference | 98,773 | 24,684 |
| Experiential follow-up | 98,123 | 24,521 |
| Multi-turn continuation | 98,061 | 24,506 |
| Ordinary observation "I look around." | 103,854 | 25,953 |
| Ordinary movement, unresolved destination | 104,643 | 26,151 |
| Notice-board inspection | 106,771 | 26,683 |
| Hidden-information question | 107,312 | 26,818 |
| Consequential social question | 108,362 | 27,080 |
| Authored patrol question | 110,114 | 27,518 |
| Scene transition "Enter Cinderwatch" | 113,279 | 28,310 |
| Synthetic skill check | 91,621 | 22,897 |
| Synthetic combat attack | 121,416 | 30,336 |

A calibration check, not a conversion to use as fact: PR-DA's 30,166 live input tokens divided by `127336/4` is about 0.95. The character estimate was slightly high on that one payload. Applying 0.95 to the new estimates would be an unverified assumption, because the payloads differ and the tokenizer is not in-repo. This report does not apply that factor.

## Hypothetical savings

Exact contract-mirror removal, preference request: 10,947 bytes, about 2,737 estimated tokens, about 11.1% of that request. Hypothetical only. It has not been built, and it has not been tokenized by the provider.

History growth on the same preference resolution, using repeated authored visible-fact snippets:

| Probe entries | Request bytes | Estimated tokens | History block bytes |
|---|---:|---:|---:|
| 0 | 98,773 | 24,684 | 1,082 |
| 4 | 102,509 | 25,618 | 3,198 |
| 8 | 103,039 | 25,750 | 3,728 |

From empty to eight entries the request grew 4,266 bytes, about 4.3%. The last four entries added 530 bytes. Further history truncation has little room.

Hypothetical retry instruction for `unresolved_question`: 4,239 bytes, about 1,060 estimated tokens, appended on top of a resent prior request. The historical PR-CY retry did not add 1,060 tokens. It sent a second full request of 39,262 input tokens. Eliminating a retry of that shape saves about 39,593 total tokens per avoided failure. That is larger than the 11% context trim.

## Per 100 successful turns

Using the two accepted historical samples, if every turn matched that sample:

| Basis | Input tokens per 100 | Output tokens per 100 | Total tokens per 100 |
|---|---:|---:|---:|
| PR-CY T1 preference, accepted | 2,744,200 | 10,900 | 2,755,100 |
| PR-DA follow-up, accepted | 3,016,600 | 11,600 | 3,028,200 |

```
cost_per_100 = (input_tokens_per_100 * P_in + output_tokens_per_100 * P_out) / 1_000_000
```

If one turn in ten instead followed the PR-CY T2 failure (72,065 tokens instead of an accepted ~30,282), those ten failures would replace about 302,820 tokens with about 720,650 tokens. That single assumption is not a measured rate. PR-CY and PR-DA are two sessions, not a rate.

The useful affordability lever on current evidence is first-attempt acceptance. Context trimming of about 11% matters on every turn. A prevented full retry matters more on the turns that fail.
