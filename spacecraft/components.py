"""Typed spacecraft parts and a small editable demonstration catalog."""

from dataclasses import dataclass, field
import math
from uuid import uuid4


def _require_nonnegative(field_name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{field_name} must be a finite nonnegative number")


def _require_positive(field_name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{field_name} must be a finite positive number")


@dataclass(kw_only=True)
class Component:
    name: str
    dry_mass: float
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name must not be empty")
        _require_nonnegative("dry_mass", self.dry_mass)


@dataclass(kw_only=True)
class Engine(Component):
    thrust: float
    isp: float
    fuel_type: str
    power_draw_kw: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_positive("thrust", self.thrust)
        _require_positive("isp", self.isp)
        _require_nonnegative("power_draw_kw", self.power_draw_kw)
        if not self.fuel_type.strip():
            raise ValueError("fuel_type must not be empty")


@dataclass(kw_only=True)
class FuelTank(Component):
    capacity: float
    fuel_mass: float
    fuel_type: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_nonnegative("capacity", self.capacity)
        _require_nonnegative("fuel_mass", self.fuel_mass)
        if self.fuel_mass > self.capacity:
            raise ValueError("fuel_mass cannot exceed tank capacity")
        if not self.fuel_type.strip():
            raise ValueError("fuel_type must not be empty")


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


_COMPONENT_TYPES = {
    "Engine": Engine,
    "FuelTank": FuelTank,
    "Payload": Payload,
    "PowerSystem": PowerSystem,
}

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
}


def component_from_catalog(catalog_id: str) -> Component:
    """Create a fresh component from the editable demonstration catalog."""
    try:
        component_type = catalog_id
        values = _CATALOG[catalog_id].copy()
    except KeyError as error:
        raise ValueError(f"Unknown component catalog id: {catalog_id}") from error
    component_class = {
        "engine": Engine,
        "fuel_tank": FuelTank,
        "payload": Payload,
        "power_system": PowerSystem,
    }[component_type]
    return component_class(**values)


def component_to_dict(component: Component) -> dict:
    """Convert a supported component into its JSON-serializable representation."""
    result = {"type": type(component).__name__}
    for key, value in vars(component).items():
        result[key] = value
    return result


def component_from_dict(data: dict) -> Component:
    """Recreate and validate a component from a preset dictionary."""
    if not isinstance(data, dict):
        raise ValueError("Each component preset entry must be an object")
    type_name = data.get("type")
    component_class = _COMPONENT_TYPES.get(type_name)
    if component_class is None:
        raise ValueError(f"Unknown component type: {type_name}")
    values = {key: value for key, value in data.items() if key != "type"}
    try:
        return component_class(**values)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid {type_name} component: {error}") from error
