# Decision Record: development PPO/timeout comparisons

**Status:** Accepted for first-review integration (team review and Python 3.11 revalidation pending)

**Date:** 2026-10-08

**Owners and reviewers:** Tusti (local defense/evaluation); Aarya (planned reviewer).

## Decision

Freeze the existing shared PPO checkpoint and compare six development variants:
clean, clean with timeout, injection-disabled, injection-disabled with timeout,
attacked, and attacked with timeout. Use the checkpoint's exact training grid
configuration and only its already declared development diagnostic map seeds.
Pair map seed, action seed and deterministic/stochastic mode across variants.
Reset one history extractor and timeout state per agent per episode. Apply the
same local timeout rule to every agent without checking attacker membership.
All variants remain in one development group; no dataset split or temporal
window training is performed and no final held-out maps are admitted.

The PPO actor receives only the original local observation; timeout inputs
remain local observation and own progress. Local features and proposed/executed
actions are logged separately from simulator-only identities, injection mass,
and honest delivery accounting. The honest population excludes the fixed
selected agents in disabled/attacked variants. Injection loss compares honest
disabled minus honest attacked; timeout gain compares honest attacked-with-
timeout minus honest attacked. Clean cost uses all-honest team deliveries.
Recovery fraction is defined only when paired injection loss is positive.

## Context and evidence

Decisions 0002/0003 provide bounded injection and a shared PPO checkpoint, but
neither implements matched defense evaluation. The existing timeout has a fixed
eight-step patience default; use it without performance tuning. Add matched
defended clean/disabled runs so generic heuristic effects are visible.
The review grid has N=2 and k=1 (50%), not a small minority. Attackers retain
the same productive PPO actions in the injector; reduced-worker effects are
not modeled. All results must retain these limitations.

## Alternatives considered

- Four scenarios only: rejected because clean/disabled defended controls help
  expose generic changes and clean-task cost.
- Defend only known honest agents: rejected as identity leakage into runtime.
- Final held-out evaluation or threshold fitting: deferred beyond this review.
- Claiming detector metrics from timeout triggers: rejected; timeout is a
  heuristic, not an attack classifier. Precision/recall/false-alarm claims do
  not follow from its activations.

## Consequences

This completes first-review integration/plots, not the full robustness study.
No-pheromone and cautionary baselines, learned detector selection, benign
false-alarm controls, minority pilot conditions, stronger/multiple-seed
policies and a frozen held-out protocol remain mandatory later. Episode/action
variability must not be presented as training-seed uncertainty. Keep negative
effects, zero degradation and undefined recovery ratios visible.

## Validation and context update

Verify clean/disabled equality of local records, matched selected identities,
bounded injection accounting, local controller inputs, episode state resets,
honest accounting and contrast formulas, checkpoint immutability, seed
repeatability, failed-run preservation and plot artifact creation. Run the full
suite and repeated development comparisons; record actual results and runtime
separately from reproducible metrics before accepting this decision.

Verification passed 73 tests on Windows Python 3.12.10. Two 48-episode runs
matched 104 files excluding timings, preserved checkpoint bytes and exercised
20-unit injection with changed local trajectories. Stochastic team delivery
was 3.75 without timeout and zero with timeout; honest injection loss was zero
and timeout gain was -2. Deterministic delivery was zero; recovery was undefined
in every group. These outcomes are preserved. Full robustness evaluation remains
pending; see the Tusti walkthrough for limitations and output schemas.
