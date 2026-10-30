from astropy import units as u

from spacecraft.mission import MissionSimulationResult
from ui.mission_outcome import mission_timeline


def test_flyby_timeline_never_claims_safe_landing():
    result = MissionSimulationResult(
        simulated=True,
        success=True,
        surface_impact=False,
        departure_time="2024-01-01",
        arrival_time="2024-01-06",
        transfer_time=5 * u.day,
        tli_delta_v=3.1 * u.km / u.s,
        required_earth_departure_delta_v=9.4 * u.km / u.s,
        available_delta_v=14 * u.km / u.s,
        closest_approach=10_000 * u.km,
        lunar_sphere_of_influence=66_000 * u.km,
        trajectory_points=100,
        data_source="JPL DE440s",
        reasons=(),
        assumptions=(),
    )

    timeline = mission_timeline(result)

    assert timeline[-1].state == "FAILED"
    assert timeline[-1].label != "SAFE LANDING"
    assert timeline[-1].reason == "Moon encounter is not a landing simulation."


def test_unrun_mission_timeline_is_ready():
    timeline = mission_timeline(None)

    assert timeline[0].state == "READY"
    assert timeline[-1].label == "Touchdown"


def test_running_mission_timeline_shows_simulation_progress():
    timeline = mission_timeline(None, running=True)

    assert timeline[0].state == "SIMULATING"
    assert all(milestone.state == "PENDING" for milestone in timeline[1:])
