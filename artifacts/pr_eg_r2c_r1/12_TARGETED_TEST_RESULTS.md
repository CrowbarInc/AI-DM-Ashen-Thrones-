# 12 — Targeted Test Results

```json
{
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T01]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T02]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T03]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T04]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T05]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T06]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T07]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T08]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T09]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T10]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T11]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T12]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T13]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T14]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T15]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T16]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T17]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T18]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T19]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T20]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T21]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T22]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T23]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T24]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T25]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T26]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T27]": "passed",
  "tests.test_pr_eg_r2c_speech_adoption::test_topic_grounding_and_recall_matrix[T28]": "passed"
}
```

T01–T28 all pass in the final combined JUnit. These are deterministic owner-seam controls, with actual storage used for persistence. Five additional controls cover five competing facts across speakers, long exact/uncertain recall, watch-absence insufficiency, no competing discovery during repetition, and provider-evidence bypass rejection. Some matrix rows exercise the same underlying seam; they are not 28 independent end-to-end provider conversations.
