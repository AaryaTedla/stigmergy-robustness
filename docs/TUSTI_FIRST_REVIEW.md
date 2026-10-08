# Tusti: first-review integration

> Historical first-review milestone. Home mechanics and review conditions are now
> superseded by [decision 0005](decisions/0005-nest-anchored-home-review.md).
> Use [the updated demo guide](REVIEW_DEMO.md) for current commands/results; retain
> the earlier measurements below as historical evidence.

The previously blocked part now connects the shared PPO checkpoint, bounded
persistent injector, local history and timeout baseline. It records six matched
development scenarios and creates comparison plots. This is simulated grid
evaluation, not a completed robustness study or learned detector.

## Code reading order

1. `src/stigmergy/defense.py`: the existing 12 local history features and timeout
   rule. Each agent gets independent state, reset at every episode.
2. `src/stigmergy/evaluation.py`: checkpoint validation, local PPO controller,
   episode recording, honest-delivery accounting and paired metrics.
3. `src/stigmergy/evaluation_plots.py`: standalone PNG/SVG delivery and effect plots.
4. `tests/test_evaluation.py`: locality, reset, control equality, accounting,
   reproducibility, checkpoint integrity and failure-record checks.
5. `src/stigmergy/cli.py` and decision 0004: command entry point and evaluation contract.

The actor still receives the original 58-value local observation. History uses
the previous executed action, including timeout overrides. The 12 derived features
are recorded for inspection; they are not inputs to a newly trained detector.
Every agent receives the same defense rule. Attacker identities and global food
accounting appear only in separate simulator metadata, never controller inputs.

## Run it

Use the installed editable package and pinned CPU stack described in
[Shashannk's guide](SHASHANNK_FIRST_REVIEW.md). Each output directory must be new.

```powershell
.\.venv\Scripts\python.exe -m stigmergy.cli compare-development --checkpoint artifacts/shashannk-review-final/policy.zip --output artifacts/tusti-review-new
.\.venv\Scripts\python.exe -m pytest -q --basetemp artifacts/pytest-tusti-new
```

Checkpoints and run outputs are ignored local artifacts. If the checkpoint is
absent, first run `train --policy-config configs/policy/review-smoke.json --output
artifacts/tusti-policy-new` through the same Python CLI, then compare its
`policy.zip`. A new training run produces its own evidence; do not assume it
reproduces the measured checkpoint below without checking.

The optional `--attack-config` defaults to
`configs/attack/persistent-review.json`; `--comparison-config` defaults to
`configs/evaluation/review-development.json`. The latter has these fields:

| Field | Meaning |
| --- | --- |
| `purpose` | Must be `development_only`; final evaluation is rejected. |
| `map_seeds` | Unique development maps, restricted to the checkpoint's declared diagnostic maps. |
| `action_seeds` | Unique action RNG seeds; deterministic mode uses only the first to avoid duplicate episodes. |
| `action_modes` | `deterministic` and/or seeded `stochastic` PPO action selection. |
| `timeout` | Positive number of completed no-progress steps before redirection; default 8. |
| `progress_horizon` | Positive normalization horizon for recorded local progress features; default 20. |

All six related variants are assigned to the same development group before
rollout/history extraction. No temporal-window dataset or fitted detector is
created. Final held-out maps and configurations are not used.

## Outputs and metrics

`manifest.json` records configs, seeds, dependency versions, checkpoint and source
hashes, feature names, groups and completion/failure status. Each episode has a
JSON summary and step JSONL separating local records from simulator metadata.
`episodes.csv`, `contrasts.csv` and `summary.json` hold reproducible metrics;
`runtime.json` holds elapsed timings separately. Delivery/effect plots are saved
as PNG and SVG. Failed runs retain a failed manifest and available partial records.

The clean variants have no selected attackers. Injection-disabled and attacked
variants share the same fixed selected agents, who retain productive PPO behavior.
Honest deliveries exclude those selected agents only in these four variants.
Clean cost therefore uses team deliveries; injection effects use the matched
honest population. Do not directly compare their differently sized populations.

- Injection loss = honest disabled deliveries minus honest attacked deliveries.
- Timeout gain = honest attacked-with-timeout minus honest attacked deliveries.
- Clean cost = clean team deliveries minus clean-with-timeout team deliveries.
- Disabled cost = honest disabled minus honest disabled-with-timeout deliveries.
- Recovery = timeout gain / injection loss only when injection loss is positive;
  otherwise JSON uses null and CSV leaves the field blank. Negative effects remain.

Units are delivered food units per episode; injection mass uses simulator field
units. Timeout activations are heuristic activity, not detector alarms.

## Verified results, 2026-10-08

Windows Python 3.12.10 passed all 73 tests, including 12 focused evaluation checks.
Two runs (`artifacts/tusti-review-a` and `artifacts/tusti-review-b`) each completed
48 episodes: four maps (100–103), two action modes and six variants, action seed 7.
All 104 files other than the timing file matched byte-for-byte, including plots
and local trajectories. The frozen checkpoint remained unchanged. Clean/disabled
local records matched with and without defense. Every attacked episode applied
20 units of injection and changed its local trajectory relative to its control.

| Stochastic scenario | Mean team deliveries | Mean honest deliveries |
| --- | ---: | ---: |
| Clean | 3.75 | 3.75 |
| Clean with timeout | 0 | 0 |
| Injection disabled | 3.75 | 2.00 |
| Injection disabled with timeout | 0 | 0 |
| Attacked | 3.75 | 2.00 |
| Attacked with timeout | 0 | 0 |

Deterministic deliveries were zero in all six scenarios. Stochastic mean
injection loss was zero, timeout gain was -2 honest units, and clean cost was
3.75 team units. All eight paired groups had undefined recovery because none had
positive injection loss. No episode completed the task within 500 steps.

This preserves a negative result: the existing timeout harms this checkpoint's
development performance. No delivery degradation from injection was observed
here, despite changed local trajectories. Neither result supports a general
claim about attacks or defenses. The policy was trained for only 4096 transitions
with one training seed; useful coordination and pheromone reliance remain
unverified. N=2, k=1 is 50%, so this is integration evidence, not a minority study.
Elapsed time includes logging and concurrent work, not an isolated defense benchmark.

Python 3.11, stronger/multiple-seed policies, the eight-agent minority pilot,
no-pheromone and cautionary baselines, learned detector/false-alarm controls, and
final held-out evaluation remain pending. Evaluation provenance records base
`cf260b6` with working-tree changes; retain the checkpoint's original training
manifest. Fresh runs after the team's commit are needed for committed provenance.
This checkpoint is ready for team review; no commit, push or merge was performed.
