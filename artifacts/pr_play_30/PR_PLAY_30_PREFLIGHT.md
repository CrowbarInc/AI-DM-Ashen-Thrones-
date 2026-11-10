# PR-PLAY-30 preflight
Revision: d40f1ed198236c604085f1c842ead267a8104ce2. Inherited dirty working tree retained; git_status_inherited.txt records all entries excluding this pass. No commit/push. All 240 PR-PLAY-29 source/content hashes remain unchanged (source_hash_verification.json). Status capture was made after the observation harness; prior-pass hashes provide the independent implementation baseline.

Fixture: frontier-gate-v1; source revision b012c3d7e5887fdfb09d10bb9cc0f0220de09df9. Manifest SHA256 9c390c78f3fcf7507793e1037eb0add59e5e373050d1996f29f0c26f3b7bf0ea; world SHA256 44d04db85e3e0d5f352d9aff17808acfc1e8dac8734e979b72bae76d3bc91ded. Strict manifest and seven-file validation passed. All relevant scene digests are in fixture_verification.json.

Provider/model: OpenAI Responses; configured gpt-4.1-mini; safe_configuration.json records routing names and credential-presence boolean only. Harness selects ASHEN_OPENING_RENDERER=1. Zero actual provider dispatches. Mock SDK and interpretation/expression surfaces only. Host/SDK retry-disable settings installed by existing test fixture; fallback-model and judge calls zero. No model configuration changed.

API: unchanged production FastAPI endpoints available through TestClient; opening and all three ordinary submissions HTTP 200. Loopback socket exchange passed. External provider/network availability not probed because offline gate failed. No external readiness claim.

Security: 29/29 current confidentiality and privileged-read controls pass. Player mode only. Ordinary evaluator runs for each turn with authoritative snapshots; no integrity/confidentiality findings. The investigation's semantic failure is preserved, not waived.

Harness: verified authored fixture files copied into test-isolated storage after existing campaign-reset fixture creates runtime. No invented session/clue snapshot; opening and both conversation turns execute through production API. Turn 1/2 interpretation outputs are replayed from actual PR-PLAY-29 responses 02/04. The public offering expression and renderer plan are mocked; Turn 2 authored topic uses engine speech. PR-PLAY-29 capability reproduced offline.

Harness launch initially omitted tests.conftest and failed before gameplay because production_call_gpt was not captured. Loading that existing plugin corrected harness setup. No provider retry or implementation change. Correct command: `.venv/Scripts/python.exe -m pytest -p tests.conftest artifacts/pr_play_30/test_validation.py --basetemp=development/tmp/pr_play_30_run2 -q`.

Live budget readiness: ceiling seven, zero used. NO-GO at offline semantic gate; no live controller launched. No need to install or exercise a live seven-request admission guard when no live request is authorized by the gate.
