"""UI-friendly lunar mission milestones and terminal-state semantics."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MissionMilestone:
    key: str
    label: str
    state: str
    reason: str = ""


def mission_timeline(result=None, running: bool = False) -> list[MissionMilestone]:
    """Return visible milestones; sphere-of-influence entry never means landing."""
    if result is None:
        launch_state = "SIMULATING" if running else "READY"
        remaining_state = "PENDING" if running else "READY"
        return [
            MissionMilestone("launch", "Launch", launch_state),
            MissionMilestone("earth_orbit", "Earth orbit", remaining_state),
            MissionMilestone("tli", "Trans-lunar injection", remaining_state),
            MissionMilestone("arrival", "Lunar arrival", remaining_state),
            MissionMilestone("touchdown", "Touchdown", remaining_state),
        ]

    if not result.simulated:
        stop_reason = result.reasons[0] if result.reasons else "Vehicle precheck failed."
        return [
            MissionMilestone("launch", "Launch", "FAILED", stop_reason),
            MissionMilestone("earth_orbit", "Earth orbit", "PENDING"),
            MissionMilestone("tli", "Trans-lunar injection", "PENDING"),
            MissionMilestone("arrival", "Lunar arrival", "PENDING"),
            MissionMilestone("touchdown", "Touchdown", "PENDING"),
        ]

    arrival_state = "REACHED" if result.success else "FAILED"
    arrival_reason = (
        "Entered the Moon's sphere of influence."
        if result.success
        else "Propagated trajectory missed the lunar sphere of influence."
    )
    return [
        MissionMilestone(
            "launch",
            "Launch",
            "SCREENED",
            "Launch/ascent is an allowance, not simulated.",
        ),
        MissionMilestone(
            "earth_orbit",
            "Earth orbit",
            "SCREENED",
            "Circular parking orbit is assumed.",
        ),
        MissionMilestone(
            "tli",
            "Trans-lunar injection",
            "SCREENED",
            f"Required {result.tli_delta_v.to_value('km/s'):.2f} km/s.",
        ),
        MissionMilestone("arrival", "Lunar arrival", arrival_state, arrival_reason),
        MissionMilestone(
            "touchdown",
            "Safe landing",
            "FAILED",
            "Moon encounter is not a landing simulation.",
        ),
    ]
