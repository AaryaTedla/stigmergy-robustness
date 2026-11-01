# Decision Record: Phase 2A scout-and-follow environment

**Status:** Completed; close result, but did not pass the predeclared gate

**Date:** 2026-10-31

**Owners and reviewers:** Capstone team

## Decision

Run one new clean Phase 2A environment, Candidate G. It uses a 12 by 12 grid,
four agents, a 1,100-step horizon, 30 food units at each of two adjacent food
cells, and 0.02 evaporation. At reset, the two food cells form one distant
cluster outside the nest. The cluster location changes with the declared map
seed, so a policy cannot rely on one memorised food location.

Candidate G keeps the existing 3 by 3 local observation, parameter-shared PPO,
food/home fields, reward, no-pheromone baseline, training seeds (7, 17 and 27),
diagnostic map seeds, PPO budget and random-action reference. It adds only a
declared map-layout option that places the existing two food cells next to each
other and far from the nest. Explicit food-position test fixtures continue to
override this generated layout.

## Context and evidence

Candidates A through F show that PPO beats random movement, but they do not
show a reliable full-pheromone advantage. Candidate F established that slower
field fading makes food pheromone more visible locally, but it still lost one
of three fair comparisons. So fading is not the only issue.

With eight agents and two separate food cells, several agents can find food by
chance. The no-pheromone policy can therefore score well without using a trail.
Candidate G creates a simpler coordination opportunity: a small team starts at
the nest; a scout must find a distant, high-capacity food cluster; then other
agents have time to benefit from a trail left on the return route. The cluster
location still varies across maps, preserving the need for local discovery.

## Alternatives considered

- Start Phase 2B now: rejected because no clean three-seed benefit exists.
- Keep eight agents and only add more food: rejected because that has already
  been tested in Candidates D, E and F.
- Fix food at one permanent location: rejected because a no-pheromone policy
  could memorise the route instead of using local trail information.
- Add obstacles, larger observations, global coordinates, identity features,
  direct communication or reward shaping: rejected because each adds a new
  capability or makes the environment needlessly complex.
- Reduce the team to four and use a distant, seed-varying adjacent food cluster:
  selected. It is the smallest simple environment that directly creates a
  scout-and-follow opportunity without changing what an agent can observe.

## Consequences

This is still Phase 2A development work. It does not create attack, detector or
dataset artifacts and does not change attacker scope. Four agents are used only
to establish whether clean local pheromone coordination can be made reliable;
any later attack protocol must separately set and report a valid minority.

Candidate G passes only when full PPO beats both its separately trained
no-pheromone PPO baseline and the seeded random reference for seeds 7, 17 and
27. One good seed is not enough. The result must preserve deterministic and
stochastic delivery, completion, episode-length and provenance reports.

## Result

Candidate G completed all six PPO jobs and three random references in
`artifacts/phase2a/scout-follow-run-001/`. The full-policy stochastic delivery
advantage over no-pheromone PPO was 0.00, +8.75 and +5.75 for seeds 7, 17 and
27. Full PPO delivered all 60 available units on every seed and beat random
movement, whose means were 3.00, 1.75 and 2.25.

This is the closest clean result so far. Full PPO also completed every
diagnostic episode and used fewer mean steps (584.25, 691.00 and 621.00) than
the no-pheromone model (751.00, 1,023.25 and 813.25). However, seed 7 was a
delivery tie: both full and no-pheromone models reached the 60-unit maximum.
The predeclared mechanical gate requires a strict delivery win on every seed,
so Candidate G's gate is false. The tie must remain a non-passing result; it
cannot be reinterpreted after observing it.

## Validation and context update

Focused checks for generated distant adjacent food clusters, seeded replay,
fixture override, configuration validation and plan loading were added. The
complete pinned Python 3.12 suite passed 102 tests. The six PPO jobs, three
random references, completed manifest and false gate were checked before the
context and changelog were updated. Candidate G does not authorize Phase 2B.
