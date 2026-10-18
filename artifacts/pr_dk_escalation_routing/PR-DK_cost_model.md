# PR-DK Cost Model

PR-DH provider baseline:

- Candidate B: 6 interpretation calls, 4,414 input tokens, 1,361 output tokens, 5,775 total tokens.
- Candidate C: 16 interpretation calls, 18,983 input tokens, 2,859 output tokens, 21,842 total tokens.
- PR-DH total live interpretation requests: 22 / 24 rows.

Average per interpretation call from PR-DH:

- Candidate B: about 962.5 total tokens per call.
- Candidate C: about 1,365.1 total tokens per call.
- Overall PR-DH: about 992.8 total tokens per call.

Hypothetical calls per 100 player turns:

| Complication rate | Selective calls / 100 | Universal calls / 100 | Selective token overhead at B avg | Universal token overhead at B avg |
| --- | ---: | ---: | ---: | ---: |
| 5% | 5 | 100 | ~4,813 | ~96,250 |
| 15% | 15 | 100 | ~14,438 | ~96,250 |
| 30% | 30 | 100 | ~28,875 | ~96,250 |
| 50% | 50 | 100 | ~48,125 | ~96,250 |

This does not invent provider prices and does not claim full-turn savings. Narration cost remains. Clarification overhead and repeated-call overhead are additional risks; PR-DH Candidate C demonstrated repeated interpretation calls on difficult cases.
