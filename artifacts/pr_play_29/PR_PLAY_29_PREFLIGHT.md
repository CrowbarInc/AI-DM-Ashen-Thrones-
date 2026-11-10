# PR-PLAY-29 offline preflight

Decision: PASS. Zero live requests during preflight.

- Repository revision: d40f1ed198236c604085f1c842ead267a8104ce2. Dirty inherited working tree is recorded in git_status_before.txt. Existing game/API/content changes are PR-PLAY-23 through 28 prerequisites, not PR-PLAY-29 edits. Source hashes recorded before execution.
- Provider: OpenAI Responses, configured gpt-4.1-mini; credentials present, values never exported. Model routing names have no differing configured override. Provider timeout defaults to 45 seconds; API timeout 90 seconds. No connectivity model probes.
- Budget: atomic production accounting capped at five actual dispatches, input/output/total token ceilings 200000/20000/220000. Synthetic accounting admits five, refuses sixth. SDK max_retries=0; host retries disabled; observing worker refuses additional dispatch after provider failure or any differing configured model. No AI judges or fallback models.
- Network: Windows loopback socket exchange and owned production HTTP GET /api/state succeeded; offline diagnostics/http_ready.json records HTTP 200. Zero live dispatches.
- Opening: ASHEN_OPENING_RENDERER=1 and selected=true attested by owned worker.
- Security: 29 response-projection/privileged-read controls pass, including player-mode hidden filtering and client author/debug rejection. No privileged browser mode enabled.
- Local interaction/public-fact/expression/topic/authority/harness: 147 focused offline controls pass. Includes conservative local approach, offering attribution, faithful paraphrase adoption, unsupported additions rejected, recoverable versus generic fallback stops, rumor category eligibility, disclosure restrictions, and legitimate versus corrupted clue provenance.
- Initial security run: 27/29 passed; two mocked opening tests returned 422 because the global ASHEN_DISABLE_PROVIDER_CALLS=1 setting prevented their synthetic SDK transport from dispatching. Repeating with the tests' guarded mock transport enabled passed 29/29. This changed only the test process environment; no application repair. Both outputs retained.
- Fixture: frontier-gate-v1; source revision b012c3d7e5887fdfb09d10bb9cc0f0220de09df9; pinned manifest SHA256 9c390c78f3fcf7507793e1037eb0add59e5e373050d1996f29f0c26f3b7bf0ea; world SHA256 44d04db85e3e0d5f352d9aff17808acfc1e8dac8734e979b72bae76d3bc91ded. Strict load_baseline verification passes every file and manifest pin. Source note records PR-PLAY-28 rumor metadata update.
- Content: frontier_gate visible fact attributes hot stew and rumors to tavern runner. Runner patrol_rumor has discovery_categories=["rumor"]. Disposable store copied by established isolation helper; actual post-reset state must be rechecked before ordinary actions.
- Harness: observation-only copy of PR-PLAY-26 controller and observer, scoped to exact required NPC/actions and added existing opening integrity evaluator. Human agent gates opening and Turn 1 using persisted evidence. No provider retry/reset; maximum two actions. Deterministic engine fallback allowed, fallback models forbidden. Full diagnostics kept separate from player transcript.

Evidence: fixture_verification.json; safe_configuration.json; offline_result.json; offline_budget_verification.json; preflight_tests.xml (147/147); security_corrected_tests.xml (29/29); artifacts/atgb/pr_play_29/offline diagnostics and snapshots.
