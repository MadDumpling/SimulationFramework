"""Typed spacecraft parts with traceable data, plus a small illustrative catalog.

Optional fields default to ``None``, meaning *unknown*. Unknowns are surfaced by
``spacecraft.readiness`` rather than silently treated as zero or as a default.
Vehicle axes: +Y is the long axis (base at y=0); X and Z are lateral.
"""

from dataclasses import dataclass, field, fields, is_dataclass
import math
from uuid import uuid4

from .propulsion import (
    SEA_LEVEL_PRESSURE,
    STANDARD_GRAVITY,
    Gimbal,
    IgnitionLimits,
    ThrottleSpec,
)
from .provenance import DataProvenance, MissingDataError
from .placement import Placement


def _require_nonnegative(field_name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{field_name} must be a finite nonnegative number")


def _require_positive(field_name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{field_name} must be a finite positive number")


def _optional_positive(field_name: str, value: float | None) -> None:
    if value is not None:
        _require_positive(field_name, value)


def _tuple_or_none(field_name: str, value, length: int, positive: bool) -> tuple | None:
    if value is None:
        return None
    try:
        result = tuple(float(v) for v in value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be {length} numbers") from error
    if len(result) != length or not all(math.isfinite(v) for v in result):
        raise ValueError(f"{field_name} must be {length} finite numbers")
    if positive and not all(v > 0.0 for v in result):
        raise ValueError(f"{field_name} values must be positive")
    return result


@dataclass(kw_only=True)
class Component:
    name: str
    dry_mass: float
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    stage: int = 1
    provenance: DataProvenance = field(default_factory=DataProvenance)
    # Centre of mass in vehicle axes (m) and principal inertia about it (kg m^2).
    com_m: tuple[float, float, float] | None = None
    inertia_kgm2: tuple[float, float, float] | None = None
    # Envelope as (length along +Y, diameter), metres.
    dimensions_m: tuple[float, float] | None = None
    # Optional attachment transform. None preserves legacy automatic stacking.
    placement: Placement | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name must not be empty")
        _require_nonnegative("dry_mass", self.dry_mass)
        if not isinstance(self.stage, int) or isinstance(self.stage, bool) or self.stage < 1:
            raise ValueError("stage must be an integer of at least 1")
        self.com_m = _tuple_or_none("com_m", self.com_m, 3, positive=False)
        self.inertia_kgm2 = _tuple_or_none("inertia_kgm2", self.inertia_kgm2, 3, positive=True)
        self.dimensions_m = _tuple_or_none("dimensions_m", self.dimensions_m, 2, positive=True)


@dataclass(kw_only=True)
class Engine(Component):
    """Rated vacuum performance plus the data to evaluate off-nominal operation.

    ``thrust`` and ``isp`` are vacuum values at the rated (throttle 1.0) point.
    """

    thrust: float
    isp: float
    fuel_type: str
    power_draw_kw: float = 0.0
    sea_level_thrust: float | None = None
    chamber_pressure_pa: float | None = None
    exit_area_m2: float | None = None
    throttle: ThrottleSpec = field(default_factory=ThrottleSpec)
    ignition: IgnitionLimits = field(default_factory=IgnitionLimits)
    gimbal: Gimbal = field(default_factory=Gimbal)

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_positive("thrust", self.thrust)
        _require_positive("isp", self.isp)
        _require_nonnegative("power_draw_kw", self.power_draw_kw)
        if not self.fuel_type.strip():
            raise ValueError("fuel_type must not be empty")
        _optional_positive("sea_level_thrust", self.sea_level_thrust)
        _optional_positive("chamber_pressure_pa", self.chamber_pressure_pa)
        _optional_positive("exit_area_m2", self.exit_area_m2)
        if self.sea_level_thrust is not None and self.sea_level_thrust > self.thrust:
            raise ValueError("sea_level_thrust cannot exceed vacuum thrust")

    # -- operating model ----------------------------------------------------

    @property
    def rated_mass_flow(self) -> float:
        return self.thrust / (self.isp * STANDARD_GRAVITY)

    def effective_exit_area(self) -> float | None:
        """Nozzle exit area, from the stated value or the vac/sea-level thrust gap."""
        if self.exit_area_m2 is not None:
            return self.exit_area_m2
        if self.sea_level_thrust is not None:
            return (self.thrust - self.sea_level_thrust) / SEA_LEVEL_PRESSURE
        return None

    def mass_flow_at(self, throttle: float = 1.0) -> float:
        """Propellant flow (kg/s); independent of ambient pressure (choked nozzle)."""
        mass_flow_fraction, _ = self.throttle.response(throttle)
        return self.rated_mass_flow * mass_flow_fraction

    def vacuum_thrust_at(self, throttle: float = 1.0) -> float:
        mass_flow_fraction, isp_fraction = self.throttle.response(throttle)
        return self.thrust * mass_flow_fraction * isp_fraction

    def thrust_at(self, throttle: float = 1.0, ambient_pressure_pa: float = 0.0) -> float:
        """Thrust (N) at a throttle setting and ambient pressure: F = F_vac - p_a * A_e."""
        _require_nonnegative("ambient_pressure_pa", ambient_pressure_pa)
        vacuum = self.vacuum_thrust_at(throttle)
        if ambient_pressure_pa == 0.0 or vacuum == 0.0:
            return vacuum
        area = self.effective_exit_area()
        if area is None:
            raise MissingDataError(
                "exit_area_m2 (or sea_level_thrust) is needed to correct thrust for ambient pressure"
            )
        return max(vacuum - ambient_pressure_pa * area, 0.0)

    def isp_at(self, throttle: float = 1.0, ambient_pressure_pa: float = 0.0) -> float:
        flow = self.mass_flow_at(throttle)
        if flow == 0.0:
            return 0.0
        return self.thrust_at(throttle, ambient_pressure_pa) / (flow * STANDARD_GRAVITY)

    def chamber_pressure_at(self, throttle: float = 1.0) -> float:
        """Chamber pressure (Pa); scales with mass flow for a choked nozzle (constant c*)."""
        if self.chamber_pressure_pa is None:
            raise MissingDataError("chamber_pressure_pa is unknown")
        mass_flow_fraction, _ = self.throttle.response(throttle)
        return self.chamber_pressure_pa * mass_flow_fraction


@dataclass(kw_only=True)
class FuelTank(Component):
    capacity: float
    fuel_mass: float
    fuel_type: str
    # Loaded propellant that cannot be burned (trapped/residual). None = unknown.
    residual_propellant: float | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_nonnegative("capacity", self.capacity)
        _require_nonnegative("fuel_mass", self.fuel_mass)
        if self.fuel_mass > self.capacity:
            raise ValueError("fuel_mass cannot exceed tank capacity")
        if not self.fuel_type.strip():
            raise ValueError("fuel_type must not be empty")
        if self.residual_propellant is not None:
            _require_nonnegative("residual_propellant", self.residual_propellant)

    @property
    def usable_propellant(self) -> float:
        """Burnable propellant; unknown residual is treated as zero (and flagged)."""
        return max(self.fuel_mass - (self.residual_propellant or 0.0), 0.0)


@dataclass(kw_only=True)
class Payload(Component):
    pass


@dataclass(kw_only=True)
class PowerSystem(Component):
    generation_kw: float = 0.0
    storage_kwh: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_nonnegative("generation_kw", self.generation_kw)
        _require_nonnegative("storage_kwh", self.storage_kwh)


@dataclass(kw_only=True)
class LandingLeg(Component):
    """Illustrative multi-leg landing-gear assembly and visual envelope."""

    leg_count: int = 4
    leg_length_m: float = 2.0
    footprint_radius_m: float = 2.5
    footpad_radius_m: float = 0.3
    rated_load_n: float | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if (
            not isinstance(self.leg_count, int)
            or isinstance(self.leg_count, bool)
            or not 3 <= self.leg_count <= 12
        ):
            raise ValueError("leg_count must be an integer from 3 to 12")
        _require_positive("leg_length_m", self.leg_length_m)
        _require_positive("footprint_radius_m", self.footprint_radius_m)
        _require_positive("footpad_radius_m", self.footpad_radius_m)
        _optional_positive("rated_load_n", self.rated_load_n)


@dataclass(kw_only=True)
class RcsThruster(Component):
    """Auxiliary reaction-control thruster cluster; not a launch engine."""

    thrust_n: float
    isp_s: float
    propellant_type: str
    thruster_count: int = 4
    minimum_impulse_bit_ns: float | None = None
    power_draw_kw: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_positive("thrust_n", self.thrust_n)
        _require_positive("isp_s", self.isp_s)
        if not self.propellant_type.strip():
            raise ValueError("propellant_type must not be empty")
        if (
            not isinstance(self.thruster_count, int)
            or isinstance(self.thruster_count, bool)
            or not 1 <= self.thruster_count <= 32
        ):
            raise ValueError("thruster_count must be an integer from 1 to 32")
        _optional_positive("minimum_impulse_bit_ns", self.minimum_impulse_bit_ns)
        _require_nonnegative("power_draw_kw", self.power_draw_kw)


@dataclass(kw_only=True)
class SolarPanel(Component):
    """Deployable array with rated power at its documented reference conditions."""

    area_m2: float
    generation_kw: float

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_positive("area_m2", self.area_m2)
        _require_nonnegative("generation_kw", self.generation_kw)


@dataclass(kw_only=True)
class Battery(Component):
    """Electrical energy storage; discharge power and capacity are separate limits."""

    capacity_kwh: float
    max_charge_kw: float = 0.0
    max_discharge_kw: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_nonnegative("capacity_kwh", self.capacity_kwh)
        _require_nonnegative("max_charge_kw", self.max_charge_kw)
        _require_nonnegative("max_discharge_kw", self.max_discharge_kw)


@dataclass(kw_only=True)
class Avionics(Component):
    """Vehicle guidance, navigation, and control electronics electrical load."""

    power_draw_kw: float
    redundancy: int = 1

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_nonnegative("power_draw_kw", self.power_draw_kw)
        if (
            not isinstance(self.redundancy, int)
            or isinstance(self.redundancy, bool)
            or self.redundancy < 1
        ):
            raise ValueError("redundancy must be an integer of at least 1")


_COMPONENT_TYPES = {
    "Engine": Engine,
    "FuelTank": FuelTank,
    "Payload": Payload,
    "PowerSystem": PowerSystem,
    "LandingLeg": LandingLeg,
    "RcsThruster": RcsThruster,
    "SolarPanel": SolarPanel,
    "Battery": Battery,
    "Avionics": Avionics,
}

# Nested dataclass fields that need rebuilding from JSON objects.
_NESTED_TYPES = {
    "provenance": DataProvenance,
    "throttle": ThrottleSpec,
    "ignition": IgnitionLimits,
    "gimbal": Gimbal,
    "placement": Placement,
}

_ILLUSTRATIVE_NOTE = (
    "Illustrative placeholder values, not real flight hardware data."
)

# Demonstration values are editable and are not certified flight-performance data.
_CATALOG = {
    "engine": {
        "name": "Demo kerolox engine",
        "dry_mass": 500.0,
        "thrust": 845_000.0,
        "isp": 300.0,
        "fuel_type": "LOX/RP-1",
        "power_draw_kw": 0.0,
        "description": "Illustrative sea-level chemical engine parameters.",
    },
    "fuel_tank": {
        "name": "Demo LOX/RP-1 tank",
        "dry_mass": 2_500.0,
        "capacity": 40_000.0,
        "fuel_mass": 40_000.0,
        "fuel_type": "LOX/RP-1",
        "description": "Illustrative tank; fuel mass is user-configurable.",
    },
    "payload": {
        "name": "Demo payload",
        "dry_mass": 1_000.0,
        "description": "Illustrative payload mass.",
    },
    "power_system": {
        "name": "Demo solar array",
        "dry_mass": 80.0,
        "generation_kw": 1.2,
        "storage_kwh": 5.0,
        "description": "Illustrative power-system parameters.",
    },
    "landing_leg": {
        "name": "Demo landing gear",
        "dry_mass": 180.0,
        "leg_count": 4,
        "leg_length_m": 2.0,
        "footprint_radius_m": 2.5,
        "footpad_radius_m": 0.3,
        "description": "Illustrative landing-leg structure; no contact simulation.",
    },
    "rcs_thruster": {
        "name": "Demo RCS cluster",
        "dry_mass": 24.0,
        "thrust_n": 450.0,
        "isp_s": 220.0,
        "propellant_type": "monomethylhydrazine / nitrogen tetroxide",
        "thruster_count": 4,
        "minimum_impulse_bit_ns": 10.0,
        "description": "Illustrative attitude-control thrusters; propellant use is not simulated.",
    },
    "solar_panel": {
        "name": "Demo solar array",
        "dry_mass": 45.0,
        "area_m2": 12.0,
        "generation_kw": 2.4,
        "description": "Illustrative rated output; illumination and pointing are not simulated.",
    },
    "battery": {
        "name": "Demo battery",
        "dry_mass": 35.0,
        "capacity_kwh": 8.0,
        "max_charge_kw": 2.0,
        "max_discharge_kw": 3.0,
        "description": "Illustrative electrical storage; charge state is not simulated.",
    },
    "avionics": {
        "name": "Demo avionics",
        "dry_mass": 18.0,
        "power_draw_kw": 0.35,
        "redundancy": 2,
        "description": "Illustrative guidance, navigation, and control electronics.",
    },
}


def component_from_catalog(catalog_id: str) -> Component:
    """Create a fresh component from the editable demonstration catalog."""
    try:
        values = _CATALOG[catalog_id].copy()
    except KeyError as error:
        raise ValueError(f"Unknown component catalog id: {catalog_id}") from error
    component_class = {
        "engine": Engine,
        "fuel_tank": FuelTank,
        "payload": Payload,
        "power_system": PowerSystem,
        "landing_leg": LandingLeg,
        "rcs_thruster": RcsThruster,
        "solar_panel": SolarPanel,
        "battery": Battery,
        "avionics": Avionics,
    }[catalog_id]
    return component_class(
        provenance=DataProvenance(quality="illustrative", notes=_ILLUSTRATIVE_NOTE),
        **values,
    )


def dataclass_to_dict(value) -> dict:
    """Shallow-recursive dataclass to JSON-ready dict (tuples become lists)."""
    result = {}
    for item in fields(value):
        attribute = getattr(value, item.name)
        if is_dataclass(attribute):
            attribute = dataclass_to_dict(attribute)
        elif isinstance(attribute, tuple):
            attribute = [list(row) if isinstance(row, tuple) else row for row in attribute]
        result[item.name] = attribute
    return result


def dataclass_from_dict(cls, data):
    """Build ``cls`` from a JSON object, rejecting non-objects and unknown keys."""
    if not isinstance(data, dict):
        raise ValueError(f"{cls.__name__} data must be an object")
    try:
        return cls(**data)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid {cls.__name__}: {error}") from error


def component_to_dict(component: Component) -> dict:
    """Convert a supported component into its JSON-serializable representation."""
    return {"type": type(component).__name__, **dataclass_to_dict(component)}


def component_from_dict(data: dict) -> Component:
    """Recreate and validate a component from a preset dictionary."""
    if not isinstance(data, dict):
        raise ValueError("Each component preset entry must be an object")
    type_name = data.get("type")
    component_class = _COMPONENT_TYPES.get(type_name)
    if component_class is None:
        raise ValueError(f"Unknown component type: {type_name}")
    values = {key: value for key, value in data.items() if key != "type"}
    for key, nested_class in _NESTED_TYPES.items():
        if key in values:
            if values[key] is None:
                del values[key]  # fall back to the default (all-unknown) record
            else:
                values[key] = dataclass_from_dict(nested_class, values[key])
    try:
        return component_class(**values)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid {type_name} component: {error}") from error
