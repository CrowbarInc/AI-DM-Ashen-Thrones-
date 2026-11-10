# Conversational root cause

After "Hello, Gate Guard.", the integrated dialogue path set `npc_focus` to `gate_guard` and spoke the host hello. "Who are you?" does not contain the name. The follow-up resolver only continued the focus for a short list of pronouns and greetings, and it looked for a dynamic NPC. The authored Gate Guard is not a dynamic NPC, so the turn asked which person was meant.

When live interpretation was enabled, the local follow-up decision also returned immediately, so an obvious continuation waited on a provider classification that did not keep the interlocutor.

A second live failure, found in this cycle's HTTP run, is separate: `authored_action_language.propose` treated a question that mentions a patrol anchor as an unavailable authored choice before the conversation owner ran. "What do you know about the missing patrol?" and "What about the patrol again?" returned "Nothing was attempted. That is not available here yet."
