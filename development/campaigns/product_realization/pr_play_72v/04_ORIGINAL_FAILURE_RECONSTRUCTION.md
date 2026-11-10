# PR-PLAY-72V — ORIGINAL FAILURE RECONSTRUCTION

| Case | Original input | Target/result | Earliest mismatch |
|---|---|---|---|
| H04 | Study the marker. | milestone / already_searched | F/G: completed repeat versus no-new-discovery status; scorer required success |
| H05 | Examine the weathered stone. | milestone / already_searched | F/G: completed repeat versus no-new-discovery status; scorer required success |
| H09 | Read the notice board again. | notice_board / already_searched | F/G: completed repeat versus no-new-discovery status; scorer required success |
| H10 | Inspect the notice board. | notice_board / already_searched | F/G: completed repeat versus no-new-discovery status; scorer required success |
| H11 | Can I examine the board? | notice_board / already_searched | F/G: completed repeat versus no-new-discovery status; scorer required success |
| H15 | Look at the posted notices. | notice_board / already_searched | F/G: completed repeat versus no-new-discovery status; scorer required success |
| H20 | Please reexamine the notice board. | notice_board / already_searched | F/G: completed repeat versus no-new-discovery status; scorer required success |
| H38 | See what happened. | conversational_answer / conversational_answer | A: memory classification before ambiguity |

The seven action cases are not assumed alike: each original trace was inspected and each names the correct local target with already_searched and no discovery. H04/H05 concern the milestone; the other five concern the board. Historical score remains 52/60 and was not rerun. H38 genuinely lacks one public event/object referent in the survey context; the broad what-happened memory regex claimed it first. Original expected values, actual interpretation, resolver, publication and before/after authority are in original_failure_reconstruction.json.
