# 02 — Readiness and Startup

**Blocked — representative startup/play.** The single nonbillable readiness check found configured credentials and production model settings, then socket.getaddrinfo(api.openai.com, 443) raised gaierror errno 11001 in 6.839 ms. This is DNS lookup time, not model latency. Evidence: artifacts/pr_play_01/readiness.json and baseline_environment.json. No repeated DNS checks, network repair, endpoint switch, TCP/TLS request, authentication request or inference followed. Endpoint reachability beyond DNS is blocked; credential presence is not credential validity. Root cause unresolved; do not infer provider outage or product defect.

The application startup preflight itself invokes Responses inference (game/api_upstream_preflight.py). It was deliberately not used as the nonbillable gate. No Uvicorn server, lifespan startup, browser session, New Campaign endpoint or Start Campaign endpoint was launched after readiness failed. Therefore actual startup elapsed time, opening response, UI readiness and repeated-action friction remain unmeasured.

**Deterministically validated:** Six existing tests in tests/test_campaign_reset.py executed the actual reset owner using temporary stores. They verify campaign_started cleared; new run ID; removal of stale nested runtime references; world flags/events/projects and faction playthrough reset; empty log; fresh-campaign invariant checks. They do not generate or display an opening.

**Deterministically validated:** Current production interpretation request construction under a stub passed in R1-07/R2-04 tests. Current instructions, schema slots, public evidence controls and grounding controls were exercised without dispatch.

**Inspected only:** Browser New Campaign silently resets and reloads; a separate enabled Start Campaign button requests opening narration. New/start endpoints consult upstream gate before their respective flows. Fresh bootstrap source remains the existing frontier-gate-v1 fixture, not newly authored content.

Gameplay did not become available in this pass. Environment classification C; primary failure F2. No F1 startup defect established. The manual handoff includes exact disposable launch instructions; it is an unexecuted future procedure.
