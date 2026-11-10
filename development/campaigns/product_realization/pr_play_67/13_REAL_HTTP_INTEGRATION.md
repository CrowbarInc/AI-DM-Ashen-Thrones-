# REAL HTTP INTEGRATION

78 endpoint/fault requests (70 primary plus eight supplemental) use actual Uvicorn/FastAPI localhost TCP and urllib, not solely TestClient. Fifty holdout cases and ten raw-authority control requests are separate. Requests, status, complete redacted JSON, wire-byte counts, timings and leakage scans are preserved in http_integration.json, failure_injection.json, supplemental_http.json, gameplay_replay.json and serialized_http_payloads.json.

Modes enabled and disabled cover state refresh, actions, log, scene activation, character updates, response mode, snapshot list/save/load, reset, new/start campaign, author/debug denial, unsupported action and request validation. Supplemental multipart imports exercise valid and malformed input. Initialization/resolution/encoding exceptions return safe 500 rather than fabricated successful gameplay. All servers were ephemeral and stopped after capture. Holdout figures count cases; some cases issue multiple HTTP requests.
