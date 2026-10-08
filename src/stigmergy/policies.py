"""Seeded local-observation controller for debugging, not learned evidence.

LocalDebugPolicy receives a single 58-value float observation: a row-major
3x3x6 patch followed by carrying/pickup/delivery/blocked flags. Channels are
food, nest, normalized food/home fields, occupancy, and boundary. It chooses
an adjacent visible task landmark first, then sometimes explores or follows
the largest relevant pheromone value. It never receives environment state,
absolute coordinates, agent IDs, attacker labels or a global resource map.

Create one seeded controller per agent, then call act(observation). Its NumPy
RNG resolves ties and exploration reproducibly. Movement actions 1..4 mean
north/east/south/west; 0 is stay. This heuristic helps inspect local interfaces,
but is neither PPO nor evidence that learned pheromone coordination works.
"""

import numpy as np

MOVES = ((0, 0), (-1, 0), (0, 1), (1, 0), (0, -1))


def local_patch(observation):
    """Validate/copy one normalized observation and return its patch and state."""
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (58,) or not np.isfinite(obs).all() or np.any((obs < 0) | (obs > 1)):
        raise ValueError("observation must be 58 finite values in [0, 1]")
    return obs[:54].reshape(3, 3, 6), obs[54:]


class LocalDebugPolicy:
    """Select legal local actions using a seeded heuristic and exploration rate."""

    def __init__(self, seed=0, exploration=0.2):
        if isinstance(exploration, bool) or not np.isfinite(exploration) or not 0 <= exploration <= 1:
            raise ValueError("exploration must be finite in [0, 1]")
        self.rng = np.random.default_rng(seed)
        self.exploration = exploration

    def act(self, observation):
        """Return one integer action using only the supplied local observation."""
        patch, state = local_patch(observation)
        carrying = bool(state[0])
        goal_channel = 1 if carrying else 0
        if patch[1, 1, goal_channel]:
            return 0  # Useful for a stationary pickup/delivery fixture.
        legal = [a for a, (dr, dc) in enumerate(MOVES[1:], 1)
                 if not patch[1 + dr, 1 + dc, 5]]
        if not legal:
            return 0
        goals = [a for a in legal if patch[1 + MOVES[a][0], 1 + MOVES[a][1], goal_channel]]
        if goals:
            return int(self.rng.choice(goals))
        if self.rng.random() < self.exploration:
            return int(self.rng.choice(legal))
        field_channel = 3 if carrying else 2
        values = np.array([patch[1 + MOVES[a][0], 1 + MOVES[a][1], field_channel] for a in legal])
        best = [a for a, value in zip(legal, values) if value == values.max()]
        return int(self.rng.choice(best))
