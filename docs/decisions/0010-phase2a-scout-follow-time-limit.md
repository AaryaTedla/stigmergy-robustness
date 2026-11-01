# Decision Record: Phase 2A scout-and-follow time-limit validation

**Status:** Completed; candidate did not pass the Phase 2A gate

**Date:** 2026-10-31

**Owners and reviewers:** Capstone team

## Decision

Run Candidate H, a time-limited validation of Candidate G. It keeps the same
12 by 12 map, four agents, distant seed-varying adjacent food cluster, 30 food
units per food cell, 2% evaporation, local inputs, PPO settings, full/no-
pheromone comparison, seeds and random reference. The only change is the
horizon: 700 steps instead of 1,100.

Candidate H retains the same strict advancement rule: full PPO must deliver
strictly more food than its separately trained no-pheromone PPO baseline and
the random reference on seeds 7, 17 and 27. This is a fresh training matrix,
not a post-hoc re-score of Candidate G.

## Context and evidence

Candidate G was the first environment with a consistent direction of evidence:
full PPO matched the 60-unit delivery ceiling on seed 7 and exceeded no-
pheromone PPO by 8.75 and 5.75 units on seeds 17 and 27. It also completed all
diagnostic episodes faster. The full/no-pheromone seed-7 delivery tie cannot
pass the existing gate, but it suggests a ceiling effect rather than a loss of
the coordination signal.

A shorter deadline tests one precise, useful question: when delivery speed
matters, does the same local scout-and-follow opportunity produce a reliable
full-pheromone delivery advantage? The 700-step horizon is near the observed
full-policy completion times (584.25, 691.00 and 621.00) and below all three
no-pheromone means (751.00, 1,023.25 and 813.25). This is an evidence-based
environment change, not an attempt to reinterpret the completed Candidate G
result.

## Alternatives considered

- Advance Candidate G after its tie: rejected because its written gate required
  a strict delivery win for every seed.
- Change the gate after seeing Candidate G's speed result: rejected as post-hoc
  evaluation.
- Change food amount, agents, layout and horizon together: rejected because
  Candidate G already identifies the useful structure.
- Keep the same scout-and-follow environment and shorten only its horizon:
  selected as a fresh, simple test of delivery before the time limit.

## Consequences

This remains clean Phase 2A development. It adds no attack, detector, dataset,
global input, reward shaping or communication. Phase 2B remains blocked unless
the complete Candidate H matrix passes the declared strict delivery gate.

## Result

Candidate H completed six PPO jobs and three random references in
`artifacts/phase2a/scout-follow-deadline-run-001/`. Its full-minus-no-
pheromone stochastic delivery was -51.50, -42.75 and +5.50 for seeds 7, 17 and
27. Full PPO delivered 0.00 on seeds 7 and 17, below both its no-pheromone
baseline and random movement; it beat both only on seed 27.

The shorter horizon did not turn Candidate G's speed difference into a stable
delivery benefit. Instead, it made full-pheromone training unstable at the
same 300,000-transition budget. Candidate H therefore fails the strict gate.
The completed result does not invalidate Candidate G's faster completions, but
it shows that a 700-step deadline is not a usable continuation environment.
Phase 2B remains blocked.

## Validation and context update

Confirm the plan resolves to one candidate, two modes and three seeds; run the
complete pinned Python 3.12 suite. Then run six fresh PPO jobs and three random
references in a new artifact directory, inspect completed manifests and paired
rows, and record the outcome without changing the gate. The complete suite
passed 103 tests before the completed matrix; the completed manifest and false
gate were checked before context and changelog updates.
