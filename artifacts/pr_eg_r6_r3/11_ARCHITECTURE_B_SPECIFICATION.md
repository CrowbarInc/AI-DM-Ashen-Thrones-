# 11 — Architecture B Specification

B asks for a move (`fresh_question`, `revise_previous`, `ask_about_previous`, `unresolved`), an anchor, only the changed roles, and a gap name. It does not emit referent ids or operation opcodes. The host copies unmentioned roles and derives the opcode. The free-text `meaning` field is ignored by the compiler. This is not A's schema with renamed fields: preservation is by host copy, and the model never names `replace_role_value` or `source_attribution`.

Referent binding rose to 57/94 from A's 28/94. Role preservation fell to 53/132 from A's 71/132. False clarifications rose to 12/132. The distinction is real, and on this evidence it does not win.
