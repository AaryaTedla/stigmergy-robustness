"""Focused checks for the local-history feature interface and timeout baseline.

Run with ``python -m pytest tests/test_defense.py``. These unit tests use small
synthetic observations with the environment's documented 3x3x6 layout. They
verify bounded/local inputs, temporal updates, own-action revisitation, timer
resets, and locally legal choices; they are not attack or policy evaluations.
"""

import numpy as np
import pytest

from stigmergy.defense import FEATURE_NAMES, LocalHistoryFeatures, LocalTimeoutDefense


def observation():
    """Make an all-zero 58-value observation in the environment convention."""
    return np.zeros(58, dtype=np.float32)


def test_feature_order_bounds_events_and_pheromone_delta():
    history = LocalHistoryFeatures(progress_horizon=4)
    first = observation()
    a = history.update(first)
    second = first.copy()
    second[4 * 6 + 2] = 0.8  # center food field
    second[54] = 1  # carrying
    second[55] = 1  # picked up
    b = history.update(second, previous_action=0)
    assert len(FEATURE_NAMES) == len(a) == len(b) == 12
    assert a.dtype == np.float32 and b.dtype == np.float32
    assert b[0] > a[0] and b[4] > 0
    assert a[10] == 0 and b[6] == 1 and b[7] == 1 and b[10] == 0
    assert np.all(np.isfinite(b)) and np.all((b >= -1) & (b <= 1))


def test_revisitation_uses_only_own_actions_and_reset_clears_history():
    history = LocalHistoryFeatures()
    obs = observation()
    history.update(obs)
    history.update(obs, previous_action=2)
    repeated = history.update(obs, previous_action=4)
    assert repeated[11] > 0
    history.reset()
    reset = history.update(obs)
    assert reset[11] == 0 and reset[10] == 0


@pytest.mark.parametrize("bad", [np.zeros(57), np.full(58, np.nan), np.full(58, 2)])
def test_history_rejects_invalid_observation(bad):
    with pytest.raises(ValueError):
        LocalHistoryFeatures().update(bad)


def test_timeout_passthrough_visible_goal_and_progress_reset():
    defense = LocalTimeoutDefense(timeout=2)
    obs = observation()
    assert defense.select_action(obs, 3) == 3
    obs[1 * 6] = 1  # food-present channel in north neighbor
    assert defense.select_action(obs, 0) == 0
    assert defense.select_action(obs, 0) == 1
    progress = obs.copy()
    progress[55] = 1
    assert defense.select_action(progress, 4) == 4  # timer reset, pass through


def test_timeout_uses_nest_when_carrying_and_avoids_boundary():
    defense = LocalTimeoutDefense(timeout=1)
    obs = observation()
    obs[54] = 1
    obs[1 * 6 + 1] = 1  # north neighbor is a nest cell
    obs[1 * 6 + 5] = 1  # north neighbor's boundary channel blocks it
    obs[5 * 6 + 1] = 1  # east neighbor is a nest cell and locally legal
    assert defense.select_action(obs, 0) == 0  # initial observation has no elapsed step
    assert defense.select_action(obs, 0) == 2


def test_invalid_timeout_parameters_and_actions():
    with pytest.raises(ValueError):
        LocalTimeoutDefense(timeout=0)
    with pytest.raises(ValueError):
        LocalTimeoutDefense().select_action(observation(), True)
