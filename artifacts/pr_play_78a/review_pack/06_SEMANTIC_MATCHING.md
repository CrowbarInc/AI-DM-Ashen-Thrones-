# Semantic matching

Matching is lexical and contextual, not exact equality. Travel words such as return, go, and walk are stopwords so they do not by themselves select a branch. Report language ("tell the watch", "give my report", "report the uncertain trail") scores `patrol_report`. Survey, document, and note language scores `patrol_survey`. If the record follow-up is unavailable and the survey choice is available, documentation language selects the survey. After `patrol_survey` is set, "I record the survey" selects `patrol_record_survey`.

Questions, negation, hypotheticals, discussion, and quotation do not execute. Two close available scores ask which label is meant. A sentence with no authored anchor returns no proposal and ordinary adjudication continues. "I walk toward the town gate." does not take the report branch. "Survey the distant galaxy." and "I want to report a programming bug." do not execute.
