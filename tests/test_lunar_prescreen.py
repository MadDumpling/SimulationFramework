"""The lunar mission check shown in the panel must agree with the simulation's pre-check."""

import types

import pytest

import spacecraft.mission as mission
import ui.spacecraft_designer as designer_module
from core.event_bus import EventBus
from spacecraft import analyze_spacecraft
from spacecraft.components import Engine, FuelTank, component_from_catalog
from spacecraft.demo_designs import build_lunar_demo
from spacecraft.vehicle import Spacecraft
from ui import mission_outcome as o
from ui.spacecraft_designer import SpacecraftDesignerUI


def vehicle(fuel_tonnes, engines, thrust=845_000.0):
    craft = Spacecraft("Grid design")
    for _ in range(engines):
        engine = component_from_catalog("engine")
        engine.thrust = thrust
        craft.add_component(engine)
    tank = component_from_catalog("fuel_tank")
    tank.capacity = tank.fuel_mass = fuel_tonnes * 1000.0
    craft.add_component(tank)
    craft.add_component(component_from_catalog("payload"))
    return craft


class ReachedEphemeris(Exception):
    """Raised by the stand-in ephemeris: the vehicle pre-check passed."""


@pytest.fixture
def simulation_passes_precheck(monkeypatch):
    """Whether the real simulation lets a design through its vehicle pre-check."""

    def raise_reached(*args, **kwargs):
        raise ReachedEphemeris

    monkeypatch.setattr(mission, "_make_ephemeris_splines", raise_reached)

    def passes(craft):
        try:
            result = mission.run_lunar_flyby_simulation(craft, "2030-01-01")
        except ReachedEphemeris:
            return True
        assert result.simulated is False  # stopped by the pre-check
        return False

    return passes


# -- the readout --------------------------------------------------------------


def test_ready_design_says_so():
    check = o.lunar_prescreen(analyze_spacecraft(build_lunar_demo()))

    assert check.ready and check.liftoff_ok and check.delta_v_ok
    assert check.summary.startswith("Ready") and check.hint == ""


def test_too_little_delta_v_is_explained():
    check = o.lunar_prescreen(analyze_spacecraft(vehicle(30, 1)))

    assert check.liftoff_ok and not check.delta_v_ok and not check.ready
    assert "falls short" in check.summary
    assert "raise thrust" in check.hint  # more propellant lowers thrust-to-weight


def test_too_heavy_to_lift_off_is_explained():
    check = o.lunar_prescreen(analyze_spacecraft(vehicle(300, 1)))

    assert not check.liftoff_ok and "will not lift off" in check.summary.lower()
    assert check.twr < 1.0
    assert "engines" in check.hint


def test_both_gates_failing_points_to_thrust_first():
    check = o.lunar_prescreen(analyze_spacecraft(vehicle(30, 1, thrust=50_000.0)))

    assert not check.liftoff_ok and not check.delta_v_ok
    assert "thrust" in check.hint and "then add propellant" in check.hint


def test_no_engine_cannot_lift_off():
    craft = Spacecraft("No engine")
    craft.add_component(component_from_catalog("fuel_tank"))

    check = o.lunar_prescreen(analyze_spacecraft(craft))

    assert not check.liftoff_ok and not check.ready


def test_panel_text_shows_both_numbers_and_requirements():
    text = o.prescreen_text(o.lunar_prescreen(analyze_spacecraft(vehicle(30, 1))))

    assert "thrust-to-weight" in text and "needs > 1.0" in text
    assert "needs about 12.6 km/s" in text and "[FAIL]" in text and "[OK]" in text
    assert len(text.splitlines()) == 4  # summary, two gates, hint


# -- agreement with the simulation ---------------------------------------------
#
# The simulation checks the vehicle in two steps: a cheap pre-check (thrust-to-weight
# above 1, and delta-v above the 9.4 km/s Earth ascent), then, once the ephemeris is
# loaded, that the Lambert transfer injection (~3.1 km/s) also fits. The panel models
# both, so it is never more lenient than the pre-check and is stricter exactly where the
# injection step would reject the design.

# Fuel (tonnes) x engine count with the default 845 kN catalog engine.
GRID = [
    (30, 1), (100, 1), (300, 1), (30, 2), (100, 2), (200, 2), (300, 3),
    (200, 3), (500, 5), (500, 8), (800, 8), (800, 12), (500, 12), (800, 20),
]


@pytest.mark.parametrize("fuel,engines", GRID)
def test_panel_never_promises_what_the_simulation_rejects(
    simulation_passes_precheck, fuel, engines
):
    craft = vehicle(fuel, engines)
    analysis = analyze_spacecraft(craft)
    check = o.lunar_prescreen(analysis)
    passes = simulation_passes_precheck(craft)

    if check.ready:
        assert passes, f"{fuel} t x {engines}: panel says ready but the pre-check rejects it"
    if not passes:
        assert not check.ready
    # The pre-check's two conditions, restated: both must hold for the simulation to go on.
    assert passes == (analysis.thrust > 0 and analysis.twr > 1.0 and analysis.delta_v > 9_400.0)


def test_panel_is_stricter_where_only_the_transfer_injection_would_fail(
    simulation_passes_precheck,
):
    # 20 engines + 800 t: lifts off with 12.06 km/s, which clears the pre-check
    # (> 9.4 km/s) but not the ~3.1 km/s injection that the simulation checks next
    # (it reports 3,132 m/s needed against 2,658 m/s left, as seen in a real run).
    craft = vehicle(800, 20)
    check = o.lunar_prescreen(analyze_spacecraft(craft))

    assert simulation_passes_precheck(craft)
    assert check.liftoff_ok and not check.delta_v_ok and not check.ready
    assert 9.4 < check.delta_v_kms < check.needed_kms


def test_panel_liftoff_gate_is_exactly_the_launch_check():
    for fuel, engines in GRID:
        analysis = analyze_spacecraft(vehicle(fuel, engines))
        assert o.lunar_prescreen(analysis).liftoff_ok == o.can_lift_off(analysis)[0]


def test_demo_design_clears_the_precheck_and_is_labelled_illustrative(simulation_passes_precheck):
    craft = build_lunar_demo()
    analysis = analyze_spacecraft(craft)

    assert simulation_passes_precheck(craft)
    assert analysis.twr > 1.0 and analysis.delta_v > 12_600.0
    assert all(part.provenance.quality == "illustrative" for part in craft.components)
    assert "Demonstration only" in next(
        p for p in craft.components if isinstance(p, FuelTank)
    ).provenance.notes
    assert any(isinstance(p, Engine) for p in craft.components)


def test_default_preset_clears_the_simulation_precheck_and_is_illustrative(
    simulation_passes_precheck,
):
    # The default opens as the lunar demo and must pass the same vehicle gates
    # that the trajectory simulation applies before it queries the ephemeris.
    from spacecraft.presets import load_spacecraft

    craft = load_spacecraft(designer_module.DEFAULT_PRESET)
    analysis = analyze_spacecraft(craft)

    assert craft.name.startswith("Lunar-capable demo")
    assert simulation_passes_precheck(craft)
    assert o.lunar_prescreen(analysis).ready
    assert analysis.twr > 1.0 and analysis.delta_v > 12_600.0
    assert all(part.provenance.quality == "illustrative" for part in craft.components)


# -- failure banner gives numbers -------------------------------------------------


def make_failed_result(have_ms=6_200.0, tli_ms=0.0):
    from astropy import units as u

    return types.SimpleNamespace(
        simulated=False,
        success=False,
        reasons=("Insufficient vehicle delta-v after the 9.40 km/s Earth-ascent allowance.",),
        closest_approach=None,
        lunar_sphere_of_influence=66_000.0 * u.km,
        available_delta_v=have_ms * u.m / u.s,
        tli_delta_v=tli_ms * u.m / u.s,
        required_earth_departure_delta_v=9_400.0 * u.m / u.s,
    )


def test_fall_banner_states_the_shortfall_in_numbers():
    text, color = o.verdict_banner(make_failed_result(), "fall")

    assert "cannot reach the Moon" in text and color == o.RED
    assert "6.2 km/s" in text and "12.6 km/s" in text


def test_fall_banner_uses_the_exact_transfer_delta_v_when_known():
    text, _ = o.verdict_banner(make_failed_result(have_ms=12_000.0, tli_ms=3_132.0), "fall")

    assert "12.0 km/s" in text and "12.5 km/s" in text  # 9.4 + 3.132


# -- designer: demo button and live readout -------------------------------------


def test_load_lunar_demo_replaces_the_design_and_updates_the_check(tmp_path):
    events = EventBus()
    selected, updated = [], []
    events.subscribe("component.selected", selected.append)
    events.subscribe("spacecraft.updated", updated.append)
    path = tmp_path / "design.json"
    ui = SpacecraftDesignerUI(events, preset_path=path)
    assert not o.lunar_prescreen(ui.analysis).ready  # the starter cannot go

    ui.load_lunar_demo()

    assert ui.spacecraft.name.startswith("Lunar-capable demo")
    assert ui.preset_path == path  # the save location is untouched
    assert ui.selected_id is None and selected == [None] and len(updated) == 1
    assert o.lunar_prescreen(ui.analysis).ready


def test_refresh_publishes_the_check_text_to_the_panel(tmp_path):
    ui = SpacecraftDesignerUI(EventBus(), preset_path=tmp_path / "design.json")
    ui.built = True
    designer_module.dpg.set_value.reset_mock()

    ui.refresh()
    shown = {call.args[0]: call.args[1] for call in designer_module.dpg.set_value.call_args_list}

    assert "spacecraft_lunar_check" in shown
    assert shown["spacecraft_lunar_check"] == o.prescreen_text(o.lunar_prescreen(ui.analysis))
    assert "falls short" in shown["spacecraft_lunar_check"]

    ui.load_lunar_demo()
    shown = {call.args[0]: call.args[1] for call in designer_module.dpg.set_value.call_args_list}
    assert shown["spacecraft_lunar_check"].startswith("Ready")
