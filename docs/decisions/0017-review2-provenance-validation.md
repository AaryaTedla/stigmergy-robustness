# Decision 0017: Review 2 provenance and input validation

**Status:** Accepted for implementation; verification recorded separately

**Date:** 2026-11-05

**Owners and reviewers:** Capstone team; authorized Review 2 audit

## Decision

Strengthen existing calibration/data validation without changing simulator,
PPO, threat, field, split or evaluation behavior. Require paired Phase 2A
policy configurations to match except observation mode. New calibration roots
bind all candidate/policy configuration bytes and policy-relevant source files;
resume reuses completed rows only when their immutable training artifacts
still match recorded hashes and their metrics/configuration agree. A legacy
root without this evidence is preserved but must use a fresh output directory
rather than silently resume unverifiable work.

Phase 2B will inherit this correction. Its corpus/export validators will require
unique complete clean/control/attack groups, consistent group provenance and
explicit local-record types/shapes. Non-finite values, invalid actions and
privileged or unknown local fields must fail closed. Generated data remains
development-only, with no new labels, windows, partitions or detector.

## Context and evidence

The audit reproduced acceptance of mismatched baseline budgets/maps, NaN/Inf
inputs and invalid actions, missing scenario families, and conflicting map
provenance. Current checked-in Phase 2A pairs themselves match. Existing test
fixtures do not cover these malformed inputs; these findings do not invalidate
or independently reproduce historical research results.

## Alternatives considered

- Trust completed status or root-plan hash alone: rejected; referenced files
  can change without changing that hash.
- Rewrite old artifacts or retrain all policies: rejected; preserve history.
- Change attacks to obtain a gap: excluded from this audit.

## Consequences

CLI commands and valid data schemas remain unchanged. New provenance fields
are additive; strict resume rejects legacy roots lacking verifiable hashes.
No policy/environment source changes are required, preserving frozen-policy
compatibility. Historical reported numbers remain reported, not rerun results.

## Validation and context update

Run separate pinned Python 3.12 baseline/final suites, malformed-input and
resume regression tests, a small PPO/checkpoint plus matched-rollout smoke,
and reproducible corpus/CSV checks. Record actual results and unavailable
historical artifacts in the audit, context and changelog only after checks.

## Phase 2A verification

Pinned Python 3.12.14 baseline 107 / final 116 tests passed; focused calibration
checks 20 passed and a fresh 4096-transition update/reload smoke passed. See
[the audit](../REVIEW2_AUDIT.md). Phase 2B checks are recorded on its branch.
