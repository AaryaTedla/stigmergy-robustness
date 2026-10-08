"""Versioned, local-observation trajectory artifacts for the attack pilot.

The recorder writes a fresh directory containing ``manifest.json`` and
``steps.jsonl``.  The manifest captures configuration, seed, source revision,
scenario label, and final food/attack accounting.  Each JSONL row contains the
agents' local observations, supplied actions, rewards, lifecycle flags, and a
separate ``simulator_metadata`` object.  That separation is deliberate:
attacker selection and injection mass are useful for auditing generated data
but are not model-observable inputs.

Use ``record_episode`` with an environment and an action provider that maps
the current local observation dictionary to one action per live agent.  The
function does not implement a policy, split data, train a detector, or claim a
benchmark result.  Its action provider may be a future parameter-shared PPO
policy or a clearly labelled scripted fixture.  Clean, injection-disabled,
and attacked scenarios should reuse a map seed and base attack configuration;
``matched_attack_configs`` supplies those three scenario definitions.
"""

from dataclasses import asdict
import json
from pathlib import Path
import subprocess

import numpy as np

from .attacks import AttackConfig


def matched_attack_configs(base_config):
    """Return clean, injection-disabled, and attacked config choices.

    The clean scenario has no injector.  The disabled and attacked scenarios
    use the same ``AttackConfig`` apart from its enabled bit, so a shared reset
    seed selects the same episode-fixed compromised agents in both controls.
    """
    if not isinstance(base_config, AttackConfig):
        raise TypeError("base_config must be an AttackConfig")
    return {"clean": None, "injection_disabled": base_config.injection_disabled(),
            "attacked": base_config}


def _json_value(value):
    """Convert NumPy scalars/arrays and nested values into deterministic JSON."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _git_provenance():
    """Read revision state when the recorder runs inside a Git checkout."""
    revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    return {"source_revision": revision.stdout.strip() if revision.returncode == 0 else "unknown",
            "working_tree_dirty": bool(dirty.stdout.strip()) if dirty.returncode == 0 else None}


class TrajectoryRecorder:
    """Write one episode's auditable steps to a previously unused directory.

    ``start`` must be called after environment reset and before the first
    action.  ``append`` records a complete transition, retaining policy-visible
    observations outside the simulator-only attack metadata.  ``finish``
    finalizes the manifest after termination or truncation.
    """

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.steps_file = None
        self.manifest = None
        self.step_count = 0

    def start(self, environment, seed, scenario, reset_options=None):
        """Create output files and provenance for a just-reset environment."""
        if self.steps_file is not None:
            raise RuntimeError("recorder has already started")
        if not isinstance(scenario, str) or not scenario:
            raise ValueError("scenario must be a nonempty string")
        self.output_dir.mkdir(parents=True, exist_ok=False)
        self.manifest = {"format_version": 1, "scenario": scenario, "seed": seed,
                         "environment_config": asdict(environment.config),
                         "reset_options": _json_value(reset_options or {}),
                         "provenance": _git_provenance(),
                         "model_observable_fields": ["observations_before", "observations_after",
                                                     "actions", "rewards", "terminations", "truncations",
                                                     "infos"],
                         "simulator_only_fields": ["simulator_metadata.attack_events",
                                                     "simulator_metadata.attack_summary"],
                         "steps_file": "steps.jsonl"}
        self.steps_file = (self.output_dir / "steps.jsonl").open("x", encoding="utf-8")

    def append(self, observations_before, actions, transition, environment):
        """Record one transition returned by ``environment.step(actions)``."""
        if self.steps_file is None:
            raise RuntimeError("call start before append")
        observations_after, rewards, terminations, truncations, infos = transition
        event_records = [event.as_dict() for event in environment.last_attack_events]
        record = {"step": self.step_count, "observations_before": observations_before,
                  "actions": actions, "observations_after": observations_after,
                  "rewards": rewards, "terminations": terminations,
                  "truncations": truncations, "infos": infos,
                  "simulator_metadata": {"attack_events": event_records}}
        self.steps_file.write(json.dumps(_json_value(record), sort_keys=True, separators=(",", ":")) + "\n")
        self.step_count += 1

    def finish(self, environment):
        """Close the JSONL file and save final food and attack accounting."""
        if self.steps_file is None or self.manifest is None:
            raise RuntimeError("call start before finish")
        self.steps_file.close()
        self.steps_file = None
        self.manifest.update({"steps": self.step_count, "delivered": int(environment.delivered_total),
                              "remaining_food": int(environment.food.sum()),
                              "carried_food": int(environment.carrying.sum()),
                              "simulator_metadata": {"attack_summary": environment.attack_summary()}})
        (self.output_dir / "manifest.json").write_text(
            json.dumps(_json_value(self.manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return self.manifest


def record_episode(environment, seed, scenario, action_provider, output_dir, reset_options=None):
    """Reset, roll out, and record one episode using only provided actions.

    ``action_provider(observations)`` receives the current dictionary of local
    observations and must return exactly one valid action for every live agent.
    The environment enforces that action contract.  Callers who use scripted
    fixture state must label the artifact as such; this utility itself is not a
    policy implementation.
    """
    if not callable(action_provider):
        raise TypeError("action_provider must be callable")
    observations, _ = environment.reset(seed=seed, options=reset_options)
    recorder = TrajectoryRecorder(output_dir)
    recorder.start(environment, seed, scenario, reset_options)
    while environment.agents:
        actions = action_provider(observations)
        transition = environment.step(actions)
        recorder.append(observations, actions, transition, environment)
        observations = transition[0]
    return recorder.finish(environment)
