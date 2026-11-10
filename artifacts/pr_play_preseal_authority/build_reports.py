"""Cycle reports and canonical low-context handoff, bound to captured evidence."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ID = 'pr_play_preseal_authority'
REPORT = ROOT/'development/campaigns/product_realization'/ID
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
results = read(OUT/'test_results.json')
cases = read(OUT/'three_case_comparison.json')['cases']
turns = read(OUT/'twelve_turn_comparison.json')['turns']
performance = read(OUT/'performance.json')
assert not results['newly_failing']
assert results['added_tests_final']['passed'] == 17
assert all(t['publication_equal'] and t['scene_equal'] for t in turns)


def write(name, text):
    (REPORT/name).write_text(text.strip()+'\n', encoding='utf-8')


write('SUMMARY.md', f'''# Pre-Seal Closed-Surface Authority Repair

Milestone `{ID}`. Client date 2026-11-08. **Cycle verdict: A/PASS for this bounded repair**, subject to the independently reopened archive seal recorded in artifacts/{ID}/archive_verification.json. No broad gameplay acceptance claim.

The authoritative predecessor is `pr_play_claim_acceptance_audit`; its NEXT_STEP_DECISION and IMPLEMENTATION_OPTIONS select this exact pre-seal repair. No numbered successor was assigned. This descriptive identifier implements that authorized action; PR-PLAY-80 and AT-OPT-07 were not opened. No material discrepancy exists between the request and source recommendation.

Primary failure class: implementation. Explicit inspection restrictions were available before validation but only enforced by a downstream mutator that correctly skipped immutable text. Bounded claim recognizers missed the three claims. The repair projects the closed outcome before the first hard check, validates it normally, and seals once through the existing lifecycle.

Production files: `game/immutable_valid_response.py`, `game/referenced_surface.py`. No perception-grounding/API/provider/prompt/state-owner change was needed. New tests: `tests/test_pr_play_preseal_authority.py` (17 collected cases).

All three original unchanged HTTP reproductions pass: hidden-token pocketing, Glassport crews and four overseers are absent from publication. Hidden authority remains hidden; inventory/NPCs/record truth are not invented. Normal faction-pressure simulation still occurs exactly as on the baseline.

| Selection | Before passed/failed | After passed/failed |
|---|---:|---:|
| Established 356 | 333/23 | 336/20 |
| Expanded 381 | 358/23 | 361/20 |
| Added tests, 17 | Draft 6/11 | Final 17/0 |

The initial test draft overconstrained total world equality; both baseline and post-change traces demonstrate normal faction/event simulation. That new assertion was corrected to check no invented truth. It does not alter frozen tests or count as a production regression fix. Intermediate results remain in evidence. Final existing selection plus added tests: 398 tests, 378 passed/20 known failures; zero collection errors/skips. No newly failing assertion. Twenty existing failure identities and normalized failures match exactly.

Seven conversational HTTP controls and AT-OPT-06 controls pass. Twelve-turn before/after publication and scene outcomes are identical for all turns. Authorized clue, acquisition, resolved physical result, travel, dialogue and incidental texture precedence are protected. Acquisition/physical precedence tests exercise actual acceptance with synthetic resolver deltas; end-to-end loot persistence is not established.

Remaining limitations: closed-route coverage only; missing/stale classifications, contradictory or unmapped effects retain existing behavior with internal ambiguity diagnostics. No general English fact checker. Twelve-turn physical completion, stock jab, generic responses and trading remain inadequate. Twelve obsolete public-resolution assertions, stew mismatch, four refusal/publication failures including the portal exception, and three KeyErrors remain deferred. No full suite, held-out, live-model or Gameplay Benchmark claim. Live provider calls: **0**. No commits/pushes.
''')

write('IMPLEMENTATION.md', '''# Implementation

`game/immutable_valid_response.py`: add `_closed_surface_preparation`, integrate it in `run_preserve_if_valid` immediately before the first `_check`, and add provenance `closed_surface_authority_projection`. Already immutable inputs return unchanged before preparation or host adoption.

Eligibility requires structured `resolution.kind == investigate`, an inspection-compatible contract operation, no social resolution, and resolver-stamped `referenced_surface_authority` of authored_hidden, authored_abstract_reference or unsupported. The helper never reclassifies player/provider prose, never uses candidate keywords as eligibility, and never treats generic investigate success as acquisition.

Precedence is checked before rendering: selected `revealed_information` through the existing mechanical adapter; inspectable contents; mechanical effects including item grants; physical adjudication/physical operation; resolved travel/activation; engine publication; permitted decision mutations; other resolution state changes/world updates. Any such signal preserves the existing owner. Unmapped effects are an explicit ambiguity, not an inferred prohibition. Incidental authorized scene facts in the GM decision are not mistaken for a selected record disclosure. This is not a universal unchanged-state rejection.

The helper reuses `classification_from_resolution`, `mechanical_outcome`, and `render_referenced_surface_inspection_line`. Existing perception policy was considered: moving its whole mutator would include unrelated observation/repetition rules and violate scope. Reusing just the structured classification and renderer suffices, so `perception_grounding.py` remains unchanged. No parallel fact authority or fallback library is introduced.

`game/referenced_surface.py::render_referenced_surface_inspection_line`: hidden and unsupported outcomes share the existing neutral nonconfirming template. Classification is never relabeled. Abstract-reference rendering remains unchanged. The old hidden assertion of absence and generic INSPECT_SAFE_LINE failed actual hard checks; neither is whitelisted. Visible surroundings use the existing renderer.

For eligible outcomes, prepare a detached candidate, then run the unchanged hard validator, selected-information check, leak/structured-contract checks and perception validator. Adopt the replacement only if validation passes. A failure records the failed validation, leaves the original draft unadopted and invokes existing terminal safety through `_finish`, with effects blocked and no regeneration/sentence salvage. The injected-failure test verifies this branch.

The accepted record gets the existing digest and delivery seal. `_finish` records completion; downstream grounding still skips immutable text. The three HTTP captures verify helper-before-validator-before-seal order, attempt 1, passing hard validation, digest integrity and exact final-publication equality. No accepted text is rewritten.

Internal `closed_surface_preparation` diagnostics retain a 2,000-character original candidate preview, full length/SHA-256, initial-generation source, classified authority, bounded resolution summary, eligibility/precedence/reason, prepared text, bounded validation result, final acceptance reason and selected publication. Full raw authority is captured by cycle-owned evidence, not duplicated in runtime diagnostics. Player DTO tests verify that internal diagnostics are absent. No new provider dispatch/retry occurs.

Cycle-only production diff: artifacts/pr_play_preseal_authority/production.diff. This is relative to preserved dirty entry bytes, not Git HEAD.
''')

text = '# Three original HTTP cases: before and after\n\nUnchanged original test functions, requests and local provider stubs; original public DTO contract remains intact.\n\n'
for c in cases:
    text += f'''## {c['id']}

- Request: `{c['request']['text']}`.
- Before: {c['before_publication']}
- After publication: {c['after_publication']}
- Authority: `{c['preparation']['classification']['authority']}`; investigate handled successfully, with no clue, retrieval, transition or state delta granting the rejected claim.
- Preparation passes normal hard validation before sealing; attempt 1; immutable digest verified; accepted text equals HTTP and publication-pointer text.
- Character unchanged. World changes only factions/event_log through the same preexisting turn simulation as before; no record, NPC or acquisition authority is added. Hidden facts remain undisclosed.
- Original unchanged reproduction: **PASS**. No obsolete stopping assertion remains in this case. Other tests in the historical selection still fail obsolete public-resolution assertions; those tests were not edited.

'''
text += 'Machine evidence: artifacts/pr_play_preseal_authority/three_case_comparison.json. Full before/after requests, raw pre-DTO payloads, authority, state and nested publication/validation traces remain under before/ and after/.\n'
write('THREE_CASE_COMPARISON.md', text)

write('PRECEDENCE_VERIFICATION.md', '''# Precedence verification

| Authority / control | Evidence | Result |
|---|---|---|
| Authorized notice clue | Added selected-clue test with stale hidden classification; existing recorded_handoff HTTP and T05/T09 | Preserved without requiring state mutation |
| Authorized acquisition | Added acceptance test with explicit items_added silver-key grant and stale hidden classification; existing mechanical controls | Narration preserved and hard-valid; synthetic resolver delta, no end-to-end loot claim |
| Resolved physical action | Added acceptance test using actual physical_operation/physical_adjudication fields with stale restriction | Actual resolved result retained |
| Genuine travel | Added travel test; existing HTTP genuine_travel; T11 | Old Milestone arrival retained |
| NPC dialogue | Three added opinion/uncertainty/question cases; existing seven HTTP controls including repeat/follow-up | Unchanged |
| Harmless improvisation | Added rain observation; existing immutable/mechanical quiet-exploration controls | Accepted outside closed inspection |
| Hidden protection | Three unit cases, three added HTTP cases and original token HTTP | No token existence/location/acquisition confirmation; no hidden reveal/state effect |
| Immutable acceptance | Added no-repreparation and downstream-grounding identity checks; all three real HTTP traces/digests | Normal validation precedes seal; accepted/final text identical |
| Failed replacement validation | Injected normal hard-check failure with regeneration spy | Terminal safety, no retry, effects blocked |
| Missing classification | Added unclassified investigate case | Existing behavior retained, no prose-derived eligibility |

Seventeen new tests pass. Existing post-NPC HTTP controls: 7/7; all selected AT-OPT-06 controls pass. Relevant collected nodes/outcomes are in artifacts/pr_play_preseal_authority/precedence_results.json. These are bounded implementation/regression controls, not independent held-out generalization. Existing mixed refusal/publication defects are unchanged and remain deferred.
''')

text = '''# Regression results

Before production edits: branch/HEAD/dirty status saved; all 1,294 predecessor source-manifest hashes match. Two historical selections rerun unchanged with fail-closed nonloopback network guards, provider disable flags, and existing storage isolation. Original three defects reproduce in the first selection. No reset/reconstruction was used.

| Selection | Before | After | Collection errors/skips |
|---|---:|---:|---:|
| Main, 235 | 219 pass / 16 fail | 222 pass / 13 fail | 0/0 |
| Authority, 146 (121 established + 25 mechanical) | 139/7 | 139/7 | 0/0 |
| Established, 356 | 333/23 | 336/20 | 0/0 |
| Expanded, 381 | 358/23 | 361/20 | 0/0 |
| Added final, 17 | See draft note | 17/0 | 0/0 |
| Existing + added, 398 | — | 378/20 | 0/0 |

Newly failing assertions: **none**. Resolved identities (all original HTTP publication defects):

'''
text += '\n'.join('- `'+n+'`' for n in results['resolved'])
text += '\n\nUnchanged known failures:\n\n' + '\n'.join('- `'+n+'`' for n in results['unchanged_known_failures'])
text += '''

All twenty retained failures have identical assertion/raise identities and normalized diagnostics. Only generated turn_id UUIDs and hexadecimal object addresses are normalized; full raw tracebacks remain intact. Known categories: twelve obsolete public-resolution assertions, one stew mismatch, four authority/refusal/publication nodes (including the known AnyIO portal exception), three unrelated KeyErrors. No new failure is declared obsolete to excuse a regression.

Added-test draft: 6/11 before implementation; first after run 14/3. The three new HTTP assertions incorrectly required total world equality, while both unchanged baseline and after captures show normal faction pressure/event-log updates. The final assertions compare every other world key, character, event content, resolution, hidden state and publication. Final 17/17. Tests were authored during this repair; no frozen fixture/old assertion was edited. All intermediate commands, JUnit, traces and source draft remain available; draft/final counts are not an exact same-test-source improvement claim.

Commands from repository root, .venv/Scripts/python.exe:

```powershell
.\\.venv\\Scripts\\python.exe artifacts/pr_play_preseal_authority/run_audit.py before
.\\.venv\\Scripts\\python.exe artifacts/pr_play_preseal_authority/run_controls.py before
.\\.venv\\Scripts\\python.exe artifacts/pr_play_preseal_authority/run_audit.py after
.\\.venv\\Scripts\\python.exe artifacts/pr_play_preseal_authority/run_controls.py after
.\\.venv\\Scripts\\python.exe artifacts/pr_play_preseal_authority/run_focused.py focused_final
.\\.venv\\Scripts\\python.exe artifacts/pr_play_preseal_authority/run_sequence.py before
.\\.venv\\Scripts\\python.exe artifacts/pr_play_preseal_authority/run_sequence.py after
.\\.venv\\Scripts\\python.exe artifacts/pr_play_preseal_authority/analyze_results.py
.\\.venv\\Scripts\\python.exe artifacts/pr_play_preseal_authority/compare_assertions.py
```

Exact pytest module/node selections, flags, basetemp, collected IDs and executable are in each run's command.json/collected_nodes.json; copied from the predecessor selection without changing old tests. The three original HTTP cases are part of main; controls include conversational handoff, immutable/mechanical authority, negative controls and AT-OPT-06 transition tests. Scripts use separate cycle outputs and isolated storage and execute sequentially. Each execution integrity report records zero protected-file modifications and external network attempts. Live provider calls: **0**. No full-suite, live-model or Gameplay Benchmark run.

Machine results: test_results.json and assertion_comparison.json under artifacts/pr_play_preseal_authority/.
'''
write('REGRESSION_RESULTS.md', text)

text = '# Twelve-turn comparison\n\nThe established provider-free run_sequence.py harness was copied with only cycle output redirection; all twelve utterances and initialization remain unchanged. Both runs completed HTTP 200 for all turns with no errors and zero provider requests. All twelve publication strings and scene outcomes match exactly. This preserves the existing experience; it does not make that experience playable.\n\n| Turn | After publication | Before/after |\n|---|---|---|\n'
for t in turns:
    text += f"| {t['id']} | {t['after'].replace('|', '/')} | Identical |\n"
text += '''
T04 remains local without movement, clue disclosure or actual touching completion. T05 still publishes the authorized northwest patrol clue and the unrelated stock jab. T06 declines unsupported copying, with inventory unchanged. T09 recalls previously disclosed clue content without an NPC addressee. T11 travels to Old Milestone; T12 remains an operational refusal. Seven separate unchanged HTTP controls preserve genuine repetition/follow-up, unknown destination and hidden protection.

T01/T07 disabled narration, T08 generic action wording, T02's unhelpful answer, trading and physical completion remain deficient. No broad NPC/world improvisation was added. Evidence: before/twelve_turn and after/twelve_turn, plus twelve_turn_comparison.json under artifacts/pr_play_preseal_authority/.
'''
write('TWELVE_TURN_COMPARISON.md', text)

write('PERFORMANCE.md', f'''# Performance and provider impact

Live provider calls: **0**. Added dispatches: 0. Added retries: 0. Added standing prompt tokens: 0. No model/interface/budget change, claim-extraction call, context rebuild or per-sentence processing was introduced. Eligible outcomes reuse one existing local renderer and the same normal hard validation rather than adding a validator pass. Failed deterministic preparation terminates safely without regeneration.

Six eligible helper calls captured during actual local HTTP regression tests took {min(performance['helper_samples_ms']):.4f}–{max(performance['helper_samples_ms']):.4f} ms, median {performance['helper_median_ms']:.5f} ms. Timing covers predicate and rendering, excluding instrumentation copying and existing validation. It is a small local sample, not a throughput/provider-latency benchmark or complete lifecycle-overhead estimate. Runtime adds a detached candidate copy and bounded internal diagnostics for eligible candidates. No expensive benchmark was needed.

Twelve-turn runs each report zero provider requests/tokens and four entries into the existing disabled-provider wrapper; those entries are not live calls. The reused harness's preflight budget probe admits a local stub with synthetic usage; it is not a live-provider bill. No avoided-generation savings are claimed; this repair does not remove initial generation. Machine samples: artifacts/{ID}/performance.json.
''')

write('NEXT_STEP_DECISION.md', '''# Next step decision

**Acceptance recommendation: A/PASS for the bounded pre-seal closed-inspection repair**, after the archive-verification seal succeeds. The three real HTTP publication defects are corrected; hard validation, immutable identity, authority precedence and targeted state consistency hold, with no new regression. The game remains substantially incomplete.

Exactly one proposed next action: remove the unrelated stock jab appended after authorized notice-board clue publication, preserving selected clue delivery and accepted-response identity. This is a future narrowly authorized repair; do not begin it in this cycle.

Remaining authority limitation: classification must already be resolver-stamped and closed. Missing classifications, other routes, contradictory readable grants or unmapped effects retain existing authority behavior; diagnostic ambiguity is recorded for closed classified cases. There is no universal consequential-claim detector or proof of arbitrary English completeness. Synthetic granted-item/physical precedence tests do not establish a production loot resolver or broad physical gameplay.

Deferred: physical completion T04/T06; generic T01/T07/T08 and trading; general NPC/world improvisation; twelve obsolete public-resolution assertions; stew/refusal/publication-pointer defects and AnyIO portal exception; three unrelated KeyErrors; historical provenance, full-suite/held-out/live-model/Gameplay Benchmark work. PR-PLAY-80, AT-OPT-07 and live play are not opened. Stop after this cycle's verification and handoff.
''')

before = read(OUT/'before_source_manifest.json')
after = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
new_test = 'tests/test_pr_play_preseal_authority.py'
after[new_test] = hashlib.sha256((ROOT/new_test).read_bytes()).hexdigest()
(OUT/'after_source_manifest.json').write_text(json.dumps(after, indent=2), encoding='utf-8')
changed = [p for p in before if before[p] != after[p]]
assert sorted(changed) == ['game/immutable_valid_response.py', 'game/referenced_surface.py'], changed
(OUT/'source_hashes.json').write_text(json.dumps({p: {'before': before[p], 'after': after[p]} for p in [
    'game/immutable_valid_response.py', 'game/perception_grounding.py', 'game/referenced_surface.py', 'game/api.py']}, indent=2), encoding='utf-8')
frozen = [p for p in before if p.startswith('tests/fixtures/') or p.startswith('data/validation/')]
assert all(before[p] == after[p] for p in frozen)
(OUT/'frozen_integrity.json').write_text(json.dumps({'checked': len(frozen), 'changed': [], 'paths': frozen}, indent=2), encoding='utf-8')
write('INTEGRITY.md', f'''# Integrity

Milestone `{ID}`. Branch `feature/product-realization`; HEAD `d40f1ed198236c604085f1c842ead267a8104ce2`. Substantial preexisting dirty work preserved. Entry Git status, production bytes and NEXT_SESSION bytes retained before editing. All 1,294 predecessor manifest hashes matched. No commit/push/reset/clean/stash/revert/historical checkout; no frozen fixture overwrite.

Before/after source manifests and source_hashes.json distinguish this cycle from existing dirty edits. Exactly two preexisting manifest paths changed: game/immutable_valid_response.py and game/referenced_surface.py. game/perception_grounding.py and game/api.py are byte-identical to entry. One test module added with 17 cases. {len(frozen)} frozen/validation input paths hash-identical. Cycle-only diff is production.diff; Git HEAD diff also contains older work and is not claimed as this cycle's patch. All test runs report no protected-source/data/fixture mutation and no network attempt.

Reports created: SUMMARY.md, IMPLEMENTATION.md, THREE_CASE_COMPARISON.md, PRECEDENCE_VERIFICATION.md, REGRESSION_RESULTS.md, TWELVE_TURN_COMPARISON.md, PERFORMANCE.md, NEXT_STEP_DECISION.md, INTEGRITY.md under development/campaigns/product_realization/{ID}/. Machine evidence, before/after manifests, JUnit/failures/commands, full raw captures, compact comparisons, test draft/intermediate results and cycle scripts live under artifacts/{ID}/. No unrelated module was repaired.

NEXT_SESSION is prepended from retained entry bytes; all historical entries survive as an exact suffix. Standard tools/build_review_handoff.py generates the review Markdown, manifest and ZIP using explicit cycle config. Existing dated archives are hash-checked and preserved. The new stable and New York timestamped archive are reopened and CRC-checked; internal milestone, all nine reports, comparison/results, handoff suffix and member/source/evidence hashes are verified. Final verification outputs are external to avoid circular self-hashing.

Archive SHA-256 and exact final path: artifacts/{ID}/archive_sha256.txt. Verification status, member checks, stable/dated equality, source preservation, frozen integrity and handoff verification: archive_verification.json. These files are the final seal authority; do not infer archive success from this protocol description alone.
''')

entry = (OUT/'before/docs/NEXT_SESSION.md').read_bytes()
header = f'''# NEXT_SESSION — PR-PLAY Pre-Seal Closed-Surface Authority Repair (2026-11-08)

**A/PASS for the bounded repair. The game remains incomplete.** Milestone `{ID}`. Branch feature/product-realization; HEAD d40f1ed198236c604085f1c842ead267a8104ce2. Existing dirty work preserved. Production changes only immutable_valid_response.py and referenced_surface.py; 17 tests added. No commits/pushes. Live provider calls: **0**.

Three original unchanged HTTP cases now pass: no hidden-token pocketing, Glassport crews or four overseers published. Resolver-stamped hidden/abstract/unsupported investigate outcomes are prepared before normal hard validation and sealing. Hidden authority retained; selected clues, resolved effects/acquisition/travel and dialogue take precedence. Failed preparation validation uses existing terminal safety without retry. Accepted digests/final identity verified; no invented state. Missing/stale classification and unmapped effects remain outside this bounded guarantee.

Same 356 tests: 333/23 before → 336/20 after; expanded 381: 358/23 → 361/20. Added tests 17/17, combined 378/20 of 398. Zero collection errors/skips; zero new failures. Twenty known assertion identities/normalized failures unchanged. Seven conversational HTTP controls pass. Full twelve-turn harness rerun before/after: all published strings and scene outcomes identical. T04/T06 lack physical completion; T05 stock jab, T01/T07/T08 generic responses, trading and other gameplay limitations remain. No full-suite/held-out/live-model/Gameplay Benchmark acceptance claim.

**Exactly one proposed next action: remove the unrelated stock jab after authorized notice-board clue publication**, preserving clue delivery and immutable identity. Do not begin automatically. Defer obsolete public-resolution tests, stew/refusal/pointer defects, portal exception and unrelated KeyErrors. Do not reopen historical provenance, PR-PLAY-80, AT-OPT-07 or live play.

Reports: development/campaigns/product_realization/{ID}/. Evidence: artifacts/{ID}/. Minimum reading: SUMMARY, IMPLEMENTATION, THREE_CASE_COMPARISON, REGRESSION_RESULTS, NEXT_STEP_DECISION; test_results.json, three_case_comparison.json, precedence_results.json, twelve_turn_comparison.json. Final archive path/hash and independently reopened verification: archive_sha256.txt and archive_verification.json. Review export: handoff/CURRENT_REVIEW.md and fresh stable/dated ZIP.

---

'''.encode('utf-8')
(ROOT/'docs/NEXT_SESSION.md').write_bytes(header+entry)
print(json.dumps({'reports': 9, 'changed_source': changed, 'new_tests': 17, 'frozen_unchanged': len(frozen), 'handoff_history_preserved': True}))
