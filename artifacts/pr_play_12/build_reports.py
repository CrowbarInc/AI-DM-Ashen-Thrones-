"""PR12 report authoring. All observed tables come from saved executions."""
import json
from pathlib import Path
from build_evidence import table
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'artifacts/pr_play_12'
REPORTS=ROOT/'development/campaigns/product_realization/pr_play_12'
def report(n,title,text):
    REPORTS.mkdir(parents=True,exist_ok=True)
    (REPORTS/(f'{n:02d}_'+title.upper().replace(' ','_')+'.md')).write_text(f'# {n:02d} — {title}\n\nPR-PLAY-12 · 2026-10-31 America/New_York. Offline investigation and isolated prototypes only.\n\n'+text.strip()+'\n',encoding='utf-8')
def main():
    hist=json.loads((OUT/'historical_evidence.json').read_text())
    corpus=json.loads((OUT/'corpus.json').read_text())
    stats=json.loads((OUT/'regression_summary.json').read_text()) if (OUT/'regression_summary.json').exists() else {'status':'pending'}
    stats=stats.get('headline',stats)
    report(1,'Baseline and Historical Evidence',f'''
Revision: `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`. HEAD does not identify the dirty entry source. `artifacts/pr_play_12/entry_status.txt` records extensive existing production, data, documentation, test and artifact changes. `protected_before.json`, `source_snapshot_hashes.json` and the final integrity result distinguish this pass from that work. No applicable AGENTS.md was found in the working directory or .agents. No reset or unrelated repair was made.

The task attachment authorizes diagnostics and isolated prototypes, superseding earlier stop instructions only for that scope. It does not authorize a production implementation or live call. This pass writes its reports and artifacts plus the generated review export. Existing tests run in a byte-copied disposable source tree, so their historical-artifact writers cannot overwrite original evidence. The test copy has no .env or credentials. It is not a clean HEAD checkout.

Orientation reviewed: DEVELOPMENT_CONSTITUTION; NEXT_SESSION; PR-AA portfolio/roadmap; AR-AD target architecture doctrine; state_authority_model; validation_layer_separation; narrative_integrity_architecture; ai_gm_contract; realization_provenance_audit; PR-BN bounded authority; validation_evidence_standard; product_realization_validation; ATGB fixture README; PR-PLAY-04–11 baseline/closeout reports, relevant source and tests. Current executable contracts resolve older general prose prohibitions: PR-BN permits bounded sensory detail and NPC claims, never mechanics, secrets, topology or quest outcomes.

PR04 supplies acceptance-before-commit and rollback; PR05 provider diagnostic/accounting distinctions; PR06 bounded opening output and incomplete-status rejection; PR07 original parsed capture and first semantic reasons; PR08 owned HTTP/SDK-stub transport; PR09 five-turn scenario and six-request stop; PR10 receipt-backed opening overlays; PR11 declaration/prose split and exact-text prompt guidance. None is replaced here.

## Historical openings

{(OUT/'historical_evidence.md').read_text()}

All four available parsed captures and baseline document bundles are preserved byte-for-byte under `artifacts/pr_play_12/historical/<run>/`. Original provider wire bytes and exact historical outgoing request messages are unavailable. Synthetic replay serializes the original parsed mapping as JSON, passes it through production extraction/parser/semantic/final-emission/acceptance/storage owners, and restores all captured baseline documents. The SDK object and token accounting are synthetic; this is not a reproduction of provider inference or exact historical input tokenization.

`evidence(4).zip` was not found in the workspace root, Downloads, or Codex attachment inventory inspected. The matching local latest run is confirmed by its nine declarations, both reported candidate paraphrases, 26714 input / 1784 output tokens and `unauthorized_resolution_decision_fact`. Do not confuse its run timestamp (17:05 UTC / 13:05 New York) with the earlier PR11 rejection (01:57 UTC / previous local evening).

Relevant production owners and exact function lines are indexed in `source_locations.json` and reports 03–04. Existing test selections are retained in regression_runs.json. The PR11 baseline is 878 passing executions / 14 inherited failures, not a full-suite green result. Known issues include three rich-opening assertions, stale readiness/source attestations, a deterministic guard incompatibility, and legacy claim/provenance failures. New failure IDs are compared individually, not inferred from aggregate totals.

Current validation summary: `{json.dumps(stats,ensure_ascii=False)}`. See report 10 and regression_summary.json for final classifications. No ATGB gameplay score or live-quality result is claimed.
''')
    report(2,'Latest Rejection Root Cause',f'''
The sole latest rejection span is **“Threadbare watchers and refugees cluster tightly along the muddy gate line.”** All nine structured declarations pass. The associated authored public fact is “Threadbare watchers and refugees cluster along the muddy gate line.”, source `scene.visible_facts.3`, `rc_b59727e13c62`.

The tavern-runner and census-delay passages mentioned in the request are **not rejected spans** in this execution. Their absence from violations is observed, not inferred from similarity. `span_diagnostics.json` retains every narration unit, candidate source, content-token differences, coverage checks, declaration audit and actual violations. The census wording adds “adding to the bustle”, a causal/flavor implication not proved semantically equivalent by this investigation; its acceptance is not a safety endorsement.

Exact control flow:

1. `gm._safe_json` parses the synthetic SDK output; declared_claims and narration are present.
2. `immutable_valid_response.validate_generated_response` delegates to `gm_resolution_decision.audit_realization_envelope_against_decision`.
3. `validate_declared_claims_against_decision` accepts all nine claims with their supplied IDs, authored provenance and empty semantic_identity.
4. `_decision_with_accepted_declarations` supplies accepted rows to the narration audit. `_empty_identity_covers` accepts the watchers sentence: its only additional content token is `tightly`, within the one-token allowance. The initial narration audit is hard-valid and records world authority for this sentence.
5. `_undeclared_consequential_violations` then compares the full sentence to accepted declaration texts. It is not equal. `_proposition_restates_statement` rejects it because `tightly` adds a token; this second comparison does not share the one-token allowance. With `authority == AUTH_WORLD` and no restatement exemption, the row receives `authorized_consequential_claim` internally and becomes `undeclared_consequential_claim` in the exported violation.
6. The envelope is hard-invalid; the wrapper emits aggregate `unauthorized_resolution_decision_fact`. Safe nonresolution cannot satisfy opening acceptance, so the API returns 422 and rolls back gameplay.

{(OUT/'span_rejection_table.md').read_text()}

The failure is lexical and consequential-classification based. It is not a rejected provenance declaration, missing source ID, hidden disclosure, mechanical adjudication or an unauthorized state transition. Expected and supplied authority are both authored/public world authority, but the second prose/declaration comparison refuses to carry that authority to the changed string. Source locations: gm_resolution_decision.py:1012, :1039, :1645, :3971–4101; immutable_valid_response.py:736–764. Full source excerpts and snapshots are packaged.

Semantically, `tightly` intensifies the existing cluster description. The muddy crowded gate and clustered refugees support a density reading. It does not add a participant, event, travel destination, interaction outcome or resource change. This is a medium-confidence supported presentation interpretation, not a deterministic proof of arbitrary synonym equivalence. The precise addition could imply closer spacing than canon states; the bounded presentation contract must explicitly decide that allowance. Do not infer safety for all one-word additions such as “dead” or “armed”.

`results/<latest-run>_replay.json` is historical parsed-response replay through normal opening production owners, not a simplified unit test. All captured baseline documents are restored under the fixture storage root. Observation wrappers delegate unchanged inputs and results. The existing test fixture stubs external admission/preflight and SDK IO, not semantic checks. Both historical accepted openings still commit once; both rejected openings reproduce 422. The single-word control removes only `tightly` in the two narration fields, keeps declarations unchanged and commits once through the full parser/gate/acceptance path; repeat Start is 409 with no second dispatch. Direct single-span/all-span checks corroborate, rather than substitute for, this replay.

Rollback preserves gameplay payloads and transcript, not byte-identical files. Original persistence-envelope saved_at/integrity timestamps, session.last_saved_at, diagnostic debug_traces and the transient __turn_start_active_interaction_target_id can change. Initial overstrict byte-comparison failures are retained in initial_assessment.xml. The corrected comparison excludes only those explicit non-gameplay fields and still compares every remaining captured gameplay field, scene document and transcript. Raw snapshots remain in replay evidence; this is not crash-atomicity proof.

Primary classification: contract mismatch between two deterministic conservative approximations of prose authority. Prompt wording alone did not prevent another ordinary wording variation. No production repair was made.
''')
    pipeline=[
      ['Canonical documents / resolver','storage.load_*, api.start_campaign, domain resolvers','campaign, character, session, world, combat, scenes → engine outcome','Engine owns truth; storage owns envelope IO','Reset/start eligibility, domain rules, scope lock / rollback; existing stores only','test_pr_play_04_opening_integrity, noncombat_runtime_integration'],
      ['Resolved meaning','ctir_runtime.build_runtime_ctir_for_narration; gm_resolution_decision.build_gm_resolution_decision','resolution and state → CTIR, proposed_facts, permitted_state_mutations, realization_claims','Engine/planner derivative; not model truth','Authority, provenance, uncertainty, permitted mutations; no independent truth store','structured realization, state_authority'],
      ['Model context','api._build_gpt_narration_from_authoritative_state; prompt_context.build_narration_context','state + CTIR + visibility + decision → prompt/context','Planner packages authorized read views','Guidance and public read models; hidden checks remain necessary after generation','prompt_context, opening narrative plan'],
      ['Provider IO / schema','gm.call_gpt; gm._safe_json','one SDK response → normalized gm mapping and metadata','Model proposes prose, claims and optional update fields','JSON/envelope/status/budget checks reject malformed/incomplete output; diagnostics are not authority','PR06, PR07, structured envelope'],
      ['Declaration authority','gm_resolution_decision.validate_declared_claims_against_decision','model declarations + decision → accepted/rejected claims','Source authorizes, declaration exposes intended meaning','ID, identity, lexical fallback, modality and premise ceiling; malformed/unsupported reject','PR11, claim-control, provenance'],
      ['Prose hard legality','immutable_valid_response.run_preserve_if_valid / validate_generated_response; audit_realization_envelope_against_decision','narration + accepted claims + context → hard_valid/reasons','Gate owns legality, never outcomes','Sentence classifiers, lexical coverage, undeclared consequences, hidden markers, mechanics/travel heuristics; safe fallback if invalid','new E1–E20, immutable boundary'],
      ['Final delivery legality','final_emission_runtime / final_emission_gate; final_emission_narrative_authority; narration_visibility.validate_player_facing_visibility','candidate + scene/session/world contracts → selected/sealed text','Gate owns final publication','Visibility, narrative-authority and referent enforcement may replace prose; accepted semantics is not final delivered text','narrative_authority_rules, PR12 E7/E11'],
      ['Opening acceptance','api._opening_response_rejection','final gm + opening contract → acceptance or failure reason','API transaction spine','Rejects safe_nonresolution, invalid structure/provider/fallback/scene contract before commit','PR04, PR07, PR12 replay'],
      ['Post-GM adoption','api._post_gm_adoption_gateway; bounded_improvisation.promote_accepted_bounded_improvisation','validated proposals / legacy optional updates → runtime overlays/ledger','Existing branch owners, not free-form narration','Legacy gateway shape-enforces but semantic policy is observe_only; bounded improvisation independently constrains proposals','PR10 overlays; post_gm_adoption_gateway'],
      ['Persistence / response','api._complete_opening_turn_persistence_like_chat; storage.save_* / append_log','accepted outcome, overlay, final text → stores + projected API response','Engine/API commit; storage mechanics','Normal scope restore on rejected opening; accepted log text is conversational evidence, not truth authority','save_load, world progression, PR12 persistence checks'],
    ]
    pipeline_table=table(['Stage','Module / function','Input → output','Authority','Validation / failure / persistence','Tests'],pipeline)
    (OUT/'authority_pipeline_map.md').write_text(pipeline_table,encoding='utf-8')
    report(3,'Current Narrative Authority Architecture',f'''
The repository already distinguishes runtime truth, planning, expression, legality and offline scoring. Its practical prose-authority boundary remains partly lexical and heuristic. The implementation is not a single “compare text, then commit” validator.

Actual opening flow: eligibility and locked transaction → baseline capture → provisional engine tick / opening resolution → resolved meaning and prompt contracts → SDK draft → structural parse → declaration and narration hard audit → final publication legality/selection → opening acceptance → authorized adoption and durable commit → player projection. Failure restores the opening scope; the engine may provisionally mutate in-memory state before generation, so authority establishment and durable commit are distinct.

{pipeline_table}

Exact functions, signatures and line ranges are in source_locations.json; source_excerpts.md includes complete selected functions, and source_snapshots contains entry-equivalent production bytes. Final emission spans several collaborators; function naming alone was not used as evidence. The E11 observation proves a downstream stage can replace text accepted by the earlier semantic audit. The gateway source explicitly says observe_only, so its receipt is not evidence of comprehensive semantic authorization.

## Trust boundaries

* Authoritative state: canonical authored documents plus engine resolutions and owned runtime stores. Models cannot authorize domain transitions by writing a sentence.
* Authorized claims: engine-derived proposed_facts / realization_claims, visibility and provenance ceilings; these are communicable permissions, not synonymous with stored truth.
* Structured declarations: untrusted realize/propose requests. Matching source ID, structured identity or lexical fallback can support acceptance. A valid source ID currently matches before comparing free-text meaning; _realization_claim_to_narrated_claim retains declared.text. ID presence is therefore not a complete content-binding guarantee. Compatible identity matching is also heuristic in legacy paths.
* Narrative realization: untrusted player-facing prose. Narration and claims have no explicit character-range association. Sentence/claim audits infer association by wording and identity patterns. The same sentence can pass initial world-coverage and fail the undeclared-consequence check.
* Presentation embellishment: sensory texture, mannerism and cadence may remain plain narration or use accepted bounded incidental proposals. Permissions do not cover secret transactions, new navigable geography, outcomes or strengthened certainty.
* Consequential assertions: causes, history, leads, NPC knowledge, resources, transitions and other meaningful outcomes need engine authorization. Regex/proposition heuristics identify many, not all. E8–E10/E12/E15/E20 show delivery gaps in the exact opening context.
* Mechanical adjudication: resolver-owned outcomes and permitted mutations. Checks compare explicit success/failure flags, dead speakers and movement patterns, but absence of a resolved check does not universally forbid every prose success pattern.

Deterministic execution does not imply complete semantic verification. ID equality, state-domain guards, JSON validation, committed state and rollback comparisons are deterministic concrete checks. Token sets, overlapping identity fields, consequential regexes, phrase-based visibility and NPC-rule classifiers are deterministic conservative approximations; they have both false positives and false negatives. Arbitrary semantic equivalence is not established by any of them.

When the hard audit cannot establish authority it rejects and selects safe_nonresolution. Later visibility/narrative-authority stages may instead select grounded replacement text. Opening rejects a nonresolution terminal output, but can accept a grounded replacement. Ordinary turns may have other operation-specific fallback behavior. Offline ATGB evaluates behavior and has no runtime authority.

Conclusion: categories have distinct intended ownership and several real mechanisms. The ambiguity is at the interface from typed accepted claims to unrestricted prose, compounded by a transitional legacy adoption seam. A model-authored declaration neither proves semantic fidelity nor substitutes for publication filtering.
''')
    safeguards=[
      ['Hidden disclosure','visibility normalized exact/substring facts, entity aliases; hard internal-marker regex; narrative-authority gate','Schema alone: no','Yes; E11 semantics passes, final text replaced','Hidden store protects state, not disclosure','Yes; keep visibility and positive public catalog','Engine publication/reveal allowlist + closed rendering','Paraphrased secrets and broad alias inference unproved'],
      ['Combat result / NPC death or injury','decision authority patterns, dead-speaker check, narrative-authority invent-outcome rules','Declaration authority when detected; syntax insufficient','Partial; E9 death delivered unchanged','Combat owner; E9 combat/NPC snapshots unchanged','Yes, though current patterns miss this example','Render resolver receipts only; no open death/injury slot','Ordinary combat variants not exhaustive'],
      ['Skill success','resolution success/failure comparison and decision heuristics','Typed claims partial','E8 automatic success delivered unchanged','Noncombat resolver owns check and state','Yes; metadata alone cannot constrain prose','Outcome rendering bound to resolved check ID/result','No absent-check universal prose check demonstrated'],
      ['Movement','permitted location mutation, travel-arrival regex, final consistency repair','Update shape and typed identity partial','E10 entry delivered unchanged','Scene owner retains active_scene in corpus','Yes','Transition receipt and engine destination text','Opening arrived_at_scene capability may be too coarse; not isolated causally'],
      ['Faction changes','proposition authoritative-rule / history / decision patterns; adoption branches','Claims checked; update syntax alone no','Partial; original PR11 controls reject explicit gate closure','World engine, domain guards; legacy gateway observe_only','Yes','Whitelist exact engine event and affected faction','Natural paraphrases / legacy update payloads not comprehensively proven'],
      ['Quest completion','gameplay lead/history patterns and narrative-authority rules','Partial','E12 rescued/completed delivered unchanged','Quest/world owners; text is not quest transition','Yes','Engine completion receipt and renderer','No complete quest-semantic parser'],
      ['Unsupported world facts / NPC behavior','claim matcher, consequential/residual and rule heuristics; bounded proposal validator','Authority partial; structure no','E6 rejected; E7 bribes replaced downstream','Legacy adoption retains risk if optional updates supplied','Yes','Finite public facts and authorized incidental enum slots','Arbitrary topology/behavior detection incomplete'],
      ['Scene contradiction','authored corpus, semantic identity and narrative-authority comparisons','Partial','E13 abandoned gate rejected','Scene/runtime owner does not equate all text with truth','Yes','Positive current-state anchors with no polarity/text override','Negation and omitted context variants remain unproved'],
      ['Inventory/resources','decision/semantic and mechanical patterns; proposal forbidden terms','Partial','E15/E20 gold delivered unchanged','Character fields unchanged in all corpus runs','Yes','Resource delta receipt rendered by engine','Player belief can be contaminated without a stored gold change'],
      ['Time progression','clock regex; time/history decision constraints','Partial','Heuristic, not complete duration entailment','World tick/clocks owned by engine; rollback verified','Yes','Engine time-delta receipt; no arbitrary connective time assertions','No exhaustive temporal paraphrase test'],
      ['NPC knowledge','dialogue_authority, speaker/epistemic ceilings, bounded NPC claims','Premise/modality ceiling checks','Yes; many matching and qualification heuristics','NPC memory/claim provenance separate from world truth','Yes','Publication and NPC epistemic capability, closed claim slots','Rumor attribution does not prove a safe embedded proposition'],
      ['Persistence / overlays','API opening scope, adoption validators and receipts, state-authority registry','Shape is not semantic authorization','Prose guards limit unsupported premises before adoption','PR10 projections and rollback / state checks','Yes, indirectly; text can enter temporal/conversation memory','Reuse receipt-backed projection and atomic scope; no prose-to-canon promotion','Gateway semantic policy observe_only; crash atomicity outside evidence'],
    ]
    safeguard_table=table(['Protection','Current mechanism','Structured coverage','Narration coverage / evidence','State coverage','Weakened by removal?','Alternative deterministic safeguard','Uncertainty'],safeguards)
    (OUT/'safeguard_dependency_matrix.md').write_text(safeguard_table,encoding='utf-8')
    report(4,'Safeguard Dependency Matrix',f'''
Lexical narration checks are part of the current safety net. Removing them would lose coverage even though the same checks reject supported prose and miss other assertions. Structured JSON validity, engine state invariants and player-facing factual validity protect different surfaces.

{safeguard_table}

Source anchors: immutable_valid_response.validate_generated_response (mechanics, travel, hidden marker and decision checks); gm_resolution_decision.audit_narrated_claims / _undeclared_consequential_violations (prose authority); narration_visibility.validate_player_facing_visibility (publication); narrative_authority.validate_narrative_authority (invented outcome/hidden/intent checks); bounded_improvisation.validate_bounded_improvisation_proposal (positive incidental policy); api._post_gm_adoption_gateway and _restore_opening_baseline (transitional adoption and rollback). Reports 02–03 and source_locations.json give precise positions.

The core invariant requires both **state integrity** and **publication integrity**. In the corpus, unauthorized outcome wording does not change character resources, combat, conditions, canonical campaign, NPC state or active scene; those six comparisons pass in every case. Nevertheless the player can be told that an NPC died or gold was awarded. Logged text can shape future interpretation and player choices. Unchanged numeric state is not sufficient containment for a solo GM.

The deterministic alternative is a positive construction boundary: only public engine-authored factual anchors and renderer-owned typed outcomes enter player-visible text. With arbitrary surrounding free text, neither reference IDs nor regex prohibitions guarantee this invariant. Existing visibility, mechanical and final-delivery guards must remain defense in depth; this pass neither removes nor weakens them.
''')
    report(5,'Narrative Equivalence Corpus',f'''
E1–E20 execute the production opening pipeline once each using synthetic SDK transport, the latest captured baseline documents and the same nine valid structured declarations. Only E19 adds a forged declaration with no valid source. For other cases prose varies while declarations remain valid, deliberately exposing the declaration-to-prose boundary. Cases are synthetic boundary/stress controls, not human gameplay or independent held-out evidence.

All input text, interpretations and exact delivered text are in corpus.json; raw nested audits and API output are in results/E*.json. In particular, opening HTTP status, semantic hard-validity and final emitted text are separate columns. The direct prototype experiments are separate from these production results.

{(OUT/'corpus_results.md').read_text()}

Interpretation judgments: E2 moves the same location clause without introducing a barrel or actor. E3 substitutes informal gossip for rumors without upgrading reliability; E4 preserves the warning and present missing-patrol status. E5 adds already plausible rain-on-stone texture, turn-local and without mechanics. E6 adds a second open gate, a navigable spatial affordance outside incidental permission. E7 establishes corruption; E14 upgrades rumors to reliable patrol-specific intelligence. Neither is a harmless synonym. E16 joins two known independent facts without asserting a causal relationship. E18 repeats a fact without increasing authority.

E17 is an omission probe, not a proven false-negative violation: all nine model declarations request MUST_STATE, but model role flags are not themselves an engine obligation that every sentence must appear. The current decision also marks many alternative/journal/runtime rows MUST_STATE without a simple globally executable completeness requirement. The observed acceptance shows this ambiguity. The next contract must select explicit required public anchors instead of treating every generated role string as an obligation.

Observed false-positive candidates: E3 and E4. Observed semantic-stage false-negative candidates: E7, E8, E9, E10, E11, E12, E15 and E20. E7 and E11 are replaced downstream with grounded rain/gate fallback text; they are **not final-delivery failures** for these exact strings. Final-delivery false-negative candidates are E8, E9, E10, E12, E15 and E20. E11 uses an exact hidden fact in the restored scene, not a fabricated secret. No claim of exhaustive paraphrased-secret protection follows.

All twenty runs preserve the six domain comparisons recorded in state_protection. Rejected openings preserve the normalized entire captured gameplay document set and transcript. Accepted controls produce ordinary initialization progression. No prose is injected as accepted state and no hard-valid assertion was changed to make the corpus pass. Tests assert the evidence mechanics and containment, then report actual semantic failures rather than pretending the desired safe outcomes already hold.
''')
    report(6,'Architectural Alternatives','''
**A — Existing lexical authority.** Keep both declaration and prose audits, visibility, mechanical checks, final-delivery selection and rollback. Improve reporting and clarify claim references; consider a narrowly shared normalization only after targeted safety controls. This is the least disruptive path. It preserves existing safeguards but also their gaps, and encourages rigid copying. PR11 guidance did not prevent the latest one-word failure. Raising the one-token allowance globally is unsafe: modifiers can change polarity, ownership, certainty or outcome. Harmonizing two token rules could remove this exact rejection but is not an architecture-level equivalence solution.

**B — Structured authority with flexible arbitrary prose.** Claims must remain validated, explicit, source-bound and operation-scoped, with preserved uncertainty and resolver outcome permissions. Narration segments could reference claims and undergo separate checks. This improves traceability but references do not prove the string says only what the claim authorizes. Current source-ID matching can accept before comparing declared text, and even perfect declaration validation does not reject undeclared free-text outcomes. A deterministic prohibited-word detector cannot reliably distinguish every disguised success, hidden identity or causal implication. A finite semantic grammar can be safe, but that changes B into a bounded renderer rather than unrestricted realization. Do not remove prose guards under a structured-only argument.

**C — Engine-owned factual narration.** The engine creates a public operation-scoped fact catalog and renders facts/outcomes itself. The model may choose closed presentation selectors, ordering and reviewed variants; it may not supply arbitrary final text. Positive construction makes a new unrepresented factual assertion impossible within the renderer's grammar, conditional on catalog correctness. It costs authoring effort, produces repetitive wording, and must handle attribution, uncertainty, grammar and referents. A secret accidentally placed in the public catalog would still leak. This does not eliminate the need for the existing publication owner.

**Rejected loose hybrid:** exact factual anchors embedded in unrestricted model connective prose. “The serjeant watches the queue. You kill him.” remains possible. Labeling a string sensory or linking its segment to an approved claim is not validation. Post-hoc regex filtering does not close this hole.

**Preferred bounded hybrid H:** reuse C's closed rendering for openings and authoritative consequential outcome segments. Let the model select ordering, a finite reviewed variant and context-authorized presentation tokens. Retain the current production path for operations not explicitly migrated; do not claim those operations gain C's guarantees. The future shared contract carries operation capabilities and a required-anchor subset. Conjunctions may arrange independent anchors, never introduce because/therefore/negation/death/time/resource text unless an engine-owned component supplies it. There is no arbitrary prefix, suffix, caption, dialogue or sensory text hole in the first implementation.

Information flow: existing resolver + visibility/publication owner → ephemeral public fact/outcome catalog and operation capabilities → model plan of opaque claim IDs / variant IDs / presentation selectors → strict plan validation → deterministic renderer → existing hard validation and final-publication guards → existing opening acceptance / adoption / commit. Model-origin scene_update/world_updates are absent from this new opening envelope; if optional updates appear, reject the envelope rather than silently adopt them. Ordinary legacy turns remain governed by their existing path until separately reviewed. No new persistent gameplay schema is needed.

This confines the missing responsibility to the existing meaning/planning and final-delivery boundary rather than adding a second truth engine or model judge. The current source already owns authoritatively phrased facts, publication and transactionality; it lacks a positive final-text construction contract independent of copying model prose.
''')
    proto=json.loads((OUT/'prototype_results.json').read_text())
    report(7,'Prototype Findings',f'''
The experiment code is `artifacts/pr_play_12/prototypes.py`. It is imported only in the disposable assessment environment. There are no runtime imports, provider requests, dependencies, canonical state writes or persistent schema additions. `test_assessment.py` retains the replay/corpus/prototype test code; prepare.py and run_regression.py document reproduction.

**A:** E1–E20 measure unchanged current production behavior. The two supported synonym/tense variants fail while several unauthorized outcomes pass. The latest historical single-word control commits once. These establish both lexical friction and incomplete detection, not a replacement validator.

**B lower-bound prototype:** validate declarations with the real source authority function, then publish arbitrary narration. All ordinary valid-declaration corpus variants pass, including unauthorized success, combat, movement, resource/quest and hidden-fact text; E19's forged declaration fails. This deliberately minimal prototype isolates what structured authority alone can guarantee. It is not an implementation of every possible enhanced B safeguard. A reference-linked arbitrary string has the same semantic hole; a reliable general deterministic semantic equivalence algorithm was not demonstrated.

**C/H finite prototype:** plan shape is exactly atoms + texture. Atoms contain only claim_id and variant; no supplied text is read. IDs must exist in the caller's public scene catalog; canonical text is engine-supplied. Three reviewed alternatives cover word order, rumor/gossip and missing-patrol tense. Required anchors are a three-fact experimental subset (notice/serjeant/runner), not a claimed extraction of production obligation semantics. One finite rain texture is allowed. Duplicate atoms and independent anchors are permitted. Required omissions, raw unsupported prose, unknown/hidden IDs, unreviewed variants, injected text fields and unknown sensory selectors fail closed.

Twenty comparative corpus plans and four hostile plan controls run deterministically. Supported/incidental cases accept reviewed realization choices; unsupported cases and E17 omission reject the new representation. Input-context equality and empty state_mutations are asserted. Results and rendered output are in prototype_results.json. This does **not** mean the original arbitrary E2/E3/E4 prose is semantically understood: the plan selects a renderer-owned variant. E16 renders supported anchors as separate sentences. C enforces its own explicit required-anchor policy, which differs from current E17 behavior.

Each candidate against the minimum objective:

{table(['Candidate','Supported paraphrase','Unauthorized mechanics','Hidden information','Unsupported consequences','State authority'],[['A','Some; E3/E4 false-positive candidates','E8/E9 delivered: incomplete','Exact E11 repaired downstream; paraphrases uncertain','Mixed: E6 rejected, E12/E20 delivered','Six domain checks pass; legacy adoption risk remains'],['B lower bound','Yes, arbitrary strings','Fails','Fails without downstream publication enforcement','Fails','No direct writes, but unsafe narrative premise exposure'],['C/H closed plan','Yes, three finite reviewed forms','Reject unrepresentable text/outcome','Unknown IDs/text injection rejected, conditional on public catalog','Reject unrepresented statements','Pure renderer; input unchanged; no state mutations']])}

Limitations: finite author-reviewed variants are not NLP entailment; publication filtering is a precondition, not fully integrated; runtime grammar, accessibility, attribution and ordinary-turn migration remain unimplemented; no latency or token-cost benchmark; no gameplay-quality score; no crash/restart transaction proof. A complete safe interface allowing arbitrary fresh prose is still unproved. The evidence supports a smaller constrained implementation, not a broad prose-validation relaxation.
''')
    scores={'A':[2,3,1,2,5,4,5],'B':[1,1,5,1,3,4,2],'C':[4,4,1,4,2,5,2],'H':[4,4,2,4,3,4,3]}
    weights={'Required':[25,20,15,15,10,10,5],'Safety emphasis':[35,25,10,15,5,5,5],'Narration emphasis':[15,10,35,15,10,10,5],'Implementation emphasis':[20,15,10,10,25,10,10]}
    weighted={name:{a:round(sum(s*w/100 for s,w in zip(ss,ww)),2) for a,ss in scores.items()} for name,ww in weights.items()}
    (OUT/'architecture_scores.json').write_text(json.dumps(dict(scores=scores,weights=weights,weighted=weighted,uncertainty='Ordinal engineering judgments; unintegrated designs and costs uncertain, not statistical measurements'),indent=2))
    dimensions=['Deterministic authority 25%','Hidden protection 20%','Narrative flexibility 15%','Reliability 15%','Implementation simplicity 10%','Performance/token economy 10%','Migration safety 5%']
    reasons=[
      ['E8–E10/E12/E20 delivered without authority','Structured-only accepts unauthorized prose','Closed plan disallows unrepresented outcomes; public-catalog correctness unproved','Same closed guarantee in migrated lane; other operations remain legacy'],
      ['Exact E11 repaired; semantic pass and paraphrases unproved','Arbitrary secret string accepted by prototype','No hidden ID/free text; positive catalog precondition uncertain','Reuse visibility owner plus closed plan; integration uncertain'],
      ['E3/E4 rejected; exact-copy pressure','Arbitrary wording possible; no truth guarantee','Finite alternatives only, repetitive engine text','Ordering/style/variants flexible within finite grammar'],
      ['Four histories replay; live latest rejected after prompt repair','Unsupported text accepted; no proof of complete detector','Pure deterministic plan; grammatical/integration reliability uncertain','Operation-scoped migration limits impact; integration uncertain'],
      ['Existing path; diagnostics/normalization relatively small','Claims/segment contract and checks require nontrivial changes','Catalog, grammar, outcomes and content rendering substantial','Opening-first, reuse current state/contracts; smaller than whole-runtime C'],
      ['No judge; current large prompt and duplicated claim/prose cost','No judge but claim/segment metadata still needed','Compact IDs; could eliminate duplicated factual prose; estimate only','One existing call, compact plan; no measured token reduction'],
      ['Smallest delta, existing limitations retained','Changes meaning of accepted free prose and temporal premises','Broad renderer migration touches many operations','Opening-first additive switch and rollback; legacy behavior contained but unchanged'],
    ]
    scoretable=table(['Dimension','A score / evidence','B score / evidence','C score / evidence','H score / evidence'],[[d,*[str(scores[a][i])+' — '+reasons[i][j] for j,a in enumerate(scores)]] for i,d in enumerate(dimensions)])
    failuretable=table(['Design','False positives / negatives','Worst plausible failure and containment','Recovery / observability'],[
      ['A','Supported synonyms rejected; unrecognized outcomes missed','Player believes a death/resource/movement outcome absent from state. Engine state checks contain direct changes, not belief; retain final guards and add diagnostic probes.','Opening rollback on detected invalidity; accepted false negatives can log misleading text. Nested audits needed; aggregate reason is insufficient.'],
      ['B','Claim links could be valid yet wording changes truth; strict detectors recreate A friction','An approved claim ID launders a hidden identity or outcome in its linked prose. IDs alone do not detect it; retain guards, but complete deterministic containment is unproved.','Fail closed when unsupported; no retry/judge expansion. If classifier misses prose, observability may show structurally clean unsafe text.'],
      ['C','Unknown variants rejected; catalog omissions reduce coverage; incorrect templates misstate facts','Hidden fact incorrectly placed in public catalog is faithfully disclosed. Positive publication filtering, catalog review, reveal-receipt tests and final visibility checks are mandatory.','Reject bad plan before commit; do not silently render unvalidated raw text. Plan/anchor lineage is observable, semantic quality still human-reviewed.'],
      ['H','Finite expression limits and operation classification mistakes; legacy gaps outside migrated lane','Capability error routes a consequential turn through an insufficient renderer or legacy lane. Bind operation/capabilities to engine resolution, disallow model selection, keep legacy policy and tests.','Opening scope remains atomic; default-off reversible rollout. Diagnostics identify operation, allowed IDs, rendering and final-selection provenance.'],
    ])
    (OUT/'risk_assessment.md').write_text(failuretable,encoding='utf-8')
    report(8,'Comparative Evaluation',f'''
Scores are ordinal 0–5 (higher is better); simplicity and migration safety invert cost/risk. They are engineering assessments backed by source and finite tests, not measured live reliability or numerical safety probabilities. C/H scores describe the proposed constrained emission boundary, not guarantees for all current gameplay. Unknown catalog completeness, implementation reliability, cost and migration behavior are explicitly **uncertain**. Four is used instead of five for conditional safety designs; implementation-sensitive entries may reasonably vary by at least one point.

{scoretable}

{table(['Weight scenario','A / 5','B / 5','C / 5','H / 5'],[[n,*[v[a] for a in scores]] for n,v in weighted.items()])}

Weights for each sensitivity case are in architecture_scores.json in the listed dimension order. H leads under the required weights and the three stated alternatives. This is not robust dominance: reduce H's authority and hidden scores by one each for an integration mistake and its required-weight total falls by 0.45, below C. With much greater emphasis on unrestricted prose, B can win an aesthetic score while failing the safety objective. Safety minimums therefore remain gates, not compensable score points. C and H are variants of the same positive-construction direction; the recommendation for H is a bounded migration decision, not statistically proved superiority.

{failuretable}

No design should treat declarations or logged prose as canonical truth. A/B are rejected as the next primary direction because better opening acceptance does not prove safety, and arbitrary prose cannot be verified by source IDs alone. Broad C is deferred because replacing ordinary gameplay rendering would exceed the smallest justified pass. H permits an independently testable opening implementation while retaining current domain owners, persistence and operation-specific boundaries.
''')
    report(9,'Recommended Architecture and Implementation Plan','''
**Recommend a bounded C-led hybrid: engine-owned factual opening rendering with explicit operation capabilities and finite presentation choices.** Do not implement flexible unrestricted prose acceptance or replace the production validator. This is conditionally ready for a scoped implementation proposal, not deployment authority.

Authority ownership stays with existing domain resolvers, CTIR/decision meaning, narration_visibility publication, API transaction spine and storage. The new responsibility is positive rendering at the existing narration/final-delivery boundary, using an ephemeral plan. It must not introduce a second router, state store or model judge. The model may improvise presentation only within a granted finite vocabulary; consequential facts remain engine-controlled because the renderer has no free-text factual channel.

Structured contract: an opening-specific plan containing only bounded ordered atoms of public claim_id and renderer variant ID, plus finite context-authorized presentation selectors. The engine supplies the catalog, required anchor subset, operation and capability set; model labels cannot elevate them. Bind IDs to source value, current scene, operation and turn; do not inherit today's permissive ID-to-declared.text matching. Duplicate handling and maximum output length must be explicit. Reject unknown keys, IDs, variants, optional legacy mutations and raw text. Do not persist the plan or new schema roots.

Narration contract: factual sentences come from engine text or reviewed semantic variants with preserved referent, polarity, modality and attribution. No arbitrary connective prose, dialogue, sensory string or caption may bypass that construction boundary. The first increment may provide ordering and rain/cadence choices, not an open-ended natural-language paraphraser. Low narrative flexibility is an acknowledged tradeoff; broad authored variant coverage is future work, not silently delegated authority.

Validation stages: current structural extraction → strict closed plan check against the engine's public catalog and operation capabilities → deterministic rendering → existing hard semantic, visibility and final-delivery legality → ordinary opening acceptance → unchanged adoption/commit/rollback. Gate ordering and accepted-response sealing need explicit review: construct the candidate before sealing rather than mutating an already accepted immutable string. Do not suppress an existing hard rejection merely because a plan is valid. If current validators reject a renderer-owned variant, fail the experiment and diagnose it; do not add a blanket exemption.

Hidden information: construct the catalog from positive published/revealed facts, not all gm_resolution_decision.realization_claims, all prompt text or hidden_facts with prohibited words removed. A guessed hidden ID must fail even if it exists in the broader engine. Preserve independent visibility checking after rendering. Resolver outcomes and NPC knowledge require their own operation receipts/capabilities; a visible NPC existence claim does not authorize its private knowledge or actions.

Mechanical enforcement: no player success, death, injury, inventory change, movement, quest completion, faction or time mutation can originate in a presentation selector. For later ordinary-turn adoption, use engine-owned outcome components bound to exact resolver receipts. An opening can publish initial scene state and normal initialization bookkeeping; it cannot grant player-action success merely because arrival context exists.

Persistence: reuse existing session/world/combat/log writes and opening scope lock/restore. Rendered text may enter existing transcript/provenance fields; it must not create independent world truth. Preserve receipt-based scene overlay projection. First opening-plan implementation emits no model scene/world update payloads, so unsupported updates fail before adoption; legitimate existing seed overlay needs must be represented by existing engine-owned sources and receipts, not reintroduced as an unchecked text escape.

Failure: reject invalid plan or rendered output before commit, return the current bounded opening failure response, retain useful claim/span/operation diagnostics and state rollback. No new retry, fallback authorization, provider request, budget increase or judge call. A renderer fallback is not automatically an accepted opening; the existing scene-opening/required-anchor checks must accept it independently.

**Opening policy decision: shared authority policy with engine-selected operation-specific capabilities.** Opening has initial authored public anchors and initialization/overlay work but no player action to adjudicate. It still contains hidden facts and consequential hooks. Ordinary turns additionally need resolver results, NPC claims and uncertainty permissions. A narrower capability profile is appropriate; a global bypass for opening prose is not. The policy is shared, the grants differ by engine operation, and the model cannot select a more permissive operation.

## Phase 1 — Contract definition

Document the exact public catalog projection and required anchor subset. Resolve existing blanket MUST_STATE ambiguity; distinguish optional authored observations from necessary opening orientation. Define semantics of missing source, expired/wrong-scene/reveal IDs, uncertainty, repeated atoms, ordering and operation binding. Inventory entry into final sealing and native adoption so the new plan cannot authorize legacy writes. Review canonical text for accidental hidden content. Gate: a source-reviewed contract and adversarial fixtures; no production behavior change yet.

## Phase 2 — Minimal implementation

Add a default-off opening renderer-plan envelope at the existing gm schema boundary and an ephemeral catalog/renderer helper beside existing narration owners. Keep ordinary turns on their current envelope and keep all state schemas. Reuse the existing one-call provider route and output allowance; do not add model calls. Add no new runtime persistent structures. Implement a small finite variant/selector set only. The engine selects the envelope based on operation, not user/model text. Gate: exact plan inputs, deterministic output, no free-text escape or optional mutation channel, no production default change.

## Phase 3 — Deterministic validation

Replay all four parsed historical captures through unchanged legacy mode, preserving both 200 and 422 outcomes. In plan mode, use explicitly derived engine plans with their own lineage; never claim those are unmodified historical provider responses. Run E1–E20 against legacy mode and equivalent hostile/supported plan representations against renderer mode. Require every unsafe outcome to be rejected or impossible to represent, unknown/hidden IDs rejected, reviewed variants accepted by all downstream gates, original state unchanged on rejection, commit once on acceptance. Preserve false-positive/negative reporting across stages.

## Phase 4 — Safety regression

Re-run mechanical/hidden/epistemic/scene/overlay/state/provenance suites, provider budgets and retries, opening concurrency/repeat/rollback and persistence. Add attack controls for valid-ID wrong text, raw text in every field, polarity/strengthening, stale-turn/wrong-operation/wrong-scene IDs, hidden catalog membership, forged outcome/reveal receipts, model-supplied capability sets and required omissions. Keep ATGB corpus, saved judgments and attestations frozen; record new evidence separately. Gate: no new relevant failure, no relaxed guard, complete input/output lineage, no unchecked adoption seam and no secret disclosure in delivered text.

## Phase 5 — Controlled live test (future authority required)

Only after external approval and separate authorization, return to the existing FiveTurnGameplay scenario with the unchanged six-request ceiling, model, output caps and retry suppression. If five turns do not fit, stop and report incomplete feasibility. Do not raise limits or retry automatically. Inspect opening and all delivered turns, state, publication and mutation receipts; keep ATGB/human judgments separate from structural success. Require review of narrative adequacy, not merely an accepted opening.

Migration is additive, flag-controlled and reversible. Legacy mode retains historical outcomes; no frozen attestation is rewritten to bless source changes. The exact next implementation objective is **an opt-in opening-only, public-catalog-bound rendering-plan contract and renderer that passes downstream existing validators without any arbitrary text or model-state-update field**. It does not include ordinary-turn migration or broader semantic-validator changes. One next action: external review of this contract and the evidence package. Do not execute that implementation during PR-PLAY-12.
''')
    report(10,'Final Verdict and Handoff',f'''
**B — Conditionally ready.** A specific bounded architecture exists: C-led hybrid H, engine-rendered public opening facts with finite presentation choices and shared operation-specific capabilities. The conditional recommendation reflects an incomplete public catalog/obligation integration proof and finite expression, not permission to relax current prose validation.

Supporting evidence: both accepted historical openings still commit; both rejected openings reproduce production semantic rejection and opening rollback. The latest sole cause is the added `tightly` token passing initial coverage then failing the undeclared-consequential restatement rule. Removing that word alone commits through the same normal path. E1–E20 expose two supported-wording false-positive candidates and six delivered unsafe-outcome candidates; exact hidden disclosure is replaced downstream. All six measured domain state checks remain intact in the corpus. The closed-plan prototype accepts reviewed variants and rejects unrepresentable outcomes/hidden IDs/raw-text injections; it does not understand arbitrary natural language.

Rejected/deferred alternatives: prompt-only/exact-copy guidance A does not resolve architectural friction or known detection gaps. Structured-only flexible prose B cannot guarantee publication authority. Exact anchors plus arbitrary connective prose leaves the same hole. Whole-runtime C is deferred in favor of an opening-scoped reversible implementation. Ordinary-turn behavior remains outside the new construction guarantee until separately migrated.

Validation summary: `{json.dumps(stats,ensure_ascii=False)}`. Full commands, case-level failures, classification, environment-blocked initial runs and local HTTP reruns are in regression_summary.json / regression_runs.json and JUnit/log files. The consolidated final selection matches every PR11 lane's pass/fail count and all fourteen failure IDs. Seven initially failing same cases were resolved by unchanged-original-source controls and are not counted twice. Initial environment failures are retained separately. Production source is unchanged from entry. This is not a full-suite result, live reliability measurement or rewritten historical verdict.

Remaining risks: exact original provider wire/full request unavailable; source-ID text binding permissive; open prose semantic enforcement incomplete; public/revealed catalog correctness and required-anchor policy unresolved; ordinary adoption gateway semantic policy observe_only; immutable sealing order integration unimplemented; finite templates may sound repetitive; six-request five-turn feasibility and live quality unproved; crash atomicity and arbitrary hidden paraphrases not established. None is silently marked solved by the prototype.

Exact next implementation objective: an opt-in opening-only rendering-plan contract bound to the positive public catalog and current operation, with deterministic factual output, no arbitrary text or update channel, unchanged existing legality checks and transactionality. One recommended next action: **external review of this archive and the bounded plan in report 09**. No implementation or live action was executed after this recommendation.

Closeout confirmations for this pass:

* No live provider calls and no provider connectivity tests.
* No production semantic-validator changes and no production gameplay changes.
* No model or provider-configuration changes and no output-budget increases.
* No automatic production/provider retries were enabled or performed. Existing synthetic retry-control tests are diagnostics only.
* No unauthorized claim acceptance was enabled in production. Existing false negatives were observed in disposable fixtures; prototype acceptance cannot reach gameplay.
* No hidden-information relaxation and no state-authority relaxation.
* No new persistent gameplay structures and no experimental PR-EG integration.
* Frozen ATGB baseline unchanged, subject to the packaged entry/exit hash verification; benchmark scoring was not run.
* No commit or push performed; existing dirty work preserved.

The generated timestamped CURRENT_REVIEW archive is the stop boundary. Await external review before implementing the recommended architecture.
''')
if __name__=='__main__': main()
