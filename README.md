## Starting a coding task

For any task that creates, changes, tests, evaluates, or documents this capstone repository, start with:

Read and follow AGENTS.md, docs/CONTEXT.md, and .agents/skills/capstone-implementation/SKILL.md before working.

To continue your first-review implementation, add your name (for example, “I am Rohan. Continue my first-review milestone.”). Agents must follow the [team milestone and handoff plan](docs/FIRST_REVIEW_PLAN.md) and verify current progress before acting.

# Robust Stigmergic Coordination under Minority Pheromone Injection Attacks

This repository is the documentation-first foundation for a capstone on cooperative learned policies that coordinate through a shared pheromone field. It records the agreed research scope before implementation begins.

The project asks whether a lightweight defense based only on an agent's local pheromone history and its own task progress can improve cooperative learned-policy performance under minority pheromone-injection attacks, including attack and map conditions withheld during development, without materially reducing clean-task performance.

## Current status

Aarya's clean simulator milestone is implemented: a tested PettingZoo parallel grid environment, local observations, pickup/delivery, bounded food/home fields with evaporation, and a scripted visual demo. Shashannk's clean shared-PPO pipeline and local debugging controller now run with reproducible short development diagnostics; useful learning and pheromone reliance remain unverified. Rohan's attack/provenance foundation adds one bounded persistent false-food injector and paired fixture controls. Tusti's local history and timeout baseline are now integrated with matched PPO/attack development comparisons and plots; see [Tusti's walkthrough](docs/TUSTI_FIRST_REVIEW.md) for usage and the negative timeout result. Candidate J passed Phase 2A's clean pheromone-benefit gate, while all three Phase 2B bounded persistent-attack calibrations (20-unit immediate, 200-unit immediate and 200-unit delayed) found no consistent delivery degradation. Their 108 trajectories are now packaged as a development-only calibration corpus with local records separated from audit metadata, but detector fitting, a final split dataset and robustness work remain blocked pending a new attack-calibration decision. See [the Phase 2A guide](docs/PHASE2A_CALIBRATION.md), [decision 0013](docs/decisions/0013-phase2b-attack-calibration-contract.md), [decision 0014](docs/decisions/0014-phase2b-persistent-attack-duration.md), [decision 0015](docs/decisions/0015-phase2b-delayed-persistent-attack.md) and [decision 0016](docs/decisions/0016-phase2b-development-calibration-corpus.md). Decoy/intermittent attacks, detector fitting, final split trajectory datasets, and research comparisons remain unimplemented. The three final Word documents in [`docs/reference`](docs/reference/) are the authoritative project records. [`docs/CONTEXT.md`](docs/CONTEXT.md) tracks verified progress.

## Updated eight-agent review demo

Decision [0005](docs/decisions/0005-nest-anchored-home-review.md) corrects home
pheromone: empty agents deposit weakening trails when moving outside the nest;
stationary/blocked outside agents add none. Food deposition remains unchanged.
Use `configs/env/review-eight.json` (8×8, eight agents) and the unchanged
one-attacker config (12.5%). Previous two-agent results remain historical.

See [review slides, speaking notes and commands](docs/REVIEW_DEMO.md). The latest
verified Linux Python 3.12 run passed 83 tests, fresh 4,096-transition smoke and
300,032-transition training, checkpoint reload, 96 matched comparison episodes
and 16 frozen-policy sensitivity episodes within 162 seconds. Stochastic
clean/attacked mean team delivery was equal at 7.67; timeout variants delivered
zero and deterministic delivery remained zero. Input ablation improved sampled
retrieval slightly; useful pheromone coordination/robustness remain unproven.

```bash
python scripts/run_review_budget.py --output artifacts/review-eight-new
python scripts/review_evidence.py figures --root artifacts/review-eight-new
```

The runner applies a common 30-minute experiment budget. Output directories must
be new. Generated figures are in `artifacts/review-eight/figures/`; updated team
handbook is `output/pdf/capstone_implementation_handbook.pdf` (12 pages).
Artifacts are ignored by Git; share images separately. Running existing two-
agent configs now uses the corrected mechanics, and their old checkpoints are
incompatible. Older walkthrough results below describe historical runs.

## Shared PPO review pipeline

See [Shashannk's walkthrough](docs/SHASHANNK_FIRST_REVIEW.md) for the code reading order, Windows setup, config fields and measured results. Install `requirements-training.lock` for the optional CPU training stack and install the package editable. Then run:

```powershell
.\.venv\Scripts\python.exe -m stigmergy.cli debug-policy --output artifacts/local-debug-new
.\.venv\Scripts\python.exe -m stigmergy.cli train --policy-config configs/policy/review-smoke.json --output artifacts/ppo-smoke-new
```

Each output directory must be new. All agents use the same PPO actor/local value network on the existing local observation. The smoke budget is 4096 agent transitions; `configs/policy/development.json` provides the planned 300000-transition budget. The pinned training stack was verified on Windows Python 3.12.10; the declared Python 3.11 target still requires a recheck. Full-stack checks passed 61 tests. Two smoke runs matched exactly; deterministic diagnostic deliveries remained zero. A short run is pipeline evidence and does not establish useful coordination or robustness.

## Review 2 validation audit

The 2026-11-05 audit passed 116 tests on pinned Python 3.12.14 and a fresh
4,096-transition checkpoint/update/reload smoke. Paired policy settings must
match except observation mode. New root manifests bind configuration/source
bytes and completed child artifacts. Resume rejects changed or missing evidence
before rewriting anything; legacy roots without these hashes remain historical
and need a fresh output directory. See [the audit record](docs/REVIEW2_AUDIT.md).
The original Candidate J artifacts are unavailable in this checkout; their
reported development results were not independently rerun.

## Phase 2A calibration (completed; Candidate J passed the clean gate)

The current eight-agent review checkpoint does not show beneficial pheromone use: clean and attacked delivery were equal, and a frozen-policy input ablation slightly improved sampled delivery. Before collecting attack or detector data, Phase 2A compares three larger/repeated-retrieval development environments and three PPO seeds against separately trained no-pheromone PPO baselines plus random actions. The baseline masks only food/home pheromone entries in copied policy batches during both training and evaluation; it does not alter simulator observations or mechanics.

The declared matrix, random baseline, reporting fields, and advancement gate are documented in [the Phase 2A guide](docs/PHASE2A_CALIBRATION.md) and [decision 0006](docs/decisions/0006-phase2a-calibration-contract.md). Earlier candidates had mixed paired results, but the capacity-only Candidate J follow-up passed the strict stochastic gate on seeds 7, 17 and 27: its full-minus-no-pheromone delivery was +31.25, +16.50 and +19.50, while it also beat random action in every pair. Candidate J is the clean-policy basis for Phase 2B planning; attack calibration, data splits, detector fitting and robustness claims still require their own documented Phase 2B protocol. See [decision 0012](docs/decisions/0012-phase2a-scout-follow-capacity.md).

```bash
python -m stigmergy.cli phase2a-calibrate --output artifacts/phase2a/calibration-run-001
```

If a process is interrupted after writing its manifest, resume only that exact
plan/output pair; completed PPO artifacts are reused and a partial job is
preserved in place:

```bash
python -m stigmergy.cli phase2a-calibrate --output artifacts/phase2a/calibration-run-001 --resume
```

The command is covered by the pinned audit suite; it does not select an environment automatically or generate the final dataset. The full historical training matrices were not rerun during this audit.

## Phase 2B attack calibration (completed; negative result)

Phase 2B's development-only calibrations freeze Candidate J's three
full PPO checkpoints and run matched clean, injection-disabled and bounded
persistent-attack episodes. They keep attacker identity and injected mass out
of policy-visible inputs and assign each complete policy/map/action family to
one group before any future detector windows. The 20-unit matrix produced a
mean honest-delivery injection loss of -2.17 units; a capacity-only 200-unit
immediate follow-up produced -0.42 units; and a 200-unit attack delayed until
transition 201 produced -2.25 units. None established consistent degradation,
so detector fitting, defense tuning and robustness claims remain unauthorized.

```bash
python -m stigmergy.cli phase2b-calibrate \
  --plan configs/phase2b/attack-calibration.json \
  --output artifacts/phase2b/attack-calibration-run-001

python -m stigmergy.cli phase2b-calibrate \
  --plan configs/phase2b/attack-calibration-persistent-200.json \
  --output artifacts/phase2b/attack-calibration-persistent-200-run-001

python -m stigmergy.cli phase2b-calibrate \
  --plan configs/phase2b/attack-calibration-persistent-delayed-200.json \
  --output artifacts/phase2b/attack-calibration-persistent-delayed-200-run-001
```

All three matrices are verified development-only calibrations. The command does
not select an environment automatically or generate a final dataset.

## Phase 2B development calibration corpus (completed; not detector data)

The corpus builder packages all three completed calibration matrices into 36
whole development groups and 108 episodes. Each episode has a
`model_observable` step file containing only local records and a separate
`audit` step file containing attack events, attacker identity and global
accounting. It has no temporal windows, train/validation/test partition,
detector labels, fitted detector or robustness claim.

```bash
python -m stigmergy.cli phase2b-build-corpus \
  --plan configs/phase2b/development-calibration-corpus.json \
  --output data/generated/phase2b-development-calibration-corpus-002
```

Use a new output directory each time. Generated corpus data is intentionally
local and ignored by Git; the plan, builder, tests and [decision 0016](docs/decisions/0016-phase2b-development-calibration-corpus.md)
are versioned.

### Inspectable agent-step CSV view

For spreadsheet or dataframe inspection, export only the corpus's local records
into one agent-step CSV. Each row represents one agent at one completed
environment transition. The generated schema separates safe local input columns
(58 observations plus 12 local-history features) from provenance and local
outcome columns. The export never reads the corpus audit tree, so attacker
identity, attack events, injected mass and global delivery cannot become CSV
features. This is still development-only data preparation: it does not create
detector labels, temporal windows, a train/validation/test split or a trained
model.

```bash
python -m stigmergy.cli phase2b-export-agent-steps \
  --corpus data/generated/phase2b-development-calibration-corpus-003 \
  --output data/generated/phase2b-agent-steps-001
```

See [the Phase 2B dataset roadmap](docs/PHASE2B_DATASET_ROADMAP.md) for the
literature delta, architecture diagram, data boundary and next milestones.

## Local-defense foundation

`LocalHistoryFeatures` converts one agent's observation and its own preceding action into 12 named, bounded history features. Construct one instance per agent, call `reset()` at each episode, and call `update(observation, previous_action)` for each new observation; use `None` for the initial observation. `LocalTimeoutDefense` wraps an already selected action and, after a configurable number of steps without pickup or delivery, uses only visible food/nest landmarks and the local boundary mask to redirect movement. Both are simulator-only rule-based components; they are not a detector, learned policy, or evidence of attack robustness.

After installing the pinned development dependencies below, run their focused unit checks with `python -m pytest -q tests/test_defense.py`. First-review integration passed 73 tests and two reproducible 48-episode comparisons on Windows Python 3.12.10. Full research baselines and held-out evaluation remain pending. See [Tusti's walkthrough](docs/TUSTI_FIRST_REVIEW.md) for the `compare-development` command.

## Attack and trajectory foundation

`AttackConfig` and `PersistentFalseFoodInjector` in `src/stigmergy/attacks.py` implement the review's persistent, nonnegative false-food deposits. The environment selects a fixed seeded compromised subset at reset; after legal movement and the ordinary pickup/delivery transition, it permits deposits only at those agents' actual occupied cells. Per-step/episode budgets and the same food-field cap constrain mass; requested, authorized, and applied mass are logged separately. Attacker IDs and logs remain simulator-only provenance and never enter observations or infos.

`python -m stigmergy.cli record-fixture` records a clearly labelled privileged scripted fixture to a fresh directory as `manifest.json` plus `steps.jsonl`. It supports `clean`, `injection_disabled`, and `attacked` scenarios sharing a seed and attack configuration. The output is for mechanics/provenance checks, not policy training, a baseline, or a robustness result. See [Rohan's walkthrough](docs/ROHAN_FIRST_REVIEW.md) and decision 0002 for usage and limitations.

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

The JSON-configured `demo`, `record-fixture`, `debug-policy`, `train`, `phase2a-calibrate` and `compare-development` commands are implemented. The YAML-configured interfaces below describe future plans; use the JSON PPO commands above for the current pipeline.

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
