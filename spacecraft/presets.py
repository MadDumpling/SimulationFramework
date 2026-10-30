"""Versioned JSON persistence for spacecraft assemblies."""

import json
from pathlib import Path

from .appearance import SpacecraftAppearance
from .components import (
    component_from_dict,
    component_to_dict,
    dataclass_from_dict,
    dataclass_to_dict,
)
from .provenance import DataProvenance
from .vehicle import AttitudeLimits, LandingGear, Spacecraft

# v2 adds editor layout plus vehicle revision/provenance, landing gear, attitude
# limits, and per-component provenance, propulsion envelope, and mass-property
# fields. v1 files load unchanged: every new field defaults to unknown/illustrative.
SCHEMA_VERSION = 2


def save_spacecraft(spacecraft: Spacecraft, filepath: str | Path) -> None:
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": SCHEMA_VERSION,
        "name": spacecraft.name,
        "revision": spacecraft.revision,
        "provenance": dataclass_to_dict(spacecraft.provenance),
        "landing_gear": (
            dataclass_to_dict(spacecraft.landing_gear)
            if spacecraft.landing_gear is not None
            else None
        ),
        "attitude_limits": (
            dataclass_to_dict(spacecraft.attitude_limits)
            if spacecraft.attitude_limits is not None
            else None
        ),
        "appearance": dataclass_to_dict(spacecraft.appearance),
        "components": [
            component_to_dict(component) for component in spacecraft.components
        ],
        "layout": {
            component_id: [float(position[0]), float(position[1])]
            for component_id, position in spacecraft.layout.items()
        },
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_spacecraft(filepath: str | Path) -> Spacecraft:
    path = Path(filepath)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read spacecraft preset: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("Spacecraft preset must be a JSON object")
    schema_version = data.get("schema_version")
    if schema_version not in (1, SCHEMA_VERSION):
        raise ValueError(
            f"Unsupported spacecraft preset schema version: "
            f"{schema_version}"
        )
    name = data.get("name")
    components_data = data.get("components")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Spacecraft preset must include a nonempty name")
    if not isinstance(components_data, list):
        raise ValueError("Spacecraft preset components must be a list")

    revision = data.get("revision", "")
    if not isinstance(revision, str):
        raise ValueError("Spacecraft preset revision must be a string")
    optional = {}
    for key, cls in (
        ("provenance", DataProvenance),
        ("landing_gear", LandingGear),
        ("attitude_limits", AttitudeLimits),
        ("appearance", SpacecraftAppearance),
    ):
        if data.get(key) is not None:
            optional[key] = dataclass_from_dict(cls, data[key])

    spacecraft = Spacecraft(name=name, revision=revision, **optional)
    for component_data in components_data:
        spacecraft.add_component(component_from_dict(component_data))

    layout_data = data.get("layout", {}) if schema_version >= 2 else {}
    if not isinstance(layout_data, dict):
        raise ValueError("Spacecraft preset layout must be an object")
    component_ids = {component.id for component in spacecraft.components}
    for component_id, position in layout_data.items():
        if component_id not in component_ids:
            raise ValueError(f"Layout refers to unknown component id: {component_id}")
        if (
            not isinstance(position, list)
            or len(position) != 2
            or any(not isinstance(value, (int, float)) for value in position)
        ):
            raise ValueError(f"Invalid layout position for component: {component_id}")
        x, y = float(position[0]), float(position[1])
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            raise ValueError(f"Layout position must be within [0, 1]: {component_id}")
        spacecraft.layout[component_id] = (x, y)
    return spacecraft
