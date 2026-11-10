"""Compare before/after junit failure identities."""
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def failures(name):
    tree = ET.parse(ROOT / name)
    suite = tree.getroot().find("testsuite")
    ids = []
    for case in suite.findall("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            ids.append(f"{case.get('classname')}::{case.get('name')}")
    return {
        "tests": int(suite.get("tests")),
        "failures": int(suite.get("failures")),
        "errors": int(suite.get("errors")),
        "skipped": int(suite.get("skipped")),
        "ids": ids,
    }


before = failures("before_combined_junit.xml")
after = failures("after_combined_junit.xml")
bset, aset = set(before["ids"]), set(after["ids"])
print("BEFORE", before["tests"], before["failures"], before["errors"], before["skipped"])
print("AFTER", after["tests"], after["failures"], after["errors"], after["skipped"])
print("NEW", sorted(aset - bset))
print("RESOLVED", sorted(bset - aset))
print("SAME", len(aset & bset))
