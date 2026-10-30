"""Illustrative demonstration designs (not real hardware)."""

from .components import component_from_catalog
from .provenance import DataProvenance
from .vehicle import Spacecraft

LUNAR_DEMO_NOTE = (
    "Demonstration only: sized so the single-stage lunar screening passes (thrust-to-weight "
    "above 1 and enough ideal delta-v for the Earth ascent plus transfer). Tank and engine "
    "masses are far lighter than real hardware of this size, so this shows the pass window, "
    "not a flyable vehicle."
)


def build_lunar_demo() -> Spacecraft:
    """A design that clears the lunar-mission pre-screen and reaches the Moon."""
    craft = Spacecraft("Lunar-capable demo (illustrative)")

    engine = component_from_catalog("engine")
    engine.name = "Demo heavy engine"
    engine.thrust = 15_000_000.0
    engine.provenance = DataProvenance(quality="illustrative", notes=LUNAR_DEMO_NOTE)

    tank = component_from_catalog("fuel_tank")
    tank.name = "Demo heavy tank"
    tank.capacity = tank.fuel_mass = 400_000.0
    tank.provenance = DataProvenance(quality="illustrative", notes=LUNAR_DEMO_NOTE)

    for part in (engine, tank, component_from_catalog("payload"), component_from_catalog("power_system")):
        craft.add_component(part)
    return craft
