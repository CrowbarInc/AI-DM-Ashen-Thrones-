# Conversational routing

Root cause: authored_action_language.propose treated a question that shared a patrol anchor as an unavailable authored choice before the dialogue owner ran.

Repair: a question to the focused NPC returns no authored proposal unless it commits an authored choice (survey, record, report). Memory, notice-board, and where-am-I questions also return no proposal. Asking someone is dialogue unless it is that commit.

Live result: zero authored interceptions and zero target clarifications across the HTTP script, including both patrol questions.
