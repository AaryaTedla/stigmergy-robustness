"""Static scientific development comparison figures from recorded episode rows.

plot_comparisons receives episode metrics/paired contrasts, the grid config,
and an existing output directory. It does not access a policy, resource map,
attack identity or runtime defense. It saves delivery_comparison.png/.svg and
paired_effects.png/.svg using matplotlib's headless Agg backend. Each bar is
the mean over displayed paired groups; overlaid dots show individual episodes
or contrasts, not confidence intervals or training-seed variability.

Team delivery plots include all six variants. Honest delivery plots include
only disabled/attacked variants, whose N-k honest population is matched; they
do not compare that population directly to the all-honest clean population.
Food units are counted per episode, not summed agent rewards. Deterministic
and stochastic modes occupy distinct panels. Captions identify development
conditions and compromised fraction, including the review's N=2/k=1 caveat.
Deterministic metadata/font SVG IDs permit repeated-data artifact comparison.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .evaluation import SCENARIOS

LABELS = ("Clean", "Clean\n+ timeout", "Disabled", "Disabled\n+ timeout", "Attack", "Attack\n+ timeout")


def _bars_and_points(ax, samples, labels, color):
    """Draw sample means and visible individual observations without CI claims."""
    positions = np.arange(len(samples))
    ax.bar(positions, [np.mean(s) for s in samples], color=color, alpha=0.75, width=0.65)
    for x, values in enumerate(samples):
        offsets = np.linspace(-0.16, 0.16, len(values)) if len(values) > 1 else [0]
        ax.scatter(x + np.asarray(offsets), values, color="#172b4d", s=22, zorder=3)
    ax.set_xticks(positions, labels, fontsize=9)
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)


def _save(figure, output, name):
    """Save reproducible PNG/SVG content and release the figure resources."""
    figure.savefig(Path(output) / f"{name}.png", dpi=150, metadata={"Software": "stigmergy review"})
    figure.savefig(Path(output) / f"{name}.svg", metadata={"Date": None, "Creator": "stigmergy review"})
    plt.close(figure)


def plot_comparisons(rows, contrasts, grid, output):
    """Create delivery and paired-effect figures from deterministic metric rows."""
    modes = tuple(dict.fromkeys(r["action_mode"] for r in rows))
    attack = next(r for r in rows if r["scenario"] == "attacked")
    caption = (f"Development integration only | N={grid.n_agents}, k={attack['compromised_count']} "
               f"({attack['compromised_fraction']:.1%}) | one training seed\n"
               "Bars: means; dots: paired groups. No final held-out or training-seed uncertainty claim.")
    with plt.rc_context({"svg.hashsalt": "stigmergy-review-v1", "font.family": "DejaVu Sans"}):
        figure, axes = plt.subplots(2, len(modes), figsize=(7 * len(modes), 8), squeeze=False)
        for column, mode in enumerate(modes):
            for row_index, (field, scenarios, labels) in enumerate((
                    ("total_delivered", SCENARIOS, LABELS),
                    ("honest_delivered", SCENARIOS[2:], LABELS[2:]))):
                samples = [[r[field] for r in rows if r["action_mode"] == mode and r["scenario"] == scenario]
                           for scenario in scenarios]
                ax = axes[row_index, column]
                _bars_and_points(ax, samples, labels, "#2886af" if row_index == 0 else "#7975b5")
                ax.set_ylim(0, 2 * grid.food_per_patch + 0.5)
                ax.set_ylabel("Food delivered (units)")
                ax.set_title(f"{mode.capitalize()}: {'all agents' if row_index == 0 else 'matched honest agents'}")
        figure.suptitle("PPO and timeout: development delivery comparisons", fontsize=16)
        figure.text(0.5, 0.035, caption, ha="center", fontsize=10)
        figure.subplots_adjust(top=0.89, bottom=0.19, hspace=0.65, wspace=0.25)
        _save(figure, output, "delivery_comparison")

        figure, axes = plt.subplots(1, len(modes), figsize=(7 * len(modes), 5), squeeze=False)
        fields = ("injection_loss_units", "timeout_gain_units", "clean_cost_units", "disabled_cost_units")
        labels = ("Injection loss", "Timeout gain\nunder attack", "Clean cost\nof timeout", "Disabled cost\nof timeout")
        for column, mode in enumerate(modes):
            samples = [[r[field] for r in contrasts if r["action_mode"] == mode] for field in fields]
            ax = axes[0, column]
            _bars_and_points(ax, samples, labels, "#5a9b78")
            ax.axhline(0, color="#172b4d", linewidth=1)
            ax.set_ylabel("Paired difference (food units)")
            ax.set_title(mode.capitalize())
        figure.suptitle("Paired effects: retain zero and negative outcomes", fontsize=16)
        figure.text(0.5, 0.035, caption, ha="center", fontsize=10)
        figure.subplots_adjust(top=0.82, bottom=0.30, wspace=0.25)
        _save(figure, output, "paired_effects")
