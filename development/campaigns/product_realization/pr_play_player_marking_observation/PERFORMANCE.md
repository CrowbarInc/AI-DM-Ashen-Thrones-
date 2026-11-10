# Performance

Command: `.\.venv\Scripts\python.exe artifacts\pr_play_player_marking_observation\measure_performance.py`

Evidence: `artifacts/pr_play_player_marking_observation/performance.json`.

| Stage | Mean |
|---|---:|
| Observation intent | 0.000007 seconds |
| Target resolution | 0.000575 seconds |
| Disclosure projection | 0.000090 seconds |
| HTTP examination, including publication | 0.0259 seconds |

The HTTP examination returns 74 bytes of player text. The preceding marking sentence is 125 bytes. Character size stays 9349 bytes across the examination.

Live provider calls: 0. Added tokens: 0. Provider retries: 0. No additional model classification pass. Resolution reads the character inventory, not the world catalog. Network blocks: none.
