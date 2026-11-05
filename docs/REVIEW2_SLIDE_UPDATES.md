# Review 2 Canva updates and speaking notes

Prepared and applied 5 November 2026. Browser access was restored after the
initial audit. The same 22-slide Canva design now includes the Phase 2B updates,
polished native text/tables/diagram, and revised speaking notes. All 22 slides
and their notes were checked after reloading the design to verify persistence.
Screenshots and the captured verification record are in `output/review2/`.

Design: https://www.canva.com/design/DAHZvTzceTU/oi6hDFDe_6nLpilrtBlSjw/edit

Preserve the white/turquoise/PES/orange Review 1 style, 22-slide order, template
section headings, project/team/guide/ID, and cover date **6 November 2026**.
Compare the live deck first and preserve any intervening user edits. Replace
stale future-tense Phase 2B statements; keep all charts/tables editable.

## Slide 2 - Introduction

**Slide text**

- Problem: can strictly local defense protect learned stigmergic retrieval under bounded false-food injection?
- Review 1: simulator, PPO, injection and timeout pipeline; useful pheromone benefit unverified.
- Review 2 / Phase 2A: fair trained baselines; Candidate J passed a three-seed clean stochastic development gate.
- Review 2 / Phase 2B: three negative attack calibrations, separated development corpus and inspectable agent-step CSV.
- Learned detector, final dataset and held-out robustness remain pending.

**Say:** “Our delta is both implementation and evidence quality. We checked
clean benefit before attacking the frozen policies. The attacks did not
consistently reduce delivery, so we preserved that outcome instead of claiming
a successful defense.” Phase 2A/2B are work packages, not academic phases.

**Sources:** historical decisions 0012-0016 at branch base 67b3c7a; fresh audit.

## Slide 4 - Suggestions from Review 1

Label these **shared faculty guidance**, not invented panel-specific feedback.

- Start with the gap and progress since Review 1: stated in the introduction.
- Demonstrate new code: calibration, observation masking, attack/corpus/CSV tooling and validation.
- Know the dataset: 108 reported development episodes, separated local/audit records; final labels and splits still pending.
- Deepen literature: critically compare current references; the 30+ relevant-paper target remains open.

**Say:** “We responded with code and a concrete data boundary, while retaining
the negative calibration results and incomplete research milestones.”

## Slide 5 - Scope and Objectives

- Simulation only; shared PPO uses 58-value local observations.
- Bounded, nonnegative false-food deposits at the selected agent's occupied cell.
- Completed: clean calibration, persistent-attack matrices, development corpus and CSV export.
- Next: accepted attack-calibration decision, validated exposure labels and grouped final partitions/windows.
- Future: local detector/mitigation, required baselines and unseen-condition evaluation.

**Say:** “No direct messages, trail-author trust or privileged detector inputs.
Phase 2B has four agents and one selected attacker: 25%. Do not reuse the old
eight-agent 12.5% caption for these results.”

## Slide 9 - Requirement Specification

- Seeded local-observation simulator, shared PPO and fair trained comparisons.
- Frozen checkpoint, matched clean/disabled/attacked scenarios and honest/team accounting.
- Reproducible manifests, complete scenario families and immutable outputs.
- Validated local record types/shapes, finite values and provenance consistency.
- Planned: residual-exposure labels, grouped partitions/windows and held-out evaluation.

**Say:** “Completed status alone is insufficient. The audit now rejects missing
scenarios, inconsistent group information and malformed local data.”

## Slide 10 - Proposed Architecture / Block Diagram

Use two clearly marked editable lanes, joined at collection:

```text
CURRENT
Seeded simulator -> local 58-value view -> shared PPO -> executed actions
                            |
Frozen clean policies + bounded persistent injection
                            |
Matched clean / injection-disabled / attacked rollouts
                            |
                +-----------+-----------+
                |                       |
      model_observable/              audit/
       local records         identities, events, mass,
                |             honest/global accounting
         agent-step CSV                |
     70 candidate local inputs          |
                +-----------+-----------+
                            |
PLANNED: validated exposure labels -> grouped partitions -> temporal windows
        -> local detector -> mitigation/baselines -> held-out evaluation
```

**Say:** “The corpus and CSV are implemented. Audit truth can support future
label construction, but never becomes a policy/detector input. There is no
trained detector here yet.” Directory names/scenario metadata are not features.

## Slide 11 - Further Implementation: code additions

| Component | New code / purpose |
| Phase 2A | observations.py masks 18 entries; calibration.py runs fair matrices and validates resume evidence |
| Local diagnostics | exposure.py and action_sensitivity.py measure visibility/input sensitivity, not detector scores |
| Phase 2B calibration | phase2b.py freezes checkpoints and records triplets; attacks.py adds separately declared delayed onset |
| Development corpus | phase2b_corpus.py separates local/audit trees and verifies complete groups |
| CSV view | phase2b_dataset.py creates agent-step rows and explicit schema; strict type/provenance checks |

**Say:** “This is the code delta beyond Review 1. Simulator mechanics, network,
learning settings and the recorded attack configurations were unchanged by the
November 5 audit. All substantially changed modules/tests explain their role.”

## Slides 12-15 - retain the Phase 2A comparison and J chart

Keep the fair separately trained baseline explanation, A-I failure history,
Candidate J setup and three-seed editable chart. Label the chart **previously
recorded clean stochastic development results**, not an independent rerun.

| Seed | Full | No-pheromone | Random | Full minus no-pheromone |
| 7 | 100.00 | 68.75 | 3.00 | +31.25 |
| 17 | 80.00 | 63.50 | 1.75 | +16.50 |
| 27 | 100.00 | 80.50 | 2.25 | +19.50 |

**Say:** “18 masked entries during both training and evaluation; the baseline
is trained from scratch. J passes a development gate, not statistical
significance or final robustness. Full deterministic means remain 100, 0, 60.”
Raw original checkpoints/CSV artifacts are unavailable in this checkout.

## Slide 16 - Further Implementation: demo and verification

**Slide text**

- Walkthrough: local input -> PPO action -> simulator transition -> separate local/audit logs -> corpus -> CSV/schema.
- Fresh Python 3.12.14 checks: Phase 2A **116 passed** (baseline 107); Phase 2B **162 passed** (baseline 124).
- Fresh 4,096-transition smoke passed update/reload checks; tiny genuine frozen-policy triplets passed corpus/CSV integration.
- Repeated outputs matched; checkpoints stayed unchanged; malformed/incomplete data is rejected.
- Historical J/full-corpus measurements are recorded evidence, not independently rerun here.

**Say:** “The demo can show code, schemas and tests without pretending the
original experiment files are in this clone. The small integration is not the
108-episode research matrix. Do not put its delivery numbers on J's chart.”

**Demo order:** open observations.py, calibration.py, phase2b.py, then the corpus
and exporter. Show schema input/provenance/outcome lists. Use completed original
artifacts only if recovered and verified; otherwise show the tiny test fixture
with an explicit integration-only label. Do not run the full J training live.

## Slide 17 - Any Other Information: Phase 2B attack results

**Slide text**

- Frozen J policies: 3 seeds x 4 maps x 3 scenarios = 36 episodes per calibration.
- One selected attacker among four agents (**25%**); same productive PPO movement.
- All three bounded persistent settings failed to establish consistent delivery degradation.
- Preserve negative findings; learned defense remains unproven.

Editable table or column chart (y-axis **mean honest-delivery injection loss,
food units**; show zero reference and negative values):

| Setting | Cap | First deposit | Mean loss |
| Immediate persistent | 20 | Transition 1 | -2.17 |
| Longer persistent | 200 | Transition 1 | -0.42 |
| Delayed persistent | 200 | Transition 201 | -2.25 |

Caption: **Previously recorded development results; no defense applied.**

**Say:** “Loss is disabled honest delivery minus attacked honest delivery.
Negative means attacked happened to deliver more in the paired mean; it does
not prove attacks are beneficial or harmless. Local input changes did not
establish consistent task damage under these settings.” If asked why: task
outcomes depend on trajectories and sampling; no confirmed causal explanation
has been established. Do not invent one.

## Slide 18 - Any Other Information: actual data and pending dataset work

**Slide text**

- Reported development archive: **36 groups, 108 episodes** across all three calibrations.
- Separate **model_observable/** local steps and **audit/** privileged metadata.
- Reported CSV: **412,016 agent-step rows** from **103,004 world transitions**.
- Schema: **58 observations + 12 history inputs**; **10 provenance + 9 outcome columns** excluded from default inputs.
- Still pending: exposure labels, final grouped partitions/windows, trained detector and learned-defense trajectories.

**Say:** “This is a development corpus and inspectable CSV, not a prepared
labelled detector dataset. The simulator knows injection events, but residual
exposure attribution still needs a definition and validation. Group maps and
related variants before windows; fit preprocessing only on training groups.
No row counts or split percentages have been invented.”

## Slide 19 - Capstone Project Timeline

Retain an editable timeline using relative academic phases, without inventing
calendar dates or implying these work packages are academic phases.

| Work | Review 1 | Review 2 | Next development | Held-out/final study |
| Simulator/shared PPO | Done | Reused | Maintain | Reproducibility audit |
| Literature | Ongoing | Extended comparison | 30+ target ongoing | Final synthesis |
| Clean calibration | Initial diagnostics | J gate recorded | Frozen-policy use | Required baselines |
| Persistent attack calibration | Foundation | Three negative matrices recorded | New accepted hypothesis | Withheld setting |
| Corpus/CSV | Initial logs | Development tooling complete | Label/split/window protocol | Final data audit |
| Learned detector/defense | Pending | Pending | Train/validate after gates | Evaluate once |

**Say:** “Negative attack calibration limits what we can claim. Finishing data
engineering does not mean detector/defense research is complete.”

## Slides 1, 3, 6-8, 20-22

Keep the cover, outline, critical current-reference literature slides,
bibliography and closing style. Ensure the outline still describes Phase 2B
progress and next work. Update closing notes to mention completed corpus/CSV
but pending labels and defense. Do not add unreviewed references or describe the
faculty's 30-paper expectation as complete.

## Speaker-note source links

Historical recorded evidence:

- https://github.com/AaryaTedla/stigmergy-robustness/blob/67b3c7a/docs/decisions/0012-phase2a-scout-follow-capacity.md
- https://github.com/AaryaTedla/stigmergy-robustness/blob/67b3c7a/docs/decisions/0013-phase2b-attack-calibration-contract.md
- https://github.com/AaryaTedla/stigmergy-robustness/blob/67b3c7a/docs/decisions/0014-phase2b-persistent-attack-duration.md
- https://github.com/AaryaTedla/stigmergy-robustness/blob/67b3c7a/docs/decisions/0015-phase2b-delayed-persistent-attack.md
- https://github.com/AaryaTedla/stigmergy-robustness/blob/67b3c7a/docs/decisions/0016-phase2b-development-calibration-corpus.md
- https://github.com/AaryaTedla/stigmergy-robustness/blob/67b3c7a/CHANGELOG.md

Fresh correction/evidence:

- https://github.com/AaryaTedla/stigmergy-robustness/commit/0ec8349
- https://github.com/AaryaTedla/stigmergy-robustness/commit/0aa1219
- https://github.com/AaryaTedla/stigmergy-robustness/blob/0aa1219/docs/REVIEW2_AUDIT.md

## Literature follow-through from the attached reading guide

The guide recommends eight papers. Seven already appeared as R1, R2, R3, R4,
R8, R9 and R11. Added **R17**, J. Schulman et al., “Proximal Policy Optimization
Algorithms,” arXiv:1707.06347 (2017), to slide 7 and the research references on
slide 21. Its role is the learning method, not evidence of swarm robustness.
Primary source: https://arxiv.org/abs/1707.06347 .

Verified R11's publisher metadata: K. O. Aina and S. Ha, *Artificial Life and
Robotics*, vol. 31, pp. 484–494 (2026), online publication 26 November 2025:
https://doi.org/10.1007/s10015-025-01089-z . Retained the verified revised-2024
arXiv citation for R9, rather than adopting the guide's unsupported 2025 label:
https://arxiv.org/abs/2302.03322 . Full R14 and R17 citations are in slide 21's
notes; software/data resources remain separate from research papers. The wider
30+ relevant-paper survey is still incomplete.

## Final live-deck acceptance (completed 5 November 2026)

Inspected all 22 slides, including original branding, spacing, editable
tables/chart/architecture, signed losses, separate J/attack populations,
cover date/order/outline and sources/notes. Corrected mixed text formatting,
diagram-arrow overlap and reference-table fit. Reopened the same design and
verified every slide and nonempty speaker notes persisted. The chart retains
all nine J values and labels its original runs as not independently rerun.
Slide 17 includes the three negative losses and explicitly states that the
measurements are recorded development results with no defense applied.
The source revision used for implementation status is merged main `72c1ddf`.
No simulator/policy changes or new experiment runs were made for this edit.
