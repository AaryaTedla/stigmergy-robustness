"""Local-history features and a rule-based timeout baseline.

This module is the first-review local-defense foundation. It consumes only one
agent's 58-value observation and (for path reconstruction) that agent's own
previous action. The observation contains a flattened 3x3 patch in row-major
order with six channels per cell, followed by carrying, pickup, delivery, and
blocked flags. Pheromone values are normalized to [0, 1]. The extractor emits
12 float32 features: local food/home field mean and maximum, step-to-step mean
changes, own task events, normalized time without progress, and a normalized
revisitation frequency. No simulator arrays, map coordinates, attacker labels,
or attack timing are inputs.

Call ``LocalHistoryFeatures.reset()`` at each episode, then ``update(obs,
previous_action)`` once per new observation. The optional previous action is
the action taken since the prior observation; pass None for the initial
observation. The timeout baseline wraps an already selected action. After a
configured number of steps without pickup or delivery, it chooses a locally
legal action toward visible food or cycles through legal movement actions.
This is a debugging/baseline heuristic, not a learned policy or a validated
attack defense. Its behavior is deterministic given observations and actions.
"""

from collections import Counter

import numpy as np


FEATURE_NAMES = (
    "food_field_mean", "food_field_max", "home_field_mean", "home_field_max",
    "food_field_mean_delta", "home_field_mean_delta", "carrying",
    "picked_up", "delivered", "blocked", "steps_without_progress",
    "revisit_fraction",
)
_MOVES = ((0, 0), (-1, 0), (0, 1), (1, 0), (0, -1))


class LocalHistoryFeatures:
    """Build bounded per-agent features from observations and own actions.

    ``update`` returns a float32 vector in ``FEATURE_NAMES`` order. A new
    instance or ``reset`` starts a fresh episode; callers must not share an
    instance between agents, since history is intentionally agent-local.
    """

    def __init__(self, progress_horizon=20):
        if isinstance(progress_horizon, bool) or not isinstance(progress_horizon, int) or progress_horizon < 1:
            raise ValueError("progress_horizon must be a positive integer")
        self.progress_horizon = progress_horizon
        self.reset()

    def reset(self):
        """Clear temporal state at an episode boundary."""
        self.previous_means = None
        self.position = np.zeros(2, dtype=np.int32)
        self.visits = Counter()
        self.observations = 0
        self.steps_without_progress = 0

    def update(self, observation, previous_action=None):
        """Return the current local feature vector.

        The previous action and current blocked flag reconstruct relative
        displacement without absolute coordinates. Revisit frequency is the
        fraction of observations at the inferred current cell beyond its first
        visit, divided by observations seen so far.
        """
        obs = np.asarray(observation, dtype=np.float32)
        if obs.shape != (58,) or not np.isfinite(obs).all() or np.any((obs < 0) | (obs > 1)):
            raise ValueError("observation must be a finite 58-value vector in [0, 1]")
        if previous_action is not None and (isinstance(previous_action, bool) or
                                              not isinstance(previous_action, (int, np.integer)) or
                                              not 0 <= previous_action < len(_MOVES)):
            raise ValueError("previous_action must be None or an integer from 0 to 4")

        patch = obs[:54].reshape(3, 3, 6)
        food = patch[:, :, 2]
        home = patch[:, :, 3]
        food_mean, home_mean = float(food.mean()), float(home.mean())
        food_delta, home_delta = (0.0, 0.0) if self.previous_means is None else (
            food_mean - self.previous_means[0], home_mean - self.previous_means[1])
        self.previous_means = (food_mean, home_mean)

        carrying, picked_up, delivered, blocked = obs[54:58]
        if previous_action is not None and not blocked:
            self.position += _MOVES[int(previous_action)]
        key = tuple(int(v) for v in self.position)
        self.visits[key] += 1
        self.observations += 1
        # The initial observation describes state, not a completed transition.
        if previous_action is not None and (picked_up or delivered):
            self.steps_without_progress = 0
        elif previous_action is not None:
            self.steps_without_progress += 1
        revisit_fraction = (self.observations - len(self.visits)) / self.observations
        return np.asarray((food_mean, float(food.max()), home_mean, float(home.max()),
                           food_delta, home_delta, carrying, picked_up, delivered, blocked,
                           min(1.0, self.steps_without_progress / self.progress_horizon),
                           revisit_fraction), dtype=np.float32)


class LocalTimeoutDefense:
    """A local patience/timeout baseline that redirects stale actions.

    Before ``timeout`` unproductive steps, the proposed action passes through.
    Once the threshold is reached, the heuristic prefers an immediately
    adjacent nest cell while carrying or visible food while searching;
    otherwise it cycles over locally legal moves. Boundary bits and local
    landmarks are read only from the current 3x3 observation.
    Pickup or delivery resets the timer. This baseline is not a detector and
    does not establish performance against attacks.
    """

    def __init__(self, timeout=8):
        if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
            raise ValueError("timeout must be a positive integer")
        self.timeout = timeout
        self.reset()

    def reset(self):
        """Clear the baseline's own episode-local progress timer."""
        self.stale_steps = 0
        self.exploration_step = 0
        self.initial_observation = True

    def select_action(self, observation, proposed_action):
        """Pass through or locally redirect ``proposed_action`` (0..4)."""
        obs = np.asarray(observation, dtype=np.float32)
        if obs.shape != (58,) or not np.isfinite(obs).all() or np.any((obs < 0) | (obs > 1)):
            raise ValueError("observation must be a finite 58-value vector in [0, 1]")
        if isinstance(proposed_action, bool) or not isinstance(proposed_action, (int, np.integer)) or not 0 <= proposed_action < 5:
            raise ValueError("proposed_action must be an integer from 0 to 4")
        _, picked_up, delivered, _ = obs[54:58]
        if self.initial_observation:
            self.initial_observation = False
            return int(proposed_action)
        if picked_up or delivered:
            self.stale_steps = 0
            self.exploration_step = 0
        else:
            self.stale_steps += 1
        if self.stale_steps < self.timeout:
            return int(proposed_action)

        patch = obs[:54].reshape(3, 3, 6)
        # Stay is always legal. For movement, the neighbor's boundary flag
        # identifies off-grid actions without access to absolute coordinates.
        legal = [0] + [action for action, (dr, dc) in enumerate(_MOVES[1:], 1)
                       if patch[1 + dr, 1 + dc, 5] == 0]
        carrying = bool(obs[54])
        goal_channel = 1 if carrying else 0
        goal_moves = [action for action in legal if action and patch[
            1 + _MOVES[action][0], 1 + _MOVES[action][1], goal_channel] > 0]
        if goal_moves:
            chosen = goal_moves[0]
        else:
            chosen = legal[self.exploration_step % len(legal)]
        self.exploration_step += 1
        return int(chosen)
