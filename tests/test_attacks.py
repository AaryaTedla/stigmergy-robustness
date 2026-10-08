"""Focused evidence for the bounded persistent false-food attack pilot.

Run with ``python -m pytest tests/test_attacks.py`` after installing the pinned
Python 3.11 dependencies.  The pure injector checks establish deterministic
selection, nonnegative occupied-cell writes, budget/cap accounting, and the
injection-disabled control.  Environment and recorder checks ensure attacker
metadata remains outside agent observations/infos while trajectory artifacts
retain it separately for audit.  These are mechanics/provenance checks, not
learned-policy robustness or attack-effectiveness evidence.
"""

import json

import numpy as np
import pytest

from stigmergy import AttackConfig, GridConfig, PersistentFalseFoodInjector, ResourceRetrievalEnv
from stigmergy.trajectories import matched_attack_configs, record_episode


def test_seeded_selection_is_fixed_and_does_not_modify_other_field_channels():
    config = AttackConfig(compromised_count=2, requested_deposit=1, per_step_budget=2, episode_budget=4)
    injectors = [PersistentFalseFoodInjector(config), PersistentFalseFoodInjector(config)]
    selected = [injector.reset(("agent_0", "agent_1", "agent_2"), seed=19) for injector in injectors]
    assert selected[0] == selected[1] and len(selected[0]) == 2
    fields = np.zeros((2, 4, 4), dtype=np.float64)
    positions = np.array([(0, 0), (1, 1), (2, 2)])
    events = injectors[0].inject(fields, positions, field_cap=10)
    assert {event.agent for event in events} == set(selected[0])
    assert all(event.position == tuple(positions[int(event.agent[-1])]) for event in events)
    assert all(event.requested_mass == event.authorized_mass == event.applied_mass == 1 for event in events)
    assert not fields[1].any()


def test_budget_and_field_cap_are_logged_separately():
    injector = PersistentFalseFoodInjector(AttackConfig(
        compromised_count=1, requested_deposit=2, per_step_budget=1.5, episode_budget=2,
    ))
    injector.reset(("agent_0",), seed=1)
    fields = np.zeros((2, 3, 3), dtype=np.float64)
    positions = np.array([(1, 1)])
    first = injector.inject(fields, positions, field_cap=10)[0]
    second = injector.inject(fields, positions, field_cap=10)[0]
    third = injector.inject(fields, positions, field_cap=10)[0]
    assert (first.requested_mass, first.authorized_mass, first.applied_mass) == (2, 1.5, 1.5)
    assert (second.requested_mass, second.authorized_mass, second.applied_mass) == (2, 0.5, 0.5)
    assert (third.requested_mass, third.authorized_mass, third.applied_mass) == (2, 0, 0)
    assert injector.summary()["total_applied_mass"] == 2

    capped = PersistentFalseFoodInjector(AttackConfig(
        compromised_count=1, requested_deposit=2, per_step_budget=2, episode_budget=2,
    ))
    capped.reset(("agent_0",), seed=1)
    fields[0, 1, 1] = 9.5
    event = capped.inject(fields, positions, field_cap=10)[0]
    assert event.authorized_mass == 2 and event.applied_mass == 0.5 and fields[0, 1, 1] == 10


def test_injection_disabled_twin_selects_same_attackers_but_writes_no_mass():
    active = AttackConfig(compromised_count=1, requested_deposit=1, per_step_budget=1, episode_budget=3)
    disabled = PersistentFalseFoodInjector(active.injection_disabled())
    enabled = PersistentFalseFoodInjector(active)
    assert disabled.reset(("agent_0", "agent_1"), seed=31) == enabled.reset(("agent_0", "agent_1"), seed=31)
    fields = np.zeros((2, 3, 3), dtype=np.float64)
    assert disabled.inject(fields, np.array([(0, 0), (1, 1)]), field_cap=10) == ()
    assert not fields.any()
    assert disabled.summary()["total_applied_mass"] == 0


@pytest.mark.parametrize("kwargs", [
    {"compromised_count": 0}, {"requested_deposit": -1}, {"per_step_budget": float("nan")},
    {"episode_budget": -1}, {"mode": "decoy"}, {"enabled": 1},
])
def test_invalid_attack_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        AttackConfig(**kwargs)


def test_environment_hides_attack_identity_and_logs_only_simulator_metadata():
    grid = GridConfig(size=8, n_agents=2, food_per_patch=1, deposit=0, evaporation=0)
    attack = AttackConfig(compromised_count=1, requested_deposit=1, per_step_budget=1, episode_budget=2)
    env = ResourceRetrievalEnv(grid, attack_config=attack)
    observations, infos = env.reset(seed=7, options={"food_positions": [(1, 3), (6, 6)]})
    next_observations, _, _, _, next_infos = env.step({agent: 0 for agent in env.agents})
    assert env.last_attack_events and env.last_attack_events[0].position == tuple(env.positions[
        int(env.last_attack_events[0].agent[-1])
    ])
    assert all("attack" not in key and "compromised" not in key for info in infos.values() for key in info)
    assert all("attack" not in key and "compromised" not in key for info in next_infos.values() for key in info)
    assert all(env.observation_space(agent).contains(value) for agent, value in observations.items())
    assert all(env.observation_space(agent).contains(value) for agent, value in next_observations.items())
    assert env.attack_summary()["compromised_count"] == 1


def test_recorder_separates_auditing_metadata_from_local_observations(tmp_path):
    config = GridConfig(size=8, n_agents=2, horizon=2, deposit=0, evaporation=0)
    attack = AttackConfig(compromised_count=1, requested_deposit=1, per_step_budget=1, episode_budget=2)
    scenarios = matched_attack_configs(attack)
    assert scenarios["clean"] is None and not scenarios["injection_disabled"].enabled and scenarios["attacked"].enabled
    environment = ResourceRetrievalEnv(config, attack_config=scenarios["attacked"])
    manifest = record_episode(environment, seed=9, scenario="attacked",
                              action_provider=lambda observations: {agent: 0 for agent in observations},
                              output_dir=tmp_path / "episode",
                              reset_options={"food_positions": [(1, 3), (6, 6)]})
    saved_manifest = json.loads((tmp_path / "episode" / "manifest.json").read_text())
    records = [json.loads(line) for line in (tmp_path / "episode" / "steps.jsonl").read_text().splitlines()]
    assert manifest == saved_manifest and manifest["steps"] == 2
    assert "simulator_metadata.attack_events" in manifest["simulator_only_fields"]
    assert manifest["simulator_metadata"]["attack_summary"]["total_applied_mass"] == 2
    assert len(records) == 2 and records[0]["simulator_metadata"]["attack_events"]
    assert "compromised_agents" not in records[0]["observations_before"]
