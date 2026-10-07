# Decision Record: clean grid pilot mechanics

**Status:** Accepted (mechanics validated; team review pending)

**Date:** 2026-10-07

**Owners and reviewers:** Aarya (environment owner); Shashannk (planned team reviewer). Implementation assisted by Codex; team review pending.

## Decision

Implement a PettingZoo ParallelEnv with an 8×8/two-agent development configuration and a 16×16/eight-agent pilot configuration, 500-step horizon, top-left 2×2 nest, and two seeded single-cell resource patches. Coordinates are (row, column). Actions are stay, north, east, south, west. Boundaries block movement. Agents may share cells and swap positions; this explicitly permits congestion without exclusion collisions.

Each step validates all actions before mutation, moves all agents, automatically delivers carried food at the nest or picks up one unit elsewhere, deposits food pheromone when carrying and home pheromone otherwise, clips each channel, then evaporates. No diffusion or obstacles in this milestone. Pickup contention uses a seeded random permutation each step. Deposits are nonnegative fixed configuration amounts at occupied post-movement cells. Field cap and evaporation apply uniformly. Future attack insertion must occur before the same clipping/decay stage and requires its own record.

Observations contain a 3×3 local patch (food availability, nest, food pheromone, home pheromone, occupancy fraction, boundary mask), own carrying state, and own pickup/delivery/blocked events. No absolute coordinates, global food map, identity labels, or attack metadata enter observations or per-agent info. Reward is the common count delivered this step. Full completion terminates; horizon truncates only if not complete.

## Context and evidence

This makes the existing environment commitments executable. Defaults are development fixtures, not a frozen evaluation protocol. See `tests/test_environment.py` for conservation, determinism, locality, lifecycle, and interface checks. The visual demo uses a scripted route on an explicit fixture map; it is mechanics evidence, not a policy baseline or learned coordination result.

## Alternatives considered

- Exclusive cell occupancy: deferred because collision resolution would add complexity before clean mechanics are verified.
- Diffusion: optional and deferred; evaporation is sufficient for the first field demo.
- Global observations or goal-directed oracle baseline: excluded from policy interfaces. The scripted demo remains a separate fixture.

## Consequences

Co-location makes congestion different from exclusive-occupancy environments. Fixed deposits are an initial field model, not evidence of useful learned trail following. PPO, threat implementation, split manifests, defenses, and comparisons remain pending. Changing mechanics or action/observation semantics requires a subsequent record.

## Validation and context update

Accept after focused pytest checks, PettingZoo parallel API validation, repeated seeded demo output, and package installation pass on Python 3.11. Record exact results in context/changelog. Team review remains pending even after mechanical validation.

Validation completed on CPython 3.11.16: 27 pytest cases passed, including parallel API checks and exact repeated demo summary/SVG comparisons. Seed 7 fixtures delivered all eight units in 89 steps (development) and 55 steps (pilot). Editable installation with pinned dependencies succeeded. Generic reset options are ignored for compatibility with the PettingZoo test; food fixture options are validated.
