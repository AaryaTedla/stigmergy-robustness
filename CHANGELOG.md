# Changelog

This file records verified project changes. Planned work belongs in `docs/CONTEXT.md` and must not be recorded here as completed.

## Unreleased

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
