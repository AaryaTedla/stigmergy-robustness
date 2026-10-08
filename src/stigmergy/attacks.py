"""Bounded false-food injection for the first-review simulator attack pilot.

This module implements one intentionally narrow threat: selected compromised
agents repeatedly request a nonnegative food-pheromone deposit after legal
movement at their actual occupied grid cell.  It does not alter actions,
rewards, observations, food, home pheromone, or policy parameters.  The
environment owns the field array and calls :class:`PersistentFalseFoodInjector`
before its normal common clipping and evaporation stage.

``AttackConfig`` expresses mass in the simulator's pheromone units.  A request
is first constrained by the per-step and remaining episode budgets, then by
the food field's remaining room under its cap.  Each ``AttackEvent`` preserves
the requested, budget-authorized, and actually applied masses so a capped cell
cannot make a run look as though its requested attack was fully applied.

The compromised IDs and returned events are simulator-only provenance.  They
must never be copied into policy observations, PettingZoo infos, detector
features, or a controller's input.  Call ``reset(agent_ids, seed)`` at an
episode boundary and ``inject(fields, positions, field_cap)`` once per
environment step after movement.  The current first-review mode is persistent;
decoy and intermittent modes remain future work.
"""

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class AttackConfig:
    """Configuration for one persistent false-food attack episode.

    ``compromised_count`` is fixed for an episode.  ``requested_deposit`` is
    the desired mass per selected agent per step; both budget fields are hard
    upper bounds on mass actually applied.  Set ``enabled`` to ``False`` for
    an injection-disabled twin: it retains the same deterministic selection
    but applies zero mass.  The clean control is represented by no injector.
    """

    compromised_count: int = 1
    requested_deposit: float = 1.0
    per_step_budget: float = 1.0
    episode_budget: float = 20.0
    enabled: bool = True
    mode: str = "persistent"

    def __post_init__(self):
        if (isinstance(self.compromised_count, bool) or
                not isinstance(self.compromised_count, int) or self.compromised_count < 1):
            raise ValueError("compromised_count must be a positive integer")
        for name in ("requested_deposit", "per_step_budget", "episode_budget"):
            value = getattr(self, name)
            if (isinstance(value, bool) or not isinstance(value, (int, float)) or
                    not np.isfinite(value) or value < 0):
                raise ValueError(f"{name} must be a finite nonnegative number")
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a boolean")
        if self.mode != "persistent":
            raise ValueError("the first-review injector supports only mode='persistent'")

    def as_dict(self):
        """Return JSON-ready configuration provenance without runtime state."""
        return asdict(self)

    def injection_disabled(self):
        """Return a matched control config with the same selection parameters."""
        return AttackConfig(**{**self.as_dict(), "enabled": False})


@dataclass(frozen=True)
class AttackEvent:
    """Simulator-only accounting for one selected agent's step-level request.

    ``position`` uses the environment's ``(row, column)`` convention.
    ``authorized_mass`` is bounded by the local per-step and episode budgets;
    ``applied_mass`` is additionally bounded by field capacity.  A disabled
    control records no events because it makes no injection request.
    """

    agent: str
    position: tuple[int, int]
    requested_mass: float
    authorized_mass: float
    applied_mass: float

    def as_dict(self):
        """Return a stable JSON-ready event record."""
        return {"agent": self.agent, "position": list(self.position),
                "requested_mass": self.requested_mass,
                "authorized_mass": self.authorized_mass,
                "applied_mass": self.applied_mass}


class PersistentFalseFoodInjector:
    """Select fixed attackers and apply their bounded food-field requests.

    The caller supplies the two-channel field array and current post-movement
    positions.  This object mutates only ``fields[0]`` and only at selected
    agents' positions.  It intentionally does not know food locations, policy
    observations, actions, rewards, or any defensive state.
    """

    def __init__(self, config):
        if not isinstance(config, AttackConfig):
            raise TypeError("config must be an AttackConfig")
        self.config = config
        self._agent_ids = ()
        self.compromised_agents = ()
        self.episode_applied_mass = 0.0
        self.total_requested_mass = 0.0
        self.total_authorized_mass = 0.0
        self.last_events = ()

    def reset(self, agent_ids, seed=None):
        """Seed-select a fixed subset and clear all episode accounting.

        Agent IDs must be unique strings, matching the parallel environment's
        deterministic ordering.  A dedicated generator keeps attacker
        selection from consuming the environment's map/contention RNG stream.
        """
        agent_ids = tuple(agent_ids)
        if (len(agent_ids) != len(set(agent_ids)) or not agent_ids or
                not all(isinstance(agent, str) for agent in agent_ids)):
            raise ValueError("agent_ids must be a nonempty sequence of unique strings")
        if self.config.compromised_count > len(agent_ids):
            raise ValueError("compromised_count cannot exceed the number of agents")
        if seed is not None and (isinstance(seed, bool) or not isinstance(seed, (int, np.integer))):
            raise ValueError("seed must be None or an integer")
        # The constant creates a distinct, reproducible RNG stream from reset.
        rng = np.random.default_rng(None if seed is None else np.random.SeedSequence([int(seed), 0xA77AC]))
        selected = rng.choice(len(agent_ids), size=self.config.compromised_count, replace=False)
        self._agent_ids = agent_ids
        self.compromised_agents = tuple(agent_ids[int(index)] for index in sorted(selected))
        self.episode_applied_mass = 0.0
        self.total_requested_mass = 0.0
        self.total_authorized_mass = 0.0
        self.last_events = ()
        return self.compromised_agents

    def inject(self, fields, positions, field_cap):
        """Apply this step's bounded requests and return immutable event records.

        ``fields`` must have food channel zero and one row/column location for
        each agent in reset order.  The environment performs the final shared
        clipping and evaporation after this method; the local capacity check
        below makes applied mass auditable even before that common stage.
        """
        array = np.asarray(fields)
        position_array = np.asarray(positions)
        if not self._agent_ids:
            raise RuntimeError("reset must be called before inject")
        if array.ndim != 3 or array.shape[0] < 1 or not np.isfinite(array).all():
            raise ValueError("fields must be a finite array with a food channel at index 0")
        if position_array.shape != (len(self._all_agent_ids()), 2):
            raise ValueError("positions must have shape (agent_count, 2)")
        if (isinstance(field_cap, bool) or not isinstance(field_cap, (int, float)) or
                not np.isfinite(field_cap) or field_cap <= 0):
            raise ValueError("field_cap must be a finite positive number")
        if not self.config.enabled:
            self.last_events = ()
            return self.last_events

        # Agent IDs use their reset ordering, which mirrors environment rows.
        index_by_agent = {agent: index for index, agent in enumerate(self._all_agent_ids())}
        events = []
        step_applied = 0.0
        for agent in self.compromised_agents:
            index = index_by_agent[agent]
            raw_row, raw_column = position_array[index]
            if (not np.isfinite(raw_row) or not np.isfinite(raw_column) or
                    int(raw_row) != raw_row or int(raw_column) != raw_column):
                raise ValueError("selected agent positions must be finite integer grid cells")
            row, column = int(raw_row), int(raw_column)
            if not (0 <= row < array.shape[1] and 0 <= column < array.shape[2]):
                raise ValueError("selected agent position must be inside the field")
            requested = float(self.config.requested_deposit)
            remaining_step = max(0.0, float(self.config.per_step_budget) - step_applied)
            remaining_episode = max(0.0, float(self.config.episode_budget) - self.episode_applied_mass)
            authorized = min(requested, remaining_step, remaining_episode)
            headroom = max(0.0, float(field_cap) - float(array[0, row, column]))
            applied = min(authorized, headroom)
            array[0, row, column] += applied
            step_applied += applied
            self.episode_applied_mass += applied
            self.total_requested_mass += requested
            self.total_authorized_mass += authorized
            events.append(AttackEvent(agent, (row, column), requested, authorized, applied))
        self.last_events = tuple(events)
        return self.last_events

    def _all_agent_ids(self):
        """Return reset order retained for position-to-agent provenance mapping."""
        if not self._agent_ids:
            raise RuntimeError("reset must be called before inject")
        return self._agent_ids

    def summary(self):
        """Return JSON-ready episode-level metadata for a trajectory manifest."""
        return {"config": self.config.as_dict(), "compromised_agents": list(self.compromised_agents),
                "compromised_count": len(self.compromised_agents),
                "total_requested_mass": self.total_requested_mass,
                "total_authorized_mass": self.total_authorized_mass,
                "total_applied_mass": self.episode_applied_mass}
