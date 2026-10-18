# PR-DO Implementation Report

MODE: BOUNDED CONTRACT REFINEMENT AND DETERMINISTIC REPLAY

LIVE PROVIDER CALLS: 0

PRODUCTION INTEGRATION: none

HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

The worktree was already dirty. It was left dirty. Production saves were not written. Their hashes match the stored PR-DN fingerprints. See `phase0_snapshot.json`.

Stored inputs:

- `artifacts/pr_dn_interpretation_robustness/raw_results.json` (sha256 `5b52b366...`, read only)
- `artifacts/pr_dl_interpretation_comparison/raw_results.json` (sha256 `da8bbabe...`, not modified and not sent to a provider)

PR-DL outputs use the same old interpretation schema as PR-DN. They were preserved as a stored source. They were not translated into the new contract, because that translation would repeat the PR-DN finding: the old schema cannot represent the split.

## What changed

New experiment package `experiments/pr_do/`:

- `schema.py` defines the model-facing contract. It has no execution-grant field.
- `adapter.py` validates structure and stores claims and wishes as non-authoritative records.
- `eligibility.py` produces the engine-owned disposition from enums, ids, and statuses only.
- `fixtures.py` holds assumption-bearing contract cases and adversarial cases.
- `translate.py` copies stored PR-DN fields without inventing the missing split.
- `routing.py` records how an explicit `OOC:` prefix relates to the existing router.
- `replay.py` evaluates fixtures without calling the engine.

`tests/test_pr_do_authority_separation.py` covers the boundary. The PR-DM regex guard was not extended.

## Phase 1 overlap

The PR-DJ / PR-DL schema puts several meanings in the same places:

| Field | What it was asked to do | Where the meanings collide |
| --- | --- | --- |
| `interpreted_intent` | Describe the attempt | DN05, DN07, and DN09 also put premises and wished results here |
| `primary_operation` | Name a broad intent | The adapter copied it into a proposal whose validation set `authoritative_operation` and `discourse_commit_allowed` |
| `multiple_action_components` | List attempts | DN07 used the list for HP assignment and a critical-hit claim |
| `unsupported_action` | Name a refusal | A non-empty value made the PR-DM guard skip its proposing checks, so DN07 passed |
| `non_authoritative_explanation` | Explain the reading | DN01 used it to say the player "is performing" the actions |
| `status=INTERPRETED` | Mark a usable reading | DN05, DN07, DN09, and DN10 were then consumable |
| `clarification_question` | Ask one question | DN08 asked how to obtain an item the player was not allowed to grant |
| entity ids | Point at visible referents | The same ids became targets of unauthorized acts |

There is no communication-mode field, no premise field, no wished-outcome field, and no engine-owned eligibility field. Authority therefore depended on reading the prose. The PR-DM guard's phrase list missed indirect NPC permission, HP phrased as "HP", inspiration retcon, and hidden-map reveal.

## What this package does not do

It does not mutate HP, inventory, canon, NPC commitments, hidden information, time, or dice. It does not call a resolver. It does not roll back history. It does not change narration prompts. It does not redesign the router. It does not add forbidden-phrase coverage to PR-DM.
