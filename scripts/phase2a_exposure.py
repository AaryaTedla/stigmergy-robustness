"""Write a reproducible local-pheromone visibility report for one PPO policy.

Run this script with a completed full-input Phase 2A checkpoint, its grid JSON
and its policy JSON.  The script rolls the frozen model over the policy's
declared development diagnostic maps and writes a new output directory with a
manifest and summary.  It records how often the policy's own local observation
contains nonzero food/home pheromone, plus the local normalized field values it
could see.  It does not alter PPO weights, simulator mechanics, reward, maps,
or observations and it does not inspect global arrays or privileged attack data.

Example:
    python scripts/phase2a_exposure.py \
      --checkpoint artifacts/phase2a/simple-repeat-run-001/candidate_e_12x12_repeat/full-seed-7/policy.zip \
      --config configs/phase2a/env/candidate_e_12x12_repeat.json \
      --policy-config configs/phase2a/policy/full_seed_7.json \
      --output artifacts/phase2a/exposure-candidate-e-seed-7

The report is a Phase 2A diagnostic, not evidence that a policy uses pheromone
well.  It measures only whether pheromone was locally visible during a frozen
rollout.  Use fresh output paths so previous reports remain auditable.
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

from stigmergy.environment import GridConfig, ResourceRetrievalEnv
from stigmergy.exposure import LocalPheromoneExposure
from stigmergy.observations import apply_observation_mode
from stigmergy.training import TrainingConfig
from stigmergy.trajectories import _git_provenance


def run_exposure(checkpoint, grid_path, policy_path, output):
    """Evaluate one full-input checkpoint and save a local-only exposure report.

    The stochastic rollout uses the same seed-plus-map seed rule as the normal
    PPO diagnostic.  Deterministic and stochastic results are kept separate,
    because sampled actions can visit different local field values.  The policy
    must be a full-input policy: measuring a no-pheromone model here would only
    describe hidden simulator values, not values available to that model.
    """
    checkpoint = Path(checkpoint)
    grid_path, policy_path, output = Path(grid_path), Path(policy_path), Path(output)
    if not checkpoint.is_file():
        raise ValueError(f"checkpoint does not exist: {checkpoint}")
    grid = GridConfig(**json.loads(grid_path.read_text(encoding="utf-8")))
    policy = TrainingConfig(**json.loads(policy_path.read_text(encoding="utf-8")))
    if policy.observation_mode != "full":
        raise ValueError("exposure diagnostic requires a full-input policy config")
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "status": "started",
        "purpose": "development_only_phase2a_local_pheromone_exposure",
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
            exposure = LocalPheromoneExposure()
            episodes = []
            for map_seed in policy.diagnostic_map_seeds:
                world = ResourceRetrievalEnv(grid)
                observations, _ = world.reset(seed=map_seed)
                with torch.random.fork_rng(devices=[]):
                    torch.manual_seed(policy.seed + map_seed)
                    while world.agents:
                        agents = tuple(world.agents)
                        batch = np.stack([observations[agent] for agent in agents])
                        # Update before masking/action selection: this is exactly the full local input.
                        exposure.update(batch)
                        actions, _ = model.predict(apply_observation_mode(batch, "full"), deterministic=deterministic)
                        observations, _, _, _, _ = world.step(dict(zip(agents, map(int, actions))))
                episodes.append({"map_seed": map_seed, "steps": world.steps,
                                 "delivered": world.delivered_total,
                                 "completed": not world.food.any() and not world.carrying.any()})
                world.close()
            results["deterministic" if deterministic else "stochastic"] = {
                **exposure.summary(), "episodes": episodes,
                "mean_delivered": float(np.mean([episode["delivered"] for episode in episodes])),
            }
        summary = {"checkpoint": str(checkpoint), "results": results,
                   "limitations": [
                       "development diagnostic maps only",
                       "visibility does not prove pheromone use or benefit",
                       "no attack, detector, dataset, or held-out evaluation",
                   ]}
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
    print(json.dumps(run_exposure(args.checkpoint, args.config, args.policy_config, args.output), indent=2))
