# 04 — Renderer and Publication Integrity

`render_opening` resolves each validated selection to engine text, joins the sentences, and records for each component:

- catalog id
- variant id
- source claim reference
- rendered text
- disclosure `public`
- character position in the final string

The GM object created from that render has the rendered string as `player_facing_text`. Scene, world, activation, draft, suggestion, and improvisation fields are null. Engine-built declarations repeat the rendered sentences and the source claim's provenance, modality, and role. The model does not supply those fields.

## Bypass

An otherwise shaped plan that also carries "The guards award you 100 gold." is rejected before publication. The same holds for injected movement, combat, skill-check success, quest completion, hostility, items, time, damage, and hidden identity. A later stage that appends text to an accepted render is overwritten by `enforce_rendered_publication`, which puts the trace text back and clears model update fields. Structured failures and safe nonresolution are not restored into a success.

The deterministic five-turn run `20261101T144743Z-14b8c942e340` delivered a 563-character opening from six public catalog components. The saved result does not contain the gold sentence.

## Player-visible fields

The opening failure body is the existing fixed error and reason code. The success body uses the trace text. Diagnostic metadata records the trace, which is authorized catalog text, not the raw provider body.
