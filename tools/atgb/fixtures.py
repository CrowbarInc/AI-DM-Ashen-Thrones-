"""Load and check ATGB scenario fixtures.

Fixtures state communicative expectations. They do not define an exact GM string.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from tools.atgb import BENCHMARK_VERSION, RUBRIC_VERSION, SCENARIO_VERSION
from tools.atgb.isolation import repo_root

PARTITIONS = ("development_visible", "related_variation", "held_out")
CAPABILITIES = (
    "intent_recognition",
    "conversational_continuity",
    "corrections_and_clarifications",
    "response_relevance",
    "npc_dialogue_coherence",
    "ic_ooc_boundaries",
    "ambiguity_handling",
    "initiative_and_naturalness",
)
FORBIDDEN_EXACT_KEYS = frozenset(
    {
        "expected_gm_text",
        "expected_response_text",
        "exact_response",
        "exact_gm_text",
        "required_reply",
    }
)
TURN_FIELDS = (
    "turn_id",
    "catalog_heading",
    "primary_capability",
    "player_input",
    "communicative_act",
    "interpretation_pass",
    "response_pass",
    "authority_pass",
    "acceptable_variations",
    "unacceptable_behaviors",
    "clarification_expected",
    "clarification_notes",
    "continuity_expected",
    "continuity_notes",
    "required_evidence",
)
SCENARIO_FIELDS = (
    "scenario_id",
    "title",
    "catalog_heading",
    "source_catalog",
    "partition",
    "catalog_partition",
    "evidence_status",
    "evidence_status_note",
    "primary_capability",
    "secondary_capabilities",
    "environment_id",
    "initial_context",
    "authoritative_facts",
    "npc_knowledge",
    "expected_outcomes",
    "acceptable_variations",
    "unacceptable_behaviors",
    "required_evidence",
    "setup_dependencies",
    "determinism",
    "turns",
)


class FixtureError(ValueError):
    """A fixture is missing, internally inconsistent, or not the adopted corpus."""


def corpus_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "data" / "validation" / "atgb"


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FixtureError(f"{path} is not valid JSON: {exc}") from exc


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise FixtureError(f"{label} must be a JSON object.")
    return value


def _forbid_exact_match(value: Mapping[str, Any], label: str) -> None:
    present = FORBIDDEN_EXACT_KEYS.intersection(value)
    if present:
        raise FixtureError(
            f"{label} uses exact-response matching ({', '.join(sorted(present))}). "
            "Behavioral criteria must accept multiple natural replies."
        )


def _scenario_paths(directory: Path) -> list[Path]:
    visible = sorted((directory / "visible").glob("S*.json"))
    held = sorted((directory / "held_out").glob("S*.json"))
    return visible + held


def load_corpus(
    root: Path | None = None,
    *,
    partitions: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Load the adopted corpus. Held-out files are included when that partition is requested.

    Ordinary gameplay tests should not call this for tuning. The benchmark loader
    reads held-out fixtures so partition counts and schema can be checked, and so
    a future checkpoint can execute them. Their evidence status stays
    ``held_out_previously_exposed``.
    """

    directory = corpus_dir(root)
    corpus_path = directory / "corpus.json"
    if not corpus_path.is_file():
        raise FixtureError(f"Missing corpus manifest {corpus_path}.")
    corpus = dict(_require_mapping(_load_json(corpus_path), str(corpus_path)))
    if corpus.get("benchmark_version") != BENCHMARK_VERSION:
        raise FixtureError(
            f"Corpus benchmark_version is {corpus.get('benchmark_version')!r}, expected {BENCHMARK_VERSION}."
        )
    if corpus.get("scenario_version") != SCENARIO_VERSION:
        raise FixtureError(
            f"Corpus scenario_version is {corpus.get('scenario_version')!r}, expected {SCENARIO_VERSION}."
        )
    if corpus.get("rubric_version") != RUBRIC_VERSION:
        raise FixtureError(
            f"Corpus rubric_version is {corpus.get('rubric_version')!r}, expected {RUBRIC_VERSION}."
        )
    environments = _require_mapping(corpus.get("environments"), "environments")
    selected = tuple(partitions) if partitions is not None else PARTITIONS
    unknown = [item for item in selected if item not in PARTITIONS]
    if unknown:
        raise FixtureError(f"Unknown partition(s): {', '.join(unknown)}.")
    scenarios: list[dict[str, Any]] = []
    for path in _scenario_paths(directory):
        document = dict(_require_mapping(_load_json(path), str(path)))
        folder = path.parent.name
        _validate_scenario(document, path=path, folder=folder, environments=environments)
        if document["partition"] in selected:
            scenarios.append(document)
    scenarios.sort(key=lambda item: item["scenario_id"])
    _validate_collection(scenarios, corpus, selected=selected)
    return {
        "manifest": corpus,
        "scenarios": scenarios,
        "partitions": list(selected),
    }


def _validate_scenario(
    scenario: Mapping[str, Any],
    *,
    path: Path,
    folder: str,
    environments: Mapping[str, Any],
) -> None:
    label = str(path)
    missing = [field for field in SCENARIO_FIELDS if field not in scenario]
    if missing:
        raise FixtureError(f"{label} is missing {', '.join(missing)}.")
    _forbid_exact_match(scenario, label)
    partition = scenario["partition"]
    if partition not in PARTITIONS:
        raise FixtureError(f"{label} has unknown partition {partition!r}.")
    if folder == "held_out" and partition != "held_out":
        raise FixtureError(f"{label} is in held_out/ but its partition is {partition!r}.")
    if folder == "visible" and partition == "held_out":
        raise FixtureError(f"{label} is held-out and must live in held_out/.")
    if partition == "held_out" and scenario.get("evidence_status") != "held_out_previously_exposed":
        raise FixtureError(
            f"{label} is held-out and must record evidence_status held_out_previously_exposed. "
            "These scenarios already appeared in the ATGB-01 review."
        )
    if scenario.get("primary_capability") not in CAPABILITIES:
        raise FixtureError(f"{label} has unknown primary capability {scenario.get('primary_capability')!r}.")
    environment_id = scenario.get("environment_id")
    if environment_id not in environments:
        raise FixtureError(f"{label} references unknown environment {environment_id!r}.")
    environment = _require_mapping(environments[environment_id], f"environment {environment_id}")
    if "location_id" not in environment or "shared_facts" not in environment:
        raise FixtureError(f"Environment {environment_id} needs location_id and shared_facts.")
    turns = scenario.get("turns")
    if not isinstance(turns, list) or not turns:
        raise FixtureError(f"{label} needs at least one turn.")
    expected_prefix = f"{scenario['scenario_id']}."
    previous = 0
    for turn in turns:
        turn_map = _require_mapping(turn, f"{label} turn")
        _forbid_exact_match(turn_map, f"{label} {turn_map.get('turn_id')}")
        missing_turn = [field for field in TURN_FIELDS if field not in turn_map]
        if missing_turn:
            raise FixtureError(f"{label} turn is missing {', '.join(missing_turn)}.")
        turn_id = str(turn_map["turn_id"])
        if not turn_id.startswith(expected_prefix):
            raise FixtureError(f"{turn_id} does not belong to {scenario['scenario_id']}.")
        number = int(turn_id.split(".")[1])
        if number != previous + 1:
            raise FixtureError(f"{label} turns are not in catalog order at {turn_id}.")
        previous = number
        if not str(turn_map["player_input"]).strip():
            raise FixtureError(f"{turn_id} has an empty player input.")
        if turn_map["primary_capability"] not in CAPABILITIES:
            raise FixtureError(f"{turn_id} has unknown primary capability.")
        for prose_field in ("interpretation_pass", "response_pass", "authority_pass"):
            if not str(turn_map[prose_field]).strip():
                raise FixtureError(f"{turn_id} is missing a behavioral {prose_field}.")
        if turn_map["player_input"] == turn_map["response_pass"]:
            raise FixtureError(f"{turn_id} uses the player line as the required reply.")


def _validate_collection(scenarios: list[dict[str, Any]], corpus: Mapping[str, Any], *, selected: tuple[str, ...]) -> None:
    if not scenarios:
        raise FixtureError("No scenarios matched the requested partitions.")
    ids = [item["scenario_id"] for item in scenarios]
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise FixtureError(f"Scenario ids are not a unique ordered set: {ids}.")
    if selected == PARTITIONS:
        expected = corpus.get("expected_turns")
        if not isinstance(expected, dict):
            raise FixtureError("corpus.json expected_turns is missing.")
        actual = partition_counts(scenarios)
        for key in ("development_visible", "related_variation", "held_out", "total"):
            if actual.get(key) != expected.get(key):
                raise FixtureError(
                    "Scenario counts do not match corpus.json expected_turns. "
                    f"Actual {actual}. Expected {dict(expected)}. "
                    "Counts were not changed to force agreement."
                )
        discrepancy = str(corpus.get("catalog_discrepancy") or "").strip()
        if "S07" not in discrepancy:
            raise FixtureError("corpus.json must document the S07 partition discrepancy with the ATGB-01 catalog.")


def partition_counts(scenarios: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts = {name: 0 for name in PARTITIONS}
    total = 0
    for scenario in scenarios:
        partition = str(scenario["partition"])
        turn_count = len(scenario["turns"])
        counts[partition] = counts.get(partition, 0) + turn_count
        total += turn_count
    counts["total"] = total
    return counts


def iter_turns(scenarios: Iterable[Mapping[str, Any]]) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
    rows: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for scenario in scenarios:
        for turn in scenario["turns"]:
            rows.append((scenario, turn))
    return rows


def authoritative_context(scenario: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    environments = manifest.get("environments") if isinstance(manifest.get("environments"), dict) else {}
    environment = environments.get(scenario["environment_id"]) if isinstance(environments, dict) else None
    shared = []
    location_id = None
    if isinstance(environment, dict):
        location_id = environment.get("location_id")
        facts = environment.get("shared_facts")
        if isinstance(facts, list):
            shared = facts
    return {
        "environment_id": scenario.get("environment_id"),
        "location_id": location_id,
        "shared_facts": shared,
        "initial_context": scenario.get("initial_context"),
        "authoritative_facts": scenario.get("authoritative_facts"),
        "npc_knowledge": scenario.get("npc_knowledge"),
        "unacceptable_behaviors": scenario.get("unacceptable_behaviors"),
    }
