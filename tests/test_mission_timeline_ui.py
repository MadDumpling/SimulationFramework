from astropy import units as u

from spacecraft.apollo11_reference import APOLLO_11_REFERENCE, format_elapsed_time
from spacecraft.mission import MissionSimulationResult
from ui.mission_outcome import (
    apollo11_reference_report,
    apollo11_reference_summary,
    mission_timeline,
)


def test_apollo11_reference_matches_published_launch_and_transfer_anchors():
    mission = APOLLO_11_REFERENCE

    assert mission.launch_date_utc == "1969-07-16"
    assert mission.launch_site == "Launch Complex 39A, Kennedy Space Center"
    assert mission.launch_azimuth_deg == 72.063
    assert mission.maximum_dynamic_pressure_time_s == 81.0
    assert mission.maximum_dynamic_pressure_pa == 34_725.243
    assert mission.s_ic_outboard_cutoff.elapsed_seconds == 160.819
    assert mission.s_ii_cutoff.elapsed_seconds == 551.384
    assert mission.s_ivb_first_burn_cutoff.altitude_m == 191_339.56
    assert mission.parking_orbit.geocentric_radius_m == 6_563_308.7
    assert mission.parking_orbit.inertial_velocity_m_s == 7_793.1014
    assert mission.tli.elapsed_seconds == 10_203.801
    assert mission.tli.inertial_velocity_m_s == 10_831.069
    assert all(
        earlier.elapsed_seconds <= later.elapsed_seconds
        for earlier, later in zip(mission.events, mission.events[1:])
    )
    assert mission.source_id == "NASA-CR-61291"
    assert "not raw telemetry" in mission.fidelity_note


def test_apollo11_reference_report_exposes_data_and_limits():
    report = apollo11_reference_report()

    assert "Launch Complex 39A" in report
    assert "80.604133° W" in report
    assert "event sequence predicted" in report
    assert "S-IC/S-II separation complete" in report
    assert "S-II/S-IVB separation complete" in report
    assert "STAGE CUTOFF CONDITIONS" in report
    assert "EARTH PARKING ORBIT" in report
    assert "TRANSLUNAR INJECTION" in report
    assert "10,831.069 m/s" in report
    assert "34,725 Pa" in report
    assert "NASA-CR-61291" in report
    assert "not raw telemetry" in report


def test_apollo11_reference_summary_highlights_launch_and_tli():
    summary = apollo11_reference_summary()

    assert "1969-07-16" in summary
    assert "LC-39A" in summary
    assert "T+02:50:03.80" in summary
    assert "10.831 km/s" in summary


def test_elapsed_time_uses_hundredths_and_elapsed_hours():
    assert format_elapsed_time(0.0) == "T+00:00:00.00"
    assert format_elapsed_time(160.819) == "T+00:02:40.82"
    assert format_elapsed_time(10_203.801) == "T+02:50:03.80"


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
