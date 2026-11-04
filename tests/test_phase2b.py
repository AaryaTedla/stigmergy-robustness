"""Focused Phase 2B attack-calibration contracts.

The tests create a tiny genuine four-agent PPO checkpoint so they exercise the
same frozen-checkpoint validation and stochastic local-policy path that the
Candidate J runner uses. They do not execute the 36-episode Candidate J
matrix. Instead, a one-policy/one-map plan checks matched controls, group
atomicity, and rejection of a changed attack contract before output creation.
"""

from dataclasses import asdict
import json
from pathlib import Path

import pytest

pytest.importorskip("stable_baselines3")

from stigmergy import AttackConfig, GridConfig
from stigmergy.phase2b import (PLAN_PURPOSE, Phase2BAttackCalibrationPlan,
                               load_phase2b_plan, run_phase2b_attack_calibration)
from stigmergy.training import TrainingConfig, run_training


def _write_json(path, value):
    """Save one small JSON fixture, creating only its immediate parent path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def phase2b_plan(tmp_path):
    """Create a complete one-group plan and frozen checkpoint inside a fake root."""
    root = tmp_path / "project"
    grid = GridConfig(n_agents=4, horizon=4, food_per_patch=1)
    grid_path = root / "configs" / "phase2a" / "env" / "candidate.json"
    policy_path = root / "configs" / "phase2a" / "policy.json"
    _write_json(grid_path, asdict(grid))
    _write_json(policy_path, asdict(TrainingConfig(seed=7, total_transitions=8, n_steps=4,
        batch_size=4, n_epochs=1, train_map_seeds=(1,), diagnostic_map_seeds=(2,))))
    trained = root / "training"
    run_training(grid_path, policy_path, trained)
    checkpoint_dir = root / "checkpoints" / "full-seed-7"
    checkpoint_dir.mkdir(parents=True)
    for name in ("policy.zip", "manifest.json", "summary.json"):
        (checkpoint_dir / name).write_bytes((trained / name).read_bytes())
    attack_path = root / "configs" / "attack" / "persistent.json"
    _write_json(attack_path, AttackConfig().as_dict())
    plan_path = root / "configs" / "phase2b" / "plan.json"
    _write_json(plan_path, {
        "format_version": 1, "purpose": PLAN_PURPOSE, "candidate_id": "tiny-candidate",
        "grid_config_path": "configs/phase2a/env/candidate.json",
        "checkpoint_template": "checkpoints/full-seed-{seed}/policy.zip",
        "attack_config_path": "configs/attack/persistent.json", "training_seeds": [7],
        "map_seeds": [2], "action_seeds": [7], "action_mode": "stochastic",
        "group_split": "development",
    })
    return root, plan_path


def test_phase2b_plan_accepts_the_declared_persistent_calibration_contract(phase2b_plan):
    """The plan resolves a four-agent Candidate-J-shaped grid and 1/1/20 attack budget."""
    root, plan_path = phase2b_plan
    plan, resolved_root, _, grid, _, attack = load_phase2b_plan(plan_path)
    assert resolved_root == root
    assert plan.training_seeds == (7,) and plan.map_seeds == (2,) and plan.action_seeds == (7,)
    assert grid.n_agents == 4
    assert (attack.compromised_count, attack.requested_deposit, attack.per_step_budget,
            attack.episode_budget, attack.mode) == (1, 1.0, 1.0, 20.0, "persistent")


def test_repository_duration_followup_changes_only_the_declared_episode_budget():
    """The 200-unit plan remains four-agent, local and persistent rather than changing attack scope."""
    root = Path(__file__).resolve().parents[1]
    plan, _, _, grid, _, attack = load_phase2b_plan(
        root / "configs/phase2b/attack-calibration-persistent-200.json")
    assert plan.training_seeds == (7, 17, 27) and plan.map_seeds == (100, 101, 102, 103)
    assert (grid.n_agents, attack.compromised_count, attack.requested_deposit,
            attack.per_step_budget, attack.episode_budget, attack.start_step,
            attack.mode) == (4, 1, 1.0, 1.0, 200.0, 0, "persistent")


def test_repository_delayed_followup_changes_only_the_predeclared_attack_onset():
    """The timing follow-up keeps the same local four-agent 200-unit attack contract."""
    root = Path(__file__).resolve().parents[1]
    plan, _, _, grid, _, attack = load_phase2b_plan(
        root / "configs/phase2b/attack-calibration-persistent-delayed-200.json")
    assert plan.attack_start_step == attack.start_step == 200
    assert (grid.n_agents, attack.compromised_count, attack.requested_deposit,
            attack.per_step_budget, attack.episode_budget, attack.mode) == (4, 1, 1.0, 1.0, 200.0, "persistent")


def test_phase2b_runner_preserves_matched_controls_and_whole_groups(phase2b_plan, tmp_path):
    """A genuine local PPO rollout records one indivisible clean/control/attack family."""
    _, plan_path = phase2b_plan
    output = tmp_path / "output"
    summary = run_phase2b_attack_calibration(plan_path, output)
    assert summary["development_only"] and summary["group_count"] == 1 and summary["episode_count"] == 3
    manifest = json.loads((output / "manifest.json").read_text())
    splits = json.loads((output / "group_splits.json").read_text())
    assert manifest["status"] == "completed" and len(manifest["groups"]) == len(splits["assignments"]) == 1
    group = manifest["groups"][0]
    assert group["split"] == "development" and group["scenarios"] == ["clean", "injection_disabled", "attacked"]
    group_dir = output / "episodes" / group["group_id"]
    clean = json.loads((group_dir / "clean" / "episode.json").read_text())
    disabled = json.loads((group_dir / "injection_disabled" / "episode.json").read_text())
    attacked = json.loads((group_dir / "attacked" / "episode.json").read_text())
    assert clean["metrics"]["local_record_sha256"] == disabled["metrics"]["local_record_sha256"]
    assert (disabled["simulator_metadata"]["compromised_agents"] ==
            attacked["simulator_metadata"]["compromised_agents"])
    assert attacked["metrics"]["applied_mass"] <= 20.0
    first_record = json.loads((group_dir / "attacked" / "steps.jsonl").read_text().splitlines()[0])
    assert "compromised_agents" not in first_record["local"]
    assert "attack_events" in first_record["simulator_metadata"]


def test_phase2b_rejects_a_changed_attack_contract_before_writing_output(phase2b_plan, tmp_path):
    """Changing the declared minority fraction cannot silently create a new experiment."""
    root, plan_path = phase2b_plan
    raw = json.loads(plan_path.read_text())
    _write_json(root / raw["attack_config_path"], AttackConfig(compromised_count=2).as_dict())
    with pytest.raises(ValueError, match="four-agent bounded persistent-attack contract"):
        run_phase2b_attack_calibration(plan_path, tmp_path / "must-not-exist")
    assert not (tmp_path / "must-not-exist").exists()


def test_phase2b_rejects_an_attack_onset_that_the_plan_did_not_declare(phase2b_plan, tmp_path):
    """Timing is experiment provenance, so config and plan must agree before output exists."""
    root, plan_path = phase2b_plan
    raw = json.loads(plan_path.read_text())
    _write_json(root / raw["attack_config_path"], AttackConfig(start_step=1).as_dict())
    with pytest.raises(ValueError, match="four-agent bounded persistent-attack contract"):
        run_phase2b_attack_calibration(plan_path, tmp_path / "must-not-exist")
    assert not (tmp_path / "must-not-exist").exists()


@pytest.mark.parametrize("kwargs", [{"action_mode": "deterministic"}, {"action_seeds": [7, 7]},
                                    {"checkpoint_template": "/outside/policy-{seed}.zip"}])
def test_phase2b_plan_rejects_noncontract_inputs(kwargs):
    """The public plan schema permits only reviewable development calibration inputs."""
    with pytest.raises(ValueError):
        Phase2BAttackCalibrationPlan(**kwargs)
