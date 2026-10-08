# Aarya's first-review simulator walkthrough

> Historical first-review milestone. Home mechanics and review conditions are now
> superseded by [decision 0005](decisions/0005-nest-anchored-home-review.md).
> Use [the updated demo guide](REVIEW_DEMO.md) for current commands/results; retain
> the earlier measurements below as historical evidence.

This milestone implements simulated clean resource retrieval and field mechanics. It does not complete the learned-policy capstone or establish attack robustness. Shashannk's policy milestone follows after this branch is reviewed and merged.

## Reading order

1. `docs/decisions/0001-clean-grid-mechanics.md`: rules and their limitations.
2. `configs/env/development.json`: the small development settings.
3. `src/stigmergy/environment.py`: explanation at the top, configuration validation, reset, step, and observation construction.
4. `src/stigmergy/cli.py`: explicitly scripted demonstration and saved outputs.
5. `tests/test_environment.py`: checks that support the mechanics claims.

## What happens in one step

All agents submit one movement action. Invalid batches are rejected before movement. Legal moves update positions; an attempted move outside the grid stays put and records a blocked event. Agents can share cells or swap positions. Carrying agents deliver at the nest, and empty agents pick up one available unit outside it. A seeded random order resolves competition for the last unit.

Agents carrying food deposit food pheromone; other agents deposit home pheromone. All deposits occur at occupied cells. The two fields are capped, then multiplied by `1 - evaporation`. There is no diffusion in this version. Rewards give every agent the number of deliveries this step; sum rewards is not the food-delivery metric because the reward is shared.

Each agent receives a 58-value observation: 54 values for its local 3×3 patch and four for its carrying state and own pickup, delivery, and blocked events. The patch has six channels: food present, nest, normalized food pheromone, normalized home pheromone, occupancy fraction, and boundary mask. Global arrays are available to simulator tests and human rendering only, not future learned policies or defenses.

## Show it during the review

Follow the README setup instructions, run the tests, then run the development demo with seed 7 and a fresh output directory. Show the initial and final terminal grids, `snapshot.svg`, and `summary.json`. The development fixture delivers eight food units in 89 steps. The pilot fixture delivers eight in 55 steps. These fixtures use different agent counts and scripted routes, so their step counts are not a controlled performance comparison.

The SVG is a final snapshot, not an animation. Resource cells may disappear after depletion; the initial terminal grid shows their starting locations. An agent marker takes precedence over a nest or resource marker. Field values are printed in simulation units, with color intensity normalized to the configured cap.

Suggested accurate statement: “We implemented and tested the clean grid simulator, local observations, resource conservation, and pheromone deposition/evaporation. This demonstration is scripted. Shared PPO training, attacks, and local defenses are next.”

## Handoff and limitations

- Shared policy training can consume the same observation and action spaces for all agents. The PPO/SuperSuit adapter has not been tested or implemented.
- Rohan's attack integration must use post-movement occupied positions and the same cap/decay stage, after recording the attack design. No injection API exists yet.
- Tusti can later build temporal histories from local observations and own events. No detector or timeout defense exists yet.
- Co-location is allowed, maps have no obstacles, and resource patches are single cells. Future changes require a decision record and tests.
- Seeded map generation is for development only. There are no dataset split manifests or final evaluation results.
- Team review by Shashannk remains pending. Run and retain fresh demo outputs after committing so their source revision identifies the implementation commit; current validation used uncommitted changes on base revision `3c7cc20`.

## Commit checkpoint

Current branch: `feat/environment-pilot`. Review changes, commit and push this milestone, then merge into `main` before starting Shashannk's branch. Generated artifacts and the virtual environment are ignored. Code and test files start with explanatory docstrings; configuration details are explained here and in the decision record.
