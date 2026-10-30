"""Spacecraft assembly model, intentionally independent of the UI framework."""

from dataclasses import dataclass, field
import math

from .components import Component
from .provenance import DataProvenance


def _optional_nonnegative(name: str, value: float | None) -> None:
    if value is not None and (not math.isfinite(value) or value < 0.0):
        raise ValueError(f"{name} must be a finite nonnegative number")


@dataclass
class LandingGear:
    """Contact envelope for touchdown checks. ``None`` fields are unknown.

    ``foot_plane_y_m`` is the footpad plane on the vehicle +Y axis (the vehicle
    base is y=0, so feet below the base are negative). The ``rated_*`` speeds
    are the gear's structural capability, not mission touchdown requirements.
    """

    leg_count: int | None = None
    footprint_radius_m: float | None = None
    foot_plane_y_m: float | None = None
    engine_clearance_m: float | None = None
    rated_vertical_speed_mps: float | None = None
    rated_horizontal_speed_mps: float | None = None

    def __post_init__(self) -> None:
        if self.leg_count is not None and self.leg_count < 3:
            raise ValueError("a landing gear needs at least 3 legs for static stability")
        for name in (
            "footprint_radius_m",
            "engine_clearance_m",
            "rated_vertical_speed_mps",
            "rated_horizontal_speed_mps",
        ):
            _optional_nonnegative(name, getattr(self, name))
        if self.foot_plane_y_m is not None and not math.isfinite(self.foot_plane_y_m):
            raise ValueError("foot_plane_y_m must be finite")


@dataclass
class AttitudeLimits:
    """Allowable vehicle attitude and angular rate (structural/control limits)."""

    max_tilt_deg: float | None = None
    max_rate_dps: float | None = None

    def __post_init__(self) -> None:
        _optional_nonnegative("max_tilt_deg", self.max_tilt_deg)
        _optional_nonnegative("max_rate_dps", self.max_rate_dps)
        if self.max_tilt_deg is not None and self.max_tilt_deg > 180.0:
            raise ValueError("max_tilt_deg cannot exceed 180")


@dataclass
class Spacecraft:
    name: str = "Untitled spacecraft"
    components: list[Component] = field(default_factory=list)
    # Editor-only normalized canvas positions, keyed by component ID.
    layout: dict[str, tuple[float, float]] = field(default_factory=dict)
    revision: str = ""
    provenance: DataProvenance = field(default_factory=DataProvenance)
    landing_gear: LandingGear | None = None
    attitude_limits: AttitudeLimits | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("spacecraft name must not be empty")

    def add_component(self, component: Component) -> None:
        if not isinstance(component, Component):
            raise TypeError("component must be a spacecraft Component")
        if any(existing.id == component.id for existing in self.components):
            raise ValueError(f"Component id already exists: {component.id}")
        self.components.append(component)

    def remove_component(self, component_id: str) -> bool:
        for index, component in enumerate(self.components):
            if component.id == component_id:
                del self.components[index]
                self.layout.pop(component_id, None)
                return True
        return False

    def get_component(self, component_id: str) -> Component | None:
        return next(
            (part for part in self.components if part.id == component_id),
            None,
        )
