# PR-PLAY-32 failure analysis

First failed boundary: **process ownership/isolation attestation during harness readiness**. Critical harness readiness failure before production HTTP access: controller PID 31692 differs from ready.json PID 18644. runner.wait_for_http_ready rejected the attestation with RuntimeError: Isolation attestation mismatch.

Evidence: live/diagnostics/readiness_poll.jsonl worker_spawned and attestation_mismatch; ready.json reports correctly isolated data path, model, retry settings and renderer but a different PID. execute.py launches sys.executable from .venv; unlike the prior PR-PLAY-29 controller it does not select sys._base_executable. A Windows virtual-environment launcher creating a child interpreter is the likely explanation. This is an evidence-supported inference; process ancestry was not captured, and CIM process inspection was unavailable. The exact fact established is PID mismatch, not corrupted campaign isolation.

Classification: experiment instrumentation/environment, not provider or gameplay. This pass's artifact controller introduced a launcher choice inconsistent with the prior working controller; no new product defect is established. Secondary observations: initial unsafe harness storage location refused; one offline security-test setup hit the previously documented WinError 5 and passed on recheck. Neither is evidence of failed live gameplay.

No provider error, parsing error, wrong target, route defect, clue-authority failure or dialogue defect was observed live. No repairs made. Recommended next investigation: review launcher/process ownership in the harness offline using the prior base-interpreter pattern, retaining strict attestation, before separately authorizing a fresh bounded live attempt. Do not launch PR-PLAY-33 automatically.

Procedural limitations: correct fixture verified and evidence packaged, but required live initialization/transitions were not performed because mandatory preflight failed. This is a completed stop report, not completion of the requested live gameplay validation.
