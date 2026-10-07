"""Reproducible first-review demo using explicit scripted mechanics fixtures.

Run `python -m stigmergy.cli demo --config configs/env/development.json`.
The demo uses two known food cells on the right edge and sends alternating
agents to one assigned cell and back to nest cell (1, 1). This script reads
simulator positions to execute its fixture; it is neither a decentralized
policy nor a baseline and makes no learning or coordination claim.

Outputs: a terminal grid, summary.json (configuration, seed, source revision,
food accounting, and fixture label), and snapshot.svg with the final grid and
two pheromone heatmaps. Output directories must be fresh, preserving earlier
runs. To check repeatability run twice with the same config/seed in separate
directories: summary and SVG content should match. These are development
demonstration artifacts, not held-out evaluation data or attack trajectories.
"""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess

from .environment import GridConfig, ResourceRetrievalEnv


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


def main():
    """Expose only implemented commands; future training interfaces remain absent."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="scripted simulator mechanics fixture")
    demo.add_argument("--config", default="configs/env/development.json")
    demo.add_argument("--seed", type=int, default=7)
    demo.add_argument("--output", default="artifacts/aarya-demo")
    args = parser.parse_args()
    run_demo(args.config, args.seed, args.output)


if __name__ == "__main__":
    main()
