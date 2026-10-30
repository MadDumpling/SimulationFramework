"""Vehicle mass, centre of mass, and inertia from component data."""

from dataclasses import dataclass, field
import math

from .components import FuelTank
from .vehicle import Spacecraft


@dataclass
class MassProperties:
    mass: float = 0.0
    com_m: tuple[float, float, float] | None = None
    inertia_kgm2: tuple[float, float, float] | None = None
    # Component names lacking the data needed for the value that is None.
    missing_com: list[str] = field(default_factory=list)
    missing_inertia: list[str] = field(default_factory=list)


def mass_properties(spacecraft: Spacecraft, include_propellant: bool = True) -> MassProperties:
    """Aggregate mass properties; centre of mass/inertia are None if any part lacks data.

    Approximations: component inertias are principal values about their own
    centre of mass with axes aligned to the vehicle (products of inertia are
    ignored), and loaded propellant is a point mass at its tank's centre of
    mass (no slosh or fill-level shift). Explicit component placements transform
    each known COM from its automatic-layout position into the current assembly.
    """
    result = MassProperties()
    weighted = [0.0, 0.0, 0.0]
    entries = []  # (mass, com, inertia or None for point masses)
    if any(
        part.placement is not None and part.com_m is not None
        for part in spacecraft.components
    ):
        from .geometry import component_com_positions

        com_positions = component_com_positions(spacecraft)
    else:
        com_positions = {}

    for part in spacecraft.components:
        propellant = part.fuel_mass if include_propellant and isinstance(part, FuelTank) else 0.0
        mass = part.dry_mass + propellant
        result.mass += mass
        if mass == 0.0:
            continue
        com = com_positions.get(part.id, part.com_m)
        if com is None:
            result.missing_com.append(part.name)
            continue
        entries.append((part.dry_mass, com, part.inertia_kgm2, part.name))
        if propellant > 0.0:
            entries.append((propellant, com, (0.0, 0.0, 0.0), part.name))
        for axis in range(3):
            weighted[axis] += mass * com[axis]

    if result.missing_com or result.mass <= 0.0:
        return result
    com = tuple(w / result.mass for w in weighted)
    result.com_m = com

    inertia = [0.0, 0.0, 0.0]
    for mass, part_com, part_inertia, name in entries:
        if part_inertia is None:
            if mass > 0.0 and name not in result.missing_inertia:
                result.missing_inertia.append(name)
            continue
        dx, dy, dz = (part_com[i] - com[i] for i in range(3))
        inertia[0] += part_inertia[0] + mass * (dy * dy + dz * dz)
        inertia[1] += part_inertia[1] + mass * (dx * dx + dz * dz)
        inertia[2] += part_inertia[2] + mass * (dx * dx + dy * dy)
    if not result.missing_inertia:
        result.inertia_kgm2 = tuple(inertia)
    return result


def static_tip_over_angle_deg(spacecraft: Spacecraft) -> float | None:
    """Tilt at which the centre of mass passes over the footpad circle edge.

    Level, rigid ground; None if gear footprint, foot plane, or centre of mass
    is unknown. Uses the lateral COM offset, so an off-axis COM reduces margin
    in the worst-case direction.
    """
    gear = spacecraft.landing_gear
    if gear is None or gear.footprint_radius_m is None or gear.foot_plane_y_m is None:
        return None
    com = mass_properties(spacecraft).com_m
    if com is None:
        return None
    height = com[1] - gear.foot_plane_y_m
    if height <= 0.0:
        return 90.0
    lateral = math.hypot(com[0], com[2])
    radius = gear.footprint_radius_m
    # Worst direction tips toward the COM offset: stability radius is r - offset.
    margin = radius - lateral
    if margin <= 0.0:
        return 0.0
    return math.degrees(math.atan2(margin, height))
