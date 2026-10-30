import json

import pytest

from spacecraft.components import (
    Engine,
    FuelTank,
    Payload,
    PowerSystem,
)
from spacecraft.presets import load_spacecraft, save_spacecraft
from spacecraft.vehicle import Spacecraft


def test_spacecraft_preset_round_trip(tmp_path):
    craft = Spacecraft("Moon Explorer")
    craft.add_component(
        Engine(
            name="Vacuum engine",
            dry_mass=500.0,
            thrust=981_000.0,
            isp=348.0,
            fuel_type="LOX/RP-1",
            power_draw_kw=0.2,
        )
    )
    craft.add_component(
        FuelTank(
            name="Main tank",
            dry_mass=2_500.0,
            capacity=40_000.0,
            fuel_mass=15_000.0,
            fuel_type="LOX/RP-1",
        )
    )
    craft.add_component(Payload(name="Lander", dry_mass=2_000.0))
    craft.add_component(
        PowerSystem(
            name="Solar panels",
            dry_mass=80.0,
            generation_kw=1.2,
            storage_kwh=5.0,
        )
    )
    path = tmp_path / "craft.json"

    save_spacecraft(craft, path)
    restored = load_spacecraft(path)

    assert restored.name == craft.name
    assert [type(part) for part in restored.components] == [
        Engine,
        FuelTank,
        Payload,
        PowerSystem,
    ]
    assert restored.components[1].fuel_mass == 15_000.0
    assert restored.components[0].id == craft.components[0].id


def test_load_rejects_unsupported_preset_version(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"schema_version": 99, "components": []}))

    with pytest.raises(ValueError, match="schema version"):
        load_spacecraft(path)


def test_load_rejects_unknown_component_types(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "name": "Invalid",
                "components": [{"type": "UnknownComponent"}],
            }
        )
    )

    with pytest.raises(ValueError, match="Unknown component type"):
        load_spacecraft(path)
