# Changelog

This file records verified project changes. Planned work belongs in `docs/CONTEXT.md` and must not be recorded here as completed.

## Unreleased

### Coding guidance

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
