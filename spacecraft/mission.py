"""Earth-to-Moon trajectory screening with real JPL ephemerides.

This module shoots a Lambert transfer toward the date-specific Moon position,
then numerically propagates the spacecraft under Earth, Moon, and Sun point-mass
gravity. The test only reports success if the propagated path actually enters
the Moon's Laplace sphere of influence; no patched-conic delta-v-only answer is
labeled a successful mission.
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np
from astropy import units as u
from astropy.constants import GM_earth, GM_sun, R_earth
from astropy.time import Time, TimeDelta
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq, minimize_scalar

from .analysis import STANDARD_GRAVITY, SpacecraftAnalysis, analyze_spacecraft
from .lunar import (
    PARKING_ORBIT_ALTITUDE,
    _coerce_time,
    _de440s_kernel_path,
    moon_sphere_of_influence,
)
from .vehicle import Spacecraft

SUN_MU = GM_sun.to_value(u.m**3 / u.s**2)
EARTH_MU = GM_earth.to_value(u.m**3 / u.s**2)
MOON_MU = 4.902800066e12
EARTH_RADIUS_M = R_earth.to_value(u.m)
# Mean lunar radius from JPL Solar System Dynamics physical parameters.
MOON_RADIUS_M = 1_737_400.0


@dataclass(frozen=True)
class MissionSimulationResult:
    simulated: bool
    success: bool
    surface_impact: bool
    departure_time: str
    arrival_time: str
    transfer_time: u.Quantity
    tli_delta_v: u.Quantity
    required_earth_departure_delta_v: u.Quantity
    available_delta_v: u.Quantity
    closest_approach: u.Quantity | None
    lunar_sphere_of_influence: u.Quantity
    trajectory_points: int
    data_source: str
    reasons: tuple[str, ...]
    assumptions: tuple[str, ...]


def lambert_universal(
    initial_position: np.ndarray,
    final_position: np.ndarray,
    flight_time_seconds: float,
    gravitational_parameter: float,
    *,
    prograde: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Solve the zero-revolution Lambert boundary-value problem (universal z).

    All vector distances, times, and gravitational parameters must use mutually
    consistent units. This solver targets the requested endpoints; propagation
    later verifies whether the real dynamical model actually reaches the Moon.
    """
    r1 = np.asarray(initial_position, dtype=np.float64)
    r2 = np.asarray(final_position, dtype=np.float64)
    mu = float(gravitational_parameter)
    tof = float(flight_time_seconds)
    if r1.shape != (3,) or r2.shape != (3,):
        raise ValueError("Lambert position vectors must each have three values")
    if not np.all(np.isfinite(r1)) or not np.all(np.isfinite(r2)):
        raise ValueError("Lambert position vectors must be finite")
    if mu <= 0.0 or tof <= 0.0:
        raise ValueError("Lambert mu and flight time must be positive")

    norm1 = np.linalg.norm(r1)
    norm2 = np.linalg.norm(r2)
    cosine = float(np.clip(np.dot(r1, r2) / (norm1 * norm2), -1.0, 1.0))
    cross = np.cross(r1, r2)
    sine = float(np.linalg.norm(cross) / (norm1 * norm2))
    if (prograde and cross[2] < 0.0) or (not prograde and cross[2] >= 0.0):
        sine = -sine
    denominator = 1.0 - cosine
    if denominator <= 0.0:
        raise ValueError("Lambert transfer endpoints cannot be coincident")
    a_parameter = sine * np.sqrt(norm1 * norm2 / denominator)
    if abs(a_parameter) < 1e-12:
        raise ValueError("Lambert transfer geometry is singular")

    sqrt_mu = np.sqrt(mu)

    def stumpff_c(z_value: float) -> float:
        if z_value > 1e-8:
            root = np.sqrt(z_value)
            return (1.0 - np.cos(root)) / z_value
        if z_value < -1e-8:
            root = np.sqrt(-z_value)
            return (np.cosh(root) - 1.0) / (-z_value)
        return 0.5

    def stumpff_s(z_value: float) -> float:
        if z_value > 1e-8:
            root = np.sqrt(z_value)
            return (root - np.sin(root)) / root**3
        if z_value < -1e-8:
            root = np.sqrt(-z_value)
            return (np.sinh(root) - root) / root**3
        return 1.0 / 6.0

    def time_of_flight(z_value: float) -> float:
        c_value = stumpff_c(z_value)
        s_value = stumpff_s(z_value)
        if c_value <= 0.0:
            return np.inf
        y_value = norm1 + norm2 + a_parameter * (
            z_value * s_value - 1.0
        ) / np.sqrt(c_value)
        if y_value < 0.0:
            return np.inf
        x_value = np.sqrt(y_value / c_value)
        return (x_value**3 * s_value + a_parameter * np.sqrt(y_value)) / sqrt_mu

    z_grid = np.linspace(-4.0 * np.pi**2 + 1e-5, (2.0 * np.pi) ** 2 - 1e-5, 4001)
    previous_z = None
    previous_residual = None
    bracket = None
    for z_value in z_grid:
        tof_value = time_of_flight(float(z_value))
        if not np.isfinite(tof_value):
            previous_z = None
            previous_residual = None
            continue
        residual = tof_value - tof
        if previous_residual is not None and previous_residual * residual <= 0.0:
            bracket = (previous_z, float(z_value))
            break
        previous_z = float(z_value)
        previous_residual = residual
    if bracket is None:
        raise RuntimeError("Could not bracket a zero-revolution Lambert solution")
    z_solution = brentq(
        lambda z_value: time_of_flight(z_value) - tof,
        *bracket,
        xtol=1e-12,
        rtol=1e-12,
    )
    c_value = stumpff_c(z_solution)
    s_value = stumpff_s(z_solution)
    y_value = norm1 + norm2 + a_parameter * (
        z_solution * s_value - 1.0
    ) / np.sqrt(c_value)
    f_value = 1.0 - y_value / norm1
    g_value = a_parameter * np.sqrt(y_value / mu)
    g_dot = 1.0 - y_value / norm2
    if abs(g_value) < 1e-12:
        raise RuntimeError("Lambert solution has a singular transfer coefficient")
    return (r2 - f_value * r1) / g_value, (g_dot * r2 - r1) / g_value


@lru_cache(maxsize=8)
def _make_ephemeris_splines(
    departure_time: Time,
    duration_seconds: float,
    samples: int = 2500,
) -> tuple[CubicSpline, CubicSpline]:
    """Sample JPL DE440s and interpolate geocentric Moon and Sun states."""
    from astropy.coordinates import get_body_barycentric_posvel, solar_system_ephemeris

    _ = _de440s_kernel_path()
    elapsed = np.linspace(0.0, duration_seconds, samples)
    epochs = departure_time + TimeDelta(elapsed, format="sec")
    with solar_system_ephemeris.set(_de440s_kernel_path()):
        moon_position, _moon_velocity = get_body_barycentric_posvel("moon", epochs)
        earth_position, _earth_velocity = get_body_barycentric_posvel("earth", epochs)
        sun_position, _sun_velocity = get_body_barycentric_posvel("sun", epochs)

    moon = (moon_position.xyz - earth_position.xyz).to_value(u.m).T
    sun = (sun_position.xyz - earth_position.xyz).to_value(u.m).T
    return CubicSpline(elapsed, moon, axis=0), CubicSpline(elapsed, sun, axis=0)


def _ideal_tli_delta_v(spacecraft: Spacecraft, analysis: SpacecraftAnalysis) -> float:
    """Compute ideal rocket-equation capability remaining after ascent to LEO."""
    engines = [part for part in spacecraft.components if hasattr(part, "isp")]
    if not engines or analysis.fuel_mass <= 0.0:
        return 0.0
    mass_flow = sum(
        engine.thrust / (engine.isp * STANDARD_GRAVITY) for engine in engines
    )
    if mass_flow <= 0.0 or analysis.wet_mass <= analysis.fuel_mass:
        return 0.0
    effective_isp = analysis.thrust / (mass_flow * STANDARD_GRAVITY)
    final_mass = analysis.wet_mass - analysis.fuel_mass
    if analysis.wet_mass <= final_mass or final_mass <= 0.0:
        return 0.0
    return effective_isp * STANDARD_GRAVITY * np.log(analysis.wet_mass / final_mass)


def run_lunar_flyby_simulation(
    spacecraft: Spacecraft,
    departure_time: Any,
    transfer_time: u.Quantity = 5.0 * u.day,
    *,
    max_step: float = 300.0,
    rtol: float = 1e-9,
    atol: float = 1e-3,
) -> MissionSimulationResult:
    """Run an end-to-end impulsive-transfer lunar encounter screening.

    The spacecraft starts at a 200 km Earth parking orbit. A Lambert solution
    computes the required trans-lunar injection; the vehicle's ideal rocket
    equation and thrust are checked against that requirement. If feasible, a
    Sun/Earth/Moon point-mass propagation is integrated over the requested time
    of flight. ``success`` is true only when the simulated trajectory enters the
    Moon's Laplace sphere of influence. This is a trajectory screening result,
    not a powered lunar capture or surface landing simulation.
    """
    departure = _coerce_time(departure_time)
    flight_seconds = transfer_time.to_value(u.s)
    soi_radius = moon_sphere_of_influence()
    analysis = analyze_spacecraft(spacecraft)
    total_vehicle_delta_v = _ideal_tli_delta_v(spacecraft, analysis)
    orbit_radius = (R_earth + PARKING_ORBIT_ALTITUDE).to_value(u.m)
    required_ascent = 9_400.0
    available_tli = total_vehicle_delta_v - required_ascent
    arrival = departure + TimeDelta(flight_seconds, format="sec")
    reasons = []

    empty_result = dict(
        simulated=False,
        success=False,
        surface_impact=False,
        departure_time=departure.isot,
        arrival_time=arrival.isot,
        transfer_time=transfer_time.to(u.s),
        required_earth_departure_delta_v=required_ascent * u.m / u.s,
        available_delta_v=total_vehicle_delta_v * u.m / u.s,
        closest_approach=None,
        lunar_sphere_of_influence=soi_radius,
        trajectory_points=0,
        data_source="JPL DE440s not queried (vehicle precheck failed)",
        assumptions=(
            "200 km circular Earth parking orbit",
            "one impulsive departure burn from Earth parking orbit",
            "finite vehicle propulsion reduced to ideal total-delta-v and TWR checks",
            "Sun, Earth, and Moon modeled as point-mass gravitating bodies",
            "Moon encounter means crossing the Laplace sphere of influence, not capture or landing",
            "no launch-site, atmosphere, staging, guidance, or finite-burn model",
        ),
    )

    if analysis.twr <= 1.0:
        reasons.append("Vehicle TWR is not greater than 1.0 for Earth ascent.")
    if available_tli <= 0.0:
        reasons.append(
            "Insufficient vehicle delta-v after the 9.40 km/s Earth-ascent allowance."
        )
    if analysis.thrust <= 0.0:
        reasons.append("No usable engine thrust is installed.")
    if reasons:
        return MissionSimulationResult(
            **empty_result,
            tli_delta_v=0.0 * u.m / u.s,
            reasons=tuple(reasons),
        )

    moon_spline, sun_spline = _make_ephemeris_splines(
        departure,
        float(flight_seconds),
    )
    empty_result["data_source"] = "JPL DE440s + JPL lunar physical constants"
    moon_departure = moon_spline(0.0)
    moon_arrival = moon_spline(flight_seconds)
    earth_mu = EARTH_MU
    circular_speed = np.sqrt(earth_mu / orbit_radius)

    # Assume the parking orbit is coplanar with the lunar orbit and select its
    # phase so the transfer begins about 180 degrees behind the Moon's arrival
    # position. This is a phase-aligned departure assumption, not launch-site
    # or launch-window optimization.
    lunar_normal = np.cross(moon_departure, moon_arrival)
    normal_length = np.linalg.norm(lunar_normal)
    if normal_length < 1e-12:
        raise RuntimeError("Could not determine lunar orbital plane from ephemeris")
    lunar_normal /= normal_length
    moon_departure_direction = moon_departure / np.linalg.norm(moon_departure)
    moon_arrival_direction = moon_arrival / np.linalg.norm(moon_arrival)
    lunar_advance = np.arctan2(
        np.dot(lunar_normal, np.cross(moon_departure_direction, moon_arrival_direction)),
        np.dot(moon_departure_direction, moon_arrival_direction),
    )
    # Avoid the singular exactly-180-degree Lambert geometry while retaining
    # a near-Hohmann transfer arc; launch phase is treated as selectable.
    transfer_arc_angle = np.deg2rad(179.0)
    phase_angle = lunar_advance - transfer_arc_angle
    parking_direction = (
        moon_departure_direction * np.cos(phase_angle)
        + np.cross(lunar_normal, moon_departure_direction) * np.sin(phase_angle)
        + lunar_normal
        * np.dot(lunar_normal, moon_departure_direction)
        * (1.0 - np.cos(phase_angle))
    )
    departure_radius = orbit_radius * parking_direction
    circular_velocity = circular_speed * np.cross(lunar_normal, parking_direction)
    departure_velocity, _arrival_velocity = lambert_universal(
        departure_radius,
        moon_arrival,
        float(flight_seconds),
        earth_mu,
        prograde=lunar_normal[2] >= 0.0,
    )
    tli_required = float(np.linalg.norm(departure_velocity - circular_velocity))
    if tli_required > available_tli:
        reasons.append(
            "Lambert transfer injection exceeds vehicle delta-v remaining after "
            f"Earth ascent ({tli_required / 1000:.2f} km/s required, "
            f"{available_tli / 1000:.2f} km/s available)."
        )
        return MissionSimulationResult(
            **empty_result,
            tli_delta_v=tli_required * u.m / u.s,
            reasons=tuple(reasons),
        )

    initial_velocity = departure_velocity

    def acceleration(time_seconds: float, position: np.ndarray) -> np.ndarray:
        earth_acceleration = -earth_mu * position / np.linalg.norm(position) ** 3
        moon_position = moon_spline(time_seconds)
        moon_relative = moon_position - position
        moon_acceleration = MOON_MU * (
            moon_relative / np.linalg.norm(moon_relative) ** 3
            - moon_position / np.linalg.norm(moon_position) ** 3
        )
        sun_position = sun_spline(time_seconds)
        sun_relative = sun_position - position
        sun_acceleration = SUN_MU * (
            sun_relative / np.linalg.norm(sun_relative) ** 3
            - sun_position / np.linalg.norm(sun_position) ** 3
        )
        return earth_acceleration + moon_acceleration + sun_acceleration

    def equations(time_seconds: float, state: np.ndarray) -> np.ndarray:
        position = state[:3]
        velocity = state[3:]
        return np.concatenate((velocity, acceleration(time_seconds, position)))

    def moon_distance_event(time_seconds: float, state: np.ndarray) -> float:
        return float(np.linalg.norm(state[:3] - moon_spline(time_seconds)) - soi_radius.to_value(u.m))

    moon_distance_event.terminal = False
    moon_distance_event.direction = 0

    solution = solve_ivp(
        equations,
        (0.0, float(flight_seconds)),
        np.concatenate((departure_radius, initial_velocity)),
        method="DOP853",
        dense_output=True,
        events=moon_distance_event,
        max_step=max_step,
        rtol=rtol,
        atol=atol,
    )
    if not solution.success:
        reasons.append(f"Trajectory integration failed: {solution.message}")
        return MissionSimulationResult(
            **empty_result,
            tli_delta_v=tli_required * u.m / u.s,
            reasons=tuple(reasons),
        )

    evaluation_times = np.linspace(0.0, float(flight_seconds), 5000)
    trajectory = solution.sol(evaluation_times)[:3].T
    moon_positions = moon_spline(evaluation_times)
    distances = np.linalg.norm(trajectory - moon_positions, axis=1)
    nearest_index = int(np.argmin(distances))
    lower_index = max(0, nearest_index - 1)
    upper_index = min(len(evaluation_times) - 1, nearest_index + 1)
    if lower_index == upper_index:
        closest_distance = float(distances[nearest_index])
    else:
        closest_time = minimize_scalar(
            lambda seconds: float(
                np.linalg.norm(
                    solution.sol(seconds)[:3] - moon_spline(seconds)
                )
            ),
            bounds=(evaluation_times[lower_index], evaluation_times[upper_index]),
            method="bounded",
            options={"xatol": 1e-3},
        )
        closest_distance = float(closest_time.fun)
    closest_approach = closest_distance * u.m
    success = closest_approach <= soi_radius
    surface_impact = closest_distance <= MOON_RADIUS_M
    if not success:
        reasons.append(
            "Propagated trajectory never entered the Moon's Laplace sphere of influence."
        )

    return MissionSimulationResult(
        **{
            **empty_result,
            "simulated": True,
            "success": bool(success),
            "surface_impact": bool(surface_impact),
            "closest_approach": closest_approach.to(u.km),
            "trajectory_points": len(evaluation_times),
        },
        tli_delta_v=tli_required * u.m / u.s,
        reasons=tuple(reasons),
    )
