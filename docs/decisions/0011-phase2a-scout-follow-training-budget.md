# Decision Record: Phase 2A scout-and-follow training-budget validation

**Status:** Completed; candidate did not pass the Phase 2A gate

**Date:** 2026-10-31

**Owners and reviewers:** Capstone team

## Decision

Run Candidate I using the same 700-step scout-and-follow environment as
Candidate H. Keep its grid, four agents, seed-varying distant food cluster,
food amount, field settings, local observation, PPO architecture, seeds,
diagnostic maps, random reference and strict delivery gate unchanged. Increase
the training budget from 300,000 to 600,000 agent transitions for both the
full-input and separately trained no-pheromone PPO policies.

## Context and evidence

Candidate G showed a useful local-pheromone signal but hit a delivery ceiling
on one seed. Candidate H converted the same map to a 700-step delivery task,
but full-input PPO delivered zero on two seeds after 300,000 transitions. The
failure was training instability, not a simulator error: runs completed,
checkpoints passed their round trips, and the no-pheromone policies still
learned on the same maps.

The project contract permits extending training toward one million transitions
only when there is measured reason. Candidate G's two wins and faster full
completion, plus Candidate H's short-horizon instability, provide that reason.
Doubling the budget is a small, predeclared training-only test. It does not add
information, alter rewards, or change the environment again.

## Alternatives considered

- Start Phase 2B from Candidate G's near-result: rejected because its gate did
  not pass.
- Use Candidate H with the same 300,000-transition budget again: rejected
  because the completed result already shows two full-policy failures.
- Change the horizon, food, map layout and PPO settings together: rejected
  because it would hide whether additional learning time addresses the failure.
- Double both policy modes' budgets while retaining Candidate H exactly:
  selected as the smallest fair stability test.

## Consequences

This is clean Phase 2A work only. Both modes receive exactly the same extra
training budget; the no-pheromone baseline remains fair. Candidate I still
passes only with strict full-delivery wins over no-pheromone PPO and random
movement at seeds 7, 17 and 27. A longer run that does not pass remains a
negative result and does not authorize attacks, datasets or Phase 2B.

## Result

Candidate I completed all six 600,000-transition PPO jobs and three random
references in `artifacts/phase2a/scout-follow-stability-run-001/`. Full-minus-
no-pheromone stochastic delivery was -50.75, -39.25 and -5.25 for seeds 7, 17
and 27. Full PPO lost to the no-pheromone model on every seed; it delivered
zero on seed 7, 13.25 on seed 17, and 45.00 on seed 27.

Doubling the budget did not fix the short-horizon full-input instability. This
rules out the narrow explanation that Candidate H only needed more learning
time at the unchanged PPO settings. Candidate I fails the gate; do not spend
more compute repeating this 700-step configuration or start Phase 2B.

## Validation and context update

Add a plan check that confirms the Candidate H environment and the 600,000
transition policy configurations are used for both modes. Run the complete
pinned Python 3.12 suite. Then execute six fresh PPO jobs and three random
references in a new artifact directory; inspect manifests, paired rows and the
gate before recording the result in context and the changelog.

The plan check and complete suite passed 104 tests before the completed matrix.
The completed manifest, all nine aggregate rows and false gate were checked
before context and changelog updates.
