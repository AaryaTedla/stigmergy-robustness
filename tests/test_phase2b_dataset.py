"""Contracts for the inspectable Phase 2B agent-step CSV export.

The fixture is deliberately tiny but retains the corpus boundary: local files
contain only local data, while the audit index supplies grouping provenance.
The tests prove that one environment step becomes one row per agent, the CSV
schema separates model inputs from metadata/outcomes, and leaked attack fields
cause a fail-closed export rather than a convenient but invalid dataset.
"""

import csv
import json

import pytest

from stigmergy.phase2b_corpus import PLAN_PURPOSE
from stigmergy.phase2b_dataset import export_phase2b_agent_steps


def _write_json(path, value):
    """Write a JSON fixture while making its parent tree explicit."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _make_corpus(root, leaked=False):
    """Create one complete three-scenario family, with two agents and two steps each."""
    corpus = root / "corpus"
    group = "persistent_20_immediate__policy-7_map-100_action-7_stochastic"
    relative = "model_observable/persistent_20_immediate/policy-7_map-100_action-7_stochastic/clean/steps.jsonl"
    group_details = {"corpus_group_id": group, "calibration_id": "persistent_20_immediate",
                     "training_seed": 7, "map_seed": 100, "action_seed": 7, "action_mode": "stochastic",
                     "split": "development", "scenarios": ["clean", "injection_disabled", "attacked"]}
    _write_json(corpus / "group_splits.json", {"assignments": [group_details]})
    _write_json(corpus / "manifest.json", {
        "format_version": 1, "status": "completed", "purpose": PLAN_PURPOSE,
        "development_only": True, "groups": [group_details],
    })
    index = {"calibration_id": "persistent_20_immediate", "corpus_group_id": group,
             "scenario": "clean", "split": "development", "training_seed": 7,
             "map_seed": 100, "action_seed": 7, "action_mode": "stochastic",
             "step_count": 2, "model_observable_steps": relative}
    records = []
    for step in (1, 2):
        agents = ("agent_0", "agent_1")
        local = {
            "observations_before": {agent: [float(step)] * 58 for agent in agents},
            "features": {agent: [0.1] * 12 for agent in agents},
            "proposed_actions": {agent: 2 for agent in agents},
            "executed_actions": {agent: 2 for agent in agents},
            "rewards": {agent: 0.0 for agent in agents},
            "terminations": {agent: False for agent in agents},
            "truncations": {agent: False for agent in agents},
            "infos": {agent: {"blocked": False, "picked_up": False, "delivered": False}
                      for agent in agents},
            "timeout_active": {agent: False for agent in agents},
        }
        if leaked:
            local["attack_events"] = []
        records.append({"step": step, "local": local})
    entries = []
    for scenario in group_details["scenarios"]:
        entry = {**index, "scenario": scenario,
                 "model_observable_steps": relative.replace("/clean/", f"/{scenario}/")}
        entries.append(entry)
        steps = corpus / entry["model_observable_steps"]
        steps.parent.mkdir(parents=True, exist_ok=True)
        steps.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    (corpus / "audit_index.jsonl").write_text("".join(json.dumps(entry) + "\n" for entry in entries))
    return corpus


def test_agent_step_export_flattens_local_rows_and_marks_safe_input_columns(tmp_path):
    """Three paired two-agent/two-step episodes produce twelve safely typed CSV rows."""
    corpus = _make_corpus(tmp_path)
    output = tmp_path / "export"
    summary = export_phase2b_agent_steps(corpus, output)
    assert summary["episode_count"] == 3
    assert summary["environment_step_count"] == 6
    assert summary["agent_step_count"] == 12
    with (output / "agent_steps.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 12
    assert rows[0]["agent_id"] == "agent_0" and rows[0]["observation_before_00"] == "1.0"
    assert rows[-1]["step"] == "2" and rows[-1]["history_revisit_fraction"] == "0.1"
    schema = json.loads((output / "schema.json").read_text())
    assert "observation_before_00" in schema["model_input_columns"]
    assert "scenario" in schema["provenance_columns_not_model_inputs"]
    assert "attack_events" in schema["excluded_simulator_only_fields"]


def test_agent_step_export_rejects_a_leaked_attack_field(tmp_path):
    """Audit-only attack provenance can never silently reach the flat CSV."""
    corpus = _make_corpus(tmp_path, leaked=True)
    with pytest.raises(ValueError, match="leaks simulator-only metadata"):
        export_phase2b_agent_steps(corpus, tmp_path / "must-fail")
    manifest = json.loads((tmp_path / "must-fail" / "manifest.json").read_text())
    assert manifest["status"] == "failed"


@pytest.mark.parametrize("field,value", [("observations_before", float("nan")),
    ("features", float("inf")), ("rewards", float("nan")), ("executed_actions", -1),
    ("proposed_actions", True), ("terminations", "false"), ("timeout_active", 0),
    ("infos", 1), ("unknown_field", 0)])
def test_export_rejects_invalid_local_values_and_never_marks_complete(tmp_path, field, value):
    """Malformed model inputs and outcomes fail closed with inspectable partial status."""
    corpus = _make_corpus(tmp_path); path = next((corpus / "model_observable").glob("**/clean/steps.jsonl"))
    records = [json.loads(line) for line in path.read_text().splitlines()]; local = records[0]["local"]
    if field in ("observations_before", "features"): local[field]["agent_0"][0] = value
    elif field == "infos": local[field]["agent_0"]["blocked"] = value
    elif field == "unknown_field": local[field] = value
    else: local[field]["agent_0"] = value
    path.write_text("".join(json.dumps(record) + "\n" for record in records)); output = tmp_path / "export"
    with pytest.raises(ValueError): export_phase2b_agent_steps(corpus, output)
    assert json.loads((output / "manifest.json").read_text())["status"] == "failed"


@pytest.mark.parametrize("change", ["missing", "duplicate", "map", "split", "unknown", "duplicate_group", "audit_path"])
def test_export_rejects_incomplete_or_conflicting_provenance_before_output(tmp_path, change):
    """Every indexed family must exactly match its whole development group and local-tree path."""
    corpus = _make_corpus(tmp_path); path = corpus / "audit_index.jsonl"
    entries = [json.loads(line) for line in path.read_text().splitlines()]
    if change == "missing": entries.pop()
    elif change == "duplicate": entries.append(entries[0].copy())
    elif change == "map": entries[0]["map_seed"] = 999
    elif change == "split":
        split = corpus / "group_splits.json"; value = json.loads(split.read_text())
        value["assignments"][0]["map_seed"] = 999; split.write_text(json.dumps(value))
    elif change == "unknown": entries[0]["scenario"] = "other"
    elif change == "audit_path": entries[0]["model_observable_steps"] = "audit/steps.jsonl"
    else:
        manifest_path = corpus / "manifest.json"; value = json.loads(manifest_path.read_text())
        value["groups"].append(value["groups"][0].copy()); manifest_path.write_text(json.dumps(value))
    path.write_text("".join(json.dumps(entry) + "\n" for entry in entries)); output = tmp_path / "must-not-exist"
    with pytest.raises(ValueError): export_phase2b_agent_steps(corpus, output)
    assert not output.exists()


def test_export_repeated_outputs_match_and_existing_output_is_immutable(tmp_path):
    """Inspectability does not permit overwriting evidence; independent exports are byte-repeatable."""
    corpus = _make_corpus(tmp_path); first, second = tmp_path / "first", tmp_path / "second"
    assert export_phase2b_agent_steps(corpus, first) == export_phase2b_agent_steps(corpus, second)
    for name in ("agent_steps.csv", "schema.json", "summary.json", "manifest.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    before = (first / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError): export_phase2b_agent_steps(corpus, first)
    assert (first / "manifest.json").read_bytes() == before


def test_export_interruption_preserves_incomplete_manifest(tmp_path, monkeypatch):
    """A stopped CSV write must remain inspectable and explicitly incomplete."""
    import stigmergy.phase2b_dataset as module
    corpus = _make_corpus(tmp_path)
    def interrupted(*args):
        """Model interruption after the fresh export directory has been created."""
        raise KeyboardInterrupt
    monkeypatch.setattr(module, "_agent_row", interrupted)
    output = tmp_path / "interrupted"
    with pytest.raises(KeyboardInterrupt): export_phase2b_agent_steps(corpus, output)
    assert json.loads((output / "manifest.json").read_text())["status"] == "incomplete"
