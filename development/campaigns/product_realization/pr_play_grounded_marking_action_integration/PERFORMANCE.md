# Performance

Command: `.\.venv\Scripts\python.exe artifacts\pr_play_grounded_marking_action_integration\measure_performance.py`

Isolated store. Providers disabled. Non-loopback sockets blocked. No blocks fired.

Mean stage time over 200 pure calls, and 50 full resolutions:

| Stage | Seconds |
| --- | --- |
| Intent classification | 0.0000088 |
| Object resolution | 0.000391 |
| Medium resolution | 0.0000319 |
| Content resolution | 0.0000092 |
| Prerequisite and full resolution | 0.000435 |
| HTTP commit and publication | 0.0811 |
| Save/reload read | 0.000258 |

Character file grew by 4325 bytes for one committed mark, its visibility record, and the receipt. One mark. Published success true.

Live provider calls: 0. Token consumption: 0. Provider retries: 0. No new model classification pass, world scan, prompt expansion, or provider retry loop.
