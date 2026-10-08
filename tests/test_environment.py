"""Mechanics evidence for the clean simulator, not research performance tests.

Run `python -m pytest`. Fixtures use explicit food cells and controlled agent
positions to isolate movement, contention, food accounting, field evolution,
and observation locality. Seeded multi-step runs check exact repeatability.
PettingZoo's own parallel test checks the external multi-agent lifecycle.
The CLI fixture checks reproducible end-to-end delivery and saved artifacts.
"""

import json

import numpy as np
import pytest
from pettingzoo.test import parallel_api_test

from stigmergy import GridConfig, ResourceRetrievalEnv
from stigmergy.cli import run_demo


def fixture(**kwargs):
    env = ResourceRetrievalEnv(GridConfig(**kwargs))
    env.reset(seed=7, options={"food_positions": [(1, 3), (6, 6)]})
    return env


def stay(env):
    return {a: 0 for a in env.agents}


@pytest.mark.parametrize("kwargs", [{"size": 3}, {"n_agents": 0}, {"horizon": True},
    {"food_per_patch": 1.5}, {"deposit": -1}, {"deposit": 11},
    {"field_cap": 0}, {"evaporation": 1.1}, {"deposit": float("nan")}])
def test_invalid_config(kwargs):
    with pytest.raises(ValueError):
        GridConfig(**kwargs)


def test_boundaries_and_atomic_validation():
    env = fixture()
    before = env.positions.copy()
    with pytest.raises(ValueError):
        env.step({"agent_0": 2, "agent_1": 9})
    np.testing.assert_array_equal(env.positions, before)
    assert env.steps == 0
    with pytest.raises(ValueError):
        env.step({"agent_0": 0})
    _, _, _, _, infos = env.step({"agent_0": 1, "agent_1": 0})
    assert infos["agent_0"]["blocked"]
    np.testing.assert_array_equal(env.positions[0], [0, 0])


def test_swaps_and_colocation():
    env = fixture()
    env.step({"agent_0": 2, "agent_1": 4})
    np.testing.assert_array_equal(env.positions, [[0, 1], [0, 0]])
    env.step({"agent_0": 4, "agent_1": 0})
    np.testing.assert_array_equal(env.positions, [[0, 0], [0, 0]])


def test_pickup_delivery_and_conservation():
    env = fixture(food_per_patch=1)
    env.positions[:] = [(1, 3), (6, 6)]
    _, rewards, _, _, infos = env.step(stay(env))
    assert env.carrying.all() and env.food.sum() == 0
    assert all(i["picked_up"] for i in infos.values()) and sum(rewards.values()) == 0
    env.positions[:] = [(1, 1), (0, 0)]
    _, rewards, terms, truncs, _ = env.step(stay(env))
    assert env.delivered_total == 2 and not env.carrying.any()
    assert all(v == 2 for v in rewards.values())
    assert all(terms.values()) and not any(truncs.values()) and not env.agents
    assert env.step({}) == ({}, {}, {}, {}, {})


def test_pickup_contention_no_negative_food():
    env = fixture(food_per_patch=1)
    env.positions[:] = (1, 3)
    env.step(stay(env))
    assert env.carrying.sum() == 1 and env.food[1, 3] == 0
    assert env.food.sum() + env.carrying.sum() + env.delivered_total == 2


def test_deposit_cap_decay_and_channels():
    env = fixture(deposit=2, field_cap=3, evaporation=0.5)
    env.positions[:] = (1, 1)
    env.step(stay(env))
    assert env.fields[1, 1, 1] == 1.5
    assert env.fields[0].sum() == 0
    env.positions[:] = [(1, 3), (6, 6)]
    env.step(stay(env))
    assert env.fields[0, 1, 3] == 1 and env.fields[1, 1, 1] == 0.75
    assert np.isfinite(env.fields).all() and (env.fields >= 0).all()


def test_locality_and_observation_copy():
    env = fixture()
    before = env._observations()["agent_0"]
    env.food[6, 6] = 99
    env.fields[:, 7, 7] = 5
    after = env._observations()["agent_0"]
    np.testing.assert_array_equal(before, after)
    assert env.observation_space("agent_0").contains(after)
    assert after.reshape(-1)[:54].reshape(3, 3, 6)[0, 0, 5] == 1
    after[:] = 1
    assert not np.all(env._observations()["agent_0"] == 1)
    assert set(env._infos()["agent_0"]) == {"picked_up", "delivered", "blocked"}


def test_horizon_and_reset():
    env = fixture(horizon=1)
    _, _, terms, truncs, _ = env.step(stay(env))
    assert not any(terms.values()) and all(truncs.values()) and not env.agents
    env.reset(seed=7)
    assert len(env.agents) == 2 and env.steps == 0 and env.delivered_total == 0
    assert not env.fields.any()


@pytest.mark.parametrize("evaporation,expected", [(0, 1), (1, 0)])
def test_evaporation_endpoints(evaporation, expected):
    env = fixture(evaporation=evaporation)
    env.step(stay(env))
    assert env.fields[1, 0, 0] == expected


def test_completion_at_horizon_is_termination():
    env = fixture(food_per_patch=1, horizon=2)
    env.positions[:] = [(1, 3), (6, 6)]
    env.step(stay(env))
    env.positions[:] = (1, 1)
    _, _, terms, truncs, _ = env.step(stay(env))
    assert all(terms.values()) and not any(truncs.values())


def test_pilot_observations_and_generic_reset_options():
    env = ResourceRetrievalEnv(GridConfig(size=16, n_agents=8))
    obs, _ = env.reset(seed=7, options={"options": 1})
    assert len(obs) == 8 and env.food.sum() == 8
    assert all(env.observation_space(a).contains(v) for a, v in obs.items())


def test_seeded_rollout():
    envs = [ResourceRetrievalEnv(), ResourceRetrievalEnv()]
    for env in envs:
        env.reset(seed=42)
    rng = np.random.default_rng(4)
    for _ in range(100):
        actions = {a: int(rng.integers(5)) for a in envs[0].agents}
        outputs = [env.step(actions) for env in envs]
        for key in ("positions", "food", "fields", "carrying"):
            np.testing.assert_array_equal(getattr(envs[0], key), getattr(envs[1], key))
        for a in outputs[0][0]:
            np.testing.assert_array_equal(outputs[0][0][a], outputs[1][0][a])
        assert outputs[0][1:] == outputs[1][1:]
        assert envs[0].food.sum() + envs[0].carrying.sum() + envs[0].delivered_total == 8


def test_parallel_contract():
    parallel_api_test(ResourceRetrievalEnv(GridConfig(horizon=50)), num_cycles=100)


@pytest.mark.parametrize("patches", [[(0, 0), (3, 3)], [(3, 3), (3, 3)], [(1.0, 3), (6, 6)], None])
def test_invalid_fixture(patches):
    if patches is None:
        patches = [(99, 99), (3, 3)]
    with pytest.raises(ValueError):
        ResourceRetrievalEnv().reset(options={"food_positions": patches})


def test_demo_reproducibility(tmp_path):
    summaries = [run_demo("configs/env/development.json", 7, tmp_path / name) for name in ("a", "b")]
    assert summaries[0] == summaries[1]
    assert summaries[0]["completed"] and summaries[0]["delivered"] == 8
    assert (tmp_path / "a/snapshot.svg").read_bytes() == (tmp_path / "b/snapshot.svg").read_bytes()
    assert json.loads((tmp_path / "a/summary.json").read_text()) == summaries[0]


def test_nest_anchored_outbound_and_return():
    """Outbound deposits decay with movement age; returning resets the counter."""
    env = fixture(evaporation=0)
    env.positions[0] = (1, 1)
    env.step({"agent_0": 2, "agent_1": 0})
    assert env.steps_since_nest[0] == 1
    assert env.fields[1, 1, 2] == pytest.approx(.95)
    env.step({"agent_0": 3, "agent_1": 0})
    assert env.steps_since_nest[0] == 2
    assert env.fields[1, 2, 2] == pytest.approx(.95**2)
    env.step({"agent_0": 4, "agent_1": 0})
    env.step({"agent_0": 1, "agent_1": 0})
    assert env.steps_since_nest[0] == 0
    assert env.fields[1, 1, 1] == 1
    env.reset(seed=7)
    assert not env.steps_since_nest.any()


@pytest.mark.parametrize("action", [0, 1])
def test_outside_wait_or_block_only_evaporates(action):
    """Stationary/blocked outside agents cannot build home concentration."""
    env = fixture()
    env.positions[0] = (0, 3)
    env.fields[1, 0, 3] = 2
    env.step({"agent_0": action, "agent_1": 0})
    assert env.fields[1, 0, 3] == pytest.approx(1.8)
    assert env.steps_since_nest[0] == 0


def test_stationary_carrying_food_unchanged():
    """Food is deposited after pickup and still deposited while waiting loaded."""
    env = fixture()
    env.positions[0] = (1, 3)
    env.step(stay(env))
    assert env.fields[0, 1, 3] == pytest.approx(.9)
    env.step(stay(env))
    assert env.fields[0, 1, 3] == pytest.approx(1.71)
    assert env.fields[1, 1, 3] == 0


@pytest.mark.parametrize("value", [-.1, 1.1, True, float("nan")])
def test_invalid_home_decay(value):
    with pytest.raises(ValueError):
        GridConfig(home_decay=value)
