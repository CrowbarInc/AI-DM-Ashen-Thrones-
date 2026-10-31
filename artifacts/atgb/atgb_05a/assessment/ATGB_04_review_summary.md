# ATGB-04 — Independent transcript assessment (provisional)

Reviewer: ChatGPT (GPT-6). This is an AI-assisted independent reading of the captured player-facing transcripts and bounded state evidence, **not an authenticated human review**. The JSON review file intentionally sets `human_review_attestation: false`; the official report tool requires an explicit human attestation before accepting scored results. A human reviewer should inspect and sign off on the judgments before importing them as the official baseline.

## Integrity / authority concerns first

**S03.4**: After the player asks whether the notice and runner accounts match, the reply repeats the runner rumor and three unrelated faction agenda flags appear in the state evidence. Whether this is authorized time-driven progression or an unintended conversational mutation cannot be established from the bounded snapshots. Authority **uncertain**, not an established critical violation.

**S05.4**: The player selects the runner's account; the response says the runner cannot tell them, and the same three faction agenda flags appear. Authority **uncertain** for the same reason. No proven critical authority failure is assigned.

No verified consequential invention, hidden-fact leak, unauthorized travel, or purchase was observed in the supplied bounded evidence. This is not a claim of complete world-state integrity.

## Major conversational failure families

- **Misclassified conversational acts and corrections:** S01.4, S04.2, S06.4, S07.2, S08.2. Ordinary statements or corrections receive mechanical rulings, hidden-information denials, or pending-intention messages.
- **Related but nonresponsive answers:** S02.2–S02.4, S03.4–S03.5, S08.4. The host repeats general scene/notice/rumor text instead of answering the requested detail or admitting the specific fact is unknown.
- **Lost interlocutor or referent:** S03.3, S05.3–S05.4, S09.2, S10.2. The system asks unnecessary or wrong-slot clarification questions despite conversational context.
- **NPC dialogue limitations:** S04.3–S04.4 and S06.2. Appropriate grounded uncertainty is possible, but generic refusals frequently fail to address the actual question.
- **Opening-delivery limitation:** S07 and S09 lacked the authored opening; S07.1/S07.3 are therefore not scored on unsupported opening-dependent expectations. Some other responses remain independently judgeable.

## Provisional dimension counts

| Dimension | Pass | Fail | Uncertain | Pass among determinate |
|---|---:|---:|---:|---:|
| Interpretation | 18 | 16 | 3 | 18/34 (52.9%) |
| Response adequacy | 10 | 25 | 2 | 10/35 (28.6%) |
| Authority | 35 | 0 | 2 | 35/35 (100% of determinate only) |

The authority figure must not be presented as an overall safety rate: the two uncertain turns involve unexplained faction-flag changes, and state evidence is bounded. **No composite score is calculated.**

By evidence class, response adequacy: development-visible 7/25; related variation 2/4; previously exposed held-out 1/6 determinate, 2 uncertain. The held-out class is **not independently unseen**.

Clarification: 1 necessary and appropriate; 5 unnecessary; 1 missing focused clarification. Continuity: 11 preserved, 11 lost, 15 not applicable (qualitative classifications, including scenario setup qualifications). Three successful turns have minor style defects. Twenty-five turns have major response failures. No confirmed critical failure was assigned.

## What this means

The first run shows that direct observation and explicitly addressed NPC questions can work, while conversational corrections, follow-up references, and natural remarks often fail. The main measured weakness is **response adequacy**, not a demonstrated general pattern of fact invention. The system often protects authority by declining to answer, but the refusal is not conversationally appropriate.

## Recommended next step

Have the user or another designated human reviewer verify the turn-by-turn file, especially S01.2, S02.1, S03.4, S05.4, S07, and S09, and explicitly attest only after review. Then import the attested JSON into the existing `report_human_review.py` tool, preserve the official baseline, and reconcile `NEXT_SESSION.md`. Do not rewrite the scenario corpus or start another ATGB infrastructure campaign.
