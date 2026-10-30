"""3D layout of a spacecraft assembly for the configurator viewport.

Pure numpy and independent of any rendering backend. Every part is drawn as a
unit primitive mesh plus a model matrix, so layouts are cheap to rebuild on
each design edit. Units are metres with +Y up; the vehicle base sits at y=0.

Sizes are derived from component properties with illustrative densities and
scaling rules. The result is a readable visualization, not engineering CAD.
"""

import math
from dataclasses import dataclass, field, replace
from functools import cache

import numpy as np

from .components import (
    Avionics,
    Battery,
    Component,
    Engine,
    FuelTank,
    LandingLeg,
    Payload,
    PowerSystem,
    RcsThruster,
    SolarPanel,
)
from .mass_properties import mass_properties
from .transforms import (  # noqa: F401  (re-exported for existing callers)
    euler_xyz_degrees,
    rotate_x,
    rotate_y,
    rotate_z,
    rotation_between,
    scale,
    translate,
)
from .vehicle import Spacecraft

PROPELLANT_DENSITY = 1_000.0  # kg/m^3, bulk average used only for sizing
PAYLOAD_DENSITY = 250.0  # kg/m^3
SOLAR_POWER_DENSITY = 0.25  # kW/m^2 of array area

COMPONENT_COLORS = {
    Engine: (0.72, 0.38, 0.22),
    FuelTank: (0.78, 0.80, 0.84),
    Payload: (0.45, 0.62, 0.42),
    PowerSystem: (0.22, 0.30, 0.62),
    LandingLeg: (0.70, 0.72, 0.76),
    RcsThruster: (0.80, 0.48, 0.25),
    SolarPanel: (0.10, 0.42, 0.82),
    Battery: (0.36, 0.68, 0.45),
    Avionics: (0.66, 0.57, 0.36),
}
STRUCTURE_COLOR = (0.42, 0.45, 0.50)
SEAM_COLOR = (0.25, 0.27, 0.31)
GAUGE_COLOR = (0.25, 0.85, 0.95)
CHAMBER_COLOR = (0.30, 0.30, 0.33)


@dataclass(frozen=True)
class Mesh:
    """Non-indexed triangle list."""

    positions: np.ndarray  # (N, 3) float32
    normals: np.ndarray  # (N, 3) float32

    @property
    def vertex_count(self) -> int:
        return len(self.positions)

    def interleaved(self) -> np.ndarray:
        return np.ascontiguousarray(
            np.hstack([self.positions, self.normals]),
            dtype=np.float32,
        )


@dataclass(frozen=True)
class PartVisual:
    """One drawable piece of the vehicle; component_id is None for decoration."""

    component_id: str | None
    primitive: str
    model: np.ndarray
    color: tuple[float, float, float]


@dataclass
class VehicleLayout:
    parts: list[PartVisual] = field(default_factory=list)
    height: float = 0.0
    extent: float = 0.0  # max horizontal distance from the vehicle axis
    core_radius: float = 1.0
    frame_center: tuple[float, float, float] | None = None
    frame_radius: float | None = None

    @property
    def center(self) -> np.ndarray:
        return np.array([0.0, self.height / 2.0, 0.0], dtype=np.float32)

    @property
    def camera_center(self) -> np.ndarray:
        if self.frame_center is None:
            return self.center
        return np.asarray(self.frame_center, dtype=np.float32)

    @property
    def bounding_radius(self) -> float:
        if self.frame_radius is not None:
            return self.frame_radius
        return max(1.0, math.hypot(self.height / 2.0, self.extent))

    def component_ids(self) -> list[str]:
        seen = []
        for part in self.parts:
            if part.component_id is not None and part.component_id not in seen:
                seen.append(part.component_id)
        return seen


# ---------------------------------------------------------------------------
# Unit primitives
# ---------------------------------------------------------------------------


def lathe(profile, segments: int = 48, crease_degrees: float = 40.0) -> Mesh:
    """Revolve a (radius, height) profile around +Y.

    Normals are smoothed along the profile except across sharp creases, so
    cylinders keep hard cap edges while bells and domes shade smoothly.
    """
    points = np.asarray(profile, dtype=np.float64)
    tangents = np.diff(points, axis=0)
    seg_normals = np.stack([tangents[:, 1], -tangents[:, 0]], axis=1)
    seg_normals /= np.maximum(np.linalg.norm(seg_normals, axis=1, keepdims=True), 1e-12)

    crease = math.cos(math.radians(crease_degrees))
    start_normals = seg_normals.copy()
    end_normals = seg_normals.copy()
    for i in range(len(seg_normals) - 1):
        a, b = seg_normals[i], seg_normals[i + 1]
        if np.dot(a, b) >= crease:
            blended = a + b
            blended /= np.linalg.norm(blended)
            end_normals[i] = blended
            start_normals[i + 1] = blended

    theta = np.linspace(0.0, 2.0 * math.pi, segments + 1)
    cos_t, sin_t = np.cos(theta), np.sin(theta)

    def ring(radius, height):
        return np.stack([radius * cos_t, np.full_like(cos_t, height), radius * sin_t], axis=1)

    def ring_normal(normal):
        return np.stack([normal[0] * cos_t, np.full_like(cos_t, normal[1]), normal[0] * sin_t], axis=1)

    positions, normals = [], []
    for i in range(len(tangents)):
        p0, p1 = ring(*points[i]), ring(*points[i + 1])
        n0, n1 = ring_normal(start_normals[i]), ring_normal(end_normals[i])
        # Two triangles per quad: (p0[j], p0[j+1], p1[j+1]) and (p0[j], p1[j+1], p1[j]).
        positions.append(np.stack([p0[:-1], p0[1:], p1[1:], p0[:-1], p1[1:], p1[:-1]], axis=1))
        normals.append(np.stack([n0[:-1], n0[1:], n1[1:], n0[:-1], n1[1:], n1[:-1]], axis=1))

    return Mesh(
        np.concatenate(positions).reshape(-1, 3).astype(np.float32),
        np.concatenate(normals).reshape(-1, 3).astype(np.float32),
    )


def box() -> Mesh:
    """Unit cube centred on the origin."""
    faces = []
    for axis in range(3):
        for sign in (-1.0, 1.0):
            normal = np.zeros(3)
            normal[axis] = sign
            u_axis, v_axis = [a for a in range(3) if a != axis]
            corners = []
            for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                corner = np.zeros(3)
                corner[axis] = sign * 0.5
                corner[u_axis] = u * 0.5
                corner[v_axis] = v * 0.5
                corners.append(corner)
            for index in (0, 1, 2, 0, 2, 3):
                faces.append((corners[index], normal))
    positions = np.array([p for p, _ in faces], dtype=np.float32)
    normals = np.array([n for _, n in faces], dtype=np.float32)
    return Mesh(positions, normals)


def _nose_profile(steps: int = 20):
    profile = [(0.0, 0.0)]
    for i in range(steps + 1):
        y = i / steps
        profile.append(((1.0 - y) ** 0.7, y))
    return profile


def _bell_profile(steps: int = 16):
    # Exit (radius 1) at the bottom, throat (radius 0.32) at the top.
    return [(0.32 + 0.68 * (1.0 - i / steps) ** 1.8, i / steps) for i in range(steps + 1)]


def _sphere_profile(steps: int = 24):
    return [
        (math.sin(math.pi * i / steps), -math.cos(math.pi * i / steps))
        for i in range(steps + 1)
    ]


@cache
def primitive(name: str) -> Mesh:
    builders = {
        "cylinder": lambda: lathe([(0, 0), (1, 0), (1, 1), (0, 1)]),
        "nose": lambda: lathe(_nose_profile()),
        "bell": lambda: lathe(_bell_profile()),
        "box": box,
        "sphere": lambda: lathe(_sphere_profile()),
    }
    try:
        return builders[name]()
    except KeyError as error:
        raise ValueError(f"Unknown primitive: {name}") from error


PRIMITIVES = ("cylinder", "nose", "bell", "box", "sphere")
PRIMITIVE_BOUNDS = {
    "box": ((-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)),
    "cylinder": ((-1.0, 0.0, -1.0), (1.0, 1.0, 1.0)),
    "bell": ((-1.0, 0.0, -1.0), (1.0, 1.0, 1.0)),
    "nose": ((-1.0, 0.0, -1.0), (1.0, 1.0, 1.0)),
    "sphere": ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0)),
}


# ---------------------------------------------------------------------------
# Vehicle layout
# ---------------------------------------------------------------------------


def _cylinder(radius: float, y0: float, height: float) -> np.ndarray:
    return translate(0.0, y0, 0.0) @ scale(radius, height, radius)


def core_radius(spacecraft: Spacecraft) -> float:
    """Common stack radius, sized so the largest tank is roughly 3 diameters long."""
    volumes = [
        part.capacity / PROPELLANT_DENSITY
        for part in spacecraft.components
        if isinstance(part, FuelTank)
    ]
    if not volumes or max(volumes) <= 0.0:
        return 1.0
    return float(np.clip((max(volumes) / (6.0 * math.pi)) ** (1.0 / 3.0), 0.5, 5.0))


def engine_exit_radius(engine: Engine) -> float:
    return float(np.clip(0.16 * math.sqrt(engine.thrust / 1e5), 0.06, 3.0))


def _engine_positions(engines: list[Engine]) -> list[tuple[float, float]]:
    count = len(engines)
    if count == 1:
        return [(0.0, 0.0)]
    largest = max(engine_exit_radius(engine) for engine in engines)
    centre = count >= 7
    ring_count = count - 1 if centre else count
    ring_radius = (largest * 1.12) / math.sin(math.pi / ring_count)
    if centre:
        ring_radius = max(ring_radius, largest * 2.3)
    positions = [(0.0, 0.0)] if centre else []
    for index in range(ring_count):
        angle = 2.0 * math.pi * index / ring_count
        positions.append((ring_radius * math.cos(angle), ring_radius * math.sin(angle)))
    return positions


def layout_spacecraft(
    spacecraft: Spacecraft | None,
    explode: float = 0.0,
    include_analysis: bool = True,
) -> VehicleLayout:
    """Arrange components bottom-to-top: engines, tanks, power bus, payload, nose.

    ``explode`` in [0, 1] separates sections vertically for inspection.
    """
    layout = VehicleLayout()
    if spacecraft is None or not spacecraft.components:
        return layout

    components = spacecraft.components
    engines = [c for c in components if isinstance(c, Engine)]
    tanks = [c for c in components if isinstance(c, FuelTank)]
    power = [c for c in components if isinstance(c, PowerSystem)]
    landing_legs = [c for c in components if isinstance(c, LandingLeg)]
    rcs_clusters = [c for c in components if isinstance(c, RcsThruster)]
    solar_panels = [c for c in components if isinstance(c, SolarPanel)]
    batteries = [c for c in components if isinstance(c, Battery)]
    avionics = [c for c in components if isinstance(c, Avionics)]
    payloads = [c for c in components if isinstance(c, Payload)]
    others = [
        c for c in components
        if not isinstance(
            c,
            (
                Engine,
                FuelTank,
                PowerSystem,
                LandingLeg,
                RcsThruster,
                SolarPanel,
                Battery,
                Avionics,
                Payload,
            ),
        )
    ]

    radius = core_radius(spacecraft)
    layout.core_radius = radius
    gap = max(0.0, explode) * radius * 1.5
    parts = layout.parts
    extent = radius
    y = 0.0

    def add(component: Component | None, primitive_name: str, model, color=None):
        if color is None:
            color = COMPONENT_COLORS.get(type(component), STRUCTURE_COLOR)
        parts.append(
            PartVisual(
                component.id if component is not None else None,
                primitive_name,
                model.astype(np.float32),
                color,
            )
        )

    # Legacy designs without explicit placement retain the familiar automatic stack.
    # Once any parts have placement data, each placed component is rendered from
    # its resolved transform below, while unplaced parts remain auto-stacked.
    # Engines hang below a shared mount plane.
    if engines:
        mount = max(engine_exit_radius(e) * 2.6 for e in engines)
        for engine, (x, z) in zip(engines, _engine_positions(engines)):
            exit_radius = engine_exit_radius(engine)
            chamber = exit_radius * 0.6
            bell = exit_radius * 2.0
            top = mount
            add(engine, "cylinder",
                translate(x, top - chamber, z) @ scale(exit_radius * 0.42, chamber, exit_radius * 0.42),
                CHAMBER_COLOR)
            add(engine, "bell",
                translate(x, top - chamber - bell, z) @ scale(exit_radius, bell, exit_radius))
            extent = max(extent, math.hypot(x, z) + exit_radius)
        y = mount + gap
        thrust_structure = radius * 0.35
        add(None, "cylinder", _cylinder(radius, y, thrust_structure))
        y += thrust_structure + gap

    # Tanks share the core radius; length follows propellant volume.
    for tank in tanks:
        volume = tank.capacity / PROPELLANT_DENSITY
        length = float(np.clip(volume / (math.pi * radius**2), 0.3 * radius, 40.0))
        add(tank, "cylinder", _cylinder(radius, y, length))
        seam = radius * 0.06
        add(tank, "cylinder", _cylinder(radius * 1.015, y, seam), SEAM_COLOR)
        add(tank, "cylinder", _cylinder(radius * 1.015, y + length - seam, seam), SEAM_COLOR)
        fill = tank.fuel_mass / tank.capacity if tank.capacity > 0 else 0.0
        if fill > 0.0:
            gauge_height = max(length * fill - 2 * seam, 0.01)
            add(tank, "box",
                translate(radius * 1.01, y + seam + gauge_height / 2.0, 0.0)
                @ scale(radius * 0.05, gauge_height, radius * 0.18),
                GAUGE_COLOR)
        y += length + gap

    # Landing gear is rendered as one editable assembly with radial legs.
    for gear in landing_legs:
        body_y = max(y * 0.55, radius * 1.8)
        upper_radius = radius * 0.8
        lower_y = 0.08
        strut_radius = max(0.035, min(radius * 0.035, gear.footpad_radius_m * 0.2))
        for index in range(gear.leg_count):
            angle = 2.0 * math.pi * index / gear.leg_count
            radial_x, radial_z = math.cos(angle), math.sin(angle)
            upper = np.array((radial_x * upper_radius, body_y, radial_z * upper_radius))
            lower = np.array(
                (
                    radial_x * gear.footprint_radius_m,
                    lower_y,
                    radial_z * gear.footprint_radius_m,
                )
            )
            direction = upper - lower
            length = float(np.linalg.norm(direction))
            add(
                gear,
                "cylinder",
                translate(*lower)
                @ rotation_between((0.0, 1.0, 0.0), direction)
                @ scale(strut_radius, length, strut_radius),
            )
            add(
                gear,
                "box",
                rotate_y(angle)
                @ translate(
                    gear.footprint_radius_m,
                    lower_y,
                    0.0,
                )
                @ scale(
                    gear.footpad_radius_m * 2.0,
                    max(0.06, strut_radius * 2.0),
                    gear.footpad_radius_m * 1.2,
                ),
            )
            extent = max(extent, gear.footprint_radius_m + gear.footpad_radius_m)

    # Auxiliary thrusters are shown around the body but do not add main-engine thrust.
    for cluster in rcs_clusters:
        centre_y = max(y * 0.65, radius)
        pod_radius = max(0.08, min(radius * 0.12, 0.35))
        nozzle_radius = pod_radius * 0.35
        for index in range(cluster.thruster_count):
            angle = 2.0 * math.pi * index / cluster.thruster_count
            radial_x, radial_z = math.cos(angle), math.sin(angle)
            spin = rotate_y(angle)
            add(
                cluster,
                "box",
                translate(
                    radial_x * (radius + pod_radius * 0.35),
                    centre_y,
                    radial_z * (radius + pod_radius * 0.35),
                )
                @ scale(pod_radius * 0.45, pod_radius * 1.4, pod_radius * 0.45),
            )
            add(
                cluster,
                "bell",
                translate(
                    radial_x * (radius + pod_radius),
                    centre_y,
                    radial_z * (radius + pod_radius),
                )
                @ rotation_between((0.0, 1.0, 0.0), (radial_x, 0.0, radial_z))
                @ scale(nozzle_radius, nozzle_radius * 1.5, nozzle_radius),
            )
            extent = max(extent, radius + pod_radius * 2.0)

    # Power systems mount on an avionics bus with deployable wings.
    if power:
        bus_radius = radius * 0.9
        bus_height = max(0.6 * radius, 0.8)
        add(None, "cylinder", _cylinder(bus_radius, y, bus_height))
        for index, system in enumerate(power):
            angle = math.pi * index / len(power)
            spin = rotate_y(angle)
            mid = y + bus_height / 2.0
            if system.generation_kw > 0.0:
                area = system.generation_kw / SOLAR_POWER_DENSITY
                width = bus_height * 0.85
                length = float(np.clip((area / 2.0) / width, 0.3, 40.0))
                boom = radius * 0.35
                for side in (-1.0, 1.0):
                    boom_centre = side * (bus_radius + boom / 2.0)
                    wing_centre = side * (bus_radius + boom + length / 2.0)
                    add(system, "box",
                        spin @ translate(boom_centre, mid, 0.0) @ scale(boom, 0.06, 0.06),
                        STRUCTURE_COLOR)
                    add(system, "box",
                        spin @ translate(wing_centre, mid, 0.0) @ scale(length, width, 0.04))
                extent = max(extent, bus_radius + boom + length)
            else:
                size = float(np.clip(system.storage_kwh / 20.0, 0.2, bus_height * 0.8))
                add(system, "box",
                    spin @ translate(bus_radius + size / 2.0, mid, 0.0) @ scale(size, size, size))
        y += bus_height + gap

    # A solar array is sized from its declared deployed area.
    for panel in solar_panels:
        width = max(radius * 0.38, 0.45)
        length = max(panel.area_m2 / (2.0 * width), 0.35)
        boom = radius * 0.35
        mid = max(y * 0.5, radius * 1.5)
        for side in (-1.0, 1.0):
            add(
                panel,
                "box",
                translate(side * (radius + boom / 2.0), mid, 0.0)
                @ scale(boom, 0.055, 0.055),
                STRUCTURE_COLOR,
            )
            add(
                panel,
                "box",
                translate(side * (radius + boom + length / 2.0), mid, 0.0)
                @ scale(length, width, 0.035),
            )
        extent = max(extent, radius + boom + length)

    # Electrical storage and avionics boxes mount on opposite sides of the bus.
    for index, system in enumerate(batteries + avionics):
        size = float(
            np.clip(
                math.sqrt(max(system.dry_mass, 1.0) / 80.0) * radius * 0.32,
                0.2,
                radius * 0.75,
            )
        )
        centre_y = max(y * 0.58, radius * 1.4)
        side = 1.0 if index % 2 == 0 else -1.0
        add(
            system,
            "box",
            translate(side * (radius + size * 0.25), centre_y, index * size * 0.12)
            @ scale(size, size * 0.7, size * 0.8),
        )
        extent = max(extent, radius + size * 0.75)

    # Payloads and any unrecognised component types stack under the nose.
    for payload in payloads + others:
        payload_radius = radius * 0.85
        volume = payload.dry_mass / PAYLOAD_DENSITY
        height = float(np.clip(volume / (math.pi * payload_radius**2), 0.4 * radius, 6.0 * radius))
        add(None, "cylinder", _cylinder(payload_radius * 0.7, y, radius * 0.12))
        add(payload, "cylinder", _cylinder(payload_radius, y + radius * 0.12, height))
        y += radius * 0.12 + height + gap

    if tanks or power or solar_panels or batteries or avionics or payloads or others:
        nose = radius * 1.6
        add(None, "nose", _cylinder(radius, y, nose))
        y += nose

    layout.height = y
    layout.extent = extent

    default_centres = _component_default_centres(parts)
    placed = _placement_transforms(spacecraft, default_centres)
    if placed:
        layout.parts = [
            replace(
                part,
                model=(
                    placed[part.component_id]
                    @ translate(*(-default_centres[part.component_id]))
                    @ part.model
                ).astype(np.float32),
            )
            if part.component_id in placed
            else part
            for part in layout.parts
        ]
        parts = layout.parts

    if include_analysis:
        properties = mass_properties(spacecraft)
        if properties.com_m is not None:
            com_x, com_y, com_z = properties.com_m
            marker_radius = max(0.08, min(radius * 0.09, 0.35))
            parts.append(
                PartVisual(
                    None,
                    "sphere",
                    translate(com_x, com_y, com_z)
                    @ scale(marker_radius, marker_radius, marker_radius),
                    (1.0, 0.78, 0.12),
                )
            )

    if spacecraft.landing_gear is not None:
        footprint = spacecraft.landing_gear.footprint_radius_m
        if footprint is not None and footprint > 0.0:
            parts.append(
                PartVisual(
                    None,
                    "cylinder",
                    translate(0.0, 0.005, 0.0) @ scale(footprint, 0.005, footprint),
                    (0.18, 0.85, 0.38),
                )
            )
    layout.frame_center, layout.frame_radius = _visual_bounds(layout.parts)
    return layout


def _visual_bounds(parts: list[PartVisual]) -> tuple[tuple[float, float, float], float]:
    points = []
    for part in parts:
        low, high = PRIMITIVE_BOUNDS[part.primitive]
        corners = np.array(
            [
                (x, y, z, 1.0)
                for x in (low[0], high[0])
                for y in (low[1], high[1])
                for z in (low[2], high[2])
            ],
            dtype=np.float32,
        )
        points.append((part.model @ corners.T).T[:, :3])
    if not points:
        return (0.0, 0.0, 0.0), 1.0
    all_points = np.concatenate(points)
    low, high = all_points.min(axis=0), all_points.max(axis=0)
    centre = (low + high) / 2.0
    radius = float(np.max(np.linalg.norm(all_points - centre, axis=1)))
    return tuple(float(value) for value in centre), max(1.0, radius)


def _component_default_centres(parts: list[PartVisual]) -> dict[str, np.ndarray]:
    component_parts = {}
    for part in parts:
        if part.component_id is not None:
            component_parts.setdefault(part.component_id, []).append(part)

    centres = {}
    for component_id, visuals in component_parts.items():
        primary = [part for part in visuals if part.primitive != "box"] or visuals
        transformed = []
        for part in primary:
            low, high = PRIMITIVE_BOUNDS[part.primitive]
            corners = np.array(
                [
                    (x, y, z, 1.0)
                    for x in (low[0], high[0])
                    for y in (low[1], high[1])
                    for z in (low[2], high[2])
                ],
                dtype=np.float32,
            )
            transformed.append((part.model @ corners.T).T[:, :3])
        points = np.concatenate(transformed)
        centres[component_id] = (points.min(axis=0) + points.max(axis=0)) / 2.0
    return centres


def component_centers(spacecraft: Spacecraft) -> dict[str, np.ndarray]:
    """Return visual component centres in vehicle coordinates."""
    return _component_default_centres(layout_spacecraft(spacecraft).parts)


def _placement_transforms(
    spacecraft: Spacecraft,
    default_centres: dict[str, np.ndarray] | None = None,
) -> dict[str, np.ndarray]:
    """Resolve explicit part attachments to vehicle-frame transforms.

    Node positions are approximate envelopes from dimensions, with the current
    auto-layout model supplying a sensible default length when dimensions are
    missing. Root placements define a centre translation; attached placements
    snap the selected child node to the requested parent node, then apply offset
    and local Euler rotation.
    """
    placed_parts = {
        component.id: component
        for component in spacecraft.components
        if component.placement is not None
    }
    if not placed_parts:
        return {}

    if default_centres is None:
        defaults = layout_spacecraft(
            _without_placements(spacecraft),
            explode=0.0,
            include_analysis=False,
        )
        default_centres = _component_default_centres(defaults.parts)

    transforms: dict[str, np.ndarray] = {}
    visiting: set[str] = set()

    def resolve(component_id: str) -> np.ndarray:
        if component_id in transforms:
            return transforms[component_id]
        if component_id in visiting:
            raise ValueError("cycle detected in component placement tree")
        component = placed_parts[component_id]
        placement = component.placement
        assert placement is not None
        visiting.add(component_id)
        local_rotation = euler_xyz_degrees(*placement.rotation_deg)

        if placement.parent_id is None:
            result = translate(*placement.offset) @ local_rotation
        else:
            parent = spacecraft.get_component(placement.parent_id)
            if parent is None:
                raise ValueError(
                    f"placement for {component.name} references missing parent "
                    f"{placement.parent_id}"
                )
            parent_transform = (
                resolve(parent.id)
                if parent.id in placed_parts
                else translate(*default_centres.get(parent.id, np.zeros(3)))
            )
            parent_node = _node_local(parent, placement.parent_node)
            child_node = _node_local(component, placement.node)
            angle = np.deg2rad(placement.angle_deg)
            radial_rotation = rotate_y(angle)
            target = parent_transform @ (
                translate(*parent_node)
                @ radial_rotation
                @ translate(*placement.offset)
            )
            result = target @ local_rotation @ translate(*(-child_node))

        visiting.remove(component_id)
        transforms[component_id] = result.astype(np.float32)
        return transforms[component_id]

    for component_id in placed_parts:
        resolve(component_id)
    return transforms


def component_com_positions(spacecraft: Spacecraft) -> dict[str, tuple[float, float, float]]:
    """Return known component COM points after applying explicit placements."""
    known = {
        component.id: component.com_m
        for component in spacecraft.components
        if component.com_m is not None
    }
    if not known or not any(
        component.placement is not None
        for component in spacecraft.components
        if component.id in known
    ):
        return known

    defaults = layout_spacecraft(
        _without_placements(spacecraft),
        explode=0.0,
        include_analysis=False,
    )
    default_centres = _component_default_centres(defaults.parts)
    transforms = _placement_transforms(spacecraft, default_centres)
    positions = {}
    for component_id, com_m in known.items():
        transform = transforms.get(component_id)
        if transform is None:
            positions[component_id] = com_m
            continue
        relative = np.asarray(com_m) - default_centres[component_id]
        position = transform @ np.array((*relative, 1.0), dtype=np.float32)
        positions[component_id] = tuple(float(value) for value in position[:3])
    return positions


def _without_placements(spacecraft: Spacecraft) -> Spacecraft:
    """Build a temporary automatic-layout assembly without recursive placements."""
    from copy import copy

    clone = copy(spacecraft)
    clone.components = []
    for component in spacecraft.components:
        duplicate = copy(component)
        duplicate.placement = None
        clone.components.append(duplicate)
    return clone


def _node_local(component: Component, node: str):
    length = (
        component.dimensions_m[0]
        if component.dimensions_m is not None
        else _fallback_component_length(component)
    )
    if node == "top":
        return np.array([0.0, length / 2.0, 0.0])
    if node == "bottom":
        return np.array([0.0, -length / 2.0, 0.0])
    if node == "side":
        return np.array([core_radius_for(component), 0.0, 0.0])
    if node == "mount":
        return np.zeros(3)
    raise ValueError(f"Unsupported attachment node: {node}")


def _fallback_component_length(component: Component) -> float:
    if isinstance(component, FuelTank):
        radius = core_radius_for(component)
        volume = component.capacity / PROPELLANT_DENSITY
        return float(np.clip(volume / (math.pi * radius**2), 0.3 * radius, 40.0))
    if isinstance(component, Engine):
        return engine_exit_radius(component) * 2.6
    if isinstance(component, LandingLeg):
        return component.leg_length_m
    if isinstance(component, SolarPanel):
        return math.sqrt(component.area_m2)
    if isinstance(component, (RcsThruster, Battery, Avionics)):
        return float(np.clip(component.dry_mass**0.5 * 0.1, 0.2, 4.0))
    radius = core_radius_for(component)
    volume = component.dry_mass / PAYLOAD_DENSITY
    return float(np.clip(volume / (math.pi * radius**2), 0.4 * radius, 6.0 * radius))


def core_radius_for(component: Component) -> float:
    if isinstance(component, FuelTank) and component.capacity > 0.0:
        return float(np.clip((component.capacity / PROPELLANT_DENSITY / (6.0 * math.pi)) ** (1.0 / 3.0), 0.5, 5.0))
    if component.dimensions_m is not None:
        return component.dimensions_m[1] / 2.0
    return 0.5
