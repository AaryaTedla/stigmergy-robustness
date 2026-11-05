# Review 2 branch audit - 5 November 2026

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

## Phase 2B follow-through

Audited base `67b3c7a36dd07e588807b80f31663037ee58ec45` on `phase-2b`,
which descends from the Phase 2A base. Applied Phase 2A correction `0ec8349`
while retaining all Phase 2B code, decision records and negative results.

The audit reproduced these additional defects before correction:

- CSV accepted non-finite observations/features/rewards, out-of-range actions
  and non-Boolean terminal outcomes.
- An index containing only clean, with missing disabled/attacked episodes, could
  be accepted as completed input. Manifest duplicate groups were not rejected.
- Source manifest/split group map provenance could disagree while IDs matched.

The corpus and CSV boundary now share an explicit local-record validator.
Documented local fields, per-agent keys, shapes, finite values, action range and
Boolean event/outcome flags are checked. Complete unique scenario families and
map/policy/action/split provenance must agree. CSV paths must stay inside the
model-observable tree; the exporter never reads privileged audit step files.
Original output schemas and CLI names remain unchanged.

### Executed Phase 2B checks

- Baseline: **124 passed** on the unmodified Phase 2B base.
- Final: **162 passed**, Python 3.12.14 with the unchanged CPU training lock.
- Package consistency check passed. ReportLab/PyPDF were added only as document
  tooling to the temporary environment, not as project training requirements.
- Genuine tiny four-agent PPO fixture: completed checkpoint reload, matched
  frozen-policy clean/disabled/attack triplets twice, identical aggregate
  reports, unchanged checkpoint bytes, repeated corpus and agent-step exports.
  Agent-step counts equal four times environment-step counts. This is a short
  integration fixture, not the Candidate J development matrix.
- Regression checks reject unfair paired configs, changed resume evidence,
  missing/duplicate scenarios/groups, map/split mismatches, audit paths, unknown
  local fields, NaN/Inf, invalid actions and non-Boolean outcomes.
- Repeated JSON-only corpus/export fixtures matched byte-for-byte. Existing
  output directories were refused; malformed writes retained failed status and
  simulated interrupts retained incomplete status.
- `git diff --check` passed. Simulator, PPO implementation/configurations and
  attack configuration files are unchanged by the correction.

### Historical results and unavailable evidence

Decision 0012 records Candidate J full/no-pheromone/random stochastic means
100/68.75/3, 80/63.50/1.75 and 100/80.50/2.25 (seeds 7/17/27), with mixed
full deterministic means 100/0/60. Decisions 0013-0015 record mean honest
injection losses -2.17/-0.42/-2.25. Decision 0016 and the 2026-11-02 changelog
record 108 episodes, 36 development groups, 103,004 world transitions and
412,016 agent-step rows. These records were checked for agreement, but the
original checkpoints/calibration directories/generated corpus are not available
locally or tracked in Git. They were not recreated or independently rerun.

### Presentation and learning handoff

The last saved 22-slide Canva deck predates Phase 2B's completed calibration,
corpus and CSV tooling. `REVIEW2_SLIDE_UPDATES.md` supplies specific replacement
text and notes while retaining its style, headings and slide count. No browser
or connected document session is currently available, so live Canva inspection,
edits and saved-state verification are **pending**, not completed.

The learning guide source and renderer accompany this branch; final PDF checks
are recorded in the documentation entry after generation. Preserve the older
handbook and do not describe the wider research roadmap or 30+ paper expectation
as complete. Pushes are authorized by the explicit Review 2 audit request.
