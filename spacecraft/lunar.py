"""Date-specific, patched-conic estimate for reaching low lunar orbit.

The Moon state comes from Astropy's JPL DE440s ephemeris. The transfer model is
an optimistic two-body Hohmann approximation, not a launch-window optimizer or
flight-certified trajectory simulation.
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import certifi
import numpy as np
from astropy import units as u
from astropy.constants import GM_earth, R_earth
from astropy.time import Time, TimeDelta
from astropy.utils.data import download_file

from .analysis import SpacecraftAnalysis

EARTH_ASCENT_BUDGET = 9_400.0 * u.m / u.s
PARKING_ORBIT_ALTITUDE = 200.0 * u.km
LUNAR_ORBIT_ALTITUDE = 100.0 * u.km
# Lunar constants from NASA/JPL Solar System Dynamics physical parameters.
# Astropy does not publish a nominal lunar GM or radius in astropy.constants.
# Source: https://ssd.jpl.nasa.gov/planets/phys_par.html
GM_MOON = 4.902800066e12 * u.m**3 / u.s**2
R_MOON = 1_737.4 * u.km
DE440S_URL = (
    "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp"
)


@dataclass(frozen=True)
class LunarOrbitBudget:
    departure_time: str
    arrival_time: str
    moon_distance: u.Quantity
    transfer_time: u.Quantity
    earth_ascent: u.Quantity
    trans_lunar_injection: u.Quantity
    lunar_orbit_insertion: u.Quantity
    required_delta_v: u.Quantity
    data_source: str
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class LunarReachability:
    achievable: bool
    required_delta_v: u.Quantity
    available_delta_v: u.Quantity
    delta_v_margin: u.Quantity
    reasons: tuple[str, ...]


def _moon_geocentric_state(epoch: Time) -> tuple[u.Quantity, u.Quantity]:
    """Return JPL DE440s Earth-relative Moon position and velocity."""
    from astropy.coordinates import get_body_barycentric_posvel, solar_system_ephemeris

    kernel_path = _de440s_kernel_path()
    with solar_system_ephemeris.set(kernel_path):
        moon_position, moon_velocity = get_body_barycentric_posvel("moon", epoch)
        earth_position, earth_velocity = get_body_barycentric_posvel("earth", epoch)

    return (
        (moon_position.xyz - earth_position.xyz).to(u.m),
        (moon_velocity.xyz - earth_velocity.xyz).to(u.m / u.s),
    )


@lru_cache(maxsize=1)
def _de440s_kernel_path() -> str:
    """Download/cache JPL's DE440s kernel with a known CA bundle."""
    try:
        return download_file(
            DE440S_URL,
            cache=True,
            show_progress=True,
            timeout=60,
            ssl_context={"cafile": certifi.where()},
        )
    except Exception as error:
        raise RuntimeError(
            "Could not obtain JPL DE440s ephemeris data. Check the network and "
            "TLS certificates, then retry; the Moon reachability check does not "
            "silently substitute approximate ephemerides."
        ) from error


def _coerce_time(value: Any) -> Time:
    if isinstance(value, Time):
        return value.utc
    return Time(value, scale="utc")


def moon_sphere_of_influence() -> u.Quantity:
    """Return Laplace's lunar sphere of influence from real body parameters."""
    return (
        (GM_MOON / GM_earth) ** (2.0 / 5.0)
        * (384_400.0 * u.km)
    ).to(u.km)


def estimate_lunar_orbit_budget(departure_time: Any) -> LunarOrbitBudget:
    """Estimate Earth-surface-to-100-km-lunar-orbit delta-v for a departure.

    A 200 km circular parking orbit, circular/coplanar Hohmann transfer, and a
    typical 9.4 km/s Earth-surface-to-LEO budget are assumed. The Moon's real
    DE440s state is sampled at the estimated arrival epoch for lunar capture.
    """
    departure = _coerce_time(departure_time)
    earth_mu = GM_earth.to(u.m**3 / u.s**2)
    moon_mu = GM_MOON.to(u.m**3 / u.s**2)
    parking_radius = (R_earth + PARKING_ORBIT_ALTITUDE).to(u.m)

    # Iterate transfer time and Moon range so the encounter epoch uses the
    # ephemeris position at arrival, rather than a fixed mean lunar distance.
    arrival = departure + TimeDelta(5.0 * u.day)
    moon_position, moon_velocity = _moon_geocentric_state(arrival)
    for _ in range(4):
        moon_distance = np.linalg.norm(moon_position.to_value(u.m)) * u.m
        semimajor_axis = (parking_radius + moon_distance) / 2.0
        transfer_time = np.pi * np.sqrt(semimajor_axis**3 / earth_mu)
        arrival = departure + TimeDelta(transfer_time)
        moon_position, moon_velocity = _moon_geocentric_state(arrival)

    moon_distance = np.linalg.norm(moon_position.to_value(u.m)) * u.m
    semimajor_axis = (parking_radius + moon_distance) / 2.0
    transfer_time = np.pi * np.sqrt(semimajor_axis**3 / earth_mu)
    parking_speed = np.sqrt(earth_mu / parking_radius)
    transfer_departure_speed = np.sqrt(
        earth_mu * (2.0 / parking_radius - 1.0 / semimajor_axis)
    )
    tli = (transfer_departure_speed - parking_speed).to(u.m / u.s)

    r_hat = moon_position.to_value(u.m) / moon_distance.to_value(u.m)
    angular_momentum = np.cross(
        moon_position.to_value(u.m),
        moon_velocity.to_value(u.m / u.s),
    )
    angular_momentum_norm = np.linalg.norm(angular_momentum)
    if angular_momentum_norm == 0.0:
        raise ValueError("JPL ephemeris returned a degenerate lunar orbit state")
    normal_hat = angular_momentum / angular_momentum_norm
    tangent_hat = np.cross(normal_hat, r_hat)

    transfer_arrival_speed = np.sqrt(
        earth_mu * (2.0 / moon_distance - 1.0 / semimajor_axis)
    ).to_value(u.m / u.s)
    moon_velocity_value = moon_velocity.to_value(u.m / u.s)
    radial_speed = float(np.dot(moon_velocity_value, r_hat))
    transverse_speed = float(np.dot(moon_velocity_value, tangent_hat))
    relative_speed = np.sqrt(
        (transfer_arrival_speed - transverse_speed) ** 2 + radial_speed**2
    ) * u.m / u.s

    lunar_orbit_radius = (R_MOON + LUNAR_ORBIT_ALTITUDE).to(u.m)
    moon_orbit_speed = np.sqrt(moon_mu / lunar_orbit_radius)
    hyperbolic_periapsis_speed = np.sqrt(
        relative_speed**2 + 2.0 * moon_mu / lunar_orbit_radius
    )
    lunar_insertion = (hyperbolic_periapsis_speed - moon_orbit_speed).to(u.m / u.s)
    total = EARTH_ASCENT_BUDGET + tli + lunar_insertion

    return LunarOrbitBudget(
        departure_time=departure.isot,
        arrival_time=arrival.isot,
        moon_distance=moon_distance.to(u.km),
        transfer_time=transfer_time.to(u.s),
        earth_ascent=EARTH_ASCENT_BUDGET,
        trans_lunar_injection=tli,
        lunar_orbit_insertion=lunar_insertion,
        required_delta_v=total.to(u.m / u.s),
        data_source="JPL DE440s + JPL lunar physical constants",
        assumptions=(
            "9.4 km/s approximate Earth-surface-to-LEO budget, including typical losses",
            "200 km circular Earth parking orbit",
            "coplanar two-body Hohmann transfer; no launch-window optimization",
            "100 km circular lunar orbit and impulsive lunar orbit insertion",
            "no staging, finite-burn, attitude, reserve, or engine-throttle model",
        ),
    )


def lunar_mission_assessment(
    analysis: SpacecraftAnalysis,
    budget: LunarOrbitBudget,
) -> LunarReachability:
    """Compare ideal vehicle delta-v and liftoff TWR with the lunar budget."""
    available = analysis.delta_v * u.m / u.s
    margin = (available - budget.required_delta_v).to(u.m / u.s)
    reasons = []
    if margin < 0.0 * u.m / u.s:
        reasons.append(
            f"Delta-v shortfall: {abs(margin.to_value(u.km / u.s)):.2f} km/s."
        )
    if analysis.twr < 1.0:
        reasons.append("Liftoff TWR is below 1.0.")
    return LunarReachability(
        achievable=not reasons,
        required_delta_v=budget.required_delta_v,
        available_delta_v=available,
        delta_v_margin=margin,
        reasons=tuple(reasons),
    )
