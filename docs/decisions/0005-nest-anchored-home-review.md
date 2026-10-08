# Decision 0005: nest-anchored home deposits and eight-agent diagnostics

Status: Accepted for implementation; measured verification recorded separately.
Date: 2026-10-09
Authorization: Aarya's explicit implementation plan.

Empty agents inside the nest deposit the ordinary amount. Outside it, only
successful movement deposits home pheromone: deposit × 0.95^counter, where
counter counts successful movements outside the nest since its last visit.
Every visit resets the counter, including carrying visits. Waiting and blocked
movement outside deposit nothing. Movement is counted before pickup/delivery;
the resulting carrying state still chooses the deposit channel. Carrying food
deposits remain unchanged. Common clipping and evaporation remain unchanged.
This anchors home deposits to nest visits without guaranteeing a monotonic
gradient when trails overlap. It corrects the old stationary home hotspot.

Keep old artifacts and two-agent configurations. Add an explicit 8×8, eight-
agent development configuration with one selected productive attacker (12.5%).
No attack capability, budget, reward, observation shape, timeout threshold or
dataset split changes. Historical checkpoints cannot validate new mechanics.

Run fresh 4,096-transition smoke and 300,000-transition seed-7 PPO training
with existing network/optimizer settings, maps 0–15 and diagnostics 100–103.
Training plus comparisons share a 30-minute wall-clock budget. Preserve partial
artifacts as incomplete; compare only completed validated checkpoints. Six
matched scenarios use stochastic action seeds 7/8/9; deterministic seeds are
deduplicated because argmax actions do not use sampling RNG (96 episodes).
A separate frozen-policy clean observation ablation zeros both pheromone
channels. It measures sensitivity, not a separately trained no-pheromone baseline.

Render actual scripted states at steps 0/10/20/final and an explicit waiting
diagnostic. Plot delivery histories, team/honest counts with episode points,
requested/applied mass, and matched local observation changes. Report all
outcomes without map/budget selection or robustness promises. Twelve-page
handbook and slide notes must distinguish mechanics from learned evidence.

Validate counter/reset/deposit rules, unchanged food/reward/locality/attack
accounting, full pinned Python 3.12 tests, repeated seeded fixtures, checkpoint
reload, matched clean/disabled equality, and N/k/fraction provenance. Update
context/changelog only after checks. Final held-out tests, multiple training
seeds, learned detector and required baselines remain future work.

## Verified development outcome

Linux Python 3.12.14: 83 tests and pinned package compatibility checks passed.
Fresh smoke/main runs, reload checks, 96 matched episodes and 16 ablation
episodes completed within 161.5 seconds. Main actual count is 300,032 agent
transitions. Stochastic seed-7 four-map mean changed 6.25 to 7.00; deterministic
delivery remains zero. Across three stochastic action seeds, clean/disabled/
attacked team means are equal at 7.6667, timeout means zero. Honest injection
loss is -.1667 and timeout gain -6.5833; recovery undefined in 15/16 groups
(one defined value -6). Zeroed-input stochastic mean is 8 versus 7.6667 full.
Input sensitivity is measured but beneficial trail coordination is unverified.
Repeated scripted clean/disabled arrays match, selected IDs match, and eight
units are delivered at step 23. The new-mechanics waiting fixture decays rather
than accumulating home. Saved old artifacts are preserved. This accepts the
mechanics correction and executable diagnostics, not robustness claims.
