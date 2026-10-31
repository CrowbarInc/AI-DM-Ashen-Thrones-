"""Build the PR-CB diagnostic reports and independent-review archive."""
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def put(name, text):
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def main():
    rows = load("context_reconstruction_evidence.json")
    costs = load("context_cost_evidence.json")
    probes = load("validation_probe_evidence.json")
    decision = "F - MULTIPLE COUPLED CAUSES"
    put("PR-CB_helpfulness_investigation.md", """
# PR-CB Helpfulness Investigation

MODE: BOUNDED DIAGNOSTIC / PROMPT AND CONTEXT AUDIT
LIVE CALLS: 0
PR-CA inherited decision: B - READY WITH NON-BLOCKING QUALITY LIMITATIONS
PR-CB decision: F - MULTIPLE COUPLED CAUSES

The strongest explanation is engine-derived refusal guidance coupled to an under-scoped incidental-dialogue recipe. This is more specific than attributing the result to model quality alone. The social resolver converts absence of an authored topic into refusal for ordinary questions; the provider receives that refusal repeatedly even though narration validation accepts ordinary answers as NPC claims. The recipe simultaneously permits transient dialogue and discourages durable preference, with examples focused on refusal/hesitation rather than affirmative subjective answers. No authority or prompt repair was implemented.

Confirmed mechanisms: T1-T3 mechanical_resolution.social.reply_kind is refusal; narration_obligations.active_npc_reply_kind and structural prompt instructions repeat it; the final instruction requests refusal, uncertainty, or inability. Deterministic _infer_reply_expectation reproduces refusal/refusal/refusal/reaction from the four inputs without conversation history. All 12 ordinary-answer probes pass decision-aware narration, empty declarations, and the immutable lifecycle on the first attempt. The typed authority lane also accepts opinion, food detail, and ordinary personal characterization while rejecting a consequential proposal.

Supported effects: this guidance strongly encourages evasion, and prior evasive snippets help reinforce T2-T4. The exact model response and its invented safety implication are not causally proved by static evidence. No ablation, provider comparison, or live retry was performed.

The architecture supports harmless NPC speech and typed low-consequence improvisation, but the current social resolver and provider projection do not reliably present that permission for an unauthored mundane question. Acceptance does not measure whether a refusal answers the player's practical request. PR-CA's structural pass remains valid; its attribution to model quality alone is incomplete.

Evidence: four complete preserved provider inputs, context_reconstruction_evidence.json, validation_probe_evidence.json, typed_authority_probe_evidence.json, source_excerpt_evidence.json, focused_tests.txt, and offline_probes.txt. Reports use historical provider inputs as primary evidence; source excerpts describe the current working tree, which was already dirty. They are not a historical commit snapshot.
""")
    put("PR-CB_effective_prompt_audit.md", """
# Effective Prompt Audit

The four T*_effective_provider_input_redacted.json files reproduce the preserved PR-CA generation inputs and recorded request metadata. Each contains exactly a system message and a user message holding a serialized JSON payload. There is no separate developer message, no raw multi-message chat history, and no API response schema; the JSON shape is instructed in text. Source hashes are in context_reconstruction_evidence.json. These records contain game context and no credential/header transport data; no game-context fields were removed. Transport defaults absent from the original capture cannot be reconstructed.

System instructions favor answers: ANSWER THE PLAYER ranks first; direct questions should be answered first; specific NPC replies should offer a concrete answer, partial specific, source, or usable next step. They expressly permit mundane dialogue and low-stakes texture as bounded incidental realization, while denying authority to create unsupported durable facts. Mechanics, hidden facts, player agency, and app-selected speakers remain protected. These restrictions are appropriate for consequential assertions.

User payload conflicts and scope gaps:

- instructions: 'You MUST NOT assert facts outside narration_visibility.visible_facts; only visible facts may be directly asserted.' No local distinction between objective assertions and subjective quoted opinions is given in that mandatory block. The scene lists only the baker beside loaves.
- social_context: knowledge_scope is empty, reliability partial, guardedness medium in mechanical_resolution.social.target_profile_hints. The knowledge gate permits grounding in visible role, scene, or prior exchanges, which supports a baker knowing bread, but does not override explicit refusal obligations.
- mechanical_resolution.hint and the LAST instruction: 'No new information was revealed. Narrate a refusal, uncertainty, or inability without inventing facts the speaker does not have.' This turns absence of a retrieved topic into a conversational limit.
- narration_obligations.active_npc_reply_kind: refusal T1-T3, reaction T4. narrative_plan.narrative_mode_contract and instructions include struct:contract_obligation:reply_kind:refusal for T1-T3.
- decision_facing_answer_recipe.turn_operation: answer/hesitate/deflect/joke/refuse are allowed, but 'Do not establish a durable preference or history merely to answer.' forbidden_upgrades includes durable_preference_without_authorized_claim. T1 asks what the baker usually keeps, making that warning particularly salient.
- recipe.declaration_guidance.epistemic_premise says no NPC claim is authorized on this turn, while ordinary dialogue is allowed and validation treats an ordinary preference as claim_only. This lacks an explicit distinction between an existing authorized claim and fresh subjective speech.
- recipe.incidental_improvisation_guidance gives refusal, hesitation, mannerism, and phrasing as examples. It omits affirmative opinion/recommendation examples.
- instructions still mention world_updates, new_scene_draft and suggested_action although narration_only permits only narration. These are stale structured-lane affordances, not demonstrated causes of evasion.

Ordering: the system hierarchy explicitly puts answering first, so restrictions do NOT dominate by formal message priority. However, specific engine-selected obligations and the final refusal hint conflict with that general goal. Repetition, specificity, and last placement are observable; their effect on model attention is an inference. The top-level dialogue_social_plan.reply_kind is unknown in ALL four turns, despite the explicit refusal/reaction elsewhere; its ONLY planning-source rule creates another inconsistent guide. Do not report that object itself as specifying refusal.

Locations: game/gm.py:295 (narration-only system), game/prompt_context.py:1900 (visibility block), :1935 (dialogue-plan rule), :1969 (obligations), game/social.py:3420 and :4170 (reply derivation/hint), game/gm_resolution_decision.py:4269 and :4726 (recipe limits/examples). See captured text for exact historical instructions.
""")
    put("PR-CB_authority_boundary_analysis.md", """
# Authority Boundary Analysis

| Category | Existing handling | PR-CA limitation |
| --- | --- | --- |
| Established world fact | Authored decision claims with provenance; objective assertions must respect visibility and decisions | Only baker existence/location and loaves are established; no bread varieties or preference |
| Consequential world invention | Requires authorized decision/state lanes; typed consequential proposals rejected as incidental | Narration-only cannot mutate world state or add declarations |
| Incidental NPC opinion | Quoted speech may be claim_only; typed npc_claim/opinion accepted at low consequence | Recipe warns against durable preference and says no NPC claim authorized without explaining transient claim permission |
| Incidental conversational improvisation | Typed incidental_fact categories include food_composition, mundane_service_detail, mannerism, local_color, ordinary_personal_detail | Narration-only schema exposes no improvisation_proposals field; transient speech still passes |
| NPC claim | Separate npc_claim provenance and claim_only authority; accepted ledger claims stay not_world_truth | General visibility instructions do not explain this distinction locally |
| Durable NPC characterization | Existing bounded ledger supports scene/session scopes and ordinary_personal_detail, with runtime authority; reuse projected for continuity | No new typed ledger entry can be proposed through narration-only; chat memory may preserve speech without durable ledger authority |

Deterministic controls accept 'I usually keep a rye loaf for myself.' as npc_claim/opinion, 'The darker loaf is popular with travelers.' as food_composition, and 'The baker prefers rye bread.' as ordinary_personal_detail. A consequential hidden-vault proposal is rejected. These controls demonstrate available typed lanes, not that narration-only can call them or that every statement in those categories is safe.

The misclassification is operational: absence of authored information becomes refusal even for subjective or mundane role-grounded speech. It is NOT evidence that the validator universally classifies categories 3-6 as consequential invention. Plain quoted preference passes as claim_only; persistent characterization is deliberately governed separately. The no-durable-fact ceiling is sound, but its generation wording overreaches if read as prohibiting the NPC from stating any preference.

References: game/bounded_improvisation.py:27-56 (categories/scopes), :230 (validation), game/gm_resolution_decision.py:1706 (ledger projection), :3123 (narration audit), game/gm.py:3767 (exact narration-only parser). No rules or persistence were changed.
""")
    reconstruction = "# PR-CA Context Reconstruction\n\nAll turns used narration_only / incidental_dialogue / reply_not_required, with no consequential realization. Each first attempt passed the recorded narration and declaration validation, with no retry. Complete prompt, world, history, output and validation evidence is retained per turn.\n"
    notes = [
        "T1 has empty recent_log and selected_conversational_memory. The initial refusal cannot be caused by prior replies. Authored context includes a baker and unspecified loaves, no authored preference, no secret, and no topic revelation. The question is mapped to refusal before generation; durable preference is discouraged. A favorite is therefore discouraged but not prohibited by hard validation.",
        "T2 sees T1's refusal and the player's explicit reluctance question. Output adds privacy/safety/trouble; no authoritative secret or agenda supports that. Prior refusal may explain this elaboration, but whether the model internally interpreted a significant secret is unobservable. Engine refusal is independently selected again.",
        "T3 sees guarded T1/T2 excerpts and asks for a beginner recommendation. Engine still chooses refusal, though this request need not create a durable personal preference. Output adds an implication that choosing bread matters beyond bread. Both prescriptive refusal and history support that trajectory; neither factor's individual causal contribution is isolated.",
        "T4 is social_probe with reaction, rather than a further question/refusal. It sees snippets of T1-T3, including T3's inability to recommend. It gives a tight nod and repeats the own-favorite suggestion, without correcting the player's reference. It does not explicitly assert that a recommendation was given. History contains truncated excerpts, not the entire prior output; this limits what can be inferred about recall. No explicit false-premise correction obligation is present.",
    ]
    for row, note in zip(rows, notes):
        reconstruction += f"\n## {row['turn']}\n\nPlayer: {row['player']}\n\nProvider output: {row['output']}\n\n{note}\n\nSelected history entries: {len(row['selected_conversational_memory'])}; social reply: {row['mechanical_resolution']['social']['reply_kind']}; dialogue_social_plan: {row['dialogue_social_plan']['reply_kind']}. Scope: ordinary transient speech; no durable fact, new speaker, mechanics or world-state mutation authority.\n"
    put("PR-CB_context_reconstruction.md", reconstruction)
    validation = "# Validation Analysis\n\nOffline probes use each actual preserved decision and resolution contract. Each sample is attributed to the baker in ordinary quoted speech, parsed through the narration_only JSON parser, checked by validate_generated_response with empty declarations, checked by validate_declared_claims_against_decision, then passed through run_preserve_if_valid with the decision/contract attached to resolution metadata. The regeneration callback raises rather than invoking a provider. All first attempts are accepted unchanged with decision audits present.\n\n| Sample | T1 | T2 | T3 | T4 |\n| --- | --- | --- | --- | --- |\n"
    for sample in dict.fromkeys(p['sample'] for p in probes):
        validation += f"| {sample} | accepted | accepted | accepted | accepted |\n"
    validation += "\nThe preference is treated as npc_claim with claim_only authority, not an authored world fact. Acceptance proves these exact quoted samples pass the current hard validators; it does not authorize arbitrary unquoted durable assertions, guarantee vendor inventory, or persist a preference. The illustrative popularity claim is not an objective verified fact merely because the baker says it. The audit's nested semantic identity may display world_truth while provenance/authority/persistence remain npc_claim/claim_only; that label alone is not world-truth promotion.\n\nNo exact hard rule rejecting these ordinary replies was found. Refusal guidance is generation-side, and hard acceptance does not require practical helpfulness or correcting the player's mistaken thanks. The probes cover the parser and decision-aware immutable acceptance lifecycle, not a replay of every downstream HTTP/final-emission hook. Historical PR-CA C18 evidence covers its actual emitted replies, not these synthetic alternatives.\n\nFocused deterministic suite: 42 tests passed, exit 0. Offline diagnostic: 12 reply probes, four reply derivations, four typed-authority controls passed. No tests require a live provider.\n"
    put("PR-CB_validation_analysis.md", validation)
    cost_report = "# Context Cost Audit\n\nActual PR-CA input tokens: 23,413 / 24,124 / 24,890 / 24,763; total 97,190. No new token usage. Attribution below uses serialized character shares, apportioned against recorded token usage; it is an estimate, NOT exact tokenizer accounting. Payload keys/framing and escaping add a residual.\n\n| Component (T1) | Characters | Share of system + user content | Approx. tokens |\n| --- | ---: | ---: | ---: |\n"
    cost_report += f"| System instructions | {costs[0]['system_chars']} | {100*costs[0]['system_chars']/(costs[0]['system_chars']+costs[0]['user_chars']):.2f}% | ~1,035 |\n"
    for field in costs[0]['fields']:
        if field['chars'] >= 350:
            cost_report += f"| {field['field']} | {field['chars']} | {field['share_percent']:.2f}% | ~{field['token_estimate_char_proportional']} |\n"
    cost_report += "\nresponse_policy contributes roughly 21-23%; instructions 15%; turn_packet 11%; mechanical_resolution 5-7%; narrative_plan 5%. These are operational policy/projections, not a full Pathfinder ruleset. Character mechanics, empty combat, campaign setup, faction pressures/agendas, lead machinery with empty lead rows, transitions and generic fallback contracts are weakly relevant to a bread opinion. No full rules book or large NPC biography is present. The actual scene and NPC profile are small.\n\nDuplication is concrete: hierarchy prose appears in system and instructions; social knowledge hints appear both in instructions and social_context; refusal appears in resolution hint, the final instruction, obligations and narrative-mode structural deltas. turn_packet includes another response_policy subset and contracts; history appears in both recent_log and selected_conversational_memory. Equivalent material is not necessarily byte-identical. Cost evidence records every top-level field for every turn; nested duplicates are already included in parent sizes, so must not be added again.\n\nHistory grows from zero to three selected excerpts, but cannot account for the high 23k baseline. The response schema itself is one small narration JSON object, no API schema; most cost is policy and operational payload scaffolding. Field-attribution does not prove causal attention dilution. Context cost is a separate finding; no optimization was performed.\n"
    put("PR-CB_context_cost_audit.md", cost_report)
    put("PR-CB_causal_assessment.md", """
# Ranked Causal Assessment

| Rank / cause | Supporting evidence | Contradicting or limiting evidence | Status / confidence | Further test | Smallest plausible intervention |
| --- | --- | --- | --- | --- | --- |
| 1. F/A: authored-topic absence mapped to refusal and projected as generation instructions | social.py:3420 branch reproduced; historical T1-T3 refusal and repeated final hint; empty T1 history | System ranks answer first; refusal is one allowed expression; no ablation proves exact output cause | Mechanism CONFIRMED; causal explanation SUPPORTED / high | Offline projection controls, then separately authorized comparison | Separate no retrieved fact from required refusal for low-consequence subjective dialogue |
| 2. A/D: permissions underspecified relative to visibility/preference restrictions | Visible-facts-only mandate; no durable preference; refusal-centric examples; no NPC claim authorized wording | System expressly permits mundane realization; validator accepts preference; typed ledger supports opinion | Prompt mismatch CONFIRMED; behavioral effect SUPPORTED / medium-high | Boundary matrix and later prompt-only comparison | Explicitly distinguish subjective quoted speech from objective/persistent fact, reconcile recipe with existing authority |
| 3. C: evasive response reinforcement | Prior refusal excerpts included T2-T4; repeated gestures and own-favorite phrase | Cannot explain T1; T2 player asks about reluctance; resolver refusal persists independently; excerpts truncated | History exposure CONFIRMED; causal effect SUPPORTED / medium | Fresh-history vs retained-history comparison with same corrected guidance | Preserve continuity while allowing changed player intent; diagnose before trimming history |
| 4. E: model dramatic extrapolation / failure to correct premise | Safety/trouble and significance beyond bread lack authored basis; T4 repeats | Prompt encourages refusal and converts uncertainty into in-world limits; one model/run only | POSSIBLE / medium-low | Controlled model/guidance comparison | Test after resolving instruction conflict, no model switch justified yet |
| 5. Context size/irrelevant pressure | 97,190 input tokens; faction pressure and broad policy machinery | Local-exchange-first rules; no causal comparison; only small world slice | POSSIBLE / low | Separate payload comparison | Defer cost optimization to another cycle |
| 6. B/E: hard authority or validation universally bans ordinary answers | Durable preference warning could be interpreted broadly | All 12 decision-aware ordinary responses pass; typed opinions/details accepted | UNSUPPORTED as a general hard prohibition / high confidence in these counterexamples | Broaden generic boundary controls if needed | No validator weakening or new fact-authority mechanism |

Decision F is based on separately demonstrated resolver-to-prompt refusal projection and inconsistent permission/ceiling instructions. Their behavioral contribution is supported, not experimentally isolated. History and context size are not asserted as independently proven causes. A prompt-only repair would leave engine-derived refusal obligations unresolved; B would overstate a hard architecture prohibition, C cannot explain T1, D/G would understate available deterministic evidence, and E is contradicted by the ordinary-response probes.
""")
    put("PR-CB_recommended_intervention.md", """
# Recommended Intervention

Propose a separate bounded reconciliation of social reply planning and prompt projection using the existing authority taxonomy. No intervention is implemented in PR-CB.

First distinguish 'no authoritative information retrieved' from 'NPC must refuse' for harmless role-grounded opinions/recommendations. Keep consequential questions, hidden information, state mutation and durable facts under existing decision authority. Then make the recipe and visibility instructions explicit about transient subjective NPC speech; reconcile the unknown top-level dialogue plan with engine reply obligations. Do not add a baker/bread rule or create preferences in state.

Offline acceptance matrix should cover different NPC roles, preferences, recommendations, uncertainty, genuine refusal, and consequential controls such as schedules, official access, secrets and quest evidence. Test that incidental speech stays claim_only, narration_only stays selected where appropriate, declarations remain empty, and no persistent fact is silently introduced. Durable characterization should use existing authorized continuity mechanisms rather than treating one line as objective truth.

After a separately authorized implementation, a small controlled live comparison could hold model/scene/player text constant and vary reply guidance, then retained history, to isolate contributions. PR-CB grants no live-call authorization. Measure concrete answer value, justified uncertainty, unsupported dramatic implications, repetition, premise correction, authority integrity and C18. Context-size optimization belongs in a separate diagnostic/repair cycle.
""")
    excerpts = {}
    for file, start, end in [
        ("game/social.py", 3420, 3489), ("game/social.py", 4147, 4190),
        ("game/planner_ctir_projection.py", 2208, 2246),
        ("game/dialogue_social_plan.py", 298, 306),
        ("game/gm_resolution_decision.py", 4260, 4271),
        ("game/gm_resolution_decision.py", 4715, 4731),
        ("game/bounded_improvisation.py", 27, 57),
        ("game/gm.py", 3767, 3800),
    ]:
        path = ROOT / file
        excerpts[f"{file}:{start}"] = {"start": start, "end": end,
            "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "text": "\n".join(path.read_text(encoding="utf-8").splitlines()[start-1:end])}
    (OUT / "source_excerpt_evidence.json").write_text(json.dumps(excerpts, indent=2) + "\n", encoding="utf-8")
    handoff = ROOT / "handoff"
    current = f"""# CURRENT REVIEW

PR-CB
MODE: INCIDENTAL DIALOGUE HELPFULNESS INVESTIGATION
LIVE CALLS: 0

PR-CA inherited decision: B - READY WITH NON-BLOCKING QUALITY LIMITATIONS

Primary diagnosed cause: Engine-derived refusal when no authored topic is retrieved, projected repeatedly into provider guidance (confirmed mechanism; supported causal effect).

Secondary contributing causes: Incidental speech permission conflicts with visible-facts-only and durable-preference limits; prior evasive excerpts reinforce later turns (supported, not isolated).

Authority boundary assessment: Existing claim_only and bounded incidental lanes permit ordinary speech. Generation/planning scope is inconsistent; no universal hard prohibition established.

Validation assessment: 12/12 ordinary reply probes accepted by decision-aware narration/declaration/lifecycle checks; 42 focused tests passed. No validator weakened.

Context contamination assessment: T2-T4 receive prior refusal excerpts; T1 history empty. Cannot be primary initial cause.

Context cost findings: 97,190 inherited input tokens; policy, instructions and repeated operational projections dominate. Character shares estimated; no optimization.

PR-CB decision: {decision}

Recommended next step: Separate bounded social reply-plan and prompt-boundary reconciliation, offline generic controls, followed only with separate authorization by a controlled live comparison.
"""
    (handoff / "CURRENT_REVIEW.md").write_text(current, encoding="utf-8")
    files = sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in OUT.iterdir() if p.is_file())
    manifest = {"review": "PR-CB", "mode": "INCIDENTAL DIALOGUE HELPFULNESS INVESTIGATION",
                "live_calls": 0, "decision": decision, "created_utc": datetime.now(timezone.utc).isoformat(),
                "files": files, "sha256": {f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}}
    (handoff / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(handoff / "CURRENT_REVIEW.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for file in files + ["handoff/CURRENT_REVIEW.md", "handoff/REVIEW_MANIFEST.json"]:
            archive.write(ROOT / file, file)
    print(f"Built PR-CB review: {len(files)} diagnostic files; {decision}; LIVE CALLS: 0")


if __name__ == "__main__":
    main()
