"""Unit contracts for the local Phase 2A action-sensitivity aggregation.

These synthetic probability rows prove the report's math and validation without
loading a PPO checkpoint or reading simulator-global state.  Integration with
Stable-Baselines3 is exercised only by the explicit diagnostic script.
"""

import numpy as np
import pytest

from stigmergy.action_sensitivity import LocalActionSensitivity


def test_action_sensitivity_reports_all_and_visible_row_differences():
    """Total variation and greedy-action changes are aggregated without traces."""
    report = LocalActionSensitivity()
    report.update(
        [[0.8, 0.2], [0.1, 0.9]],
        [[0.2, 0.8], [0.1, 0.9]],
        [True, False],
    )
    summary = report.summary()
    assert summary["agent_observations"] == 2
    assert summary["visible_agent_observations"] == 1
    assert summary["visible_fraction"] == 0.5
    assert summary["mean_total_variation"] == pytest.approx(0.3)
    assert summary["visible_mean_total_variation"] == pytest.approx(0.6)
    assert summary["argmax_changed_fraction"] == 0.5
    assert summary["visible_argmax_changed_fraction"] == 1.0
    assert summary["action_count"] == 2


def test_action_sensitivity_rejects_malformed_probability_rows():
    """Bad shapes, normalization and visibility masks cannot silently skew evidence."""
    report = LocalActionSensitivity()
    with pytest.raises(ValueError, match="sum to one"):
        report.update([[0.2, 0.2]], [[0.5, 0.5]], [True])
    with pytest.raises(ValueError, match="leading dimensions"):
        report.update([[0.5, 0.5]], [[0.5, 0.5]], [[True]])
    with pytest.raises(ValueError, match="same action count"):
        report.update([[0.5, 0.5]], [[0.5, 0.5]], [True])
        report.update([[1.0]], [[1.0]], [True])
