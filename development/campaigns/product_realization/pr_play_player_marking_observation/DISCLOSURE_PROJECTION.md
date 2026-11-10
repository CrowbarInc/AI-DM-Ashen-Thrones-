# Disclosure Projection

`project_observation` calls `observe_object` and then `narration_from_projection`. The sentence is built from the returned property only.

| Projection | Player sentence |
|---|---|
| `known_present` | `On the {surface}, the visible writing reads: {content}` |
| `unknown` | `You look at the {surface}. No writing is visible there.` |
| `known_absent` | `On the {surface}, no marking is present.` |
| service unresolved | `The writing could not be read.` |

Ordinary grants are not complete, so an empty visible subset is `unknown`. That sentence does not say that concealed markings are absent. `known_absent` is available only if a future trusted caller supplies a complete grant. This player path does not.

The narrator does not receive modification ids, request ids, receipts, visibility records, or undisclosed content. Undisclosed strings are collected only inside the publication check that rejects a sealed sentence containing them. They are not stored on the resolution summary.
