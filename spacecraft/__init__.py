"""Spacecraft design, analysis, and persistence domain package."""

from .analysis import (
    MISSION_PROFILES,
    MissionAssessment,
    MissionProfile,
    SpacecraftAnalysis,
    analyze_spacecraft,
    assess_mission,
)
from .components import (
    Component,
    Engine,
    FuelTank,
    Payload,
    PowerSystem,
    component_from_catalog,
)
from .presets import load_spacecraft, save_spacecraft
from .vehicle import Spacecraft
from .lunar import (
    LunarOrbitBudget,
    LunarReachability,
    estimate_lunar_orbit_budget,
    lunar_mission_assessment,
)
from .mission import (
    MissionSimulationResult,
    lambert_universal,
    run_lunar_flyby_simulation,
)

__all__ = [
    "Component",
    "Engine",
    "FuelTank",
    "Payload",
    "PowerSystem",
    "Spacecraft",
    "LunarOrbitBudget",
    "LunarReachability",
    "MissionSimulationResult",
    "SpacecraftAnalysis",
    "MissionProfile",
    "MissionAssessment",
    "MISSION_PROFILES",
    "analyze_spacecraft",
    "assess_mission",
    "estimate_lunar_orbit_budget",
    "lunar_mission_assessment",
    "lambert_universal",
    "run_lunar_flyby_simulation",
    "component_from_catalog",
    "load_spacecraft",
    "save_spacecraft",
]
