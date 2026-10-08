"""Shared PPO adapter and executable pipeline checks, not performance evidence.

Run python -m pytest tests/test_training.py after installing the training lock.
This module skips if the optional SB3 stack is absent. Direct simulator
equivalence, terminal/truncated observations, explicit map cycling and invalid
batch checks protect the adapter. Tiny repeated training runs check finite
parameter updates, exact same-stack repeatability, shared-row predictions,
checkpoint loading, failure preservation and disjoint development seeds.
Simulator arrays are mutated only in a clearly isolated termination fixture.
"""

from dataclasses import asdict
import json

import numpy as np
import pytest

pytest.importorskip("stable_baselines3")
from stable_baselines3 import PPO

from stigmergy import GridConfig, ResourceRetrievalEnv
from stigmergy.ppo_adapter import SharedGridVecEnv
from stigmergy.training import TrainingConfig, run_training


def test_adapter_matches_direct_parallel_transitions():
    config = GridConfig(n_agents=4, horizon=10)
    direct = ResourceRetrievalEnv(config)
    expected, _ = direct.reset(seed=7)
    adapter = SharedGridVecEnv(config, [7])
    np.testing.assert_array_equal(adapter.reset(), np.stack(list(expected.values())))
    for actions in ([1, 2, 3, 4], [2, 2, 0, 4], [0, 0, 0, 0]):
        obs, rewards, terms, truncs, _ = direct.step(dict(zip(direct.agents, actions)))
        batch, got_rewards, done, infos = adapter.step(np.array(actions))
        np.testing.assert_array_equal(batch, np.stack(list(obs.values())))
        np.testing.assert_array_equal(got_rewards, list(rewards.values()))
        np.testing.assert_array_equal(done, [terms[a] or truncs[a] for a in obs])
        assert all(set(info) == {"picked_up", "delivered", "blocked", "TimeLimit.truncated"} for info in infos)


def test_timeout_preserves_final_observations_and_auto_resets_all_slots():
    adapter = SharedGridVecEnv(GridConfig(horizon=1), [7, 8])
    initial = adapter.reset()
    next_obs, _, done, infos = adapter.step(np.array([2, 3]))
    assert done.all() and adapter.current_map_seed == 8 and adapter.world.steps == 0
    assert all(info["TimeLimit.truncated"] for info in infos)
    assert all(info["terminal_observation"].shape == (58,) for info in infos)
    assert not np.array_equal(infos[0]["terminal_observation"], initial[0])
    infos[0]["terminal_observation"].fill(1)
    assert not np.all(next_obs[0] == 1)  # terminal copies do not alias reset rows


def test_true_termination_is_not_timeout():
    adapter = SharedGridVecEnv(GridConfig(horizon=1), [7])
    adapter.reset()
    adapter.world.food.fill(0)  # simulator-only completion fixture
    _, _, done, infos = adapter.step(np.array([0, 0]))
    assert done.all() and all(not info["TimeLimit.truncated"] for info in infos)


def test_map_schedule_and_invalid_batches():
    adapter = SharedGridVecEnv(GridConfig(horizon=1), [7, 8])
    adapter.seed(2)
    adapter.reset()
    assert adapter.current_map_seed == 7
    for invalid in ([0], [True, False], [0, 5], [1.0, 2.0]):
        with pytest.raises(ValueError):
            adapter.step_async(invalid)
    assert adapter.world.steps == 0
    adapter.step_async(np.array([0, 0]))
    with pytest.raises(RuntimeError):
        adapter.step_async(np.array([0, 0]))
    adapter.step_wait()
    assert adapter.current_map_seed == 8
    with pytest.raises(RuntimeError):
        adapter.step_wait()


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"n_steps": 1}, {"gamma": float("nan")},
                                    {"diagnostic_map_seeds": [1]}, {"train_map_seeds": [1, 1]}])
def test_invalid_training_configuration(kwargs):
    with pytest.raises(ValueError):
        TrainingConfig(**kwargs)


def small_configs(tmp_path):
    """Save minimal valid development configs for inexpensive update checks."""
    grid = tmp_path / "grid.json"
    policy = tmp_path / "policy.json"
    grid.write_text(json.dumps(asdict(GridConfig(horizon=8))))
    policy.write_text(json.dumps(asdict(TrainingConfig(total_transitions=33, n_steps=8,
        batch_size=8, n_epochs=1, train_map_seeds=(1,), diagnostic_map_seeds=(2,)))))
    return grid, policy


def test_real_shared_ppo_updates_repeat_and_checkpoint_roundtrips(tmp_path):
    grid, config = small_configs(tmp_path)
    first = run_training(grid, config, tmp_path / "first")
    second = run_training(grid, config, tmp_path / "second")
    assert first == second
    assert first["requested_agent_transitions"] == 33
    assert first["actual_agent_transitions"] == 48  # full 16-transition rollouts
    assert first["world_steps"] == 24
    assert first["parameters_changed"] and first["checkpoint_roundtrip"]
    model = PPO.load(tmp_path / "first" / "policy.zip", device="cpu")
    observations = np.zeros((2, 58), dtype=np.float32)
    actions, _ = model.predict(observations, deterministic=True)
    assert actions[0] == actions[1]  # identical local rows use the same network
    assert (tmp_path / "first" / "progress.csv").is_file()
    with pytest.raises(FileExistsError):
        run_training(grid, config, tmp_path / "first")


def test_failed_training_preserves_manifest_and_initial_checkpoint(tmp_path, monkeypatch):
    grid, config = small_configs(tmp_path)

    def failed_learn(*args, **kwargs):
        raise RuntimeError("deliberate pipeline failure fixture")

    monkeypatch.setattr(PPO, "learn", failed_learn)
    with pytest.raises(RuntimeError, match="deliberate"):
        run_training(grid, config, tmp_path / "failed")
    manifest = json.loads((tmp_path / "failed" / "manifest.json").read_text())
    assert manifest["status"] == "failed" and "deliberate" in manifest["error"]
    assert (tmp_path / "failed" / "initial.zip").is_file()


def test_interrupted_training_is_incomplete_and_not_comparable(tmp_path, monkeypatch):
    """Budget SIGINT retains provenance/initial weights without a final checkpoint."""
    grid, config = small_configs(tmp_path)

    def interrupted_learn(*args, **kwargs):
        raise KeyboardInterrupt("budget fixture")

    monkeypatch.setattr(PPO, "learn", interrupted_learn)
    with pytest.raises(KeyboardInterrupt):
        run_training(grid, config, tmp_path / "interrupted")
    manifest = json.loads((tmp_path / "interrupted/manifest.json").read_text())
    assert manifest["status"] == "incomplete"
    assert (tmp_path / "interrupted/initial.zip").is_file()
    assert not (tmp_path / "interrupted/policy.zip").exists()
    assert not (tmp_path / "interrupted/summary.json").exists()
