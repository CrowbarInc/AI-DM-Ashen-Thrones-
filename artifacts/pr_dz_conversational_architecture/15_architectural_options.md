# Architectural Options

Option A: Targeted Repair

Patch start phrases, add more follow-up heuristics, tune multi-action wording. Low scope and low migration cost, but high recurrence risk. It preserves current brittle behavior and likely grows phrase tables.

Option B: Conversational Orchestration Layer

Add a bounded intent/adjudication stage before execution. It decides answer, clarify, decline, execute, or plan. Existing resolvers, persistence, CTIR, narration plan, and validators remain. Medium scope, medium regression risk, best fit for evidence.

Option C: Partial Turn-Pipeline Replacement

Replace much of `/api/chat` routing/contract flow while preserving resolvers and storage. Better conceptual cleanliness but higher migration risk because many existing tests guard current seams.

Recommendation: Option B. The evidence shows downstream simulation components are useful; the failing part is the conversational orchestration contract that decides whether and how to use them.
