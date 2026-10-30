"""Turn a mission simulation result into a flight outcome and a verdict banner.

Pure functions (no DearPyGui/OpenGL) so the wording and the classification are
unit-testable. Colours are 0-255 RGB.
"""

from dataclasses import dataclass

from spacecraft.analysis import SpacecraftAnalysis
from spacecraft.apollo11_reference import APOLLO_11_REFERENCE, format_elapsed_time
from spacecraft.mission import (
    EARTH_ASCENT_DELTA_V,
    MOON_RADIUS_M,
    TYPICAL_TLI_DELTA_V,
    MissionSimulationResult,
)
from viewport import flight

from .mission_timeline import mission_timeline as mission_timeline

GREEN = (110, 220, 130)
RED = (255, 105, 90)
AMBER = (255, 190, 80)
BLUE = (140, 180, 255)

SLOW_RUN_SECONDS = 15


def running_banner(elapsed_seconds: float) -> tuple[str, tuple]:
    """Progress banner so a long run (e.g. first-use ephemeris download) is not silent."""
    seconds = int(elapsed_seconds)
    text = f"MISSION IN PROGRESS — simulating the transfer to the Moon… {seconds} s"
    if seconds >= SLOW_RUN_SECONDS:
        text += " (the first run downloads the JPL ephemeris, which can take a while)"
    return text, BLUE


LANDING_CAVEAT = (
    "The landing shown is an illustration: capture, descent and touchdown are not simulated."
)


def apollo11_reference_report() -> str:
    """Format the source-backed Apollo 11 launch-to-TLI reference profile."""
    mission = APOLLO_11_REFERENCE
    parking = mission.parking_orbit
    tli = mission.tli
    s_ic = mission.s_ic_outboard_cutoff
    s_ii = mission.s_ii_cutoff
    s_ivb = mission.s_ivb_first_burn_cutoff
    lines = [
        f"{mission.mission} — historical reference, not a live simulation",
        (
            f"Launch: {mission.launch_date_utc} {mission.launch_time_utc} UTC "
            f"({mission.launch_time_basis})"
        ),
        (
            f"Site: {mission.launch_site}; {mission.launch_latitude_deg:.6f}° N, "
            f"{mission.launch_longitude_east_deg:.6f}° E "
            f"({360.0 - mission.launch_longitude_east_deg:.6f}° W); "
            f"azimuth {mission.launch_azimuth_deg:.3f}°"
        ),
        (
            f"Maximum dynamic pressure: {mission.maximum_dynamic_pressure_pa:,.0f} Pa "
            f"at {format_elapsed_time(mission.maximum_dynamic_pressure_time_s)}"
        ),
        "",
        "Reference profile only; the source labels its event sequence predicted.",
        "STAGING AND FLIGHT EVENTS",
    ]
    lines.extend(
        f"{format_elapsed_time(event.elapsed_seconds)}  {event.phase}: {event.label}"
        for event in mission.events
    )
    lines.extend(
        [
            "",
            "STAGE CUTOFF CONDITIONS",
            (
                f"S-IC outboard cutoff: {s_ic.altitude_m:,.1f} m altitude; "
                f"{s_ic.inertial_velocity_m_s:,.4f} m/s; "
                f"flight-path angle {s_ic.flight_path_angle_deg:.6f}°"
            ),
            (
                f"S-II cutoff: {s_ii.altitude_m:,.1f} m altitude; "
                f"{s_ii.inertial_velocity_m_s:,.4f} m/s; "
                f"flight-path angle {s_ii.flight_path_angle_deg:.6f}°"
            ),
            (
                f"S-IVB first-burn cutoff: {s_ivb.altitude_m:,.2f} m altitude; "
                f"{s_ivb.inertial_velocity_m_s:,.4f} m/s; "
                f"flight-path angle {s_ivb.flight_path_angle_deg:.6f}°"
            ),
            "",
            "EARTH PARKING ORBIT",
            (
                f"Geocentric radius: {parking.geocentric_radius_m:,.1f} m; "
                f"inertial speed: {parking.inertial_velocity_m_s:,.3f} m/s"
            ),
            (
                f"Inclination: {parking.inclination_deg:.6f}°; "
                f"descending node: {parking.descending_node_deg:.6f}°; "
                f"eccentricity: {parking.eccentricity:.7f}; "
                f"period: {parking.orbital_period_s:,.3f} s"
            ),
            "",
            "TRANSLUNAR INJECTION (S-IVB SECOND-BURN CUTOFF)",
            (
                f"Geocentric radius: {tli.geocentric_radius_m:,.1f} m; "
                f"inertial speed: {tli.inertial_velocity_m_s:,.3f} m/s"
            ),
            (
                f"Flight-path angle: {tli.flight_path_angle_deg:.6f}°; "
                f"inclination: {tli.inclination_deg:.6f}°; "
                f"descending node: {tli.descending_node_deg:.6f}°; "
                f"eccentricity: {tli.eccentricity:.8f}"
            ),
            (
                f"Post-injection osculating orbit: apogee radius "
                f"{tli.apogee_radius_m / 1000:,.1f} km; perigee radius "
                f"{tli.perigee_radius_m / 1000:,.1f} km; period "
                f"{tli.orbital_period_s:,.3f} s"
            ),
            "",
            f"Source: {mission.source_id}, {mission.source_title}.",
            f"{mission.source_tables}; {mission.source_url}",
            mission.fidelity_note,
        ]
    )
    return "\n".join(lines)


def apollo11_reference_summary() -> str:
    """Return a compact overview for the Mission tab."""
    mission = APOLLO_11_REFERENCE
    return (
        f"{mission.launch_date_utc} · LC-39A · TLI "
        f"{format_elapsed_time(mission.tli.elapsed_seconds)} · "
        f"{mission.tli.inertial_velocity_m_s / 1000:.3f} km/s"
    )


@dataclass(frozen=True)
class LunarPrescreen:
    """The two gates the mission check applies to the vehicle, with live numbers."""

    liftoff_ok: bool
    delta_v_ok: bool
    twr: float
    delta_v_kms: float
    needed_kms: float
    summary: str
    hint: str

    @property
    def ready(self) -> bool:
        return self.liftoff_ok and self.delta_v_ok


def lunar_prescreen(analysis) -> LunarPrescreen:
    """Will this design clear the single-stage lunar pre-screen? (Approximate.)

    Needs thrust-to-weight above 1 to leave the pad, and ideal delta-v for the Earth
    ascent plus the trans-lunar transfer. Adding propellant raises delta-v but lowers
    thrust-to-weight, so a design has to balance both.
    """
    needed = (EARTH_ASCENT_DELTA_V + TYPICAL_TLI_DELTA_V) / 1000.0
    have = analysis.delta_v / 1000.0
    liftoff_ok = analysis.thrust > 0.0 and analysis.twr > 1.0
    delta_v_ok = have >= needed
    if liftoff_ok and delta_v_ok:
        summary = "Ready: lifts off and has the delta-v to reach the Moon."
        hint = ""
    elif not liftoff_ok and not delta_v_ok:
        summary = "Will not lift off, and lacks the delta-v."
        hint = (
            "Raise thrust (more or bigger engines) first so thrust-to-weight exceeds 1, "
            "then add propellant for delta-v."
        )
    elif not liftoff_ok:
        summary = "Will not lift off: thrust-to-weight must exceed 1.0."
        hint = "Add engines or thrust, or remove propellant and payload mass."
    else:
        summary = "Lifts off, but falls short: not enough delta-v."
        hint = (
            "Add propellant or a higher-Isp engine. More propellant lowers thrust-to-weight, "
            "so raise thrust with it."
        )
    return LunarPrescreen(liftoff_ok, delta_v_ok, analysis.twr, have, needed, summary, hint)


def prescreen_text(check: LunarPrescreen) -> str:
    lift = "OK" if check.liftoff_ok else "FAIL"
    dv = "OK" if check.delta_v_ok else "FAIL"
    lines = [
        check.summary,
        f"Lift-off: thrust-to-weight {check.twr:.2f}, needs > 1.0  [{lift}]",
        f"Delta-v: {check.delta_v_kms:.1f} km/s, needs about {check.needed_kms:.1f} km/s "
        f"(9.4 ascent + ~3.2 transfer)  [{dv}]",
    ]
    if check.hint:
        lines.append(check.hint)
    return "\n".join(lines)


def delta_v_summary(result) -> str:
    """How far the vehicle is from what the mission needs, from a simulation result."""
    have = result.available_delta_v.to_value("km/s")
    transfer = result.tli_delta_v.to_value("km/s") or TYPICAL_TLI_DELTA_V / 1000.0
    needed = result.required_earth_departure_delta_v.to_value("km/s") + transfer
    return f"The vehicle has {have:.1f} km/s of ideal delta-v; the mission needs about {needed:.1f} km/s."


def can_lift_off(analysis) -> tuple[bool, bool]:
    """(liftoff, has_thrust), using the same check as the mission pre-screen."""
    has_thrust = analysis.thrust > 0.0
    return has_thrust and analysis.twr > 1.0, has_thrust


def flight_outcome(result) -> str:
    """Map a MissionSimulationResult onto the animation outcome."""
    if not result.simulated:
        return flight.FALL  # the vehicle cannot get to the Moon
    return flight.LAND if result.success else flight.MISS


def no_liftoff_banner(analysis) -> tuple[str, tuple]:
    if analysis.thrust <= 0.0:
        why = "no engine thrust is installed"
    else:
        why = f"thrust-to-weight is {analysis.twr:.2f}, it must exceed 1.0"
    return f"MISSION FAILED — the vehicle cannot lift off: {why}.", RED


def verdict_banner(result, outcome: str) -> tuple[str, tuple]:
    km = lambda quantity: f"{quantity.to_value('km'):,.0f} km"  # noqa: E731
    if outcome == flight.LAND:
        approach = (
            f" (closest approach {km(result.closest_approach)})"
            if result.closest_approach is not None
            else ""
        )
        return (
            f"REACHED THE MOON — the path enters the lunar sphere of influence{approach}. "
            + LANDING_CAVEAT,
            GREEN,
        )
    if outcome == flight.MISS:
        approach = (
            f"closest approach {km(result.closest_approach)}, "
            if result.closest_approach is not None
            else ""
        )
        return (
            "MISSION FAILED — the trajectory misses the Moon "
            f"({approach}lunar sphere of influence {km(result.lunar_sphere_of_influence)}).",
            RED,
        )
    reason = result.reasons[0] if result.reasons else "the vehicle lacks the required delta-v."
    return (
        f"MISSION FAILED — the vehicle cannot reach the Moon: {reason} {delta_v_summary(result)}",
        RED,
    )


def error_banner(error) -> tuple[str, tuple]:
    return f"SIMULATION ERROR — no verdict: {error}", AMBER


def lunar_mission_report(
    result: MissionSimulationResult,
    analysis: SpacecraftAnalysis,
) -> str:
    """Format the measured run outcome, vehicle metrics, margins, and model limits."""
    available = result.available_delta_v.to_value("km/s")
    ascent = result.required_earth_departure_delta_v.to_value("km/s")
    remaining_after_ascent = available - ascent
    tli_required = result.tli_delta_v.to_value("km/s")
    tli_margin = remaining_after_ascent - tli_required
    transfer_days = result.transfer_time.to_value("day")

    if not result.simulated:
        outcome = "NOT PROPAGATED — vehicle or transfer pre-check blocked the run."
        tli_text = (
            f"{tli_required:.3f} km/s (solved, but run stopped before propagation)"
            if tli_required > 0.0
            else "Not solved; vehicle pre-check stopped the run."
        )
    elif result.success:
        outcome = "LUNAR ARRIVAL — propagated trajectory entered the lunar sphere of influence."
        tli_text = f"{tli_required:.3f} km/s"
    else:
        outcome = "MISSION FAILED — propagated trajectory missed the lunar sphere of influence."
        tli_text = f"{tli_required:.3f} km/s"

    if result.closest_approach is None:
        closest_text = "Not available; no trajectory was propagated."
        soi_margin_text = "Not available."
        surface_clearance_text = "Not available."
    else:
        closest_km = result.closest_approach.to_value("km")
        soi_km = result.lunar_sphere_of_influence.to_value("km")
        soi_margin_km = soi_km - closest_km
        closest_text = f"{closest_km:,.1f} km"
        soi_margin_text = (
            f"{soi_margin_km:+,.1f} km "
            f"({'inside' if soi_margin_km >= 0.0 else 'outside'} the SOI boundary)"
        )
        surface_clearance_km = closest_km - MOON_RADIUS_M / 1000.0
        surface_clearance_text = (
            f"{surface_clearance_km:+,.1f} km from the mean lunar surface "
            f"({'impact predicted' if surface_clearance_km <= 0.0 else 'no impact predicted'})"
        )

    lines = [
        outcome,
        "",
        "VEHICLE AND PROPULSION",
        f"Dry mass: {analysis.dry_mass:,.1f} kg",
        f"Usable propellant: {analysis.fuel_mass:,.1f} kg",
        f"Wet mass: {analysis.wet_mass:,.1f} kg",
        f"Rated thrust: {analysis.thrust:,.1f} N",
        f"Initial thrust-to-weight: {analysis.twr:.3f}",
        f"Effective specific impulse: {analysis.isp:.2f} s",
        f"Ideal burn time: {analysis.burn_time:,.1f} s",
        "",
        "DELTA-V BUDGET",
        f"Ideal vehicle delta-v available: {available:.3f} km/s",
        f"Earth-ascent allowance: {ascent:.3f} km/s",
        f"Delta-v after ascent allowance: {remaining_after_ascent:+.3f} km/s",
        f"Required TLI: {tli_text}",
        (
            f"Margin after TLI: {tli_margin:+.3f} km/s"
            if result.simulated or tli_required > 0.0
            else "Margin after TLI: unavailable; TLI was not solved."
        ),
        "",
        "TRAJECTORY",
        f"Departure (UTC): {result.departure_time}",
        f"Arrival (UTC): {result.arrival_time}",
        f"Transfer duration: {transfer_days:.3f} days",
        f"Propagation: {'completed' if result.simulated else 'not started'}",
        f"Closest approach to Moon center: {closest_text}",
        f"Closest-approach time (UTC): {result.closest_approach_time or 'not available'}",
        (
            "Relative speed at closest approach: "
            f"{result.relative_speed_at_closest_approach_mps:,.1f} m/s"
            if result.relative_speed_at_closest_approach_mps is not None
            else "Relative speed at closest approach: not available."
        ),
        f"SOI radius: {result.lunar_sphere_of_influence.to_value('km'):,.1f} km",
        f"SOI margin: {soi_margin_text}",
        f"Mean lunar radius: {MOON_RADIUS_M / 1000:,.1f} km",
        f"Surface clearance: {surface_clearance_text}",
        f"Surface impact flag: {'YES' if result.surface_impact else 'NO'}",
        f"Trajectory evaluation samples: {result.trajectory_points:,}",
        (
            f"Integrator: {result.integrator}; max step "
            f"{result.integration_max_step_s:g} s; relative tolerance "
            f"{result.integration_rtol:g}; absolute tolerance "
            f"{result.integration_atol:g}"
        ),
        f"Ephemeris/model data: {result.data_source}",
    ]

    if result.reasons:
        lines.extend(("", "FAILURE REASONS", *(f"- {reason}" for reason in result.reasons)))
    if result.vehicle_warnings:
        lines.extend(("", "VEHICLE WARNINGS", *(f"- {warning}" for warning in result.vehicle_warnings)))
    if result.simulated and not result.success and result.closest_approach is not None:
        lines.extend(
            (
                "",
                "WHY THE TRAJECTORY MISSED",
                (
                    f"The closest pass stayed {abs(soi_margin_km):,.1f} km outside "
                    "the lunar SOI, so the modeled path did not count as lunar arrival."
                ),
                (
                    f"Run inputs: departure {result.departure_time}; "
                    f"{transfer_days:.3f}-day transfer; required TLI "
                    f"{tli_required:.3f} km/s; post-ascent TLI margin {tli_margin:+.3f} km/s."
                ),
                "The run uses an assumed phase-aligned parking-orbit departure. "
                "Date and transfer duration affect the Moon-target geometry; this model "
                "does not optimize a correction burn or launch window.",
            )
        )
    if result.success:
        lines.extend(
            (
                "",
                "ARRIVAL IS NOT LANDING",
                (
                    "Sphere-of-influence entry does not model lunar capture, powered descent, "
                    "or touchdown."
                ),
                (
                    "A mean-surface intersection is only an impact estimate; it does not "
                    "establish a safe landing."
                    if result.surface_impact
                    else "No mean-surface intersection was predicted; this does not establish "
                    "a safe landing."
                ),
            )
        )
    if result.assumptions:
        lines.extend(("", "MODEL ASSUMPTIONS AND LIMITS", *(f"- {item}" for item in result.assumptions)))

    return "\n".join(lines)
