import numpy as np
import pytest

from spacecraft.components import component_from_catalog
from spacecraft.geometry import (
    PRIMITIVES,
    layout_spacecraft,
    primitive,
)
from spacecraft.presets import load_spacecraft
from spacecraft.vehicle import Spacecraft
from ui.spacecraft_designer import DEFAULT_PRESET


@pytest.mark.parametrize("name", PRIMITIVES)
def test_primitives_are_valid_triangle_meshes(name):
    mesh = primitive(name)

    assert mesh.vertex_count > 0
    assert mesh.vertex_count % 3 == 0
    assert mesh.positions.shape == mesh.normals.shape
    assert np.all(np.isfinite(mesh.positions))
    lengths = np.linalg.norm(mesh.normals, axis=1)
    np.testing.assert_allclose(lengths, 1.0, atol=1e-4)
    assert mesh.interleaved().shape == (mesh.vertex_count, 6)


def test_cylinder_is_unit_sized_and_sits_on_y_zero():
    positions = primitive("cylinder").positions

    np.testing.assert_allclose(positions.min(axis=0), (-1, 0, -1), atol=1e-5)
    np.testing.assert_allclose(positions.max(axis=0), (1, 1, 1), atol=1e-5)


def test_empty_design_has_empty_layout():
    layout = layout_spacecraft(Spacecraft())

    assert layout.parts == []
    assert layout.height == 0.0
    assert layout_spacecraft(None).parts == []


def test_starter_design_layout_covers_every_component():
    craft = load_spacecraft(DEFAULT_PRESET)
    layout = layout_spacecraft(craft)

    assert layout.height > 0.0
    assert set(layout.component_ids()) == {c.id for c in craft.components}
    assert {part.primitive for part in layout.parts} <= set(PRIMITIVES)
    for part in layout.parts:
        assert part.model.shape == (4, 4)
        assert np.all(np.isfinite(part.model))


def test_tank_length_grows_with_capacity():
    def height(capacity):
        craft = Spacecraft()
        tank = component_from_catalog("fuel_tank")
        tank.capacity = capacity
        tank.fuel_mass = capacity
        craft.add_component(tank)
        return layout_spacecraft(craft).height

    assert height(80_000.0) > height(20_000.0)


def test_engine_cluster_spreads_wider_than_single_engine():
    def extent(count):
        craft = Spacecraft()
        for _ in range(count):
            craft.add_component(component_from_catalog("engine"))
        return layout_spacecraft(craft).extent

    assert extent(3) > extent(1)
    assert extent(7) > extent(3)


def test_explode_separates_sections():
    craft = load_spacecraft(DEFAULT_PRESET)

    assert layout_spacecraft(craft, explode=1.0).height > layout_spacecraft(craft).height


def test_solar_array_widens_with_generation():
    def extent(kw):
        craft = Spacecraft()
        craft.add_component(component_from_catalog("fuel_tank"))
        power = component_from_catalog("power_system")
        power.generation_kw = kw
        craft.add_component(power)
        return layout_spacecraft(craft).extent

    assert extent(20.0) > extent(1.2)
