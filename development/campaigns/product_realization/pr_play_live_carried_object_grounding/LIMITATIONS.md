# Limitations

- Live-model behavior is unmeasured. Listing `spellbook` and instructing the model to use a listed id does not establish that a future completion will select it. A1's null target and A2/A3's which-spellbook questions were produced when the id was absent. Replaying those captured records shows host recovery. It does not show a new model completion.

- Spellbook pages are not an authoritative field. Recorded-content questions say the sheet does not record them. Prepared spells are published only for a prepared or ready question, with that qualification. The four names are not described as written in the book.

- Positive-quantity inventory membership is treated as carried when the row has no hidden, accessible, or stored flag. There is no new accessibility subsystem. Objects that are stored without `stored: true` would be exposed. The fixture does not contain such a row.

- The attacks array is not inventory. The default Light Crossbow is not catalogued.

- Narration-only objects are not catalogued and are not bound.

- `volume`, `book`, and `tome` bind the book class only after a specific `reference_compatible` miss. A uniquely carried non-book is not selected for those words. A uniquely carried book-class object is selected for `volume`. That is a class rule, not a first-candidate rule.

- The deterministic owner does not take `examine` or `inspect`. Those sentences stay with the older inspection owner, which already binds `I examine the book.` A stored model record of an examine can be grounded on the model path.

- An unresolved examine on the model path returns no decision from this owner, so the existing referent decline remains. A model target id that is absent from the catalog is still rejected as fabricated before that deferral. The footprints fixture does not take that branch; its test passes as `referent_not_in_scene`.

- A4 and B1 remain at `uncertain_actionable_coverage`. This milestone does not bypass that gate.

- Generic book-class matching and deictic follow-up depend on the previous decision having stored `subject_id` under `inventory_information`, `inventory_inspection`, or `spell_information` for the same scene and character. A prior answer from another owner does not supply that authorization.

- Worktree changes from earlier milestones were left in place. This milestone's delta is the files named in `SUMMARY.md`.
