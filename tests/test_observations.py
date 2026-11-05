"""Unit checks for Phase 2A's copied no-pheromone policy input mode.

Run with ``python -m pytest -q tests/test_observations.py`` after installing
the repository dependencies. These checks establish only shape preservation,
non-aliasing, and masking boundaries. They do not train PPO or establish a
pheromone-use result.
"""

import numpy as np
import pytest

from stigmergy.observations import OBSERVATION_MODES, PHEROMONE_INDICES, apply_observation_mode


def test_no_pheromone_masks_only_declared_local_field_channels_without_aliasing():
    """The baseline removes 18 field inputs but preserves all other local data."""
    source = np.arange(2 * 58, dtype=np.float32).reshape(2, 58)
    transformed = apply_observation_mode(source, "no_pheromone")
    assert transformed.shape == source.shape and transformed.dtype == np.float32
    assert np.array_equal(source, np.arange(2 * 58, dtype=np.float32).reshape(2, 58))
    assert np.all(transformed[:, PHEROMONE_INDICES] == 0)
    retained = [index for index in range(58) if index not in PHEROMONE_INDICES]
    np.testing.assert_array_equal(transformed[:, retained], source[:, retained])
    transformed[0, 0] = -1
    assert source[0, 0] == 0


def test_full_mode_returns_float32_copy_without_value_change():
    """Full PPO receives the documented observation unchanged, but copied."""
    source = np.linspace(0, 1, 58, dtype=np.float64)
    transformed = apply_observation_mode(source)
    np.testing.assert_array_equal(transformed, source.astype(np.float32))
    transformed[0] = 0.5
    assert source[0] == 0


@pytest.mark.parametrize("mode", ["masked", None, 1])
def test_invalid_modes_and_observation_shapes_are_rejected(mode):
    """Reject ambiguous baseline declarations before policy training starts."""
    if mode in OBSERVATION_MODES:
        pytest.skip("covered by valid-mode tests")
    with pytest.raises(ValueError):
        apply_observation_mode(np.zeros(58), mode)
    with pytest.raises(ValueError):
        apply_observation_mode(np.zeros(57), "full")
    with pytest.raises(ValueError):
        apply_observation_mode(np.full(58, np.nan), "full")
