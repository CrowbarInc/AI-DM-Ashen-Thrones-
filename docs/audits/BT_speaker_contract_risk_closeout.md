# BT Speaker Contract Risk Closeout Report

Date: 2026-06-20  
Scope: BT1–BT3 closeout audit; diagnostic test-only; no runtime, golden, or telemetry changes

## Executive summary

BT delivers a **repeatable, test-only Speaker Contract Risk audit** that joins pre-speaker, post-speaker, final-emission, and replay-projection checkpoints for representative replacement/fallback families. All six measurability goals from the discovery audit are now satisfied at the test-helper layer. **BT is complete for its stated scope.** Runtime checkpoint telemetry (formerly proposed BT4) remains **deferred and not justified** by current evidence.

---

## Block inventory

### BT1 — Checkpoint / risk helper

**Files:** `tests/helpers/speaker_contract_risk.py`, `tests/helpers/post_speaker_finalize_probe.py` (reuse), `tests/test_speaker_contract_risk.py`

**Delivered:**

- Immutable `SpeakerContractObservation` with ordered checkpoints P0–P4
- Normalized text hashes and `detect_emitted_speaker_signature` at each checkpoint
- Explicit `speaker_status` (`resolved`, `neutral`, `unattributed`, `ambiguous`, `unresolved`)
- First divergence across text and speaker identity (named checkpoint or explicitly `None`)
- Component risk scoring: `D` (localization), `S` (speaker), `T` (text), `A` (attribution), capped total + band
- Stable `as_record()` JSON-like export

**Tests (BT1):** 8 focused unit tests — zero-divergence, dialogue-plan strip localization, unresolved speaker, missing owner/source, text mismatch, D-without-localization, record shape, plus 1 conditional live probe test (see skipped test below).

### BT2 — Final-emission-to-replay parity adapter

**Files:** `tests/helpers/speaker_contract_risk.py` (`observe_final_to_replay_speaker_contract`, `final_replay_parity_record`, `build_replay_projection_checkpoint`)

**Delivered:**

- Projects finalized gate output through canonical `project_turn_observation` / golden replay
- Compares P3 final text/hash/signature to P4 `final_text` / `selected_speaker_id` / source
- Explicit unavailable-replay-speaker handling (not silently equal to match)
- Golden-aligned normalization toggle for P3/P4 hash parity

**Tests (BT2):** 6 focused tests — hash parity, speaker parity, S=40 mismatch, missing replay source, T=25 text mismatch, unavailable speaker explicitness, P3/P4 checkpoint presence.

### BT3 — Replacement / fallback fixture matrix

**Files:** `tests/test_speaker_contract_risk.py` (matrix + builders), reuse of Block S/T/U fixtures, referential-clarity bundle, N4 sealed pattern, BT2 replay adapter

**Delivered:**

- Nine-family diagnostic matrix exercising local rebind, canonical rewrite, narrator-neutral, forbidden generic fallback, referential/visibility local substitution, strict-social emergency fallback, sealed replacement, live gate rebind, and replay speaker mismatch anchor
- `speaker_contract_family_risk_rows(...)` summary helper
- `speaker_contract_closeout_rows(...)` closeout helper (path, D/S/T/A, owner evidence, notes)

**Tests (BT3):** 2 tests — full matrix assertions + summary-row shape lock.

---

## Measurability confirmation

| Goal | Status | Evidence |
|------|--------|----------|
| Speaker-finalize parity measurable | **Yes** | P0/P1 checkpoints via `observe_speaker_contract`; live gate via shadow harness (`local_rebind_gate`) |
| Speaker identity preservation measurable | **Yes** | `resolved_speaker_id` + `speaker_status` at P1/P3/P4; S component scores 0/20/40 |
| Normalized text divergence measurable | **Yes** | Per-checkpoint hashes; T component; `text_parity` in family rows |
| First divergence named or explicitly absent | **Yes** | `first_divergence_checkpoint_id` + `first_divergence_layer_id`; D=15 when mismatch lacks localization |
| Final emission ↔ replay parity measurable | **Yes** | BT2 adapter; `final_replay_parity_record`; `replay_speaker_mismatch` family |
| Runtime checkpointing justified | **No** | All families observable through existing test wrappers; no production blind path demonstrated |

---

## Family metric table

Snapshot generated via `speaker_contract_closeout_rows(...)` against the BT3 matrix builders (2026-06-20).

| family | observation path | first divergence | speaker status | text parity | D | S | T | A | total | band | owner/source evidence? | notes |
|--------|------------------|------------------|----------------|-------------|---|---|---|---|-------|------|------------------------|-------|
| local_rebind | unit `enforce_emitted_speaker_with_contract` | `P1_post_speaker_finalize` | resolved | yes | 0 | 0 | 0 | 0 | 0 | low | yes | Merchant → Tavern Runner rebind; post==final |
| canonical_rewrite | unit `enforce_emitted_speaker_with_contract` | `P1_post_speaker_finalize` | resolved | yes | 0 | 0 | 0 | 0 | 0 | low | yes | Unquoted wrong speaker → canonical rewrite |
| narrator_neutral | unit enforce + `narrator_neutral` flag | `P1_post_speaker_finalize` | **neutral** | yes | 0 | 0 | 0 | 0 | 0 | low | yes | Valid neutral; S=0 by design |
| forbidden_generic_fallback | unit enforce (generic label → local rebind) | `P1_post_speaker_finalize` | resolved | yes | 0 | 0 | 0 | 0 | 0 | low | yes | `Ragged stranger` forbidden → rebind repair |
| referential_visibility_local_substitution | `apply_final_emission_gate_consumer` (no probes) | `P3_final_emission` | unattributed | no | 0 | 20 | 25 | 0 | 45 | elevated | yes | P0/P1 held equal; she→Tavern Runner at terminal layer; S=20 reflects unattributed final signature |
| local_rebind_gate | gate + shadow harness + post-speaker probes | `P1_post_speaker_finalize` | resolved | no | 0 | 0 | 25 | 0 | 25 | guarded | yes | Live Block S/T/U stack; T=25 = post→final delta without named P2 layer in observation |
| strict_social_emergency_fallback | gate + bad strict-social stub + probes | `P2_acceptance_quality_n4` | resolved | no | 0 | 0 | 10 | 0 | 10 | low | yes | `minimal_social_emergency_fallback`; named layer diverger |
| sealed_replacement | gate N4 sealed replace (synthetic P0/P1) | `P3_final_emission` | unattributed | no | 0 | 0 | 25 | **5** | 30 | guarded | partial | Non-strict path; no speaker-enforcement checkpoint; A=5 = missing enforcement owner on mismatch |
| replay_speaker_mismatch | `observe_final_to_replay_speaker_contract` (BT2) | **absent** (`null`) | resolved | yes | **15** | **40** | 0 | 0 | 55 | elevated | yes | BT2 S=40 anchor; D=15 = speaker mismatch without named checkpoint localization |

**Risk band key:** 0–19 low · 20–39 guarded · 40–69 elevated · 70–100 high

Nonzero totals in the matrix are **expected diagnostic signal**, not regressions — they mark families where text/speaker/attribution evidence is partial or intentionally mismatched.

---

## Remaining guarded risks

### Cases covered only synthetically

| Case | Limitation |
|------|------------|
| **sealed_replacement** | P0/P1 set equal manually; non-strict path never runs speaker enforcement — terminal replace only |
| **referential_visibility_local_substitution** | P0/P1 held equal; terminal substitution not captured as a named P2 probe event |
| **replay_speaker_mismatch** | Synthetic gm_output/resolution pairing; not a full gate run |

### Cases relying on test wrappers

| Wrapper | Used for |
|---------|----------|
| `install_dual_run_enforce` / `ShadowEnforceCapture` | Pre/post speaker text at enforcement boundary |
| `install_post_speaker_text_probes` | P2 layer first-divergence (strict-social path) |
| `build_finalize_stack_fixture` + stub strict-social build | Block S/T/U live gate |
| `apply_final_emission_gate_consumer` | Referential substitution (probes break substitution when combined with stub fixture) |
| `observe_final_to_replay_speaker_contract` | P3/P4 replay join |
| `monkeypatch` stubs | Emergency fallback bad-build, sealed N4 visibility noop |

### Skipped test

| Test | Reason |
|------|--------|
| `test_dialogue_plan_strip_live_fixture_when_observed` | Skips when `dialogue_plan_subtractive_strip` probe event is deferred or absent on the current branch — not a failure, branch-conditional coverage |

### Families with nonzero attribution risk (A > 0)

| Family | A | Cause |
|--------|---|-------|
| sealed_replacement | 5 | Mismatch present without `enforcement_owner` (non-strict path) |
| *(BT1 unit)* `test_missing_owner_source_increments_a` | ≥10 | Missing expected/replay source fields — documented, not in BT3 matrix |

No BT3 matrix family scores A > 0 except **sealed_replacement**. Current behavior is asserted, not patched.

---

## BT completion recommendation

### Verdict: **Complete**

BT1–BT3 satisfy the discovery audit's recommended implementation sequence. The repository now has:

1. A reusable observation + risk helper
2. A final-to-replay parity adapter
3. A replacement/fallback fixture matrix with deterministic scoring

The audit is **repeatable**: run `python -m pytest tests/test_speaker_contract_risk.py -q` and inspect `speaker_contract_family_risk_rows` / `speaker_contract_closeout_rows` output.

### If risk increases in a future cycle

| Trigger | Suggested follow-up (not BT4 unless blind path proven) |
|---------|----------------------------------------------------------|
| New replacement family ships | Add one row to BT3 matrix; no runtime change required if wrappers observe it |
| Production path lacks pre/post speaker capture | Demonstrate blind path first, then consider bounded pre/post telemetry |
| Golden replay `selected_speaker_id` diverges from emitted prose routinely | Extend BT2 protected cases; optionally add emitted-signature vs replay comparison to golden invariants |
| Post-speaker layer ordering changes | Refresh Block U probe order + BT3 live gate expectations |
| `dialogue_plan_subtractive_strip` deferred branch stabilizes | Remove skip in live probe test; add matrix row if diverger becomes stable |

### BT4 runtime telemetry: **remain deferred**

No production checkpoint gap was demonstrated. Test wrappers observe:

- Pre/post enforcement text (shadow harness)
- Post-speaker layer deltas (probes)
- Final emission text/signature (gate output)
- Replay projection (golden adapter)

Adding `stage_diff_telemetry` pre/post speaker fields would increase payload surface area without unlocking a family currently unmeasurable in tests. Revisit only if a **concrete production-only path** is identified that cannot be wrapped.

---

## Validation performed

```text
python -m pytest tests/test_speaker_contract_risk.py -q
→ 16 passed, 1 skipped

python -m pytest tests/test_block_u_finalize_stack_divergence.py tests/test_speaker_contract_risk.py -q
→ 21 passed, 1 skipped

python -m pytest --collect-only -q
→ collection OK (test_speaker_contract_risk.py: 17 tests)
```

Metric snapshot: `speaker_contract_closeout_rows(...)` over BT3 matrix builders (2026-06-20).

---

## Related documents

- Discovery audit: `docs/audits/BT_speaker_finalization_divergence_discovery.md`
- Helper: `tests/helpers/speaker_contract_risk.py`
- Tests: `tests/test_speaker_contract_risk.py`
