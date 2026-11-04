# Phase 2B dataset roadmap and review architecture

This document gives the project-review answer for the literature delta,
architecture and coding roadmap. It distinguishes implemented evidence from
the planned final dataset and detector work. The current corpus is a verified
development-only archive, not evidence that a detector or defense works.

## A. Delta from literature to project deliverable

Existing work already shows that misleading pheromone can disrupt simulated
foraging, that a malicious minority can matter, and that cautionary pheromone
is a possible mitigation. Learned stigmergic coordination also exists. The
project therefore does **not** claim those ideas as new.

The reviewed literature did not establish a public, standardized dataset that
combines parameter-shared learned coordination, a shared pheromone field,
bounded local false-food injection, matched controls and local-only defense
inputs. The project delta is a reproducible evaluation/data pipeline for that
specific protocol:

| Literature/design gap | Project response | Evidence status |
| --- | --- | --- |
| Attack effects are often not recorded as leakage-audited local trajectories. | Save local observations separately from simulator-only attack provenance. | Implemented: Phase 2B corpus. |
| Clean versus attacker-designation effects can be confounded. | Use matched clean, injection-disabled and attacked episode families. | Implemented: 108 development episodes. |
| Random row splits leak correlated trajectories. | Preserve complete policy/map/action/attack families as groups before any windows. | Implemented for development corpus; final split remains future work. |
| A local detector must not see attacker identity, global map or attack timing. | Restrict model input to local observation and local history; keep provenance in audit files. | Implemented data boundary; detector not yet fit. |
| Robustness needs unseen maps and attacks. | Reserve maps and an attack configuration before final windows/model selection. | Not yet implemented. |

The important current result is also a delta in *evidence quality*: three
bounded persistent-attack calibrations did **not** consistently reduce
delivery. That negative result is preserved in the corpus rather than hidden
or turned into an unsupported detector claim.

## B. Architecture block diagram and roadmap

```text
                     Versioned grid / map / seed configuration
                                      |
                                      v
              +-------------------------------------------+
              | Cooperative resource-retrieval simulator  |
              | shared food + home pheromone fields        |
              +-------------------------------------------+
                    |                         |
                    | local 58-value view     | simulator truth only
                    v                         v
       +--------------------------+   +---------------------------+
       | Shared PPO policy        |   | Bounded false-food attack |
       | same parameters/agent    |   | occupied-cell deposits    |
       +--------------------------+   +---------------------------+
                    |                         |
                    +------------+------------+
                                 v
                    Matched episode collection
              clean / injection-disabled / attacked
                                 |
                 +---------------+----------------+
                 v                                v
  model_observable/                         audit/
  local observations, actions,              attack events, attacker ID,
  local features and own progress           mass and global delivery
                 |                                |
                 v                                v
       agent-step CSV export                 provenance / later labels
       (current coding deliverable)          never model inputs
                 |
                 v
  Future only after approved attack and split protocol:
  grouped train/validation/test -> temporal windows -> local detector
  -> bounded local mitigation -> held-out robustness evaluation
```

Roadmap:

1. **Completed:** clean simulator, shared PPO pipeline, Candidate J clean gate,
   persistent attack calibrations, leakage-separated development corpus.
2. **Completed in this codebase:** tabular agent-step export. It makes the
   local records inspectable in a spreadsheet/dataframe without reading audit
   files, training a model or creating invalid row-level splits.
3. **Next, needs an accepted decision:** specify and implement a new bounded
   attack calibration such as decoy or intermittent injection. It must retain
   the occupied-cell, nonnegative, budgeted threat boundary and matched
   controls.
4. **Then:** collect complete episode groups on development and reserved maps;
   assign grouped train/validation/test partitions before building windows.
5. **Then:** train only local-input detector candidates on training groups;
   select threshold/mitigation on validation groups; report once on held-out
   maps and at least one withheld attack configuration.

## C. Additional coding deliverable

`phase2b-export-agent-steps` adds a concrete data-engineering component for
the review. It converts a completed corpus into `agent_steps.csv`, with one
row per agent per completed environment transition. The generated
`schema.json` explicitly identifies which columns may be used as local model
inputs and which are provenance or outcome columns.

Run it from the repository root using a fresh output directory:

```bash
python -m stigmergy.cli phase2b-export-agent-steps \
  --corpus data/generated/phase2b-development-calibration-corpus-003 \
  --output data/generated/phase2b-agent-steps-001
```

The CSV includes 58 `observation_before_*` columns and 12 named
`history_*` columns as the local input view. Group/map/scenario/seed columns
are provenance-only; executed action, reward and own pickup/delivery/blocked
state are local transition outcomes. The command rejects corpus records that
contain attack events, attacker identity, injected mass or global delivery in
their local record. It neither opens nor exports the audit tree.

This supports data inspection and loader/prototype development. It does not
create temporal windows, a train/validation/test partition, detector labels,
a fitted model or a robustness result.
