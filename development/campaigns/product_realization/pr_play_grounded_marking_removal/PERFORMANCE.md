# Performance

Command: `.\.venv\Scripts\python.exe artifacts\pr_play_grounded_marking_removal\measure_performance.py`

Evidence: `artifacts/pr_play_grounded_marking_removal/performance.json`. Two hundred rounds timed the local stages. One HTTP wipe and the following examination were timed once.

| Stage | Time |
|---|---:|
| Removal intent | 0.000007 seconds |
| Object, marking, and feasibility resolution | 0.000688 seconds |
| Observation intent | 0.000009 seconds |
| HTTP removal plus the following examination | 0.0463 seconds |

The published removal sentence is 101 bytes. The following observation is 52 bytes. The character grew from 9554 bytes to 11439 bytes. The 1885-byte growth is the removal receipt and the revision change. Resolution returned `ready`.

Live provider calls: 0. Token consumption: 0. Provider retries: 0. No additional model classification pass. No full-world scan. Network blocks: none. The provider snapshot has no token counter, so the before-token field is null and the measured consumption is 0.
