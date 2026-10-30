import numpy as np
import pytest

from spacecraft import mass_properties
from spacecraft.components import Engine, FuelTank, Payload
from spacecraft.geometry import component_centers, layout_spacecraft
from spacecraft.placement import NODE_BOTTOM, NODE_MOUNT, NODE_TOP, Placement
from spacecraft.vehicle import LandingGear, Spacecraft


def make_craft():
    craft = Spacecraft("Assembly")
    craft.add_component(
        Engine(name="Engine", dry_mass=100.0, thrust=1_000.0, isp=300.0, fuel_type="test")
    )
    craft.add_component(
        FuelTank(
            name="Tank",
            dry_mass=200.0,
            capacity=500.0,
            fuel_mass=400.0,
            fuel_type="test",
        )
    )
    craft.add_component(Payload(name="Payload", dry_mass=50.0))
    return craft


def test_placement_json_validation_round_trip(tmp_path):
    from spacecraft.presets import load_spacecraft, save_spacecraft

    craft = make_craft()
    engine = craft.components[0]
    engine.placement = Placement(
        parent_id=craft.components[1].id,
        parent_node=NODE_BOTTOM,
        node=NODE_TOP,
        offset=(0.2, 0.3, -0.1),
        rotation_deg=(0.0, 90.0, 0.0),
    )
    path = tmp_path / "placed.json"

    save_spacecraft(craft, path)
    restored = load_spacecraft(path)

    assert restored.components[0].placement == engine.placement


def test_attachment_layout_snaps_child_node_to_parent_node():
    craft = Spacecraft("Stack")
    tank = FuelTank(
        name="Tank", dry_mass=100.0, capacity=1_000.0, fuel_mass=500.0, fuel_type="test"
    )
    engine = Engine(
        name="Engine", dry_mass=50.0, thrust=1_000.0, isp=300.0, fuel_type="test"
    )
    craft.add_component(tank)
    craft.add_component(engine)
    engine.placement = Placement(
        parent_id=tank.id,
        parent_node=NODE_BOTTOM,
        node=NODE_TOP,
    )

    layout = layout_spacecraft(craft)
    tank_part = next(part for part in layout.parts if part.component_id == tank.id)
    engine_part = next(part for part in layout.parts if part.component_id == engine.id)

    # Tank bottom is its base plane; engine top is the engine-mount point.
    tank_bottom = tank_part.model @ np.array([0.0, 0.0, 0.0, 1.0])
    engine_top = engine_part.model @ np.array([0.0, 1.0, 0.0, 1.0])
    np.testing.assert_allclose(engine_top[:3], tank_bottom[:3], atol=1e-6)


def test_mount_attachment_snaps_component_centres():
    craft = make_craft()
    tank, engine = craft.components[:2]
    engine.placement = Placement(
        parent_id=tank.id,
        parent_node=NODE_MOUNT,
        node=NODE_MOUNT,
    )

    centres = component_centers(craft)

    np.testing.assert_allclose(centres[engine.id], centres[tank.id], atol=1e-6)


def test_mass_properties_and_tip_over_are_available_for_defined_coms():
    craft = Spacecraft(
        "Stable lander",
        landing_gear=LandingGear(
            leg_count=4,
            footprint_radius_m=2.0,
            foot_plane_y_m=0.0,
        ),
    )
    craft.add_component(
        Payload(name="Structure", dry_mass=100.0, com_m=(0.0, 2.0, 0.0))
    )
    craft.add_component(
        FuelTank(
            name="Fuel",
            dry_mass=10.0,
            capacity=100.0,
            fuel_mass=50.0,
            fuel_type="test",
            com_m=(0.0, 1.0, 0.0),
        )
    )
    props = mass_properties(craft)

    assert props.com_m == pytest.approx((0.0, 1.625, 0.0))
    assert craft.tip_over_angle_deg() == pytest.approx(np.degrees(np.arctan2(2.0, 1.625)))


def test_mass_properties_follow_explicit_component_placement():
    craft = Spacecraft("Placed COM")
    payload = Payload(name="Payload", dry_mass=10.0, com_m=(0.0, 0.0, 0.0))
    craft.add_component(payload)
    centre = component_centers(craft)[payload.id]
    payload.com_m = tuple(centre + np.array([0.0, 0.2, 0.0]))

    payload.placement = Placement(offset=(4.0, 2.0, 1.0))
    properties = mass_properties(craft)

    assert properties.com_m == pytest.approx((4.0, 2.2, 1.0))


def test_attachment_cycles_are_rejected():
    craft = make_craft()
    first, second = craft.components[:2]
    first.placement = Placement(parent_id=second.id)
    second.placement = Placement(parent_id=first.id)

    with pytest.raises(ValueError, match="cycle"):
        layout_spacecraft(craft)
