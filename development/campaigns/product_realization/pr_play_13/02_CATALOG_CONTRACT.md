# 02 — Catalog Contract

The catalog is built by `build_opening_public_catalog` from the opening prompt payload the engine already assembled. The model does not create, edit, or reclassify entries.

## Eligibility

A realization claim is public only when all of these hold:

- It has text, and that text is not in the hidden, discoverable-but-unpublished, or restricted sets.
- Its disclosure field is empty or one of `public`, `player`, `visible`, `player_visible`, `revealed`. Any other value, including an unknown label, is excluded.
- Its `source_ref` does not contain a hidden, secret, backstage, private, motivation, restricted, undiscovered, or journal marker.
- It comes from `scene.visible_facts` or `scene.opening_seed_facts`, or its text is in the positive visible-fact set.

Duplicate texts are kept once. Duplicate catalog identifiers fail the catalog closed. An empty required set fails closed before any provider call.

## Required and order

When curated opening facts match public entries, those matches are required and order-constrained in catalog sequence. Other public entries are optional. If no curated fact matches, public `MUST_STATE` entries become the required set. This separates the existing blanket `MUST_STATE` role from opening orientation without a second fact store.

## Variants

Every entry has variant `authored`, the exact public sentence. `APPROVED_PRESENTATION_VARIANTS` may add reviewed alternatives for that exact sentence. The current table has one `concise` wording for the taxes, curfew, and missing-patrol notice. It names the same referents and adds no outcome.

To add a variant later, add a reviewed row keyed by the exact authored sentence. No authority-model change is required. The model can select the new variant id only after the row exists. The variant must keep referent, polarity, modality, and attribution, and it must not add a consequential fact.

## Identifiers

Existing `claim_id` values are the catalog ids. A public fact without one receives `opening_fact_` plus a stable short hash of its source and text. Hidden claim ids are not listed. Selecting one fails as an unknown catalog id.
