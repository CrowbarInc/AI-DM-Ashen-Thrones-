PR-DW IC/OOC results

| Input | Classified mode | Destination | Execution | State changed | Time advanced |
| --- | --- | --- | --- | --- | --- |
| `OOC: I am checking whether the interface is alive; do not change game state.` | Not safely OOC; deterministic contract treated as inspect-like | Ordinary chat pipeline | Yes, nonresolution/inspection-style path | Yes, `turn_counter` 0 to 1 | Yes, `time_pressure` 0 to 1 |
| `OOC: I was only asking about the lantern's appearance.` | OOC | OOC correction shortcut | No resolver | No gameplay mutation from this turn | No additional turn advancement |

Finding:
- Explicit OOC prefix alone is insufficient.
- OOC safety currently depends on narrow text patterns.

