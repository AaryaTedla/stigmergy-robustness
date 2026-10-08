# Rohan's first-review attack and trajectory walkthrough

This checkpoint implements a bounded persistent false-food injection and an
auditable trajectory format. It is simulator mechanics/provenance work only:
the repository still has no parameter-shared PPO policy, learned-policy attack
result, detector, split manifest, or robustness conclusion.

## Reading order

1. `docs/decisions/0002-review-persistent-false-food-injection.md`: exact
   threat boundary, update order, controls, and limitations.
2. `configs/attack/persistent-review.json`: the review fixture's one-attacker,
   one-unit-per-step, twenty-unit-per-episode configuration.
3. `src/stigmergy/attacks.py`: selection, budget/cap accounting, and
   simulator-only event records.
4. `src/stigmergy/environment.py`: attack hook after ordinary deposits and
   before the existing shared cap/evaporation stage.
5. `src/stigmergy/trajectories.py`: JSONL transitions and manifest provenance.
6. `tests/test_attacks.py`: focused mechanics and metadata-separation checks.

## Threat and control semantics

At reset, the injector uses a dedicated seed-derived random stream to select a
fixed number of agent IDs. This does not consume the environment's map or
pickup-contention RNG stream. After legal movement and automatic
pickup/delivery, each selected agent requests a food-field deposit at exactly
its occupied post-movement cell. The requested mass is constrained by the
global per-step budget and remaining episode budget, then by the target cell's
remaining field capacity. The existing environment clips both honest and false
deposits and applies the same evaporation immediately afterward.

Every attack event records three numbers: `requested_mass`,
`authorized_mass`, and `applied_mass`. They differ when a budget or field cap
binds. A clean run has no injector. An injection-disabled twin keeps the same
attack configuration, seed, and fixed selected attacker set but adds no false
mass; this separates injection from merely designating a compromised agent.

Attacker IDs, the event records, and episode totals are simulator-only. They
do not enter the 58-value observations or PettingZoo infos. The trajectory
manifest calls this separation out explicitly, while the JSONL step records
place events under `simulator_metadata`.

## Reproduce the review fixtures

After the README setup, use three fresh output directories:

```bash
python -m pytest -q

python -m stigmergy.cli record-fixture --scenario clean --seed 7 --output /tmp/rohan-clean
python -m stigmergy.cli record-fixture --scenario injection_disabled --seed 7 --output /tmp/rohan-disabled
python -m stigmergy.cli record-fixture --scenario attacked --seed 7 --output /tmp/rohan-attacked
```

`record-fixture` uses the existing privileged scripted route to make the
environment transition reproducible before a PPO policy is available. It is
not decentralized, trained, or a baseline. Its manifest records source
revision and dirty-tree status; retain generated outputs outside version
control. For the development fixture at seed 7, all three runs delivered eight
food units in 89 steps. The disabled and clean runs had identical
policy-visible transition data; the attacked run selected `agent_1`, requested
89 units, and was authorized/applied 20 units due to its episode budget. These
are accounting checks, not evidence that the attack degrades a learned policy.

## Validation and handoff

The full suite passed 46 tests in a disposable CPython 3.14.4 environment with
the locked runtime/test versions. The focused attack checks cover deterministic
selection, occupied-cell placement, nonnegativity, budget/cap accounting,
disabled controls, no observation/info leakage, and recorded metadata. The
same seed-7 fixtures were recorded for all three scenarios; clean and disabled
transitions matched once their simulator-only metadata was removed.

The project’s declared target remains CPython 3.11, which was unavailable in
this workspace and still needs a fresh full-suite recheck. Persistent mode is
the only implemented mode. Decoy/intermittent attacks, PPO-generated
trajectories, grouped map/episode splits, held-out attack configurations, and
all performance comparisons remain future work. Stop at this checkpoint for
review and user-controlled commit/merge; do not begin Tusti's milestone.
