# Decision Record: Phase 2B attack-calibration and data-protocol contract

**Status:** Completed; initial persistent-attack calibration did not establish
delivery degradation. Detector fitting, held-out evaluation and robustness
claims remain out of scope.

**Date:** 2026-11-01

**Owners and reviewers:** Capstone team. Proposed implementation ownership:
Rohan (attack/provenance and grouped data), Tusti (local features, detector and
evaluation), Shashannk (frozen PPO checkpoint loading), Aarya (environment and
field-mechanics review).

## Decision

Phase 2B will begin from the completed Phase 2A Candidate J clean policies and
will first run a small, auditable *development-only* attack calibration. The
clean Candidate J environment, full-observation PPO architecture, policy
checkpoints, transition budget, local 3 by 3 observation and field mechanics
are frozen. No Phase 2B work may retrain or select a clean policy after seeing
attack results.

The calibration will use the already implemented persistent false-food injector
only: one episode-fixed compromised agent out of four (25%), nonnegative food
pheromone deposits at its actual post-movement cell, and the shared field cap
and evaporation stage. The initial requested deposit, per-step cap and episode
cap are 1.0, 1.0 and 20.0 field units, respectively, matching
`configs/attack/persistent-review.json`. These are calibration settings, not a
claim that this is the strongest or final attack. The attacker may not erase
pheromone, write globally, alter food/rewards/actions/policy weights, or use
negative mass.

For each frozen Candidate J full-input checkpoint (training seeds 7, 17 and
27) and each declared Phase 2A diagnostic map seed (100, 101, 102 and 103),
run a matched stochastic triplet: `clean`, `injection_disabled`, and
`attacked`. Clean has no injector. Injection-disabled retains the same
episode-fixed compromised-agent selection as attacked but deposits no false
mass. This separates the false-pheromone signal from the possible effect of
having a compromised-worker designation. The first calibration compares the
frozen full-input policy without a defense; it does not yet fit a detector,
tune a timeout threshold, add a warning channel, or evaluate a final test set.
Use action seed 7 for this initial integration matrix: 3 checkpoints × 4 maps
× 1 action-seed replication × 3 scenarios = 36 episodes.

Before any temporal detector windows are created, the implementation will
create immutable group-level split manifests. A group contains every complete
episode variant sharing a policy checkpoint, map seed, action-seed replication
and attack configuration. No group, map seed, or variant from that group may
appear in more than one split. The Candidate J diagnostic maps remain
development-only. Final held-out map seeds and at least one held-out attack
configuration will be declared in a later accepted evaluation record and must
not guide calibration or detector design.

## Context and evidence

Decision 0012 completed the Phase 2A clean gate with Candidate J. The
full-input PPO policy exceeded the separately trained no-pheromone PPO on
stochastic mean food delivery by +31.25, +16.50 and +19.50 units for training
seeds 7, 17 and 27, and exceeded random action on each seed. That creates a
specific clean learned-policy basis for Phase 2B planning, but it does not
measure an attack, detector, dataset, held-out result or robustness.

The repository already contains the narrow persistent-attack and provenance
foundation defined in decision 0002. `AttackConfig` enforces a seeded,
episode-fixed compromised subset, occupied-cell-only nonnegative false-food
deposits, per-step and per-episode budgets, and the common cap/evaporation
mechanics. `matched_attack_configs` already constructs clean,
injection-disabled and attacked controls without revealing attacker identity or
attack events to policy inputs. The old fixture validates accounting, not
attack effectiveness against a learned Candidate J policy.

The current trajectory/evaluation components preserve the required information
boundary: local observations, own actions and own progress can form future
defense features, while compromised-agent identity, attack events and injected
mass remain simulator-only metadata. The existing timeout controller is a
baseline, not a detector. Candidate J's deterministic diagnostics were mixed,
so this calibration uses the same stochastic evaluation interpretation that
passed Phase 2A and records deterministic analysis only if separately
declared.

## Protocol detail

### Frozen clean reference

- Environment: `configs/phase2a/env/candidate_j_12x12_scout_follow_capacity.json`.
- Policies: completed `full` Candidate J checkpoints for training seeds 7, 17
  and 27, with their manifests, parameter hashes and source/config provenance.
- Development maps: diagnostic seeds 100, 101, 102 and 103 recorded in the
  matching Candidate J policy configurations.
- Policy input: the unchanged 58-value full local observation. Phase 2B does
  not add coordinates, global fields, attacker labels, attack timing or direct
  communication.

### Attack calibration conditions

| Condition | Injector | Purpose |
| --- | --- | --- |
| `clean` | None | Normal Candidate J reference. |
| `injection_disabled` | Same seeded attacker selection; `enabled=false` | Control for the episode-fixed compromised-agent designation without false mass. |
| `attacked` | Persistent, one compromised agent, request/step cap 1.0 and episode cap 20.0 | Measures the effect of bounded false-food pheromone. |

The calibration must record the actual compromised-agent count/fraction and
requested, budget-authorized and cap-applied mass. It must never infer an
attack effect merely because the requested amount is nonzero.

### Required development outputs

For every complete episode, write a fresh provenance-bearing artifact and an
episode summary. At minimum, retain:

- policy checkpoint digest, grid/attack configuration hashes, map seed,
  action-seed replication, scenario and group ID;
- total and honest food delivered, completed-task flag and world-step count;
- requested, authorized and applied injected mass, plus compromised fraction;
- local policy-visible trajectory records separate from simulator-only attack
  metadata; and
- failures/interruption status without silently dropping incomplete groups.

The primary paired attack metric is **injection loss**:

```text
injection loss = honest delivery(injection_disabled) - honest delivery(attacked)
```

Also report total delivery, paired clean-versus-disabled differences,
completion rate, episode length, and per-training-seed values. A negative,
zero or inconsistent injection loss is a valid result; it is not evidence that
the attack or detector succeeded.

### Split rules before detector data

1. Generate complete episodes first; never split individual rows/windows.
2. Give every policy/map/action-seed/attack-configuration family one stable
   group ID and put all of its clean, disabled and attacked variants in exactly
   one split.
3. Reserve unseen map seeds and at least one attack configuration for final
   testing before detector-window creation. Record their IDs and manifest hash
   in a later accepted held-out-evaluation record.
4. Fit any future scaler, classifier, threshold and mitigation setting only on
   training/validation groups. Do not derive features from attacker labels,
   global maps, attack timing or simulator-only metadata.

## Alternatives considered

- **Jump directly to detector fitting or a large trajectory dataset:** rejected.
  A detector dataset is not meaningful until the clean Candidate J reference,
  attack effect, controls and group-split contract are frozen.
- **Run decoy and intermittent attacks immediately:** deferred. The current
  code implements and tests only persistent injection. Adding a new attack
  capability changes the threat implementation and needs its own accepted
  decision and tests before it can be used in a comparison or held out.
- **Reuse a no-pheromone policy as the primary attacked policy:** rejected.
  It is a required baseline, but it cannot establish whether false pheromone
  harms the full-input Candidate J behavior because it does not consume those
  pheromone channels.
- **Treat attack metadata as detector input:** rejected. It would violate the
  local-observability boundary and make a detector result invalid.
- **Use the development map seeds as final test data:** rejected. They have
  already informed Phase 2A development and will inform attack calibration.

## Consequences and limits

This proposed decision authorizes only Phase 2B protocol implementation after
team acceptance: frozen-checkpoint verification, matched persistent-attack
rollouts, provenance/episode summaries, and group-level split manifests. It
does not yet authorize attack-strength selection beyond the initial calibration
setting, detector training, threshold selection, warning-channel mechanics,
decoy/intermittent attacks, held-out scoring or any robustness claim.

The 25% compromise fraction follows Candidate J's four-agent environment and
is reported explicitly; it must not be described as equivalent to the earlier
eight-agent 12.5% review fixture. The 20-unit episode cap is an initial,
auditable calibration setting, not a hidden hyperparameter search. Any later
change to attacker fraction, placement, budget, onset/timing, attack mode,
map split, policy, field mechanics or defense capability requires a new or
amended accepted decision record.

## Result

The approved calibration completed on pinned Linux Python 3.12.14 using the
three frozen Candidate J full-input checkpoints, diagnostic maps 100--103 and
stochastic action seed 7: 12 complete policy/map/action groups and 36 episodes
in `artifacts/phase2b/attack-calibration-run-001/`. Every attacked episode
applied the full 20.0-unit episode budget. Clean and injection-disabled
policy-visible records matched in every group, while disabled and attacked
episodes selected the same compromised agent.

The mean paired injection loss was -2.17 honest food units. Per-group losses
were zero for eight groups, +1 for one group and negative for three groups
(-2, -24 and -1). Thus this initial bounded persistent setting did not show a
consistent reduction in Candidate J delivery. It is a valid negative
development result: it neither proves the attack harmless in general nor
authorizes detector fitting, defense tuning, a dataset claim or robustness
claim. Any follow-up attack calibration needs its own written decision.

## Validation and context update

Before running the calibration, the implementation must validate the frozen
policy locations/hashes, map/action-seed assignments, attack settings and
split-manifest design. It requires focused tests for:

1. exact clean/injection-disabled policy-visible equivalence under a shared
   seed and action stream;
2. identical disabled/attacked compromised-agent selection;
3. occupied-cell placement, nonnegative mass, cap/evaporation interaction and
   per-step/episode budget accounting;
4. no leak of attacker IDs, labels, mass or global state into PPO or local
   feature inputs;
5. complete-group split disjointness, including all scenario variants; and
6. checkpoint/config/provenance validation and reproducible paired summaries.

Only after those tests and a completed calibration run may `docs/CONTEXT.md`
and `CHANGELOG.md` be updated with executed Phase 2B evidence. Preserve a
zero-effect or negative calibration result rather than creating a detector
dataset to force a positive outcome.
