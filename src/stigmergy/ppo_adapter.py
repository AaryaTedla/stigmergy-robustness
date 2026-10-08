"""Adapt the fixed-lifecycle clean grid to SB3's parameter-shared VecEnv API.

One slot per agent supplies an (N, 58) float32 observation batch, an (N,)
integer action vector, shared delivery rewards (N,), and simultaneous done
flags (N,). These slots interact within one grid; they are not independent
episodes. PPO applies a single local network to each row without IDs or
global state. This adapter supports only ResourceRetrievalEnv's synchronous
lifecycle and excludes attacks during clean policy training.

All agents reset together. At terminal/truncated boundaries, returned rows
are the next episode's initial observations, while infos retain copies of
the preceding final observations and TimeLimit.truncated for SB3's timeout
bootstrap. Simulator-only completed-episode accounting is kept on the adapter,
never added to observations. Call reset() before step(); step_async stores a
validated action batch, and step_wait consumes it once. Map seeds cycle over
the supplied development list; seed(seed) selects a deterministic starting
offset in that list, rather than creating new or held-out map seeds.

Requires the optional training stack. Imported only by training and its tests,
so simulator/demo use does not require PyTorch or Stable-Baselines3.
"""

import numpy as np
from stable_baselines3.common.vec_env import VecEnv

from .environment import ResourceRetrievalEnv


class SharedGridVecEnv(VecEnv):
    """Batch one fixed homogeneous world into local agent slots for shared PPO."""

    def __init__(self, config, map_seeds):
        seeds = tuple(map_seeds)
        if not seeds or any(isinstance(s, bool) or not isinstance(s, int) or s < 0 for s in seeds):
            raise ValueError("map_seeds must contain nonnegative integer development seeds")
        if len(set(seeds)) != len(seeds):
            raise ValueError("map_seeds must be unique")
        self.world = ResourceRetrievalEnv(config)
        self.agent_order = tuple(self.world.possible_agents)
        self.map_seeds = seeds
        self.cursor = 0
        self.pending_actions = None
        self.episode_records = []
        first = self.agent_order[0]
        super().__init__(len(self.agent_order), self.world.observation_space(first), self.world.action_space(first))

    def seed(self, seed=None):
        """Restart the declared map cycle at a reproducible offset; no new maps."""
        self.cursor = 0 if seed is None else int(seed) % len(self.map_seeds)
        return [self.map_seeds[self.cursor]] * self.num_envs

    def reset(self):
        """Reset the whole world to the next declared development map seed."""
        if any(self._options):
            raise ValueError("custom reset options are unsupported; use declared map seeds")
        self.current_map_seed = self.map_seeds[self.cursor % len(self.map_seeds)]
        self.cursor += 1
        observations, infos = self.world.reset(seed=self.current_map_seed)
        self.reset_infos = [infos[a] for a in self.agent_order]
        self.pending_actions = None
        self._reset_seeds()
        self._reset_options()
        return self._batch(observations)

    def _batch(self, observations):
        """Stack copied local rows in stable agent order without any augmentation."""
        return np.stack([observations[a] for a in self.agent_order]).astype(np.float32)

    def step_async(self, actions):
        """Validate and store one complete batch without moving the world yet."""
        if self.pending_actions is not None:
            raise RuntimeError("consume the pending batch with step_wait first")
        values = np.asarray(actions)
        if values.shape != (self.num_envs,) or values.dtype.kind not in "iu" or np.any((values < 0) | (values >= 5)):
            raise ValueError("actions must be an integer vector with one value 0..4 per agent")
        if not self.world.agents:
            raise RuntimeError("call reset before stepping")
        self.pending_actions = values.copy()

    def step_wait(self):
        """Apply the stored batch, preserving final observations before auto-reset."""
        if self.pending_actions is None:
            raise RuntimeError("call step_async before step_wait")
        actions = dict(zip(self.agent_order, map(int, self.pending_actions)))
        self.pending_actions = None
        obs, rewards, terms, truncs, own_infos = self.world.step(actions)
        done = np.array([terms[a] or truncs[a] for a in self.agent_order], dtype=bool)
        if done.any() and not done.all():
            raise RuntimeError("this adapter requires simultaneous agent lifecycle")
        infos = [dict(own_infos[a], **{"TimeLimit.truncated": bool(truncs[a] and not terms[a])})
                 for a in self.agent_order]
        batch = self._batch(obs)
        if done.all():
            self.episode_records.append({"map_seed": self.current_map_seed,
                                         "steps": self.world.steps,
                                         "delivered": self.world.delivered_total})
            for i in range(self.num_envs):
                infos[i]["terminal_observation"] = batch[i].copy()
            batch = self.reset()
        return batch, np.array([rewards[a] for a in self.agent_order], dtype=np.float32), done, infos

    def close(self):
        """Release simulator resources; no workers or native windows are created."""
        self.world.close()

    def get_attr(self, attr_name, indices=None):
        """Expose administrative world attributes requested by the VecEnv base."""
        return [getattr(self.world, attr_name) for _ in self._get_indices(indices)]

    def set_attr(self, attr_name, value, indices=None):
        """Reject per-slot mutation because slots share one world."""
        raise NotImplementedError("per-slot world mutation is unsupported")

    def env_method(self, method_name, *method_args, indices=None, **method_kwargs):
        """Reject independent-slot method calls on this coupled world."""
        raise NotImplementedError("use the explicit whole-world adapter interface")

    def env_is_wrapped(self, wrapper_class, indices=None):
        """Report that the underlying clean grid has no Gymnasium wrappers."""
        return [False for _ in self._get_indices(indices)]
