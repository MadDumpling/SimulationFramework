"""Idealized single-stage spacecraft performance and mission analysis."""

from dataclasses import dataclass, field
import math

from .components import Engine, FuelTank, PowerSystem
from .vehicle import Spacecraft

STANDARD_GRAVITY = 9.80665


@dataclass(frozen=True)
class MissionProfile:
    id: str
    name: str
    required_delta_v: float


@dataclass
class SpacecraftAnalysis:
    dry_mass: float = 0.0
    fuel_mass: float = 0.0
    wet_mass: float = 0.0
    thrust: float = 0.0
    isp: float = 0.0
    delta_v: float = 0.0
    twr: float = 0.0
    burn_time: float = 0.0
    power_generation_kw: float = 0.0
    power_draw_kw: float = 0.0
    power_surplus_kw: float = 0.0
    power_storage_kwh: float = 0.0
    warnings: list[str] = field(default_factory=list)


@dataclass
class MissionAssessment:
    mission: MissionProfile
    achievable: bool
    delta_v_margin: float
    reasons: list[str] = field(default_factory=list)


# Approximate ideal mission budgets for educational comparison, not guarantees.
MISSION_PROFILES = {
    "leo": MissionProfile("leo", "Low Earth Orbit", 9_400.0),
    "geostationary": MissionProfile("geostationary", "Geostationary Orbit", 12_500.0),
    "moon_transfer": MissionProfile("moon_transfer", "Moon Transfer", 12_800.0),
    "lunar_orbit": MissionProfile("lunar_orbit", "Lunar Orbit", 14_000.0),
    "mars_transfer": MissionProfile("mars_transfer", "Mars Transfer", 15_000.0),
}


def analyze_spacecraft(spacecraft: Spacecraft) -> SpacecraftAnalysis:
    """Calculate an ideal single-stage performance estimate for an assembly.

    This uses the Tsiolkovsky rocket equation and excludes drag, gravity losses,
    trajectory effects, and stage separation. Declared residual (unusable)
    propellant is carried as mass but not burned; unknown residual counts as 0.
    """
    result = SpacecraftAnalysis()
    engines = [part for part in spacecraft.components if isinstance(part, Engine)]
    tanks = [part for part in spacecraft.components if isinstance(part, FuelTank)]
    power_systems = [
        part for part in spacecraft.components if isinstance(part, PowerSystem)
    ]

    result.dry_mass = sum(part.dry_mass for part in spacecraft.components)
    result.wet_mass = result.dry_mass + sum(tank.fuel_mass for tank in tanks)
    result.thrust = sum(engine.thrust for engine in engines)
    result.power_generation_kw = sum(
        system.generation_kw for system in power_systems
    )
    result.power_storage_kwh = sum(system.storage_kwh for system in power_systems)
    result.power_draw_kw = sum(engine.power_draw_kw for engine in engines)
    result.power_surplus_kw = result.power_generation_kw - result.power_draw_kw

    if not engines:
        result.warnings.append("No engine is installed.")
    elif not tanks:
        result.warnings.append("No fuel tank is installed.")
    else:
        engine_fuels = {engine.fuel_type for engine in engines}
        if len(engine_fuels) > 1:
            result.warnings.append(
                "Mixed engine propellants are not supported by this single-stage estimate."
            )
        else:
            fuel_type = next(iter(engine_fuels))
            compatible_tanks = [tank for tank in tanks if tank.fuel_type == fuel_type]
            incompatible_tanks = [tank for tank in tanks if tank.fuel_type != fuel_type]
            if incompatible_tanks:
                result.warnings.append(
                    "Some tank propellant does not match the installed engine fuel type."
                )

            result.fuel_mass = sum(tank.usable_propellant for tank in compatible_tanks)
            if result.fuel_mass > 0.0:
                result.thrust = sum(engine.thrust for engine in engines)
                mass_flow = sum(
                    engine.thrust / (engine.isp * STANDARD_GRAVITY)
                    for engine in engines
                )
                result.isp = result.thrust / (mass_flow * STANDARD_GRAVITY)
                result.burn_time = result.fuel_mass / mass_flow
                if result.dry_mass > 0.0:
                    final_mass = result.wet_mass - result.fuel_mass
                    result.delta_v = (
                        result.isp
                        * STANDARD_GRAVITY
                        * math.log(result.wet_mass / final_mass)
                    )
            else:
                result.warnings.append(
                    "No propellant compatible with the installed engine is loaded."
                )

    if result.wet_mass > 0.0:
        result.twr = result.thrust / (result.wet_mass * STANDARD_GRAVITY)
    if result.power_surplus_kw < 0.0:
        result.warnings.append("Engine power demand exceeds installed generation.")

    return result


def assess_mission(
    analysis: SpacecraftAnalysis,
    mission: MissionProfile,
) -> MissionAssessment:
    reasons = []
    margin = analysis.delta_v - mission.required_delta_v
    if margin < 0.0:
        reasons.append(
            f"Delta-v shortfall: {-margin:,.0f} m/s below the ideal budget."
        )
    if analysis.twr < 1.0:
        reasons.append("Liftoff TWR is below 1.0; the vehicle cannot lift off vertically.")
    return MissionAssessment(
        mission=mission,
        achievable=not reasons,
        delta_v_margin=margin,
        reasons=reasons,
    )
