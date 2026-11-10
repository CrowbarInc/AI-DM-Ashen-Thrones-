# Process ownership

Control A, module worker, captured before cleanup.

| Field | Value |
| --- | --- |
| Controller pid | 26144 |
| Controller image | `C:\Users\Master Mandalcio\AppData\Local\Programs\Python\Python312\python.exe` |
| Controller created | 2026-11-02T01:05:11Z |
| Popen / worker pid | 32792 |
| Worker-reported pid | 32792 |
| Parent pid | 26144 |
| Worker image | `C:\Users\Master Mandalcio\AppData\Local\Programs\Python\Python312\python.exe` |
| Base interpreter | `C:\Users\Master Mandalcio\AppData\Local\Programs\Python\Python312\python.exe` |
| Worker created | 2026-11-02T01:05:13Z |
| Child | `conhost.exe` pid 16612, created 2026-11-02T01:05:13Z |
| Launch | `C:\Users\Master Mandalcio\AppData\Local\Programs\Python\Python312\python.exe -u -m tools.playtest.worker C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\artifacts\atgb\pr_play_34\readiness\A\20261102T010511Z-7938740cf7c8` |
| HTTP | 200 in 1.61 seconds |
| Shutdown | owned pid 32792, stopped, exit 1, 0.0 seconds |
| Orphans after cleanup | none |
| Port released | True |

Exit code 1 is the controller's owned-handle terminate, which is the harness shutdown action. The controller observed the exit. No orphan remained.

Control E, observer `artifacts/pr_play_32/worker_capture.py`: controller 26144, worker 18696, parent 26144, reported 18696, image `C:\Users\Master Mandalcio\AppData\Local\Programs\Python\Python312\python.exe`. HTTP 200 in 1.453 seconds. Cleanup stopped pid 18696. Orphans: none.

Control D timed out at 0.406 seconds against a 0.4 second deadline and then stopped pid 34352. Control C's worker exited on its own with code 2 before readiness. Control F's worker pid 460 was the cleaned-up pid; the port holder pid 29176 was still alive and still bound to port 50267. The holder was a process this diagnostic spawned with the base interpreter, and it was terminated only after that check.
