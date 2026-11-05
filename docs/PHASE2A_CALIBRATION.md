# Phase 2A: make learned pheromone coordination testable

## Why this phase comes before the dataset

The Phase 1 simulator and PPO pipeline are executable, but the most recent
eight-agent development evidence does not show that pheromone helps the learned
policy: clean and attacked mean delivery were equal, deterministic actions
delivered zero, and a frozen-policy channel-zeroing diagnostic slightly improved
sampled delivery. A large attack/detector dataset from that policy could not
support the capstone's central question. Phase 2A is a development-only gate:
it determines whether a clean learned task has a reproducible pheromone benefit
before attack calibration and trajectory generation begin.

## Results so far

The first 18-run matrix is complete. No candidate passed all three full versus
no-pheromone comparisons, so Phase 2B has not started. This does not mean
pheromone can never help. It means we do not yet have a reliable clean result.

Decision 0007 checked two simpler maps. They kept eight agents and the same PPO
comparison, but used smaller grids and more food at each food cell. The idea
was simple: more repeat trips might give useful trails more time to help.

That check is also complete. Candidate D was worse, better, then tied against
no-pheromone PPO across seeds 7, 17 and 27. Candidate E was better, better,
then worse. Both maps beat random actions, but neither map passed every
full-versus-no-pheromone comparison. Phase 2B still does not start and no
dataset is created.

Decision 0008 then tested one possible reason for the failure: perhaps food
trails faded before nearby agents could see them. Candidate F was exactly
Candidate E except that fields lost 2% per step instead of 10%. The local
exposure check showed that food trails were visible more often after this
change: 55.54%, 39.14% and 49.32% of stochastic local observations, versus
34.24%, 28.95% and 37.00% in Candidate E (seeds 7, 17 and 27). So the change
made food trails easier to see. It still did not make the benefit reliable:
full PPO was +2.75, +4.00 and -1.25 food units versus no-pheromone PPO. It
lost on seed 27, so Candidate F also failed the all-three-seed rule.

The useful conclusion is narrow: disappearing food trails were not the only
problem. We should not keep changing settings at random or start Phase 2B.
Any further Phase 2A test needs a new written decision that explains one clear
idea, keeps the comparison fair, and requires all three seeds again.

Decision 0009 then used a more targeted scout-and-follow task: four agents,
a distant food cluster that moves by map seed, enough food for repeated trips,
and slow fading. This was the closest result so far. Full PPO delivered all 60
food units on all three seeds. It tied no-pheromone PPO at the 60-unit maximum
on seed 7, then beat it by 8.75 and 5.75 units on seeds 17 and 27. It also
finished every seed faster. The strict delivery gate still failed because a tie
is not a win.

Decision 0010 tested the same task with a 700-step deadline, so the speed
advantage could appear as more delivered food. That did not work: full PPO
delivered 0.00 on seeds 7 and 17, while the no-pheromone policies delivered
51.50 and 42.75. It won only seed 27 by 5.50. The shorter deadline made full
training unstable at the current training budget. Candidate H is not a usable
environment, and Phase 2B remains blocked.

Decision 0011 doubled both models' training budget to 600,000 transitions on
the same 700-step task. This did not help: full PPO lost to no-pheromone PPO
on all three seeds by 50.75, 39.25 and 5.25 food units. More training time did
not stabilize the short version, so we should stop spending compute on that
environment. Candidate G remains the closest long-horizon result, but it has
not passed the delivery gate.

Decision 0012 then tested the one remaining documented explanation for
Candidate G's seed-7 tie: the 60-unit delivery ceiling could hide its faster
full-input completion. Candidate J retained Candidate G's four agents,
seed-varying distant cluster, 1,100-step horizon, 2% evaporation, PPO settings
and fair comparison, increasing only food capacity from 30 to 50 units per
patch. Its six PPO jobs and three random references are in
`artifacts/phase2a/scout-follow-capacity-run-001/`. Full-minus-no-pheromone
stochastic delivery was +31.25, +16.50 and +19.50 across seeds 7, 17 and 27,
and full input also beat random on every seed. Candidate J therefore passed
the strict development gate. Its deterministic diagnostics remain mixed, so
this authorizes Phase 2B planning from a stochastic clean-policy result; it is
not itself an attack, detector, dataset or robustness result.

## What remains fixed

- The existing PettingZoo `ResourceRetrievalEnv`, local 3-by-3 observation,
  shared delivery reward, food/home fields, nest, co-location, and field update
  order remain unchanged.
- PPO remains one parameter-shared 32-by-32 actor/local critic. It has no
  identity feature, global-state critic, direct communication, reward shaping,
  or attack training.
- All Phase 2A maps are development maps. They are not final dataset splits
  or final held-out maps.
- No attacks, detector labels, temporal windows, or timeout tuning are used in
  this phase.

## The fair comparison

Each candidate/seed has two independent training runs:

```text
full             58 local values, including food/home pheromone channels
no_pheromone     same 58-value shape, but the 18 local pheromone entries are
                  zero during both training and diagnostic evaluation
```

The latter is a distinct model, not the old post-training ablation. It keeps
visible food, nest, occupancy, boundaries, carrying, pickup, delivery, and
blocked state. Both models use the same environment candidate, training maps,
diagnostic maps, PPO settings, and seed. Compare it with a random-action
baseline on the same diagnostic maps as well.

## Candidate environments

| ID | Grid | Agents | Food per patch | Horizon | Rationale |
| --- | --- | ---: | ---: | ---: | --- |
| A | 12×12 | 8 | 6 | 500 | Moderate search distance and repeated retrieval. |
| B | 16×16 | 8 | 6 | 600 | Larger search space while retaining the same resource density. |
| C | 16×16 | 8 | 8 | 600 | Larger search space with more repeat trips to form/use trails. |

All candidates have two food patches and no obstacles or diffusion. This
isolates task difficulty and trail opportunity from changes to the mechanics.

## Run matrix

Run every row in the declared matrix—do not stop after a promising seed:

```text
3 environments × 3 PPO seeds (7, 17, 27) × 2 input modes = 18 fresh runs
```

Use the pinned Python 3.12 training stack. Example for candidate B/full/seed 7:

```bash
python -m stigmergy.cli train \
  --config configs/phase2a/env/candidate_b_16x16.json \
  --policy-config configs/phase2a/policy/full_seed_7.json \
  --output artifacts/phase2a/candidate-b/full-seed-7
```

For the paired baseline, substitute
`configs/phase2a/policy/no_pheromone_seed_7.json` and use a different fresh
output directory. The full run plan is machine-readable in
`configs/phase2a/calibration.json`.

To execute the complete fixed matrix, including a seeded random-action baseline
and aggregate `runs.csv`/`paired.csv` reports, use one fresh directory:

```bash
python -m stigmergy.cli phase2a-calibrate \
  --plan configs/phase2a/calibration.json \
  --output artifacts/phase2a/calibration-run-001
```

The command preserves failed per-run manifests and continues through other
declared runs. It reports a mechanical per-candidate gate flag but never selects
an environment automatically; team review is still required.

## Advancement gate

After all runs and the random baseline finish, make one development calibration
table with per-seed results for every candidate. A candidate may advance only
when the full-input model has a consistent same-seed advantage over both the
separately trained no-pheromone model and random actions on the declared
diagnostic maps. Report deterministic and stochastic results separately,
completed-task rate, delivered food, episode length, source/config hashes and
runtime. Preserve failures and negative results.

If none passes, stop. Do not generate the detector dataset or tune an attack
until the team creates a follow-up decision record explaining the next tested
change.
