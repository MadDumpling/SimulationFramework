"""Conservative touchdown classification for future powered-descent runs.

This evaluates a terminal state against explicit vehicle/site limits. It does
not itself propagate descent or prove that a trajectory is safe.
"""

from dataclasses import dataclass

from .reference_data import APOLLO_11_SITE
from .vehicle import Spacecraft


@dataclass(frozen=True)
class TouchdownState:
    latitude_deg: float
    longitude_deg: float
    vertical_speed_mps: float
    horizontal_speed_mps: float
    tilt_deg: float
    angular_rate_dps: float
    terrain_contact_valid: bool = True


@dataclass(frozen=True)
class TouchdownAssessment:
    success: bool
    reasons: tuple[str, ...]


def assess_touchdown(
    spacecraft: Spacecraft,
    state: TouchdownState,
    site=APOLLO_11_SITE,
) -> TouchdownAssessment:
    """Classify touchdown against gear, target-site, and attitude limits.

    Unknown hard limits deliberately fail closed: the outcome cannot be called a
    safe landing when the vehicle definition lacks a required structural limit.
    """
    reasons = []
    gear = spacecraft.landing_gear
    attitude = spacecraft.attitude_limits
    if gear is None:
        reasons.append("Landing gear/contact envelope is unknown.")
    else:
        if gear.rated_vertical_speed_mps is None:
            reasons.append("Rated vertical touchdown speed is unknown.")
        elif state.vertical_speed_mps > gear.rated_vertical_speed_mps:
            reasons.append("Vertical touchdown speed exceeds landing-gear rating.")
        if gear.rated_horizontal_speed_mps is None:
            reasons.append("Rated horizontal touchdown speed is unknown.")
        elif state.horizontal_speed_mps > gear.rated_horizontal_speed_mps:
            reasons.append("Horizontal touchdown speed exceeds landing-gear rating.")
    if attitude is None or attitude.max_tilt_deg is None:
        reasons.append("Allowable touchdown tilt is unknown.")
    elif state.tilt_deg > attitude.max_tilt_deg:
        reasons.append("Touchdown tilt exceeds vehicle limit.")
    if attitude is None or attitude.max_rate_dps is None:
        reasons.append("Allowable touchdown angular rate is unknown.")
    elif state.angular_rate_dps > attitude.max_rate_dps:
        reasons.append("Touchdown angular rate exceeds vehicle limit.")
    if not state.terrain_contact_valid:
        reasons.append("Vehicle intersects terrain outside the allowed landing contact.")
    if site.landing_ellipse_km is None:
        reasons.append("Target landing ellipse is unknown.")
    elif site.elevation_m is None:
        reasons.append("Target-site terrain elevation is unknown.")
    return TouchdownAssessment(success=not reasons, reasons=tuple(reasons))
