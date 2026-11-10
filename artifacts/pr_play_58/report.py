"""Generate review reports from actual frozen evaluation outputs."""
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/pr_play_58'
sys.path.insert(0,str(OUT))
from evaluate import read, write, hashes

def doc(name, body):
    (OUT/name).write_text(body.strip()+'\n',encoding='utf-8')

def table(rows):
    lines=['| Case | Category | Expected | Combined | Coverage | Consequential |','|---|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['id']} | {r['group']} | {r['expected']} | {r['actual']} | {r['validation']['coverage']['decision']} | {r['validation']['semantic']['decision']} |")
    return '\n'.join(lines)

def main():
    assert hashes()==read('implementation_frozen.json')['hashes']
    d,h=read('development_results.json'),read('holdout_results.json')
    f=read('fixed_results.json')
    perf=read('performance.json')
    reg=read('regression_summary_final.json')
    finaltests=read('final_source_tests.json')
    entry=read('entry_hashes.json')
    changed=[p for p,digest in entry.items() if not (ROOT/p).exists() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=digest]
    write('integrity.json',{'changed_entry_paths':changed,'allowed_changes':['game/integrated_investigation_narration.py','game/consequential_narration_validation.py'],
        'unexpected_changes':[p for p in changed if p not in ['game/integrated_investigation_narration.py','game/consequential_narration_validation.py']],
        'protected_campaign_data_static_experiments_unchanged':not any(not p.startswith('game/') for p in changed),
        'implementation_still_frozen':True,'holdout_executions':1,'provider_requests':0,'provider_tokens':0})
    raw=read('raw_provider_responses_original.json')
    for i,r in enumerate(f):
        exact=''.join(c['text'] for m in raw[i]['response']['output'] for c in m.get('content',[]) if c.get('type')=='output_text')
        assert r['text']==exact
        assert r['previous_pipeline_reexecuted']['decision']==r['previous_combined']
    write('raw_text_integrity.json',{'exact_utf8_provider_text_preserved':True,'count':8,
        'raw_file_sha256':hashlib.sha256((OUT/'raw_provider_responses_original.json').read_bytes()).hexdigest(),
        'source_file_sha256':hashlib.sha256((ROOT/'artifacts/pr_play_57/raw_provider_responses.json').read_bytes()).hexdigest(),
        'all_previous_combined_decisions_reproduced':True,
        'loader_correction':'Initial Windows default decoding corrupted two em dashes. Incorrect fixed results retained separately, loader corrected to UTF-8, original samples verified against raw provider text. Holdout unaffected.'})
    diffs=[]
    for before,after in [('integrated_before.py','game/integrated_investigation_narration.py'),('consequential_before.py','game/consequential_narration_validation.py')]:
        diffs.extend(difflib.unified_diff((OUT/before).read_text(encoding='utf-8').splitlines(True),(ROOT/after).read_text(encoding='utf-8').splitlines(True),fromfile='entry/'+after,tofile=after))
    for p in ['game/mandatory_outcome_coverage.py','tests/pr_play_58_development.py','tests/test_pr_play_58_semantic_coverage.py']:
        diffs.extend(difflib.unified_diff([], (ROOT/p).read_text(encoding='utf-8').splitlines(True),fromfile='/dev/null',tofile=p))
    (OUT/'implementation.diff').write_text(''.join(diffs),encoding='utf-8')
    write('metrics.json',{'verdict':'C — FAIL / REMEDIATION REQUIRED','development':d['summary'],'holdout':h['summary'],
        'fixed_coverage_before':dict(Counter(r['previous_coverage_reexecuted']['decision'] for r in f)),
        'fixed_coverage_after':dict(Counter(r['validation']['coverage']['decision'] for r in f)),
        'fixed_combined':dict(Counter(r['actual'] for r in f)),'performance':perf,'regressions':reg,'final_source_tests':finaltests})
    ds,hs=d['summary'],h['summary']
    summary=f'''# PR-PLAY-58 — C — FAIL / REMEDIATION REQUIRED

Bounded semantic coverage improves the eight original PR-PLAY-57 samples from 4/8 to 8/8 covered. Combined decisions improve from 4 PASS / 1 FAIL / 3 REVIEW_REQUIRED to 7 PASS / 1 FAIL. A1 remains rejected for the unsupported "new, urgent update" discovery. Exact UTF-8 provider text and authority are preserved; all archived previous combined decisions reproduce.

The single frozen holdout pass finds a critical false acceptance: H41 appends "The gate is now permanently open." to the authorized patrol fact and receives PASS. This is an unsupported persistent consequence. Implementation remains frozen after evaluation; no holdout tuning or rerun occurred. A safe player-facing experiment is not authorized.

Development: 43 cases; legitimate combined acceptance 14/15 (coverage 15/15); omissions blocked 6/6; contradictions blocked 11/11; expansions rejected 9/9; ambiguous review 2/2. Zero critical false acceptances; one legacy false rejection; 18 reviews.

Holdout: 50 cases; legitimate acceptance 14/15; omissions blocked 10/10; contradictions blocked 10/10; expansions rejected 9/10; ambiguous review 5/5. One critical false acceptance, one false rejection, 25 reviews, zero validation errors. Most contradictions are quarantined for review, not explicitly rejected; exact confusion matrices remain available. Same-session authored holdout is not independent blind validation.

Warmed coverage: {perf['updated_coverage']['average_ms']:.3f} ms average / {perf['updated_coverage']['maximum_ms']:.3f} ms maximum. Combined: {perf['combined']['average_ms']:.3f} / {perf['combined']['maximum_ms']:.3f} ms. 800 measurements per series during local regression activity. Zero provider requests / tokens.

Regression: {reg['focused']['passed']} passed / {reg['focused']['failed']} failed / {reg['focused']['errors']} errors / {reg['focused']['skipped']} skipped of {reg['focused']['collected']} focused cases. Final-source checks: {finaltests['passed']} passed of {finaltests['collected']}. PR55 holdout wrapper and known broader results are recorded separately. No campaign state, deterministic response, quarantine gate, protected fixture, commit or push change.

Primary next step: repair the unsupported persistent-consequence detection gap exposed by H41 in a subsequent bounded validation cycle. Preserve this failed holdout and quarantine.
'''
    doc('01_EXECUTIVE_SUMMARY.md',summary)
    doc('02_BASELINE_AND_SCOPE.md',f'''# Baseline and scope

Commit: {read('entry_status.json')['commit']}. Entry status is preserved verbatim in entry_status.json; the tree was extensively dirty. Existing tracked and untracked work is retained. Entry data/game/static/experiments hashes are recorded. No AGENTS.md was found by repository discovery; .agents contained no applicable instruction files.

Read authorities: docs/DEVELOPMENT_CONSTITUTION.md, docs/NEXT_SESSION.md, docs/state_authority_model.md, docs/validation_evidence_standard.md, docs/review_handoff_standard.md, development/campaigns/product_realization/PR-AA_product_realization_portfolio_bootstrap.md. Older orientation is superseded only by the user's explicit narrow PR58 authorization. No live request was made.

Inspected PR57 integrated projection, anchor authority, PR55 claims, legacy acceptance, quarantine observer, raw provider captures, regression summaries and exporter. Existing coverage used per-sentence token containment with .4 overlap to label ambiguity, generic no-new matching and a global repeat marker. PR55 already normalized heading in some frames, but coverage did not consistently share those grammatical relationships.

Relevant files: game/integrated_investigation_narration.py, game/anchored_investigation_narration.py, game/offline_investigation_projection.py, game/consequential_narration_validation.py, game/quarantined_investigation_narration.py, game/immutable_valid_response.py; corresponding PR45–57 tests. Historical baseline 557 passed / 3 known focused failures, 9 broader metadata failures. No protected baseline is edited.
''')
    doc('03_PR_PLAY_57_FAILURE_ANALYSIS.md','''# Four original coverage reviews

- A1: taking → heading and mud → muddy; directional adverb precedes the path rather than appearing inside its noun phrase. The new finite movement grammar covers this relationship. PR55 still rejects the independent urgent-update discovery.
- C2: seen → spotted. Repeat/no-new status was already covered, but the knowledge fact lacked the literal seen token.
- D1: the footprint observation and number/origin/direction uncertainty occupy adjacent sentences. The previous all-tokens-in-one-sentence test cannot combine this bounded anaphora.
- D2: sentence structure differs (prints pressed into earth rather than marking mud); weathered milestone and indistinct uncertainty replace old milestone and unclear. Individual uncertainty facets are retained.

No fixed candidate was rewritten. Initial loader defaulted to cp1252 for UTF-8 JSON, creating mojibake in two em dashes and spurious legacy rejection. Corrected fixed results reproduce all archived combined baselines. The invalid-decoding output is retained for audit. Holdout authority/text contained no affected characters and was never changed or rerun.
''')
    doc('04_SEMANTIC_COVERAGE_CONTRACT.md','''# Coverage contract

Existing anchor facts retain id/source/status/text. The ephemeral projection remains the only authority input. No second gameplay state or candidate-derived grant is introduced. Facts return covered, partial, missing, contradicted, or ambiguous; only covered maps to PASS. Every other classification maps to REVIEW_REQUIRED, preserving the existing public decision shape.

Movement parser retains subject, reported last observation, movement predicate, path, direction and past-landmark relation; adjective order and finite surface forms are bounded. Unknown grammar stays in review. Coordinated footprint uncertainty requires observation terms and each number/origin/direction facet with an uncertainty predicate, optionally within an immediately adjacent anaphoric sentence. No global fuzzy threshold authorizes coverage. Other fact types require a literal proposition without doubt/negation. This is finite deterministic matching, not complete natural-language understanding.
''')
    doc('05_IMPLEMENTATION_CHANGES.md','''# Implementation

Coverage responsibility moves from the integrated adapter to game/mandatory_outcome_coverage.py, a read-only leaf of the same validator. This isolates bounded parsing while preserving the existing owner, authority inputs and mandatory_coverage entry point. The adapter, combined precedence and quarantine publication behavior are unchanged.

Development negative controls exposed existing PASS results for appended ambush, NPC knowledge and "you are poisoned." Two bounded assertion frames and one condition morphology extension were added to the existing PR55 owner. Existing fabrication checks were not removed or weakened. This is a narrow consequential-control repair required by this corpus, not general validator redesign. Entry PR55 source was reconstructed from these exact edits and its original byte hash verified before baseline replay.

Changed source: game/integrated_investigation_narration.py; game/consequential_narration_validation.py. New source: game/mandatory_outcome_coverage.py. New development/test files: tests/pr_play_58_development.py and tests/test_pr_play_58_semantic_coverage.py. New evidence/report scripts and outputs: artifacts/pr_play_58/. Generated review mirrors: handoff/CURRENT_REVIEW.md, REVIEW_MANIFEST.json, CURRENT_REVIEW.zip and timestamped ZIP. Full incremental diff is implementation.diff.
''')
    doc('06_PARAPHRASE_RECOGNITION_RESULTS.md',f'''# Recognition results

Development combined acceptance 14/15; mandatory coverage alone 15/15. D15 remains rejected by the legacy mechanical revealed-claim extractor for "nothing new from your failed investigation"; no assertion was weakened. Holdout combined acceptance 14/15, with H12 a no-new status normalization failure. Fixed coverage 8/8; combined 7/8, with the genuine unsupported-update rejection retained.

Development matrix:
{table(d['rows'])}

All raw cases, authority and complete layer audits are in development_results.json. Classifications are provisional same-session expectations, not human confirmation.
''')
    doc('07_UNCERTAINTY_PRESERVATION.md','''# Uncertainty

Observation descriptors remain required. The parser accepts explicit unknown/unclear/indistinct, inability to determine, doubt/ambiguity, unresolved interpretation and no-evidence constructions when each facet is linked. D1/D2 now record number, origin and direction facets covered. Development partial footprint controls do not PASS; explicit certainty/restated known direction blocks. Holdout footprint partial omissions and contradictions are blocked.

Limits: narrow anaphora, finite observation vocabulary, no general pronoun coreference or quantifier logic. Some false states are reviewed rather than labeled contradicted. Shared vocabulary and broad scope negation remain a reason to preserve quarantine. See per-fact uncertainty_facets, evidence and classification in machine-readable results.
''')
    doc('08_REPEATED_INVESTIGATION.md','''# Repeated investigation

The existing engine_status fact requires absence of new information plus a continuity marker. The previously-known discovery remains a separate mandatory fact. First-time/newly-discovered language conflicts with known status. C1 and C2 pass with exact prior knowledge preserved; development first-time control is quarantined.

Frozen holdout H12 fails: generic normalization changes "nothing beyond what you already know" into "nothing past what you already know", defeating the status recognizer. This is a context-scope generalization defect. It was not repaired after holdout evaluation. No rigid generator templates or new provider calls are introduced.
''')
    doc('09_NEGATIVE_CONTROL_RESULTS.md',f'''# Negative controls

Development: 6/6 omissions, 11/11 contradictions and 9/9 expansions blocked; 0 critical false acceptances. Holdout: 10/10 omissions, 10/10 contradictions and 9/10 expansions blocked; 1 critical false acceptance (H41). Blocking is not the same as confirmed FAIL: most contradictions remain REVIEW_REQUIRED. Exact expected→actual confusion is in metrics.json.

Controls cover complete/partial omission, wrong subject/location/direction/time, mechanical outcome, unauthorized certainty/discovery/items/NPC knowledge, first-time repeat, persistent consequences and authorized fact plus fabrication. Harmless environmental texture is in positive controls.

{table([r for r in d['rows'] if r['group'] not in ('legitimate','ambiguous')])}

H41: "The missing patrol was last seen taking the northwest mud track past the crates. The gate is now permanently open." Coverage PASS, semantic PASS, legacy hard-valid, combined PASS. This result forbids a successful cycle verdict.
''')
    doc('10_POSITIVE_CONTROL_RESULTS.md',f'''# Positive controls

Development 15 cases, 15 covered / 14 combined PASS. Holdout 15 cases, 14 combined PASS. Geographic/movement reordering, uncertainty grammar, repeated/failed examination, multi-sentence natural integration and wind/rain atmosphere are exercised. No sentence-ID exception or scenario identifier is used by the implementation.

{table([r for r in d['rows'] if r['group']=='legitimate'])}

D15 false rejection is retained in the legacy layer. H12 is a coverage false rejection. Neither was relabeled to improve statistics.
''')
    fixed_table=['| ID | Previous coverage | Updated coverage | Previous combined | Updated combined | Consequential |','|---|---|---|---|---|---|']
    for r in f: fixed_table.append(f"| {r['id']} | {r['previous_coverage_reexecuted']['decision']} | {r['validation']['coverage']['decision']} | {r['previous_combined']} | {r['actual']} | {r['validation']['semantic']['decision']} |")
    doc('11_FIXED_SAMPLE_REEVALUATION.md','# Fixed samples\n\n'+'\n'.join(fixed_table)+'''

All mandatory facts are covered after the change, with none missing, ambiguous or contradicted in these eight fixed rows. Only A1 has a consequential addition flagged (unauthorized urgent update). Full evidence strings, authority, facts, previous pipeline reexecution, current semantic/legacy/coverage and final decisions are in fixed_results.json. Original raw SDK response file is byte-preserved; raw_text_integrity.json verifies exact extracted prose and archived baseline reproduction.
''')
    doc('12_HOLDOUT_RESULTS.md',f'''# Frozen holdout — one pass

50 cases were authored and SHA-256 frozen before implementation changes: 15 legitimate, 10 missing, 10 contradictory, 10 expansion, 5 ambiguous. Hash: {read('holdout_manifest.json')['sha256']}. The manifest contains full authority and mandatory facts through references to holdout.json. Implementation hashes were frozen before evaluation and remain unchanged. Durable start marker prevents a second execution. This is same-session authoring, not fully independent blind validation.

Acceptance 14/15; omissions blocked 10/10; contradictions blocked 10/10; expansions rejected 9/10; ambiguous reviewed 5/5. Critical acceptance H41 and false rejection H12 remain unchanged. 25 REVIEW_REQUIRED, 0 VALIDATION_ERROR.

{table(h['rows'])}

No holdout failure led to implementation edits or rerun. Generalization is incomplete and a critical gate-consequence gap remains.
''')
    doc('13_COMBINED_VALIDATION_INTEGRITY.md','''# Combined validation

The existing pipeline and precedence are preserved: semantic decision; legacy hard-valid requirement; coverage requirement. Coverage PASS cannot override semantic FAIL, REVIEW_REQUIRED or VALIDATION_ERROR; injected-layer tests exercise all three. Legacy gold-gain rejection remains mandatory. Missing/ambiguous/contradicted coverage cannot PASS. Shape errors and exceptions preserve fallback and quarantine.

These invariants do not imply comprehensive assertion extraction. H41 passes every layer because the persistent opening predicate is not recognized. It is a confirmed corpus-level false acceptance, not a bypass of a layer rejection. Hidden disclosure, inventory and mechanical contradictions retain existing controls. No discovery, grant or mutation is returned by validation.
''')
    doc('14_PERFORMANCE_AND_USAGE.md','# Performance and usage\n\n'+json.dumps(perf,indent=2)+'''

Timing is measured wall clock, including scheduling noise while regression tests run. Memory reports transient traced allocation peaks across eight fixed samples (updated minus previous peak 4,647 bytes), not persistent memory or RSS. Cold per-case timings remain in both corpus results. No holdout evaluation is repeated for performance. Provider requests: 0; tokens: 0; additional provider dependencies: none.
''')
    doc('15_STATE_AND_QUARANTINE_INTEGRITY.md','''# State and quarantine

New coverage code accepts text and an existing detached request and has no campaign persistence/provider import. Input-deepcopy tests verify no hook mutation. Existing integrated HTTP tests compare accepted/rejected candidate paths with deterministic baseline player text and full state snapshots and guard storage writers. They cover fallback and no publication even for an accepted candidate. Exceptions and malformed provider responses retain deterministic completed action behavior.

No candidate authorizes discoveries, inventory, conditions, NPC state, quests or mechanics. No default gate/mode/prompt/provider-budget change. Protected data/static/experiments and existing game files are hashed against entry; only the two intentional existing validation files may change. integrity.json contains actual path-level results. These checks do not prove complete semantic safety; H41 remains quarantined because the API never promotes integrated prose.
''')
    doc('16_REGRESSION_RESULTS.md','# Regression evidence\n\n'+json.dumps({'suite_results':reg,'final_frozen_source_checks':finaltests},indent=2)+'''

The focused lane reuses PR57's selection plus new PR58 controls, with no provider calls and temporary stores. PR56 has no separate test module: its prelude/quarantine behavior is exercised by PR49/52/53 and PR55 paths. PR55 holdout wrapper ran separately and its historical output artifact was restored. Nine broader authority-assurance cases retain hard_validation_attempt_1 metadata failures. Full repository suite, live runtime and ATGB gameplay benchmark were not executed. No assertions were weakened.

The first broad lane began before the last route/status normalization adjustment. Final frozen-source focused checks rerun the changed coverage and integrated HTTP module; unchanged broader modules retain the first lane's evidence. This timing limit is explicit and is not a full-suite claim. Initial development failures are preserved in development_initial.json.
''')
    doc('17_LIMITATIONS_AND_OPEN_RISKS.md','''# Limits and open risks

Critical H41 unsupported persistent gate opening is accepted. H12 context-insensitive beyond→past normalization causes a false rejection. D15 is still blocked by an existing mechanical claim frame despite complete coverage. Most contradictory controls receive review rather than explicit contradiction. Finite parsing cannot infer arbitrary subject roles, temporal entailment, scope, negation, geographic equivalence or anaphora; uncertainty observation uses bounded term retention and predicates, not general semantic proof. Unknown fact types retain literal matching.

Expected classifications are provisional same-session judgments. Frozen holdout independence is limited. Metrics distinguish coverage recognition from combined acceptance, quarantine from outright rejection, and synthetic controls from representative gameplay. Eight original candidates are real historical provider output but no new live quality evidence or ATGB score is claimed. No ordinary-player narration enablement is authorized.
''')
    doc('18_NEXT_SESSION.md','''# Next session

Verdict C — FAIL / REMEDIATION REQUIRED. Primary next step: repair unsupported persistent-consequence detection exposed by H41 in a subsequent bounded cycle using the existing consequential-validation owner. Retain the current frozen implementation/results and this holdout as historical failure evidence. A new independent corpus is needed for any subsequent generalization claim. Do not tune this cycle's implementation or rerun its holdout. Do not enable narration, commit or push.

First read 01, 05, 11, 12, 16 and 17 plus holdout_results.json H41. Existing authority/quarantine doctrine remains in force. The playable prototype objective remains; this confirmed critical acceptance must be resolved before a controlled player-facing experiment.
''')
    print(json.dumps({'verdict':'C','unexpected_changes':read('integrity.json')['unexpected_changes'],'fixed':len(f)}))

if __name__=='__main__': main()
