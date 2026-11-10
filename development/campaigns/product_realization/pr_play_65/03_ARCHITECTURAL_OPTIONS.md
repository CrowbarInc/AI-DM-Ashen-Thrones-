# ARCHITECTURAL OPTIONS

| Dimension | A: free-form | B: engine plus AI | C: segments |
|---|---|---|---|
| complexity | Lowest immediate change; recurring grammar repairs | Small hook plus publication provenance | New provider schema and segment orchestration |
| reliability | Heuristic free-form coverage | Engine segment deterministic; publication seam must guarantee delivery | Strong if segment schema and publisher cooperate |
| consequences | Existing gates | All gates plus finite optional surface | Still needs segment and final gates |
| hidden | Existing gates, known gaps | No hidden projection; finite optional surface | Still needs segment and final gates |
| naturalness | High potential | Limited but coherent introductions | Potentially greater control |
| duplication | Low | Prompt responsibility plus whole-segment omission | Explicit slots |
| latency | One provider call | One provider call | One call possible |
| compatibility | Existing | Reuses hook and publication helper | Additional response/schema surface |
| reversibility | High | Default-off flag | Medium |
| regression | Growing validator surface | Two production files | Larger than B |

Selected B before implementation: reuse the integrated owner; avoid another narrator, provider or response schema. Selection was based on bounded ownership and reversibility, not acceptance statistics. The live failure exposes an overlooked publisher precondition.
