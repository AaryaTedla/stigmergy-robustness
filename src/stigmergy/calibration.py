"""Execute and summarize the declared Phase 2A PPO calibration matrix.

This module is an orchestration layer, not a new training algorithm or a final
evaluation. Given ``configs/phase2a/calibration.json``, it runs the fixed matrix
of environment candidates, training seeds, and observation modes. Each PPO run
delegates to ``training.run_training`` and therefore retains its own fresh
checkpoint, manifest, diagnostics, and failed-run record. A seeded random-action
rollout is recorded for the same grid, diagnostic maps, and action seed.

The output directory is new and contains a root manifest, one subdirectory per
PPO run, ``runs.csv`` with all completed/failed rows, ``paired.csv`` with
same-seed full-minus-no-pheromone and full-minus-random contrasts, and
``summary.json``. The runner never selects a winner or starts attack/dataset
generation. Its reported gate flag is a mechanical summary for team review;
all runs, including failures and non-advancing candidates, remain visible.
"""

from dataclasses import asdict
import csv
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np

from .environment import GridConfig, ResourceRetrievalEnv
from .observations import OBSERVATION_MODES
from .trajectories import _git_provenance


def _load_plan(plan_path):
    """Validate and resolve the small, explicit development-only run matrix."""
    plan_path = Path(plan_path)
    raw = json.loads(plan_path.read_text(encoding="utf-8"))
    required = {"format_version", "purpose", "environment_candidates", "observation_modes",
                "training_seeds", "policy_config_template", "selection_rule", "required_reports"}
    missing = required - set(raw)
    if missing:
        raise ValueError(f"calibration plan is missing fields: {sorted(missing)}")
    if raw["format_version"] != 1 or raw["purpose"] != "development_only_phase2a_calibration":
        raise ValueError("unsupported or non-development Phase 2A calibration plan")
    modes = tuple(raw["observation_modes"])
    if modes != OBSERVATION_MODES:
        raise ValueError(f"observation_modes must be exactly {OBSERVATION_MODES}")
    seeds = tuple(raw["training_seeds"])
    if not seeds or len(set(seeds)) != len(seeds) or any(isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 for seed in seeds):
        raise ValueError("training_seeds must be unique nonnegative integers")
    candidates = tuple(raw["environment_candidates"])
    if not candidates or len(set(candidates)) != len(candidates) or not all(isinstance(path, str) and path for path in candidates):
        raise ValueError("environment_candidates must be unique nonempty paths")
    root = plan_path.parents[2]
    resolved = []
    for relative in candidates:
        path = root / relative
        if not path.is_file():
            raise ValueError(f"candidate environment config does not exist: {relative}")
        grid = GridConfig(**json.loads(path.read_text(encoding="utf-8")))
        resolved.append((Path(relative).stem, path, grid))
    template = raw["policy_config_template"]
    if not isinstance(template, str) or "{mode}" not in template or "{seed}" not in template:
        raise ValueError("policy_config_template must include {mode} and {seed}")
    for mode in modes:
        for seed in seeds:
            policy_path = root / template.format(mode=mode, seed=seed)
            if not policy_path.is_file():
                raise ValueError(f"policy config does not exist: {policy_path.relative_to(root)}")
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            if policy.get("seed") != seed or policy.get("observation_mode") != mode:
                raise ValueError(f"policy config does not match declared mode/seed: {policy_path.relative_to(root)}")
    return raw, root, tuple(resolved), modes, seeds


def evaluate_random_actions(grid, map_seeds, action_seed):
    """Measure a reproducible local-observation-free random-action baseline.

    The baseline receives no map, field, attack, or policy privilege. It samples
    one legal action value for every live agent on each world step. Map reset
    RNG and action RNG are intentionally separate so policy and random results
    can share declared maps and action-seed accounting.
    """
    episodes = []
    for map_seed in map_seeds:
        world = ResourceRetrievalEnv(grid)
        observations, _ = world.reset(seed=map_seed)
        action_rng = np.random.default_rng(np.random.SeedSequence((action_seed, map_seed)))
        while world.agents:
            actions = {agent: int(action_rng.integers(5)) for agent in observations}
            observations, _, _, _, _ = world.step(actions)
        episodes.append({"map_seed": map_seed, "steps": world.steps,
                         "delivered": world.delivered_total,
                         "completed": not world.food.any() and not world.carrying.any()})
        world.close()
    return {"episodes": episodes,
            "mean_delivered": float(np.mean([episode["delivered"] for episode in episodes])),
            "completed_rate": float(np.mean([episode["completed"] for episode in episodes])),
            "mean_steps": float(np.mean([episode["steps"] for episode in episodes]))}


def _metric_summary(diagnostic):
    """Normalize PPO diagnostic details into a compact CSV/reporting record."""
    return {mode: {"mean_delivered": float(result["mean_delivered"]),
                   "completed_rate": float(np.mean([episode["completed"] for episode in result["episodes"]])),
                   "mean_steps": float(np.mean([episode["steps"] for episode in result["episodes"]]))}
            for mode, result in diagnostic.items()}


def _write_csv(path, rows, replace=False):
    """Write auditable CSV with a stable union of row keys for partial runs.

    Fresh calibrations use exclusive creation.  A validated resume may replace
    only an aggregate report, because it is fully derived from immutable
    per-run manifests and can have been written before an interruption updated
    the root manifest.
    """
    columns = sorted({key for row in rows for key in row})
    with Path(path).open("w" if replace else "x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _resumed_output_path(output, candidate_id, mode, seed):
    """Choose a fresh directory without discarding an interrupted PPO attempt.

    A completed declaration normally uses ``<mode>-seed-<seed>``.  If a process
    was interrupted after ``run_training`` created that directory but before the
    calibration manifest recorded a row, that location cannot safely be reused:
    training outputs are deliberately immutable.  This helper returns the
    canonical name when available, otherwise a numbered ``-resume-`` sibling so
    the partial checkpoint/progress file remains inspectable.
    """
    candidate_output = output / candidate_id
    candidate_output.mkdir(parents=True, exist_ok=True)
    base = candidate_output / f"{mode}-seed-{seed}"
    if not base.exists():
        return base
    attempt = 1
    while True:
        resumed = candidate_output / f"{mode}-seed-{seed}-resume-{attempt}"
        if not resumed.exists():
            return resumed
        attempt += 1


def _resume_manifest(output, plan, plan_sha256, expected_ppo_runs, expected_random_runs):
    """Load and validate an interrupted calibration manifest before resuming.

    The validation permits signal-left states and a failed final aggregation
    only when all declared PPO rows are already complete.  It rejects a changed
    plan, duplicate PPO rows, and malformed entries, because silently combining
    unlike experiments would invalidate the same-seed comparison contract.
    """
    manifest_path = output / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("--resume requires an existing calibration manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    status = manifest.get("status")
    if status not in {"started", "incomplete", "failed"}:
        raise ValueError("--resume requires a started, incomplete, or recoverable failed calibration manifest")
    if manifest.get("purpose") != plan["purpose"] or manifest.get("plan_sha256") != plan_sha256:
        raise ValueError("--resume plan does not match the existing calibration manifest")
    if (manifest.get("ppo_run_count") != expected_ppo_runs or
            manifest.get("random_baseline_count") != expected_random_runs):
        raise ValueError("--resume manifest does not match the declared calibration size")
    runs = manifest.get("runs")
    if not isinstance(runs, list):
        raise ValueError("--resume manifest runs must be a list")
    if status == "failed" and (len(runs) != expected_ppo_runs or
                               any(row.get("status") != "completed" for row in runs)):
        raise ValueError("--resume can recover a failed manifest only after every PPO row completed")
    seen = set()
    for row in runs:
        key = (row.get("candidate_id"), row.get("training_seed"), row.get("observation_mode"))
        if None in key or key in seen:
            raise ValueError("--resume manifest contains missing or duplicate PPO rows")
        seen.add(key)
    return manifest


def run_phase2a_calibration(plan_path, output, resume=False):
    """Run the fixed matrix, preserve partial failures, and write no winner claim.

    Interruptions create an ``incomplete`` root manifest and are re-raised.
    Other per-run failures are recorded and the remaining declared matrix still
    runs, preventing a single failed job from hiding the rest of the evidence.
    With ``resume=True``, only a plan-identical started/incomplete artifact
    directory is accepted; already recorded PPO rows are reused, while an
    unrecorded partial training directory receives a new ``-resume-N`` output.
    """
    plan, root, candidates, modes, seeds = _load_plan(plan_path)
    output = Path(output)
    plan_bytes = Path(plan_path).read_bytes()
    plan_sha256 = hashlib.sha256(plan_bytes).hexdigest()
    expected_ppo_runs = len(candidates) * len(modes) * len(seeds)
    expected_random_runs = len(candidates) * len(seeds)
    if resume:
        manifest = _resume_manifest(output, plan, plan_sha256, expected_ppo_runs, expected_random_runs)
        manifest["status"] = "started"
        manifest["resume_count"] = int(manifest.get("resume_count", 0)) + 1
        manifest.pop("error", None)
    else:
        output.mkdir(parents=True, exist_ok=False)
        manifest = {"format_version": 1, "status": "started", "purpose": plan["purpose"],
                    "plan": plan, "plan_sha256": plan_sha256,
                    "provenance": _git_provenance(), "python": platform.python_version(),
                    "candidate_count": len(candidates), "ppo_run_count": expected_ppo_runs,
                    "random_baseline_count": expected_random_runs, "runs": []}

    def save_manifest():
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    save_manifest()
    start = time.perf_counter()
    recorded = {(row["candidate_id"], row["training_seed"], row["observation_mode"]): row
                for row in manifest["runs"]}
    rows, paired = [], []
    try:
        # Import optional Torch/SB3 code only when this explicit training command runs.
        from .training import run_training

        for candidate_id, grid_path, grid in candidates:
            candidate_results = {}
            for seed in seeds:
                random_result = evaluate_random_actions(grid, tuple(json.loads(
                    (root / plan["policy_config_template"].format(mode="full", seed=seed)).read_text(encoding="utf-8")
                )["diagnostic_map_seeds"]), seed)
                random_row = {"candidate_id": candidate_id, "training_seed": seed, "observation_mode": "random",
                              "status": "completed", "stochastic_mean_delivered": random_result["mean_delivered"],
                              "stochastic_completed_rate": random_result["completed_rate"],
                              "stochastic_mean_steps": random_result["mean_steps"], "error": ""}
                rows.append(random_row)
                candidate_results[(seed, "random")] = random_row
                for mode in modes:
                    key = (candidate_id, seed, mode)
                    if key in recorded:
                        row = recorded[key]
                        rows.append(row)
                        candidate_results[(seed, mode)] = row
                        continue
                    policy_relative = plan["policy_config_template"].format(mode=mode, seed=seed)
                    run_output = _resumed_output_path(output, candidate_id, mode, seed)
                    entry = {"candidate_id": candidate_id, "training_seed": seed, "observation_mode": mode,
                             "grid_config": asdict(grid), "grid_config_path": str(grid_path.relative_to(root)),
                             "policy_config_path": policy_relative, "output": str(run_output.relative_to(output))}
                    try:
                        summary = run_training(grid_path, root / policy_relative, run_output)
                        metrics = _metric_summary(summary["after"])
                        row = {**entry, "status": "completed",
                               "deterministic_mean_delivered": metrics["deterministic"]["mean_delivered"],
                               "deterministic_completed_rate": metrics["deterministic"]["completed_rate"],
                               "deterministic_mean_steps": metrics["deterministic"]["mean_steps"],
                               "stochastic_mean_delivered": metrics["stochastic"]["mean_delivered"],
                               "stochastic_completed_rate": metrics["stochastic"]["completed_rate"],
                               "stochastic_mean_steps": metrics["stochastic"]["mean_steps"],
                               "actual_agent_transitions": summary["actual_agent_transitions"], "error": ""}
                    except KeyboardInterrupt:
                        raise
                    except BaseException as error:
                        row = {**entry, "status": "failed", "error": f"{type(error).__name__}: {error}"}
                    rows.append(row)
                    manifest["runs"].append(row)
                    recorded[key] = row
                    save_manifest()
                    candidate_results[(seed, mode)] = row
            for seed in seeds:
                full = candidate_results.get((seed, "full"))
                no_pheromone = candidate_results.get((seed, "no_pheromone"))
                random = candidate_results[(seed, "random")]
                if full and no_pheromone and full["status"] == no_pheromone["status"] == "completed":
                    paired.append({"candidate_id": candidate_id, "training_seed": seed,
                                   "full_minus_no_pheromone": full["stochastic_mean_delivered"] - no_pheromone["stochastic_mean_delivered"],
                                   "full_minus_random": full["stochastic_mean_delivered"] - random["stochastic_mean_delivered"],
                                   "full_beats_no_pheromone": full["stochastic_mean_delivered"] > no_pheromone["stochastic_mean_delivered"],
                                   "full_beats_random": full["stochastic_mean_delivered"] > random["stochastic_mean_delivered"]})
        candidate_gate = {}
        for candidate_id, _, _ in candidates:
            rows_for_candidate = [row for row in paired if row["candidate_id"] == candidate_id]
            candidate_gate[candidate_id] = (len(rows_for_candidate) == len(seeds) and
                                             all(row["full_beats_no_pheromone"] and row["full_beats_random"]
                                                 for row in rows_for_candidate))
        _write_csv(output / "runs.csv", rows, replace=resume)
        _write_csv(output / "paired.csv", paired, replace=resume)
        summary = {"candidate_advances_by_stochastic_development_gate": candidate_gate,
                   "automatic_selection": False, "run_rows": len(rows), "paired_rows": len(paired),
                   "limitations": ["development maps only", "gate is a team-review aid, not a final result",
                                   "no attack, detector, dataset, or held-out evaluation was run"]}
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        manifest.update(status="completed", elapsed_seconds=time.perf_counter() - start,
                        candidate_advances_by_stochastic_development_gate=candidate_gate)
        save_manifest()
        return summary
    except BaseException as error:
        manifest.update(status="incomplete" if isinstance(error, KeyboardInterrupt) else "failed",
                        error=f"{type(error).__name__}: {error}", elapsed_seconds=time.perf_counter() - start)
        save_manifest()
        raise
