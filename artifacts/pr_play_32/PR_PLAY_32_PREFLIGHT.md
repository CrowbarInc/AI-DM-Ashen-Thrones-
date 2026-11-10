# PR-PLAY-32 preflight

**STOP BEFORE LIVE REQUESTS — preflight did not pass.**

Repository revision: `d40f1ed198236c604085f1c842ead267a8104ce2`. Inherited working tree is heavily dirty, including earlier gameplay repairs and historical artifact changes/deletions. Full status is in git_status_before.txt; game/tools source hashes were unchanged during the server attempt (source_integrity.json). No gameplay, campaign content, fixture, commit or push changes made by this pass.

Fixture: `frontier-gate-v1`, strict verification PASS. Manifest SHA-256 `9c390c78f3fcf7507793e1037eb0add59e5e373050d1996f29f0c26f3b7bf0ea`; source revision `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`. Full file digests in fixture_verification.json. Tavern Runner, patrol_rumor rumor metadata, separate rumor/physical clues, authored patrol exit, Old Milestone and prints interactable are present in the pinned fixture. Isolated copied files match the manifest; no knowledge injected.

Provider: OpenAI Responses, configured gpt-4.1-mini; credentials available (value never printed). All configured routing models resolve to that same model. Existing 45-second provider timeout; 110-second controller action timeout. Native limits 10 requests / 200000 input / 20000 output / 220000 total tokens. SDK retries 0, host retries 0; dispatch observer enforces model and request ceiling. No fallback model or judge requested. No outbound provider connectivity probes.

Opening: ASHEN_OPENING_RENDERER=1; worker attests enabled/selected. No opening generated.

Security/conversation/exploration: 132 focused offline cases selected across purpose routing, response confidentiality, privileged reads and expression recovery. 131 passed; one WinError 5 setup error while replacing test session.json. That isolated case passed on one offline recheck. No assertion failures. Existing PR-PLAY-31 offline integration was inspected, not presented as new live evidence. Native validators/evaluators remain enabled.

Network/harness: Critical harness readiness failure before production HTTP access: controller PID 31692 differs from ready.json PID 18644. runner.wait_for_http_ready rejected the attestation with RuntimeError: Isolation attestation mismatch. A loopback socket bound, but endpoint reachability was not established. Readiness guard remained enabled; no initialization or action was submitted. Configured provider accounting initialized but never dispatched. Recoverable expression-rejection classification is covered offline; live state/confidentiality evaluation is NOT RUN.

Harness assembly limitations: initial proposed data path was refused by the existing storage guard and corrected to its required artifacts/atgb path before startup. A quoting error in the first artifact-only edit command changed nothing. The corrected launch then failed process attestation. No second worker was launched, no campaign reset, and no readiness guard was bypassed. Stop honored; no live retry. Owned launcher and attested child are absent at cleanup; socket release result: True.

Decision: FAIL readiness; **D — INCONCLUSIVE** for gameplay. Do not repair or relaunch in this pass.
