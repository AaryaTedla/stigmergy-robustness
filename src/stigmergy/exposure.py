"""Measure whether an agent can locally see pheromone during a PPO rollout.

Phase 2A needs to distinguish two different problems: a policy may receive
pheromone values but not use them well, or the shared field may rarely be in an
agent's small 3-by-3 view at all.  This module records the second fact without
changing the environment, the policy, rewards, or any model input.  It consumes
only the same 58-value local observation that a full PPO policy already sees.

The first 54 values are a 3-by-3 patch with six channels per cell.  Channels 2
and 3 are normalized food and home pheromone.  ``LocalPheromoneExposure`` sums
per-agent observations over an episode or a group of episodes and reports how
often either channel is nonzero plus simple local intensity summaries.  It does
not read global field arrays, food positions, attacker labels, or agent IDs.
That makes it suitable for a clean development diagnostic, but it is not a
detector feature or a Phase 2B dataset label.

Use ``update`` once for each observation batch before choosing actions, then
call ``summary``.  Batches must end in 58 values and can contain one agent or
many agents.  All reported field values are normalized local-observation units
(the simulator field divided by its cap), not raw simulator mass.
"""

from dataclasses import dataclass

import numpy as np

from .observations import OBSERVATION_SIZE, PHEROMONE_INDICES


@dataclass
class LocalPheromoneExposure:
    """Accumulate local pheromone visibility without storing trajectories.

    ``agent_observations`` counts rows supplied to the policy.  A row is
    ``visible`` when any of its 18 local food/home pheromone entries is greater
    than zero.  The mean values average all 18 entries over all rows, so they
    describe what a local policy could have seen rather than total global field
    mass.  Call ``reset`` before reusing one instance for another report.
    """

    agent_observations: int = 0
    visible_agent_observations: int = 0
    food_visible_agent_observations: int = 0
    home_visible_agent_observations: int = 0
    food_sum: float = 0.0
    home_sum: float = 0.0
    maximum_value: float = 0.0

    def reset(self):
        """Clear all accumulated local-only measurements."""
        self.agent_observations = 0
        self.visible_agent_observations = 0
        self.food_visible_agent_observations = 0
        self.home_visible_agent_observations = 0
        self.food_sum = 0.0
        self.home_sum = 0.0
        self.maximum_value = 0.0

    def update(self, observations):
        """Record one or more full local observations.

        Parameters
        ----------
        observations:
            Array-like rows ending in 58 float values.  Leading dimensions are
            flattened into independent agent observations.  The method rejects
            non-finite values and never changes the caller's array.
        """
        values = np.asarray(observations, dtype=np.float32)
        if values.ndim < 1 or values.shape[-1] != OBSERVATION_SIZE:
            raise ValueError(f"observations must have final dimension {OBSERVATION_SIZE}")
        if not np.isfinite(values).all():
            raise ValueError("observations must be finite")
        rows = values.reshape(-1, OBSERVATION_SIZE)
        pheromone = rows[:, PHEROMONE_INDICES].reshape(-1, 9, 2)
        # Channel order is fixed by the observation contract: food, then home.
        food = pheromone[:, :, 0]
        home = pheromone[:, :, 1]
        food_visible = np.any(food > 0, axis=1)
        home_visible = np.any(home > 0, axis=1)
        self.agent_observations += int(rows.shape[0])
        self.food_visible_agent_observations += int(np.count_nonzero(food_visible))
        self.home_visible_agent_observations += int(np.count_nonzero(home_visible))
        self.visible_agent_observations += int(np.count_nonzero(food_visible | home_visible))
        self.food_sum += float(food.sum())
        self.home_sum += float(home.sum())
        if pheromone.size:
            self.maximum_value = max(self.maximum_value, float(pheromone.max()))

    def summary(self):
        """Return JSON-safe local visibility and intensity statistics.

        Empty reports return zeros rather than NaN so interrupted or zero-step
        diagnostics remain easy to audit.  ``mean_food_value`` and
        ``mean_home_value`` average over every patch cell of every agent row.
        """
        cells = self.agent_observations * 9
        return {
            "agent_observations": self.agent_observations,
            "visible_agent_observations": self.visible_agent_observations,
            "visible_fraction": (self.visible_agent_observations / self.agent_observations
                                 if self.agent_observations else 0.0),
            "food_visible_agent_observations": self.food_visible_agent_observations,
            "food_visible_fraction": (self.food_visible_agent_observations / self.agent_observations
                                      if self.agent_observations else 0.0),
            "home_visible_agent_observations": self.home_visible_agent_observations,
            "home_visible_fraction": (self.home_visible_agent_observations / self.agent_observations
                                      if self.agent_observations else 0.0),
            "mean_food_value": self.food_sum / cells if cells else 0.0,
            "mean_home_value": self.home_sum / cells if cells else 0.0,
            "maximum_value": self.maximum_value,
        }
