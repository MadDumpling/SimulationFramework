"""Deterministic design advice from the spacecraft's modeled screening values."""

from dataclasses import dataclass

from .analysis import MissionProfile, SpacecraftAnalysis
from .components import Engine, FuelTank
from .mission import EARTH_ASCENT_DELTA_V, TYPICAL_TLI_DELTA_V
from .readiness import assess_definition
from .vehicle import Spacecraft

SEVERITY_ORDER = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
}


@dataclass(frozen=True)
class AdviceItem:
    severity: str
    title: str
    evidence: str
    suggested_action: str


def advise_design(
    spacecraft: Spacecraft,
    analysis: SpacecraftAnalysis,
    mission: MissionProfile,
    result=None,
) -> list[AdviceItem]:
    """Return concrete bottlenecks, ordered by mission impact.

    Advice is based on the project's screening model. It does not certify
    hardware or prescribe a real flight design.
    """
    ranked: list[tuple[int, AdviceItem]] = []
    sequence = 0

    def add(severity, title, evidence, suggested_action):
        nonlocal sequence
        ranked.append(
            (
                sequence,
                AdviceItem(severity, title, evidence, suggested_action),
            )
        )
        sequence += 1

    engines = [part for part in spacecraft.components if isinstance(part, Engine)]
    tanks = [part for part in spacecraft.components if isinstance(part, FuelTank)]

    if not engines or analysis.thrust <= 0.0:
        add(
            "CRITICAL",
            "No usable main-engine thrust",
            f"Installed main-engine thrust is {analysis.thrust:,.1f} N.",
            "Install a main engine and enter a positive rated thrust before rerunning the screen.",
        )
    elif analysis.twr <= 1.0:
        add(
            "CRITICAL",
            "Insufficient liftoff thrust margin",
            f"Initial TWR is {analysis.twr:.3f}; the screening check requires TWR > 1.0.",
            "Increase main-engine thrust or reduce loaded vehicle mass; recheck TWR after adding propellant.",
        )

    if not tanks or analysis.fuel_mass <= 0.0:
        evidence = (
            "No propellant tanks are installed."
            if not tanks
            else "No usable propellant compatible with the installed engine is loaded."
        )
        add(
            "CRITICAL",
            "No usable compatible propellant",
            evidence,
            "Add a tank with the engine's declared propellant type and load usable propellant.",
        )

    if result is not None:
        ascent = result.required_earth_departure_delta_v.to_value("m/s")
        tli = result.tli_delta_v.to_value("m/s")
        required_delta_v = ascent + (tli if tli > 0.0 else TYPICAL_TLI_DELTA_V)
        available_delta_v = result.available_delta_v.to_value("m/s")
    else:
        required_delta_v = max(
            mission.required_delta_v,
            EARTH_ASCENT_DELTA_V + TYPICAL_TLI_DELTA_V,
        )
        available_delta_v = analysis.delta_v

    delta_v_gap = required_delta_v - available_delta_v
    if delta_v_gap > 0.0:
        add(
            "HIGH",
            "Ideal delta-v budget is short",
            (
                f"Available {available_delta_v / 1000.0:.2f} km/s; "
                f"screening requirement {required_delta_v / 1000.0:.2f} km/s; "
                f"shortfall {delta_v_gap / 1000.0:.2f} km/s."
            ),
            "Increase usable compatible propellant or engine Isp, then recheck wet mass and liftoff TWR.",
        )

    if result is not None:
        if result.simulated and not result.success and result.closest_approach is not None:
            closest = result.closest_approach.to_value("km")
            soi = result.lunar_sphere_of_influence.to_value("km")
            miss_distance = closest - soi
            add(
                "HIGH",
                "Propagated trajectory misses the lunar SOI",
                (
                    f"Closest approach is {closest:,.1f} km from the Moon's center, "
                    f"{miss_distance:,.1f} km outside the modeled SOI."
                ),
                "Review departure date and transfer duration, then rerun; this model does not optimize correction burns or launch windows.",
            )
        elif not result.simulated and result.reasons:
            add(
                "HIGH",
                "Mission pre-check blocked propagation",
                " ".join(result.reasons),
                "Resolve the vehicle or transfer pre-check reason above before rerunning the trajectory screen.",
            )

        if result.simulated and result.success and result.surface_impact:
            add(
                "HIGH",
                "Mean-surface impact is predicted",
                "The propagated path intersects the Moon's mean-radius sphere; terrain and touchdown are not modeled.",
                "Treat this as a trajectory warning, not a landing; review the encounter geometry and do not claim a safe touchdown.",
            )

    if analysis.power_generation_kw <= 0.0 and analysis.power_draw_kw > 0.0:
        add(
            "MEDIUM",
            "No electrical generation is declared",
            f"Declared load is {analysis.power_draw_kw:.2f} kW with no installed generation.",
            "Add or rate a power source and compare generation against the declared loads.",
        )
    elif analysis.power_surplus_kw < 0.0:
        add(
            "MEDIUM",
            "Declared electrical load exceeds generation",
            (
                f"Generation is {analysis.power_generation_kw:.2f} kW and "
                f"declared load is {analysis.power_draw_kw:.2f} kW "
                f"({analysis.power_surplus_kw:+.2f} kW margin)."
            ),
            "Review subsystem loads and rated generation; check battery discharge ratings separately.",
        )

    definition = assess_definition(spacecraft)
    if definition.blocking:
        examples = "; ".join(
            f"{gap.subject}: {gap.message}" for gap in definition.blocking[:3]
        )
        remaining = len(definition.blocking) - min(len(definition.blocking), 3)
        if remaining:
            examples += f"; and {remaining} more blocking definition gap(s)"
        add(
            "MEDIUM",
            "Landing-simulation inputs are incomplete",
            examples,
            "Supply the missing landing-gear, attitude-control, and engine-envelope data before making powered-descent or touchdown claims.",
        )

    mass = spacecraft.mass_properties()
    if mass.com_m is None:
        add(
            "MEDIUM",
            "Vehicle center of mass is unknown",
            "At least one component with nonzero mass lacks center-of-mass data.",
            "Enter component center-of-mass values to enable aggregate balance and stability checks.",
        )

    if definition.untraceable_parts:
        add(
            "LOW",
            "Vehicle inputs are not fully traceable",
            (
                f"{len(definition.untraceable_parts)} vehicle or component definition(s) "
                "use illustrative or estimated data."
            ),
            "Replace showcase values with sourced data and record source revision and uncertainty where available.",
        )

    if not ranked:
        add(
            "LOW",
            "No current modeled bottlenecks detected",
            "The available screening checks did not identify a blocking issue.",
            "Run the date-specific trajectory screen and review model limitations before drawing mission conclusions.",
        )

    ranked.sort(key=lambda entry: (SEVERITY_ORDER[entry[1].severity], entry[0]))
    return [item for _, item in ranked]


def format_advice(items: list[AdviceItem]) -> str:
    """Format ranked advice for the UI and exported report."""
    lines = ["RANKED DESIGN ADVISOR"]
    for rank, item in enumerate(items, start=1):
        lines.extend(
            (
                f"{rank}. [{item.severity}] {item.title}",
                f"   Evidence: {item.evidence}",
                f"   Suggested action: {item.suggested_action}",
            )
        )
    lines.extend(
        (
            "",
            "Rule-based screening advice only; it is not flight certification or a real-vehicle design prescription.",
        )
    )
    return "\n".join(lines)
