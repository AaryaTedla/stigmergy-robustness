# Decision Record: Phase 2A learned-stigmergy calibration contract

**Status:** Completed; no candidate passed the advancement gate

**Date:** 2026-10-31

**Owners and reviewers:** Capstone team; Phase 2A owner to be assigned before experiment execution.

## Decision

Before generating attack, detector, or temporal-window data, run a development-only
calibration over three declared eight-agent environments. For every candidate and
each of three training seeds, train one parameter-shared PPO model on the ordinary
58-value local observation and a distinct parameter-shared PPO model whose food-
and home-pheromone inputs are zero during both training and diagnostic evaluation.
The no-pheromone model retains every other local input and has the same architecture,
PPO settings, maps, seed, and transition budget as its paired full-input run.

No candidate is automatically accepted. The team must preserve every completed,
failed, and interrupted run. A candidate may proceed to attack calibration only if
the full-input models consistently outperform their same-seed separately trained
no-pheromone models and a declared random-action baseline on the development
diagnostic maps. This is a development decision only; it does not create final
map splits, fit a detector, or authorize held-out evaluation.

## Context and evidence

Decision 0005's latest eight-by-eight development run completed mechanics and PPO
pipeline checks, but it did not establish useful pheromone coordination. Its
stochastic clean and attacked means were both 7.6667 delivered units, deterministic
delivery was zero, and zeroing pheromone channels on the frozen model slightly
increased stochastic delivery to 8.0. The implemented timeout baseline delivered
zero in all variants. The frozen-model channel-zeroing diagnostic measures input
sensitivity only; it is not a fair no-pheromone policy baseline. Therefore using
those trajectories as a detector dataset would not yet support the intended claim.

The candidate grids in `configs/phase2a/env/` increase search distance and/or the
number of repeated retrieval trips while preserving the verified simulator mechanics:
two resource patches, a top-left two-by-two nest, local 3-by-3 sensing, shared
reward, co-location, food/home fields, bounded nonnegative attack model, and no
obstacles or diffusion. `configs/phase2a/calibration.json` records the complete
development-only candidate/seed/mode matrix.

## Alternatives considered

- Generate detector data from the current eight-by-eight review checkpoint:
  rejected because no pheromone advantage or injection-induced degradation has
  been demonstrated.
- Reuse a full-input checkpoint while zeroing fields only at evaluation:
  rejected as the no-pheromone baseline because it is an input distribution shift.
- Replace the PettingZoo simulator or add obstacles/diffusion immediately:
  deferred. It would confound the current failure diagnosis and invalidate
  comparison with the verified mechanics.
- Change rewards, introduce a global critic, identities, or direct messaging:
  rejected because each would violate the current study contract.

## Consequences

Training artifacts must record `observation_mode` and use fresh output directories.
The no-pheromone transform applies only to a copied policy-input batch; it does not
change environment observations, simulator arrays, trajectory logs, defense inputs,
or attack capability. Existing historical checkpoints are not baseline evidence.

The completed run contains 18 PPO rows, nine random-action rows and nine paired
rows in `artifacts/phase2a/calibration-run-001/`. Candidates A, B and C all
failed the strict three-seed gate: A and B lost the full-versus-no-pheromone
comparison at seed 17; C tied at seed 17 and lost at seed 27. This is a
development-only negative result, not a conclusion that pheromone cannot help.

Phase 2B may begin only after a documented review of the calibration table. Since
no candidate passed, preserve the result and open a new decision record before
changing field semantics, observation size, rewards, map generation, policy
architecture, or attacker behavior.

## Validation and context update

Before treating the implementation foundation as verified, run the full training
stack tests plus focused transform checks on the pinned Python 3.12 environment.
Then execute all 18 declared runs (three candidates × three seeds × two input modes),
record a matched random baseline, verify fresh-output/provenance requirements, and
publish a development-only calibration summary. Update `docs/CONTEXT.md` and
`CHANGELOG.md` only with executed results, including negative or failed runs.
