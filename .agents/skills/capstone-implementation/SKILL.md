---
name: capstone-implementation
description: Guardrails for implementing the Robust Stigmergic Coordination capstone while preserving its research scope, evidence boundaries, and reproducibility requirements.
---

# Capstone Implementation Guardrails

## Start every task with the context

Read `AGENTS.md`, `README.md`, `docs/CONTEXT.md`, and any decision record relevant to the files you will change. Treat the context document as the authoritative summary, and the three files in `docs/reference/` as the finalized source records.

## Preserve the study contract

- Build a small, deterministic, two-dimensional grid environment before adding scale or complexity.
- Train a small parameter-shared PPO policy with decentralized observations. Rule-based agents are permitted for fixtures and debugging but cannot satisfy the learned-policy milestone.
- Keep attacks to bounded nonnegative false-food deposits made by compromised agents at occupied reachable locations. Implement persistent, decoy, and intermittent modes with matched injection-disabled controls.
- Apply identical field dynamics to honest and malicious deposits. Log the actual compromised-agent count and fraction.
- Build the local defense from observable pheromone change, revisitation, and each agent's own progress. Privileged labels, global maps, attacker identities, and attack timing never enter policy or detector features.
- Split maps and complete episodes before generating temporal windows. Final test maps and withheld attack configurations must not guide design decisions.

## Required comparisons and evidence

Evaluate undefended pheromone coordination, a separately trained no-pheromone policy, a local timeout heuristic, and a clearly documented cautionary-pheromone adaptation. Report food delivered, attack degradation, recovery, clean cost, false alarms, detection delay, runtime, training-seed variability, and episode variability as applicable.

Do not assert that pheromone injection, minority disruption, cautionary pheromone, or lack of a standardized dataset is new. The intended contribution is a reproducible learned-policy and local-defense evaluation; publication suitability depends on results.

## Context-update protocol

1. Make the smallest change that addresses the task and preserve configuration, seed, and split provenance.
2. Run the checks that demonstrate the changed behavior. A failed check, a partial run, or an unexplained anomaly is not verification.
3. If the change alters threat scope, mechanics, splits, baselines, evaluation, or claims, create a decision record from `docs/decisions/0000-template.md` before treating it as accepted.
4. Update `docs/CONTEXT.md` only with the verified fact, affected files/configurations, evidence, and remaining limitation.
5. Add a corresponding `CHANGELOG.md` entry. Do not rewrite planned sections as completed work.

## Completion report

State what changed, why it matches the study contract, checks run and their result, and any remaining limitation. Keep negative results and incomplete milestones visible.
