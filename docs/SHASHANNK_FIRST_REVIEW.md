# Shashannk first review: local controller and shared PPO pipeline

> Historical first-review milestone. Home mechanics and review conditions are now
> superseded by [decision 0005](decisions/0005-nest-anchored-home-review.md).
> Use [the updated demo guide](REVIEW_DEMO.md) for current commands/results; retain
> the earlier measurements below as historical evidence.

This checkpoint implements clean development training and initial diagnostics.
It does not establish useful learned pheromone coordination. Work was requested
on the current local-defense branch; the user will move/commit/push the changes.

## Read the code in this order

1. `src/stigmergy/policies.py`: seeded local heuristic for debugging. Visible
   food/nest and relevant pheromone guide actions, with exploration and random
   tie breaking. It has no environment/global-state input and is not PPO.
2. `src/stigmergy/ppo_adapter.py`: batches the existing observations into
   N rows of 58 values. Agents interact in one world, share one reward and
   reset together. Terminal rows are copied before auto-reset; truncation
   flags preserve SB3's timeout bootstrap behavior.
3. `src/stigmergy/training.py`: validates configs, builds one shared 32x32
   actor/local critic, trains on explicit development maps, records diagnostics,
   saves/reloads checkpoints, hashes parameters and preserves failed runs.
4. `tests/test_policies.py` and `tests/test_training.py`: local-controller
   checks, direct simulator equivalence, episode boundaries, seed scheduling,
   invalid actions/configs, real updates, repeated runs and failure preservation.
5. `src/stigmergy/cli.py`: lazy training imports and the two new commands.

## Setup and usage

Windows CPython 3.12.10 was used; the project's Python 3.11 target is pending
revalidation. `requirements-training.lock` pins the full Windows CPU stack.
Other Python versions/platforms require wheel and behavior checks. SB3 2.4.1
was rejected by the resolver because it requires NumPy below 2. SB3 2.7.1
installed successfully with the existing NumPy 2.3.5, Gymnasium 1.0.0 and
PettingZoo 1.24.3 pins. Simulator mechanics/rewards were preserved.

With a system Python that has pip, create the isolated environment:

```powershell
python -m venv --without-pip .venv
python -m pip --python .venv install -r requirements-training.lock
python -m pip --python .venv install -e . --no-deps
New-Item -ItemType Directory -Force artifacts | Out-Null
.\.venv\Scripts\python.exe -m pytest -q --basetemp artifacts/pytest-review-new
.\.venv\Scripts\python.exe -m stigmergy.cli debug-policy --output artifacts/local-debug-new
.\.venv\Scripts\python.exe -m stigmergy.cli train --policy-config configs/policy/review-smoke.json --output artifacts/ppo-smoke-new
```

Use fresh output directories. Explicit pytest temporary storage avoids this
sandbox's restricted system temporary folder. The commands default to the
8x8/two-agent grid in `configs/env/development.json`. The 300000-transition
config, `configs/policy/development.json`, is available but has not been run.

## Policy JSON fields

Both files use TrainingConfig; unknown fields are rejected.

| Field | Meaning |
| --- | --- |
| `seed` | PPO/network/action RNG seed; starting offset in the training map cycle |
| `total_transitions` | Requested agent transitions, rounded up to complete PPO rollouts |
| `n_steps` | World steps per PPO rollout for each agent slot |
| `batch_size` | Optimizer minibatch size; must divide N times n_steps |
| `n_epochs` | Optimizer passes through each rollout |
| `learning_rate` | Positive optimizer step size |
| `gamma` | Discount per world step, in [0,1] |
| `train_map_seeds` | Unique development maps cycled in declared order |
| `diagnostic_map_seeds` | Unique development diagnostic maps disjoint from training maps |

One world step gives N agent transitions. Rows are correlated interacting
agents, not independent episodes. Reward is the unchanged shared delivery
count; there is no reward shaping or global-state critic. Seed lists are
development assignments, not a final held-out manifest or grouped trajectory
partition. Keep them as development data when creating future map/episode
splits. No temporal-window dataset is created here.

## Artifacts and evidence

`manifest.json` records configs, versions, revision/dirty flag, source hashes,
status and runtime. Failed runs keep an error status and existing artifacts.
`initial.zip` and `policy.zip` are SB3 checkpoints. `progress.csv` logs PPO
optimization diagnostics. `summary.json` contains parameter hashes, actual
transition counts, reload equivalence, completed training-episode accounting
and initial/final development diagnostics. Compare parameter hashes and JSON
summaries for reproducibility: ZIP timestamps and runtime can differ.

61 tests passed with the training stack installed. Editable installation and
dependency consistency checks passed. Two seed-7 runs each executed 4096 agent
transitions (2048 world steps), changed finite parameters, and passed checkpoint
reload. Their summaries and parameter hashes matched exactly. Artifacts remain
in `artifacts/shashannk-review-a` and `artifacts/shashannk-review-b` (ignored by
Git). Source was uncommitted on base `a647af3`; manifests preserve source hashes.
Capture fresh committed provenance after the user commits.

A final run in `artifacts/shashannk-review-final` matched the repeated pilot
summary and captures hashes of the final source headers. The final full suite
also passed 61 tests, including a non-divisible requested transition budget
that correctly rounds up to complete rollouts.

| Diagnostic on maps 100..103 | Initial mean delivered | After 4096 transitions |
| --- | --- | --- |
| Deterministic actions | 0.00 | 0.00 |
| Seeded stochastic actions | 1.75 | 3.75 |

Each map had eight units and a 500-step horizon. No diagnostic episode
completed. Initial stochastic deliveries were [3,1,2,1]; final deliveries
were [4,2,2,7]. One small development run does not establish useful learning,
pheromone reliance, attack robustness or uncertainty. Deterministic behavior
remained unsuccessful. The local debugging CLI delivered four units in its
seed-7 run; that is rule-based debugging evidence only.

## Review checkpoint and remaining work

Revalidate Python 3.11, run the longer development budget/multiple training
seeds, and check pheromone reliance before attack evaluation. Curriculum
progression, a separately trained no-pheromone baseline, grouped datasets,
final held-out evaluation and uncertainty reporting remain future work.
No commit, push or merge was performed; the user handles publication after
team review. See decision 0003 for the adapter and development protocol.
