# Phase 2B mechanism-diagnostic change report

Date: 12 November 2026  
Status: verified development-only implementation and run

## Purpose

This report records the changes made after the three original persistent-attack
calibrations produced mixed or negative mean injection loss. It separates
implemented facts from research conclusions. The goal was to measure whether
honest agents actually encounter false-food pheromone, not to force a positive
result.

## Changes implemented

| Area | Change | Boundary preserved |
|---|---|---|
| Simulator | Added `attack_food_component`, an audit-only false-food source component. It follows the same cap and evaporation stages as the food field. | It never changes the actual field, rewards, actions, or 58-value observation. |
| Audit views | Added copied normalized 3×3 false-food component views for every agent after each transition. | Views are written only in `simulator_metadata`. |
| Metrics | Added honest-agent exposed-step count and normalized false-signal sum. | Neither value is a PPO or detector input. |
| Corpus boundary | Rejects source-attribution and exposure fields if they occur in a local record. | Model-observable exports remain free of simulator truth. |
| Replication | Added a five-action-seed delayed-200 diagnostic plan. | Policies, maps, attacker fraction, placement, budgets, and field mechanics stay fixed. |
| Reporting | Added paired median and harmful-group fraction alongside the mean. | The signed injection-loss definition is unchanged. |

## Fresh replicated diagnostic

Configuration: three frozen Candidate J PPO policies (training seeds 7, 17,
27), four development maps (100–103), five predeclared stochastic action seeds
(7, 17, 27, 37, 47), and clean/injection-disabled/attacked matched scenarios.
One attacker is selected among four agents; the delayed persistent attack starts
on transition 201 and has a 200-unit episode cap.

| Measure | Result |
|---|---:|
| Paired groups | 60 |
| Episodes | 180 |
| Mean injection loss | +0.17 honest food units |
| Median injection loss | 0 units |
| Harmful groups | 14 / 60 (23.3%) |
| Attacked episodes with honest false-signal exposure | 60 / 60 |
| Mean honest exposed agent-steps | 2,130.17 |
| Mean applied false-food mass | 200 units |

Injection loss remains `honest delivery(injection-disabled) − honest
delivery(attacked)`. A positive value means the attack reduced honest delivery.
The +0.17 mean is small, the median is zero, and most groups do not show harm.
This does not establish reliable disruption, a detector, a defense, or
robustness.

## Verification

- Focused environment, attack, Phase 2B, and corpus tests: 76 passed.
- Complete pinned test suite: 164 passed in 32.86 seconds.
- Fresh output: `artifacts/phase2b/mechanism-diagnostics-delayed-200-run-001/`.
- Output includes manifest, grouped split assignments, episode metrics,
  contrasts, summaries, and separated local/audit records.

## Files changed

| File | Role |
|---|---|
| `src/stigmergy/environment.py` | Audit-only source attribution and normalized local audit views. |
| `src/stigmergy/evaluation.py` | Audit record and honest exposure aggregation. |
| `src/stigmergy/phase2b.py` | Replication summaries and narrow audit-source provenance allowance. |
| `src/stigmergy/phase2b_corpus.py` | Fails closed on source-attribution leakage. |
| `configs/phase2b/mechanism-diagnostics-delayed-200.json` | Reproducible five-seed diagnostic plan. |
| `docs/decisions/0018-phase2b-mechanism-diagnostics-protocol.md` | Accepted scope and verified result. |

## What remains

Do not train a detector or claim a defense yet. A new attack mode needs its own
accepted decision record, then development selection and final evaluation on
unseen maps and a withheld attack configuration. Keep the present result as a
small, mixed, development-only finding.
