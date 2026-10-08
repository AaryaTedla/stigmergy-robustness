"""Protect the frozen-policy sensitivity diagnostic's observation boundary.

The review script is imported as a module without running its CLI. A synthetic
58-value local batch verifies that ablation changes exactly the two pheromone
channels, preserves own progress/boundaries/food/nest/occupancy, and never
mutates the original. This is a diagnostic integrity check, not performance.
"""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip('stable_baselines3')
spec = importlib.util.spec_from_file_location('review_evidence', Path('scripts/review_evidence.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_ablation_changes_only_pheromone_and_copies():
    """Local state/progress remain accessible; no privileged input is introduced."""
    rows = np.ones((8,58), dtype=np.float32)
    result = module.zero_pheromone_rows(rows)
    mask = np.zeros(58,dtype=bool)
    mask[:54].reshape(3,3,6)[:,:,2:4] = True
    assert np.all(result[:,mask] == 0)
    assert np.all(result[:,~mask] == 1)
    assert np.all(rows == 1)
    with pytest.raises(ValueError):
        module.zero_pheromone_rows(np.ones((8,59)))
