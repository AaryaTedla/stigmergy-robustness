# Decision Record: Phase 2B mechanism-diagnostics protocol

**Status:** Accepted; implementation is limited to audit-only diagnostics and
must not change simulator physics, attack capability, PPO inputs, policy
parameters, dataset partitions, detector inputs, or research claims.

**Date:** 2026-11-12

**Owners and reviewers:** Capstone team

## Decision

Before selecting another false-food attack setting, add an audit-only
mechanism-diagnostics stage to Phase 2B.  Its question is whether the existing
bounded local deposits become visible to honest agents and are associated with
unproductive local behaviour.  It must not be used to tune a detector, alter a
PPO policy, add model inputs, change rewards, or select only favourable
episodes.  The existing injection-loss definition remains the primary
task-impact outcome:

```text
injection loss = honest delivery(injection disabled) - honest delivery(attacked)
```

The diagnostic report will be saved separately from policy-visible trajectories
and will include paired per-group effects, values grouped by PPO training seed,
map seed, and action seed, and an uncertainty summary.  Any proposed new
attack mode (for example, intermittent or decoy deposition) requires a second
accepted record that fixes its trigger, budgets, controls, development
selection rule, and held-out configuration before implementation.

## Context and evidence

The three recorded Candidate J persistent-attack calibrations used three frozen
PPO policies, four development maps, one stochastic action seed, and matched
clean/injection-disabled/attacked episodes.  Their 12 paired groups per
setting produced mean injection losses of -2.17, -0.42, and -2.25 honest food
units for immediate-20, immediate-200, and delayed-200 respectively.  These
are correct signed means, not calculation errors: a negative value means the
attacked member of the pair delivered more on average.  The group-level values
are mixed, so none establishes reliable degradation.

Every attacked episode applied its declared cap, but deposited mass alone does
not demonstrate that another agent saw a misleading signal.  Current records
also have only one stochastic action seed per policy/map group.  These limits
make it inappropriate to change the loss sign, exclude negative groups, train
a detector, or claim a defense.

## Alternatives considered

- **Relabel or negate the existing mean as a positive loss:** rejected.  It
  changes presentation only and would misstate the direction of the measured
  effect.  A slide may instead label the sign-reversed value as an explicitly
  named `attacked - injection-disabled` delivery difference.
- **Increase budgets, attacker count, or field mechanics until the mean is
  positive:** rejected.  This is outcome-driven tuning and may change the
  minority, bounded-local threat contract or the clean policy basis.
- **Train a detector on the 108-episode development corpus now:** rejected.
  The calibration has not established task damage, and no final grouped split,
  labels, or held-out evaluation has been accepted.
- **Add a new intermittent/decoy attack immediately:** deferred.  It is in
  scope only after a separate attack-mechanics decision and tests.

## Consequences

The future implementation may record audit-only quantities needed to answer
the mechanism question, such as total applied false mass, cell-cap saturation,
the amount of false-food component in honest agents' local 3 by 3 views,
honest-agent exposure counts, revisitation after exposure, and own
pickup/delivery progress after exposure.  It must preserve the ordinary local
58-value PPO observation exactly: false-component attribution, attack events,
attacker IDs, global food locations, global delivery, and exposure labels are
simulator-only audit data and are forbidden detector or policy features.

New diagnostic rollouts must retain all three matched scenarios, frozen
Candidate J checkpoints, one selected attacker among four agents, occupied-cell
nonnegative deposits, and the common field cap/evaporation dynamics.  They
must use several predeclared stochastic action seeds per policy/map group and
report all groups.  Training-seed variability and evaluation/action-seed
variability must remain separate.  Development results select no final claim;
unseen maps and one withheld attack configuration must be declared before final
evaluation.

## Validation and context update

The audit implementation must specify exact field names, units, update order,
cap attribution, and the policy/audit boundary. Tests must prove it does not
alter field physics, observations, actions, rewards, episode seeds, or the
clean/injection-disabled equivalence; they must cover deposits, clipping,
evaporation, reset, delayed onset, and corpus leakage rejection.

Before a new evidence-bearing diagnostic calibration is run, the team must:

1. Predeclare the action-seed replication count and statistical summaries:
   all paired values, per-training-seed aggregates, median, harmful-group
   fraction, and an appropriate paired uncertainty interval.
2. Run the focused checks and the full pinned suite; collect fresh output in a
   new directory with manifests and hashes.

Historical Phase 2B values remain separate from any fresh diagnostic output;
the recovered Candidate J checkpoints are validated by their recorded hashes.

## Result

The accepted audit instrumentation was implemented without modifying the
attack configuration, simulator field values, PPO observation shape, actions,
rewards, policy parameters, or dataset partitions. `attack_food_component` is
a separate simulator-only food-field array. Applied false mass is assigned to
it after injection; when ordinary deposits overflow a cell, the component uses
the documented proportional cap rule, and it then evaporates exactly with the
food field. `audit_attack_food_component_views()` returns normalized 3 by 3
copies only for audit writers.

Matched rollout records now store `attack_food_component_after` solely under
`simulator_metadata`, plus honest-agent exposed-step and normalized component
sum aggregates in episode metrics. The Phase 2B corpus forbids each of these
names in local records. Focused environment/attack/Phase 2B/corpus checks
passed 76 tests and the complete pinned suite passed 164 tests in 32.76 seconds on the local
Phase 2A virtual environment. The tiny frozen-PPO integration test exercised
the changed record boundary. No Candidate J matrix was rerun, no action-seed
replication count has been selected, and no claim about attack effectiveness,
detector performance, or robustness follows from this implementation.

The fresh delayed-200 diagnostic then ran 60 paired groups (three frozen
Candidate J policies, four development maps, five predeclared action seeds)
and 180 matched episodes. All attacked episodes applied 200 units. Mean paired
injection loss was +0.17 honest food units, the median was 0, and 14/60 (23.3%)
groups were harmful. Honest agents had nonzero false-food exposure in all 60
attacked episodes (mean 2,130.17 honest exposed agent-steps). This is a small,
mixed development result—not a reliable disruption, detector, defense, or
held-out robustness result.
