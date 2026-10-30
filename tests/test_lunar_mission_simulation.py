import math

import numpy as np
from astropy import units as u
from scipy.interpolate import CubicSpline

from spacecraft.components import Engine, FuelTank, Payload
from spacecraft.mission import (
    MissionSimulationResult,
    lambert_universal,
    run_lunar_flyby_simulation,
)
from spacecraft.vehicle import Spacecraft


def test_lambert_solver_recovers_quarter_circular_orbit():
    radius = 7_000_000.0
    mu = 3.986004e14
    speed = math.sqrt(mu / radius)
    period = 2.0 * math.pi * math.sqrt(radius**3 / mu)
    r1 = np.array([radius, 0.0, 0.0])
    r2 = np.array([0.0, radius, 0.0])

    v1, v2 = lambert_universal(r1, r2, period / 4.0, mu)

    np.testing.assert_allclose(v1, [0.0, speed, 0.0], rtol=2e-7, atol=1e-5)
    np.testing.assert_allclose(v2, [-speed, 0.0, 0.0], rtol=2e-7, atol=1e-5)


def test_simulation_propagates_vehicle_and_reports_moon_encounter(monkeypatch):
    import spacecraft.mission as mission

    def fake_ephemerides(departure, duration_seconds, samples=1000):
        times = np.linspace(0.0, duration_seconds, samples)
        moon_positions = np.column_stack(
            [384_400_000.0 + times * 0.0, times * 1_022.0, times * 0.0]
        )
        sun_positions = np.column_stack(
            [np.full(samples, 149_597_870_700.0), np.zeros(samples), np.zeros(samples)]
        )
        return (
            CubicSpline(times, moon_positions, axis=0),
            CubicSpline(times, sun_positions, axis=0),
        )

    monkeypatch.setattr(mission, "_make_ephemeris_splines", fake_ephemerides)
    craft = Spacecraft("Test lunar transfer")
    craft.add_component(
        Engine(
            name="Test engine",
            dry_mass=1_000.0,
            thrust=20_000_000.0,
            isp=450.0,
            fuel_type="test propellant",
        )
    )
    craft.add_component(
        FuelTank(
            name="Test tank",
            dry_mass=1_000.0,
            capacity=1_000_000.0,
            fuel_mass=1_000_000.0,
            fuel_type="test propellant",
        )
    )
    craft.add_component(Payload(name="Test payload", dry_mass=100.0))

    result = run_lunar_flyby_simulation(
        craft,
        departure_time="2024-01-01T00:00:00",
        transfer_time=5 * u.day,
        max_step=600.0,
    )

    assert isinstance(result, MissionSimulationResult)
    assert result.simulated is True
    assert result.trajectory_points > 10
    assert result.tli_delta_v > 0.0 * u.m / u.s
    assert result.closest_approach > 0.0 * u.km
    assert result.closest_approach_time is not None
    assert result.closest_approach_time.startswith("2024-01-")
    assert result.relative_speed_at_closest_approach_mps is not None
    assert result.relative_speed_at_closest_approach_mps > 0.0
    assert result.integrator == "DOP853"
    assert result.integration_max_step_s == 600.0
    assert result.surface_impact == (
        result.closest_approach <= mission.MOON_RADIUS_M * u.m
    )
    assert result.data_source.startswith("JPL DE440s")
    assert result.success == (
        result.closest_approach <= result.lunar_sphere_of_influence
    )


def test_simulation_refuses_lunar_claim_without_sufficient_vehicle_delta_v(monkeypatch):
    import spacecraft.mission as mission

    def fail_if_called(*args, **kwargs):
        raise AssertionError("trajectory propagation must not run")

    monkeypatch.setattr(mission, "_make_ephemeris_splines", fail_if_called)
    craft = Spacecraft("Underpowered")
    craft.add_component(
        Engine(
            name="Small engine",
            dry_mass=100.0,
            thrust=10_000.0,
            isp=100.0,
            fuel_type="test propellant",
        )
    )
    craft.add_component(
        FuelTank(
            name="Small tank",
            dry_mass=100.0,
            capacity=10.0,
            fuel_mass=10.0,
            fuel_type="test propellant",
        )
    )
    craft.add_component(Payload(name="Payload", dry_mass=100.0))

    result = run_lunar_flyby_simulation(
        craft,
        departure_time="2024-01-01T00:00:00",
        transfer_time=5 * u.day,
    )

    assert result.simulated is False
    assert result.success is False
    assert result.closest_approach is None
    assert result.data_source.startswith("JPL DE440s not queried")
    assert any("Earth-ascent" in reason for reason in result.reasons)
