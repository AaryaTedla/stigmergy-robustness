# Decision Record: Phase 2B bounded persistent-attack duration follow-up

**Status:** Completed; longer bounded duration still did not establish
consistent delivery degradation

**Date:** 2026-11-01

**Owners and reviewers:** Capstone team

## Decision

Repeat the completed Phase 2B Candidate J persistent-attack calibration while
changing only the false-food episode budget from 20.0 to 200.0 field units.
Keep four agents, one episode-fixed compromised agent (25%), occupied-cell-only
nonnegative deposits, requested deposit 1.0, per-step budget 1.0, shared field
cap/evaporation, three frozen full-input PPO checkpoints, diagnostic maps
100--103, stochastic action seed 7, and matched clean/injection-disabled/
attacked scenarios unchanged.

The new cap allows at most 200 attack-active steps rather than exhausting after
20 of the 1,100-step horizon. It remains bounded, local and auditable; it does
not add delayed onset, global writes, negative mass, policy modification or a
new attack family.

## Context and evidence

Decision 0013's initial calibration completed 36 development episodes and
applied its full 20-unit attack budget in every attacked episode. Because the
per-step cap was 1.0, injection stopped after roughly the first 20 steps of an
1,100-step task. Mean paired injection loss was -2.17 honest food units, with
eight zero-effect groups, so the result did not establish degradation.

This follow-up tests the narrow duration explanation without changing the
policy, maps, selection, attack placement, field dynamics, controls or
measurement. It is not an attempt to force a negative result: zero, positive
or inconsistent loss remains valid evidence.

## Alternatives considered

- Increase attacker count: rejected because it changes the 25% compromise
  fraction as well as duration.
- Increase per-step mass: rejected because it changes local intensity and cap
  saturation behavior as well as duration.
- Add delayed onset, decoy, intermittent injection or a detector: deferred;
  each needs its own threat-model decision and implementation checks.
- Reuse only a favourable group: rejected; run the full three-policy,
  four-map matrix again.

## Consequences

Use `configs/attack/persistent-phase2b-200.json` and
`configs/phase2b/attack-calibration-persistent-200.json` with a new artifact
directory. Preserve the original 20-unit calibration and report per-group as
well as mean injection loss. Detector fitting, defense tuning, final split
assignment and robustness claims remain out of scope unless this follow-up
produces a separate documented basis for their planning.

## Validation and context update

Run the focused Phase 2B tests and complete suite before execution. Verify
that every attacked episode applies no more than 200 units, that clean and
disabled local records match, that disabled/attacked attacker selection matches
and that all 12 groups remain whole in the development split manifest. Update
the context and changelog only with the executed result.

## Result

The follow-up completed on pinned Linux Python 3.12.14 in
`artifacts/phase2b/attack-calibration-persistent-200-run-001/`: 12 complete
groups and 36 episodes. Every attacked episode applied the full 200.0-unit
episode budget. Clean and injection-disabled policy-visible records matched,
disabled/attacked twins selected the same compromised agent, and the group
split manifest preserved every scenario family together.

Mean paired injection loss was -0.42 honest food units. Of 12 groups, two
were positive (+1 and +27), five were zero and five were negative (-4, -1,
-24, -3 and -1). The increased duration therefore changed the trajectories
but did not produce a consistent attack effect. This is another valid negative
development result. Do not fit a detector or claim robustness from it; a new
documented hypothesis is required before another attack change.
