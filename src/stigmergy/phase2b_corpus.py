"""Build a leakage-aware archive from completed Phase 2B calibration runs.

Phase 2B has three completed, development-only false-food calibrations. Each
run already contains matched ``clean``, ``injection_disabled`` and ``attacked``
episodes, but those experiment artifacts are inconvenient to inspect together.
This module packages them into one local calibration corpus while preserving
their provenance and negative results. It is deliberately *not* a detector
data generator: it creates no temporal windows, no train/validation/test
partition, no attack labels for model input, and no learned model.

For every source episode, the builder writes two files. ``model_observable``
contains only ``step`` and the existing ``local`` record (local observations,
the policy's actions, local transition events and rewards). ``audit`` contains
the corresponding simulator-only attack events, global/honest delivery and
episode provenance. The two files share a path structure for human audit, but
their contents are intentionally separate. Future detector code must consume
only an explicitly approved feature view, never the audit tree or file paths.

The source plan names completed artifact directories. A corpus group is the
source calibration identifier plus an existing policy/map/action group ID, so
identically named groups from different attack settings never collide. All
three scenario variants stay in that same development group. Generated corpus
files belong under ignored ``data/generated/``; this module, its plan and its
tests are the versioned reproducibility contract. Local records are checked
against the documented fields, per-agent shapes and types before copying.
Manifest and split provenance must agree exactly; no missing scenario, repeated
group or malformed numeric value can acquire completed corpus status.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import re

from .defense import FEATURE_NAMES


PLAN_PURPOSE = "phase2b_development_calibration_corpus"
SOURCE_PURPOSE = "development_only_phase2b_attack_calibration"
SCENARIOS = ("clean", "injection_disabled", "attacked")
FORBIDDEN_MODEL_KEYS = frozenset({
    "attack_events", "attack_summary", "compromised_agents",
    "compromised_count", "compromised_fraction", "requested_mass",
    "authorized_mass", "applied_mass", "honest_delivered", "total_delivered",
})

LOCAL_REQUIRED_KEYS = frozenset({
    "observations_before", "features", "proposed_actions", "executed_actions",
    "rewards", "terminations", "truncations", "infos", "timeout_active",
})
GROUP_PROVENANCE = ("training_seed", "map_seed", "action_seed", "action_mode", "split")


def validate_local_record(local, path):
    """Return stable agent IDs after enforcing the local trajectory contract.

    Inputs are decoded JSON records: 58 finite observation values, 12 finite
    history features, actions 0..4, finite shared reward and Boolean outcomes
    per agent. observations_after is permitted as the existing optional local
    outcome view; audit metadata and all other unknown fields are rejected.
    Agent IDs route records but remain provenance, never detector features.
    """
    if not isinstance(local, dict):
        raise ValueError(f"local record must be an object: {path}")
    if _forbidden_keys(local):
        raise ValueError(f"local record leaks simulator-only metadata; leaks simulator-only keys: {path}")
    if not LOCAL_REQUIRED_KEYS <= set(local) or set(local) - LOCAL_REQUIRED_KEYS - {"observations_after"}:
        raise ValueError(f"local record has missing or unknown fields: {path}")
    observations = local["observations_before"]
    if not isinstance(observations, dict) or not observations or not all(
            isinstance(agent, str) and agent for agent in observations):
        raise ValueError(f"local observations require nonempty string agent IDs: {path}")
    agents = tuple(sorted(observations))
    for name, values in local.items():
        if not isinstance(values, dict) or set(values) != set(agents):
            raise ValueError(f"local field {name} does not match agent IDs: {path}")
    def finite(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    for agent in agents:
        for name, width in (("observations_before", 58), ("observations_after", 58),
                            ("features", len(FEATURE_NAMES))):
            if name in local:
                values = local[name][agent]
                if not isinstance(values, list) or len(values) != width or not all(map(finite, values)):
                    raise ValueError(f"{name} must contain {width} finite numeric values: {path}")
        for name in ("proposed_actions", "executed_actions"):
            value = local[name][agent]
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < 5:
                raise ValueError(f"{name} must be an integer action 0..4: {path}")
        if not finite(local["rewards"][agent]):
            raise ValueError(f"reward must be finite numeric data: {path}")
        for name in ("terminations", "truncations", "timeout_active"):
            if not isinstance(local[name][agent], bool):
                raise ValueError(f"{name} must contain Boolean outcomes: {path}")
        info = local["infos"][agent]
        if (not isinstance(info, dict) or set(info) != {"blocked", "picked_up", "delivered"} or
                not all(isinstance(value, bool) for value in info.values())):
            raise ValueError(f"infos must contain Boolean blocked/picked_up/delivered outcomes: {path}")
    return agents


def validate_group(group, id_key="group_id"):
    """Reject incomplete families, unsafe IDs and malformed development provenance."""
    if (not isinstance(group, dict) or not isinstance(group.get(id_key), str) or
            not re.fullmatch(r"[A-Za-z0-9_-]+", group[id_key]) or
            group.get("split") != "development" or group.get("action_mode") != "stochastic" or
            not isinstance(group.get("scenarios"), (list, tuple)) or
            tuple(group["scenarios"]) != SCENARIOS):
        raise ValueError("source group is not one complete development family")
    for name in ("training_seed", "map_seed", "action_seed"):
        value = group.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < 2**32:
            raise ValueError("group provenance requires valid integer seeds")



@dataclass(frozen=True)
class CorpusSource:
    """Identify one completed calibration run by a stable local name and path."""

    calibration_id: str
    run_path: str

    def __post_init__(self):
        if not re.fullmatch(r"[a-z][a-z0-9_]*", self.calibration_id):
            raise ValueError("calibration_id must use lowercase letters, digits and underscores")
        path = Path(self.run_path) if isinstance(self.run_path, str) else None
        if (not isinstance(self.run_path, str) or not self.run_path or path.is_absolute() or
                ".." in path.parts):
            raise ValueError("run_path must be a nonempty repository-relative path")


@dataclass(frozen=True)
class Phase2BCorpusPlan:
    """Validate the explicit list of calibration artifacts admitted to one corpus."""

    format_version: int = 1
    purpose: str = PLAN_PURPOSE
    sources: tuple = ()

    def __post_init__(self):
        if self.format_version != 1 or self.purpose != PLAN_PURPOSE:
            raise ValueError("unsupported Phase 2B calibration-corpus plan")
        if not isinstance(self.sources, (list, tuple)) or not self.sources:
            raise ValueError("sources must be a nonempty list")
        sources = tuple(source if isinstance(source, CorpusSource) else CorpusSource(**source)
                        for source in self.sources)
        if len(sources) != len({source.calibration_id for source in sources}):
            raise ValueError("calibration IDs must be unique")
        object.__setattr__(self, "sources", sources)


def _sha256_bytes(value):
    """Return a content hash used to bind generated files to their sources."""
    return hashlib.sha256(value).hexdigest()


def _read_json(path, label):
    """Read one required JSON object and give malformed sources a useful error."""
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid {label}: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object: {path}")
    return value


def _write_json(path, value):
    """Write deterministic JSON so corpus manifests are diffable and hashable."""
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path, records):
    """Write JSON Lines in source step order without retaining file handles."""
    with Path(path).open("x", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def _resolve_inside(root, relative, label):
    """Resolve a repository-relative source without allowing plan path escape."""
    path = root / relative
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"{label} must remain inside the repository root") from error
    if not path.is_dir():
        raise ValueError(f"{label} does not exist: {relative}")
    return path


def load_phase2b_corpus_plan(plan_path):
    """Load a checked-in corpus plan and resolve its repository root safely."""
    plan_path = Path(plan_path)
    raw = _read_json(plan_path, "corpus plan")
    plan = Phase2BCorpusPlan(**raw)
    if len(plan_path.parents) < 3:
        raise ValueError("corpus plan must live below <root>/configs/phase2b/")
    return plan, plan_path.parents[2]


def _forbidden_keys(value):
    """Find simulator-only keys recursively before a local record is copied."""
    found = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_MODEL_KEYS:
                found.add(key)
            found.update(_forbidden_keys(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_forbidden_keys(item))
    return found


def _load_source_groups(root, source):
    """Validate one completed run and return its immutable scenario families.

    The returned list contains source paths only after completion status,
    scenario membership and development-only split membership agree. This
    ensures a later partial run cannot be mistaken for a dataset input.
    """
    run = _resolve_inside(root, source.run_path, "run_path")
    manifest_path, split_path = run / "manifest.json", run / "group_splits.json"
    manifest = _read_json(manifest_path, "source manifest")
    splits = _read_json(split_path, "source group split manifest")
    if manifest.get("status") != "completed" or manifest.get("purpose") != SOURCE_PURPOSE:
        raise ValueError(f"source run is not a completed Phase 2B calibration: {source.calibration_id}")
    groups = manifest.get("groups")
    assignments = splits.get("assignments")
    if not isinstance(groups, list) or not isinstance(assignments, list) or not groups:
        raise ValueError(f"source run has no complete group manifest: {source.calibration_id}")
    assignment_by_id = {item.get("group_id"): item for item in assignments if isinstance(item, dict)}
    if len(assignment_by_id) != len(assignments):
        raise ValueError(f"source group assignments are duplicate or malformed: {source.calibration_id}")
    validated = []
    seen = set()
    for group in groups:
        validate_group(group)
        group_id = group["group_id"]
        if group_id in seen:
            raise ValueError("duplicate source group in manifest")
        seen.add(group_id)
        if assignment_by_id.get(group_id) != group:
            raise ValueError(f"source manifest and split provenance disagree: {source.calibration_id}")
        validated.append(group)
    if set(assignment_by_id) != seen:
        raise ValueError(f"source manifest and split assignments disagree: {source.calibration_id}")
    return run, manifest, validated


def _package_episode(run, source, group, scenario, output):
    """Copy one episode into separate local and audit records after validation."""
    group_id = group["group_id"]
    source_dir = run / "episodes" / group_id / scenario
    episode_path, steps_path = source_dir / "episode.json", source_dir / "steps.jsonl"
    episode = _read_json(episode_path, "source episode")
    if not steps_path.is_file() or episode.get("split") != "development":
        raise ValueError(f"source episode is missing or outside development: {source.calibration_id}/{group_id}/{scenario}")
    metrics = episode.get("metrics")
    if not isinstance(metrics, dict) or metrics.get("scenario") != scenario or metrics.get("group_id") != group_id:
        raise ValueError(f"source episode metrics do not match its group: {source.calibration_id}/{group_id}/{scenario}")
    if any(metrics.get(key) != group[key] for key in ("map_seed", "action_seed", "action_mode")):
        raise ValueError("source episode provenance does not match its group")
    model_records, audit_records = [], []
    episode_agents = None
    for expected_step, line in enumerate(steps_path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"source steps are invalid JSON: {steps_path}") from error
        if not isinstance(record, dict) or record.get("step") != expected_step:
            raise ValueError(f"source steps are not sequential: {steps_path}")
        local, audit = record.get("local"), record.get("simulator_metadata")
        if not isinstance(local, dict) or not isinstance(audit, dict):
            raise ValueError(f"source steps do not separate local and audit fields: {steps_path}")
        leaked = _forbidden_keys(local)
        if leaked:
            raise ValueError(f"source local record leaks simulator-only keys {sorted(leaked)}: {steps_path}")
        agents = validate_local_record(local, steps_path)
        if episode_agents is not None and agents != episode_agents:
            raise ValueError("source episode changed its agent population")
        episode_agents = agents
        model_records.append({"step": expected_step, "local": local})
        audit_records.append({"step": expected_step, "simulator_metadata": audit})
    if not model_records or metrics.get("steps") != len(model_records):
        raise ValueError(f"source step count disagrees with episode metrics: {steps_path}")
    relative = Path(source.calibration_id) / group_id / scenario
    model_dir, audit_dir = output / "model_observable" / relative, output / "audit" / relative
    model_dir.mkdir(parents=True, exist_ok=False)
    audit_dir.mkdir(parents=True, exist_ok=False)
    _write_jsonl(model_dir / "steps.jsonl", model_records)
    _write_jsonl(audit_dir / "steps.jsonl", audit_records)
    _write_json(audit_dir / "episode.json", episode)
    return {
        "calibration_id": source.calibration_id,
        "original_group_id": group_id,
        "corpus_group_id": f"{source.calibration_id}__{group_id}",
        "scenario": scenario,
        "training_seed": group["training_seed"], "map_seed": group["map_seed"],
        "action_seed": group["action_seed"], "action_mode": group["action_mode"],
        "split": "development", "step_count": len(model_records),
        "model_observable_steps": str(Path("model_observable") / relative / "steps.jsonl"),
        "audit_steps": str(Path("audit") / relative / "steps.jsonl"),
        "audit_episode": str(Path("audit") / relative / "episode.json"),
        "source_local_record_sha256": metrics.get("local_record_sha256"),
    }


def build_phase2b_calibration_corpus(plan_path, output):
    """Build a fresh local corpus from all declared completed calibration sources.

    ``output`` must be a new directory inside the repository (normally under
    ``data/generated``). A started/failed manifest is retained if a source is
    invalid, while a successful corpus includes a stable audit index and a
    group manifest. The function returns only aggregate counts; callers should
    inspect audit files for simulator-only outcomes.
    """
    plan, root = load_phase2b_corpus_plan(plan_path)
    output = Path(output)
    if not output.is_absolute():
        output = root / output
    try:
        output.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise ValueError("corpus output must remain inside the repository root") from error
    source_details = []
    for source in plan.sources:
        run, manifest, groups = _load_source_groups(root, source)
        source_details.append((source, run, manifest, groups))
    output.mkdir(parents=True, exist_ok=False)
    plan_bytes = Path(plan_path).read_bytes()
    manifest = {
        "format_version": 1, "status": "started", "purpose": PLAN_PURPOSE,
        "development_only": True, "plan": asdict(plan), "plan_sha256": _sha256_bytes(plan_bytes),
        "model_observable_fields": ["step", "local"],
        "simulator_only_location": "audit/",
        "forbidden_model_keys": sorted(FORBIDDEN_MODEL_KEYS), "sources": [], "groups": [],
    }
    _write_json(output / "manifest.json", manifest)
    index = []
    try:
        for source, run, source_manifest, groups in source_details:
            manifest["sources"].append({
                "calibration_id": source.calibration_id, "run_path": source.run_path,
                "manifest_sha256": _sha256_bytes((run / "manifest.json").read_bytes()),
                "attack_config": source_manifest.get("attack_config"),
                "group_count": len(groups),
            })
            for group in groups:
                corpus_group_id = f"{source.calibration_id}__{group['group_id']}"
                manifest["groups"].append({
                    "corpus_group_id": corpus_group_id, "calibration_id": source.calibration_id,
                    "original_group_id": group["group_id"], "split": "development",
                    "training_seed": group["training_seed"], "map_seed": group["map_seed"],
                    "action_seed": group["action_seed"], "action_mode": group["action_mode"],
                    "scenarios": list(SCENARIOS),
                })
                for scenario in SCENARIOS:
                    index.append(_package_episode(run, source, group, scenario, output))
        _write_jsonl(output / "audit_index.jsonl", index)
        groups = manifest["groups"]
        split_manifest = {
            "format_version": 1, "purpose": "phase2b_development_corpus_group_manifest",
            "plan_sha256": manifest["plan_sha256"], "assignments": groups,
            "rule": "all scenario variants in one calibration/policy/map/action family remain together",
        }
        _write_json(output / "group_splits.json", split_manifest)
        summary = {"purpose": PLAN_PURPOSE, "development_only": True,
                   "source_run_count": len(source_details), "group_count": len(groups),
                   "episode_count": len(index), "scenario_count_per_group": len(SCENARIOS),
                   "split_counts": {"development": len(groups)},
                   "limitations": ["calibration evidence only", "no temporal windows",
                                   "no train/validation/test split", "no detector was fit",
                                   "no defense was evaluated", "not a robustness claim"]}
        _write_json(output / "summary.json", summary)
        manifest["status"] = "completed"
        manifest["group_split_manifest_sha256"] = _sha256_bytes(
            (output / "group_splits.json").read_bytes())
        manifest["summary_sha256"] = _sha256_bytes((output / "summary.json").read_bytes())
        _write_json(output / "manifest.json", manifest)
        return summary
    except BaseException as error:
        manifest.update(status="incomplete" if isinstance(error, KeyboardInterrupt) else "failed",
                        error=f"{type(error).__name__}: {error}")
        _write_json(output / "manifest.json", manifest)
        raise
