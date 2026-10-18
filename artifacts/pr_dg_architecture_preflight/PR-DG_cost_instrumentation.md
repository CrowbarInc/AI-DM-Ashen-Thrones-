# PR-DG Cost Instrumentation

No live provider call. No latency for a provider. No output-token assumption. No price.

Narration call shape from code: game.gm.call_gpt responses.create(model=route.selected_model, input=messages) has no temperature or max_output_tokens keyword
Default model name from code: `gpt-4.1-mini`.
Narration temperature and max tokens: not passed. Interpretation, if it were enabled, uses temperature 0 and max_output_tokens 400. It was not enabled.
Token estimate method: `ceil(utf-8 bytes / 4)`. This is not a provider bill. `tiktoken` was not required for this label.

Scripted planner and tool bytes are the serialized gold plan or transcript plus the tool results. They are not measured live prompt usage.

| # | A narration bytes | A est. | B narration | B scripted context | C narration | C scripted context | C rounds |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 S1 | 86764 | 21691 | 86764 | 902 | 86764 | 1977 | 3 |
| 2 S2 | 86238 | 21560 | 86238 | 833 | 86238 | 1898 | 3 |
| 3 F1 | 88106 | 22027 | 88106 | 850 | 88106 | 1883 | 3 |
| 4 H1 | 86169 | 21543 | 86169 | 789 | 86169 | 1831 | 3 |
| 5 M1 | 77693 | 19424 | 77693 | 733 | 77693 | 1806 | 3 |
| 6 O1 | 78018 | 19505 | 78018 | 688 | 78018 | 1792 | 3 |
| 7 K1 | 71744 | 17936 | 71744 | 536 | 71744 | 1857 | 3 |
| 8 B1 | 85617 | 21405 | 85617 | 730 | 85617 | 1771 | 3 |
| 9 C1 | 86282 | 21571 | 86282 | 836 | 86282 | 1885 | 3 |
| 10 compound | 77835 | 19459 | 77835 | 1054 | 77835 | 2487 | 4 |
| 11 ambiguous | 77916 | 19479 | None | 630 | None | 1858 | 3 |
| 12 courier | 86831 | 21708 | 86831 | 925 | 86831 | 1988 | 3 |
| 13 declared_canon | 78552 | 19638 | None | 769 | None | 1858 | 3 |
| 14 mechanical_dump | 90649 | 22663 | None | 701 | None | 2016 | 3 |

Hypothetical provider rounds, if these scripts were later sent to a model, and if narration retries stay unknown rather than zero:

- A: `I = 0` because interpretation is pinned off. `N = 1` when a narration payload was built, else the turn did not reach narration. `R` is not measured.
- B: `P = 1` scripted plan input, `Q = 0` replans in this preflight, plus `N` as above when the plan executed.
- C: the transcript round count (at most 4), plus `N` when execution committed.

Where B or C executed, their narration byte count matched A. The payloads are not smaller. PR-DE's published S1 figure is 87,583 bytes. This run's S1 narration payload is the `build_messages` size for the harness resolution, and it is a different number. It is not used as a cost win against PR-DE or against another candidate.

Local resolver timers were recorded in milliseconds on the result rows (`elapsed_ms`). Those are process timers around existing resolver calls. They are not provider latency and they are not a table baseline.
