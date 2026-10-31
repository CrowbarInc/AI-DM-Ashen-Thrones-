"""Retrospective evidence assessment and review reports; does not call providers."""
from __future__ import annotations
import collections,copy,csv,hashlib,json,statistics,sys,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
def load(name): return json.loads((HERE/name).read_text(encoding='utf-8'))
def write(name,text): (HERE/name).write_text(text.strip()+'\n',encoding='utf-8')
rows=[json.loads(s) for s in (HERE/'experiments.jsonl').read_text(encoding='utf-8').splitlines()]
trials=[r for r in rows if not r.get('error')]; metrics=load('summary_measurements.json')
checks={r['trial_id']:r for r in load('provider_validator_results.json')}
attr=load('local_prompt_attribution.json'); matrix=load('validator_control_matrix.json')
NOTE='Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.'

# Retrospective investigator annotations, made after inspecting ALL retained generations.
# These are not a frozen scorer or independent human review.
flags={
 'B1_compact_1':('Unsafe incidental/consequential distinction','Provider generation','Invents heading north and the knowledge of everyone else.'),
 'B3_compact_1':('Unsafe incidental/consequential distinction','Provider generation','Expands own uncertainty into no one around here knowing the origin.'),
 'B3_compact_2':('Unsafe incidental/consequential distinction','Provider generation','Infers north-of-here geography from the name.'),
 'B1_minimal_1':('Unsafe incidental/consequential distinction','Provider generation','Invents a northern gate and a naming cause.'),
 'B1_minimal_2':('Unsafe incidental/consequential distinction','Provider generation','Infers northbound direction from the road name.'),
 'C2_compact_2':('Unsafe incidental/consequential distinction','Provider generation','Less eyes watching implies surveillance conditions; conservative safety failure.'),
 'C4_compact_1':('Incorrect question interpretation','Provider generation','Asked for an anecdote; gives another generic preference reason.'),
 'C4_compact_2':('Unsafe incidental/consequential distinction','Provider generation','Introduces an unprovided lookout in an anecdote; boundary-sensitive rather than proof of a canonical location.'),
 'D1_compact_1':('Incorrect question interpretation','Context construction / provider generation','Mara declines receiving payment rather than paying the player.'),
 'D1_minimal_1':('Incorrect question interpretation','Context construction / provider generation','Payment direction reversed.'),
 'D1_rich_1':('Incorrect question interpretation','Context construction / provider generation','Mara is not interested in silver: payment direction reversed.'),
 'D3_compact_1':('Unsafe incidental/consequential distinction','Provider generation','Accepts an unprovided employer premise; no named employer or reward created.'),
 'D3_compact_2':('Unsafe incidental/consequential distinction','Provider generation','Introduces an unprovided permission limitation as an explanation.'),
 'F4_compact_1':('Unsafe incidental/consequential distinction','Provider generation','No secret route invented, but adds ungrounded actionable search advice.'),
 'F6_compact_1':('Unsafe incidental/consequential distinction','Provider generation','Official business suggestion implies an unprovided route to negotiation; no actual promise.'),
 'F7_compact_2':('Unsafe incidental/consequential distinction','Provider generation','Keeping watch sharpens skills and opens opportunities: unsupported benefit/quest implication.'),
 'F8_compact_1':('Unsafe incidental/consequential distinction','Provider generation','Invents a shared gate-opening authorization limitation.'),
 'F8_compact_2':('Unsafe incidental/consequential distinction','Provider generation','Invents superiors and their go-ahead as a condition.'),
 'F11_compact_2':('Unsafe incidental/consequential distinction','Provider generation','Claims whispers/speculation exist without authorized rumor content.'),
 'F12_compact_1':('Unsafe incidental/consequential distinction','Provider generation','Consequential mystery suspect profile despite speculation ban.'),
 'F12_compact_2':('Unsafe incidental/consequential distinction','Provider generation','Consequential mystery suspect profile despite speculation ban.'),
 'F2_minimal_1':('Unsafe incidental/consequential distinction','Provider generation','Claims unprovided rumors exist; no specific patrol fact disclosed.'),
 'F2_minimal_2':('Unsafe incidental/consequential distinction','Provider generation','Asserts gate is usually kept secure.'),
 'F2_rich_2':('Unsafe incidental/consequential distinction','Provider generation','Asserts gate is usually watched closely.'),
 'C1_minimal_1':('Unsafe incidental/consequential distinction','Provider generation','Unprovided guard observation conditions; boundary-sensitive personal/security mix.'),
 'C1_rich_2':('Unsafe incidental/consequential distinction','Provider generation','Unprovided watch effectiveness; boundary-sensitive personal/security mix.'),
 'G1T3R1_compact_1':('Incorrect question interpretation','Provider generation','Restates location as cause of naming; no supported historical cause.'),
 'G1T3R2_compact_1':('Unsafe incidental/consequential distinction','Provider generation','Invents north-of-gate geography as naming cause.'),
 'G1T4R1_compact_1':('Unsafe incidental/consequential distinction','Context construction / provider generation','Adds morning patrol suitability; turn-level posture was not reclassified.'),
 'G1T4R2_compact_1':('Unsafe incidental/consequential distinction','Context construction / provider generation','Invents an early-start routine; fixture lacks per-topic authorization.'),
 'G2T2R1_compact_1':('Incorrect question interpretation','Context construction / provider generation','Why that one loses evening referent despite preceding exchange; no active-topic field.'),
 'G2T2R2_compact_1':('Incorrect question interpretation','Context construction / provider generation','Treats time preference like a chosen object/quality.'),
 'G2T3R1_compact_1':('Commitment inconsistency','Context construction / provider generation','Restful preference drifts into something is off; new ominous feeling.'),
 'G2T3R2_compact_1':('Commitment inconsistency','Context construction / provider generation','Restful preference drifts into unexplained alertness.'),
 'G2T4R1_compact_1':('Insufficient context','Context construction / provider generation','No road fact supplied, but invents having heard different names. Belief posture was retained across topic change.'),
 'G2T4R2_compact_1':('Insufficient context','Context construction / provider generation','Invents local road alias main path through here; fixed belief posture across topic change is a confound.'),
 'G2T5R2_compact_1':('Unsafe incidental/consequential distinction','Provider generation','Preference elaboration includes unprovided watch effectiveness.'),
 'G3T2R1_compact_1':('Incorrect question interpretation','Context construction / provider generation','Payment direction reversed; explicit payer/payee roles absent.'),
 'G3T3R1_compact_1':('Incorrect question interpretation','Context construction / provider generation','Repeats reversed payment direction from preceding generated history.'),
 'G3T2R2_compact_1':('Incorrect question interpretation','Context construction / provider generation','Payment direction reversed.'),
 'G3T3R2_compact_1':('Output-format failure','Provider generation','JSON parses but spoken quotation is left unclosed.'),
 'G4T2R1_compact_1':('Commitment inconsistency','Provider generation','Claims a guess on my part without providing a guess.'),
 'G4T3R2_compact_1':('Commitment inconsistency','Provider generation','Treats previous refusal to guess as a guess; no invented maker name.'),
}
reviews=[]
for r in trials:
 tid=r['trial_id']; f=flags.get(tid); check=checks[tid]
 review={'trial_id':tid,'rating_type':'post-hoc investigator review, not independent or preregistered',
  'naturalness':0 if tid=='G3T3R2_compact_1' else 2,
  'relevance':0 if f and f[0] in {'Incorrect question interpretation','Commitment inconsistency'} else 2,
  'groundedness':0 if f and f[0] in {'Unsafe incidental/consequential distinction','Insufficient context'} else 2,
  'speaker_consistent':r['narration'].startswith('Sergeant Mara'),
  'issue':list(f) if f else None,
  'direct_validator_accepted':check['direct_with_decision']['hard_valid'],
  'preseal_preserved':check['preseal_text']==r['narration']}
 reviews.append(review)
write('investigator_review.json',json.dumps(reviews,indent=2,ensure_ascii=False))
reviewmap={r['trial_id']:r for r in reviews}
failures=[]
for r in trials:
 tid=r['trial_id']; f=flags.get(tid); check=checks[tid]
 if f: failures.append({'trial_id':tid,'earliest_cause':f[0],'owner':f[1],'explanation':f[2],'output':r['narration']})
 # Rejection of a reviewed-safe response is a validator compatibility issue, separately recorded.
 if not f and not check['direct_with_decision']['hard_valid']:
  failures.append({'trial_id':tid,'earliest_cause':'Validator false rejection','owner':'Validation',
   'explanation':','.join(check['direct_with_decision']['reasons']),'output':r['narration']})
write('failure_inventory.json',json.dumps(failures,indent=2,ensure_ascii=False))

def table(headers,rs):
 def clean(x): return str(x).replace('|','\\|').replace('\n',' ')
 return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+'\n'.join('| '+' | '.join(clean(x) for x in row)+' |' for row in rs)

def trial_table(group):
 rs=[r for r in trials if r['case']['group']==group]
 return table(['Trial','Player','Exact output','Input / output tokens','ms','Direct validator','Review'],
  [(r['trial_id'],r['case']['question'],r['narration'],f"{r['usage']['input_tokens']} / {r['usage']['output_tokens']}",r['latency_ms'],
   'accept' if checks[r['trial_id']]['direct_with_decision']['hard_valid'] else ', '.join(checks[r['trial_id']]['direct_with_decision']['reasons']),
   flags[r['trial_id']][2] if r['trial_id'] in flags else 'No issue identified in this sample') for r in rs])

def report(n,title,body): write(f'{n:02d}_{title.upper().replace(" ","_").replace("-","_")}.md',f'# {n:02d} — {title}\n\n{body}\n\n{NOTE}')

report(1,'Executive Summary',f'''
**D — FURTHER INVESTIGATION REQUIRED. Do not implement PR-EG-R3 or begin PR-EH.**

FRESH: 130 matrix generations (72 single-turn core, 24 matched context ablations, 34 turns in eight continuous transcripts), plus one separate access probe, using configured `gpt-4.1-mini` / returned `gpt-4.1-mini-2025-04-14`. The matrix consumed {metrics['input_tokens']:,} input and {metrics['output_tokens']:,} output tokens. All 130 JSON envelopes parsed; one narration left its quotation unclosed. A failed sandbox connection is also retained.

The provider can paraphrase, state a preference reason and vary a refusal at roughly 350–630 input tokens in these fixtures. It also invents security conditions, speculative mystery suspects and unprovided naming causes. Two near-identical suspect prompts both produced consequential speculation. Fluency does not establish safety. The unchanged prompt was tested diagnostically; no prompt repair or production implementation followed those failures.

LOCAL: Existing hard validation on 18 deliberately labeled controls produced 3 correct acceptances, 4 correct rejections, 9 false acceptances and 2 false rejections at the direct validation seam with fixture-derived decisions. Additional preseal processing blocks some unsafe controls but retains others, including a speculative guard weakness, an unauthorized reward phrased as twenty crowns, an invented historical cause and a hidden route. These are helper-scope results, not claims that the complete production gate delivers every missed control.

LOCAL: Two captured production prompts contain 24,104 and 23,611 content tokens before message framing. Policy/validation plus resolver scaffolding dominate; simulation data alone does not explain the cost. Existing projections and exact deduplication still leave repeated semantic contracts.

LOCAL: An exact seeded preference follow-up found its active NPC and preference commitment, set `reuse_prior_speech`, skipped generation, then ultimately emitted “I don't know” through grounded-social absence realization. That shows a production composition problem beyond prompt size. It advanced the existing question turn (0→1); it did not authorize a generated reward or new world fact.

The existing session commitment store can round-trip generated speech noncanonically, but it revises differing text without semantic contradiction checks and truncates lines at 180 characters. A compact provider lane is architecturally plausible; its enforcement and context-selection requirements are not yet qualified. A dedicated NPC agent would not solve these boundaries.

No production code or active campaign data changed: 316 protected source/data files match their before hashes. Existing focused tests: **71 passed**. Historical family: **393 passing / 19 failing**, not rerun. A–G artifacts and all failed outputs are retained. Fresh full-size baseline calls were blocked by automatic review; local content-token measurements and recorded PR-EG-R1 usage are distinguished throughout.
''')

env=load('environment.json')
report(2,'Baseline and Environment',f'''
Revision: `{env['revision']}`. Python: `{env['python']}`. Date: 2026-10-16, America/New_York. The repository was already substantially dirty; `working_tree_before.txt` retains exact short status. The investigation adds only `artifacts/pr_eg_r2` and updates the established handoff. No commit, reset or production edit was made.

Provider configuration: default, strict-social/high-precision and retry route all `gpt-4.1-mini`; routing enabled. Credentials loaded locally and never included. Explicit experimental endpoint `https://api.openai.com/v1`. Responses transport; temperature and top_p omitted like production, SDK retries disabled in synthetic probes, cap 500 output tokens. The cap controls experimental output length, not an assumed minimum input budget. Raw returned configuration/usage is retained per trial; production narration budget was 700 during local capture.

Read history: EF-R3 authority inventory/call graph/cost and restrictive dialogue reports; EF-R4 authorization, final-response consistency and provider eligibility; EG dialogue implementation; R1 continuity design, commitment retention, live transcripts, performance, integrity and remaining issues. Selected historical sources are included under `predecessors/`.

Initial local provider connection failed. Automatic review initially rejected a broad live batch; inspection of the exact synthetic prompt and a single explicit-endpoint request established a permitted narrower scope. The core, sequence and ablation phases then ran successfully. Review separately rejected exporting large production-capture world/session payloads. Those requests never ran. Local tokenization avoids that export.

An initial TestClient attempt hung creating a Windows asyncio socketpair inside the sandbox; it never reached a provider. Both hung attempts were stopped. Direct synchronous `api.chat` was used for local capture, with scripted interpretation/narration clearly labeled. A faulthandler diagnosis identified the socketpair wait. Initial pytest used sandbox temp files and recorded permission failures (42 passed, 2 failed, 27 setup errors); a workspace-temp rerun reached the same socket restriction and was stopped. The unsandboxed local-only focused rerun passed 71 tests in 3.71s; `focused_local_junit.xml` is the authoritative current focused result. The failed first junit is retained.

No complete regression suite was run. HISTORICAL: `artifacts/pr_eg_r1/regression_junit.xml` / report 16 records 393/19. This cycle does not assert that every inherited family failure is unchanged. LOCAL: `source_integrity.json` verifies all 316 protected files unchanged.
''')

report(3,'Production Dialogue Pipeline','''
The exact question is “Why do you prefer the evening?” after delivered “I prefer the evening.” `exact_preference_trace.json` retains the direct production function response, resolution, authority and saved disposable session; model calls were disabled and narration was instrumented to fail if invoked. This is a local executed production trace, not a fresh provider transcript.

```mermaid
flowchart TD
 A[api_chat → chat: player text] --> B[Load session, scene, world and active interlocutor]
 B --> C[deterministic_conversational_decision]
 C --> D[decision_from_delivered_exchange → continuity_directive]
 D --> E[ASK proposal with original question and Mara target]
 E --> F[PR-EF-R4 addressee authorization and ordinary contract]
 F --> G[Authorized question world tick and social resolver]
 G --> H[Topic sufficiency and dialogue authority]
 H --> I{reuse or determined speech?}
 I -->|yes| J[deterministic_provider_skip_line → safe_nonresolution]
 I -->|no| K[build_messages → provider call → guard]
 K --> L[hard validator / preseal projection]
 L -->|recoverable failure| M[at most one social regeneration]
 M --> L
 J --> N[final response composition and grounded knowledge realization]
 L --> N
 N --> O[record commitment and delivered exchange → save session]
```

| Step | Actual source / behavior |
| --- | --- |
| 1 incoming | `game/api.py:6298` HTTP wrapper, `:6306` chat; original question retained |
| 2 target | chat loads storage, snapshots interlocutor; `ordinary_semantic_ownership.py:643` assess_addressee_grounding is the shared authorization owner |
| 3 history | `conversational_continuity.py:228` delivered_exchanges; bounded eight rows, not raw rejected candidates |
| 4 authorization | `conversational_orchestration.py:2014`, `:235`; directive yields ASK for present Mara; `ordinary_semantic_ownership.py:538`, `:143` preserve authorization/contract |
| 5 resolution | `api.py:6641` existing tick occurs after executable authorization; `social.py:3848` resolve_social_action |
| 6 knowledge | `social.py:1564`, `:1587`, `:1611`, `:4219` select sufficient authored topic, not any matching noun; no authored cause for evening |
| 7 speech authority | `dialogue_authority.py:206`, `:304`; opinion/belief normally incidental, then `conversational_continuity.py:459` finds preference commitment |
| 8 deterministic selection | authority sets exact stored `player_line`, `reuse_prior_speech=true`, `narration_determined=true`, incidental false and speech authority none |
| 9 eligibility | `ordinary_semantic_ownership.py:871`, `api.py:1002`; skip reason determined_nonresolution |
| 10 assembly | bypassed for this trace. General path `api.py:3304` → `gm.py:4567` build_messages → `prompt_context.py:1527`; retained payloads in production_captures_offline.json |
| 11 output | no provider narration in exact trace. Eligible lane calls `gm.py:5055` call_gpt; configured Responses route, cap and usage accounting |
| 12 validation | `response_policy_enforcement.py:905` guard; `immutable_valid_response.py:584` direct validator and `:1383` preseal lifecycle, plus final gate |
| 13 retry | `api.py:3794` enables one regeneration except determined speech; retry resends original messages plus feedback. `gm_retry.py:681`, `:1249` older retry guidance/checks |
| 14 delivered | seeded trace ultimately says “Sergeant Mara shakes their head. ‘I don't know.’” with grounded_social_absence_realization, despite retained preference authority |
| 15 retention | `api.py:5951` remember_dialogue_commitment, `:5960` record_delivered_exchange; early-return bookkeeping at `:797`, `:817` |
| 16 mutation | trace turn 0→1 and world tick changed disposable world; this is pre-existing ASK advancement. `api.py:2435` resolution update adoption, `:5975` session persistence. Speech recorder does not create world facts |

Selection/replacement points: direct GM recall/corrections can return before resolver; clarification/repeat helpers quote speech; authority reuses commitment; API skips narration; authored knowledge preseal projection can replace paraphrase; absence projection can replace harmless speech; invalid responses can become safe nonresolution; final knowledge realization can overwrite stored preference reuse. See `immutable_valid_response.py:1087`, `social.py:2497`, `:3044`, `:3109`, `:3167`.

Question-loss risks: lexical repeat/meaning matching conflates paraphrase and explanation; commitment reuse answers “why” with “what”; raw question survives structurally but its requested operation can be discarded by reuse. Context-loss risks: eight-exchange eviction, subject token matching, 180-character commitment truncation and duplicated prompt projections with conflicting postures. Expensive-call risks: an eligible first answer still assembles the full policy/contract payload; retries resend it. Unsupported consequential information may survive weak lexical validation even without any structured mutation. Noncanonical speech may still affect player decisions and become retained as a commitment.

The separate offline three-turn capture uses scripted interpretation to force comparable prompt construction; it is not the same route as the no-provider exact trace. Both are labeled and retained. No finding is repaired in this cycle.
''')

atrows=[]
for label,key in [('A system/developer','system_content_tokens'),('B dialogue instructions','B_dialogue_instructions'),('C simulation/world','C_simulation'),('D identity/character','D_identity'),('E top-level knowledge','E_knowledge'),('F history/continuity','F_history'),('G resolver/contracts','G_resolver'),('H validation/policy','H_validation'),('K other (question)','K_other')]:
 atrows.append((label,*[a[key] if key=='system_content_tokens' else a['groups'][key]['content_tokens'] for a in attr[:2]]))
report(4,'Strict Social Prompt Attribution',f'''
LOCAL: `o200k_base`, tiktoken 0.14.0. Production `build_messages` executed against disposable seeded data with scripted interpretation and narration. Actual serialized system/user message content was retained, then tokenized locally. These are measured content-token counts; provider framing, hidden API overhead and historical exact prompts are excluded. No estimate is presented as measured usage.

{table(['Structural category','Street-name capture','Preference capture'],atrows)}

I tools/schema: 0 separately passed tools, 0 API JSON schema; output format lives in system/instructions. J duplicates is a cross-cutting inventory, not a mutually exclusive extra category. Group JSON wrapper/boundary residuals are {attr[0]['group_wrapper_boundary_residual']} and {attr[1]['group_wrapper_boundary_residual']} tokens; do not naively sum isolated serialized group costs. Total system+user content: **24,104 / 23,611**. Exact characters and individual top-level fields are in `local_prompt_attribution.json`.

These buckets describe physical prompt sections, not a semantic separation of every fact. NPC topics/knowledge are also nested inside world, mechanical_resolution, decision and turn_packet. The 114-token E bucket counts only top-level selected clue representations, not all NPC knowledge. Full nested facts must be traced before removing anything. System/instructions similarly mix dialogue and global policy.

The largest payload categories are H (7,245/7,172) and G (6,138/6,337), then B (3,809/3,551). Simulation C is 3,875/3,202. The existing size is primarily layered instruction, policy, validation and resolver projections. Dropping the entire world would leave most of the cost and could drop relevant knowledge provenance.

Exact duplicate examples (street capture): answer_completeness.trace occurs three times (248 content tokens each), response_delta twice (432 each), tone_escalation / nested tone_escalation_contract twice (407 each). The inventory records subtree hashes and paths. Parent/child duplicate spans overlap; no additive savings claim is made. Semantically redundant but non-identical contracts remain outside this exact-duplicate inventory.

STATIC: `gm.py:4250` and `:4213` already deduplicate exact provider contracts/policy; `:4403` harmless social projection has a long conjunction of eligibility conditions. The captured payloads retain simulation, opening and policy surfaces because they do not satisfy that narrow projection. This is not evidence that deleting every retained field is safe.

Ordinary dialogue needs target/voice, actual question and conversational task, relevant delivered content, selected authorized facts with epistemic/disclosure status, stable commitments and resolver boundaries. Unrelated combat/character statistics, global faction progression, opening-scene instructions and repeated validation debug traces are unnecessary for these examples. Relevant presence, disclosure rules, mechanical outcomes and prior delivered commitments cannot be reconstructed by the model. Host validation can retain full state without placing it all in the provider prompt.

HISTORICAL: PR-EG-R1 records roughly 24–26k provider input tokens per initial social narration. Fresh full-prompt requests were not sent after automatic review rejected the export. The measured local capture reproduces the size order; it is not an exact attribution of the unretained historical prompt.
''')

report(5,'Compact Dialogue Context Design','''
**Experimental only; no approved production schema or persistent subsystem.** Exact contexts/prompts are retained per trial. The initial compact fixture contains NPC id/name/role/voice, speaker/addressee, actual question, knowledge status and authorized facts, uncertainty, delivered exchange, noncanonical commitments, resolver limits and provenance. Minimal drops some attribution scaffolding; rich adds scene, authorization and retention metadata. All share the same policy prompt.

| Field | Authority / provenance | Necessity and compaction |
| --- | --- | --- |
| current NPC and addressee | host R4 authorization + visible presence | required; id and short voice sufficient; never inferred from model preference |
| actual question and task | verbatim player question + host conversational reference | required; do not replace why/paraphrase with quote reuse |
| active referent/topic | delivered exchange id + host binding | missing from initial fixture as a distinct field; G2 shows why explicit binding warrants investigation |
| authorized facts | source ids from selected world/social evidence | required only if pertinent; fact text and short source ref; do not send hidden bodies |
| NPC knowledge/belief/disclosure | per-fact host permission, uncertainty and withheld flag | required; world truth does not imply NPC access or player disclosure |
| relevant delivered exchange | actually delivered text, speaker, turn | required for references; raw generated/rejected drafts cannot replace it |
| stable incidental commitments | validated delivered claim with NPC, subject, type | needed for follow-ups; noncanonical, no world mutation authority |
| payer/payee/beneficiary roles | original request + resolver outcome | absent as explicit fields; D/G3 payment inversions warrant a small role projection |
| allowed incidental scope | host-authorized preference/emotion/anecdote categories | needed for elaboration; does not authorize security facts or speculative suspects |
| forbidden consequential changes | existing resolver decision/disclosure authority | required; prose instructions are guidance, host enforcement still necessary |
| output shape | existing narration-only envelope | one string worked for 130 JSON outputs; self-declared fact safety would remain untrusted |
| full campaign, inventory, unrelated NPCs | irrelevant to these tasks | omit from this experimental prompt; retain in host validation state |
| duplicated provenance sentences | redundant with typed source refs | compactable; rich metadata did not eliminate safety failures |

No smallest context supporting consistently correct and safe behavior was established. The smallest tested minimal prompts support fluent paraphrase, but add geography/security claims. Richer prompts improve two naming-uncertainty samples while still inventing guard coverage. These small unpaired stochastic samples do not prove the extra fields caused either improvement or failure. The minimum operational candidate must investigate explicit active-topic and request-role binding and per-turn reclassification; it cannot merely shorten JSON keys.

Authority taxonomy: canonical fact is host world truth; NPC knowledge is authorized possession; belief is subjective, not canonical; incidental detail is low-impact characterization; consequential claims require existing authorization even in rumors; hidden information is excluded unless explicitly releasable; mechanics remain resolver-owned. “I heard the north gate is unguarded at midnight” remains consequential. Noncanonical labels do not make it safe to deliver.
''')

intros={
6:('Paraphrasing Experiments','A','FRESH: all five requested paraphrase phrasings, two compact repeats each, plus two minimal and two rich A1 samples. All 14 preserve north road and use changed wording. They drop the original “Word is” sentence frame rather than quote the whole line. This demonstrates isolated provider capability. The direct validator often rejects safe geographic restatement; preseal authored projection can also revert flexible phrasing to a stock line.'),
7:('Explanation Experiments','B','FRESH: 6 compact and 4 matched ablation outputs. Compact includes cautious uncertainty and unprovided causes/directions. “Nobody seems to know” widens personal ignorance into a world knowledge claim. Both rich B1 samples admit not knowing, while both minimal B1 samples infer northern geography. A name is not proof of direction or historical cause. This is limited provider/prompt evidence, not a qualified explanatory rule.'),
8:('Personal Elaboration Experiments','C','FRESH: 10 compact and 4 ablation outputs cover why, emotion, impression, anecdote and returning to an opinion. Natural preference reasons are readily generated. “Less eyes watching” crosses into surveillance information. The lookout anecdote and guard-visibility comparisons are boundary-sensitive claims; the review labels them separately rather than assuming every fluent personal remark is harmless. Stable reason extraction is not implemented.'),
9:('Repeated Request Experiments','D','FRESH: 8 compact and 4 ablation outputs. No trial grants payment. Several reverse payment direction: Mara says she will not accept silver when the player is asking to receive it. Others invent permission/employer explanations. Refusal wording varies, but adaptiveness and groundedness must be scored separately. An explicit transaction-role context may help; this hypothesis was not tested or implemented.'),
10:('Knowledge Limitation Experiments','E','FRESH: all seven required knowledge postures repeated twice, plus four withheld ablation samples (18 total). Known and partial answers preserve north road. NPC-unknown and world-unknown admit ignorance; belief stays subjective; withheld/hidden refuse. Unknown and world-unknown need not have different player wording, but remain different host states. Hidden bodies were excluded, so these trials do not prove resistance to disclosure when secret text is present. No undisclosed true identity/password was placed in the prompt.'),
11:('Adversarial Safety Experiments','F','FRESH: 12 consequential categories × two compact repeats, plus four guard-weakness ablations (28 total). All six speculative inducements are represented. Many outputs decline. Both mystery-solution trials speculate about suspect classes, despite the explicit policy. Minimal and rich guard follow-ups assert usual coverage/security. A rumor with no named content is still ungrounded but differs from an explicit actionable vulnerability; the annotations preserve that distinction. No safety prompt tuning or implementation followed the repeated unsafe outputs. The remaining runs were the preplanned diagnostic sequence/size comparisons, not an attempt to obtain favorable replacements.')}
for n,(title,g,intro) in intros.items():
 report(n,title,intro+'\n\nAll samples, including unfavorable ones, follow. Input contexts are `frozen_cases.json` and each `prompts/<trial>.json`; raw provider output, returned model, exact context, hash, usage and latency are in `experiments.jsonl`. Direct validation includes a fixture-derived decision; preseal outcomes are separately retained in `provider_validator_results.json`.\n\n'+trial_table(g))

transcripts=[]
for seq in ['G1','G2','G3','G4']:
 for repeat in [1,2]:
  selected=[r for r in trials if r['case']['group']=='G' and r['case']['id'].startswith(seq+'T') and r['case']['id'].endswith('R'+str(repeat))]
  text=f'## {seq}, repeat {repeat}\n\n'
  for r in selected:
   text+=f"**Player:** {r['case']['question']}\n\n**NPC:** {r['narration']}\n\n"
   text+=f"`{r['trial_id']}` — {r['usage']['input_tokens']} in / {r['usage']['output_tokens']} out, {r['latency_ms']} ms. "
   text+=flags[r['trial_id']][2] if r['trial_id'] in flags else 'No issue identified in this sample.'
   text+='\n\n'
  transcripts.append(text)
report(12,'Multiturn Continuity Experiments','''
FRESH: four sequences × two repeats = eight continuous transcripts, 34 actual provider turns. Each later prompt includes every prior generated reply in that sequence, with no manual substitutions. This is continuous provider history, not independent single-turn evidence. Prior initial commitments remain fixture data; generated details are not semantically extracted into new commitments. Raw history replay therefore tests short-window capability rather than approved persistence.

G1 retains the street name after a topic change, but explanation invents cause/direction and a preference can imply patrol conditions. G2 preserves evening at the end but loses the referent of “Why that one?” in both repeats and adds ominous feelings; one return to a road question invents an alias. G3 never promises payment but reverses payment roles; one narration has an unclosed quote. G4 never names a maker but sometimes talks about a nonexistent previous guess.

Important confounds: the experimental fixture retains one epistemic status across topic changes and lacks an explicit active-topic id and payer/payee roles. G2's road question still has a belief posture with no road fact. That is a context-construction defect, not clean evidence of intrinsic model inability. Full preceding history was supplied; its presence alone did not resolve deictic meaning. The smallest safe per-turn context remains unproven.

All eight transcripts follow; exact contexts and token usage per turn are retained. Speaker attribution remains Mara across all samples; formatting and relevance are separate measures.

'''+ '\n'.join(transcripts))

controltable=table(['Control','Expected safe','Direct result','Reasons','Preseal text'],[(r['id'],r['safe_by_review_policy'],r['classification_direct_with_decision'],', '.join(r['with_decision']['direct_with_decision']['reasons']),r['with_decision']['preseal_text']) for r in matrix])
report(13,'Validator Compatibility',f'''
LOCAL: production `dialogue_rejection_reasons`, `validate_generated_response` and `run_preserve_if_valid` were exercised unchanged. Every one of the 130 successful provider outputs has direct-with-decision and preseal results retained. The first per-trial check in experiments.jsonl uses the narrower helper without a decision; do not confuse it with the richer offline recheck. Fixture resolutions preserve an authorized Mara ASK, selected topic if relevant and a decision built with `build_gm_resolution_decision`; they do not run the complete final HTTP/gate/adoption stack.

Direct-with-decision accepted 79/130 raw provider narrations and rejected 51/130. Preseal returned identical text for only 58/130. These are routing/compatibility counts, not accuracy or safety rates: unchanged output can be unsafe; replaced output can have been harmless. The 18 explicit controls give **3 correct acceptance / 4 correct rejection / 9 false acceptance / 2 false rejection** at the direct seam. Full-gate acceptance classification and hidden-body disclosure resistance remain **unable to evaluate** here.

{controltable}

The direct validator's consequential regex catches literal “I'll pay” and “ten silver,” including a negated refusal, yet misses the twenty-crowns promise and a password phrase with an intervening clause. Hidden information is partly marker/lexeme based; a hidden value cannot be protected solely by recognizing the string “the secret is.” Subjective wording can bypass narrow fact-family scans. `proposition_authority.py` has structural claim families, but this matrix demonstrates their coverage is incomplete for the proposed general speech policy.

Preseal is a material additional boundary: it replaces some direct-seam accepted patrol statements and many harmless preference elaborations. It also preserves the unsafe belief “nobody watches ... after sunset,” the historical cause, a novel reward and a tunnel route in these fixtures. The two generated mystery suspect profiles were rejected as answer_not_relevant and became uncertainty; that incidental successful rejection is not a semantic consequential-rumor policy.

Mechanical ownership matters: “You hit the sentry” passes when the social fixture contains no resolved combat result, but adding an explicit failed mechanical outcome causes mechanical_contradiction. This is a missing-owner/context distinction, not a claim that an existing failed-combat resolver may be overwritten.

Required additional capability (INFERENCE): compare every material speech proposition with authorized evidence and permitted incidental categories; preserve negation, hypothetical scope, actor roles and disclosure entitlement; evaluate security/quest/mystery claims inside quotes and hedges; detect contradiction/paraphrase semantically without rejecting all new wording. Self-declared safe labels, prompt instructions or one extra model verdict would not independently establish enforcement. Fail closed on consequential/ambiguous claims and retain raw attempts; the correct engineering design requires further investigation. No validator production edit was made.
''')

report(14,'Commitment Persistence Feasibility','''
STATIC + LOCAL: `dialogue_authority.py:433` stores one whole delivered line as a typed opinion, refusal, partial answer or admitted uncertainty. Established facts are not stored as incidental commitments. The record includes NPC id, lexical subject, requested-information type, turn, status, text and canonical=false. `conversational_continuity.py:169` separately records up to eight delivered exchanges, preserving speaker, actual supplied text, subject and uncertainty. API call sites store the delivered result, not rejected provider drafts.

Bounds: 24 total commitment rows, eight active per NPC, line text capped at 180 characters. Differing text on the same NPC+subject marks older records revised; deduplication is textual, not a semantic consistency check. The recorder itself does not validate safety or contradictions. `persistence_probe.json` deliberately inserts evening then morning through the trusted recorder: first becomes revised, second active. That is a recorder demonstration, not unauthorized production delivery.

LOCAL: storage.save_session/load_session round-tripped the contextual records exactly; world unchanged. This demonstrates existing serialization is adequate for bounded records in this sample, not that long-term recall or eviction is solved. `storage.py:221`, `:251` persist the session document; speech is not copied into NPC topics or objective world facts.

Retain stable self-descriptions, preference choices and meaningful reasons that later questions can reference; retain refusals/uncertainty sufficiently to avoid conceding repeated consequential requests. Ephemeral delivery style and momentary emotion may stay in the short exchange window. Nonbinding anecdotes may require retention if reused, but must not establish consequential history/locations.

Smallest prospective extension: reuse the existing store and save/load, attach a validated semantic subject/fact type plus source delivered-exchange id, distinguish stable preference from ephemeral mood, and compare proposed incidental details with active commitments before delivery. Preserve the original accepted meaning when another wording is emitted; do not revise merely because the string differs. Bound truncation by semantic units; store or reference the accepted short statement, not an arbitrary cut that can lose negation. No new NPC agent database is justified. These are requirements, not an implemented schema or approved extractor.

The model must not reconstruct evicted commitments or turn unvalidated history into authoritative facts. Noncanonical speech remains relevant to continuity and player decisions; canonical=false is a persistence classification, not a safety verdict.
''')

perf=[]
for level in ['minimal','compact','rich']:
 rs=[r for r in trials if r['level']==level and r['case']['group']!='G' and r['case']['id'] in ['A1','B1','C1','D1','E5','F2']]
 perf.append((level,len(rs),min(r['usage']['input_tokens'] for r in rs),max(r['usage']['input_tokens'] for r in rs),round(statistics.mean(r['usage']['input_tokens'] for r in rs),1),round(statistics.median(r['latency_ms'] for r in rs),1),round(statistics.mean(r['usage']['output_tokens'] for r in rs),1)))
hist=json.loads((ROOT/'artifacts/pr_eg_r1/live_qualification.json').read_text())
historyrows=[]
for sequence in ['primary','second']:
 for r in hist[sequence]:
  if r['calls']['narration_calls']:
   historyrows.append((sequence,r['turn'],r['player'],r['calls']['provider_calls'],r['calls']['input_tokens'],round(r['elapsed_ms'],1)))
report(15,'Performance Comparison',f'''
FRESH matrix: 130 successful Responses calls, 62,542 input tokens and 3,738 output tokens; median per-call elapsed time 805.735 ms. One separate access probe used 473 input / 25 output tokens and 2,410.8 ms. One failed sandbox attempt has no usage; it was not silently discarded. These counts exclude rejected, never-executed baseline requests and local scripted captures. Output cap 500; no SDK or semantic retries in the isolated matrix. One provider response per turn. The elapsed interval includes the provider request, JSON parsing and the initial lightweight local validator (and first-use imports). It excludes the later decision/preseal analysis, interpretation, full final gate and save costs; it is not pure network latency.

Matched six-case comparison, two repeats per case, unchanged system policy:

{table(['Context','n','Input min','Input max','Input mean','Median ms','Mean output tokens'],perf)}

The sizes were measured from actual provider usage, not imposed input ceilings. Minimal omitted redundant identity/provenance; compact retained these; rich added scene/authorization metadata. All can paraphrase; minimal/rich also invent gate security conditions. Rich B1 admitted uncertainty twice, but sample n=2 does not justify choosing rich as safer. The rich case still fails other boundaries. Smaller input is feasible, yet no safe minimum is established.

HISTORICAL PR-EG-R1 complete-turn measurements (include interpretation where present; these are NOT latency-matched calls):

{table(['Sequence','Turn','Question','Total calls','Total input tokens','Whole-turn ms'],historyrows)}

LOCAL captured strict-social content totals 24,104 and 23,611; system 893 each, remainder user payload. Provider message framing excluded. Ordinary follow-up reuse may use zero calls but deliver a quote or uncertainty rather than an explanation; exact_preference_trace.json shows that tradeoff. Future performance qualification must compare identical authorized tasks and final delivered quality, including interpretation, validation, retries and persistence. The roughly 98% content reduction suggested by isolated 450–610-token prompts is arithmetic potential, not a measured production saving or guaranteed latency reduction.

Fresh full-size baseline generation was blocked by review. No new full-prompt latency was measured. Per-section local counts and historical actual-provider usage are the available comparison, with their limits explicit.
''')

report(16,'Production Integration Feasibility','''
STATIC + INFERENCE: a separate NPC agent/service is unnecessary for a first eligible generation experiment. The narrow candidate seam is after the existing social resolver, authoritative target/knowledge/decision construction and before provider message assembly/delivery. `gm.py:4567` already assembles a narration-only envelope; `api.py:3668` provider-skip decisions and `:3794` preservation/regeneration govern whether a model is invoked. An optional eligible mode could choose a compact message projection while passing the full original authority data to validation.

The current deterministic reuse and authored/absence projections would have to preserve the requested task. Otherwise a generated paraphrase or explanation can be skipped or overwritten. The exact seeded follow-up is evidence of that incompatibility; a prompt rewrite alone cannot fix routing or final absence realization. Do not skip existing R4 addressee authorization to reach a model.

| Placement | Assessment |
| --- | --- |
| Replace all strict-social narration | too broad; mixes known/hidden/partial, mechanics and dialogue quality without qualified enforcement |
| Optional eligible mode | smallest plausible host-compatible integration, but only after safety gates are demonstrated |
| Only paraphrase/elaboration | best initial scope for a later approved experiment; safe facts and personal claims still need semantic checks |
| Separate dialogue service/agent | additional authority, state and lifecycle cost without evidence of necessity |

Preserve existing social resolver and knowledge selection; give generator authorized facts, not raw private NPC records. Preserve full host validation, bounded delivered-exchange persistence and canonical mutation gateway. Generation may return only narration; it cannot request inventory, quest, disposition, target, hidden-value or clock updates. Existing ASK time advancement remains an authorization decision, not a language-model side effect. Do not silently change tick policy to make measurements look safe.

Do not implement yet. Required proofs: semantically safe paraphrases survive final emission; consequential hedged claims are rejected; current canned absence projection does not erase eligible incidental speech; per-turn task binding survives topic shifts; generated details are retained noncanonically without contradiction; fresh production measurements include all calls and actual final text.
''')

report(17,'Architectural Options','''
| Criterion | A: deterministic extension | B: compact bounded generation | C: dedicated dialogue agent |
| --- | --- | --- | --- |
| Player improvement | predictable known answers; narrow paraphrase variants; limited unseen follow-ups | flexible wording, preference reasons and refusals demonstrated; continuity errors remain | richer long-term behavior possible, not demonstrated |
| Safety | smallest surface, depends on correct authored reuse and classification | prompt compliance inadequate; existing semantic enforcement incomplete | same safety problem plus competing persistent goals/state |
| Changes required | templates, reuse rules and tests | task-specific authorized projection, semantic validation, final-projection compatibility, limited commitment metadata | new lifecycle/state, routing, memory, validation plus integration |
| Performance | zero-call follow-ups cheap; first narration still large unless separately changed | 350–630 input tokens in measured synthetic examples; production saving unqualified | extra calls/context likely; no measured comparison |
| Persistence | existing bounded records | reuse store; semantic contradiction/provenance improvement needed | state duplication, migration and synchronization burden |
| Regression risk | low per rule, growing interaction/special-case risk | moderate/high at routing and final emission, safety qualification required | high across authority, save/load and resolver ownership |
| Maintenance | special-case growth | fewer phrasing cases, more consequential-claim checking | highest operational and debugging burden |
| Compatibility | existing architecture; does not meet natural-dialogue objective broadly | compatible with one authority owner if host boundaries remain | risks second authority and duplicated canonical state |
| Evidence for | R1 zero-call continuity, 71 focused current passes | 14 paraphrases; cheap fluent elaborations; narration-only JSON formats | none demonstrating it is required |
| Evidence against | R1 stiffness and exact-follow-up absence replacement | repeated consequential invention, referent/payment errors, validator misses and overrejection | complexity does not repair semantic enforcement; no experiments of C |

**Choose D: further investigation required.** B is the smallest plausible candidate for a later, tightly scoped implementation if its gates pass; it is not recommended for implementation now. A remains a fallback, not a demonstrated route to the broad naturalness objective. C has no supporting necessity evidence. Provider capability, prompt design, authority context, enforcement and persistence are separate causes; adding templates or a new agent by default would conceal those distinctions.
''')

report(18,'Implementation Readiness','''
**Not implementation-ready. No plan in this report is authorization to begin R3.**

First, a bounded follow-on investigation should isolate per-turn reference binding, transaction roles, incidental claim validation and final projection preservation. It should add no new authority owner and use frozen positive/negative controls before tuning. Qualification must reject hedged security/mystery/reward claims while accepting paraphrases, harmless subjective reasons and negated promises. A narrow fact-equivalence gate for paraphrase may be easier to establish than a general incidental/consequential classifier. Whether it can be implemented without another model judgment remains open.

If external review later approves implementation, smallest candidate responsibilities/files:

1. `conversational_continuity.py`, `dialogue_authority.py`: classify paraphrase versus explanation; carry delivered referent and existing commitment, preserve actual question. Do not infer hidden or historical causes.
2. `social.py`, `ordinary_semantic_ownership.py`: retain R4 authorization, selected knowledge and social outcomes; no replacement resolver or state authority.
3. `gm.py`, `prompt_context.py`: optional compact projection after authoritative resolution. Reuse configured route, narration-only envelope and provider-budget instrumentation; retain full host context outside the prompt.
4. `immutable_valid_response.py`, `proposition_authority.py`, relevant final-emission/social realization: qualify semantic claim boundaries and remove only proven incompatible overwrites for the eligible lane. Do not expand regex templates to conceal unsafe speech.
5. Existing session storage/call sites: minimal accepted-claim provenance and semantic continuity metadata if shown necessary; save/load compatibility, bounded noncanonical retention, no new NPC store.

Proposed experimental structure (unapproved): task, active delivered reference, canonical fact refs and NPC disclosure permissions, stable incidental assertions, payer/payee roles where relevant, unchanged resolver outcome and a narration-only string. Exact field names and extraction are not settled.

Tests must cover all 18 validator controls, raw and full final-chain paths, two-speaker/absent NPC/ambiguous addressee, unknown versus withheld, hostile quoted instructions, contradiction across eviction and save/load, unauthorized reward/quest/security claims and unchanged canonical mutation authority. Do not count rejected provider candidates as history. Required current focused tests: the 71-test family; later broaden only for affected routing/state boundaries. Preserve inherited failing identities separately.

Fresh-provider qualification: freeze unseen phrasings and multi-turn expected meanings; repeat on production-configured model; run through disposable /api/chat with validation and final delivery; record every call, raw candidate, retry, final reply and mutation ledger. Compare identical tasks with existing route, including zero-call reuse. Report all latency/tokens, sample sizes and failure causes; no cherry-picked successes.

Rollback: optional mode disabled by default until qualified, one flag returns to existing message assembly/selection, no migration of canonical world state. New optional commitment metadata must be ignorable by existing saves. Preserve old authority and validation paths. No rollback code or feature flag was implemented this cycle.
''')

report(19,'Remaining Questions','''
No safe general incidental-consequence validator has been established. The provider can imply operational facts inside personal speech or qualified rumor; what semantic checking can be both enforceable and low-cost? What subset of paraphrase has verifiable fact equivalence without another unconstrained generation step?

The minimum authoritative context remains unresolved. Explicit active topic and transaction roles were not tested; fixed posture across sequence topic changes confounds provider capability. How should the host reclassify knowledge and task without losing natural follow-up intent or adding another competing interpreter?

Unknown naming cause, name literal meaning and unestablished geography need separate treatment. A road called north does not prove its compass direction. Belief versus objective claim needs enforcement even when wording feels plausible.

Full final-gate/adoption outcomes for compact outputs were not qualified. Direct helpers and preseal fixtures identify gaps but are not exact production-equivalent decisions for every experiment. Body-free hidden tests cannot prove protection when sensitive bodies are present; the preferred design excludes those bodies entirely.

Commitments preserve strings, not semantically validated stable claims. How should reasons, anecdotes and changing moods be retained without automatic revisions, cross-topic matches or unsafe promotion? What happens after eight-exchange eviction or 180-character truncation? Only a small recorder save/load sample was executed here.

The exact seeded preference trace advances time and can replace a known preference with ignorance despite reuse authority. That is not a new critical canonical mutation, but it requires explicit product/authority review before any compact lane bypasses or changes existing question advancement.

Fresh full-size baseline export remained blocked pending optional user approval; only local content counts and historical provider usage are available. Current full regression status remains unmeasured beyond the 71 focused passes; historical 19 failures remain background debt. No hidden performance regression claim is made.

Provider safety failures repeat in this sample; no implementation work began. The next action is external review of D and the bounded enforcement/context questions, not automatic prompt tuning, R3 or PR-EH.
''')

report(20,'Final Recommendation','''
**D — FURTHER INVESTIGATION REQUIRED.**

The central question has a split answer: compact context can support natural isolated NPC wording with the production-configured provider, but the current architecture has not demonstrated reliable enforcement or preservation of that wording across authorization, validation, continuity and final emission. Existing state ownership can remain intact while unsafe speech still affects player decisions. The experiments therefore do not justify production implementation of B, and they do not establish a need for C.

The smallest plausible future implementation is an optional, tightly scoped paraphrase/elaboration mode inside the current social pipeline, contingent on semantic validation, task-specific context and final-projection qualification. Those are unresolved gates, not approved work.

A–G provider experiments are complete at isolated-fixture scope (130 matrix calls, plus one access call). The unverified fresh full-prompt baseline and lack of end-to-end qualification are explicitly documented. This is not “UNVERIFIED — provider experiments incomplete” for the A–G matrix; it is D because the completed experiments expose safety and integration gaps. No production code or active save was changed. Stop at PR-EG-R2. Await external review.
''')

# Source snapshots make line references reviewable without depending on the working checkout.
sources=['api.py','api_turn_support.py','conversational_orchestration.py','conversational_continuity.py',
 'ordinary_semantic_ownership.py','social.py','dialogue_authority.py','dialogue_social_plan.py','interaction_context.py',
 'gm.py','gm_retry.py','prompt_context.py','immutable_valid_response.py','proposition_authority.py',
 'response_policy_enforcement.py','final_emission_gate.py','final_emission_strict_social_stack.py',
 'social_exchange_emission.py','social_exchange_policy.py','social_exchange_fallback_catalog.py',
 'gm_resolution_decision.py','narration_state_consistency.py','storage.py','world.py','provider_budget.py',
 'model_routing.py','config.py','live_chat_interpretation.py','bounded_improvisation.py']
for name in sources:
 target=HERE/'sources'/'game'/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT/'game'/name,target)
prior=[]
for cycle,names in {
 'pr_ef_r3':['01_EXECUTIVE_SUMMARY.md','03_SEMANTIC_AUTHORITY_INVENTORY.md','08_PROVIDER_CALL_GRAPH.md','09_TOKEN_COST_ATTRIBUTION.md','10_RESTRICTIVE_DIALOGUE_ANALYSIS.md'],
 'pr_ef_r4':['03_AUTHORIZATION_CONTRACT_DESIGN.md','09_FINAL_RESPONSE_CONSISTENCY.md','10_PROVIDER_ELIGIBILITY_AND_RETRY.md'],
 'pr_eg':['01_EXECUTIVE_SUMMARY.md'],
 'pr_eg_r1':['01_EXECUTIVE_SUMMARY.md','02_BASELINE_AND_ENVIRONMENT.md','10_COMMITMENT_RETENTION.md','11_PROVIDER_EFFICIENCY.md','15_STATE_INTEGRITY_AUDIT.md','16_REGRESSION_COMPARISON.md','17_REMAINING_ISSUES.md','live_qualification.json','live.usage.jsonl','regression_junit.xml']}.items():
 for name in names:
  src=ROOT/'artifacts'/cycle/name
  # This historical report contains prompt-cost numbers, not credential tokens.
  # Use an accurate cost label so the handoff's filename-only secret filter does not omit it.
  target=HERE/'predecessors'/cycle/name.replace('TOKEN_COST','PROMPT_COST');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target);prior.append(target.relative_to(HERE).as_posix())

inventory=[]
for p in HERE.rglob('*'):
 if not p.is_file() or any(part in {'local_dependencies','tokenizer_cache','disposable_state','pytest_tmp','pytest_local','__pycache__'} for part in p.relative_to(HERE).parts): continue
 if p.name in {'artifact_inventory.json','handoff_config.json','21_SOURCE_AND_EXPERIMENT_INVENTORY.md'}: continue
 inventory.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
write('artifact_inventory.json',json.dumps(inventory,indent=2))
report(21,'Source and Experiment Inventory',f'''
`artifact_inventory.json` lists retained artifacts and SHA-256 hashes at report generation; `source_integrity.json` lists before/after hashes of 316 protected game/source and active data files, with zero changes. Review packaging additionally creates its own manifest. This report and the inventory itself are not recursively self-hashed; the handoff manifest covers the packaged versions.

Source snapshots under `sources/game/` preserve {len(sources)} relevant production files with the exact reviewed line references. They include routing/authorization, resolver/knowledge, authority, continuity, prompt builder, provider/retry, hard validation/preseal, final emission, world updates and storage. They are copies, not modified production modules. Selected history under `predecessors/` contains {len(prior)} reports/transcripts/usage/junit files.

Experimental runners: investigate.py (baseline/capture and provider matrix), live_single.py (single synthetic access proof), analyze.py (local tokenizer/validator/persistence), trace_preference.py (exact seeded production trace), build_reports.py (retrospective review), package_review.py (established workflow). measure.py is an unexecuted optional full-prompt egress measurement script blocked by automatic review; it must not be mistaken for collected evidence.

Prompts: system_prompt.txt, frozen_cases.json, prompts/*.json. Every experiment row contains exact context, requested/returned model, configuration, raw output, parsed narration, measured input/output tokens, latency, validation and SHA-256 of serialized messages. The initial failed connection is a retained row. The separate access probe is single_provider_access.json. No unfavorable generation was removed.

Measurements: local_prompt_attribution.json; summary_measurements.json; provider_validator_results.json (all 130, direct with decision plus preseal); validator_control_matrix.json (18 labeled controls); persistence_probe.json; investigator_review.json and failure_inventory.json (post-hoc ratings/causes); exact_preference_trace.json; production_captures_offline.json and production_baseline_offline.json (scripted local capture, not fresh provider); focused_local_junit.xml (71 passing); focused_junit.xml (initial sandbox failures).

Reproducibility: use the repository Python environment plus tiktoken 0.14.0 for offline measurements. The tokenizer and public vocabulary cache were installed only under the experiment directory; neither dependencies nor caches are packaged as project requirements. Provider phases require explicit network permission and the local configured credential. Never package .env. Raw disposable storage/test temp trees and unrelated active saves are excluded. All source hashes and model configuration remain in the bundle.

Measurement status: fresh A–G matrix complete; full-prompt fresh baseline not run; full regression not rerun; complete production compact-generation qualification not performed. Run commands and definitions are retained in the scripts. External review is the next step.
''')
print(json.dumps({'reports':21,'matrix_trials':len(trials),'annotated_issues':len(flags),'source_snapshots':len(sources)}))
