# Review Handoff Output Inventory

This inventory was completed before implementing review-handoff automation.

## Existing conventions

- Permanent campaign, architecture, audit, closeout, and standards documents live under `docs/` and
  are canonical repository evidence.
- Runtime validation outputs live below campaign-specific `artifacts/` roots. Their transcripts,
  manifests, state snapshots, evaluator outputs, and human-review records remain canonical evidence.
- The Validation Evidence Standard generates two-file review surfaces under
  `artifacts/validation_evidence/<campaign>/`: `evidence_summary.md` and
  `evidence_manifest.json`. The manifest records canonical source paths and embeds exact important
  interactions.
- Reactive/adversarial human review is canonical at
  `artifacts/reactive_adversarial_players/human_review.json`.
- Test results are ordinarily console output or summarized in permanent campaign documentation. No
  general durable pytest-output convention exists.
- Campaign IDs are commonly timestamps, stable descriptive slugs, or both. Evidence manifests expose
  a `campaign.campaign_id` field.
- Generated reports generally identify source paths in prose or JSON; there is no shared portable
  review manifest.

## Packaging availability

No existing `CURRENT_REVIEW.md`, review ZIP, review manifest, or general campaign export command was
found. Existing ZIP/archive code is not a review-handoff mechanism suitable for reuse.

## Canonical versus generated

Canonical evidence includes implementation/standard documents, evidence manifests and summaries,
source transcripts, human-review records, calibration cases, and campaign-specific reports at their
normal repository paths.

The handoff summary, handoff manifest, and ZIP are generated orientation/export artifacts. They may
quote or package canonical evidence but never replace it. Every packaged canonical file must retain its
repository-relative source path and role.

## External-review priorities

For the Validation Evidence Standard demonstration, an external reviewer needs:

- the concise handoff summary
- the handoff manifest
- the Validation Evidence Standard and producer inventory
- reactive/adversarial evidence summary and manifest
- retrospective playability evidence summary and manifest
- the preserved reactive human-review record
- the reactive campaign report needed to understand architecture and findings
- focused source files and tests necessary to review the reporting implementation

The evidence manifests already embed exact selected exchanges and point to canonical transcripts, so
packaging every raw run, state snapshot, unrelated historical campaign, or full artifact tree would be
redundant.

## Normal exclusions

- repository copies, `.git`, virtual environments, dependency/build/test caches
- previous/current handoff ZIPs and handoff history while constructing a new bundle
- unrelated artifact trees, historical campaigns, generated datasets, and state snapshots not needed
  for the review question
- `.env` files, credentials, tokens, API keys, private keys, authentication caches, and user data
- oversized files when a summary and canonical reference are sufficient

The generator will use explicit inputs plus safe evidence-packet expansion. It will not crawl the
repository and guess relevance.
