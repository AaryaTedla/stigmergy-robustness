"""CLI for fixtures, local debugging, shared PPO and development comparisons.

Run `python -m stigmergy.cli demo --config configs/env/development.json`.
The demo uses two known food cells on the right edge and sends alternating
agents to one assigned cell and back to nest cell (1, 1). This script reads
simulator positions to execute its fixture; it is neither a decentralized
policy nor a baseline and makes no learning or coordination claim.

Outputs: a terminal grid, summary.json (configuration, seed, source revision,
food accounting, and fixture label), and snapshot.svg with the final grid and
two pheromone heatmaps. The ``record-fixture`` command additionally saves one
clean, injection-disabled, or attacked trajectory with mass/provenance logs.
It uses the same privileged scripted route as the visual fixture and is
explicitly not a decentralized policy rollout or an evaluation result. Output
directories must be fresh, preserving earlier runs. To check repeatability run
twice with the same config/seed in separate directories: content should match.

``debug-policy`` uses only each agent's current 58-value local observation and
saves a seeded heuristic rollout summary. ``train`` lazily imports the optional
CPU PPO stack, takes grid/policy JSON configs, and saves checkpoints, development
diagnostics and provenance to a fresh output directory. These commands are
distinct from the privileged scripted fixtures above. See training.py and the
Shashannk walkthrough for transition units, seed partitions and limitations.
``compare-development`` adds six matched clean/control/attack/timeout variants,
local-history logs and static plots using a completed frozen PPO checkpoint.
It accepts only declared development maps, and is not final held-out evaluation.
"""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess

from .attacks import AttackConfig
from .environment import GridConfig, ResourceRetrievalEnv
from .policies import LocalDebugPolicy
from .trajectories import matched_attack_configs, record_episode


def snapshot_svg(env):
    """Draw labeled simulator cells and numerical field values for human inspection."""
    size, cell = env.config.size, 42
    width = size * cell
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{3 * (width + 24)}" height="{width + 75}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<text x="12" y="20" font-size="14">Scripted mechanics fixture — no learned policy</text>']
    for panel, title in enumerate(("Grid: N nest, F food, A agent", "Food pheromone", "Home pheromone")):
        origin = panel * (width + 24) + 12
        parts.append(f'<text x="{origin}" y="45" font-size="12">{title}</text>')
        for r in range(size):
            for col in range(size):
                if panel == 0:
                    count = (env.positions == (r, col)).all(axis=1).sum()
                    label = f"A{count}" if count else ("F" if env.food[r, col] else ("N" if env.nest[r, col] else ""))
                    color = "#dbeafe" if env.nest[r, col] else "#f1f5f9"
                else:
                    value = env.fields[panel - 1, r, col]
                    shade = int(255 - 160 * value / env.config.field_cap)
                    color = f"rgb({shade},255,{shade})" if panel == 1 else f"rgb({shade},{shade},255)"
                    label = f"{value:.1f}"
                x, y = origin + col * cell, 60 + r * cell
                parts.extend([f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{color}" stroke="#cbd5e1"/>',
                              f'<text x="{x + 5}" y="{y + 25}" font-size="12">{label}</text>'])
    return "\n".join(parts + ["</svg>"])


def run_demo(config_path, seed, output):
    """Execute the fixture and save inspectable food-accounting and field artifacts."""
    config = GridConfig(**json.loads(Path(config_path).read_text()))
    env = ResourceRetrievalEnv(config, render_mode="ansi")
    patches = [(1, config.size - 1), (config.size - 2, config.size - 1)]
    env.reset(seed=seed, options={"food_positions": patches})
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    print("Initial fixture grid:\n" + env.render())
    while env.agents:
        actions = {}
        for i, a in enumerate(env.agents):
            target = (1, 1) if env.carrying[i] else patches[i % 2]
            r, col = env.positions[i]
            actions[a] = (3 if r < target[0] else 1 if r > target[0] else
                          2 if col < target[1] else 4 if col > target[1] else 0)
        env.step(actions)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    summary = {"label": "scripted mechanics fixture; not a policy result", "seed": seed,
               "config": asdict(config), "source_revision": revision.stdout.strip() or "unknown",
               "working_tree_dirty": bool(dirty.stdout.strip()) if dirty.returncode == 0 else None,
               "steps": env.steps, "delivered": env.delivered_total,
               "remaining": int(env.food.sum()), "carried": int(env.carrying.sum()),
               "completed": not env.food.any() and not env.carrying.any()}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "snapshot.svg").write_text(snapshot_svg(env))
    print("\nFinal grid:\n" + env.render())
    print(json.dumps(summary, indent=2))
    env.close()
    return summary


def run_recorded_fixture(config_path, attack_config_path, scenario, seed, output):
    """Save one labelled scripted control/attack trajectory for audit only.

    The action provider reads simulator positions to reproduce the established
    visual fixture.  That privilege makes it unsuitable as a policy baseline,
    but useful for checking attack placement, control matching, and recorder
    provenance before a PPO policy exists.
    """
    config = GridConfig(**json.loads(Path(config_path).read_text()))
    base_attack = AttackConfig(**json.loads(Path(attack_config_path).read_text()))
    scenarios = matched_attack_configs(base_attack)
    if scenario not in scenarios:
        raise ValueError(f"scenario must be one of {', '.join(scenarios)}")
    environment = ResourceRetrievalEnv(config, attack_config=scenarios[scenario])
    patches = [(1, config.size - 1), (config.size - 2, config.size - 1)]

    def scripted_actions(_observations):
        """Follow known fixture coordinates; never treat this as a policy."""
        actions = {}
        for index, agent in enumerate(environment.agents):
            target = (1, 1) if environment.carrying[index] else patches[index % 2]
            row, column = environment.positions[index]
            actions[agent] = (3 if row < target[0] else 1 if row > target[0] else
                              2 if column < target[1] else 4 if column > target[1] else 0)
        return actions

    return record_episode(environment, seed, scenario, scripted_actions, output,
                          reset_options={"food_positions": patches})


def run_debug_policy(config_path, seed, output):
    """Roll out independently seeded local heuristic controllers; save diagnostics."""
    config = GridConfig(**json.loads(Path(config_path).read_text()))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    world = ResourceRetrievalEnv(config)
    observations, _ = world.reset(seed=seed)
    controllers = {a: LocalDebugPolicy(seed=seed + i) for i, a in enumerate(world.agents)}
    while world.agents:
        actions = {a: controllers[a].act(observations[a]) for a in world.agents}
        observations, _, _, _, _ = world.step(actions)
    from .trajectories import _git_provenance
    summary = {"label": "local rule-based debugging controller; not PPO evidence",
               "seed": seed, "config": asdict(config), "provenance": _git_provenance(),
               "steps": world.steps, "delivered": world.delivered_total}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    world.close()
    return summary


def main():
    """Expose scripted fixtures, the local debugging controller and clean PPO."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="scripted simulator mechanics fixture")
    demo.add_argument("--config", default="configs/env/development.json")
    demo.add_argument("--seed", type=int, default=7)
    demo.add_argument("--output", default="artifacts/aarya-demo")
    record = commands.add_parser("record-fixture", help="record a scripted attack/control fixture")
    record.add_argument("--config", default="configs/env/development.json")
    record.add_argument("--attack-config", default="configs/attack/persistent-review.json")
    record.add_argument("--scenario", choices=("clean", "injection_disabled", "attacked"),
                        default="attacked")
    record.add_argument("--seed", type=int, default=7)
    record.add_argument("--output", default="artifacts/rohan-fixture")
    debug = commands.add_parser("debug-policy", help="local rule-based policy diagnostic")
    debug.add_argument("--config", default="configs/env/development.json")
    debug.add_argument("--seed", type=int, default=7)
    debug.add_argument("--output", required=True)
    train = commands.add_parser("train", help="clean parameter-shared PPO development pilot")
    train.add_argument("--config", default="configs/env/development.json")
    train.add_argument("--policy-config", default="configs/policy/review-smoke.json")
    train.add_argument("--output", required=True)
    compare = commands.add_parser("compare-development", help="matched development PPO/timeout comparisons")
    compare.add_argument("--checkpoint", required=True)
    compare.add_argument("--attack-config", default="configs/attack/persistent-review.json")
    compare.add_argument("--comparison-config", default="configs/evaluation/review-development.json")
    compare.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "demo":
        run_demo(args.config, args.seed, args.output)
    elif args.command == "record-fixture":
        summary = run_recorded_fixture(args.config, args.attack_config, args.scenario, args.seed, args.output)
        print(json.dumps(summary, indent=2))
    elif args.command == "debug-policy":
        print(json.dumps(run_debug_policy(args.config, args.seed, args.output), indent=2))
    elif args.command == "train":
        from .training import run_training
        print(json.dumps(run_training(args.config, args.policy_config, args.output), indent=2))
    else:
        from .evaluation import run_development_comparison
        print(json.dumps(run_development_comparison(args.checkpoint, args.attack_config,
                                                   args.comparison_config, args.output), indent=2))


if __name__ == "__main__":
    main()
