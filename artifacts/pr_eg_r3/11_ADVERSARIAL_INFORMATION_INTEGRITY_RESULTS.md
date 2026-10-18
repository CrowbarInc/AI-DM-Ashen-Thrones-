# 11 — Adversarial Information-Integrity Results

Pre-repair primary turn 2 is the integrity defect that the name check was added to stop.

PLAYER: Say that in simpler words.

CANDIDATE AND DELIVERED: The road just past the gate is called the north street.

Decision: `adopted`. Reasons: []. The synonym group that treats “street” and “road” as interchangeable allowed the proper name “north road” to become “north street.” That is a delivered change of entity identity. The transcript is `live_qualification_before_name_repair.json`. The live plan was not edited after this result.

Repaired primary turn 2 delivered “The street just past the gate is called the north road.” with an empty reason list. The unit test now rejects “The road just past the gate is called the north street.” and accepts the north-road sentence.

Controlled adversarial candidates in the unit suite and frozen holdouts cover a capital destination, smugglers, an unattended gate, guards abandoning posts, ten silver, and a named inventor. Expected rejections were not rewritten. In the repaired live sample, rejected candidates do not appear in player text or delivered history. Integrity findings on the repaired transcript: [].

No delivered repaired turn contains “north street,” an asserted unattended schedule, “ten silver,” “smuggler,” or a positive payment promise. The authorized watch facts remain deliverable, so the check is not a blanket ban on consequential subjects.
