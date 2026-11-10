import pathlib,json,xml.etree.ElementTree as ET,re
p=pathlib.Path('artifacts/pr_play_28')
c=json.loads((p/'test_comparison.json').read_text())
new=ET.parse(p/'public_final.xml').getroot()[0].attrib
focused=ET.parse(p/'focused.xml').getroot()[0].attrib
rows=c['rows']
env=[r for r in rows if any('WinError' in ((r.get(k) or {}).get('message','')+(r.get(k) or {}).get('details','')) for k in ('baseline','current'))]
for r in env:r['classification']='environmental_failure'
c['new_regressions']=[r['test_id'] for r in rows if r['classification']=='newly_introduced_regression'];c['environmental']=[r['test_id'] for r in env]
c['resolved']=[r['test_id'] for r in rows if r['classification']=='resolved_preexisting_failure']
def norm(s):
 return re.sub(r'0x[0-9A-Fa-f]+','0xADDRESS',s)
c['changed_failure_messages']=[r['test_id'] for r in rows if r.get('baseline') and r.get('current') and r['baseline']['status']==r['current']['status']=='failure' and norm(r['baseline']['message'])!=norm(r['current']['message'])]
(p/'test_comparison.json').write_text(json.dumps(c,indent=2),encoding='utf-8')
report=f'''# PR-PLAY-28 test results

Final new tests: {new['tests']} executed, {int(new['tests'])-int(new['failures'])-int(new['errors'])} passed, {new['failures']} failed, {new['errors']} errors (public_final.xml/public_final.txt). Covers A1–A12 and B1–B12 through parameterized positive/negative selector, authorization, evaluator and real HTTP scenarios. The full public HTTP response and internal persisted evidence are both evaluated; no direct-selector substitute is used for integration.

Broader focused scope: {focused['tests']} executed, {int(focused['tests'])-int(focused['failures'])} passed, {focused['failures']} failed. Counts overlap the final new suite; do not add them as unique tests. Existing PR-PLAY-25 authority tests: 38/38. Opening-overlay adversarial tests: 22/22. Clue-knowledge: 9/9. The remaining focused failures are preexisting: 16 social-lead landing, one question-relevance, one clue idempotence. Full IDs/messages are in focused_failure_comparison.json. No assertion was changed to hide a failure.

Comparable 73-file/1,603-test scope:

- PR-PLAY-27 historical: 1,490 passed / 113 failed.
- Fresh exact pre-repair baseline: {c['baseline']}.
- Repaired existing run: {c['current']}.
- Same exact IDs: {c['exact_ids_equal']}.
- Newly introduced regressions: {len(c['new_regressions'])}.
- Resolved preexisting product failures: {len(c['resolved'])}.
- Environmental IDs: {len(env)} (details below).

The extra fresh-baseline failure versus PR-PLAY-27 is tests.test_start_campaign_api::test_start_campaign_frontier_gate_uses_journal_seed_facts_when_opening_seed_absent. It fails in unchanged game/storage.py atomic os.replace with WinError 5 on isolated temporary session.json, not in topic or evaluator logic. A changed result for this ID is environmental, not attributed to this repair. Full logs/XML retain all evidence.

Every current failure has an exact pre-repair status in test_comparison.json, including assertion messages and stack text. Address-only message differences are normalized for comparison; original strings remain intact. Relevant historical failures are **not assumed unrelated**. The social landing/idempotence failures remain directly related unresolved fixture/authority coverage: e.g. `_resolution_question_with_topic` supplies an invented runner/topic with default_world and lacks a matching owned authored source, so the preexisting source guard denies the write. The new positive fixtures supply actual NPC/topic/scene/action provenance. This pass does not weaken the guard or rewrite those historical fixtures. Other baseline social/dialogue failures remain preexisting unresolved, with no claim of causal independence.

One focused failure was outside the 1,603-ID list: `test_apply_socially_revealed_leads_twice_preserves_canonical_state` also fails with saved pre-pass functions (extra_baseline.xml/txt), because its invented resolution lacks a matching authored source. The targeted replay runs saved functions in a separate process without altering the working regression sources.

During implementation, the single metadata addition to the pinned benchmark fixture initially invalidated its manifest. This introduced 14 failed/error IDs in the first full post-run; existing_before_pin.xml/txt preserves that failure. The fix updates only world.json's manifest digest and the verifier's pinned manifest digest, with an explicit source note. File/hash verification remains mandatory. All 52 affected gameplay/harness/budget tests pass after the correction (pin_fixed.xml). An early targeted replay's controller KeyError('actions') also came from this temporary mismatch and is not classified as preexisting. Final focused/existing logs supersede the run with the missing pin update.

Live-provider request count: **0**. Pytest autouse live_model_guard denies unmocked transports; integration stubs the SDK, interpretation and expression and fails unexpected narration. `ASHEN_DISABLE_LIVE_*` flags are enabled only inside mocked tests. Provider-shaped stub records are not live requests. No models or provider settings changed.

Commands/scripts: run_baseline_complete.py runs the exact inherited test_files.json order; run_post.py runs focused_files.json then the same existing list, each with separate development/tmp/pr_play_28_* roots. Final new suite uses --basetemp=development/tmp/pr_play_28_public_final. No full-suite green claim is made. Initial interrupted baseline and failed UTF-8 patch invocation are superseded by the complete baseline and final runs; the encoding failure occurred before any production write.
'''
(p/'PR_PLAY_28_TEST_RESULTS.md').write_text(report,encoding='utf-8')
assert not c['new_regressions'],c['new_regressions']
assert new['failures']=='0' and new['errors']=='0'
verdict='''# PR-PLAY-28 final verdict

**Workstream A: A — Topic Discovery Repaired. Workstream B: A — Authority Mismatch Repaired. Overall: A / PASS for the targeted offline pass.**

1. Broad rumor failure reproduced in current real HTTP pipeline.
2. Selector required subject token overlap; plural rumors/sort did not match patrol_rumor/text. No authored category eligibility existed.
3. Explicit discovery_categories=["rumor"] plus existing source permission and answer sufficiency make the row discoverable. Only the existing runner row and its maintained campaign-fixture copy were classified.
4. Existing npc_source_permitted/authorize_npc_disclosure remain authoritative at selection, resolution and clue landing; evaluator independently rematches source evidence.
5. Broad rumor question selects patrol_rumor in the repaired real application pipeline.
6. Explicit patrol question still works.
7. Other NPC/multiple-topic tests pass without NPC-specific code.
8. Hidden/secret/unknown topics remain protected.
9. Unmet conditional disclosure policies remain denied. No dynamic quest/relationship evaluator or new partial disclosure system is claimed.
10. Category candidates select one by stable topic ID; hidden candidates excluded. Existing specific-topic ambiguity behavior remains.
11. Active NPC/conversation context is preserved; broad category questions also work independently.
12. Original clue overlay evaluator failure reproduced.
13. Primary muddy-footprints clue is authorized by patrol_rumor. Crossroads is independently supported by the authored scene discoverable and existing minimum-lead rule; the topic alone does not authorize it.
14. Evaluator supported only accepted openings and received no ordinary action/turn evidence.
15. Production defect classification: evaluator (Case B). Historical partial replay lacked complete scene/log evidence; fresh instrumented fixtures capture it, without changing campaign lifecycle rules.
16. Existing source grants, resolution, persisted log ordinal/input/turn, world events and source snapshots suffice for this bounded reconstruction. action_id is not a unique event UUID; log/turn binding is required.
17. Unsupported clues, wrong NPCs, denied/missing topic grants, invented hooks/events and absent action/scene/log evidence remain rejected.
18. Opening and ordinary-turn integrity checks remain active; unrelated overlay/inventory changes reject.
19. Mocked two-turn broad conversation completes; explicit control also completes.
20. Player receives “I've got hot stew and rumors to share.” followed by the attributed authored patrol rumor. Actual player-facing HTTP responses both pass evaluation.
21. Character/campaign/combat/conditions are unchanged; world equals normal tick plus identified events; clue overlays match source reconstruction. Restricted integration produces no clue overlay change.
22. Exact regression classifications are in TEST_RESULTS/test_comparison.json; no new product regressions established.
23. Historical failures remain unresolved; see exact scope counts in TEST_RESULTS. They are not all assumed unrelated.
24. Zero live-provider requests; no commit/push.
25. The repaired two-turn path is ready for a separately authorized bounded live validation with explicit topic metadata and complete persisted evidence. Existing broader harness/suite limitations must remain visible; this is not certification of the entire harness or game.

Remaining bounds: category metadata is opt-in; no migration of historical snapshots or arbitrary active saves. News/local events and ambiguous ellipsis are not reclassified as rumor requests. Repeated category requests do not implement topic rotation. Evaluator recognizes only the demonstrated authored social projection in addition to existing opening projection; unsupported effect families remain fail-closed.

Recommended next step: external review of this archive, then separately authorize controlled live two-turn validation using the maintained fixture. PR-PLAY-29 has not begun. Stop for external review.
'''
(p/'PR_PLAY_28_FINAL_VERDICT.md').write_text(verdict,encoding='utf-8')
print('Reports written')
