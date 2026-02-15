import pytest
import os
import yaml
from optibonds.models import LadderConditions, LadderStrategy


def test_ladder_conditions_from_yaml_expansion(tmp_path):
    # Create a temporary yaml file with single capital value
    d = tmp_path / "config"
    d.mkdir()
    p = d / "conditions.yml"

    config_data = {
        "ladder_size": 5,
        "step_size": 1,
        "step_width": 1,
        "date_tolerance_days_start": 30,
        "date_tolerance_days_end": 30,
        "years_offset": 0,
        "months_offset": 0,
        "capital_invested": 5000,  # Single value
        "strategy": "max_earnings"
    }

    with open(p, "w") as f:
        yaml.dump(config_data, f)

    # Load from yaml
    conditions = LadderConditions.from_yaml(str(p))

    # Verify expansion happened in from_yaml
    assert conditions.capital_invested == [5000.0, 5000.0, 5000.0, 5000.0, 5000.0]
    assert all(isinstance(c, float) for c in conditions.capital_invested)


def test_ladder_conditions_from_yaml_list(tmp_path):
    # Create a temporary yaml file with list capital value
    d = tmp_path / "config"
    d.mkdir()
    p = d / "conditions_list.yml"

    config_data = {
        "ladder_size": 3,
        "step_size": 1,
        "step_width": 1,
        "date_tolerance_days_start": 30,
        "date_tolerance_days_end": 30,
        "years_offset": 0,
        "months_offset": 0,
        "capital_invested": [1000, 2000, 3000],
        "strategy": "max_earnings"
    }

    with open(p, "w") as f:
        yaml.dump(config_data, f)

    # Load from yaml
    conditions = LadderConditions.from_yaml(str(p))

    # Verify list was kept
    assert conditions.capital_invested == [1000.0, 2000.0, 3000.0]


def test_ladder_conditions_volume_rating(tmp_path):
    d = tmp_path / "config"
    d.mkdir()
    p = d / "conditions_volume.yml"

    config_data = {
        "ladder_size": 1,
        "step_size": 1,
        "step_width": 1,
        "date_tolerance_days_start": 30,
        "date_tolerance_days_end": 30,
        "years_offset": 0,
        "months_offset": 0,
        "capital_invested": 1000,
        "strategy": "max_earnings",
        "min_volume_rating": 3
    }

    with open(p, "w") as f:
        yaml.dump(config_data, f)

    conditions = LadderConditions.from_yaml(str(p))
    assert conditions.min_volume_rating == 3
