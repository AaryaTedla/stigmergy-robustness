# Capstone Agent Instructions

## Required reading

Before changing code, experiments, or research claims, read `README.md`, `docs/CONTEXT.md`, the relevant files in `docs/decisions/`, and the repository-local skill at `.agents/skills/capstone-implementation/SKILL.md`.

## Non-negotiable research boundaries

- Keep the task as simulated grid-based cooperative resource retrieval. Do not claim hardware or real-world validation.
- Use a parameter-shared PPO learned policy for any learned-policy claim. Rule-based results are debugging or baseline evidence only.
- Restrict the primary attacker to bounded, nonnegative false-food deposits at reachable occupied cells. Do not add erasure, negative deposits, global writes, reward tampering, or policy modification without an evidence-backed decision record.
- Keep the runtime defense local: local sensing, local history, revisitation, and own progress only. Never use attacker identities, global resource maps, privileged labels, or an extra direct communication channel as detector inputs.
- Preserve grouped episode/map splits before temporal-window creation. Hold out maps and attack configurations for final evaluation.
- Compare against the required undefended, no-pheromone, timeout, and documented cautionary-pheromone baselines.
- Do not claim the attack, minority disruption, cautionary pheromone, or dataset absence as novel. Keep publication claims conditional on results.

## Evidence and documentation

- Treat `docs/CONTEXT.md` as a distinction between verified facts, design commitments, and future work.
- Update it only after relevant checks pass and the change advances the agreed implementation.
- Add a `CHANGELOG.md` entry for each verified milestone or correction.
- Add a decision record before changing threat scope, field mechanics, data partitions, evaluation protocol, baseline capability, or contribution claim.
- Preserve negative results and incomplete milestones. Do not convert failed or uninvestigated experiments into conclusions.

## Completion standard

Run relevant tests and reproducibility checks before describing an implementation change as complete. Report which checks passed, which did not run, and any limitations that affect conclusions.

## Code explanations for the team

- Every code file you create or substantially change must begin with a detailed explanation before the implementation. For Python, use a module docstring after any mandatory interpreter/encoding header and before imports.
- Write for a teammate learning the project: explain the file's purpose, key concepts, inputs and outputs (including shapes, units, and conventions where relevant), execution flow, important assumptions, limitations, and how to run or use it. Scale detail to the file's complexity; small files need only the applicable points.
- Document important classes and functions with their responsibilities, parameters, return values, and non-obvious behavior. Explain why significant algorithms, update ordering, formulas, and constraints are used in comments beside the relevant code. Avoid comments that merely repeat the syntax.
- Distinguish scripted/debugging behavior from learned-policy behavior, and simulator-only metadata from model-observable inputs wherever applicable.
- Keep explanations synchronized with implementation changes. Tests and scripts need explanations too. For formats that cannot contain comments, such as JSON, document their fields and usage in a linked Markdown guide rather than adding invalid comments.
- Before handing off a milestone, check that a teammate can understand and run the code from these explanations and the README. Include these instruction changes in the commit so the next agent receives them.
