"""Contracts for the Phase 2B development-calibration corpus builder.

These tests use small JSON-only source artifacts rather than PPO rollouts. They
verify the dataset boundary itself: a completed three-scenario group becomes
one development-only corpus group, model-visible steps exclude simulator-only
metadata, and an incomplete group is rejected before a corpus directory is
created. They do not turn the corpus into detector training data.
"""

import json
from pathlib import Path

import pytest

from stigmergy.phase2b_corpus import (PLAN_PURPOSE, SOURCE_PURPOSE,
                                      build_phase2b_calibration_corpus)


def _write_json(path, value):
    """Write one fixture JSON file with its parent directory created explicitly."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _make_source(root, scenarios=("clean", "injection_disabled", "attacked")):
    """Create one minimal completed calibration family with separated local/audit fields."""
    run = root / "artifacts" / "phase2b" / "run-1"
    group = {"group_id": "policy-7_map-100_action-7_stochastic", "split": "development",
             "training_seed": 7, "map_seed": 100, "action_seed": 7,
             "action_mode": "stochastic", "scenarios": list(scenarios)}
    _write_json(run / "manifest.json", {"status": "completed", "purpose": SOURCE_PURPOSE,
                                         "attack_config": {"start_step": 0}, "groups": [group]})
    _write_json(run / "group_splits.json", {"assignments": [group]})
    for scenario in scenarios:
        episode_dir = run / "episodes" / group["group_id"] / scenario
        _write_json(episode_dir / "episode.json", {"split": "development", "metrics": {
            "group_id": group["group_id"], "scenario": scenario, "steps": 1,
            "local_record_sha256": "local-digest", "map_seed": 100, "action_seed": 7, "action_mode": "stochastic",
        }, "simulator_metadata": {"compromised_agents": ["agent_0"]}})
        agent = "agent_0"
        local = {"observations_before": {agent: [0.0] * 58}, "observations_after": {agent: [0.0] * 58},
                 "features": {agent: [0.0] * 12}, "proposed_actions": {agent: 0},
                 "executed_actions": {agent: 0}, "rewards": {agent: 0.0},
                 "terminations": {agent: False}, "truncations": {agent: False},
                 "timeout_active": {agent: False},
                 "infos": {agent: {"blocked": False, "picked_up": False, "delivered": False}}}
        record = {"step": 1, "local": local,
                  "simulator_metadata": {"attack_events": [], "honest_delivered": 0}}
        episode_dir.mkdir(parents=True, exist_ok=True)
        (episode_dir / "steps.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    return run


def _write_plan(root, source_path="artifacts/phase2b/run-1"):
    """Create a repository-shaped corpus plan pointing to the fixture run."""
    plan = root / "configs" / "phase2b" / "corpus.json"
    _write_json(plan, {"format_version": 1, "purpose": PLAN_PURPOSE,
                       "sources": [{"calibration_id": "persistent_20_immediate",
                                    "run_path": source_path}]})
    return plan


def test_corpus_builder_keeps_groups_whole_and_separates_audit_metadata(tmp_path):
    """A complete source produces one development group and three safely split episode files."""
    root = tmp_path / "project"
    _make_source(root)
    plan = _write_plan(root)
    summary = build_phase2b_calibration_corpus(plan, root / "data" / "generated" / "corpus")
    assert summary == {"purpose": PLAN_PURPOSE, "development_only": True,
                       "source_run_count": 1, "group_count": 1, "episode_count": 3,
                       "scenario_count_per_group": 3, "split_counts": {"development": 1},
                       "limitations": ["calibration evidence only", "no temporal windows",
                                       "no train/validation/test split", "no detector was fit",
                                       "no defense was evaluated", "not a robustness claim"]}
    output = root / "data" / "generated" / "corpus"
    manifest = json.loads((output / "manifest.json").read_text())
    splits = json.loads((output / "group_splits.json").read_text())
    index = [json.loads(line) for line in (output / "audit_index.jsonl").read_text().splitlines()]
    assert manifest["status"] == "completed" and len(manifest["groups"]) == len(index) // 3 == 1
    assert splits["assignments"] == manifest["groups"] and "group_split_manifest_sha256" in manifest
    model = json.loads((output / index[0]["model_observable_steps"]).read_text().splitlines()[0])
    audit = json.loads((output / index[0]["audit_steps"]).read_text().splitlines()[0])
    assert set(model) == {"step", "local"} and "simulator_metadata" not in json.dumps(model)
    assert set(audit) == {"step", "simulator_metadata"} and "attack_events" in audit["simulator_metadata"]


def test_corpus_builder_rejects_an_incomplete_source_group_before_writing_output(tmp_path):
    """A missing scenario cannot become a partial corpus group or future split leak."""
    root = tmp_path / "project"
    _make_source(root, scenarios=("clean", "attacked"))
    plan = _write_plan(root)
    output = root / "data" / "generated" / "must-not-exist"
    with pytest.raises(ValueError, match="complete development family"):
        build_phase2b_calibration_corpus(plan, output)
    assert not output.exists()


def test_corpus_builder_rejects_simulator_metadata_in_a_local_source_record(tmp_path):
    """The archive fails closed if a source leaks attack fields into model-visible data."""
    root = tmp_path / "project"
    run = _make_source(root)
    steps = run / "episodes" / "policy-7_map-100_action-7_stochastic" / "attacked" / "steps.jsonl"
    record = json.loads(steps.read_text())
    record["local"]["attack_events"] = []
    steps.write_text(json.dumps(record) + "\n", encoding="utf-8")
    plan = _write_plan(root)
    with pytest.raises(ValueError, match="leaks simulator-only keys"):
        build_phase2b_calibration_corpus(plan, root / "data" / "generated" / "must-not-exist")


@pytest.mark.parametrize("change", ["duplicate", "map", "missing_assignment", "unsafe_id"])
def test_corpus_rejects_conflicting_or_duplicate_group_provenance(tmp_path, change):
    """Completion status cannot hide repeated groups or disagreement with split provenance."""
    root = tmp_path / "project"; run = _make_source(root); plan = _write_plan(root)
    path = run / "manifest.json"; manifest = json.loads(path.read_text())
    split_path = run / "group_splits.json"; splits = json.loads(split_path.read_text())
    if change == "duplicate": manifest["groups"].append(manifest["groups"][0].copy())
    elif change == "map": splits["assignments"][0]["map_seed"] = 999
    elif change == "missing_assignment": splits["assignments"] = []
    else: manifest["groups"][0]["group_id"] = "../outside"
    path.write_text(json.dumps(manifest)); split_path.write_text(json.dumps(splits))
    output = root / "data/generated/must-fail"
    with pytest.raises(ValueError): build_phase2b_calibration_corpus(plan, output)
    assert not output.exists()


@pytest.mark.parametrize("field,value", [("features", float("inf")), ("executed_actions", 5),
                                          ("terminations", "false"), ("unknown_audit", 1)])
def test_corpus_rejects_malformed_local_values_and_retains_failed_manifest(tmp_path, field, value):
    """The corpus boundary rejects the same invalid values as the tabular export."""
    root = tmp_path / "project"; run = _make_source(root); plan = _write_plan(root)
    path = next((run / "episodes").glob("*/clean/steps.jsonl")); record = json.loads(path.read_text())
    if field == "features": record["local"][field]["agent_0"][0] = value
    elif field == "unknown_audit": record["local"][field] = value
    else: record["local"][field]["agent_0"] = value
    path.write_text(json.dumps(record) + "\n"); output = root / "data/generated/must-fail"
    with pytest.raises(ValueError): build_phase2b_calibration_corpus(plan, output)
    assert json.loads((output / "manifest.json").read_text())["status"] == "failed"


def test_corpus_repeated_builds_match_and_existing_directory_is_preserved(tmp_path):
    """A valid source has deterministic outputs; a second write cannot replace the archive."""
    root = tmp_path / "project"; _make_source(root); plan = _write_plan(root)
    first, second = root / "data/generated/first", root / "data/generated/second"
    assert build_phase2b_calibration_corpus(plan, first) == build_phase2b_calibration_corpus(plan, second)
    files = [path.relative_to(first) for path in first.rglob("*") if path.is_file()]
    assert all((first / path).read_bytes() == (second / path).read_bytes() for path in files)
    before = (first / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError): build_phase2b_calibration_corpus(plan, first)
    assert (first / "manifest.json").read_bytes() == before


def test_corpus_interruption_preserves_incomplete_manifest(tmp_path, monkeypatch):
    """An interrupted write is retained as incomplete evidence and cannot look completed."""
    import stigmergy.phase2b_corpus as module
    root = tmp_path / "project"; _make_source(root); plan = _write_plan(root)
    def interrupted(*args):
        """Model a user interrupt during packaging, without modifying source artifacts."""
        raise KeyboardInterrupt
    monkeypatch.setattr(module, "_package_episode", interrupted)
    output = root / "data/generated/interrupted"
    with pytest.raises(KeyboardInterrupt): build_phase2b_calibration_corpus(plan, output)
    assert json.loads((output / "manifest.json").read_text())["status"] == "incomplete"
