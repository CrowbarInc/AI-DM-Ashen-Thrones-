"""Offline PR-PLAY-25 report/manifest/archive builder. No provider imports."""
from pathlib import Path
import difflib
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/pr_play_25'


def cases(name, exclude_new=False):
    rows = {}
    for t in ET.parse(OUT / (name + '.xml')).iter('testcase'):
        key = t.attrib['classname'] + '::' + t.attrib['name']
        if exclude_new and 'test_pr_play_25_public_fact_dialogue' in key:
            continue
        failure = t.find('failure')
        error = t.find('error')
        node = failure if failure is not None else error
        message = node.attrib.get('message', '') if node is not None else ''
        # Remove only runtime addresses, durations and temporary test paths.
        normalized = re.sub(r'0x[0-9A-Fa-f]+', '<address>', message)
        rows[key] = {'result': 'failed' if node is not None else 'passed',
                     'message': message, 'normalized_message': normalized}
    return rows


groups = [('existing', 'existing_baseline', True), ('authority', 'authority_baseline', False),
          ('historical_extension', 'historical_baseline', False)]
comparison = {}
all_current = {}
for current, before, exclude in groups:
    a, b = cases(current, exclude), cases(before, exclude)
    assert set(a) == set(b), (current, set(a) ^ set(b))
    failures = {k for k, v in a.items() if v['result'] == 'failed'}
    old_failures = {k for k, v in b.items() if v['result'] == 'failed'}
    assert not failures - old_failures, (current, failures - old_failures)
    comparison[current] = dict(tests=len(a), passed=len(a)-len(failures), failed=len(failures),
        newly_failing=sorted(failures-old_failures), resolved=sorted(old_failures-failures),
        failures={k: {'classification': 'preexisting failure', 'current': a[k], 'before': b[k]} for k in sorted(failures)})
    all_current.update(a)
old = ET.parse(ROOT/'artifacts/pr_play_23/existing.xml')
known = {t.attrib['classname']+'::'+t.attrib['name'] for t in old.iter('testcase') if t.find('failure') is not None}
known_remaining = sorted(k for k in known if k in all_current and all_current[k]['result']=='failed')
comparison['known_historical_remaining'] = known_remaining
comparison['known_historical_remaining_count'] = len(known_remaining)
assert len(known_remaining) == 25
comparison['expanded_preexisting_failures'] = sum(v['result']=='failed' for v in all_current.values())
comparison['live_provider_requests'] = 0
(OUT/'test_comparison.json').write_text(json.dumps(comparison, indent=2), encoding='utf-8')


def write(name, text):
    (OUT/('PR_PLAY_25_' + name + '.md')).write_text(text.strip()+'\n', encoding='utf-8')


write('FAILURE_RECONSTRUCTION', '''# PR-PLAY-25 failure reconstruction

The pre-repair failure is reproduced offline against the exact captured PR-PLAY-24 scene and NPC. `original_reproduction.json` records both original and repaired authority. `dialogue_authority.before.py` is the exact file copied before this pass, not a reconstruction of its logic.

1. Player: “I approach the tavern runner and ask what they're offering.”
2. Selected target: native NPC `tavern_runner`; authoritative name `Tavern Runner`, friendly informant in `frontier_gate`, explicitly addressable in that scene's roster. No NPC promotion or invented identity.
3. Public fact: `scene.visible_facts[2]`: “A tavern runner trades hot stew and rumors near the rain barrel.”
4. Authored NPC topic: `patrol_rumor`, concerning the missing patrol/old milestone. Full exact record is retained in the reproduction fixture. There is no offerings topic.
5. `game/social.py:_next_topic_to_reveal` returned None; candidate sources empty. Social target resolution and execution succeeded. The scene sentence was present at social resolver input.
6. `game/dialogue_authority.py:build_dialogue_authority` received the scene but produced unknown posture, an empty proposition and no selected source. This is the first failed authorization boundary: the topic-only selection had no public-fact fallback. The general request was also excluded from `visible_supporting_sentence`.
7. Expression input: NPC identity and exact player question, operation `uncertainty`, `AUTHORIZED FACTS: (none)`. See `original_expression_request.json`, copied from the existing capture; no new request was sent.
8. Captured expression: “I’m not sure what the tavern runner is offering right now.”
9. Validation: rejected with `unsupported_addition`; `right` and `now` were outside the uncertainty closure vocabulary. No supported answer was discarded. This is secondary to the absent proposition.
10. Host fallback: `Tavern Runner says, "I couldn't tell you."`; accepted response provenance `authorized_host_speech`, expression adoption `HOST_FALLBACK`, hard-valid and interaction-complete.
11. HTTP 200 published that exact fallback. Publication itself did not lose a useful answer.

The original published opening is reproduced verbatim in `original_transcript.md`; it advertises hot stew and paid rumor. That opening is corroboration, not the new authority source. The fix reads only the authoritative visible sentence, never generated opening prose or provider evidence.

Offline reproduction asserts the original no-topic result and exact host fallback using the pre-repair module, then applies the repaired builder to the same unmodified captured state and obtains `I offer hot stew and rumors.` The final integration initializes through the existing opening renderer, replays the compound interpretation through real approach normalization and ASK, adopts a supported mock expression, seals the response and publishes Player HTTP output.

The shared opening test fixture normally substitutes opening seed text for visible facts. The new test restores the captured visible-fact list in isolated temporary storage before opening initialization. It does not change production data, opening generation, or post-turn state to obtain a pass.
''')

write('KNOWLEDGE_PIPELINE', '''# PR-PLAY-25 knowledge pipeline

| Question | Repository finding |
| --- | --- |
| What makes a fact authoritative? | Host-loaded canonical/effective scene state, rather than a player premise or provider assertion. |
| What makes it public? | Membership in the current scene's `visible_facts`; hidden facts and discoverable clues are separate fields and are not read by the new selector. |
| Representation? | A list of free-text strings inside the `scene` envelope. There is no entity ID or provenance attached to each visible sentence. |
| Can facts identify a speaker? | Some have a direct grammatical subject that exactly matches a uniquely registered scene NPC name. Many do not; those remain ineligible. |
| Existing provenance? | NPC topics have IDs and disclosure metadata. Dialogue provenance records identify source, speaker, operation, epistemic status and proposition. Opening rendering has source references, but they do not attach NPC ownership to arbitrary visible strings. |
| Own versus another NPC's activity? | The added narrow grammar requires the sentence's entire subject to match the unique addressable record whose ID matches the resolved NPC. No word-overlap or substring attribution. |
| Question matching? | Existing authored-topic relevance and sufficiency run unchanged. The fallback recognizes a small full-question offerings grammar and the original normalized compound phrasing. No second model or exact item keyword is required. |
| Prior dialogue authority? | Authored topics, verified delivered history, bounded personal expression and host operations. Public scene text was not an answer source for the general offerings request. |
| Restricted exclusion? | `authorize_npc_disclosure` rechecks authored policy/knowledge. New public selection cannot override a selected topic, a refusal, ambiguity, a locked semantic plan, any authored offerings topic, or a restricted topic overlapping advertised items. |
| Expression validation? | Deterministic content anchors, closed vocabulary, numbers, epistemic posture, names, length and sentence checks. Scoped offering verb equivalence is added only for the new source relation; negation is explicitly rejected. |
| Multiple sources? | This repair selects one public source only. Multiple matching visible sentences fail closed; authored sources retain precedence. No concatenation or contradictory merge. |
| No match? | Existing uncertainty/refusal and host fallback remain. |
| Public facts in provider input? | Previously absent in this captured expression request. Now only the selected first-person offering proposition is passed; not the full scene or hidden state. |
| Provider schema change? | None. Existing `authorized_propositions`, `permitted_meaning`, source identity and faithful-paraphrase operation suffice. |
| Existing structures reused? | Existing dialogue authority, provenance, expression contracts, validator, immutable host sealing, accepted response and Player projection. |

Source anchors: `game/social.py:1611 _next_topic_to_reveal`, `:1564 authored_topic_relevant_to_question`, `:1587 authored_answer_sufficient_for_question`, `:3895 resolve_social_action`; `game/public_fact_dialogue.py:select_public_offering`; `game/dialogue_authority.py:509 build_dialogue_authority`, `attach_dialogue_authority`, `select_host_speech`; `game/expressive_dialogue.py:build_expression_contract`, `build_expression_prompt`, `validate_expression`, `_attempt`; `game/immutable_valid_response.py:1448` host-speech selection and expression adoption; `game/api.py:5026` and `:5044` public projection.

Authority hierarchy remains host-owned: established world/NPC sources with disclosure rules; verified history under existing restrictions; bounded expression or honest host uncertainty. Locked unified semantic plans retain their own authority and are not overridden. The new visible-source fallback supplies speech only; it grants no discovery, transaction or durable world mutation. The legacy no-topic resolver hint may still describe uncertainty; the reconciled social reply fields and selected dialogue authority own final delivery.
''')

write('AUTHORITY_CONTRACT', '''# PR-PLAY-25 authority contract

Category A: established public information may support narrowly scoped speech. Category B: authored restricted information retains its existing disclosure policy. Category C: a new price, reward, quantity, obligation or world change requires independent game-state authority and cannot be minted by dialogue.

Eligibility requires all of the following:

* A real resolved, same-scene NPC and an exact matching social target ID, with no selected authored topic, ambiguity, refusal or locked semantic plan superseding it.
* A unique explicit `addressables` row: matching NPC ID and exact NPC name, `kind=npc`, correct `scene_id`, `addressable=true`, matching NPC location. Duplicate subject names/IDs fail closed.
* A string from authoritative current `visible_facts`, full-matching the bounded form `[A/An/The] <exact registered subject> offers/sells/serves/trades <bounded list> [near <location>].` The proposition projects just the listed offerings into `I offer <items>.` It does not authorize the location or facts about the items.
* A complete recognized own-offerings question: offering/selling/serving/available/services variants, including the original approach-and-ask phrasing. Third-party questions, prices, secrets, rewards and compound qualified questions do not match.
* One eligible source only. Numbers, prices, restricted/consequential vocabulary, negation, conditional clauses and unsupported syntax fail closed.

Provenance records the actual scene ID and visible index, exact source text, resolved NPC ID, projected proposition and `own_offerings` relation. It is deterministic derived attribution, not authored entity metadata. The legacy data has no stronger per-fact entity reference; no migration or fabricated authored provenance is introduced. Display-name overlap alone is insufficient: exact grammatical subject, unique registry binding, same scene, positive bounded assertion and relevant question are all required.

Authored topics are never replaced. A selected topic wins through the existing pipeline. Any authored offerings topic blocks this fallback even if restricted or not selected. A restricted topic sharing an advertised item also blocks fallback. Multiple public candidates yield `ambiguous_facts`; ambiguous subjects yield `ambiguous_subject`. Conflicting authored offerings produce `authored_offering_precedence`, never a merge. No public source grants the guard the merchant's commercial knowledge.

The expression provider receives the existing identity/question/proposition/constraints contract. It may reword offering verbs (offer/sell/serve/I've got) while preserving all item descriptions. Content checks still reject new nouns, numbers, prices, rewards, commitments, name substitutions, strengthened epistemic claims and negation. Unsupported output falls back to the authorized host offering sentence and records rejection reasons.

Limits are intentional: arbitrary prose, aliases, pronoun subjects, unregistered actors, globally observable facts, stock/pricing mechanisms and a bare nearby-banner question are not newly authorized. A source phrased only as “shouts offers of...” remains outside this grammar. The captured direct offering sentence is supported. Existing facts need not be rewritten, and no NPC-specific name/item exception exists. This is not unrestricted natural-language understanding or general public knowledge.
''')

write('REPAIR_REPORT', '''# PR-PLAY-25 repair report

Root cause: the social resolver received the public offering sentence, but topic-only authority selection never promoted it into answer material. Expression was correctly confined to uncertainty; downstream publication worked.

Production files changed:

* `game/public_fact_dialogue.py` (new): bounded question/relation grammar, exact unique registered-subject attribution, explicit visibility/source reference, single-source selection, authored/restricted precedence and diagnostic reasons. No provider import or state writes.
* `game/dialogue_authority.py`: use the selection only after existing topic/disclosure/semantic-plan checks; reuse existing world-source provenance, proposition identity and host sentence. Reconcile social reply fields to source-bound answer with durable mutation disabled. Select the public host source through the existing host-speech lane.
* `game/expressive_dialogue.py`: feed the authority proposition through the existing contract, select faithful paraphrase for this source, identify the offering relation in existing permitted meaning, explain scoped verb equivalences in the prompt, and apply those equivalences before existing closed-content validation. Explicitly reject negated offerings. All other source validation remains unchanged.

Regression file: `tests/test_pr_play_25_public_fact_dialogue.py`. Evidence scripts and reports live under `artifacts/pr_play_25`; before-files enable exact offline comparison. `source_diff.patch` compares only this pass's changes, and source snapshots preserve the reviewable result.

Generalization uses registered NPC identity and the offering relation. Runner, merchant, innkeeper, potter and cook use the same implementation with different names, items and accepted question variants. Neither the runner's name nor hot stew appears in production selection code.

Safeguards: no all-scene context injection, no provider-selected sources, no hidden-fact scan, no disclosed secret payload, no topic/clue mutation, no merging of conflicting facts, no pricing/reward authority. Authoritative character, campaign, combat, conditions, scene and world assertions pass; world change equals only the existing ordinary-turn tick. NPC attitude/trust/fear/suspicion and revealed topics remain unchanged. Session clock, interaction binding, delivered-speech memory, log and last-interaction bookkeeping remain permitted engine behavior.

Supported mock expression “I've got hot stew and rumors.” is adopted and published. “...for three copper” is rejected with `unsupported_number` and `unsupported_addition`; the authorized offering host fallback is published instead. Provider generation disabled also publishes the host offering without an expression request. Hidden and irrelevant questions preserve refusal/uncertainty.

Remaining limits: grammar is deliberately narrow, not a parser of arbitrary prose; item descriptions must remain intact in paraphrases (omitting an adjective is not newly licensed). Ambiguous or multiple public facts produce fallback. Existing locked semantic plans and authored-topic behavior are unchanged. Known broad historical failures remain and are not repaired here. No opening/data/model/provider-contract redesign, live gameplay, live-provider request, commit or push was performed.
''')

table = '\n'.join(f"| {n} | {comparison[n]['passed']} | {comparison[n]['failed']} | 0 |" for n, _, _ in groups)
write('TEST_RESULTS', f'''# PR-PLAY-25 test results

Zero live-provider requests. Pytest's autouse guard blocks OpenAI constructors, interpretation and expression calls unless a deterministic test explicitly replaces the transport. All provider-shaped request counters in new HTTP evidence are mocks, not external requests. No live gameplay was run. Tests enable the live adapter only to exercise parsing with mocked transport.

Final focused result: **38 passed, zero failed/errors** (`focused.xml`, `focused.txt`). Six real opening-to-HTTP cases: supported generated offering, host-only offering, unsupported price question, no relevant authority, rejected price embellishment, and secret inquiry. Each checks publication, state integrity and Player projection; offering expression adoption/rejection is asserted explicitly.

Coverage A–O: original captured runner reproduction; merchant and innkeeper; unrelated registered guard; hidden allegiance question; unsupported price and reward; authored topic preservation; conflicting/restricted source precedence; no facts; accepted natural paraphrase; rejected price/reward/map embellishment and negation; unchanged inventory/currency/campaign/NPC relationships/scene/world authority; public confidentiality; five NPC generalization fixtures. Additional negatives cover duplicate identities/facts, cross-scene/inaccessible NPCs, conditional/quoted/negated prose, multiple questions, provider-evidence-only claims and mismatched resolved IDs.

| Existing group (new tests excluded) | Passed | Failed | Errors |
| --- | ---: | ---: | ---: |
{table}

The broad XML includes the new test file because its name contains dialogue: initial raw `existing.xml` is 945 tests, 857 passed / 88 failed. Of those, 36 were the then-current new focused tests; the existing-only result is 909 tests, 821 passed / 88 failed. The final focused suite has 38 cases. Exact-baseline raw `existing_baseline.xml` contains those final 38 new tests as well: 947 tests / 100 failures. Twelve failures belong to new tests intentionally exercising features absent from the old modules (one checks newly added diagnostic metadata). These are not historical regressions. Compare the identical 909 existing test IDs separately in `test_comparison.json`.

Baseline method: `baseline_plugin.py` loads the exact two pre-pass production modules before collection; production files on disk are untouched. Full existing and authority suites use the same test lists/order. Current and baseline have identical existing failure sets, including the directly relevant expression-semantics and authored-answer failures. None was fixed or reclassified obsolete. The 7 historical physical-action failures also repeat under the exact pre-pass modules. Two lead tests pass in the failing-only baseline but fail in both full suites, indicating suite-order sensitivity; these are explicitly retained as preexisting failures, not new regressions or resolved bugs.

Historical comparison: all **25** previously documented functional failures remain (17 original plus 8 expanded). This larger scope identifies **109** failing existing cases total, all present with pre-repair modules: 25 previously documented and 84 additional baseline failures. Zero newly failing existing tests, zero resolved preexisting failures, zero obsolete assertions claimed. The repository-wide suite is not green. IDs, assertion messages and classifications are retained in `test_comparison.json`; raw logs/XML include blocked live-call attempts, which fail before network access.

Commands: `.venv/Scripts/python.exe -m pytest <files> -q --tb=short --junitxml=<evidence.xml>`; full file lists are `existing_test_files.json` and `authority_test_files.json`. Historical files: physical compound/perception, PR-DU player pipeline, PR-EA orchestration, PR-EC movement. Baselines add `-p artifacts.pr_play_25.baseline_plugin`. Distinct `--basetemp` directories isolate runs. Focused evidence uses `ASHEN_PR_PLAY_25_EVIDENCE=1`. The last focused rerun follows the final scoped prompt/validation changes. `git diff --check` passed for the modified tracked production files.
''')

answers = [
'Yes; exact captured state and pre-pass module reproduce the empty proposition and original host fallback.',
'Between topic-only source selection and dialogue authority; the scene reached social resolution but was never authorized for expression.',
'Current authoritative visible sentence, bounded direct offering relation, unique own-speaker attribution, relevant complete question, and no stronger restriction/conflict.',
'Exact grammatical subject plus unique same-scene addressable record, matching resolved NPC ID/name and location; provenance records the real visible index.',
'Small complete-question offerings grammar; no second model, item keywords, unrestricted similarity or third-party knowledge.',
'Yes; original action publishes “I\'ve got hot stew and rumors.” Host-only mode also lists the offerings.',
'Yes; merchant, innkeeper, potter and cook fixtures use the same code.',
'No new access is granted to unrelated NPCs; a registered guard cannot acquire merchant offerings via this rule.',
'Yes in this repaired path; restricted-topic precedence and secret negative HTTP checks pass. Broader preexisting referent-authority failures remain documented.',
'Yes; questions do not authorize them, and generated price/reward additions are rejected.',
'Yes; selected authored topics retain authority and all preexisting outcomes match the baseline.',
'Yes; authored precedence and conservative fallback prevent contradictory public/authored merging; multiple public candidates fail closed.',
'Yes; expression captures show only the selected offering proposition plus the existing identity/question/constraint contract.',
'Yes; first-person offering paraphrases are accepted while all item descriptions remain required.',
'Yes; real HTTP Player publication and accepted response match the stored delivered text.',
'Yes for consequential authority: core state/scene unchanged, world changes exactly equal the existing ordinary-turn tick; relationship metrics unchanged.',
'Yes; deep public projection equality and synthetic hidden sentinel assertions pass.',
'No newly failing existing test IDs against exact-module baselines in the exercised scope.',
'25 previously documented failures remain; expanded scope contains 109 baseline failures total.',
'Zero. Only deterministic mocked requests and reads of prior captures.',
'Ready for external review of this scoped repair, then a separately authorized controlled NPC experiment; not general gameplay readiness or permission to start PR-PLAY-26.',
]
write('FINAL_VERDICT', '# PR-PLAY-25 final verdict\n\n**PASS — A: SCOPED PUBLIC-FACT AUTHORITY REPAIRED.**\n\n' +
      '\n\n'.join(f'{i}. {a}' for i, a in enumerate(answers, 1)) +
      '\n\nHighest-priority finding: public information needs a scoped speaker-and-question authority grant; merely placing scene context in a resolver or prompt is insufficient.\n\nStop for external review. No commit or push; no subsequent pass has begun.')

# Preserve only task-owned files and relevant original evidence.
sources = ['game/public_fact_dialogue.py', 'game/dialogue_authority.py', 'game/expressive_dialogue.py',
           'tests/test_pr_play_25_public_fact_dialogue.py']
diff = []
for rel in sources:
    dest = OUT/'source_snapshot'/rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT/rel, dest)
    old = OUT/(Path(rel).stem+'.before.py')
    before = old.read_text(encoding='utf-8').splitlines(keepends=True) if old.exists() else []
    after = (ROOT/rel).read_text(encoding='utf-8').splitlines(keepends=True)
    diff.extend(difflib.unified_diff(before, after, fromfile='a/'+rel if before else '/dev/null', tofile='b/'+rel))
(OUT/'source_diff.patch').write_text(''.join(diff), encoding='utf-8')
manifest = {str(p.relative_to(OUT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in {'MANIFEST.json','archive_verification.json','archive_path.txt'}}
(OUT/'MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
# This dated pass runs after the 2026-11-01 DST transition (EST, UTC-5).
# Windows Python here has no IANA tzdata package; do not use host-local time.
stamp = datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
archive = ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for rel in sorted([*manifest, 'MANIFEST.json']):
        z.write(OUT/rel, 'pr_play_25/'+rel)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for rel, digest in manifest.items():
        assert hashlib.sha256(z.read('pr_play_25/'+rel)).hexdigest() == digest
    verification = dict(archive=str(archive.resolve()), exists=archive.exists(), entries=len(z.namelist()),
                        crc_check='passed', sha256_members='passed', live_provider_requests=0,
                        size_bytes=archive.stat().st_size, archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
(OUT/'archive_verification.json').write_text(json.dumps(verification, indent=2), encoding='utf-8')
(OUT/'archive_path.txt').write_text(str(archive.resolve()), encoding='utf-8')
print(json.dumps(verification, indent=2))
