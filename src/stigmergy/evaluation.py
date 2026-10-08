"""Matched development PPO/timeout comparisons with auditable local trajectories.

Run the CLI compare-development command with a completed training checkpoint,
the persistent attack JSON and a DevelopmentComparisonConfig JSON. The model
must be the final policy.zip from a completed run with matching parameter hash,
58-value observations and five actions. Its grid/config provenance is reused;
only its declared diagnostic map seeds are accepted. No final-test experiment,
dataset partition, detector fit or threshold selection occurs in this module.

Each (map seed, action seed, action mode) group contains six episodes: clean,
injection-disabled and attacked, each undefended or with the same timeout rule.
The PPO network stays frozen and consumes (N,58) local rows. One history/timeout
object per agent consumes only its own observation and executed previous action.
The defense is applied to every agent uniformly, never selected by attacker ID.

Fresh output directories contain manifest.json, episodes.csv, contrasts.csv,
summary.json, runtime.json, PNG/SVG plots and per-group/per-scenario steps.jsonl.
Local features (12 float32 values) and proposed/executed actions live in the
local record; attacker identity/mass and global honest delivery accounting are
simulator_metadata only. Episode metrics use food units and world-step counts.
Injection loss = honest disabled - honest attacked; timeout gain = honest
attacked+timeout - honest attacked. Clean cost = total clean - total clean+
timeout. Recovery gain/loss is undefined for loss <= 0. Timeout activity is not
a classifier alarm and cannot supply detection precision/recall/false alarms.

The injector preserves productive PPO actions; no reduced-worker behavior is
modeled. Historical two-agent checkpoints use 50% compromise; eight-agent review runs
use one attacker (12.5%). Neither condition alone establishes robustness. Statistics are reported separately by
action mode; one training seed cannot supply training-seed uncertainty. No-
pheromone/cautionary baselines and final evaluation are explicitly not run.
Checkpoint hashes and JSON metrics support same-stack repeatability; runtime
is recorded separately. Failures retain a failed manifest and partial outputs.
"""

from dataclasses import asdict, dataclass
import csv
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import time

import numpy as np
import torch
from stable_baselines3 import PPO

from .attacks import AttackConfig
from .defense import FEATURE_NAMES, LocalHistoryFeatures, LocalTimeoutDefense
from .environment import GridConfig, ResourceRetrievalEnv
from .training import policy_digest
from .trajectories import _git_provenance, _json_value, matched_attack_configs

SCENARIOS = ("clean", "clean_timeout", "injection_disabled", "injection_disabled_timeout",
             "attacked", "attacked_timeout")


@dataclass(frozen=True)
class DevelopmentComparisonConfig:
    """Development seed assignments and fixed heuristic parameters, never test tuning."""

    purpose: str = "development_only"
    map_seeds: tuple = (100, 101, 102, 103)
    action_seeds: tuple = (7,)
    action_modes: tuple = ("deterministic", "stochastic")
    timeout: int = 8
    progress_horizon: int = 20

    def __post_init__(self):
        if self.purpose != "development_only":
            raise ValueError("only development comparisons are implemented")
        for name in ("map_seeds", "action_seeds"):
            values = tuple(getattr(self, name))
            if not values or len(set(values)) != len(values) or any(
                    isinstance(v, bool) or not isinstance(v, int) or not 0 <= v < 2**32 for v in values):
                raise ValueError(f"{name} must contain unique integer seeds in [0,2**32)")
            object.__setattr__(self, name, values)
        modes = tuple(self.action_modes)
        if not modes or len(set(modes)) != len(modes) or not set(modes) <= {"deterministic", "stochastic"}:
            raise ValueError("action_modes must be unique deterministic/stochastic modes")
        object.__setattr__(self, "action_modes", modes)
        for name in ("timeout", "progress_horizon"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")


class LocalPPOEpisodeController:
    """Frozen local PPO plus per-agent history/timeout state; no simulator inputs.

    Agent dictionary keys route independent state objects; IDs are not encoded
    in observations or used to select who is defended. Construct anew for each
    episode. act accepts only local observations and returns actions plus local
    diagnostics. Executed actions, rather than proposals, reconstruct revisits.
    """

    def __init__(self, model, agents, config, defended, deterministic):
        self.model = model
        self.agents = tuple(agents)
        self.deterministic = deterministic
        self.history = {a: LocalHistoryFeatures(config.progress_horizon) for a in self.agents}
        self.defenses = {a: LocalTimeoutDefense(config.timeout) for a in self.agents} if defended else {}
        self.previous_actions = {a: None for a in self.agents}

    def act(self, observations):
        """Compute proposals and optional local overrides from (N,58) local rows."""
        features = {a: self.history[a].update(observations[a], self.previous_actions[a]) for a in self.agents}
        rows = np.stack([observations[a] for a in self.agents])
        proposed, _ = self.model.predict(rows, deterministic=self.deterministic)
        proposals = dict(zip(self.agents, map(int, proposed)))
        actions = {a: self.defenses[a].select_action(observations[a], proposals[a])
                   if a in self.defenses else proposals[a] for a in self.agents}
        active = {a: a in self.defenses and self.defenses[a].stale_steps >= self.defenses[a].timeout
                  for a in self.agents}
        self.previous_actions = actions.copy()
        return actions, {"features": features, "proposed_actions": proposals,
                         "executed_actions": actions, "timeout_active": active}


def _save_json(path, value):
    """Write stable JSON without encoding NumPy values as invalid JSON types."""
    Path(path).write_text(json.dumps(_json_value(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path, rows):
    """Write deterministic metric rows; durations belong in separate runtime JSON."""
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def rollout_comparison_episode(model, grid, attack_config, config, map_seed, action_seed,
                               action_mode, scenario, output):
    """Record one paired episode; simulator labels are used solely by the writer.

    Returns deterministic episode metrics and a separate elapsed-time record.
    The environment seed governs map/contention/selection. A forked Torch RNG
    seeds proposals identically across variants without mutating the caller RNG.
    """
    if scenario not in SCENARIOS:
        raise ValueError("unknown comparison scenario")
    base_scenario = scenario.removesuffix("_timeout")
    chosen_attack = matched_attack_configs(attack_config)[base_scenario]
    world = ResourceRetrievalEnv(grid, attack_config=chosen_attack)
    observations, _ = world.reset(seed=map_seed)
    controller = LocalPPOEpisodeController(model, observations, config,
        defended=scenario.endswith("_timeout"), deterministic=action_mode == "deterministic")
    selected = set(world.attack_injector.compromised_agents) if world.attack_injector else set()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    group_id = f"map-{map_seed}_action-{action_seed}_{action_mode}"
    count_deliveries = {a: 0 for a in observations}
    overrides = activations = 0
    local_digest = hashlib.sha256()
    start = time.perf_counter()
    try:
        with (output / "steps.jsonl").open("x", encoding="utf-8") as stream, torch.random.fork_rng(devices=[]):
            torch.manual_seed(action_seed + map_seed)
            while world.agents:
                actions, diagnostics = controller.act(observations)
                after, rewards, terms, truncs, infos = world.step(actions)
                for agent in count_deliveries:
                    count_deliveries[agent] += int(after[agent][56])
                    overrides += int(actions[agent] != diagnostics["proposed_actions"][agent])
                    activations += int(diagnostics["timeout_active"][agent])
                local = {"observations_before": observations, "observations_after": after,
                         **diagnostics, "rewards": rewards, "terminations": terms,
                         "truncations": truncs, "infos": infos}
                local_digest.update(json.dumps(_json_value(local), sort_keys=True,
                                               separators=(",", ":")).encode("utf-8"))
                record = {"step": world.steps, "local": local,
                          "simulator_metadata": {"attack_events": [e.as_dict() for e in world.last_attack_events],
                              "total_delivered": world.delivered_total,
                              "honest_delivered": sum(v for a, v in count_deliveries.items() if a not in selected)}}
                stream.write(json.dumps(_json_value(record), sort_keys=True, separators=(",", ":")) + "\n")
                observations = after
        attack = world.attack_summary()
        row = {"group_id": group_id, "map_seed": map_seed, "action_seed": action_seed,
               "action_mode": action_mode, "scenario": scenario, "n_agents": grid.n_agents,
               "compromised_count": len(selected), "compromised_fraction": len(selected) / grid.n_agents,
               "total_delivered": world.delivered_total,
               "honest_delivered": sum(v for a, v in count_deliveries.items() if a not in selected),
               "steps": world.steps, "completed": not world.food.any() and not world.carrying.any(),
               "local_record_sha256": local_digest.hexdigest(),
               "timeout_active_agent_steps": activations, "overridden_agent_actions": overrides,
               "requested_mass": attack["total_requested_mass"] if attack else 0.0,
               "authorized_mass": attack["total_authorized_mass"] if attack else 0.0,
               "applied_mass": attack["total_applied_mass"] if attack else 0.0}
        if sum(count_deliveries.values()) != world.delivered_total:
            raise RuntimeError("own-delivery event accounting disagrees with simulator")
        _save_json(output / "episode.json", {"metrics": row, "split": "development",
                    "simulator_metadata": {"compromised_agents": sorted(selected),
                                           "deliveries_by_agent": count_deliveries, "attack_summary": attack}})
        return row, {"group_id": group_id, "scenario": scenario,
                     "elapsed_seconds": time.perf_counter() - start}
    finally:
        world.close()


def paired_contrasts(rows):
    """Return per-group honest injection/timeout contrasts and clean task cost.

    Recovery ratio stays None when injection loss is nonpositive, preserving
    zero/negative findings. Honest clean/disabled counts are not contrasted
    because those populations differ; total clean/disabled equality is audited
    independently through their local trajectory records.
    """
    groups = {}
    for row in rows:
        group = groups.setdefault(row["group_id"], {})
        if row["scenario"] in group:
            raise ValueError("duplicate scenario in comparison group")
        group[row["scenario"]] = row
    result = []
    for group_id, group in groups.items():
        if set(group) != set(SCENARIOS):
            raise ValueError("each comparison group must contain all six scenarios")
        loss = group["injection_disabled"]["honest_delivered"] - group["attacked"]["honest_delivered"]
        gain = group["attacked_timeout"]["honest_delivered"] - group["attacked"]["honest_delivered"]
        result.append({"group_id": group_id, "action_mode": group["clean"]["action_mode"],
                       "injection_loss_units": loss, "timeout_gain_units": gain,
                       "clean_cost_units": group["clean"]["total_delivered"] - group["clean_timeout"]["total_delivered"],
                       "disabled_cost_units": group["injection_disabled"]["honest_delivered"] - group["injection_disabled_timeout"]["honest_delivered"],
                       "recovery_fraction": gain / loss if loss > 0 else None})
    return result


def _summarize(rows, contrasts):
    """Separate action modes and episode range from unmeasured training variability."""
    result = {"training_seed_count": 1, "episode_count": len(rows), "by_action_mode": {},
              "not_run": ["separately trained no-pheromone baseline", "cautionary-pheromone adaptation",
                          "learned detector/false-alarm controls", "final held-out evaluation"],
              "limitations": ["development integration only; no established robustness",
                              "single short-trained PPO checkpoint; pheromone reliance unverified",
                              "selected agents retain productive PPO behavior",
                              "episode variability is not training-seed uncertainty"]}
    for mode in dict.fromkeys(r["action_mode"] for r in rows):
        mode_result = {"scenarios": {}, "paired_mean": {}}
        for scenario in SCENARIOS:
            samples = [r for r in rows if r["action_mode"] == mode and r["scenario"] == scenario]
            mode_result["scenarios"][scenario] = {"episodes": len(samples),
                "mean_total_delivered": float(np.mean([r["total_delivered"] for r in samples])),
                "mean_honest_delivered": float(np.mean([r["honest_delivered"] for r in samples])),
                "honest_delivery_range": [min(r["honest_delivered"] for r in samples), max(r["honest_delivered"] for r in samples)]}
        paired = [r for r in contrasts if r["action_mode"] == mode]
        for name in ("injection_loss_units", "timeout_gain_units", "clean_cost_units", "disabled_cost_units"):
            mode_result["paired_mean"][name] = float(np.mean([r[name] for r in paired]))
        mode_result["undefined_recovery_groups"] = sum(r["recovery_fraction"] is None for r in paired)
        result["by_action_mode"][mode] = mode_result
    return result


def run_development_comparison(checkpoint, attack_path, comparison_path, output):
    """Validate checkpoint provenance, execute paired local rollouts, plot and save.

    The checkpoint must be unchanged from its completed training artifacts and
    match the local environment/training source. Invalid map/config/checkpoint
    inputs are rejected before creating the output. Actual experiment failures
    retain a failed manifest and partial logs. No optimization step is executed.
    """
    config = DevelopmentComparisonConfig(**json.loads(Path(comparison_path).read_text(encoding="utf-8")))
    attack = AttackConfig(**json.loads(Path(attack_path).read_text(encoding="utf-8")))
    if not attack.enabled:
        raise ValueError("base attack must be enabled; disabled twins are generated internally")
    checkpoint = Path(checkpoint)
    training_manifest = json.loads((checkpoint.parent / "manifest.json").read_text(encoding="utf-8"))
    training_summary = json.loads((checkpoint.parent / "summary.json").read_text(encoding="utf-8"))
    if training_manifest.get("status") != "completed":
        raise ValueError("checkpoint requires a completed training manifest")
    allowed_maps = set(training_manifest["training_config"]["diagnostic_map_seeds"])
    if not set(config.map_seeds) <= allowed_maps:
        raise ValueError("comparison maps must be declared development diagnostic maps")
    grid = GridConfig(**training_manifest["grid_config"])
    if attack.compromised_count > grid.n_agents:
        raise ValueError("compromised_count exceeds the training grid agent count")
    source_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(Path(__file__).parent.glob("*.py"))}
    for name in ("environment.py", "attacks.py", "policies.py", "ppo_adapter.py", "training.py"):
        if source_hashes[name] != training_manifest["source_sha256"].get(name):
            raise ValueError(f"checkpoint training source differs for {name}")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    model = PPO.load(checkpoint, device="cpu")
    before_hash = policy_digest(model)
    if (before_hash != training_summary["final_parameter_sha256"] or
            model.observation_space.shape != (58,) or model.action_space.n != 5):
        raise ValueError("checkpoint does not match the completed local PPO run")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"format_version": 1, "status": "started", "purpose": "development_only",
                "grid_config": asdict(grid), "attack_config": attack.as_dict(),
                "comparison_config": asdict(config), "provenance": _git_provenance(),
                "source_sha256": source_hashes, "python": platform.python_version(),
                "versions": {n: version(n) for n in ("numpy", "torch", "stable-baselines3", "matplotlib", "pettingzoo", "gymnasium")},
                "checkpoint": {"file_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                               "parameter_sha256": before_hash, "training_manifest": training_manifest},
                "feature_names": FEATURE_NAMES, "groups": [], "scenarios": SCENARIOS,
                "model_inputs": ["local.observations_before"],
                "defense_inputs": ["own local observation and own progress history"],
                "simulator_only": ["attacker identities", "attack mass", "honest/global delivery accounting"],
                "not_a_minority_study": attack.compromised_count * 2 >= grid.n_agents}
    _save_json(output / "manifest.json", manifest)
    rows, runtimes = [], []
    try:
        for mode in config.action_modes:
            # Deterministic actions do not depend on sampling seeds: do not count
            # duplicate deterministic runs as additional episode variability.
            seeds = config.action_seeds[:1] if mode == "deterministic" else config.action_seeds
            for map_seed in config.map_seeds:
                for action_seed in seeds:
                    group_id = f"map-{map_seed}_action-{action_seed}_{mode}"
                    manifest["groups"].append({"group_id": group_id, "split": "development",
                        "map_seed": map_seed, "action_seed": action_seed, "action_mode": mode,
                        "scenarios": SCENARIOS})
                    for scenario in SCENARIOS:
                        row, runtime = rollout_comparison_episode(model, grid, attack, config,
                            map_seed, action_seed, mode, scenario, output / "episodes" / group_id / scenario)
                        rows.append(row)
                        runtimes.append(runtime)
                    group_rows = {r["scenario"]: r for r in rows if r["group_id"] == group_id}
                    for clean, disabled in (("clean", "injection_disabled"),
                                            ("clean_timeout", "injection_disabled_timeout")):
                        if group_rows[clean]["local_record_sha256"] != group_rows[disabled]["local_record_sha256"]:
                            raise RuntimeError("clean/disabled local controls diverged")
        if policy_digest(model) != before_hash:
            raise RuntimeError("evaluation modified the frozen PPO parameters")
        contrasts = paired_contrasts(rows)
        summary = _summarize(rows, contrasts)
        summary.update(checkpoint_unchanged=True, n_agents=grid.n_agents,
                       attack_compromised_count=attack.compromised_count,
                       attack_compromised_fraction=attack.compromised_count / grid.n_agents,
                       not_a_minority_study=manifest["not_a_minority_study"])
        _write_csv(output / "episodes.csv", rows)
        _write_csv(output / "contrasts.csv", contrasts)
        _save_json(output / "summary.json", summary)
        _save_json(output / "runtime.json", runtimes)
        from .evaluation_plots import plot_comparisons
        plot_comparisons(rows, contrasts, grid, output)
        manifest["status"] = "completed"
        _save_json(output / "manifest.json", manifest)
        return summary
    except BaseException as error:
        manifest.update(status="incomplete" if isinstance(error, KeyboardInterrupt) else "failed", error=f"{type(error).__name__}: {error}")
        _save_json(output / "manifest.json", manifest)
        _save_json(output / "runtime.json", runtimes)
        raise
