"""Turn a mission simulation result into a flight outcome and a verdict banner.

Pure functions (no DearPyGui/OpenGL) so the wording and the classification are
unit-testable. Colours are 0-255 RGB.
"""

from dataclasses import dataclass

from spacecraft.mission import EARTH_ASCENT_DELTA_V, TYPICAL_TLI_DELTA_V
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
