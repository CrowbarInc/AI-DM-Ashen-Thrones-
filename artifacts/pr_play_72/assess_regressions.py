"""Compare retained failure identities and messages; never label by intuition."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
PRIOR = OUT.parent / "pr_play_71v"


def failures(path):
    result = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        failure = case.find("failure")
        if failure is None: failure = case.find("error")
        if failure is not None:
            result[case.get("classname", "") + "::" + case.get("name", "")] = failure.get("message", "")
    return result


def main():
    rows = {}
    for lane in ("focused", "boundary", "broader"):
        current = failures(OUT / (lane + ".xml")); previous = failures(PRIOR / (lane + "_final.xml"))
        rows[lane] = dict(same_failed_nodeids=sorted(set(current)&set(previous)), new_failed_nodeids=sorted(set(current)-set(previous)), prior_not_seen=sorted(set(previous)-set(current)), retained_messages={k:dict(current=current[k], prior=previous.get(k)) for k in current})
    rows["scope"] = "Focused combined suite began before the final two routing repairs. Boundary, broader, clean lifecycle and post-repair owner tests run in separate fresh processes. This is not a full-suite claim."
    post = OUT / "post_repair_regression.xml"
    if post.exists(): rows["post_repair_failed_nodeids"] = sorted(failures(post))
    entry = OUT / "entry_owner.xml"
    if entry.exists() and post.exists():
        old_owner = failures(entry); final_owner = failures(post)
        rows["owner_comparison"] = dict(new_failed_nodeids=sorted(set(final_owner)-set(old_owner)), same_failed_nodeids=sorted(set(final_owner)&set(old_owner)), limits="Targeted pre-repair owner loaded in memory; other current files remain current. See entry_owner_provenance.json.")
    isolated = OUT / "lifecycle_isolated.xml"
    if isolated.exists(): rows["clean_lifecycle_failed_nodeids"] = sorted(failures(isolated))
    timing = "tests.test_pr_play_54_consequential_validation::test_corpus_validation_stays_fast_and_local"
    rows["timing_classification"] = "Newly observed combined-run timing assertion; not called historical. See isolated final rerun for reproducibility."
    if post.exists() and timing not in failures(post): rows["timing_classification"] += " Passed in the fresh post-repair process."
    (OUT / "regression_assessment.json").write_text(json.dumps(rows, indent=2))
    print({k:v.get("new_failed_nodeids") for k,v in rows.items() if isinstance(v,dict)})


if __name__ == "__main__": main()
