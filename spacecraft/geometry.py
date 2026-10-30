"""3D layout of a spacecraft assembly for the configurator viewport.

Pure numpy and independent of any rendering backend. Every part is drawn as a
unit primitive mesh plus a model matrix, so layouts are cheap to rebuild on
each design edit. Units are metres with +Y up; the vehicle base sits at y=0.

Sizes are derived from component properties with illustrative densities and
scaling rules. The result is a readable visualization, not engineering CAD.
"""

from dataclasses import dataclass, field
from functools import cache
import math

import numpy as np

from .components import Component, Engine, FuelTank, Payload, PowerSystem
from .vehicle import Spacecraft

PROPELLANT_DENSITY = 1_000.0  # kg/m^3, bulk average used only for sizing
PAYLOAD_DENSITY = 250.0  # kg/m^3
SOLAR_POWER_DENSITY = 0.25  # kW/m^2 of array area

COMPONENT_COLORS = {
    Engine: (0.72, 0.38, 0.22),
    FuelTank: (0.78, 0.80, 0.84),
    Payload: (0.45, 0.62, 0.42),
    PowerSystem: (0.22, 0.30, 0.62),
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

    @property
    def center(self) -> np.ndarray:
        return np.array([0.0, self.height / 2.0, 0.0], dtype=np.float32)

    @property
    def bounding_radius(self) -> float:
        return max(1.0, math.hypot(self.height / 2.0, self.extent))

    def component_ids(self) -> list[str]:
        seen = []
        for part in self.parts:
            if part.component_id is not None and part.component_id not in seen:
                seen.append(part.component_id)
        return seen


# ---------------------------------------------------------------------------
# Matrices (row-major, column vectors: p' = M @ p)
# ---------------------------------------------------------------------------


def translate(x: float, y: float, z: float) -> np.ndarray:
    matrix = np.eye(4, dtype=np.float32)
    matrix[:3, 3] = (x, y, z)
    return matrix


def scale(x: float, y: float, z: float) -> np.ndarray:
    return np.diag([x, y, z, 1.0]).astype(np.float32)


def rotate_y(angle: float) -> np.ndarray:
    c, s = math.cos(angle), math.sin(angle)
    matrix = np.eye(4, dtype=np.float32)
    matrix[0, 0], matrix[0, 2] = c, s
    matrix[2, 0], matrix[2, 2] = -s, c
    return matrix


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


@cache
def primitive(name: str) -> Mesh:
    builders = {
        "cylinder": lambda: lathe([(0, 0), (1, 0), (1, 1), (0, 1)]),
        "nose": lambda: lathe(_nose_profile()),
        "bell": lambda: lathe(_bell_profile()),
        "box": box,
    }
    try:
        return builders[name]()
    except KeyError as error:
        raise ValueError(f"Unknown primitive: {name}") from error


PRIMITIVES = ("cylinder", "nose", "bell", "box")


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
    payloads = [c for c in components if isinstance(c, Payload)]
    others = [
        c for c in components
        if not isinstance(c, (Engine, FuelTank, PowerSystem, Payload))
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

    # Payloads and any unrecognised component types stack under the nose.
    for payload in payloads + others:
        payload_radius = radius * 0.85
        volume = payload.dry_mass / PAYLOAD_DENSITY
        height = float(np.clip(volume / (math.pi * payload_radius**2), 0.4 * radius, 6.0 * radius))
        add(None, "cylinder", _cylinder(payload_radius * 0.7, y, radius * 0.12))
        add(payload, "cylinder", _cylinder(payload_radius, y + radius * 0.12, height))
        y += radius * 0.12 + height + gap

    if tanks or power or payloads or others:
        nose = radius * 1.6
        add(None, "nose", _cylinder(radius, y, nose))
        y += nose

    layout.height = y
    layout.extent = extent
    return layout
