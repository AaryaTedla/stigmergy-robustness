"""Reproducible CPU parameter-shared PPO pilot and development diagnostics.

Use the CLI train command with a JSON TrainingConfig and a JSON GridConfig.
One SB3 PPO MLP (32x32 actor and local critic) consumes the (N,58) observation
batch from SharedGridVecEnv; every row is an agent-local input. The unchanged
shared delivery count is the reward. No global-state critic, reward shaping,
identity encoding, attack training or final-test tuning occurs here.

The requested budget is in agent transitions, not world steps. SB3 rounds up
to whole n_steps*N rollouts; the actual count is saved. Maps cycle through
explicit development seeds. Distinct development diagnostic maps are rolled
out before and after updates, with deterministic and seeded stochastic actions
reported separately. These are diagnostic episodes, not a frozen held-out
benchmark. A short training run can fail to improve and must remain visible.

Output is a fresh directory with manifest.json (configs, versions, source
hashes and outcome), initial.zip/policy.zip, progress.csv, and summary.json
(per-map deliveries, parameter hashes, roundtrip check, completed training
episodes). Errors leave a failed manifest and existing artifacts intact.
Fixed CPU single-thread operations and explicit seeds support reproducibility
on the same dependency/runtime stack; cross-platform identity is not promised.
Requires the optional pinned training dependencies; simulator commands import
this module only when train is requested.
"""

from dataclasses import asdict, dataclass
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import time

import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.logger import configure

from .environment import GridConfig, ResourceRetrievalEnv
from .ppo_adapter import SharedGridVecEnv
from .trajectories import _git_provenance


@dataclass(frozen=True)
class TrainingConfig:
    """Validated PPO/development-map parameters; budgets count agent transitions."""

    seed: int = 7
    total_transitions: int = 300000
    n_steps: int = 128
    batch_size: int = 64
    n_epochs: int = 4
    learning_rate: float = 0.0003
    gamma: float = 0.99
    train_map_seeds: tuple = tuple(range(16))
    diagnostic_map_seeds: tuple = (100, 101, 102, 103)

    def __post_init__(self):
        for name in ("seed", "total_transitions", "n_steps", "batch_size", "n_epochs"):
            value = getattr(self, name)
            minimum = 0 if name == "seed" else 2 if name in ("n_steps", "batch_size") else 1
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")
        for name in ("learning_rate", "gamma"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
                raise ValueError(f"{name} must be a finite number")
        if self.learning_rate <= 0 or not 0 <= self.gamma <= 1:
            raise ValueError("require learning_rate > 0 and gamma in [0,1]")
        for name in ("train_map_seeds", "diagnostic_map_seeds"):
            seeds = tuple(getattr(self, name))
            if not seeds or any(isinstance(s, bool) or not isinstance(s, int) or s < 0 for s in seeds):
                raise ValueError(f"{name} must be nonempty nonnegative integer seeds")
            if len(set(seeds)) != len(seeds):
                raise ValueError(f"{name} must have unique seeds")
            object.__setattr__(self, name, seeds)
        if set(self.train_map_seeds) & set(self.diagnostic_map_seeds):
            raise ValueError("training and development diagnostic map seeds must be disjoint")


def policy_digest(model):
    """Hash named parameter tensors independently of ZIP timestamps/serialization."""
    digest = hashlib.sha256()
    for name, value in sorted(model.policy.state_dict().items()):
        digest.update(name.encode())
        digest.update(value.detach().cpu().numpy().tobytes())
    return digest.hexdigest()


def evaluate_model(model, grid, map_seeds, action_seed):
    """Measure local PPO behavior on development maps without changing training RNG.

    Actor calls receive only copied local rows. Global delivered counts are
    simulator-only diagnostic outputs. A forked CPU RNG isolates evaluation
    from subsequent training, and pairs initial/final stochastic action seeds.
    """
    results = {}
    for deterministic in (True, False):
        episodes = []
        for map_seed in map_seeds:
            world = ResourceRetrievalEnv(grid)
            observations, _ = world.reset(seed=map_seed)
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(action_seed + map_seed)
                while world.agents:
                    agents = tuple(world.agents)
                    batch = np.stack([observations[a] for a in agents])
                    actions, _ = model.predict(batch, deterministic=deterministic)
                    observations, _, _, _, _ = world.step(dict(zip(agents, map(int, actions))))
            episodes.append({"map_seed": map_seed, "steps": world.steps,
                             "delivered": world.delivered_total,
                             "completed": not world.food.any() and not world.carrying.any()})
            world.close()
        results["deterministic" if deterministic else "stochastic"] = {
            "episodes": episodes, "mean_delivered": float(np.mean([e["delivered"] for e in episodes]))}
    return results


def run_training(grid_path, training_path, output):
    """Train one shared clean-development PPO policy and preserve auditable artifacts.

    Returns the JSON-compatible summary after verified save/load equivalence.
    Output directories must be new. Invalid configurations are rejected before
    creating artifacts; run-time failures update the manifest and are re-raised.
    """
    grid = GridConfig(**json.loads(Path(grid_path).read_text(encoding="utf-8")))
    training = TrainingConfig(**json.loads(Path(training_path).read_text(encoding="utf-8")))
    rollout_size = grid.n_agents * training.n_steps
    if training.batch_size > rollout_size or rollout_size % training.batch_size:
        raise ValueError("batch_size must divide n_agents*n_steps without exceeding it")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "started", "label": "clean shared PPO development pilot; not a robustness result",
                "grid_config": asdict(grid), "training_config": asdict(training),
                "provenance": _git_provenance(), "python": platform.python_version(),
                "versions": {n: version(n) for n in ("numpy", "gymnasium", "pettingzoo", "torch", "stable-baselines3")},
                "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(Path(__file__).parent.glob("*.py"))}}

    def save_manifest():
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    save_manifest()
    start = time.perf_counter()
    adapter = None
    try:
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        adapter = SharedGridVecEnv(grid, training.train_map_seeds)
        model = PPO("MlpPolicy", adapter, seed=training.seed, device="cpu",
                    n_steps=training.n_steps, batch_size=training.batch_size,
                    n_epochs=training.n_epochs, learning_rate=training.learning_rate,
                    gamma=training.gamma, policy_kwargs={"net_arch": {"pi": [32, 32], "vf": [32, 32]}})
        model.set_logger(configure(str(output), ["csv"]))
        initial_hash = policy_digest(model)
        model.save(output / "initial.zip")
        before = evaluate_model(model, grid, training.diagnostic_map_seeds, training.seed)
        model.learn(total_timesteps=training.total_transitions)
        if not all(torch.isfinite(value).all().item() for value in model.policy.state_dict().values()):
            raise RuntimeError("nonfinite learned parameters")
        final_hash = policy_digest(model)
        model.save(output / "policy.zip")
        reloaded = PPO.load(output / "policy.zip", device="cpu")
        probe, _ = ResourceRetrievalEnv(grid).reset(seed=training.diagnostic_map_seeds[0])
        rows = np.stack(list(probe.values()))
        roundtrip = (policy_digest(reloaded) == final_hash and np.array_equal(
            model.predict(rows, deterministic=True)[0], reloaded.predict(rows, deterministic=True)[0]))
        if not roundtrip:
            raise RuntimeError("checkpoint roundtrip mismatch")
        after = evaluate_model(reloaded, grid, training.diagnostic_map_seeds, training.seed)
        summary = {"requested_agent_transitions": training.total_transitions,
                   "actual_agent_transitions": model.num_timesteps,
                   "world_steps": model.num_timesteps // grid.n_agents,
                   "initial_parameter_sha256": initial_hash, "final_parameter_sha256": final_hash,
                   "parameters_changed": initial_hash != final_hash, "checkpoint_roundtrip": roundtrip,
                   "before": before, "after": after, "training_episodes": adapter.episode_records,
                   "limitations": ["single training seed; development diagnostics only",
                                   "no verified pheromone reliance or robustness",
                                   "no no-pheromone baseline or final held-out evaluation"]}
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        manifest.update(status="completed", elapsed_seconds=time.perf_counter() - start)
        save_manifest()
        return summary
    except BaseException as error:
        manifest.update(status="incomplete" if isinstance(error, KeyboardInterrupt) else "failed", error=f"{type(error).__name__}: {error}",
                        elapsed_seconds=time.perf_counter() - start)
        save_manifest()
        raise
    finally:
        if adapter is not None:
            adapter.close()
