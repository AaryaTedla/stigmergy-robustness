# Decision Record: review persistent false-food injection and provenance

**Status:** Accepted (CPython 3.11 recheck pending)

**Date:** 2026-10-08

**Owners and reviewers:** Rohan (attacks and trajectories owner); Tusti (planned review owner). Implementation assisted by Codex; team review pending.

## Decision

For the first-review attack milestone, implement one persistent false-food
injection mode. At the start of every episode, the simulator selects a fixed,
seeded count of compromised agents. After all agents have made their legal
movement and completed the ordinary pickup/delivery transition, each selected
agent can request a nonnegative food-pheromone deposit at its own resulting
cell. The injector limits the request by a configured per-step allowance and
the remaining episode allowance, then limits the applied mass by the same food
field cap used for ordinary deposits. The combined field is clipped and
evaporated in the existing common stage. Clean, injection-disabled, and
attacked scenario configurations share the environment seed and attack
parameters; the injection-disabled control retains the same selected
compromised set but writes no false mass.

## Context and evidence

The clean mechanics decision already reserves attack insertion before common
clipping/decay, but did not define selection, budgets, logs, or controls.
This narrow mode meets the agreed first-review target without asserting that it
is a complete attack suite. The implementation will log requested,
budget-authorized, and cap-applied mass separately because a requested deposit
need not fit the field cap. Attack events and attacker identity remain
simulator-only trajectory metadata and are never included in agent
observations or infos.

## Alternatives considered

- Adding persistent, decoy, and intermittent modes together: deferred so this
  review checkpoint has one auditable mechanism.
- Selecting a new malicious set every step: rejected because the threat model
  fixes the compromised set for an episode.
- Making injection a privileged global write or allowing erasure/negative
  mass: rejected by the project threat boundary.
- Logging only applied mass: rejected because it would conceal budget and cap
  effects needed to audit an attack run.

## Consequences

The first-review artifact is a simulator attack and provenance foundation, not
an evaluation result. It adds no policy-visible feature, direct communication,
or detector input. The future decoy and intermittent modes, trained PPO
rollouts, split manifests, held-out maps, and learned-policy comparisons remain
separate work. Any change to placement, attacker capability, or the common
field transport rule requires a new decision record.

## Validation and context update

Focused deterministic checks passed for seeded selection, occupied-cell
placement, nonnegativity, per-step and episode budgets, cap interaction,
injection-disabled controls, no observation/info leakage, and trajectory
metadata separation. The full suite passed 46 tests with the locked
dependencies on CPython 3.14.4. Seed-7 clean, injection-disabled, and attacked
fixtures all delivered eight units in 89 steps; the clean and disabled
policy-visible transition records matched, while the attacked fixture selected
one agent and applied its full 20-unit episode budget. CPython 3.11 was not
available in this workspace, so rerun the full suite and these fixtures on the
declared target runtime before release or evaluation.
