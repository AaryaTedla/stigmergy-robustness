# Changelog

This file records verified project changes. Planned work belongs in `docs/CONTEXT.md` and must not be recorded here as completed.

## Unreleased

### Review 2 Phase 2B data-validation correction - 2026-11-05

- Inherited Phase 2A paired-setting/resume validation. Enforced complete unique
  clean/disabled/attacked families and matching manifest/split/index provenance.
  Local records now reject unknown/audit fields, non-finite values, malformed
  shapes, invalid actions and non-Boolean outcomes before completed data status.
- Pinned Python 3.12.14 baseline 124 / final 162 tests passed, with package
  consistency. A tiny real frozen-PPO calibration passed repeated corpus/CSV
  integration without modifying checkpoint bytes; failure/interruption status,
  output immutability and repeatability passed. No J training matrix was rerun.
- Historical negative attack findings and generated-data counts remain reported
  evidence because their raw artifacts are absent from this checkout. No threat,
  simulator/PPO settings, final splits, labels, detector or defense were added.


### Review 2 Phase 2A validation correction - 2026-11-05

- Enforced equal full/no-pheromone settings and maps; current versioned pairs
  remain unchanged. New roots bind referenced config/source bytes and completed
  checkpoint/manifest/summary hashes. Resume rejects changed, malformed or
  unverifiable cached evidence before modifying its root manifest. Historical
  artifacts remain untouched; legacy roots without hashes require fresh output.
- Pinned Python 3.12.14 baseline: 107 passed; final: 116 passed. Fresh
  4,096-transition integration smoke passed finite/update/reload checks.
  Two-agent diagnostics: deterministic 0 before/after, stochastic 1.75 to 4.00.
  Original Candidate J results remain previously recorded, not rerun.
- Added decision 0017 and the branch audit record; no simulator, PPO settings,
  attack, split, detector or evaluation behavior changed.

### Phase 2B inspectable agent-step dataset view - 2026-11-02

- Added `phase2b-export-agent-steps`, a fail-closed exporter that flattens an
  existing completed development corpus into one row per agent per environment
  transition. Its schema separates 58 local-observation and 12 local-history
  input columns from group/scenario provenance and local outcomes; it never
  reads the simulator-only audit tree and rejects leaked attack metadata.
- Exported the fresh corpus into 412,016 agent-step rows from 103,004
  environment steps, 108 episodes and 36 intact development groups. Focused
  exporter/corpus/Phase 2B/attack tests passed 28 cases. The view has no
  temporal windows, train/validation/test split, detector labels, fitted model
  or robustness claim.

### Phase 2B development calibration corpus - 2026-11-01

- Decision 0016 added `phase2b-build-corpus` and a versioned plan that packages
  all three completed Phase 2B calibrations without selecting a favourable
  attack result. It writes local policy-visible records and simulator-only audit
  records to separate trees and fails closed on incomplete groups or leaked
  attack fields.
- Built the fresh local corpus with 36 intact development groups and 108
  episodes, three scenarios per group. It has 108 model-observable and 108
  audit step files; boundary inspection found zero simulator-only attack fields
  in model-observable records. No temporal windows, train/validation/test split,
  detector, defense, final dataset claim or robustness result was created.
  Focused corpus tests passed 3 cases, focused corpus/Phase 2B/attack checks
  passed 26 cases, and the complete suite passed 122.

### Phase 2B delayed persistent-attack follow-up - 2026-11-01

- Decision 0015 added a separately configured `start_step` to the bounded
  persistent injector. The delayed plan retains the 200-unit cap, one-of-four
  episode-fixed attacker, local occupied-cell placement, frozen Candidate J
  policies, maps and matched controls, while leaving the first 200 transitions
  untouched and permitting the first deposit on transition 201.
- The new 36-episode matrix applied all 200 units in every attacked episode
  but still did not establish consistent degradation: mean paired honest
  injection loss was -2.25 units, with one positive, six zero and five
  negative groups. Focused attack/Phase 2B checks passed 23 cases and the
  complete suite passed 119. This is a third negative development calibration;
  no detector, defense, final dataset, held-out evaluation or robustness claim
  was created.

### Phase 2B bounded-duration follow-up - 2026-11-01

- Decision 0014 changed only the bounded persistent attack's episode budget
  from 20 to 200 units, extending its possible active duration from roughly
  20 to 200 steps of Candidate J's 1,100-step horizon. The same three frozen
  policies, four maps, action seed, one-of-four attacker, local placement and
  matched controls were retained.
- The fresh 36-episode matrix applied all 200 units in every attacked episode
  but still did not establish consistent degradation: mean paired honest
  injection loss was -0.42 units, with two positive, five zero and five
  negative groups. Preserve both negative calibrations; no detector, defense,
  dataset, held-out evaluation or robustness claim was created. Focused tests
  passed 7 cases and the complete suite passed 114 tests.

### Phase 2B initial persistent-attack calibration - 2026-11-01

- Added the `phase2b-calibrate` command and a versioned Candidate J plan. It
  validates three frozen full-input checkpoints before running only matched
  stochastic clean, injection-disabled and bounded persistent-attack rollouts.
  It records local trajectories separately from simulator-only attack metadata
  and creates whole-group split manifests before any future temporal windows.
- Completed the 36-episode development calibration: three Candidate J policies
  × four diagnostic maps × one action seed × three scenarios. Every attacked
  episode applied the declared 20.0-unit budget, clean and disabled local
  records matched, and disabled/attacked controls selected the same agent.
  Mean paired honest-delivery injection loss was -2.17 units (eight zero,
  one positive and three negative groups), so this persistent setting did not
  establish attack degradation. No detector, defense, trajectory dataset,
  held-out evaluation or robustness claim was created. The complete suite
  passed 113 tests.

### Phase 2A clean-gate advancement - 2026-11-01

- Added the local-only frozen-policy action-sensitivity diagnostic and ran it
  on Candidate G's three full checkpoints. Masking only locally observed food
  and home pheromone changed the stochastic action distribution by mean total
  variation 0.272/0.187/0.230 and changed the most likely action on
  25.1%/19.9%/18.7% of visible observations (seeds 7/17/27). This is input
  sensitivity evidence, not proof of coordination or a detector feature.
- Completed decision 0012's predeclared Candidate J capacity-only validation:
  it retained Candidate G's long scout-and-follow task and changed only food
  capacity from 30 to 50 units per adjacent patch. Six fresh 300,000-transition
  PPO jobs and three random references completed under pinned Linux Python
  3.12.14. Full-minus-no-pheromone stochastic delivery was
  +31.25/+16.50/+19.50, while full-minus-random was +97.00/+78.25/+97.75.
  Candidate J passed the strict three-seed mechanical development gate.
- A timeout-interrupted invocation was preserved and the plan-identical resume
  generated fresh `-resume-1` outputs without overwriting partial artifacts.
  Root manifests, six PPO rows, three random rows and three paired rows were
  inspected. The complete suite passed 107 tests. Candidate J now supports
  Phase 2B planning; attack, detector, dataset and held-out robustness claims
  remain unimplemented until their Phase 2B protocol is declared.

### Phase 2A calibration completion and safe resume - 2026-10-31

- Completed the fixed development-only calibration matrix on Linux Python
  3.12.14: 18 clean shared-PPO runs across three eight-agent candidates, three
  seeds and full/no-pheromone observation modes, plus nine seeded random-action
  references. The no-pheromone model is separately trained with the same
  58-value shape and zeros only copied food/home input entries; simulator
  mechanics and diagnostics remain unchanged.
- All candidates failed the strict all-three-seed advancement gate. Stochastic
  full-minus-no-pheromone delivery was A: +2.50/-12.00/+1.75, B:
  +8.50/-1.75/+2.75 and C: +6.75/0.00/-0.25 (seeds 7/17/27). These mixed,
  development-only outcomes do not establish useful pheromone coordination;
  they block attack calibration, detector/dataset generation and robustness
  claims pending a follow-up decision record.
- Added a plan-validated `phase2a-calibrate --resume` path. It reuses only
  manifest-recorded jobs, preserves an interrupted training directory and
  writes a fresh `-resume-N` sibling, while replacing only derived aggregate
  CSV reports on recovery. Focused calibration/observation/training tests (24)
  and the complete Python 3.12 suite (95) passed.
- Tried two simpler Phase 2A maps after decision 0007: a 10×10 grid with eight
  food units per food cell and a 12×12 grid with ten. The complete follow-up
  has 12 PPO runs and six random references. Both maps beat random actions but
  failed the same three-seed full-versus-no-pheromone rule: D was -0.25/+2.00/
  0.00 and E was +2.75/+5.00/-0.50 across seeds 7/17/27. Phase 2B is still
  blocked; no attack, detector, or dataset work was started. Configuration
  checks and the complete Python 3.12 suite passed 96 tests before the run.
- Added `output/pdf/PHASE2A_WHY_NOT_WORKING.pdf`, a plain-language explanation
  of why the clean pheromone benefit is not yet reliable. It separates verified
  results from likely causes, explains why the current evidence blocks Phase 2B,
  and does not claim that the simulator or PPO pipeline is broken.
- Completed decision 0008's one-variable slow-evaporation follow-up: Candidate
  F kept Candidate E's map and training setup but changed evaporation from 0.10
  to 0.02. Local-only exposure reports showed that stochastic food pheromone
  was visible more often (55.54/39.14/49.32% for seeds 7/17/27, versus
  34.24/28.95/37.00% in Candidate E). The complete matrix of six PPO runs and
  three random references still failed the gate: full-minus-no-pheromone
  delivery was +2.75/+4.00/-1.25. Candidate F beat random actions but lost the
  fair no-pheromone comparison on seed 27. Phase 2B remains blocked. Exposure
  and plan tests plus the complete Python 3.12 suite passed 99 tests before
  the completed run; manifests and negative results are preserved.
- Added the `distant_cluster` food-layout option, which preserves two local
  food cells but places them adjacent and far from the nest using only reset
  RNG. Explicit fixture positions still override it. Candidate G used that
  layout with four agents, 30 food units per cell, 2% evaporation and a
  1,100-step horizon. Its six PPO runs and three random references made it the
  closest clean result: full-minus-no-pheromone delivery was 0.00/+8.75/+5.75,
  with full PPO faster on every seed. The seed-7 maximum-delivery tie fails the
  predeclared strict gate, so Phase 2B remains blocked.
- Completed a fresh Candidate H validation with only the scout-and-follow
  horizon reduced from 1,100 to 700. It failed rather than converting the speed
  signal into stable delivery: full-minus-no-pheromone delivery was
  -51.50/-42.75/+5.50, and full PPO scored zero on seeds 7 and 17. The shorter
  deadline is not a usable environment at the existing 300,000-transition
  budget. Focused layout/plan checks and the complete pinned Python 3.12 suite
  passed 103 tests before this completed matrix; Phase 2B did not start.
- Completed Candidate I, which repeated Candidate H exactly while doubling both
  PPO modes' training budget to 600,000 agent transitions. It did not repair
  full-input learning: full-minus-no-pheromone delivery was -50.75/-39.25/
  -5.25, so full PPO lost on every seed. The short-horizon scout-and-follow
  configuration is rejected at both tested budgets. The complete Python 3.12
  suite passed 104 tests before the completed matrix; Phase 2B remains blocked.

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
  harmful exposure. [Review guide](docs/REVIEW_DEMO.md) supplies two-slide text,
  speaking notes and Linux/Windows commands. The updated searchable handbook
  retains exactly 12 pages with linked contents/bookmarks; all pages rendered
  and inspected, with no page-bound violations. Source revision is `76970cc`
  plus verified working-tree changes; commits/pushes are left to the user.
- Longer/multiple-seed reliable policies, learned detector/score mitigation,
  decoy/intermittent attacks, grouped datasets, trained no-pheromone/cautionary
  baselines and final held-out robustness evaluation remain future work.


### Concise handbook correction - 2026-10-08

- Replaced the initial 65-page handbook with the requested 12-page team edition, retaining the project idea, environment/PPO/attack/timeout flow, source-file roles, actual screenshots, measured outcomes, commands and two-slide review notes.
- Verified all 12 rendered pages, searchable text, linked contents, bookmarks and page bounds. Reused measured evidence; no experiment or implementation behavior changed.

### Implementation handbook PDF - 2026-10-08

- Added `output/pdf/capstone_implementation_handbook.pdf`: a 65-page team handbook covering the project idea, current source/configuration/test inventory, execution/PPO/attack/timeout flows, actual screenshots, measured development results, operating commands and review preparation.
- Checked current source hashes against the saved training manifest and reused the recorded 73-test, 4096-transition and 48-episode evidence. Preserved zero/negative outcomes and separated planned detector/baseline/held-out work from implemented behavior; resolved the external DQN/source-trust note's disagreement with the repository.
- Verified searchable text, clickable contents, 39 chapter bookmarks and page bounds; rendered and visually inspected all pages. No simulator/policy/attack/defense/evaluation behavior changed, and no expensive experiment was rerun for document authoring.

### Linux review verification — 2026-10-08

- Verified the unchanged pinned training stack on Linux Python 3.12.14: dependency consistency and 73 tests passed. Python 3.11 core checks passed 50 tests with two optional-stack skips; full training-lock installation failed because the contourpy pin requires Python >=3.12.
- Fresh smoke training and 48-episode comparisons reproduced the documented zero/negative results, parameter/reload checks, and unchanged checkpoint. Scripted fixture controls and 20-unit injection accounting passed. Generated actual-state PNGs, measured charts, run instructions and two-slide explanations in ignored `artifacts/review-current/`; no capture source tool or mechanics change was added.

### Tusti development defense integration - 2026-10-08

- Added frozen shared-PPO evaluation with local history/timeout, six matched development scenarios, separated local/simulator logs, honest accounting, paired metrics and PNG/SVG plots; documented in decision 0004 and Tusti's walkthrough.
- Windows Python 3.12.10 passed 73 tests. Two 48-episode runs matched 104 reproducible files excluding timings. Checkpoint integrity, local control equality, bounded injection and failure preservation passed.
- Preserved negative results: stochastic team deliveries fell from 3.75 to zero with timeout; honest timeout gain was -2, injection loss was zero and all recovery ratios were undefined. Deterministic deliveries remained zero. Attacked episodes applied 20 units and changed local trajectories.
- N=2/k=1 is 50%, with one short training seed and development maps only. Python 3.11, pheromone reliance, minority pilot, full required baselines, detector and held-out evaluation remain pending. No robustness claim follows.

### Shashannk shared PPO review pipeline — 2026-10-08

- Added a local-observation debugging controller, fixed-lifecycle PettingZoo-to-SB3 adapter, shared CPU PPO training, JSON smoke/development configs, lazy CLI commands, pinned training dependencies and teammate walkthrough (decision 0003).
- Preserved the existing 58-value local observation, five actions and unmodified team delivery reward. Adapter checks cover simultaneous reset, terminal copies and horizon bootstrapping; no global critic, identity inputs or reward shaping was added.
- Windows CPython 3.12.10 with SB3 2.7.1/torch 2.5.1+cpu passed 61 tests, editable install and dependency consistency checks. Two seed-7 smoke runs executed 4096 agent transitions (2048 world steps), changed finite parameters, passed reload and matched summaries/parameter hashes exactly. Development stochastic mean deliveries changed from 1.75 to 3.75; deterministic mean remained zero and no diagnostic episode completed.
- Python 3.11 revalidation, the 300000-transition budget, curriculum progression, multiple training seeds, trail-reliance checks and research comparisons remain pending. The observed small development change does not establish useful learned coordination or robustness. SB3 2.4.1 was rejected by dependency resolution because it requires NumPy below 2; simulator pins were preserved.

### Rohan attack and trajectory foundation — 2026-10-08

- Added one persistent false-food attack mode with seeded episode-fixed compromised agents, occupied-cell-only nonnegative deposits, global per-step and per-episode applied-mass budgets, common food-field cap/evaporation, and separate requested/authorized/applied mass accounting. The injector never changes actions, rewards, observations, or infos.
- Added paired clean, injection-disabled, and attacked scenario configuration, JSONL trajectory recording, and a scripted review fixture command. Attack IDs/events stay under simulator-only metadata; only local observations and normal environment transition data appear in the policy-visible record.
- Added decision 0002, a review walkthrough, a review attack config, and focused checks. With locked dependencies on CPython 3.14.4, all 46 tests passed. Seed-7 clean, disabled, and attacked scripted fixtures each delivered eight units in 89 steps; clean and disabled policy-visible records matched, while the attack applied its configured 20-unit episode budget.
- This is mechanics/provenance evidence only. The repository target is CPython 3.11 and still needs a fresh run there. There is no PPO-generated trajectory, learned-policy attack result, detector comparison, data split, or decoy/intermittent implementation.

### Tusti local-defense foundation — 2026-10-08

- Added `src/stigmergy/defense.py` with 12 agent-local temporal features derived from the documented observation and own action/progress history, plus a deterministic patience/timeout baseline using local food/nest/boundary cues.
- Added focused tests for feature bounds and order, pheromone deltas, inferred revisitation, episode reset, timeout behavior, progress reset, local goal selection, and invalid inputs. Eight tests passed on Python 3.12 using an isolated import of the defense module. The full environment suite did not run because the interpreter lacks the pinned Gymnasium/PettingZoo dependencies; the repository targets Python 3.11.
- Corrected both progress timers so the initial observation is not counted as an elapsed no-progress step. The eight focused checks passed again, including initial-state timing; syntax compilation and whitespace checks passed. Full-suite execution remains blocked by missing dependencies and unavailable package network access.
- This verifies only the local component interface. PPO policy integration, attack/trajectory comparisons, plots, and the complete Tusti review milestone remain pending.

### Coding guidance

- Added `docs/FIRST_REVIEW_PLAN.md` and links from agent instructions, context, and README so a startup instruction plus teammate name selects the corresponding milestone, checks dependencies, and stops at the user's commit/merge checkpoint. Documentation-only change; links and whitespace checked.

- Added repository-wide requirements in `AGENTS.md` for explanatory code-file headers, important function/class documentation, non-obvious reasoning comments, and synchronized explanations. Documentation-only change; verified with `git diff --check`.

### Added

- Documentation-only repository bootstrap with agent instructions, canonical context, a decision-record template, and the finalized capstone documents.

### Verified state

- The repository intentionally contains no simulator, policy-training code, attack generator, dataset generator, or defense implementation.

## 2026-10-07 — Aarya clean simulator milestone

- Added the PettingZoo parallel grid simulator, bounded food/home pheromone deposits and evaporation, local observations, seeded maps/contention, pickup/delivery and episode lifecycle.
- Recorded mechanics in decision 0001; added development/pilot JSON configurations, pinned runtime/test dependencies, explanatory module docstrings, a scripted demo with SVG and provenance summary, and a review walkthrough.
- Verified on Python 3.11.16: editable installation and 27 pytest cases passed, including the PettingZoo parallel API check and repeated seeded demo outputs. Seed 7 fixtures delivered eight units in 89 development steps and 55 pilot steps. Validation was on uncommitted changes based on `3c7cc20`.
- Corrected current-state documentation to reflect the simulator. PPO, attacks, datasets, defenses, diffusion, and research comparisons remain incomplete; team review pending. The original bootstrap entry above describes the historical documentation-only state.
