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
    """Create one completed one-episode corpus with two local agents and two steps."""
    corpus = root / "corpus"
    group = "persistent_20_immediate__policy-7_map-100_action-7_stochastic"
    relative = "model_observable/persistent_20_immediate/policy-7_map-100_action-7_stochastic/clean/steps.jsonl"
    _write_json(corpus / "manifest.json", {
        "format_version": 1, "status": "completed", "purpose": PLAN_PURPOSE,
        "development_only": True, "groups": [{"corpus_group_id": group}],
    })
    index = {"calibration_id": "persistent_20_immediate", "corpus_group_id": group,
             "scenario": "clean", "split": "development", "training_seed": 7,
             "map_seed": 100, "action_seed": 7, "action_mode": "stochastic",
             "step_count": 2, "model_observable_steps": relative}
    (corpus / "audit_index.jsonl").write_text(json.dumps(index) + "\n", encoding="utf-8")
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
    steps = corpus / relative
    steps.parent.mkdir(parents=True, exist_ok=True)
    steps.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    return corpus


def test_agent_step_export_flattens_local_rows_and_marks_safe_input_columns(tmp_path):
    """Two two-agent transitions produce four CSV rows with no audit fields."""
    corpus = _make_corpus(tmp_path)
    output = tmp_path / "export"
    summary = export_phase2b_agent_steps(corpus, output)
    assert summary["episode_count"] == 1
    assert summary["environment_step_count"] == 2
    assert summary["agent_step_count"] == 4
    with (output / "agent_steps.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 4
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
