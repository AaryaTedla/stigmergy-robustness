"""Report frozen full-policy action sensitivity to locally visible pheromone.

The script replays a saved full-input PPO checkpoint on its declared Phase 2A
diagnostic maps.  Before every action, it obtains the policy's categorical
distribution for the genuine 58-value local observation and again after
zeroing only its 18 food/home pheromone values.  It aggregates distribution
differences and does not alter the action used for the rollout.  This keeps
the rollout, simulator, reward, map seeds and checkpoint immutable while
testing whether local field values can affect the learned policy.

Example:
    .venv-phase2a/bin/python scripts/phase2a_action_sensitivity.py \
      --checkpoint artifacts/phase2a/scout-follow-run-001/candidate_g_12x12_scout_follow/full-seed-7/policy.zip \
      --config configs/phase2a/env/candidate_g_12x12_scout_follow.json \
      --policy-config configs/phase2a/policy/full_seed_7.json \
      --output artifacts/phase2a/action-sensitivity-candidate-g-seed-7

The output is development-only diagnostic evidence.  A changed distribution
does not establish that pheromone improves delivery, and this script never
creates Phase 2B labels, attacks, detectors or datasets.
"""

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
import torch
from stable_baselines3 import PPO

from stigmergy.action_sensitivity import LocalActionSensitivity
from stigmergy.environment import GridConfig, ResourceRetrievalEnv
from stigmergy.observations import PHEROMONE_INDICES, apply_observation_mode
from stigmergy.training import TrainingConfig
from stigmergy.trajectories import _git_provenance


def _action_probabilities(model, observations):
    """Return CPU NumPy categorical probabilities for an observation batch.

    Stable-Baselines3 keeps the policy distribution behind its PyTorch policy
    object.  ``obs_to_tensor`` preserves the model's expected dtype/device;
    detached CPU values make this diagnostic independent of gradient state.
    """
    tensor, _ = model.policy.obs_to_tensor(observations)
    with torch.no_grad():
        return model.policy.get_distribution(tensor).distribution.probs.cpu().numpy()


def run_action_sensitivity(checkpoint, grid_path, policy_path, output):
    """Evaluate one full checkpoint and write its immutable diagnostic report."""
    checkpoint = Path(checkpoint)
    grid_path, policy_path, output = Path(grid_path), Path(policy_path), Path(output)
    if not checkpoint.is_file():
        raise ValueError(f"checkpoint does not exist: {checkpoint}")
    grid = GridConfig(**json.loads(grid_path.read_text(encoding="utf-8")))
    policy = TrainingConfig(**json.loads(policy_path.read_text(encoding="utf-8")))
    if policy.observation_mode != "full":
        raise ValueError("action-sensitivity diagnostic requires a full-input policy config")
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "status": "started", "purpose": "development_only_phase2a_local_action_sensitivity",
        "checkpoint": str(checkpoint), "checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        "grid_config": asdict(grid), "policy_config": asdict(policy),
        "provenance": _git_provenance(), "python": platform.python_version(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    start = time.perf_counter()
    try:
        torch.set_num_threads(1)
        model = PPO.load(checkpoint, device="cpu")
        results = {}
        for deterministic in (True, False):
            report, episodes = LocalActionSensitivity(), []
            for map_seed in policy.diagnostic_map_seeds:
                world = ResourceRetrievalEnv(grid)
                observations, _ = world.reset(seed=map_seed)
                with torch.random.fork_rng(devices=[]):
                    torch.manual_seed(policy.seed + map_seed)
                    while world.agents:
                        agents = tuple(world.agents)
                        batch = np.stack([observations[agent] for agent in agents])
                        visible = np.any(batch[:, PHEROMONE_INDICES] > 0, axis=1)
                        full = _action_probabilities(model, batch)
                        masked_batch = apply_observation_mode(batch, "no_pheromone")
                        report.update(full, _action_probabilities(model, masked_batch), visible)
                        actions, _ = model.predict(batch, deterministic=deterministic)
                        observations, _, _, _, _ = world.step(dict(zip(agents, map(int, actions))))
                episodes.append({"map_seed": map_seed, "steps": world.steps,
                                 "delivered": world.delivered_total,
                                 "completed": not world.food.any() and not world.carrying.any()})
                world.close()
            results["deterministic" if deterministic else "stochastic"] = {**report.summary(), "episodes": episodes}
        summary = {
            "checkpoint": str(checkpoint), "results": results,
            "limitations": [
                "local input sensitivity does not prove pheromone coordination or delivery benefit",
                "development diagnostic maps only",
                "no attack, detector, dataset, or held-out evaluation",
            ],
        }
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        manifest.update(status="completed", elapsed_seconds=time.perf_counter() - start)
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return summary
    except BaseException as error:
        manifest.update(status="incomplete" if isinstance(error, KeyboardInterrupt) else "failed",
                        error=f"{type(error).__name__}: {error}", elapsed_seconds=time.perf_counter() - start)
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--policy-config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(run_action_sensitivity(args.checkpoint, args.config, args.policy_config, args.output), indent=2))
