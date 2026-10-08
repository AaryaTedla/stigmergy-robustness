"""Deterministic, locally observed cooperative resource-retrieval simulator.

Purpose: provide Aarya's environment foundation, not a learned-policy result.
Grid coordinates are (row, column), with a top-left 2×2 nest. Agents carry at
most one food unit. Two resource cells are sampled outside the nest on reset;
an explicit pair may instead be supplied for deterministic test/demo fixtures.

Usage: construct ResourceRetrievalEnv(GridConfig()), reset(seed=7), then pass
one integer action for every live agent to step(). Actions 0..4 mean stay,
north, east, south, west. The five returned dictionaries follow PettingZoo's
parallel contract: observations, rewards, terminations, truncations, infos.

Step order: validate the entire action batch; move (off-grid moves stay put);
deliver/pick up in seeded contention order; deposit according to carrying
state; optionally inject bounded false-food mass at selected attackers' actual
post-movement cells; cap fields; evaporate; emit observations and own progress
events.  Attack selection and mass accounting are simulator-only provenance,
never an observation or info field.
Co-location and swaps are allowed. Team reward counts deliveries. Completion
terminates; reaching the horizon otherwise truncates. Food is conserved among
resource cells, carried units, and deliveries.

Observation layout: flattened 3×3×6 patch in row/column/channel order, then
four own-state values: carrying, picked_up, delivered, blocked. Patch channels
are food-present, nest, normalized food field, normalized home field,
occupancy divided by agent count, and out-of-bounds. Outside cells contain
zeros except the boundary channel. No global map or absolute position is
provided to policies. Public simulator arrays are for tests/rendering only;
future policy and defense code must use observations, not these arrays.

Fields have shape (2, size, size): food channel 0, home channel 1. Deposits
occur at actual post-movement positions, are nonnegative, and share the cap
and evaporation rule. The optional first-review persistent attack uses the
same food-field cap and transport stage; see decision 0002 for its narrow
threat model. Diffusion and learned defenses remain future milestones.
"""

from dataclasses import dataclass

import numpy as np
from gymnasium import spaces
from pettingzoo import ParallelEnv

from .attacks import AttackConfig, PersistentFalseFoodInjector


@dataclass(frozen=True)
class GridConfig:
    """Validated mechanics parameters; field amounts use arbitrary simulation units."""

    size: int = 8
    n_agents: int = 2
    horizon: int = 500
    food_per_patch: int = 4
    deposit: float = 1.0
    field_cap: float = 10.0
    evaporation: float = 0.1

    def __post_init__(self):
        for name in ("size", "n_agents", "horizon", "food_per_patch"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.size < 4:
            raise ValueError("size must be at least 4")
        for name in ("deposit", "field_cap", "evaporation"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
                raise ValueError(f"{name} must be a finite number")
        if not 0 <= self.deposit <= self.field_cap or self.field_cap <= 0:
            raise ValueError("require 0 <= deposit <= field_cap and field_cap > 0")
        if not 0 <= self.evaporation <= 1:
            raise ValueError("evaporation must be in [0, 1]")


class ResourceRetrievalEnv(ParallelEnv):
    """Simultaneous movement with local observations and seeded pickup contention."""

    metadata = {"name": "resource_retrieval_v0", "render_modes": ["ansi"], "is_parallelizable": True}
    MOVES = np.array([(0, 0), (-1, 0), (0, 1), (1, 0), (0, -1)])

    def __init__(self, config=None, render_mode=None, attack_config=None):
        """Create a clean environment or one with explicit attack provenance.

        ``attack_config`` is optional because a clean environment must retain
        no attacker state.  When present, its selection and event log remain
        on simulator-only attributes, not the PettingZoo agent interface.
        """
        self.config = config or GridConfig()
        if render_mode not in (None, "ansi"):
            raise ValueError("render_mode must be None or ansi")
        self.render_mode = render_mode
        self.possible_agents = [f"agent_{i}" for i in range(self.config.n_agents)]
        self.agents = []
        self.observation_spaces = {a: spaces.Box(0, 1, shape=(58,), dtype=np.float32) for a in self.possible_agents}
        self.action_spaces = {a: spaces.Discrete(5) for a in self.possible_agents}
        self.rng = np.random.default_rng()
        if attack_config is not None and not isinstance(attack_config, AttackConfig):
            raise TypeError("attack_config must be None or an AttackConfig")
        self.attack_injector = (PersistentFalseFoodInjector(attack_config)
                                if attack_config is not None else None)
        self.last_attack_events = ()

    def observation_space(self, agent):
        return self.observation_spaces[agent]

    def action_space(self, agent):
        return self.action_spaces[agent]

    def reset(self, seed=None, options=None):
        """Create a seeded development map, or validate an explicit two-cell fixture."""
        if seed is not None:
            self.rng = np.random.default_rng(seed)
            for i, a in enumerate(self.possible_agents):
                self.action_space(a).seed(seed + i)
        c = self.config
        options = options or {}
        # PettingZoo tests pass generic options; unrecognized keys have no effect.
        candidates = [(r, col) for r in range(c.size) for col in range(c.size) if not (r < 2 and col < 2)]
        patches = options.get("food_positions")
        if patches is None:
            patches = [candidates[i] for i in self.rng.choice(len(candidates), 2, replace=False)]
        try:
            patches = [tuple(p) for p in patches]
            valid = len(patches) == 2 and len(set(patches)) == 2 and all(p in candidates for p in patches)
            valid = valid and all(isinstance(v, (int, np.integer)) and not isinstance(v, bool) for p in patches for v in p)
        except (TypeError, ValueError):
            valid = False
        if not valid:
            raise ValueError("food_positions must be two distinct integer cells outside the nest")
        self.agents = self.possible_agents.copy()
        self.positions = np.array([(i // 2 % 2, i % 2) for i in range(c.n_agents)])
        self.carrying = np.zeros(c.n_agents, dtype=bool)
        self.nest = np.zeros((c.size, c.size), dtype=bool)
        self.nest[:2, :2] = True
        self.food = np.zeros((c.size, c.size), dtype=np.int32)
        for p in patches:
            self.food[p] = c.food_per_patch
        self.fields = np.zeros((2, c.size, c.size), dtype=np.float64)
        self.events = np.zeros((c.n_agents, 3), dtype=np.float32)
        self.steps = self.delivered_total = 0
        self.last_attack_events = ()
        if self.attack_injector is not None:
            self.attack_injector.reset(self.possible_agents, seed=seed)
        return self._observations(), self._infos()

    def step(self, actions):
        """Apply one complete batch atomically with respect to invalid input."""
        if not self.agents:
            if actions:
                raise ValueError("reset before stepping an inactive environment")
            return {}, {}, {}, {}, {}
        if set(actions) != set(self.agents):
            raise ValueError("provide exactly one action per live agent")
        if any(isinstance(v, (bool, np.bool_)) or not self.action_space(a).contains(v) for a, v in actions.items()):
            raise ValueError("actions must be integers from 0 to 4")
        live = self.agents.copy()
        self.events.fill(0)
        for i, a in enumerate(live):
            target = self.positions[i] + self.MOVES[int(actions[a])]
            if np.all((target >= 0) & (target < self.config.size)):
                self.positions[i] = target
            else:
                self.events[i, 2] = 1
        deliveries = 0
        for i in self.rng.permutation(len(live)):
            p = tuple(self.positions[i])
            if self.carrying[i] and self.nest[p]:
                self.carrying[i] = False
                self.events[i, 1] = 1
                deliveries += 1
            elif not self.carrying[i] and self.food[p] > 0:
                self.food[p] -= 1
                self.carrying[i] = True
                self.events[i, 0] = 1
        for i in range(len(live)):
            channel = 0 if self.carrying[i] else 1
            self.fields[(channel, *self.positions[i])] += self.config.deposit
        if self.attack_injector is not None:
            self.last_attack_events = self.attack_injector.inject(
                self.fields, self.positions, self.config.field_cap)
        np.clip(self.fields, 0, self.config.field_cap, out=self.fields)
        self.fields *= 1 - self.config.evaporation
        self.steps += 1
        self.delivered_total += deliveries
        complete = self.food.sum() == 0 and not self.carrying.any()
        timed_out = self.steps >= self.config.horizon and not complete
        observations, infos = self._observations(), self._infos()
        if complete or timed_out:
            self.agents = []
        return (observations, {a: float(deliveries) for a in live},
                {a: bool(complete) for a in live}, {a: timed_out for a in live}, infos)

    def _observations(self):
        """Copy a bounded local crop; simulator-wide arrays never enter this output."""
        result = {}
        for i, a in enumerate(self.agents):
            patch = np.zeros((3, 3, 6), dtype=np.float32)
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    r, col = self.positions[i] + (dr, dc)
                    cell = patch[dr + 1, dc + 1]
                    if not (0 <= r < self.config.size and 0 <= col < self.config.size):
                        cell[5] = 1
                        continue
                    cell[:2] = self.food[r, col] > 0, self.nest[r, col]
                    cell[2:4] = self.fields[:, r, col] / self.config.field_cap
                    cell[4] = np.all(self.positions == (r, col), axis=1).sum() / self.config.n_agents
            result[a] = np.concatenate((patch.ravel(), [self.carrying[i]], self.events[i])).astype(np.float32)
        return result

    def _infos(self):
        # Attack metadata deliberately stays out of infos: policy, defense,
        # and external wrappers must not receive attacker labels or timing.
        return {a: dict(zip(("picked_up", "delivered", "blocked"), map(bool, self.events[i])))
                for i, a in enumerate(self.agents)}

    def attack_summary(self):
        """Return simulator-only accounting for provenance writers, not agents."""
        return None if self.attack_injector is None else self.attack_injector.summary()

    def render(self):
        """Return a global ASCII view for humans only: N nest, F food, digits occupancy."""
        grid = np.full(self.food.shape, ".", dtype="<U1")
        grid[self.nest] = "N"
        grid[self.food > 0] = "F"
        for r, col in self.positions:
            count = np.all(self.positions == (r, col), axis=1).sum()
            grid[r, col] = str(min(count, 9))
        return "\n".join(" ".join(row) for row in grid)

    def close(self):
        """No external windows or handles are opened by this environment."""
