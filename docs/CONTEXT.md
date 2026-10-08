# Project Context

## Purpose and authority

This is the agent-readable source of truth for the capstone. It consolidates the finalized documents while preserving the difference between established literature, design commitments, and unimplemented plans.

Authoritative source documents:

- [Refined one-pager](reference/capstone_refined_one_pager.docx)
- [Project proposal](reference/capstone_project_proposal.docx)
- [Internal implementation handbook](reference/capstone_internal_implementation_handbook.docx)

If this file conflicts with those documents, stop and create a decision record before changing the scope or claim.

## Verified research framing

### Central question

Can a lightweight defense using local pheromone history and an agent's own task progress improve cooperative learned-policy performance under minority pheromone-injection attacks, including attack conditions withheld during development, without substantially reducing clean-task performance?

### What prior work already establishes

*Hacking the Colony* establishes misleading food-pheromone attacks, minority disruption, and a cautionary-pheromone mitigation in simulated ant foraging. Learned stigmergic coordination also exists. Therefore, this project must not claim that fake pheromone, a small malicious minority, cautionary pheromone, or swarm disruption is itself novel.

The candidate contribution is a reproducible evaluation of learned stigmergic policies and lightweight local defenses under controlled attack, map, and timing shifts. Novelty and publication suitability remain conditional on evidence from the final protocol.

### Dataset finding

The reviewed sources did not establish a ready-made public standardized dataset matching the full protocol: cooperative learned policies using a shared stigmergic field under minority pheromone injection, with clean, attacked, and defended trajectories. This is a qualified search finding, not proof that no such dataset exists.

Distinguish source code, benign physical/simulation datasets, literature corpora, and generated attack trajectories. The project will generate versioned clean, attacked, and defended trajectories and label simulator-only metadata separately from model-observable inputs.

## Design commitments

These are agreed implementation requirements, not proof that code already exists.

### Environment

- Use simulated cooperative resource retrieval, not hardware deployment or real-world validation.
- Start with a small 2D grid using Python, NumPy, and the PettingZoo parallel interface.
- Use food and home pheromone channels, local sensing, explicit movement rules, bounded deposits, deterministic seeded execution, evaporation, and optional diffusion.
- Specify update order, boundary behavior, pickup, delivery, collisions, resource depletion, and field clipping in tested code.
- Start from a 16 by 16 grid, eight agents, 500-step horizon, two by two nest, and two resource patches; simplify before increasing compute if learning is unreliable.

### Policies

- Include a rule-based policy for debugging and deterministic fixtures.
- Train a small parameter-shared PPO policy with decentralized observations. Learned-policy training is mandatory for the capstone's learned-policy claims.
- Use a CPU-first curriculum: 8 by 8/two agents, then 12 by 12/four agents, then 16 by 16/eight agents. Start near 300,000 agent transitions per seed and extend toward one million only with measured improvement.
- A rule-based-only result may document mechanics but is an incomplete learned-policy milestone.

### Threat model

- At episode start select `k` compromised agents and keep the set fixed. The pilot starts with `N=8`, `k=1` or `2`; always report count and fraction.
- Attackers may submit bounded, nonnegative false-food deposits after legal movement, only at their actual occupied positions.
- Implement persistent false deposition, decoy trails, and intermittent deposition. Use per-step and per-episode budgets and record requested versus applied mass.
- Exclude trail erasure, negative deposits, privileged global writes, reward tampering, policy modification, and detector manipulation from the primary threat model.
- Apply the same field transport, decay, diffusion, and cap to honest and malicious deposits.
- Include all-honest clean, injection-disabled twin, and attacked controls. Separate pheromone-injection effects from reduced productive-worker effects.

### Local defense and baselines

- Build local temporal features from observable pheromone changes, revisitation, and each agent's own pickup, delivery, and blocked-movement history.
- Begin with logistic regression and a small random forest; select detector, threshold, and mitigation on validation data only.
- Use the selected score to reduce reliance on suspicious food pheromone and add bounded local exploration. Keep detector inputs local and agent-specific.
- Compare with: undefended pheromone coordination; separately trained no-pheromone policy; local patience/timeout heuristic; explicitly documented adaptation of cautionary pheromone.
- Do not compare directly with approaches requiring extra identity data, direct messaging, voting, or blockchain reputation unless their extra capability is explicitly modelled and justified.

### Data and evaluation

- Split complete episodes and map seeds before creating temporal feature windows. Keep related clean, control, attacked, and defended variants in one split group.
- Use development maps for policy/detector training and validation; reserve unseen maps and attack configurations for final evaluation.
- Include benign saturation, congestion, and resource depletion as false-alarm controls.
- Prioritize honest food delivered, injection-induced degradation, recovery, and clean-task cost. Supplement with precision-recall measures, false alarms, alarm delay, and runtime.
- Report training-seed variability separately from evaluation-episode variability. Preserve failed runs and explain exclusions.

## Current verified repository state

- A clean grid environment and scripted mechanics demo are implemented and verified; see the implementation entry below.
- A first local-defense foundation exists in `src/stigmergy/defense.py`: agent-local temporal features and a deterministic timeout baseline. Eight focused unit checks passed on Python 3.12. The checks loaded this module without the environment package initializer because the pinned Gymnasium/PettingZoo dependencies are not installed in the current interpreter; full repository integration checks remain unrun. This is a component checkpoint, not attack evaluation or a completed Tusti milestone.
- No trained policy, attack injector, trajectory generator, detector, dataset, checkpoint, or research benchmark result exists here.
- The files in `docs/reference/` are finalized project documents copied into this repository as canonical references.
- The README JSON-configured demo and test commands are runnable. Training and evaluation commands and their broader dependency stack remain planned.

## Project roadmap

| Phase | Weeks | Required outcome |
| --- | --- | --- |
| Executable pilot | Weeks 1-8 | Runnable simulator, trained shared policy, attacks, logging, local-defense pilot, and reproducible release; completion target week 7 with week-8 buffer |
| Research refinement | Weeks 9-12 | Audited mechanics, stronger baselines, frozen evaluation protocol, and literature update |
| Main experiments | Weeks 13-17 | Held-out evaluation, ablations, uncertainty estimates, and failure analysis |
| Publication and final release | Weeks 18-22 | Manuscript, reproducibility audit, and demonstration; primary submission target weeks 20-22 |

Early gates: clean simulator by week 2; trained-policy/attack/logging evidence by week 4; local-defense pilot and comparisons by week 6; reproducible release by week 7.

## Team rotation

For name-based first-review continuation, follow [the team milestone and handoff plan](FIRST_REVIEW_PLAN.md). It defines the Aarya → Shashannk → Rohan → Tusti sequence and user-controlled commit/merge checkpoints; its targets are planned work, not completed evidence.

Initial owners: Aarya—environment and pheromone mechanics; Shashannk—policies and training; Rohan—attacks and trajectories; Tusti—local defense and evaluation.

Rotate in later phases so every teammate owns each subsystem, reviews another subsystem, reads anchor papers, runs experiments, and contributes to writing. Initial review cycle: Shashannk reviews Aarya, Rohan reviews Shashannk, Tusti reviews Rohan, and Aarya reviews Tusti.

## Evidence required before context changes

Use this protocol after implementation begins:

1. A code or configuration change must have a focused purpose that advances the agreed project.
2. Relevant automated tests, deterministic fixtures, or reproducible experiment checks must pass. Record configuration, seed, revision, and observed result.
3. A decision record is required before accepting a change to environment mechanics, observation/action semantics, threat capability, split rules, baseline capability, evaluation criteria, or contribution claim.
4. Update this file with only verified facts. Identify the changed component, evidence, and material limitation. Keep unverified work in a planned or open-question section.
5. Add the same verified milestone or correction to `CHANGELOG.md`.

Do not update the context merely because code was drafted, a test was skipped, an experiment produced an unexplained result, or a change makes results look stronger. Preserve negative and incomplete outcomes.

## Future implementation records

When code exists, append concise entries under these headings instead of rewriting history:

### Implemented and verified

2026-10-07 — Aarya's clean simulator milestone (`src/stigmergy/environment.py`, `src/stigmergy/cli.py`, `configs/env/*.json`, `tests/test_environment.py`). Decision 0001 specifies co-location, pickup contention, update order, observations, shared reward, bounds, and lifecycle. CPython 3.11.16 with pinned dependencies passed 27 pytest cases, including the PettingZoo parallel API test, deterministic 100-step replay, conservation, local observation isolation, and repeated demo artifact comparison. Editable package installation succeeded. Seed 7 scripted fixtures delivered eight units in 89 steps (8×8/two agents) and 55 steps (16×16/eight agents). Validation used working-tree changes on base revision `3c7cc20`; committed revision provenance must be captured in fresh runs after commit. Rule-based/scripted mechanics evidence only; no learned coordination, robustness, diffusion, or evaluation claim. Team review pending.

### Open risks and decisions

- Establish a functioning PPO/PettingZoo/SuperSuit adapter and pin validated versions before treating the planned commands as runnable.
- Confirm learned policies use the pheromone channels before evaluating attacks against them.
- Install and validate the pinned Python 3.11 environment, then run the full suite and integrate local history/timeout behavior with reproducible clean, injection-disabled, attacked, and defended comparisons once the PPO and attack/trajectory prerequisites are available.
- Freeze the final test manifest before held-out evaluation and retain clean/control/attack pairings.
- Recheck the qualified dataset finding and literature coverage before manuscript submission.
