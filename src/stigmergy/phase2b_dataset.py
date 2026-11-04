"""Export the Phase 2B calibration corpus as inspectable agent-step rows.

The Phase 2B corpus stores one JSON Lines record per *environment* step, with
one local observation/action record for each agent. That layout is safe and
faithful to rollout order, but it is awkward to open in a spreadsheet or pass
to a conventional tabular-data loader. This module creates a derived CSV view
with one row per agent per environment step. It does not create temporal
windows, fit a model, assign train/validation/test splits, or derive labels
from simulator-only attack metadata.

The exporter reads only the corpus's ``model_observable`` step files. The
resulting ``agent_steps.csv`` has three explicitly separated column families:

* provenance columns (group, map, scenario, seed and agent identifiers), which
  exist for grouping and auditing and must not be model inputs;
* local input columns: 58 observation values and the 12 named local-history
  values already available to an honest agent; and
* local transition/outcome columns such as chosen action, reward, pickup and
  delivery. These are possible targets for engineering experiments, not input
  features by default.

The matching ``schema.json`` identifies these families so accidental leakage is
visible in code review. In particular, the exporter never opens the corpus
``audit`` tree, so attacker identities, attack events, mass and global delivery
accounting cannot enter the tabular CSV. The output remains a development-only
data view: it is useful for inspection and loader prototyping, but cannot
support a held-out detector or robustness claim.
"""

import csv
import hashlib
import json
from pathlib import Path

from .defense import FEATURE_NAMES
from .phase2b_corpus import FORBIDDEN_MODEL_KEYS, PLAN_PURPOSE


FORMAT_VERSION = 1
OBSERVATION_WIDTH = 58
LOCAL_REQUIRED_KEYS = frozenset({
    "observations_before", "features", "proposed_actions", "executed_actions",
    "rewards", "terminations", "truncations", "infos", "timeout_active",
})
PROVENANCE_COLUMNS = (
    "calibration_id", "corpus_group_id", "scenario", "split", "training_seed",
    "map_seed", "action_seed", "action_mode", "agent_id", "step",
)
OBSERVATION_COLUMNS = tuple(f"observation_before_{index:02d}"
                            for index in range(OBSERVATION_WIDTH))
HISTORY_COLUMNS = tuple(f"history_{name}" for name in FEATURE_NAMES)
OUTCOME_COLUMNS = (
    "proposed_action", "executed_action", "reward", "terminated", "truncated",
    "blocked", "picked_up", "delivered", "timeout_active",
)
CSV_COLUMNS = PROVENANCE_COLUMNS + OBSERVATION_COLUMNS + HISTORY_COLUMNS + OUTCOME_COLUMNS


def _sha256_file(path):
    """Return a content digest without loading a potentially large CSV at once."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path, label):
    """Read a JSON object and turn malformed input into a clear corpus error."""
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid {label}: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object: {path}")
    return value


def _read_jsonl(path, label):
    """Read nonempty JSON Lines records while preserving declared source order."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValueError(f"invalid {label}: {path}") from error
    if not lines:
        raise ValueError(f"{label} must not be empty: {path}")
    records = []
    for line_number, line in enumerate(lines, start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSON in {label} at line {line_number}: {path}") from error
        if not isinstance(value, dict):
            raise ValueError(f"{label} record must be an object: {path}")
        records.append(value)
    return records


def _resolve_inside(root, relative, label):
    """Resolve an index path while rejecting absolute paths and parent traversal."""
    if not isinstance(relative, str) or not relative:
        raise ValueError(f"{label} must be a nonempty relative path")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{label} must remain inside the corpus")
    path = root / candidate
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"{label} must remain inside the corpus") from error
    if not path.is_file():
        raise ValueError(f"{label} does not exist: {relative}")
    return path


def _contains_forbidden_key(value):
    """Return whether a purported local record contains audit-only metadata."""
    if isinstance(value, dict):
        return any(key in FORBIDDEN_MODEL_KEYS or _contains_forbidden_key(item)
                   for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _validate_corpus(corpus):
    """Check the completed corpus manifest and return its stable episode index."""
    manifest = _read_json(corpus / "manifest.json", "corpus manifest")
    if (manifest.get("format_version") != 1 or manifest.get("status") != "completed" or
            manifest.get("purpose") != PLAN_PURPOSE or not manifest.get("development_only")):
        raise ValueError("input must be a completed development-only Phase 2B corpus")
    index = _read_jsonl(corpus / "audit_index.jsonl", "corpus audit index")
    group_ids = {group.get("corpus_group_id") for group in manifest.get("groups", [])
                 if isinstance(group, dict)}
    if not group_ids:
        raise ValueError("corpus manifest has no groups")
    seen = set()
    for entry in index:
        key = (entry.get("corpus_group_id"), entry.get("scenario"))
        if (key[0] not in group_ids or key in seen or entry.get("split") != "development" or
                not isinstance(entry.get("step_count"), int) or entry["step_count"] < 1):
            raise ValueError("corpus audit index has invalid or duplicate episode provenance")
        seen.add(key)
    return manifest, index


def _agent_ids(local, path):
    """Validate shared agent keys across one local transition record."""
    if not isinstance(local, dict) or not LOCAL_REQUIRED_KEYS <= set(local):
        raise ValueError(f"local record has missing required fields: {path}")
    if _contains_forbidden_key(local):
        raise ValueError(f"local record leaks simulator-only metadata: {path}")
    observations = local["observations_before"]
    if not isinstance(observations, dict) or not observations:
        raise ValueError(f"local observations must identify at least one agent: {path}")
    agents = tuple(sorted(observations))
    if not all(isinstance(agent, str) for agent in agents):
        raise ValueError(f"local agent IDs must be strings: {path}")
    for key in LOCAL_REQUIRED_KEYS:
        value = local[key]
        if not isinstance(value, dict) or set(value) != set(agents):
            raise ValueError(f"local field {key} does not match agent IDs: {path}")
    return agents


def _agent_row(entry, step, local, agent, path):
    """Flatten one agent's allowed local state and local transition outcomes."""
    observation, features = local["observations_before"][agent], local["features"][agent]
    if (not isinstance(observation, list) or len(observation) != OBSERVATION_WIDTH or
            not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in observation)):
        raise ValueError(f"agent observation must contain {OBSERVATION_WIDTH} numeric values: {path}")
    if (not isinstance(features, list) or len(features) != len(FEATURE_NAMES) or
            not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in features)):
        raise ValueError(f"agent history features must contain {len(FEATURE_NAMES)} numeric values: {path}")
    info = local["infos"][agent]
    if not isinstance(info, dict) or set(info) != {"blocked", "picked_up", "delivered"}:
        raise ValueError(f"agent local info fields are malformed: {path}")
    row = {column: entry[column] for column in PROVENANCE_COLUMNS[:-2]}
    row.update(agent_id=agent, step=step)
    row.update(zip(OBSERVATION_COLUMNS, observation))
    row.update(zip(HISTORY_COLUMNS, features))
    row.update(proposed_action=local["proposed_actions"][agent],
               executed_action=local["executed_actions"][agent], reward=local["rewards"][agent],
               terminated=local["terminations"][agent], truncated=local["truncations"][agent],
               blocked=info["blocked"], picked_up=info["picked_up"], delivered=info["delivered"],
               timeout_active=local["timeout_active"][agent])
    return row


def _schema():
    """Describe which exported fields are safe inputs versus provenance/outcomes."""
    return {
        "format_version": FORMAT_VERSION,
        "row_unit": "one agent at one completed environment transition",
        "development_only": True,
        "provenance_columns_not_model_inputs": list(PROVENANCE_COLUMNS),
        "model_input_columns": list(OBSERVATION_COLUMNS + HISTORY_COLUMNS),
        "local_outcome_columns_not_default_inputs": list(OUTCOME_COLUMNS),
        "excluded_simulator_only_fields": sorted(FORBIDDEN_MODEL_KEYS),
        "observation_width": OBSERVATION_WIDTH,
        "history_feature_names": list(FEATURE_NAMES),
        "temporal_windows_created": False,
        "train_validation_test_split_created": False,
        "detector_labels_created": False,
    }


def export_phase2b_agent_steps(corpus, output):
    """Write a fresh, flat CSV view of a completed Phase 2B development corpus.

    Parameters
    ----------
    corpus:
        Path to a corpus generated by ``phase2b-build-corpus``. Its manifest,
        index and local step records are validated before export.
    output:
        A new directory for ``agent_steps.csv``, ``schema.json`` and
        ``manifest.json``. Existing directories are rejected to preserve prior
        generated datasets.

    Returns
    -------
    dict
        Aggregate episode, environment-step and agent-step counts plus explicit
        development-only limitations. No model is trained by this function.
    """
    corpus, output = Path(corpus), Path(output)
    manifest, index = _validate_corpus(corpus)
    output.mkdir(parents=True, exist_ok=False)
    export_manifest = {
        "format_version": FORMAT_VERSION, "status": "started",
        "purpose": "phase2b_development_agent_step_export", "development_only": True,
        "source_corpus_manifest_sha256": _sha256_file(corpus / "manifest.json"),
        "source_corpus_index_sha256": _sha256_file(corpus / "audit_index.jsonl"),
        "source_group_count": len(manifest["groups"]), "source_episode_count": len(index),
        "source_purpose": manifest["purpose"],
        "files": {"agent_steps": "agent_steps.csv", "schema": "schema.json"},
    }
    (output / "manifest.json").write_text(json.dumps(export_manifest, indent=2, sort_keys=True) + "\n",
                                               encoding="utf-8")
    environment_steps, agent_steps = 0, 0
    try:
        with (output / "agent_steps.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for entry in index:
                path = _resolve_inside(corpus, entry.get("model_observable_steps"),
                                       "model_observable_steps")
                records = _read_jsonl(path, "model-observable step file")
                if len(records) != entry["step_count"]:
                    raise ValueError(f"episode step count disagrees with its audit index: {path}")
                for expected_step, record in enumerate(records, start=1):
                    if set(record) != {"step", "local"} or record["step"] != expected_step:
                        raise ValueError(f"model-observable steps are not sequential local records: {path}")
                    local = record["local"]
                    for agent in _agent_ids(local, path):
                        writer.writerow(_agent_row(entry, expected_step, local, agent, path))
                        agent_steps += 1
                    environment_steps += 1
        schema = _schema()
        (output / "schema.json").write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n",
                                              encoding="utf-8")
        summary = {
            "purpose": export_manifest["purpose"], "development_only": True,
            "episode_count": len(index), "group_count": len(manifest["groups"]),
            "environment_step_count": environment_steps, "agent_step_count": agent_steps,
            "csv_sha256": _sha256_file(output / "agent_steps.csv"),
            "limitations": ["development maps only", "no temporal windows",
                            "no train/validation/test split", "no detector labels", "no model was fit",
                            "not a robustness claim"],
        }
        (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                               encoding="utf-8")
        export_manifest.update(status="completed", summary_sha256=_sha256_file(output / "summary.json"),
                               schema_sha256=_sha256_file(output / "schema.json"))
        (output / "manifest.json").write_text(json.dumps(export_manifest, indent=2, sort_keys=True) + "\n",
                                                   encoding="utf-8")
        return summary
    except BaseException as error:
        export_manifest.update(status="incomplete" if isinstance(error, KeyboardInterrupt) else "failed",
                               error=f"{type(error).__name__}: {error}")
        (output / "manifest.json").write_text(json.dumps(export_manifest, indent=2, sort_keys=True) + "\n",
                                                   encoding="utf-8")
        raise
