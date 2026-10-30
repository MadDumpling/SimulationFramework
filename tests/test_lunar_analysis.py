import numpy as np
import pytest
from astropy import units as u

from spacecraft.analysis import SpacecraftAnalysis
from spacecraft.lunar import (
    estimate_lunar_orbit_budget,
    lunar_mission_assessment,
)


def test_lunar_budget_uses_ephemeris_moon_state_and_real_units(monkeypatch):
    import spacecraft.lunar as lunar

    calls = []

    def fake_moon_state(epoch):
        calls.append(epoch)
        # A plausible Moon geocentric state in SI units.
        return (
            np.array([384_400_000.0, 0.0, 0.0]) * u.m,
            np.array([0.0, 1_022.0, 0.0]) * u.m / u.s,
        )

    monkeypatch.setattr(lunar, "_moon_geocentric_state", fake_moon_state)
    budget = estimate_lunar_orbit_budget("2024-01-01T00:00:00")

    assert len(calls) >= 2
    assert budget.moon_distance.to_value(u.km) == pytest.approx(384_400.0)
    assert 4.0 < budget.transfer_time.to_value(u.day) < 6.0
    assert 2.5 < budget.trans_lunar_injection.to_value(u.km / u.s) < 4.0
    assert 0.3 < budget.lunar_orbit_insertion.to_value(u.km / u.s) < 1.5
    assert budget.required_delta_v.to_value(u.km / u.s) == pytest.approx(
        budget.earth_ascent.to_value(u.km / u.s)
        + budget.trans_lunar_injection.to_value(u.km / u.s)
        + budget.lunar_orbit_insertion.to_value(u.km / u.s)
    )
    assert "JPL DE440s" in budget.data_source


def test_lunar_requirement_changes_with_real_moon_distance(monkeypatch):
    import spacecraft.lunar as lunar

    distance = 384_400_000.0

    def fake_moon_state(_epoch):
        return (
            np.array([distance, 0.0, 0.0]) * u.m,
            np.array([0.0, 1_022.0, 0.0]) * u.m / u.s,
        )

    monkeypatch.setattr(lunar, "_moon_geocentric_state", fake_moon_state)
    near_budget = estimate_lunar_orbit_budget("2024-01-01T00:00:00")
    distance = 405_500_000.0
    far_budget = estimate_lunar_orbit_budget("2024-01-01T00:00:00")

    assert far_budget.moon_distance > near_budget.moon_distance
    assert far_budget.required_delta_v != near_budget.required_delta_v


def test_lunar_assessment_reports_clear_yes_no_and_margin():
    import spacecraft.lunar as lunar

    budget = lunar.LunarOrbitBudget(
        departure_time="2030-01-01T00:00:00",
        arrival_time="2030-01-06T00:00:00",
        moon_distance=384_400 * u.km,
        transfer_time=5 * u.day,
        earth_ascent=9.4 * u.km / u.s,
        trans_lunar_injection=3.1 * u.km / u.s,
        lunar_orbit_insertion=0.8 * u.km / u.s,
        required_delta_v=13.3 * u.km / u.s,
        data_source="JPL DE440s",
        assumptions=(),
    )

    yes = lunar_mission_assessment(
        SpacecraftAnalysis(delta_v=14_000.0, twr=1.5),
        budget,
    )
    no = lunar_mission_assessment(
        SpacecraftAnalysis(delta_v=12_000.0, twr=1.5),
        budget,
    )

    assert yes.achievable is True
    assert yes.delta_v_margin.to_value(u.km / u.s) == pytest.approx(0.7)
    assert no.achievable is False
    assert any("shortfall" in reason.lower() for reason in no.reasons)
