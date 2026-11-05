# Decision Record: Phase 2A scout-and-follow capacity validation

**Status:** Completed; passed the Phase 2A development gate

**Date:** 2026-11-01

**Owners and reviewers:** Capstone team

## Decision

Run Candidate J as one fresh Phase 2A development matrix. It retains Candidate
G's 12 by 12 grid, four agents, seed-varying distant adjacent food cluster,
1,100-step horizon, 0.02 evaporation, 3 by 3 local observation, PPO
architecture, 300,000-agent-transition budget, training seeds (7, 17 and 27),
diagnostic maps, random reference and full/no-pheromone baseline. The only
environment difference is food capacity: each of the two adjacent food cells
contains 50 units instead of 30.

The matrix is six independently trained PPO jobs (three seeds by two
observation modes) plus three seeded random-action references. It uses
`configs/phase2a/calibration-scout-follow-capacity.json` and writes to a new
artifact directory. Candidate J advances only if full input strictly exceeds
both its same-seed separately trained no-pheromone baseline and random action
on stochastic mean delivered food in every declared seed.

## Context and evidence

Candidate G was the closest prior clean result: full PPO had stochastic
delivery differences of 0.00, +8.75 and +5.75 against no-pheromone PPO, and
finished all diagnostic maps faster. Its seed-7 tie occurred at the 60-unit
maximum, so the strict delivery gate correctly remained false. Candidate H
showed that shortening the horizon to 700 steps destabilized full-input PPO;
Candidate I showed that doubling training on that short task did not solve the
instability. Neither short-horizon variant is repeated here.

Before this decision, frozen Candidate G full policies were replayed on their
own diagnostic maps with the genuine local observation and with only the local
food/home pheromone entries masked. For seeds 7, 17 and 27 respectively,
stochastic visible-observation mean action-distribution total variation was
0.272, 0.187 and 0.230; the most likely action changed on 25.1%, 19.9% and
18.7% of visible observations. These results are local input-sensitivity
evidence, not proof of causal coordination, but they rule out the narrow claim
that Candidate G's full policies were wholly insensitive to their pheromone
channels. The diagnostic reports are in
`artifacts/phase2a/action-sensitivity-candidate-g-seed-{7,17,27}/`.

Increasing capacity retains the long horizon that trained stably while making
the previously observed completion-speed difference less likely to be hidden
by a 60-unit ceiling. It does not add global information, direct communication,
identity, reward shaping, an attack, a detector feature or a new baseline.

## Alternatives considered

- Advance Candidate G after a ceiling tie: rejected because its written gate
  required a strict delivery win on all three seeds.
- Shorten the horizon again: rejected because Candidates H and I already gave
  stable negative evidence for that direction.
- Change PPO settings, reward, observation size and food capacity together:
  rejected because it would not isolate why the result changed.
- Increase only the two food cells from 30 to 50 units while retaining
  Candidate G's long-horizon structure: selected as the smallest capacity-only
  test of the documented ceiling explanation.

## Result

All six PPO jobs and three seeded random-action references completed in
`artifacts/phase2a/scout-follow-capacity-run-001/`. The full-input stochastic
delivery advantage over separately trained no-pheromone PPO was +31.25,
+16.50 and +19.50 food units for seeds 7, 17 and 27. Full input also exceeded
the paired random references by +97.00, +78.25 and +97.75 units. The
mechanical all-three-seed gate is therefore true.

The fresh full policies delivered 100.00, 80.00 and 100.00 units
stochastically, compared with 68.75, 63.50 and 80.50 for no-pheromone PPO;
random references delivered 3.00, 1.75 and 2.25. Deterministic diagnostics
remain mixed (full delivery 100.00, 0.00 and 60.00), so this result supports a
stochastic learned-policy claim only and does not establish deterministic
coordination. The root manifest records one interrupted invocation and the
fresh `-resume-1` replacements without overwriting partial artifacts.

The focused action-sensitivity and capacity-plan checks passed before the
matrix. The complete pinned Python 3.12.14 suite passed 107 tests after it.
The completed root manifest, six PPO rows, three random rows, three paired
rows and true gate were inspected before this record was updated.

## Consequences and limits

Candidate J meets Phase 2A's clean stochastic advancement condition and is the
designated learned-policy basis for Phase 2B planning. Phase 2B must still
declare its attack calibration, grouped map/episode splits, detector data,
baselines and held-out evaluation before any robustness claim. Preserve every
completed, failed and interrupted run; this development gate is not a final
robustness result.
