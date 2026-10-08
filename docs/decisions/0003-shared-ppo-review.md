# Decision Record: shared PPO review pipeline

**Status:** Accepted (pipeline verified on Python 3.12; Python 3.11/team review pending)

**Date:** 2026-10-08

**Owners and reviewers:** Shashannk (policies/training); Rohan (planned reviewer).

## Decision

Use Stable-Baselines3 PPO with one CPU MLP actor and local value network shared
by every agent. A narrow custom VecEnv adapter batches the agent observations
from one clean PettingZoo world. Slots are interacting agents, not independent
worlds. The adapter preserves the existing local observations, action semantics
and unmodified shared delivery reward. It resets all slots together and retains
each agent's terminal observation and TimeLimit.truncated flag. No centralized
critic, extra identity feature, reward shaping, or attacker metadata is added.

Training cycles an explicit list of development map seeds. Disjoint development
diagnostic seeds are used before and after training, with reproducible stochastic
actions and deterministic actions reported separately. Neither list is a final
held-out test manifest or a trajectory split. They must remain development data
in future grouped map/episode partitioning. Smoke runs use 4096 agent transitions;
the development budget is 300000, with actual rollout-rounded counts logged.

## Context and evidence

The environment has fixed homogeneous observations/actions and simultaneous
agent lifecycle, so a small adapter makes termination and seed provenance
auditable without a general wrapper stack. Parameter sharing is established in
[PettingZoo's SB3 tutorials](https://pettingzoo.farama.org/tutorials/sb3/index.html).
The adapter follows the pinned
[SB3 2.7.1 VecEnv contract](https://stable-baselines3.readthedocs.io/en/v2.7.1/guide/vec_envs.html).

## Alternatives considered

- SuperSuit's generic conversion: deferred for this fixed-lifecycle pilot;
  custom terminal/truncation checks and explicit map scheduling remain necessary.
- Independent policies or centralized/global critic inputs: excluded from this
  local-observation parameter-shared milestone.
- Reward shaping or easy oracle routes: excluded; preserve sparse shared reward
  and report poor learning honestly before any new mechanics decision.

## Consequences

The first review verifies pipeline execution, checkpoint roundtrip, parameter
updates and development diagnostics. A short run alone does not establish
learning, trail reliance, attack robustness, uncertainty or a no-pheromone
baseline. Correlated agent samples and sparse team reward may impede learning.
Only clean development training is implemented; full curriculum and final
evaluation remain future work. CPU single-thread execution bounds review cost.

## Validation and context update

Check direct-environment equivalence, seed scheduling, terminal vs truncated
bootstrap semantics, local controller inputs, finite PPO updates, checkpoint
roundtrip, repeated-seed outcomes and the full suite. Run a short reproducible
development experiment and record measured deliveries without a success claim.
Pin the dependency stack after installation/checks; report Python 3.11 recheck
as pending if the target interpreter is unavailable.

Validation: Windows CPython 3.12.10, torch 2.5.1+cpu and SB3 2.7.1 passed the
full 61-test suite, editable installation and dependency consistency checks.
SB3 2.4.1 was rejected before installation due to its NumPy<2 constraint.
Two seed-7 runs of 4096 agent transitions produced identical summaries and
parameter hashes, finite changed parameters and matching checkpoint reload.
Deterministic diagnostic mean deliveries stayed at zero; stochastic mean
changed from 1.75 to 3.75 on four development maps, with no complete episode.
This is pipeline evidence, not an established learning/robustness result.
See the Shashannk walkthrough for commands and retained artifacts.
