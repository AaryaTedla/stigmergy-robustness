"""Local heuristic input/legality and reproducibility checks.

Run python -m pytest tests/test_policies.py with the simulator dependencies.
Synthetic patches isolate visible landmarks and boundaries; a seeded simulator
rollout checks controllers receive only local observations and reproduce their
actions/deliveries. These checks are debugging evidence, not learned results.
"""

import numpy as np
import pytest

from stigmergy import GridConfig, ResourceRetrievalEnv
from stigmergy.policies import LocalDebugPolicy


def test_local_landmarks_and_boundaries():
    obs = np.zeros(58, dtype=np.float32)
    patch = obs[:54].reshape(3, 3, 6)
    patch[0, 1, 0] = 1
    assert LocalDebugPolicy().act(obs) == 1
    patch[0, 1, 5] = 1
    assert LocalDebugPolicy().act(obs) != 1
    obs[54] = 1
    patch[1, 2, 1] = 1
    assert LocalDebugPolicy().act(obs) == 2


def test_local_field_guidance():
    obs = np.zeros(58, dtype=np.float32)
    obs[:54].reshape(3, 3, 6)[1, 2, 2] = 0.9
    assert LocalDebugPolicy(exploration=0).act(obs) == 2


def test_local_controller_seeded_rollout():
    histories = []
    for _ in range(2):
        env = ResourceRetrievalEnv(GridConfig(horizon=20))
        obs, _ = env.reset(seed=7)
        controllers = {a: LocalDebugPolicy(seed=i) for i, a in enumerate(env.agents)}
        history = []
        while env.agents:
            actions = {a: controllers[a].act(obs[a]) for a in env.agents}
            obs, rewards, _, _, _ = env.step(actions)
            history.append((actions, rewards))
        histories.append(history)
    assert histories[0] == histories[1]


def test_debug_controller_rejects_global_or_nonfinite_inputs():
    for obs in (np.zeros((8, 8)), np.full(58, np.nan)):
        with pytest.raises(ValueError):
            LocalDebugPolicy().act(obs)
