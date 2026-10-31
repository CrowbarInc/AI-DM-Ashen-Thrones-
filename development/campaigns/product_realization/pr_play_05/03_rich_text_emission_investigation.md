PR-PLAY-05 · 2026-10-27 (America/New_York) · evidence_scope: structural_only. Synthetic provider controls; no live generation or gameplay-quality claim.

# 03 — Rich-Text Emission Investigation

Three independent original tests were reproduced individually on current, preserved entry and hash-verified pre04 API source. All return 200, and all three fail before the new diagnostics existed. Classification: **Confirmed preexisting defect**, explicitly excluded from PR-PLAY-05 acceptance. The existing tests remain failing and unskipped; no threshold was lowered and no filler added.

Exact fixture inputs and every captured boundary are in `emission/{rich,reconcile,prepared}.json`, with corresponding `emission_pre04/` files. Exact original-test response bodies are separately in `http/entry_1..3/` and `http/fixed_1..3/`. `emission_comparison.json` makes counts directly comparable.

| Case | Fixture / prepared chars | Accepted realization chars | Local sanitize/gate debug chars | Final response/log chars | Pre04 |
|---|---:|---:|---:|---:|---|
| rich | 1218 / none | 899 | 781 | 899 | Same |
| forced reconcile | 1218 / none | 899 | 781 | 899 | Same |
| short plus prepared rich | 111 / 1218 | 111 | 1100 | 111 | Same |

These tests bypass SDK extraction and `_safe_json`: their supplied dictionaries are legacy normalized GM stubs, without a declared_claims envelope. There is no provider-generated or parsed structured envelope to count in this path. Before acceptance is the fixture text; after acceptance is the immutable realization; final response and persisted log are separately captured. They must not be called the same boundary.

## Earliest demonstrated transformations

`immutable_valid_response.run_preserve_if_valid` and its `_bounded_keep` path check structural narration units against the decision authority, preserve hard-valid units, then seal. In the rich stub, 1218 becomes 899 before final emission: the player-location/crowd sentence and townhouse/noble-colors sentence disappear. This is substantive deletion, not merely whitespace normalization. It cannot be blamed on PR-PLAY-04, whose pre04 comparison produces the same deletion. The fixture lacks declarations and is not evidence that the deleted consequential claims were authorized. This pass does not weaken that authority check.

`api_turn_support._finalize_player_facing_for_turn` then runs strip-only sanitization and the final gate. Its local `pre_gate_text_len`, `post_final_emission_gate_text_len` and reconciliation lengths show 781, while restoration of the immutable accepted response yields 899 at delivery. Thus the previous report's approximately 781 characters describes local telemetry, not the final rich emitted string. The forced-reconcile case restores accepted output, but its old debug-length assertion remains false.

In the prepared case, the initial 111-character response is accepted/sealed before the later prepared candidate is considered. The prepared 1218 characters are recognized and local sanitized/gate telemetry shows 1100, yet immutable restoration delivers 111. The existing promotion flag therefore does not establish final promotion. Earlier immutable acceptance is the responsible boundary; changing its precedence is a separate repair requiring authority review, not a length patch.

## Purpose and disposition

Test 1 protects scene establishment, successful start and response/log/reload fidelity. Test 2 protects a valid post-gate candidate from an unrelated reconciliation overwrite. Test 3 protects adoption of an upstream prepared rich candidate. Those purposes remain meaningful. An 800-character minimum is not stated by `candidate_satisfies_scene_opening_contract` or the opening contract; it is a historical test proxy for preserving richness. Length alone cannot test semantic preservation, and is especially misleading when a debug boundary differs from final emission.

No production repair was made for these preexisting emission/fixture/telemetry conflicts. Nor were meaningful assertions replaced merely to obtain green. A later bounded owner repair should use declared authorized details, assert their preservation at acceptance/delivery, and resolve prepared-candidate precedence and telemetry meaning. This report does not claim all rich fixture sentences should be authorized or preserved. PR-PLAY-05's contract/diagnostic readiness excludes these three tests explicitly.
