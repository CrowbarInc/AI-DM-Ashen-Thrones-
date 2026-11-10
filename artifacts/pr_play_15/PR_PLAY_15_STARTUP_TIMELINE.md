# PR-PLAY-14 startup timeline

All absolute times below are UTC on November 1, 2026 (subtract five hours for EST). Filesystem timestamps are metadata observations, not fabricated application events. Original evidence was reviewed before source edits.

| Event | Time / relative order | Evidence | Observed result | Confidence |
|---|---|---|---|---|
| Launcher invoked | 15:04:18.2213858 | artifacts/pr_play_14/invocation.json | One authorized Live invocation; renderer flag set to 1 | High |
| Controller run record initialized | 15:04:18.754898 | original reports/result.json timestamp | FiveTurnGameplay, Live | High |
| Worker created | After preflight, before log creation; exact OS creation unavailable | runner.py Popen ordering; cleanup PID 2368 | Actual base interpreter launched, combined stdout/stderr piped | High ordering; exact time unavailable |
| Application log opened | 15:04:20.4798834 | original application.log CreationTimeUtc | Zero bytes throughout run | High metadata |
| Socket bound/listening | Before configuration attestation; exact time unavailable | worker.py source ordering; ready.json port 50501 | IPv4 127.0.0.1; OS listen occurs before app imports | High source order; no runtime event timestamp |
| Configuration/accounting initialized | 15:04:22.365378 | original provider_usage.jsonl initialized event | No admission/dispatch/completion events followed | High |
| Renderer configuration recorded | By readiness file creation | original ready.json | enabled/selected, retries 0, six requests, token ceilings 200000/20000/220000 | High; no renderer invocation established |
| ready.json created | 15:04:22.3694176 | original ready.json CreationTimeUtc and LastWriteTimeUtc | Configuration/isolation attestation; does not prove HTTP service | High metadata |
| HTTP server initialization attempted | After ready.json; exact location/time unrecorded | source calls uvicorn after file write | No uvicorn log, failure file, or successful HTTP response | High source ordering; runtime progress unknown |
| First HTTP readiness request | After attestation read; precise time unavailable | controller source; final TimeoutError | Outcome detail discarded by old polling loop | High source ordering; individual outcome unknown |
| Subsequent polling attempts | Until deadline; count/timestamps unavailable | controller source | No successful HTTP 200; individual errors unknown | High absence of success; count unknown |
| Deadline expired | About 30 seconds after controller started polling; exact wall time unavailable | result failure TimeoutError; configured startup 30s | application_startup_failure; no scenario actions | High |
| Worker terminated | After timeout, before final result | process_cleanup in result and execution_log | PID 2368 stopped, exit code 1; not evidence of spontaneous crash | High ordering |
| Cleanup/report complete | Result elapsed 31.312s; result file last write 15:04:50.5963282 | result.json and filesystem metadata | Owned worker reaped, evidence exported; no gameplay | High; elapsed excludes final export |

Historical first/last poll timing, actual initialization stack, HTTP status and connection errors cannot be recovered. The PR-PLAY-15 reproduction supplies new evidence, not retroactive timestamps.
