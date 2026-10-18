# PR-CP authored answer preservation

## Why PR-CI did not save the patrol sentence

PR-CI preseal (`_project_authorized_social_answer_before_seal`) replaces model text only when the selected topic is not already communicated. The PR-CO provider included "A patrol went missing near the old milestone." Preseal therefore left the reply unchanged, including "That's all I can confirm for now."

The topic was selected and stored as revealed. It was not on the decision's realization claims, so the audit could not see it as authorized. The patrol pattern then marked the authored sentence itself. Hard validation rejected the response. The safe fallback replaced the entire answer. Bounded preservation does not run when the narration-only envelope is present.

The resolver and the answer recipe were not the first failure. The provider did include the authored fact. Extraction recognized the sentence. The validator rejected it as undeclared, and finalization discarded it with the certainty clause.

## Required behavior now

`decision_with_selected_social_topic` puts the selected sentence on the audit copy before the decision audit.

If the reply is only that sentence, or a drop-only restatement, pattern licensing lets it seal.

If the reply also contains an unsupported clause, the whole reply stays hard-invalid. `_terminal_after_fidelity` then emits `format_authored_knowledge_realization_line` for the selected topic when that line alone is hard-valid. The player receives:

`Guard Captain mutters, "Word is, A patrol went missing near the old milestone."`

The certainty clause, the crossroads, and "has not returned" are not in that line. The projection runs before the generic visible-fact fallback so a patrol question is not answered with the notice-board sentence merely because both mention a missing patrol.

`safe_nonresolution` remains the fallback when no selected topic and no authorized observation can be projected.
