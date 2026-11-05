"""Local-observation transforms used for controlled policy comparisons.

The simulator emits a 58-value local observation: a 3-by-3 patch with six
channels per cell followed by four own-state values. This module transforms
only a copied policy input, never simulator state or the environment's public
observation. It provides a fair ``no_pheromone`` baseline: a separately trained
model keeps local food, nest, occupancy, boundaries and own progress, but has
both pheromone channels zeroed during training and evaluation.

``apply_observation_mode`` accepts one observation or a batch with final
dimension 58 and returns a float32 copy of the same shape. It neither exposes
attack labels/global state/identity nor changes the observation interface.
"""

import numpy as np


OBSERVATION_SIZE = 58
OBSERVATION_MODES = ("full", "no_pheromone")

# The 3x3 patch is row-major with six values per cell. Channels 2 and 3 hold
# normalized food and home pheromone respectively.
PHEROMONE_INDICES = tuple(cell * 6 + channel for cell in range(9) for channel in (2, 3))


def apply_observation_mode(observations, mode="full"):
    """Copy observations and apply one declared policy-input mode.

    ``full`` preserves all local values. ``no_pheromone`` zeros exactly the 18
    food/home field values in the patch while retaining all non-pheromone data.
    Leading dimensions can represent agents or time steps.
    """
    if mode not in OBSERVATION_MODES:
        raise ValueError(f"mode must be one of {OBSERVATION_MODES}")
    values = np.asarray(observations, dtype=np.float32)
    if values.ndim < 1 or values.shape[-1] != OBSERVATION_SIZE:
        raise ValueError(f"observations must have final dimension {OBSERVATION_SIZE}")
    if not np.isfinite(values).all():
        raise ValueError("observations must be finite")
    transformed = values.copy()
    if mode == "no_pheromone":
        transformed[..., PHEROMONE_INDICES] = 0
    return transformed
