"""Focused contracts for Phase 2A planning and random-action diagnostics.

Run with ``python -m pytest -q tests/test_calibration.py`` after installing the
core simulator dependencies. These checks validate only reproducible planning
and random-reference accounting. They never invoke the 18 PPO training jobs or
make a calibration-result claim.
"""

from pathlib import Path
import json
import sys
import types

from stigmergy import GridConfig
from stigmergy.calibration import _load_plan, evaluate_random_actions, run_phase2a_calibration


def test_repository_phase2a_plan_resolves_to_the_declared_eighteen_ppo_runs():
    """The checked-in plan retains every candidate, seed, and input mode."""
    root = Path(__file__).resolve().parents[1]
    plan, _, candidates, modes, seeds = _load_plan(root / "configs/phase2a/calibration.json")
    assert plan["purpose"] == "development_only_phase2a_calibration"
    assert len(candidates) == 3 and modes == ("full", "no_pheromone") and seeds == (7, 17, 27)
    assert len(candidates) * len(modes) * len(seeds) == 18


def test_simple_repeat_followup_plan_keeps_the_fair_three_seed_comparison():
    """The small follow-up changes only environments, not the baseline contract."""
    root = Path(__file__).resolve().parents[1]
    plan, _, candidates, modes, seeds = _load_plan(root / "configs/phase2a/calibration-simple-repeat.json")
    assert plan["purpose"] == "development_only_phase2a_calibration"
    assert [candidate[0] for candidate in candidates] == ["candidate_d_10x10_repeat", "candidate_e_12x12_repeat"]
    assert modes == ("full", "no_pheromone") and seeds == (7, 17, 27)
    assert len(candidates) * len(modes) * len(seeds) == 12


def test_slow_evaporation_plan_changes_only_one_declared_environment_candidate():
    """The follow-up retains the three seeds and fair modes for one small mechanics test."""
    root = Path(__file__).resolve().parents[1]
    plan, _, candidates, modes, seeds = _load_plan(root / "configs/phase2a/calibration-slow-evaporation.json")
    assert plan["purpose"] == "development_only_phase2a_calibration"
    assert [candidate[0] for candidate in candidates] == ["candidate_f_12x12_slow_evaporation"]
    assert candidates[0][2].evaporation == 0.02
    assert modes == ("full", "no_pheromone") and seeds == (7, 17, 27)
    assert len(candidates) * len(modes) * len(seeds) == 6


def test_scout_follow_plan_keeps_the_fair_comparison_and_declares_its_layout():
    """Candidate G is a small coordination task, not a baseline or protocol change."""
    root = Path(__file__).resolve().parents[1]
    plan, _, candidates, modes, seeds = _load_plan(root / "configs/phase2a/calibration-scout-follow.json")
    assert plan["purpose"] == "development_only_phase2a_calibration"
    assert [candidate[0] for candidate in candidates] == ["candidate_g_12x12_scout_follow"]
    grid = candidates[0][2]
    assert (grid.n_agents, grid.food_layout, grid.food_per_patch, grid.horizon, grid.evaporation) == (
        4, "distant_cluster", 30, 1100, 0.02)
    assert modes == ("full", "no_pheromone") and seeds == (7, 17, 27)
    assert len(candidates) * len(modes) * len(seeds) == 6


def test_scout_follow_deadline_plan_changes_only_the_declared_horizon():
    """Candidate H keeps the useful G structure while testing delivery under a deadline."""
    root = Path(__file__).resolve().parents[1]
    _, _, candidates, modes, seeds = _load_plan(root / "configs/phase2a/calibration-scout-follow-deadline.json")
    grid = candidates[0][2]
    assert candidates[0][0] == "candidate_h_12x12_scout_follow_deadline"
    assert (grid.size, grid.n_agents, grid.horizon, grid.food_per_patch, grid.evaporation, grid.food_layout) == (
        12, 4, 700, 30, 0.02, "distant_cluster")
    assert modes == ("full", "no_pheromone") and seeds == (7, 17, 27)


def test_scout_follow_stability_plan_changes_only_the_fair_training_budget():
    """Candidate I keeps Candidate H's task and gives both modes equal extra learning time."""
    root = Path(__file__).resolve().parents[1]
    plan, _, candidates, modes, seeds = _load_plan(root / "configs/phase2a/calibration-scout-follow-stability.json")
    assert [candidate[0] for candidate in candidates] == ["candidate_h_12x12_scout_follow_deadline"]
    assert candidates[0][2].horizon == 700 and modes == ("full", "no_pheromone") and seeds == (7, 17, 27)
    for mode in modes:
        for seed in seeds:
            policy = json.loads((root / plan["policy_config_template"].format(mode=mode, seed=seed)).read_text())
            assert policy["total_transitions"] == 600000 and policy["observation_mode"] == mode


def test_scout_follow_capacity_plan_changes_only_candidate_g_food_capacity():
    """Candidate J removes G's delivery ceiling without repeating the failed deadline task."""
    root = Path(__file__).resolve().parents[1]
    plan, _, candidates, modes, seeds = _load_plan(root / "configs/phase2a/calibration-scout-follow-capacity.json")
    grid = candidates[0][2]
    assert plan["purpose"] == "development_only_phase2a_calibration"
    assert candidates[0][0] == "candidate_j_12x12_scout_follow_capacity"
    assert (grid.size, grid.n_agents, grid.horizon, grid.food_per_patch, grid.evaporation, grid.food_layout) == (
        12, 4, 1100, 50, 0.02, "distant_cluster")
    assert modes == ("full", "no_pheromone") and seeds == (7, 17, 27)
    assert len(candidates) * len(modes) * len(seeds) == 6


def test_random_action_baseline_is_seeded_and_reports_episode_outcomes():
    """The common reference has stable action randomness and no policy inputs."""
    grid = GridConfig(size=8, n_agents=2, horizon=12, food_per_patch=1)
    first = evaluate_random_actions(grid, (100, 101), action_seed=7)
    second = evaluate_random_actions(grid, (100, 101), action_seed=7)
    assert first == second and len(first["episodes"]) == 2
    assert 0 <= first["completed_rate"] <= 1
    assert all(0 <= episode["delivered"] <= 2 for episode in first["episodes"])


def test_calibration_runner_keeps_all_declared_mocked_training_rows(tmp_path, monkeypatch):
    """The aggregator emits all PPO/random rows and never chooses a winner itself."""
    project = Path(__file__).resolve().parents[1]
    source_plan = json.loads((project / "configs/phase2a/calibration.json").read_text())
    plan_root = tmp_path / "project"
    for relative in source_plan["environment_candidates"]:
        source = project / relative
        target = plan_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text())
    template = source_plan["policy_config_template"]
    for mode in source_plan["observation_modes"]:
        for seed in source_plan["training_seeds"]:
            relative = template.format(mode=mode, seed=seed)
            target = plan_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text((project / relative).read_text())
    plan_path = plan_root / "configs/phase2a/calibration.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(source_plan))

    def fake_training(grid_path, policy_path, output):
        """Supply tiny completed diagnostics without importing the optional PPO stack."""
        output.mkdir(parents=True)
        mode = json.loads(Path(policy_path).read_text())["observation_mode"]
        delivered = 100 if mode == "full" else 1
        episode = {"map_seed": 100, "steps": 1, "delivered": delivered, "completed": True}
        return {"after": {"deterministic": {"mean_delivered": delivered, "episodes": [episode]},
                          "stochastic": {"mean_delivered": delivered, "episodes": [episode]}},
                "actual_agent_transitions": 8}

    fake_module = types.ModuleType("stigmergy.training")
    fake_module.run_training = fake_training
    monkeypatch.setitem(sys.modules, "stigmergy.training", fake_module)
    summary = run_phase2a_calibration(plan_path, tmp_path / "output")
    assert summary["automatic_selection"] is False
    assert summary["run_rows"] == 27 and summary["paired_rows"] == 9
    assert len(summary["candidate_advances_by_stochastic_development_gate"]) == 3
    assert (tmp_path / "output/runs.csv").is_file() and (tmp_path / "output/paired.csv").is_file()


def test_calibration_runner_resumes_only_missing_mocked_training_rows(tmp_path, monkeypatch):
    """A signal-left manifest reuses completed rows and preserves a partial directory.

    This models the operational case where a process died during the first
    Candidate C job: twelve earlier jobs are already manifest-backed, while the
    canonical Candidate C output exists without a root-manifest row.  Resuming
    must leave that partial directory intact and use a fresh sibling output.
    """
    project = Path(__file__).resolve().parents[1]
    source_plan = json.loads((project / "configs/phase2a/calibration.json").read_text())
    plan_root = tmp_path / "project"
    for relative in source_plan["environment_candidates"]:
        source = project / relative
        target = plan_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text())
    template = source_plan["policy_config_template"]
    for mode in source_plan["observation_modes"]:
        for seed in source_plan["training_seeds"]:
            relative = template.format(mode=mode, seed=seed)
            target = plan_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text((project / relative).read_text())
    plan_path = plan_root / "configs/phase2a/calibration.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(source_plan))
    _, root, candidates, modes, seeds = _load_plan(plan_path)
    output = tmp_path / "output"
    output.mkdir()
    completed = []
    for candidate_id, grid_path, grid in candidates[:2]:
        for seed in seeds:
            for mode in modes:
                completed.append({"candidate_id": candidate_id, "training_seed": seed,
                                  "observation_mode": mode, "grid_config": grid.__dict__,
                                  "grid_config_path": str(grid_path.relative_to(root)),
                                  "policy_config_path": template.format(mode=mode, seed=seed),
                                  "output": f"{candidate_id}/{mode}-seed-{seed}", "status": "completed",
                                  "deterministic_mean_delivered": 2.0, "deterministic_completed_rate": 0.0,
                                  "deterministic_mean_steps": 1.0, "stochastic_mean_delivered": 2.0,
                                  "stochastic_completed_rate": 0.0, "stochastic_mean_steps": 1.0,
                                  "actual_agent_transitions": 8, "error": ""})
    plan_sha256 = __import__("hashlib").sha256(plan_path.read_bytes()).hexdigest()
    (output / "manifest.json").write_text(json.dumps({
        "status": "started", "purpose": source_plan["purpose"], "plan_sha256": plan_sha256,
        "ppo_run_count": 18, "random_baseline_count": 9, "runs": completed,
    }))
    partial = output / "candidate_c_16x16_dense" / "full-seed-7"
    partial.mkdir(parents=True)
    (partial / "progress.csv").write_text("partial\n")
    calls = []

    def fake_training(grid_path, policy_path, target):
        """Return a short completed diagnostic while recording fresh targets."""
        calls.append(Path(target))
        Path(target).mkdir(parents=True)
        episode = {"map_seed": 100, "steps": 1, "delivered": 3, "completed": False}
        return {"after": {"deterministic": {"mean_delivered": 3, "episodes": [episode]},
                          "stochastic": {"mean_delivered": 3, "episodes": [episode]}},
                "actual_agent_transitions": 8}

    fake_module = types.ModuleType("stigmergy.training")
    fake_module.run_training = fake_training
    monkeypatch.setitem(sys.modules, "stigmergy.training", fake_module)
    summary = run_phase2a_calibration(plan_path, output, resume=True)
    assert summary["run_rows"] == 27 and len(calls) == 6
    assert (partial / "progress.csv").is_file()
    assert calls[0].name == "full-seed-7-resume-1"
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "completed" and manifest["resume_count"] == 1


def test_calibration_runner_rebuilds_derived_reports_after_final_aggregation_failure(tmp_path, monkeypatch):
    """A failed report write is recoverable only when every immutable PPO row completed."""
    project = Path(__file__).resolve().parents[1]
    source_plan = json.loads((project / "configs/phase2a/calibration.json").read_text())
    plan_root = tmp_path / "project"
    for relative in source_plan["environment_candidates"]:
        source = project / relative
        target = plan_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text())
    template = source_plan["policy_config_template"]
    for mode in source_plan["observation_modes"]:
        for seed in source_plan["training_seeds"]:
            relative = template.format(mode=mode, seed=seed)
            target = plan_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text((project / relative).read_text())
    plan_path = plan_root / "configs/phase2a/calibration.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(source_plan))
    _, root, candidates, modes, seeds = _load_plan(plan_path)
    output = tmp_path / "output"
    output.mkdir()
    completed = []
    for candidate_id, grid_path, grid in candidates:
        for seed in seeds:
            for mode in modes:
                completed.append({"candidate_id": candidate_id, "training_seed": seed,
                                  "observation_mode": mode, "grid_config": grid.__dict__,
                                  "grid_config_path": str(grid_path.relative_to(root)),
                                  "policy_config_path": template.format(mode=mode, seed=seed),
                                  "output": f"{candidate_id}/{mode}-seed-{seed}", "status": "completed",
                                  "deterministic_mean_delivered": 2.0, "deterministic_completed_rate": 0.0,
                                  "deterministic_mean_steps": 1.0, "stochastic_mean_delivered": 2.0,
                                  "stochastic_completed_rate": 0.0, "stochastic_mean_steps": 1.0,
                                  "actual_agent_transitions": 8, "error": ""})
    plan_sha256 = __import__("hashlib").sha256(plan_path.read_bytes()).hexdigest()
    (output / "manifest.json").write_text(json.dumps({
        "status": "failed", "purpose": source_plan["purpose"], "plan_sha256": plan_sha256,
        "ppo_run_count": 18, "random_baseline_count": 9, "runs": completed,
        "error": "FileExistsError: derived report already exists",
    }))
    (output / "runs.csv").write_text("stale\n")
    (output / "paired.csv").write_text("stale\n")
    summary = run_phase2a_calibration(plan_path, output, resume=True)
    assert summary["run_rows"] == 27 and summary["paired_rows"] == 9
    assert (output / "runs.csv").read_text() != "stale\n"
    assert json.loads((output / "manifest.json").read_text())["status"] == "completed"
