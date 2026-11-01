# Decision Record: Phase 2A local exposure check and slow evaporation test

**Status:** Completed; candidate did not pass the Phase 2A gate

**Date:** 2026-10-31

**Owners and reviewers:** Capstone team

## Decision

First measure how often the already trained full-input PPO policies can see a
nonzero food or home pheromone value in their own local 3 by 3 observation.
Then run one more clean Phase 2A candidate. It is the same as the simple 12 by
12 repeat-trip map (Candidate E), except evaporation changes from 0.10 to 0.02.
This means that 98% of a field value remains after a step instead of 90%.
Everything else stays fixed: eight agents, local observations, PPO model,
rewards, food amount, maps, seeds, full/no-pheromone baseline and random check.

## Context and evidence

The first five clean maps all beat random movement often enough to show that PPO
can learn the basic task. They did not show a stable pheromone benefit. The full
policy sometimes won, tied, or lost against the separately trained
no-pheromone policy depending on seed. The current local view is only 3 by 3
cells and the field fades by 10% per step. A trail may disappear before another
agent gets close enough to see it. The exposure check tests this idea using only
the exact local values already given to the policy; it adds no privileged input.

## Alternatives considered

- Start attacks or make a dataset now: rejected because clean trail use is not
  reliable yet.
- Change rewards, give global positions, identities, or direct communication:
  rejected because these change the research question.
- Change map size, food, reward and evaporation together: rejected because we
  would not know which change caused a result.
- Lower evaporation and keep all other Candidate E values fixed: selected as
  the smallest test of whether short-lived trails are the bottleneck.

## Consequences

This changes a field-mechanics setting only for one new development candidate.
It does not change the attacker, add an attack, alter policy input shape, create
a dataset, or authorize Phase 2B. The exposure report is simulator diagnostic
output; its per-agent calculations use only the same local observation that the
policy sees. The candidate passes only if full PPO beats both no-pheromone PPO
and random action for seeds 7, 17 and 27. A single good seed is not enough.

## Result

The local exposure reports completed for the three earlier Candidate E full
policies. During stochastic diagnostic play, food pheromone was nonzero in the
agent's local view 34.24%, 28.95% and 37.00% of the time for seeds 7, 17 and
27. Home pheromone was already visible almost all the time, so this check keeps
food and home values separate.

Candidate F completed its six PPO runs and three seeded random references in
`artifacts/phase2a/slow-evaporation-run-001/`. Lowering evaporation did what
this check was meant to test: food pheromone was locally visible 55.54%,
39.14% and 49.32% of the time for the three full policies. This shows that
slower fading made food trails more available in the local input. It does not,
by itself, show that the policy used them well.

The full-policy stochastic delivery advantage over its separately trained
no-pheromone policy was +2.75, +4.00 and -1.25 food units for seeds 7, 17 and
27. Full PPO beat random action on all three seeds, but it lost to its fair
no-pheromone comparison on seed 27. The automatic gate is therefore false.
Candidate F does not establish a reliable clean pheromone benefit, and Phase
2B remains blocked.

## Validation and context update

Focused unit tests for local exposure and the slow-evaporation plan were added.
The complete Python 3.12 test suite passed 99 tests. The exposure diagnostics,
complete six-PPO/three-random matrix, completed manifest, paired report and
false gate were then checked before the context and changelog were updated.
