# Decision Record: Phase 2B delayed persistent-attack calibration

**Status:** Completed; delayed persistent attack did not establish consistent
delivery degradation

**Date:** 2026-11-01

**Owners and reviewers:** Capstone team

## Decision

Run one further development-only calibration of Candidate J using the existing
persistent false-food attack, but delay its onset until after the first 200
completed environment transitions. Keep the four-agent task, one
episode-fixed compromised agent (25%), occupied-cell-only nonnegative deposits,
requested deposit 1.0, per-step budget 1.0, episode budget 200.0, shared field
cap/evaporation, three frozen full-input PPO checkpoints, maps 100--103,
stochastic action seed 7, and matched clean/injection-disabled/attacked
scenarios unchanged. The first deposit is permitted on transition 201.

## Context and evidence

The 20-unit persistent calibration exhausted its budget during the first 20
steps of an 1,100-step episode and did not establish degradation. Decision
0014 increased that same attack's cap to 200 units, and every attacked episode
used all 200 units, but the 12 matched groups still had mixed effects: two
positive, five zero and five negative losses (mean -0.42 honest units).

Starting false-food deposition at the first transition may influence initial
exploration rather than conflict with an already established pheromone route.
This follow-up tests that timing hypothesis without granting global placement,
negative mass, extra attackers, policy modification, a detector input, or a
new attack family. The delayed step count and attack events remain
simulator-only provenance.

The frozen clean checkpoints retain their parameter and policy-relevant source
checks. This calibration saves the current attack-source hash in its own
manifest but no longer requires it to equal the clean-training attack-source
hash: attack code is deliberately the experimental variable and clean training
ran with no injector. Environment, PPO adapter and training hashes must still
match the frozen checkpoint manifest.

## Alternatives considered

- Repeat the 200-unit immediate attack: rejected because it already produced a
  completed mixed-effect matrix.
- Increase attacker count or deposit intensity: rejected because either would
  change attack strength and confound the timing hypothesis.
- Add a decoy or intermittent attack: deferred; each changes the attack
  mechanics beyond timing and requires its own decision.
- Fit a detector to the existing runs: rejected because neither prior attack
  setting established reliable degradation.

## Consequences

Add a nonnegative integer `start_step` to the bounded persistent injector and
set it to 200 only in the new versioned attack plan. Before onset the injector
makes no request and records no deposit event; after onset its existing local
placement, cap, budgets and evaporation behavior are unchanged. Existing
configurations default to `start_step: 0` and preserve immediate behavior.

The resulting matrix remains development-only and groups complete clean,
disabled and attacked variants together. It does not create a detector dataset,
fit a defense, release a final split or establish robustness. A mixed or
non-degrading result is preserved as a negative calibration rather than tuned
away.

## Validation and context update

Run unit tests proving the injector produces no event/mass through transition
200 and begins at transition 201, while injection-disabled twins retain the
same attacker selection. Validate that plans reject an onset mismatch. Run the
focused Phase 2B/attack checks and the complete suite before the 36-episode
matrix. Verify its applied mass does not exceed 200, clean/disabled local
records match, disabled/attacked selection matches, and all 12 scenario
families remain whole in the development manifest. Update context and changelog
only with the executed outcome.

## Result

The fresh calibration completed on pinned Linux Python 3.12.14 in
`artifacts/phase2b/attack-calibration-persistent-delayed-200-run-001/`: 12
complete groups and 36 episodes. Focused attack/Phase 2B checks passed 23
tests and the complete suite passed 119. In every attacked episode the first
deposit event was transition 201 and the full 200.0-unit cap was applied;
clean and injection-disabled local records matched, disabled/attacked twins
selected the same compromised agent, and the group manifest kept each scenario
family together.

Mean paired honest-delivery injection loss was -2.25 units. Of 12 groups, one
was positive (+1), six were zero, and five were negative (-1, -1, -25, -1 and
-1). The delayed attack therefore did not establish consistent degradation and
is a third preserved negative development calibration. Do not fit a detector,
tune a defense, create the final dataset, or make a robustness claim from this
matrix. A further attack-mechanics change requires a new documented hypothesis
and decision.
