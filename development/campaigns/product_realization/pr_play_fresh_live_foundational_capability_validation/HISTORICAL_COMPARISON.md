# Historical comparison

Baseline is the original 20-turn live evaluation, preserved as recorded. This sample is directional. It is not a significance test. Denominators were not resized to match the older run.

| Measure | Historical | This run | Absolute | Percentage points | Relative |
| --- | ---: | ---: | ---: | ---: | ---: |
| Interpretation accuracy | 8/15 (53.3%) | 5/13 (38.5%) | −3 correct on a smaller eligible set | −14.8 | −27.9% |
| Legitimate-action completion | 3/14 (21.4%) | 3/14 (21.4%) | 0 | 0.0 | 0% |
| Unnecessary refusal | 11/14 (78.6%) | 11/14 (78.6%) | 0 | 0.0 | 0% |
| Conversational continuity | 3/11 (27.3%) | 4/14 (28.6%) | +1 correct, +3 eligible | +1.3 | +4.8% |
| Useful grounded responses | 5/20 (25.0%) | 4/20 (20.0%) | −1 | −5.0 | −20.0% |
| Unauthorized consequences | 0 | 0 | 0 | — | — |
| Median latency | 3.581 s | 3.476 s | −0.105 s | — | −2.9% |
| P90 latency | 4.929 s | 3.947 s | −0.982 s | — | −19.9% |
| Provider calls | 16 | 14 | −2 | — | −12.5% |
| Tokens | 65,527 | 59,732 | −5,795 | — | −8.8% |
| Expenditure | $0.032005600 | $0.0292472 | −$0.0027584 | — | −8.6% |
| Retries | 0 | 0 | 0 | — | — |
| Completed turns | 20/20 | 20/20 | 0 | — | — |

Completion and unnecessary refusal land on the same rates. The turns are different: this player was refused at named people and at a clue phrase, then completed a notice reading and two exits. Interpretation is lower because seven turns never reached the model and, of the thirteen that did, five were fully correct. Continuity is slightly higher and still fails whenever the player refers to a person or a clue instead of a printed exit name. Usefulness is one response lower. The host is a little faster and cheaper on this sample.

Safe refusals were not counted as completed actions in either column.
