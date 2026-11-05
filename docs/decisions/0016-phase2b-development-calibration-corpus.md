# Decision Record: Phase 2B development calibration corpus

**Status:** Completed; development-only calibration corpus built

**Date:** 2026-11-01

**Owners and reviewers:** Capstone team

## Decision

Package the three completed Phase 2B persistent-attack calibration runs into a
versioned, reproducible, development-only trajectory corpus. The corpus will
contain the 20-unit immediate, 200-unit immediate and 200-unit delayed
calibrations: 36 complete episodes each, for 108 episodes total. It will keep
every clean, injection-disabled and attacked variant of each policy/map/action/
attack-configuration family in one immutable development group.

The build will write policy-visible step records separately from audit-only
attack metadata. It will not create temporal windows, train/validation/test
partitions, detector labels, a detector, a defense, or a final dataset claim.
All corpus groups are explicitly development-only.

## Context and evidence

The completed Phase 2B runs already save local trajectory records, episode
metrics and group manifests, but they live as separate experiment artifacts.
The first two immediate persistent settings and the delayed setting all failed
to establish consistent degradation. That blocks detector fitting and a
robustness claim, but not the useful data-engineering milestone of preserving
the audited calibration evidence in a consistent, leakage-aware form.

The corpus therefore records the negative result rather than selecting only a
favourable run. It is an archive for inspection, schema validation and later
protocol work. Attack identity, requested/authorized/applied mass, attack
events, honest/global delivery and scenario provenance remain audit-only. They
must not be used as model input.

## Alternatives considered

- Call the corpus a detector-training dataset: rejected because the attacks did
  not reliably degrade delivery and no train/validation/final split exists.
- Keep only the latest delayed run: rejected because it would hide two valid
  negative calibrations and reduce attack-setting provenance.
- Merge rows from related scenarios into random splits: rejected because it
  would leak policy/map/action/attack-family information across future windows.
- Delay all data work until a successful attack: rejected because a verified,
  clearly limited corpus advances reproducibility without overstating results.

## Consequences

Add a corpus-builder command and versioned source plan. It must verify each
source run is completed, preserve source hashes, refuse incomplete scenario
families, assign collision-free corpus group IDs, and fail if simulator-only
keys appear in model-visible records. Generated corpus files remain local under
`data/generated/`; source code, plan, tests and this decision are versioned.

The corpus is not evidence that false pheromone is detectable, that a defense
works, or that the project has a final research dataset. Future detector work
requires a new accepted attack-effect and split/evaluation decision.

## Validation and context update

Run focused corpus tests for source validation, complete-group preservation and
metadata separation, then the full suite. Build a fresh corpus directory and
verify 108 episodes, 36 intact development groups, three scenarios per group,
and absence of attack metadata in model-visible files. Record only the executed
result in context and changelog.

## Result

The fresh local corpus completed on pinned Linux Python 3.12.14 in
`data/generated/phase2b-development-calibration-corpus-002/`. It packages all
three completed calibration runs into 36 complete development groups and 108
episodes (three scenarios per group). It contains 108 model-observable step
files and 108 matching audit step files. The generated group manifest preserves
every scenario family together; no train/validation/test partition or temporal
window was created.

The boundary audit found zero occurrences of simulator-only attack metadata in
the model-observable tree. Focused corpus tests passed 3 cases; the focused
corpus/Phase 2B/attack checks passed 26 cases; and the complete suite passed
122. This is a reproducibility and data-engineering milestone only. The corpus
does not establish an effective attack, detector label, defense, final dataset
or robustness result.
