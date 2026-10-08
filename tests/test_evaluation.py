"""Development defense integration checks, not research robustness tests.

Run python -m pytest tests/test_evaluation.py with the training dependencies.
Tiny genuine PPO checkpoints avoid oracle/scripted evaluation claims. Tests
audit local-only controller inputs and executed-action history, matched control
records, simulator-only attacker labels, honest delivery counting, immutable
checkpoints, disjoint development map restrictions, exact repeated metrics and
plot artifacts. Explicit contrast fixtures preserve undefined recovery and
negative outcomes; intentional plotting failures check partial-run provenance.
"""

from dataclasses import asdict
import hashlib
import json

import numpy as np
import pytest

pytest.importorskip("stable_baselines3")
import torch
from stable_baselines3 import PPO

from stigmergy import AttackConfig, GridConfig
from stigmergy.evaluation import (DevelopmentComparisonConfig, LocalPPOEpisodeController,
    SCENARIOS, paired_contrasts, rollout_comparison_episode, run_development_comparison)
from stigmergy.training import TrainingConfig, run_training


@pytest.fixture(scope="module")
def completed_checkpoint(tmp_path_factory):
    """Build a tiny real shared PPO run with one declared diagnostic development map."""
    root = tmp_path_factory.mktemp("evaluation-policy")
    grid = root / "grid.json"
    policy = root / "policy.json"
    grid.write_text(json.dumps(asdict(GridConfig(horizon=4))))
    policy.write_text(json.dumps(asdict(TrainingConfig(total_transitions=8, n_steps=4,
        batch_size=4, n_epochs=1, train_map_seeds=(1,), diagnostic_map_seeds=(2,)))))
    run_training(grid, policy, root / "training")
    return root / "training" / "policy.zip"


def inputs(tmp_path, **kwargs):
    """Save comparison/attack JSON fields in the documented public schema."""
    comparison = tmp_path / "comparison.json"
    attack = tmp_path / "attack.json"
    settings = asdict(DevelopmentComparisonConfig(map_seeds=(2,), action_seeds=(7, 19)))
    settings.update(kwargs)
    comparison.write_text(json.dumps(settings))
    attack.write_text(json.dumps(AttackConfig().as_dict()))
    return attack, comparison


def test_controller_uses_local_rows_and_executed_action_history():
    class LocalRowsOnly:
        """Spy policy rejects augmented rows and proposes east to each local agent."""

        def predict(self, rows, deterministic):
            assert rows.shape == (2, 58) and np.isfinite(rows).all()
            return np.full(2, 2), None

    obs = {a: np.zeros(58, dtype=np.float32) for a in ("agent_0", "agent_1")}
    config = DevelopmentComparisonConfig(timeout=1)
    controller = LocalPPOEpisodeController(LocalRowsOnly(), obs, config, True, True)
    first, _ = controller.act(obs)
    assert list(first.values()) == [2, 2]
    second, _ = controller.act(obs)
    assert list(second.values()) == [0, 0]  # timeout overrides east with stay
    _, local = controller.act(obs)
    assert all(features[11] == pytest.approx(1 / 3) for features in local["features"].values())
    renamed = {"label_a": obs["agent_0"], "label_b": obs["agent_1"]}
    fresh = LocalPPOEpisodeController(LocalRowsOnly(), renamed, config, True, True)
    actions, diagnostics = fresh.act(renamed)
    assert list(actions.values()) == [2, 2]
    assert not any(diagnostics["timeout_active"].values())
    assert set(diagnostics) == {"features", "proposed_actions", "executed_actions", "timeout_active"}


def test_repeated_comparisons_controls_accounting_and_plot_artifacts(completed_checkpoint, tmp_path):
    attack, comparison = inputs(tmp_path)
    checkpoint_hash = hashlib.sha256(completed_checkpoint.read_bytes()).hexdigest()
    first = run_development_comparison(completed_checkpoint, attack, comparison, tmp_path / "a")
    second = run_development_comparison(completed_checkpoint, attack, comparison, tmp_path / "b")
    assert first == second and first["episode_count"] == 18  # no duplicate deterministic seeds
    assert first["checkpoint_unchanged"] and first["not_a_minority_study"]
    assert hashlib.sha256(completed_checkpoint.read_bytes()).hexdigest() == checkpoint_hash
    for name in ("episodes.csv", "contrasts.csv", "delivery_comparison.png", "delivery_comparison.svg",
                 "paired_effects.png", "paired_effects.svg"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
    manifest = json.loads((tmp_path / "a" / "manifest.json").read_text())
    assert manifest["status"] == "completed" and len(manifest["groups"]) == 3
    for group in manifest["groups"]:
        assert group["split"] == "development" and tuple(group["scenarios"]) == SCENARIOS
        group_path = tmp_path / "a" / "episodes" / group["group_id"]
        for clean, disabled in (("clean", "injection_disabled"), ("clean_timeout", "injection_disabled_timeout")):
            clean_steps = [json.loads(line) for line in (group_path / clean / "steps.jsonl").read_text().splitlines()]
            disabled_steps = [json.loads(line) for line in (group_path / disabled / "steps.jsonl").read_text().splitlines()]
            assert [s["local"] for s in clean_steps] == [s["local"] for s in disabled_steps]
        selected = []
        for scenario in SCENARIOS[2:]:
            episode = json.loads((group_path / scenario / "episode.json").read_text())
            metadata = episode["simulator_metadata"]
            selected.append(metadata["compromised_agents"])
            honest = sum(v for a, v in metadata["deliveries_by_agent"].items() if a not in selected[-1])
            assert episode["metrics"]["honest_delivered"] == honest
            assert episode["metrics"]["compromised_fraction"] == 0.5
            assert episode["metrics"]["applied_mass"] <= 20
        assert all(ids == selected[0] for ids in selected)


@pytest.mark.parametrize("attacked,expected_loss", [(1, 2), (3, 0), (4, -1)])
def test_paired_formulas_and_undefined_recovery(attacked, expected_loss):
    honest = (5, 4, 3, 2, attacked, 2)
    rows = [{"group_id": "fixture", "scenario": scenario, "action_mode": "stochastic",
             "honest_delivered": value, "total_delivered": value}
            for scenario, value in zip(SCENARIOS, honest)]
    contrast = paired_contrasts(rows)[0]
    assert contrast["injection_loss_units"] == expected_loss
    assert contrast["timeout_gain_units"] == 2 - attacked
    assert contrast["clean_cost_units"] == contrast["disabled_cost_units"] == 1
    assert contrast["recovery_fraction"] == (0.5 if expected_loss > 0 else None)


def test_rejects_heldout_maps_and_changed_checkpoint(completed_checkpoint, tmp_path):
    attack, comparison = inputs(tmp_path, map_seeds=[9999])
    with pytest.raises(ValueError, match="diagnostic maps"):
        run_development_comparison(completed_checkpoint, attack, comparison, tmp_path / "heldout")
    assert not (tmp_path / "heldout").exists()
    attack, comparison = inputs(tmp_path)
    model = PPO.load(completed_checkpoint, device="cpu")
    with torch.no_grad():
        next(model.policy.parameters()).add_(0.1)
    changed = completed_checkpoint.parent / "changed.zip"
    model.save(changed)
    with pytest.raises(ValueError, match="does not match"):
        run_development_comparison(changed, attack, comparison, tmp_path / "changed-output")
    assert not (tmp_path / "changed-output").exists()


def test_zero_injection_controls_preserve_no_loss(completed_checkpoint, tmp_path):
    model = PPO.load(completed_checkpoint, device="cpu")
    config = DevelopmentComparisonConfig(map_seeds=(2,))
    rows = []
    for scenario in ("injection_disabled", "attacked"):
        row, _ = rollout_comparison_episode(model, GridConfig(horizon=4), AttackConfig(episode_budget=0),
            config, 2, 7, "stochastic", scenario, tmp_path / scenario)
        rows.append(row)
    assert rows[0]["honest_delivered"] == rows[1]["honest_delivered"]
    assert rows[0]["local_record_sha256"] == rows[1]["local_record_sha256"]
    assert rows[1]["applied_mass"] == 0


def test_failed_plotting_retains_partial_run(completed_checkpoint, tmp_path, monkeypatch):
    from stigmergy import evaluation_plots
    attack, comparison = inputs(tmp_path, action_modes=["deterministic"])

    def fail_plot(*args, **kwargs):
        raise RuntimeError("deliberate plot failure fixture")

    monkeypatch.setattr(evaluation_plots, "plot_comparisons", fail_plot)
    with pytest.raises(RuntimeError, match="deliberate plot"):
        run_development_comparison(completed_checkpoint, attack, comparison, tmp_path / "failed")
    manifest = json.loads((tmp_path / "failed" / "manifest.json").read_text())
    assert manifest["status"] == "failed" and (tmp_path / "failed" / "episodes.csv").is_file()


@pytest.mark.parametrize("kwargs", [{"purpose": "final_test"}, {"map_seeds": [1, 1]},
                                    {"timeout": 0}, {"action_modes": ["oracle"]}])
def test_invalid_comparison_config(kwargs):
    with pytest.raises(ValueError):
        DevelopmentComparisonConfig(**kwargs)
