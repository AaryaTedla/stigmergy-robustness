"""Run Phase 2B's frozen-policy, matched persistent-attack calibration.

This module is deliberately narrower than a detector or robustness benchmark.
It loads only the completed Candidate J full-observation PPO checkpoints named
by a versioned Phase 2B plan, verifies their training provenance, and evaluates
each one on its already-declared development maps.  Every checkpoint/map/action
group gets the same three stochastic scenarios: ``clean``,
``injection_disabled`` and ``attacked``.  The latter two use the same seeded,
episode-fixed compromised-agent selection; only the attacked scenario writes
bounded nonnegative false-food mass.

The runner saves local policy-visible trajectories separately from simulator-
only attack metadata through :func:`stigmergy.evaluation.rollout_comparison_episode`.
It writes an indivisible group manifest before any future detector windows can
be made.  It does not create detector labels/features, train a detector, alter
the frozen PPO policy, add another attack mode, or score a held-out map.  A
zero or negative injection loss remains a recorded calibration result rather
than an error condition.
"""

from dataclasses import asdict, dataclass
import csv
import hashlib
import json
from pathlib import Path
import platform
from statistics import fmean

from .attacks import AttackConfig
from .environment import GridConfig
from .trajectories import _git_provenance, _json_value


SCENARIOS = ("clean", "injection_disabled", "attacked")
PLAN_PURPOSE = "development_only_phase2b_attack_calibration"


@dataclass(frozen=True)
class Phase2BAttackCalibrationPlan:
    """Validate the small, predeclared Phase 2B calibration matrix.

    Paths are repository-relative so the plan can be reviewed and hashed.  One
    action seed yields 3 frozen policies × 4 development maps × 3 scenarios =
    36 recorded episodes in the checked-in plan.  The class accepts smaller
    matrices only for focused automated tests; the repository plan fixes the
    real Candidate J matrix.
    """

    format_version: int = 1
    purpose: str = PLAN_PURPOSE
    candidate_id: str = "candidate_j_12x12_scout_follow_capacity"
    grid_config_path: str = ""
    checkpoint_template: str = ""
    attack_config_path: str = ""
    training_seeds: tuple = (7, 17, 27)
    map_seeds: tuple = (100, 101, 102, 103)
    action_seeds: tuple = (7,)
    action_mode: str = "stochastic"
    group_split: str = "development"
    attack_start_step: int = 0

    def __post_init__(self):
        if self.format_version != 1 or self.purpose != PLAN_PURPOSE:
            raise ValueError("unsupported Phase 2B attack-calibration plan")
        if not isinstance(self.candidate_id, str) or not self.candidate_id:
            raise ValueError("candidate_id must be a nonempty string")
        for name in ("grid_config_path", "checkpoint_template", "attack_config_path"):
            value = getattr(self, name)
            path = Path(value) if isinstance(value, str) else None
            if not isinstance(value, str) or not value or path.is_absolute() or ".." in path.parts:
                raise ValueError(f"{name} must be a nonempty repository-relative path")
        if "{seed}" not in self.checkpoint_template:
            raise ValueError("checkpoint_template must contain {seed}")
        for name in ("training_seeds", "map_seeds", "action_seeds"):
            values = tuple(getattr(self, name))
            if (not values or len(values) != len(set(values)) or any(
                    isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < 2**32
                    for value in values)):
                raise ValueError(f"{name} must contain unique integer seeds in [0, 2**32)")
            object.__setattr__(self, name, values)
        if self.action_mode != "stochastic" or self.group_split != "development":
            raise ValueError("Phase 2B calibration is stochastic development-only work")
        if (isinstance(self.attack_start_step, bool) or not isinstance(self.attack_start_step, int) or
                self.attack_start_step < 0):
            raise ValueError("attack_start_step must be a nonnegative integer")


def _json_sha256(value):
    """Hash a JSON-compatible object with stable formatting for provenance."""
    return hashlib.sha256(json.dumps(_json_value(value), sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def _save_json(path, value):
    """Write a deterministic JSON artifact without NumPy serialization leaks."""
    Path(path).write_text(json.dumps(_json_value(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path, rows):
    """Write nonempty same-schema rows in their declared execution order."""
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _source_hashes():
    """Capture source files used by this execution, excluding generated artifacts."""
    source = Path(__file__).parent
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(source.glob("*.py"))}


def _read_repository_file(root, relative, label):
    """Resolve one plan path without allowing a plan to escape its repository root."""
    path = root / relative
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"{label} must remain inside the repository root") from error
    if not path.is_file():
        raise ValueError(f"{label} does not exist: {relative}")
    return path


def load_phase2b_plan(plan_path):
    """Load a plan plus the frozen grid and bounded attack configuration.

    Attacker count, per-step intensity, onset and placement semantics are fixed
    here. The versioned attack configuration declares the episode cap and the
    plan repeats its onset, preventing a changed timing setting from silently
    changing an existing calibration.
    """
    plan_path = Path(plan_path)
    raw = json.loads(plan_path.read_text(encoding="utf-8"))
    plan = Phase2BAttackCalibrationPlan(**raw)
    if len(plan_path.parents) < 3:
        raise ValueError("Phase 2B plan must live below <root>/configs/phase2b/")
    root = plan_path.parents[2]
    grid_path = _read_repository_file(root, plan.grid_config_path, "grid_config_path")
    attack_path = _read_repository_file(root, plan.attack_config_path, "attack_config_path")
    grid = GridConfig(**json.loads(grid_path.read_text(encoding="utf-8")))
    attack = AttackConfig(**json.loads(attack_path.read_text(encoding="utf-8")))
    if (grid.n_agents != 4 or attack.compromised_count != 1 or not attack.enabled or
            attack.mode != "persistent" or (attack.requested_deposit, attack.per_step_budget) != (1.0, 1.0) or
            attack.episode_budget <= 0 or attack.start_step != plan.attack_start_step):
        raise ValueError("plan must retain Candidate J's four-agent bounded persistent-attack contract")
    return plan, root, grid_path, grid, attack_path, attack


def _load_frozen_checkpoint(checkpoint, training_seed, grid, map_seeds, source_hashes):
    """Verify and load one completed full-input PPO checkpoint without training it."""
    import torch
    from stable_baselines3 import PPO
    from .training import policy_digest

    checkpoint = Path(checkpoint)
    if not checkpoint.is_file():
        raise ValueError(f"frozen checkpoint does not exist: {checkpoint}")
    manifest_path, summary_path = checkpoint.parent / "manifest.json", checkpoint.parent / "summary.json"
    if not manifest_path.is_file() or not summary_path.is_file():
        raise ValueError("frozen checkpoint requires sibling completed manifest.json and summary.json")
    training_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    training_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    training = training_manifest.get("training_config", {})
    if (training_manifest.get("status") != "completed" or training.get("seed") != training_seed or
            training.get("observation_mode") != "full" or training_manifest.get("grid_config") != asdict(grid)):
        raise ValueError("checkpoint is not the declared completed Candidate J full-input run")
    if not set(map_seeds) <= set(training.get("diagnostic_map_seeds", ())):
        raise ValueError("Phase 2B maps must be declared diagnostic maps for every frozen checkpoint")
    # The frozen policy is clean-trained, so its provenance must match the
    # policy-relevant environment and PPO/training implementation. Attack
    # source intentionally is not required to match: Phase 2B varies only the
    # separately logged attack configuration while the frozen policy remains
    # byte-identical. The current attack source is saved in this run's manifest.
    for name in ("environment.py", "ppo_adapter.py", "training.py"):
        if source_hashes.get(name) != training_manifest.get("source_sha256", {}).get(name):
            raise ValueError(f"checkpoint training source differs for {name}")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    model = PPO.load(checkpoint, device="cpu")
    parameter_hash = policy_digest(model)
    if (parameter_hash != training_summary.get("final_parameter_sha256") or
            model.observation_space.shape != (58,) or model.action_space.n != 5):
        raise ValueError("checkpoint does not match its completed local PPO summary")
    return model, parameter_hash, training_manifest, hashlib.sha256(checkpoint.read_bytes()).hexdigest()


def _contrasts(rows):
    """Compute the predeclared matched effect without hiding zero/negative loss."""
    grouped = {}
    for row in rows:
        group = grouped.setdefault(row["group_id"], {})
        if row["scenario"] in group:
            raise ValueError("duplicate Phase 2B scenario in a group")
        group[row["scenario"]] = row
    contrasts = []
    for group_id, group in grouped.items():
        if set(group) != set(SCENARIOS):
            raise ValueError("each Phase 2B group requires clean, disabled and attacked rows")
        disabled, attacked = group["injection_disabled"], group["attacked"]
        contrasts.append({"group_id": group_id, "training_seed": group["clean"]["training_seed"],
                          "map_seed": group["clean"]["map_seed"],
                          "action_seed": group["clean"]["action_seed"],
                          "injection_loss_units": disabled["honest_delivered"] - attacked["honest_delivered"],
                          "clean_minus_disabled_total_units": group["clean"]["total_delivered"] -
                          disabled["total_delivered"], "attacked_applied_mass": attacked["applied_mass"]})
    return contrasts


def _summary(rows, contrasts, plan, grid, attack):
    """Summarize development rows by independent PPO training seed and scenario."""
    per_seed = {}
    for seed in plan.training_seeds:
        seed_rows = [row for row in rows if row["training_seed"] == seed]
        per_seed[str(seed)] = {scenario: {
            "episodes": sum(row["scenario"] == scenario for row in seed_rows),
            "mean_total_delivered": fmean(row["total_delivered"] for row in seed_rows if row["scenario"] == scenario),
            "mean_honest_delivered": fmean(row["honest_delivered"] for row in seed_rows if row["scenario"] == scenario),
        } for scenario in SCENARIOS}
    return {"purpose": PLAN_PURPOSE, "development_only": True,
            "checkpoint_count": len(plan.training_seeds), "group_count": len(contrasts),
            "episode_count": len(rows), "n_agents": grid.n_agents,
            "attack_compromised_count": attack.compromised_count,
            "attack_compromised_fraction": attack.compromised_count / grid.n_agents,
            "per_training_seed": per_seed,
            "mean_injection_loss_units": fmean(row["injection_loss_units"] for row in contrasts),
            "mean_attacked_applied_mass": fmean(row["attacked_applied_mass"] for row in contrasts),
            "limitations": ["development maps only", "persistent attack only", "no detector was fit",
                            "no defense was evaluated", "no held-out evaluation", "not a robustness claim"]}


def run_phase2b_attack_calibration(plan_path, output):
    """Execute the approved Phase 2B development calibration in a new directory.

    This is intentionally fail-closed: plan and checkpoint validation happen
    before any output is made, while a runtime failure after startup leaves a
    failed manifest and completed episode artifacts for audit.  The saved split
    manifest contains groups, not individual observations, to prevent later
    temporal-window leakage.
    """
    plan, root, grid_path, grid, attack_path, attack = load_phase2b_plan(plan_path)
    source_hashes = _source_hashes()
    checkpoint_details = {}
    loaded = {}
    for seed in plan.training_seeds:
        relative = plan.checkpoint_template.format(seed=seed)
        checkpoint = _read_repository_file(root, relative, "checkpoint_template")
        model, parameter_hash, training_manifest, file_hash = _load_frozen_checkpoint(
            checkpoint, seed, grid, plan.map_seeds, source_hashes)
        loaded[seed] = (model, parameter_hash)
        checkpoint_details[str(seed)] = {"path": relative, "file_sha256": file_hash,
                                         "parameter_sha256": parameter_hash,
                                         "training_manifest_sha256": hashlib.sha256(
                                             json.dumps(training_manifest, sort_keys=True).encode("utf-8")).hexdigest()}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    plan_bytes = Path(plan_path).read_bytes()
    manifest = {"format_version": 1, "status": "started", "purpose": PLAN_PURPOSE,
                "plan": asdict(plan), "plan_sha256": hashlib.sha256(plan_bytes).hexdigest(),
                "grid_config_path": str(grid_path.relative_to(root)), "grid_config": asdict(grid),
                "attack_config_path": str(attack_path.relative_to(root)), "attack_config": attack.as_dict(),
                "checkpoints": checkpoint_details, "source_sha256": source_hashes,
                "provenance": _git_provenance(), "python": platform.python_version(),
                "model_inputs": ["58 local observation values"],
                "simulator_only": ["attacker identities", "attack events", "attack mass", "honest delivery accounting"],
                "groups": []}
    _save_json(output / "manifest.json", manifest)
    rows = []
    try:
        from .evaluation import DevelopmentComparisonConfig, rollout_comparison_episode
        from .training import policy_digest
        episode_config = DevelopmentComparisonConfig(map_seeds=plan.map_seeds,
                                                      action_seeds=plan.action_seeds,
                                                      action_modes=("stochastic",))
        for training_seed, (model, before_hash) in loaded.items():
            for map_seed in plan.map_seeds:
                for action_seed in plan.action_seeds:
                    group_id = f"policy-{training_seed}_map-{map_seed}_action-{action_seed}_stochastic"
                    group = {"group_id": group_id, "split": plan.group_split,
                             "training_seed": training_seed, "map_seed": map_seed,
                             "action_seed": action_seed, "action_mode": "stochastic",
                             "scenarios": list(SCENARIOS)}
                    manifest["groups"].append(group)
                    group_rows = {}
                    for scenario in SCENARIOS:
                        row, _ = rollout_comparison_episode(
                            model, grid, attack, episode_config, map_seed, action_seed,
                            "stochastic", scenario, output / "episodes" / group_id / scenario,
                            group_id=group_id)
                        row["training_seed"] = training_seed
                        rows.append(row)
                        group_rows[scenario] = row
                    if group_rows["clean"]["local_record_sha256"] != group_rows["injection_disabled"]["local_record_sha256"]:
                        raise RuntimeError("clean and injection-disabled policy-visible records diverged")
                    disabled = json.loads((output / "episodes" / group_id / "injection_disabled" / "episode.json").read_text())
                    attacked = json.loads((output / "episodes" / group_id / "attacked" / "episode.json").read_text())
                    if disabled["simulator_metadata"]["compromised_agents"] != attacked["simulator_metadata"]["compromised_agents"]:
                        raise RuntimeError("disabled and attacked scenarios selected different compromised agents")
                    _save_json(output / "manifest.json", manifest)
            if policy_digest(model) != before_hash:
                raise RuntimeError("Phase 2B calibration modified a frozen PPO policy")
        contrasts = _contrasts(rows)
        split_manifest = {"format_version": 1, "purpose": "phase2b_development_group_manifest",
                          "plan_sha256": manifest["plan_sha256"], "assignments": manifest["groups"],
                          "rule": "all complete scenario variants in one policy/map/action group remain together"}
        _save_json(output / "group_splits.json", split_manifest)
        summary = _summary(rows, contrasts, plan, grid, attack)
        summary["group_split_manifest_sha256"] = _json_sha256(split_manifest)
        _write_csv(output / "episodes.csv", rows)
        _write_csv(output / "contrasts.csv", contrasts)
        _save_json(output / "summary.json", summary)
        manifest["status"] = "completed"
        manifest["group_split_manifest_sha256"] = summary["group_split_manifest_sha256"]
        _save_json(output / "manifest.json", manifest)
        return summary
    except BaseException as error:
        manifest.update(status="incomplete" if isinstance(error, KeyboardInterrupt) else "failed",
                        error=f"{type(error).__name__}: {error}")
        _save_json(output / "manifest.json", manifest)
        raise
