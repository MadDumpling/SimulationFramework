from astropy import units as u

from core.event_bus import EventBus
from spacecraft.analysis import MISSION_PROFILES
from spacecraft.components import Engine, FuelTank, Payload, PowerSystem
from spacecraft.presets import load_spacecraft
from ui.spacecraft_designer import DEFAULT_PRESET, SpacecraftDesignerUI
import ui.spacecraft_designer as designer_module
from spacecraft.mission import MissionSimulationResult


def test_starter_preset_contains_first_mvp_component_categories():
    craft = load_spacecraft(DEFAULT_PRESET)

    assert craft.name == "Chemical Explorer Concept"
    assert [type(part) for part in craft.components] == [
        Engine,
        FuelTank,
        Payload,
        PowerSystem,
    ]


def test_designer_callbacks_add_remove_parts_and_publish_events(tmp_path):
    events = EventBus()
    added = []
    removed = []
    events.subscribe("component.added", added.append)
    events.subscribe("component.removed", removed.append)
    ui = SpacecraftDesignerUI(events, preset_path=tmp_path / "design.json")
    ui.clear()

    ui.add_component(None, None, "engine")
    engine = ui.spacecraft.components[0]
    ui.add_component(None, None, "fuel_tank")
    ui.remove_component(None, None, engine.id)

    assert len(added) == 2
    assert removed == [engine.id]
    assert len(ui.spacecraft.components) == 1
    assert ui.analysis.delta_v == 0.0


def test_mission_selection_updates_selected_profile():
    ui = SpacecraftDesignerUI(EventBus())

    ui.select_mission(None, MISSION_PROFILES["mars_transfer"].name, None)

    assert ui.mission_id == "mars_transfer"


def test_lunar_mission_callback_runs_trajectory_and_reports_result(monkeypatch):
    ui = SpacecraftDesignerUI(EventBus())
    result = MissionSimulationResult(
        simulated=True,
        success=True,
        surface_impact=False,
        departure_time="2030-01-01T00:00:00.000",
        arrival_time="2030-01-06T00:00:00.000",
        transfer_time=5.0 * u.day,
        tli_delta_v=3.1 * u.km / u.s,
        required_earth_departure_delta_v=9.4 * u.km / u.s,
        available_delta_v=14.0 * u.km / u.s,
        closest_approach=10_000.0 * u.km,
        lunar_sphere_of_influence=66_000.0 * u.km,
        trajectory_points=5000,
        data_source="JPL DE440s",
        reasons=(),
        assumptions=(),
    )
    calls = []
    monkeypatch.setattr(
        designer_module,
        "run_lunar_flyby_simulation",
        lambda craft, departure, transfer_time: (
            calls.append((craft, departure, transfer_time)) or result
        ),
    )
    monkeypatch.setattr(designer_module.dpg, "get_value", lambda tag: {
        "lunar_departure_date": "2030-01-01",
        "lunar_transfer_days": 5.0,
    }[tag])

    ui.run_lunar_mission()

    assert calls[0][0] is ui.spacecraft
    assert calls[0][1] == "2030-01-01"
    assert calls[0][2] == 5.0 * u.day
    assert ui.mission_result is result

    ui._invalidate_mission_result(None, 6.0, None)

    assert ui.mission_result is None
