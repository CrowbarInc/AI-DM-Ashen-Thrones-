# 05 — Multi-Action and Confirmation Analysis

The exact sentence comes from deterministic `_compound_clarification`, game/conversational_orchestration.py:1146–1188, specifically :1172–1173. It is neither provider narration, final-emission repair, nor the social fallback catalog. The API returns it verbatim.

```text
decision_from_interpretation_record
  classify each component into connected / incidental / unsupported
  if len(connected) > 1 OR unsupported:
      _compound_from_record_parts(...)
        unsupported description -> OTHER, supported=false, consequential=true
        _compound_clarification(..., scene=None)
          persist compound_sequence, ask to start with first step
```

The `or unsupported` condition makes cardinality irrelevant. “Begin.” has one INVENTORY_GRANT (a provider class error). Direct GM address has one SOCIAL_SIGNAL (provider explicitly understands recipient). Both become one unsupported step; no actual multiple consequential operations were described. SOCIAL_SIGNAL is allowed by PR-DO's validation schema but is absent from orchestration's connected and incidental sets and absent from the production bridge's four connected operations.

The helper computes supported/unsupported lists before composing its message. With zero supported steps it still uses the generic confirmation wording. It therefore asks approval of a step the proposal already marks non-executable. Even connected compound steps call a nonempty target sufficient for `supported`; this is not the bridge's full visible-kind/destination validation. This latter coarse support criterion is a static risk, not an additional observed six-turn failure.

Pending representation after turn three (original logged context_update):

```json
{"kind":"compound_sequence","operation":"OTHER",
 "original_text":"The player intends to start the campaign or scene at the Cinderwatch Gate District.",
 "steps":[{"text":"Start the campaign or scene at Cinderwatch Gate District.",
 "label":"Start the campaign or scene at Cinderwatch Gate District.",
 "operation":"OTHER","target_id":"","supported":false,
 "consequential":true,"dependency":"sequence","status":"pending"}],"scene_id":""}
```

`Yes.` is selected by `_select_compound_step` (:1342). Resume checks selected.supported (:1367) and immediately returns DECLINE/unsupported_compound_step (:1373), preserving the entire pending object unchanged. There is no resolver rejection: bridge and resolver were never asked. Confirmation restoration is correct for the stored step, but the stored step should not have been proposed for confirmation. Operation identity is also degraded from INVENTORY_GRANT or SOCIAL_SIGNAL to OTHER, and scene scope is erased by passing scene=None. The empty scene id prevents the usual pending scene-expiry guard from having its intended boundary; scene-change leakage is a source risk, not exercised here.

PR-EC's report and changed-file list explicitly claim introduction/extension of named compound steps, support flags and pending sequences; the current defect resides in that machinery. PR-EA already routed unsupported/multiple-component records into orchestration. Without preserved pre-EC source or a clean commit boundary, exact historical introduction of the overbroad predicate cannot be assigned conclusively. PR-EC demonstrably supplies the current harmful confirmation behavior and extends its persistence/resumption surface; its targeted tests cannot establish general provider integration correctness.

Repair boundary: classify communication purpose first, separate unsupported singleton handling from genuine compound sequencing, and validate offerability before asking for confirmation. Preserve original operation/mode and scene scope in pending state. Approval must authorize an eligible operation; it must not be used to discover an already known unsupported step. No phrase-specific start/DM handlers are proposed.
