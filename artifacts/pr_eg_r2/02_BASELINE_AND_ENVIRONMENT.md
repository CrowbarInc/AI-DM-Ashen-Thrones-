# 02 — Baseline and Environment


Revision: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. Python: `3.12.0 (tags/v3.12.0:0fb18b0, Oct  2 2023, 13:03:39) [MSC v.1935 64 bit (AMD64)]`. Date: 2026-10-16, America/New_York. The repository was already substantially dirty; `working_tree_before.txt` retains exact short status. The investigation adds only `artifacts/pr_eg_r2` and updates the established handoff. No commit, reset or production edit was made.

Provider configuration: default, strict-social/high-precision and retry route all `gpt-4.1-mini`; routing enabled. Credentials loaded locally and never included. Explicit experimental endpoint `https://api.openai.com/v1`. Responses transport; temperature and top_p omitted like production, SDK retries disabled in synthetic probes, cap 500 output tokens. The cap controls experimental output length, not an assumed minimum input budget. Raw returned configuration/usage is retained per trial; production narration budget was 700 during local capture.

Read history: EF-R3 authority inventory/call graph/cost and restrictive dialogue reports; EF-R4 authorization, final-response consistency and provider eligibility; EG dialogue implementation; R1 continuity design, commitment retention, live transcripts, performance, integrity and remaining issues. Selected historical sources are included under `predecessors/`.

Initial local provider connection failed. Automatic review initially rejected a broad live batch; inspection of the exact synthetic prompt and a single explicit-endpoint request established a permitted narrower scope. The core, sequence and ablation phases then ran successfully. Review separately rejected exporting large production-capture world/session payloads. Those requests never ran. Local tokenization avoids that export.

An initial TestClient attempt hung creating a Windows asyncio socketpair inside the sandbox; it never reached a provider. Both hung attempts were stopped. Direct synchronous `api.chat` was used for local capture, with scripted interpretation/narration clearly labeled. A faulthandler diagnosis identified the socketpair wait. Initial pytest used sandbox temp files and recorded permission failures (42 passed, 2 failed, 27 setup errors); a workspace-temp rerun reached the same socket restriction and was stopped. The unsandboxed local-only focused rerun passed 71 tests in 3.71s; `focused_local_junit.xml` is the authoritative current focused result. The failed first junit is retained.

No complete regression suite was run. HISTORICAL: `artifacts/pr_eg_r1/regression_junit.xml` / report 16 records 393/19. This cycle does not assert that every inherited family failure is unchanged. LOCAL: `source_integrity.json` verifies all 316 protected files unchanged.


Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.
