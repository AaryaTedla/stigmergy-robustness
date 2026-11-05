"""Unit contracts for the local-only Phase 2A pheromone exposure summary.

These tests use synthetic 58-value observations, not PPO or global simulator
state.  They prove that the diagnostic counts only the documented food/home
channels, computes bounded local fractions, and rejects malformed input before
any experiment relies on it.
"""

import numpy as np
import pytest

from stigmergy.exposure import LocalPheromoneExposure
from stigmergy.observations import OBSERVATION_SIZE, PHEROMONE_INDICES


def test_exposure_counts_only_rows_with_visible_pheromone():
    """Food/home values in either local channel make exactly that row visible."""
    observations = np.zeros((3, OBSERVATION_SIZE), dtype=np.float32)
    observations[1, PHEROMONE_INDICES[0]] = 0.5  # First cell's food channel.
    observations[2, PHEROMONE_INDICES[3]] = 0.25  # Second cell's home channel.
    report = LocalPheromoneExposure()
    report.update(observations)
    summary = report.summary()
    assert summary["agent_observations"] == 3
    assert summary["visible_agent_observations"] == 2
    assert summary["visible_fraction"] == pytest.approx(2 / 3)
    assert summary["food_visible_agent_observations"] == 1
    assert summary["food_visible_fraction"] == pytest.approx(1 / 3)
    assert summary["home_visible_agent_observations"] == 1
    assert summary["home_visible_fraction"] == pytest.approx(1 / 3)
    assert summary["mean_food_value"] == pytest.approx(0.5 / 27)
    assert summary["mean_home_value"] == pytest.approx(0.25 / 27)
    assert summary["maximum_value"] == pytest.approx(0.5)


def test_exposure_reset_and_invalid_rows_are_safe():
    """A reused report clears data and malformed local observations are rejected."""
    report = LocalPheromoneExposure()
    report.update(np.zeros(OBSERVATION_SIZE, dtype=np.float32))
    report.reset()
    assert report.summary() == {
        "agent_observations": 0, "visible_agent_observations": 0,
        "visible_fraction": 0.0, "food_visible_agent_observations": 0,
        "food_visible_fraction": 0.0, "home_visible_agent_observations": 0,
        "home_visible_fraction": 0.0, "mean_food_value": 0.0,
        "mean_home_value": 0.0, "maximum_value": 0.0,
    }
    with pytest.raises(ValueError, match="final dimension"):
        report.update(np.zeros(OBSERVATION_SIZE - 1, dtype=np.float32))
    with pytest.raises(ValueError, match="finite"):
        report.update(np.full(OBSERVATION_SIZE, np.nan, dtype=np.float32))
