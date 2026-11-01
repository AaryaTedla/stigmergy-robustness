# Decision Record: Phase 2A simpler repeat-retrieval environments

**Status:** Completed; neither simple environment passed

**Date:** 2026-10-31

**Owners and reviewers:** Capstone team

## Decision

Run one more clean Phase 2A check using two simple eight-agent environments.
Candidate D uses a 10 by 10 grid with eight food units at each of two food
cells. Candidate E uses a 12 by 12 grid with ten food units at each food cell.
Both retain the existing nest, local 3 by 3 view, PPO model, pheromone rules,
training maps, diagnostic maps, three seeds, and full/no-pheromone comparison.
The only changes are grid size, food amount, and episode length. We will use the
same strict three-seed rule before any Phase 2B work starts.

## Context and evidence

The first Phase 2A matrix completed, but none of its three environments passed
the rule. Full pheromone input helped in several runs, so it is worth checking a
simpler task before changing the model or the pheromone rules. The new grids are
small enough to learn within the current CPU budget, but they include enough
food for repeated trips. Repeated trips give trails a fair chance to help other
agents find a food cell after it has been discovered.

## Alternatives considered

- Start attacks, datasets, or detector training now: rejected. The clean
  pheromone benefit is still not reliable.
- Change rewards, add global information, add identity, or add communication:
  rejected. These would make the task less local and change the research scope.
- Change many things at once: rejected. We need to know whether a simpler map
  and more repeated trips are enough before making a larger change.

## Consequences

This is still clean development work. There are no attacks, detector labels,
trajectory windows, timeout changes, final maps, or held-out results. The
existing first matrix remains valid and is not replaced.

The complete follow-up run is stored in
`artifacts/phase2a/simple-repeat-run-001/`. Candidate D was worse with
pheromone at seed 7, better at seed 17, and tied at seed 27. Candidate E was
better at seeds 7 and 17, but worse at seed 27. Both candidates beat random
actions, but neither beat the trained no-pheromone policy on all three seeds.
Both advancement flags are false. We therefore stop again and need a new small
clean-learning decision before trying another change.

## Validation and context update

First check that both new JSON environment files resolve through the Phase 2A
runner and that the full test suite passes. Then run every row in the new
two-candidate matrix: 2 candidates × 3 seeds × 2 modes = 12 PPO runs, plus six
seeded random references. Preserve all artifacts, including failures. Update
the context and changelog only after the full matrix completes.
