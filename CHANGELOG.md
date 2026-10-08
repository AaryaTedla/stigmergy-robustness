# Changelog

This file records verified project changes. Planned work belongs in `docs/CONTEXT.md` and must not be recorded here as completed.

## Unreleased

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
