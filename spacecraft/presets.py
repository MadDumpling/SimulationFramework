"""Versioned JSON persistence for spacecraft assemblies."""

import json
from pathlib import Path

from .components import component_from_dict, component_to_dict
from .vehicle import Spacecraft

SCHEMA_VERSION = 1


def save_spacecraft(spacecraft: Spacecraft, filepath: str | Path) -> None:
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": SCHEMA_VERSION,
        "name": spacecraft.name,
        "components": [
            component_to_dict(component) for component in spacecraft.components
        ],
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
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported spacecraft preset schema version: "
            f"{data.get('schema_version')}"
        )
    name = data.get("name")
    components_data = data.get("components")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Spacecraft preset must include a nonempty name")
    if not isinstance(components_data, list):
        raise ValueError("Spacecraft preset components must be a list")

    spacecraft = Spacecraft(name=name)
    for component_data in components_data:
        spacecraft.add_component(component_from_dict(component_data))
    return spacecraft
