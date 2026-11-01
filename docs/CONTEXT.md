# Project Context

## Purpose and authority

This is the agent-readable source of truth for the capstone. It consolidates the finalized documents while preserving the difference between established literature, design commitments, and unimplemented plans.

Authoritative source documents:

- [Refined one-pager](reference/capstone_refined_one_pager.docx)
- [Project proposal](reference/capstone_project_proposal.docx)
- [Internal implementation handbook](reference/capstone_internal_implementation_handbook.docx)

If this file conflicts with those documents, stop and create a decision record before changing the scope or claim.

## Verified research framing

### Central question

Can a lightweight defense using local pheromone history and an agent's own task progress improve cooperative learned-policy performance under minority pheromone-injection attacks, including attack conditions withheld during development, without substantially reducing clean-task performance?

### What prior work already establishes

*Hacking the Colony* establishes misleading food-pheromone attacks, minority disruption, and a cautionary-pheromone mitigation in simulated ant foraging. Learned stigmergic coordination also exists. Therefore, this project must not claim that fake pheromone, a small malicious minority, cautionary pheromone, or swarm disruption is itself novel.

The candidate contribution is a reproducible evaluation of learned stigmergic policies and lightweight local defenses under controlled attack, map, and timing shifts. Novelty and publication suitability remain conditional on evidence from the final protocol.

### Dataset finding

The reviewed sources did not establish a ready-made public standardized dataset matching the full protocol: cooperative learned policies using a shared stigmergic field under minority pheromone injection, with clean, attacked, and defended trajectories. This is a qualified search finding, not proof that no such dataset exists.

Distinguish source code, benign physical/simulation datasets, literature corpora, and generated attack trajectories. The project will generate versioned clean, attacked, and defended trajectories and label simulator-only metadata separately from model-observable inputs.

## Design commitments

These are agreed implementation requirements, not proof that code already exists.

### Environment

- Use simulated cooperative resource retrieval, not hardware deployment or real-world validation.
- Start with a small 2D grid using Python, NumPy, and the PettingZoo parallel interface.
- Use food and home pheromone channels, local sensing, explicit movement rules, bounded deposits, deterministic seeded execution, evaporation, and optional diffusion.
- Specify update order, boundary behavior, pickup, delivery, collisions, resource depletion, and field clipping in tested code.
- Start from a 16 by 16 grid, eight agents, 500-step horizon, two by two nest, and two resource patches; simplify before increasing compute if learning is unreliable.

### Policies

- Include a rule-based policy for debugging and deterministic fixtures.
- Train a small parameter-shared PPO policy with decentralized observations. Learned-policy training is mandatory for the capstone's learned-policy claims.
- Use a CPU-first curriculum: 8 by 8/two agents, then 12 by 12/four agents, then 16 by 16/eight agents. Start near 300,000 agent transitions per seed and extend toward one million only with measured improvement.
- A rule-based-only result may document mechanics but is an incomplete learned-policy milestone.

### Threat model

- At episode start select `k` compromised agents and keep the set fixed. The pilot starts with `N=8`, `k=1` or `2`; always report count and fraction.
- Attackers may submit bounded, nonnegative false-food deposits after legal movement, only at their actual occupied positions.
- Implement persistent false deposition, decoy trails, and intermittent deposition. Use per-step and per-episode budgets and record requested versus applied mass.
- Exclude trail erasure, negative deposits, privileged global writes, reward tampering, policy modification, and detector manipulation from the primary threat model.
- Apply the same field transport, decay, diffusion, and cap to honest and malicious deposits.
- Include all-honest clean, injection-disabled twin, and attacked controls. Separate pheromone-injection effects from reduced productive-worker effects.

### Local defense and baselines

- Build local temporal features from observable pheromone changes, revisitation, and each agent's own pickup, delivery, and blocked-movement history.
- Begin with logistic regression and a small random forest; select detector, threshold, and mitigation on validation data only.
- Use the selected score to reduce reliance on suspicious food pheromone and add bounded local exploration. Keep detector inputs local and agent-specific.
- Compare with: undefended pheromone coordination; separately trained no-pheromone policy; local patience/timeout heuristic; explicitly documented adaptation of cautionary pheromone.
- Do not compare directly with approaches requiring extra identity data, direct messaging, voting, or blockchain reputation unless their extra capability is explicitly modelled and justified.

### Data and evaluation

- Split complete episodes and map seeds before creating temporal feature windows. Keep related clean, control, attacked, and defended variants in one split group.
- Use development maps for policy/detector training and validation; reserve unseen maps and attack configurations for final evaluation.
- Include benign saturation, congestion, and resource depletion as false-alarm controls.
- Prioritize honest food delivered, injection-induced degradation, recovery, and clean-task cost. Supplement with precision-recall measures, false alarms, alarm delay, and runtime.
- Report training-seed variability separately from evaluation-episode variability. Preserve failed runs and explain exclusions.

## Current verified repository state

- Latest verified milestone: Candidate J completed Phase 2A's capacity-only
  scout-and-follow validation on Linux Python 3.12.14. With Candidate G's
  long-horizon task unchanged except for 50 rather than 30 units per food
  patch, full-input PPO beat separately trained no-pheromone PPO on all three
  stochastic development comparisons by +31.25, +16.50 and +19.50 delivered
  units (seeds 7/17/27), and beat random action in every pair. The mechanical
  gate is true, so Candidate J is ready for Phase 2B planning. Deterministic
  diagnostics remain mixed, and this is only clean development evidence—not
  an attack, detector, dataset, held-out evaluation or robustness result. See
  decision 0012 and the 2026-11-01 entry below. Earlier negative results
  remain historical evidence and must not be read as the current gate state.

- A clean grid environment and scripted mechanics demo are implemented and verified; see the implementation entry below.
- A first local-defense foundation exists in `src/stigmergy/defense.py`: agent-local temporal features and a deterministic timeout baseline. Eight focused checks initially passed via an isolated Python 3.12 import. Those checks now also pass through the installed package in Shashannk's 61-test full-stack suite, including initial-observation timing. This component checkpoint was subsequently integrated into the development comparison pipeline recorded below; robustness remains unverified.
- A first attack/provenance foundation exists in `src/stigmergy/attacks.py` and `src/stigmergy/trajectories.py`: one persistent bounded nonnegative false-food injector, seeded episode-fixed attacker selection, per-step/episode accounting, injection-disabled twins, and JSONL local-observation trajectory records with separate simulator-only labels. CPython 3.14.4 with the locked dependencies passed all 46 tests; seed-7 scripted clean, disabled, and attacked fixtures each delivered eight units in 89 steps, and clean/disabled policy-visible records matched. These are mechanics/accounting checks only; PPO development rollouts were subsequently integrated below. CPython 3.11 revalidation, attack effectiveness, data splits and the full research comparisons remain unverified.
- A clean parameter-shared PPO pipeline and local-observation debugging controller are implemented. Windows CPython 3.12.10 with the pinned CPU training stack passed 61 tests, editable installation and dependency checks. Two 4096-transition seed-7 development runs matched summaries/parameter hashes and passed checkpoint reload. Deterministic mean deliveries remained zero; seeded stochastic mean deliveries changed from 1.75 to 3.75 on four development maps. This verifies pipeline execution, not useful learning, pheromone reliance or robustness. Python 3.11 revalidation and longer/multiple-seed training remain pending; see the implementation entry and Shashannk walkthrough.
- Short-run initial/final checkpoints exist only in ignored local artifacts. No detector, split trajectory dataset or research benchmark result exists. Persistent attack mode is the sole implemented mode; decoy and intermittent modes remain future work.
- The files in `docs/reference/` are finalized project documents copied into this repository as canonical references.
- The JSON demo, fixture recorder, local debug policy and clean PPO train and development comparison commands are runnable with their documented dependencies. Evaluation/dataset commands beyond development diagnostics remain planned.
- Phase 2A's `phase2a-calibrate` command now supports a plan-validated
  `--resume` mode. It reuses manifest-recorded PPO rows, preserves a partial
  training directory and uses a fresh `-resume-N` sibling for its replacement;
  it rewrites only derived aggregate reports. This is execution recovery, not
  a change to the environment, baseline, or evaluation protocol.

## Project roadmap

| Phase | Weeks | Required outcome |
| --- | --- | --- |
| Executable pilot | Weeks 1-8 | Runnable simulator, trained shared policy, attacks, logging, local-defense pilot, and reproducible release; completion target week 7 with week-8 buffer |
| Research refinement | Weeks 9-12 | Audited mechanics, stronger baselines, frozen evaluation protocol, and literature update |
| Main experiments | Weeks 13-17 | Held-out evaluation, ablations, uncertainty estimates, and failure analysis |
| Publication and final release | Weeks 18-22 | Manuscript, reproducibility audit, and demonstration; primary submission target weeks 20-22 |

Early gates: clean simulator by week 2; trained-policy/attack/logging evidence by week 4; local-defense pilot and comparisons by week 6; reproducible release by week 7.

## Team rotation

For name-based first-review continuation, follow [the team milestone and handoff plan](FIRST_REVIEW_PLAN.md). It defines the Aarya → Shashannk → Rohan → Tusti sequence and user-controlled commit/merge checkpoints; its targets are planned work, not completed evidence.

Initial owners: Aarya—environment and pheromone mechanics; Shashannk—policies and training; Rohan—attacks and trajectories; Tusti—local defense and evaluation.

Rotate in later phases so every teammate owns each subsystem, reviews another subsystem, reads anchor papers, runs experiments, and contributes to writing. Initial review cycle: Shashannk reviews Aarya, Rohan reviews Shashannk, Tusti reviews Rohan, and Aarya reviews Tusti.

## Evidence required before context changes

Use this protocol after implementation begins:

1. A code or configuration change must have a focused purpose that advances the agreed project.
2. Relevant automated tests, deterministic fixtures, or reproducible experiment checks must pass. Record configuration, seed, revision, and observed result.
3. A decision record is required before accepting a change to environment mechanics, observation/action semantics, threat capability, split rules, baseline capability, evaluation criteria, or contribution claim.
4. Update this file with only verified facts. Identify the changed component, evidence, and material limitation. Keep unverified work in a planned or open-question section.
5. Add the same verified milestone or correction to `CHANGELOG.md`.

Do not update the context merely because code was drafted, a test was skipped, an experiment produced an unexplained result, or a change makes results look stronger. Preserve negative and incomplete outcomes.

## Future implementation records

When code exists, append concise entries under these headings instead of rewriting history:

### Implemented and verified

2026-11-01 — Phase 2A's capacity-only Candidate J validation
(`action_sensitivity.py`, `phase2a_action_sensitivity.py`,
`candidate_j_12x12_scout_follow_capacity.json`,
`calibration-scout-follow-capacity.json`, decision 0012) completed on pinned
Linux Python 3.12.14. A local-only frozen-policy diagnostic first found that
Candidate G's full policies changed their stochastic action distributions when
only local pheromone entries were masked (visible-observation mean total
variation 0.272/0.187/0.230 across seeds 7/17/27). Candidate J then retained
that long-horizon scout-and-follow task and changed only food capacity from 30
to 50 units per patch. Its six fresh PPO jobs and three seeded random
references are in `artifacts/phase2a/scout-follow-capacity-run-001/`.
Full-minus-no-pheromone stochastic delivery was +31.25/+16.50/+19.50 and
full-minus-random was +97.00/+78.25/+97.75, so the predeclared strict gate is
true. The timeout-interrupted initial invocation was preserved; a
plan-identical resume recorded fresh `-resume-1` outputs without overwriting
partial artifacts. The complete suite passed 107 tests. Candidate J is the
clean learned-policy basis for Phase 2B planning, but its deterministic
diagnostics were mixed and no attack, detector, dataset, held-out evaluation
or robustness claim exists yet.

2026-10-31 — Phase 2A learned-stigmergy calibration (`calibration.py`,
`observations.py`, `configs/phase2a/`, decision 0006) completed on pinned
Linux Python 3.12.14. The fixed development-only matrix contains three
eight-agent candidates, three PPO seeds (7/17/27), and full versus separately
trained no-pheromone 58-value policies: 18 PPO runs, plus nine seeded random
references, all evaluated on diagnostic maps 100–103. The ignored artifact
`artifacts/phase2a/calibration-run-001/` contains 27 report rows and nine
same-seed paired rows. Candidate A full-minus-no-pheromone stochastic delivery
was +2.50, -12.00 and +1.75; B was +8.50, -1.75 and +2.75; C was +6.75,
0.00 and -0.25. Although full input beat random in most pairs, each candidate
failed the required strict all-three-seed full-over-no-pheromone gate; all
three mechanical gate flags are false. The matrix therefore does not establish
beneficial pheromone coordination and explicitly blocks Phase 2B attack,
detector, trajectory-dataset and held-out robustness work pending a new team
decision. A process interruption was preserved and resumed without overwriting
the partial output. Focused calibration/observation/training checks (24) and
the complete suite (95) passed. All results are development-only, use a dirty
working tree with per-run provenance, and have no uncertainty estimate or
final-split relevance.

2026-10-31 — A simpler Phase 2A follow-up (`calibration-simple-repeat.json`,
`candidate_d_10x10_repeat.json`, `candidate_e_12x12_repeat.json`, decision
0007) also completed on Linux Python 3.12.14. It kept the same eight agents,
PPO, local inputs, three seeds and fair full/no-pheromone training. It only
made the map smaller and added more food so agents could make more repeat
trips. The 12 PPO runs and six random references are in
`artifacts/phase2a/simple-repeat-run-001/`. Candidate D full-minus-no-pheromone
delivery was -0.25, +2.00 and 0.00; Candidate E was +2.75, +5.00 and -0.50
(seeds 7/17/27). Both maps beat random actions, but neither passed the strict
all-three-seed rule. This is another useful negative clean result: do not make
the Phase 2B dataset or start attack/detector work yet. The simple-plan check
and full suite passed 96 tests before the run; outputs have completed manifests
and preserved provenance.

2026-10-31 — The Phase 2A slow-evaporation check (`exposure.py`,
`phase2a_exposure.py`, `candidate_f_12x12_slow_evaporation.json`,
`calibration-slow-evaporation.json`, decision 0008) completed on Linux Python
3.12.14. It changed only Candidate E's evaporation from 0.10 to 0.02, then ran
six new full/no-pheromone PPO jobs and three random references. The local-only
exposure diagnostic showed more stochastic food-trail visibility for Candidate
F than Candidate E: 55.54/39.14/49.32% versus 34.24/28.95/37.00% for seeds
7/17/27. This confirms that slower evaporation made food values more available
in local observations; it does not prove policy use. Candidate F full-minus-
no-pheromone delivery was +2.75, +4.00 and -1.25, while full PPO beat random
on all three seeds. Because it lost the fair comparison on seed 27, the gate
is false. The complete Python 3.12 suite passed 99 tests before this completed
matrix. This is a checked negative clean result: do not start Phase 2B or make
an attack/detector dataset; a new decision is required before another change.

2026-10-31 — The Phase 2A scout-and-follow check (`food_layout` in
`environment.py`, `candidate_g_12x12_scout_follow.json`,
`calibration-scout-follow.json`, decision 0009) completed on Linux Python
3.12.14. It introduced a seed-varying pair of adjacent food cells far from the
nest, using four agents, 30 food units per cell, a 1,100-step horizon and 2%
evaporation. Explicit fixture positions still override the generated layout.
The six PPO jobs and three random references are in
`artifacts/phase2a/scout-follow-run-001/`. Full-minus-no-pheromone stochastic
delivery was 0.00, +8.75 and +5.75 (seeds 7/17/27); full PPO delivered all 60
units and beat random on every seed. It also completed all maps faster than
no-pheromone PPO. The seed-7 60-unit tie fails the declared strict-delivery
gate, so this useful near-result still does not authorize Phase 2B.

2026-10-31 — The fresh time-limited scout-and-follow validation
(`candidate_h_12x12_scout_follow_deadline.json`,
`calibration-scout-follow-deadline.json`, decision 0010) changed only the
horizon from 1,100 to 700 and retrained every policy. The six PPO jobs and
three random references are in
`artifacts/phase2a/scout-follow-deadline-run-001/`. Full-minus-no-pheromone
stochastic delivery was -51.50, -42.75 and +5.50. Full PPO delivered zero on
the first two seeds, below random movement, so the shorter deadline made the
full-input training unstable at the fixed 300,000-transition budget. Candidate
H fails the gate. The complete pinned Python 3.12 suite passed 103 tests before
this matrix. Preserve both results; do not start Phase 2B or change another
environment without a new decision.

2026-10-31 — The scout-and-follow training-budget validation
(`calibration-scout-follow-stability.json`, six `stability_*.json` policy
configs, decision 0011) retrained the same 700-step Candidate H task with
600,000 agent transitions per full/no-pheromone policy. The six PPO jobs and
three random references are in
`artifacts/phase2a/scout-follow-stability-run-001/`. Full-minus-no-pheromone
stochastic delivery was -50.75, -39.25 and -5.25 (seeds 7/17/27). Full PPO
lost to no-pheromone PPO on every seed, so doubling the budget did not fix the
short-horizon instability. The complete pinned Python 3.12 suite passed 104
tests before the matrix. Candidate I fails the gate; do not repeat this
700-step configuration or start Phase 2B.

2026-10-08 — Fresh Linux review verification on clean source revision `76970cc`: simulator/core checks on Python 3.11.16 passed 50 tests with two optional-stack skips. The pinned training lock failed resolution on Python 3.11 because `contourpy==1.4.0` requires Python >=3.12. A separate Python 3.12.14 environment installed the unchanged lock, passed dependency consistency and all 73 tests. A fresh 4096-transition PPO run passed parameter-update/reload checks and reproduced stochastic means 1.75 before/3.75 after; deterministic means remained zero. The fresh 48-episode comparison preserved its checkpoint and reproduced team means 3.75 without timeout/zero with timeout, zero injection loss, -2 honest-unit timeout gain, and undefined recovery. Clean/disabled fixture records matched; attacked fixture applied 20 units; all scripted fixtures delivered eight units in 89 steps. Actual-state PNGs and two-slide speaking notes were generated under ignored `artifacts/review-current/`. No source mechanics, training budgets, defense rules, or evaluation protocol changed. This verifies Linux execution and preserves negative results, not useful coordination or robustness.

2026-10-07 — Aarya's clean simulator milestone (`src/stigmergy/environment.py`, `src/stigmergy/cli.py`, `configs/env/*.json`, `tests/test_environment.py`). Decision 0001 specifies co-location, pickup contention, update order, observations, shared reward, bounds, and lifecycle. CPython 3.11.16 with pinned dependencies passed 27 pytest cases, including the PettingZoo parallel API test, deterministic 100-step replay, conservation, local observation isolation, and repeated demo artifact comparison. Editable package installation succeeded. Seed 7 scripted fixtures delivered eight units in 89 steps (8×8/two agents) and 55 steps (16×16/eight agents). Validation used working-tree changes on base revision `3c7cc20`; committed revision provenance must be captured in fresh runs after commit. Rule-based/scripted mechanics evidence only; no learned coordination, robustness, diffusion, or evaluation claim. Team review pending.

2026-10-08 — Rohan's persistent false-food attack/provenance milestone (`src/stigmergy/attacks.py`, `src/stigmergy/trajectories.py`, `configs/attack/persistent-review.json`, `tests/test_attacks.py`). Decision 0002 specifies fixed seeded attacker selection, occupied-cell nonnegative food deposits after legal movement/pickup-delivery, shared field cap/evaporation, global per-step/episode applied-mass budgets, and clean/injection-disabled/attacked controls. CPython 3.14.4 with locked dependencies passed 46 pytest cases. Seed-7 scripted development fixtures produced 89 steps and eight deliveries in every scenario; injection-disabled and clean policy-visible records matched, while the attacked run selected `agent_1`, requested 89 units, and authorized/applied the 20-unit episode budget. These fixtures and logs verify implementation accounting, not attack degradation or learned-policy coordination. The declared Python 3.11 target was unavailable and requires a fresh recheck; PPO, decoy/intermittent modes, grouped data splits, and evaluation remain incomplete. Team review pending.

Shashannk review checkpoint, 2026-10-08: `policies.py`, `ppo_adapter.py`,
`training.py`, policy JSON configs and CLI commands were verified with the
61-test installed-package suite on Windows Python 3.12.10. Decision 0003 and
`requirements-training.lock` document the unchanged local inputs/team reward,
custom synchronous adapter and explicit development maps. Two seed-7 smoke
runs of 4096 transitions matched summaries/parameters and passed checkpoint
roundtrip; deterministic delivery remained zero. Full learning, Python 3.11
validation and research comparisons are still open. See
`docs/SHASHANNK_FIRST_REVIEW.md` for usage, per-map outcomes and limitations.

Tusti review integration, 2026-10-08: `evaluation.py`, `evaluation_plots.py`,
comparison config and CLI connect frozen shared PPO to local history/timeout
and six paired development scenarios (decision 0004). Windows Python 3.12.10
passed 73 tests. Two 48-episode runs on maps 100-103/action seed 7 matched 104
reproducible files excluding runtime. Checkpoint bytes were unchanged and
clean/disabled local records matched. Attacked episodes applied 20 units each
and changed local trajectories. Deterministic deliveries were zero throughout.
Stochastic clean/disabled/attacked team means were 3.75; every timeout variant
produced zero. Honest injection loss was zero, timeout gain was -2, and all
recovery ratios were undefined. Preserve these negative/zero results. N=2/k=1
(50%), one short training seed, no completed episodes and unverified pheromone
reliance prevent minority/robustness conclusions. Python 3.11, full baseline/
detector work and held-out evaluation remain pending. See
[Tusti's walkthrough](TUSTI_FIRST_REVIEW.md). Team review pending; verified on
working-tree changes based on `cf260b6`.

### Nest-anchored eight-agent review verification - 2026-10-09

- Decision 0005 supersedes ordinary empty-agent home deposition. Per-agent
  successful outside movement counters reset on nest visits; empty moving
  outside deposits are `deposit * home_decay**counter` with default .95.
  Empty agents inside deposit normally; stationary/blocked outside agents do
  not deposit home. Carrying food deposition, step ordering, clipping,
  evaporation, observation shape, reward and attack capability remain unchanged.
- New explicit 8×8/eight-agent config and three-action-seed comparison config
  retain old two-agent configurations. Disabled/attacked runs select one
  productive attacker (12.5%). Saved historical artifacts remain untouched;
  running an old config now uses the NEW mechanics, and old checkpoints are
  rejected by source-hash validation.
- Pinned Linux Python 3.12.14 passed 83 tests and package compatibility checks.
  Tests cover outbound amounts, counter/nest/episode reset, stationary/blocked
  deposits, unchanged food, shared reward, conservation, local observations,
  attack accounting, ablation channel boundaries and incomplete training on
  interruption. Repeated scripted fixtures and matched controls passed.
- Fresh seed-7 smoke: 4,096 agent transitions, stochastic mean 6.25 to 6.00,
  deterministic zero. Fresh main training: requested 300,000, actual 300,032
  transitions (37,504 world steps); checkpoint finite/update/reload checks
  passed. Four-map/action-seed-7 stochastic mean 6.25 to 7.00; deterministic
  zero. Do not confuse that four-episode diagnostic with the 12-episode mean.
- Six matched scenarios: 96 episodes on development maps 100–103, stochastic
  action seeds 7/8/9 and deduplicated deterministic seeds. Stochastic team
  clean/disabled/attacked means all 7.6667; every timeout variant zero. Honest
  disabled 6.4167 versus attacked 6.5833, mean injection loss -.1667 and timeout
  gain -6.5833. Deterministic delivery remained zero in all six scenarios.
  Recovery undefined in 15/16 groups; one positive-loss group has recovery -6.
  Clean/disabled local hashes match, selected subsets match and checkpoint
  parameters remain unchanged. No harmful mean team disruption is established.
- Separate frozen-policy clean input ablation: 16 episodes, stochastic full
  mean 7.6667 versus zeroed 8.0000; same-observation action differences 21.11%
  stochastic / 49.75% deterministic. Stochastic paired-trajectory action changes
  51.26% over overlapping steps. Both deterministic delivery means zero. This
  measures input sensitivity, not beneficial trail use or the required trained
  no-pheromone baseline. One training seed/development maps remain limitations.
- All experiment stages completed in 161.5 seconds under a common 1,800-second
  deadline; source hashes/configs/seeds/provenance and budget are in ignored
  `artifacts/review-eight/`. Actual scripted states at 0/10/20/final=23 for
  clean/disabled/attacked delivered eight units; repeats match exactly.
  Two-agent new-mechanics waiting diagnostic decays .66158 at step 56 to
  .02044 at step 89 (×.9 per wait), replacing the former 8.7 hotspot.
- New readable state PNGs, training/delivery histories, team/honest episode
  plots, injection-mass/observation-change curves and sensitivity plots have
  been inspected. Observation changes are not detector scores or confirmed
  harmful exposure. [Review guide](REVIEW_DEMO.md) supplies two-slide text,
  speaking notes and Linux/Windows commands. The updated searchable handbook
  retains exactly 12 pages with linked contents/bookmarks; all pages rendered
  and inspected, with no page-bound violations. Source revision is `76970cc`
  plus verified working-tree changes; commits/pushes are left to the user.
- Longer/multiple-seed reliable policies, learned detector/score mitigation,
  decoy/intermittent attacks, grouped datasets, trained no-pheromone/cautionary
  baselines and final held-out robustness evaluation remain future work.

### Open risks and decisions

- Resolve the training lock's demonstrated Python 3.11 incompatibility (`contourpy==1.4.0` requires Python >=3.12) before claiming full-stack support on the declared target. Linux Python 3.12.14 is now verified. Audit the narrow adapter when expanding the simulator's fixed lifecycle.
- Frozen-policy input sensitivity is now measured; establish beneficial pheromone use and reliable cooperation before interpreting robustness.
- Phase 2A's declared benefit gate failed for every candidate, including the
  scout-and-follow and time-limited follow-ups. Preserve all completed
  calibrations. Create another follow-up decision record before changing
  mechanics, observations, rewards, maps, policy architecture, or attack work;
  do not generate a detector dataset from these policies.
- Investigate the negative timeout development result and confirm pheromone reliance before the full required baseline study; development comparisons do not establish robustness.
- Freeze the final test manifest before held-out evaluation and retain clean/control/attack pairings.
- Recheck the qualified dataset finding and literature coverage before manuscript submission.
