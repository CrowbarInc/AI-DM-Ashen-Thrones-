import xml.etree.ElementTree as ET

root = ET.parse("artifacts/pr_bv_operation_projection/regression.xml").getroot()
suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
tests = fails = errors = skipped = 0
failed = []
by_file: dict[str, dict[str, int]] = {}
c18 = []
for suite in suites:
    tests += int(suite.attrib.get("tests", 0))
    fails += int(suite.attrib.get("failures", 0))
    errors += int(suite.attrib.get("errors", 0))
    skipped += int(suite.attrib.get("skipped", 0))
    for case in suite.iter("testcase"):
        classname = case.attrib.get("classname", "")
        name = case.attrib.get("name", "")
        file_name = classname.split(".")[-1]
        bucket = by_file.setdefault(file_name, {"t": 0, "f": 0})
        bucket["t"] += 1
        failed_case = case.find("failure") is not None or case.find("error") is not None
        if failed_case:
            bucket["f"] += 1
            failed.append(f"{classname}::{name}")
        if "continuation18" in classname or name == "test_raw_chat_accepts_authorized_fact_and_seals_it":
            c18.append((classname, name, "FAIL" if failed_case else "PASS"))
print(f"tests {tests} failures {fails} errors {errors} skipped {skipped} passed {tests - fails - errors - skipped}")
print("FAILED", failed)
for key, value in sorted(by_file.items()):
    print(f"{key}: {value['t'] - value['f']} passed, {value['f']} failed, {value['t']} total")
print("C18_RELATED", len(c18))
for row in c18:
    if row[2] != "PASS" or row[1] == "test_raw_chat_accepts_authorized_fact_and_seals_it":
        print(row)
