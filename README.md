## Starting a coding task

For any task that creates, changes, tests, evaluates, or documents this capstone repository, start with:

Read and follow AGENTS.md, docs/CONTEXT.md, and .agents/skills/capstone-implementation/SKILL.md before working.

To continue your first-review implementation, add your name (for example, “I am Rohan. Continue my first-review milestone.”). Agents must follow the [team milestone and handoff plan](docs/FIRST_REVIEW_PLAN.md) and verify current progress before acting.

# Robust Stigmergic Coordination under Minority Pheromone Injection Attacks

This repository is the documentation-first foundation for a capstone on cooperative learned policies that coordinate through a shared pheromone field. It records the agreed research scope before implementation begins.

The project asks whether a lightweight defense based only on an agent's local pheromone history and its own task progress can improve cooperative learned-policy performance under minority pheromone-injection attacks, including attack and map conditions withheld during development, without materially reducing clean-task performance.

## Current status

Aarya's clean simulator milestone is implemented: a tested PettingZoo parallel grid environment, local observations, pickup/delivery, bounded food/home fields with evaporation, and a scripted visual demo. Tusti's local-defense foundation now includes temporal local-history features and a timeout baseline in `src/stigmergy/defense.py`; it is not yet integrated into a learned policy or attack evaluation. PPO training, attacks, trajectory datasets, and comparative results remain unimplemented. The three final Word documents in [`docs/reference`](docs/reference/) are the authoritative project records. [`docs/CONTEXT.md`](docs/CONTEXT.md) tracks verified progress.

## Local-defense foundation

`LocalHistoryFeatures` converts one agent's observation and its own preceding action into 12 named, bounded history features. Construct one instance per agent, call `reset()` at each episode, and call `update(observation, previous_action)` for each new observation; use `None` for the initial observation. `LocalTimeoutDefense` wraps an already selected action and, after a configurable number of steps without pickup or delivery, uses only visible food/nest landmarks and the local boundary mask to redirect movement. Both are simulator-only rule-based components; they are not a detector, learned policy, or evidence of attack robustness.

After installing the pinned development dependencies below, run their focused unit checks with `python -m pytest -q tests/test_defense.py`. The full first-review comparisons still require the shared PPO and attack/trajectory milestones.

## Run the first-review simulator

Validated on Python 3.11.16. From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock
python -m pip install -e . --no-deps
python -m pytest -q
python -m stigmergy.cli demo --config configs/env/development.json --seed 7 --output artifacts/review-demo
```

Use a fresh output directory for each run. Open `artifacts/review-demo/snapshot.svg` in a browser to inspect the final grid and both pheromone fields; `summary.json` records configuration, seed, source revision, dirty-tree status, and food accounting. Use `configs/env/pilot.json` for the 16×16/eight-agent fixture. The demo follows scripted routes on explicit food cells; it is mechanics evidence, not a learned-policy result. See [Aarya's walkthrough](docs/AARYA_FIRST_REVIEW.md).

## Research scope

The planned application is simulated cooperative resource retrieval in a two-dimensional grid. Honest agents use food and home pheromone channels with local sensing. A small parameter-shared PPO policy is a required milestone; a rule-based policy is only a debugging tool and separately labelled baseline.

Compromised agents may inject bounded, nonnegative food pheromone only at reachable occupied cells. Persistent false deposition, decoy trails, and intermittent deposition are in scope. Trail erasure, negative deposits, privileged global writes, reward tampering, and policy modification are out of scope.

The candidate defense uses observable local field changes, revisitation, and the agent's own progress history. It must not use attacker identities, global resource locations, privileged labels, or a new direct communication channel. Required comparisons are undefended pheromone coordination, a separately trained no-pheromone policy, a local timeout heuristic, and a documented adaptation of cautionary pheromone.

Misleading pheromone, minority disruption, and cautionary-pheromone mitigation are already established in prior work. The proposed contribution is a reproducible learned-policy evaluation and local-defense study under controlled distribution shifts. Publication potential is conditional on the completed evidence.

## Planned setup contract

The initial implementation target is Python 3.11. The expected dependency categories are NumPy, PettingZoo, SuperSuit, Stable-Baselines3, PyTorch, scikit-learn, pandas, PyArrow, PyYAML, matplotlib, and pytest. Exact versions must be selected, tested, and pinned when implementation starts.

Only the JSON-configured `demo` command above is implemented. The broader training/dependency stack below remains planned; these interfaces are not available yet.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m stigmergy.cli demo --config configs/env/pilot.yaml
python -m stigmergy.cli train --config configs/env/pilot.yaml
python -m stigmergy.cli generate --manifest data/manifests/dev.json
python -m stigmergy.cli fit-detector --split train --validate val
python -m stigmergy.cli evaluate --manifest data/manifests/test.json
python -m stigmergy.cli report --run-dir artifacts/core_v1
python -m stigmergy.cli replay --episode data/sample/episode_000123
```

## Planned repository layout

```text
src/stigmergy/       environment, policies, attacks, defenses, data, evaluation
configs/             versioned environment, policy, attack, defense, and sweep settings
tests/               deterministic environment, interface, leakage, and comparison tests
data/sample/         small versioned example trajectories and manifests
artifacts/           ignored run outputs, checkpoints, plots, and reports
docs/                agent context, decision records, and canonical references
```

## Team ownership and roadmap

Initial ownership is Aarya: environment and pheromone mechanics; Shashannk: policies and training; Rohan: attacks and trajectory generation; Tusti: local defense and evaluation. Ownership and review rotate across the project so everyone implements, reviews, experiments, reads anchor papers, and writes.

| Phase | Timing | Required outcome |
| --- | --- | --- |
| Executable pilot | Weeks 1-8 | Simulator, trained shared policy, attacks, logging, local-defense pilot, and reproducible release; target completion in week 7, buffer in week 8 |
| Research refinement | Weeks 9-12 | Audited mechanics, stronger baselines, and a frozen evaluation protocol |
| Main experiments | Weeks 13-17 | Held-out evaluation, ablations, uncertainty estimates, and failure analysis |
| Publication and final release | Weeks 18-22 | Manuscript, reproducibility audit, and demonstration; primary submission target in weeks 20-22 |

## Working rules

Read [`AGENTS.md`](AGENTS.md), [`docs/CONTEXT.md`](docs/CONTEXT.md), and the relevant decision records before changing implementation or research claims. The repository-local implementation skill gives the same rules in an actionable workflow.

## Change history

See [`CHANGELOG.md`](CHANGELOG.md). Record verified implementation milestones and corrections there; do not describe planned work as completed.
