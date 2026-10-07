# First capstone review: team milestones and agent handoff

This is the agreed first-review implementation plan, not a record of completed research. Read `AGENTS.md`, `README.md`, `docs/CONTEXT.md`, the repository-local implementation skill, and relevant decision records before acting. Verified progress belongs in `docs/CONTEXT.md`; inspect the code and checks rather than assuming this plan proves completion.

## Minimal startup prompt

```text
Read and follow AGENTS.md, docs/CONTEXT.md, and .agents/skills/capstone-implementation/SKILL.md before working.
I am <teammate name>. Continue my first-review milestone.
```

The startup instruction plus an identifiable teammate name is sufficient to request continuation. Match names case-insensitively; recognize an unambiguous spelling variant (for example, Shashank for Shashannk). Ask for clarification only when the owner cannot be identified reliably.

## Work sequence and deliverables

| Order | Owner | Suggested branch | First-review target |
| --- | --- | --- | --- |
| 1 | Aarya | `feat/environment-pilot` | Deterministic grid environment, movement/pickup/delivery, bounded food/home pheromone mechanics, local observations, tests, and visual mechanics demo. |
| 2 | Shashannk | `feat/shared-ppo-pilot` | Local-observation debugging controller, initial parameter-shared PPO training pipeline, validated adapter/dependencies, and a reproducible short training run with honest reporting of learning outcomes. |
| 3 | Rohan | `feat/attack-logging-pilot` | One bounded nonnegative false-food injection mode at occupied reachable cells, per-step/episode budgets, requested/applied mass logs, trajectory provenance, and matched clean/injection-disabled/attacked controls. |
| 4 | Tusti | `feat/local-defense-pilot` | Local history features, a documented timeout defense, and reproducible initial clean/control/attacked/defended comparisons and plots on development conditions. |

These are limited review milestones. They do not replace the full study: all attack modes, detector development, held-out evaluation, a separately trained no-pheromone baseline, cautionary-pheromone adaptation, and required uncertainty reporting remain mandatory later. A short PPO run verifies a pipeline only unless evidence supports a learning claim. Scripted results cannot satisfy learned-policy evidence. Preliminary plots do not establish robustness.

## How the next agent continues

1. Identify the named owner and inspect git status, branch/history, code, context, and decision records. Preserve existing user changes. Announce the concrete next task briefly.
2. Check earlier milestones needed by that owner. Prefer a new milestone branch based on the updated `main` after the preceding branch is merged. Do not assume a merge occurred or switch branches over unrelated uncommitted work. If a prerequisite is absent, identify the missing dependency; continue independent work where possible rather than silently completing another owner's milestone.
3. Continue the named milestone from its next incomplete, unverified, or broken component. Do not redo verified work. If it is already complete, report the evidence and checkpoint; do not automatically advance to the next owner. Branch labels represent responsibility, not authorship.
4. Implement the smallest coherent deliverable, integrate with existing interfaces, and follow the code-explanation requirements in `AGENTS.md`. Owners mostly use separate modules; environment hooks, CLI, dependencies, integration tests, and documentation may overlap. Record required design decisions before changing mechanics, threat capability, observations, or evaluation semantics.
5. Run relevant checks and reproducibility runs. Preserve unsuccessful experiments and distinguish pipeline success from performance evidence. Keep policy/defense inputs local, and preserve grouped map/episode splits before temporal windows. Use development conditions only for this review; do not tune on held-out final conditions.
6. Update verified context/changelog and provide a teammate walkthrough: files, usage, explanations, tests, observed results, limitations, and remaining work. Report unrun checks explicitly.
7. Stop at the named owner's reviewable checkpoint. The user commits, pushes, and merges before the next milestone. Do not commit, push, merge, or proceed to another owner's implementation unless explicitly requested.

## Progress at plan creation

At creation on 2026-10-07, Aarya's clean simulator was implemented and mechanically verified, with team review pending; see `docs/AARYA_FIRST_REVIEW.md` and `docs/CONTEXT.md`. Later owners' milestones were unimplemented. This is a historical snapshot: use current verified context and repository evidence to determine today's state.
