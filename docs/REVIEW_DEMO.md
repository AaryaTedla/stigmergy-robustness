# Updated review demo: what to show and say

This is development evidence under decision 0005. Use the new figures in
`artifacts/review-eight/figures/`. The previous two-agent evidence remains in
`artifacts/review-current/`; its checkpoint must not be used with new mechanics.
Generated artifacts are ignored by Git. Share the images/PDF explicitly if your
teammates need them; committing source does not upload these run directories.

## Slide 1 - Simulator and corrected pheromone mechanics

**Title:** Cooperative retrieval: verified simulator mechanics

**Text to put on the slide:**
- 8 × 8 grid, eight agents, eight food units; each agent senses only 3 × 3 cells.
- Carrying agents deposit food pheromone; empty moving agents deposit home pheromone.
- Home deposits weaken with steps since the last nest visit; waiting outside adds none.
- Both fields evaporate by 10% per step.
- Scripted mechanics fixture: eight food units delivered in 23 steps.

**Images:** Place `clean-step-0.png` and `clean-step-23.png` one above the other.
Each contains grid / food field / home field. Do not squeeze all 12 state images
onto one slide. Use `clean-step-10.png` or `clean-step-20.png` for a live walkthrough.
Keep `waiting-decay.png` and `attacked-step-20.png` as backup images.

**Say this (about 60 seconds):**
“We first validated the simulator with a scripted route. These screenshots are
actual simulator states, not PPO actions. Initially food is at two patches and
both fields are zero. Agents move, collect one unit, and return it to the nest.
When carrying food they leave food pheromone. Empty moving agents leave home
pheromone that weakens with movements since the last nest visit. Waiting outside
the nest now adds nothing, so an exhausted food patch cannot keep building a
home hotspot just because an agent waits there. By step 23 all eight units have
been delivered. The fields remain because old deposits evaporate gradually.”

**Explain the numbers:** Values are concentrations, not food counts, distances,
trust or probabilities. `F4` means four remaining food units; `A×4` means four
agents occupy that cell. Row/column coordinates start at zero. An outbound empty
agent's first post-evaporation deposit is 1 × .95 × .9 = .855; the second is
1 × .95² × .9 = .81225. Overlap adds deposits, so concentrations can exceed one.
The final home value at nest cell (1,1) rounds to 5.3. Food concentration can be
high near the nest because carrying agents recently returned there; it is not
proof of food at that cell. Nest delivery happens before deposition, so a newly
unloaded agent adds home instead. A printed 0.0 can be a small rounded residual.

**Waiting backup:** Under new mechanics the two-agent historical route reaches
the exhausted upper patch at step 56 with home concentration .66158. Every later
wait multiplies it by .9; at step 89 it is .02044. This diagnostic is explicitly
two-agent, separate from the eight-agent experiment. The old 8.7 hotspot was from
repeated stationary deposits under the former rule. New trails can still overlap
and need not make a globally perfect directional gradient.

## Slide 2 - Learned policy, attack and measured results

**Title:** Shared PPO and matched attack/timeout diagnostics

**Text to put on the slide:**
- One shared PPO actor uses 58-value local observations; fresh seed-7 training.
- 300,032 agent transitions; smoke check and checkpoint reload passed.
- Stochastic before/after diagnostic mean: 6.25 → 7.00 (four maps, action seed 7).
- Matched stochastic means: clean 7.67, attacked 7.67, attacked + timeout 0.
- One selected attacker out of eight (12.5%); bounded false food-pheromone injection.
- Field/input changes measured; harmful team disruption and successful defense remain unproven.

**Images:** Use `ppo-before-after.png` plus `delivery_comparison.png`. If the slide
looks busy, keep the before/after values as text and make delivery comparison the
large central image. Use `mass-and-observations.png`, `delivery-over-time.png` and
`pheromone-sensitivity.png` as backup evidence. Dots are individual episodes,
not confidence intervals. Separate deterministic/stochastic panels must remain.

**Say this (about 90 seconds):**
“PPO learns by interacting with the simulator: local observation, action, simulator
reward and next observation. Every agent uses the same network. We trained a
fresh policy under the corrected mechanics, without reusing the old checkpoint.
The four-map seed-7 stochastic diagnostic improved slightly, but deterministic
actions still delivered zero. We then froze the checkpoint and compared six
matched scenarios on four development maps. Stochastic actions use three action
seeds; deterministic seeds are deduplicated, giving 96 episodes. The attacker
is one of eight agents and adds only bounded nonnegative food pheromone at its
occupied cells. Its movement policy remains productive. Injection changed local
observations, but average team delivery stayed equal. Our fixed timeout rule
reduced delivery to zero, so we report it as a failed baseline here, not a
successful learned defense. These are development diagnostics; held-out research
evaluation and a learned detector are still future work.”

## Measured details and how to interpret them

| Stochastic scenario (12 episodes each) | Mean team | Mean matched honest |
| --- | ---: | ---: |
| Clean | 7.667 | 7.667 (all eight honest) |
| Clean + timeout | 0 | 0 |
| Injection disabled | 7.667 | 6.417 (seven honest) |
| Injection disabled + timeout | 0 | 0 |
| Attacked | 7.667 | 6.583 (seven honest) |
| Attacked + timeout | 0 | 0 |

Deterministic means are zero in all six scenarios (four episodes each). Honest
injection loss = disabled minus attacked: mean -.167 units; timeout gain under
attack = -6.583 units. One stochastic group has honest loss +1 and recovery -6;
15 of 16 groups have undefined recovery because loss is zero or negative. Do not
replace undefined recovery with zero or call the negative ratio successful.
Equal mean team results do not imply identical trajectories or individual credit.

The frozen-policy sensitivity diagnostic gives stochastic mean 7.667 with full
inputs and 8.000 with pheromone channels zeroed (12 clean episodes each).
Paired counterfactual actions on the SAME local observations differ in 21.11%
of sampled stochastic agent actions; realized paired trajectories differ in
51.26% of overlapping agent actions. Deterministic delivery is zero for both;
same-observation actions differ in 49.75%. This establishes input sensitivity,
not beneficial pheromone use. Zeroing inputs is distribution shift, and this
is not the required separately trained no-pheromone baseline.

`mass-and-observations.png` shows requested mass continuing to increase while
applied mass stops at the unchanged 20-unit episode budget. Values are insertion
before evaporation. Completed episodes stop requesting. Observation differences
are means of normalized food-pheromone values in each agent's 3×3 crop, attacked
minus disabled at the same world step. Different trajectories can make this
quantity negative even though injection itself is nonnegative. Only pairs still
observed contribute; these curves are not detector scores or harmful-exposure labels.

## What to run for the review

No rerun is needed to show the saved images. Open the PNGs before presenting.
Use a fresh output directory for every command. From the repository root:

Linux:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-training.lock
python -m pip install -e . --no-deps --no-build-isolation
python -m pytest -q
python -m stigmergy.cli demo --config configs/env/review-eight.json --output artifacts/live-demo-new
```

Windows PowerShell:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-training.lock
python -m pip install -e . --no-deps --no-build-isolation
python -m pytest -q
python -m stigmergy.cli demo --config configs/env/review-eight.json --output artifacts/live-demo-new
```

Full reproducible experiment and figures (both operating systems after activation):
```bash
python scripts/run_review_budget.py --output artifacts/review-eight-new
python scripts/review_evidence.py figures --root artifacts/review-eight-new
```
The runner gives smoke + training + comparisons + sensitivity one 30-minute
wall-clock budget. Partial stages remain incomplete and are not compared. New
figures/fixtures subdirectories are required. See budget.json, manifests,
summary.json, comparison/episodes.csv and contrasts.csv for audit details.

Individual commands:
```bash
python -m stigmergy.cli record-fixture --config configs/env/review-eight.json --scenario attacked --output artifacts/fixture-new
python -m stigmergy.cli debug-policy --config configs/env/review-eight.json --output artifacts/debug-new
python -m stigmergy.cli train --config configs/env/review-eight.json --policy-config configs/policy/review-smoke.json --output artifacts/smoke-new
python -m stigmergy.cli train --config configs/env/review-eight.json --policy-config configs/policy/development.json --output artifacts/train-new
python -m stigmergy.cli compare-development --checkpoint artifacts/train-new/policy.zip --comparison-config configs/evaluation/review-eight.json --output artifacts/compare-new
```
Standalone sensitivity uses the runner's root layout (`training/`, `comparison/`):
`python scripts/review_evidence.py sensitivity --root artifacts/review-eight-new`.
Do not run it again after the runner already created its sensitivity directory.

## Configuration and evidence boundary

`configs/env/review-eight.json` explicitly sets size=8, n_agents=8, horizon=500,
food_per_patch=4, deposit=1, home_decay=.95, cap=10, evaporation=.1.
`configs/evaluation/review-eight.json` preserves maps 100–103, timeout=8,
progress_horizon=20 and both action modes, adding action seeds 7/8/9.
The attack config and both PPO configs retain their prior values. Existing two-
agent JSON configurations remain available, but running them now uses NEW
mechanics; only their saved historical artifacts describe the former rule.

Verified runtime is Linux Python 3.12.14 with the pinned training stack. The
Python 3.11 training lock is incompatible with its contourpy pin, which requires
Python >=3.12. Core simulator validation on 3.11 is separate from full training.
Hardware validation, final held-out results, a learned detector, decoy/intermittent
modes and the remaining trained baselines are not implemented evidence.
