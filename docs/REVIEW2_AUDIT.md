# Review 2 Phase 2A audit - 5 November 2026

## Source and boundaries

Audited branch `phase2a`, base `b20319f4a549cc172268192682edcd70d208d855`.
Work took place in an isolated checkout; the user's main checkout is unchanged.
The original Candidate J checkpoints, CSV reports and generated trajectories
are not present here. Decision 0012's numbers are previously recorded evidence,
not independently reproduced measurements in this audit.

## Findings and corrections

1. The loader checked each mode/seed but accepted unequal paired settings.
   It now requires every policy field except observation mode to match.
2. A root-plan hash alone did not bind referenced configs or implementation.
   New roots record input/source fingerprints; changed inputs cannot resume.
3. Cached completed rows were reused without checking their child artifacts.
   Resume now validates declared experiment membership, child completion/config,
   finite summary-derived metrics and recorded checkpoint/manifest/summary hashes.

Legacy roots lacking verifiable hashes remain readable historical evidence but
cannot silently resume; use a new output directory. CLI names and valid data
schemas remain unchanged. Decision 0017 records the validation contract.

## Executed checks

Linux CPython 3.12.14, unchanged `requirements-training.lock`, CPU Torch 2.5.1,
SB3 2.7.1. Baseline suite: **107 passed**. Final suite: **116 passed**.
Focused calibration checks: **20 passed**, including unfair budgets/maps/
learning rates, changed configs/checkpoint/cached metrics, unknown rows and
legacy provenance. Existing valid resume and fresh sibling behavior passed.

Fresh CLI integration smoke (`artifacts/review2-audit-smoke`, ignored): requested
and actual 4096 agent transitions, 2048 world steps, parameters changed, checkpoint
reload matched. Two-agent development stochastic mean 1.75 -> 4.00; deterministic
0 -> 0. These are integration diagnostics, not Candidate J or robustness results.

## Remaining work

Phase 2B lives on `phase-2b`. Detector labels, final grouped partitions, windows,
learned detector/mitigation, decoy/intermittent modes, cautionary baseline and
held-out robustness evaluation are not completed by this correction. Broad
literature coverage remains ongoing. Do not claim a 30-paper survey is complete.
