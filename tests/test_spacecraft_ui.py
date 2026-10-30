from astropy import units as u

import ui.spacecraft_designer as designer_module
from core.event_bus import EventBus
from spacecraft.analysis import MISSION_PROFILES
from spacecraft.components import Engine, FuelTank, Payload
from spacecraft.mission import MissionSimulationResult
from spacecraft.placement import Placement
from spacecraft.presets import load_spacecraft
from ui.mission_outcome import lunar_mission_report
from ui.spacecraft_designer import (
    DEFAULT_PRESET,
    SHOWCASE_SCENARIOS,
    SpacecraftDesignerUI,
)


def test_default_preset_is_the_lunar_capable_demo():
    craft = load_spacecraft(DEFAULT_PRESET)

    assert craft.name == "Lunar-capable demo (illustrative)"
    assert {Engine, FuelTank, Payload} <= {type(part) for part in craft.components}
    assert {
        "LandingLeg",
        "RcsThruster",
        "SolarPanel",
        "Battery",
        "Avionics",
    } <= {type(part).__name__ for part in craft.components}


def test_loading_showcase_scenario_sets_preset_and_mission_inputs(monkeypatch):
    scenario_name = "Failure — insufficient TLI propellant"
    scenario = SHOWCASE_SCENARIOS[scenario_name]
    monkeypatch.setattr(
        designer_module.dpg,
        "get_value",
        lambda tag: scenario_name if tag == "lunar_demo_scenario" else None,
    )
    designer_module.dpg.set_value.reset_mock()
    ui = SpacecraftDesignerUI(EventBus())

    ui.load_demo_scenario()

    assert ui.spacecraft.name == "Failure demo — insufficient TLI propellant"
    set_values = {
        call.args[0]: call.args[1]
        for call in designer_module.dpg.set_value.call_args_list
    }
    assert set_values["lunar_departure_date"] == scenario["departure_date"]
    assert set_values["lunar_transfer_days"] == scenario["transfer_days"]
    assert "date-specific lunar injection" in set_values["lunar_reachability_details"]


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


def test_lunar_mission_report_explains_miss_with_run_metrics():
    ui = SpacecraftDesignerUI(EventBus())
    result = MissionSimulationResult(
        simulated=True,
        success=False,
        surface_impact=False,
        departure_time="2030-01-01T00:00:00.000",
        arrival_time="2030-01-06T00:00:00.000",
        transfer_time=5.0 * u.day,
        tli_delta_v=3.1 * u.km / u.s,
        required_earth_departure_delta_v=9.4 * u.km / u.s,
        available_delta_v=14.0 * u.km / u.s,
        closest_approach=80_000.0 * u.km,
        lunar_sphere_of_influence=66_000.0 * u.km,
        trajectory_points=5000,
        data_source="JPL DE440s",
        reasons=("Propagated trajectory never entered the lunar SOI.",),
        assumptions=("Phase-aligned parking orbit is assumed.",),
        closest_approach_time="2030-01-05T12:00:00.000",
    )

    report = lunar_mission_report(result, ui.analysis)

    assert "MISSION FAILED" in report
    assert "Initial thrust-to-weight:" in report
    assert "Ideal vehicle delta-v available: 14.000 km/s" in report
    assert "Delta-v after ascent allowance: +4.600 km/s" in report
    assert "Margin after TLI: +1.500 km/s" in report
    assert "Closest approach to Moon center: 80,000.0 km" in report
    assert "Closest-approach time (UTC): 2030-01-05T12:00:00.000" in report
    assert "Relative speed at closest approach: not available." in report
    assert "SOI margin: -14,000.0 km (outside the SOI boundary)" in report
    assert "Integrator: DOP853; max step 300 s" in report
    assert "stayed 14,000.0 km outside" in report
    assert "does not optimize a correction burn or launch window" in report
    assert "MODEL ASSUMPTIONS AND LIMITS" in report


def test_lunar_mission_report_shows_precheck_failure_and_negative_delta_v():
    ui = SpacecraftDesignerUI(EventBus())
    result = MissionSimulationResult(
        simulated=False,
        success=False,
        surface_impact=False,
        departure_time="2030-01-01T00:00:00.000",
        arrival_time="2030-01-06T00:00:00.000",
        transfer_time=5.0 * u.day,
        tli_delta_v=0.0 * u.km / u.s,
        required_earth_departure_delta_v=9.4 * u.km / u.s,
        available_delta_v=6.2 * u.km / u.s,
        closest_approach=None,
        lunar_sphere_of_influence=66_000.0 * u.km,
        trajectory_points=0,
        data_source="JPL DE440s not queried (vehicle precheck failed)",
        reasons=("Insufficient vehicle delta-v after the Earth-ascent allowance.",),
        assumptions=("Finite vehicle propulsion is reduced to ideal delta-v checks.",),
    )

    report = lunar_mission_report(result, ui.analysis)

    assert "NOT PROPAGATED" in report
    assert "Delta-v after ascent allowance: -3.200 km/s" in report
    assert "Required TLI: Not solved; vehicle pre-check stopped the run." in report
    assert "Margin after TLI: unavailable; TLI was not solved." in report
    assert "FAILURE REASONS" in report
    assert "Closest approach to Moon center: Not available" in report


def test_lunar_mission_report_explains_vehicle_fuel_warnings():
    ui = SpacecraftDesignerUI(EventBus())
    result = MissionSimulationResult(
        simulated=False,
        success=False,
        surface_impact=False,
        departure_time="2030-01-01T00:00:00.000",
        arrival_time="2030-01-06T00:00:00.000",
        transfer_time=5.0 * u.day,
        tli_delta_v=0.0 * u.km / u.s,
        required_earth_departure_delta_v=9.4 * u.km / u.s,
        available_delta_v=0.0 * u.km / u.s,
        closest_approach=None,
        lunar_sphere_of_influence=66_000.0 * u.km,
        trajectory_points=0,
        data_source="JPL DE440s not queried (vehicle precheck failed)",
        reasons=("Insufficient vehicle delta-v after the 9.40 km/s Earth-ascent allowance.",),
        vehicle_warnings=(
            "Some tank propellant does not match the installed engine fuel type.",
            "No propellant compatible with the installed engine is loaded.",
        ),
        assumptions=("No trajectory was propagated.",),
    )

    report = lunar_mission_report(result, ui.analysis)

    assert "FAILURE REASONS" in report
    assert "VEHICLE WARNINGS" in report
    assert "does not match the installed engine fuel type" in report
    assert "No propellant compatible with the installed engine is loaded" in report


def test_selection_is_published_and_cleared_when_part_removed(tmp_path):
    events = EventBus()
    selected = []
    events.subscribe("component.selected", selected.append)
    ui = SpacecraftDesignerUI(events, preset_path=tmp_path / "design.json")
    target = ui.spacecraft.components[0]

    ui.select_component(target.id)
    ui.select_component("not-a-component")
    ui.remove_component(None, None, target.id)

    assert selected == [target.id, None]
    assert ui.selected_id is None


def test_adding_a_component_selects_it(tmp_path):
    events = EventBus()
    ui = SpacecraftDesignerUI(events, preset_path=tmp_path / "design.json")

    ui.add_component(None, None, "engine")

    assert ui.selected_id == ui.spacecraft.components[-1].id


def test_placement_editor_supports_offsets_and_node_attachments(tmp_path):
    ui = SpacecraftDesignerUI(EventBus(), preset_path=tmp_path / "design.json")
    engine = next(c for c in ui.spacecraft.components if isinstance(c, Engine))
    tank = next(c for c in ui.spacecraft.components if isinstance(c, FuelTank))
    attach_label = f"Attach to {tank.name} [{tank.id[:8]}]"
    label_to_mode = {
        "Automatic layout": "auto",
        "Free placement": "root",
        attach_label: tank.id,
    }

    ui.set_component_placement_mode(
        None,
        attach_label,
        (engine.id, label_to_mode),
    )
    ui.set_component_placement_value(
        None,
        0.75,
        (engine.id, "offset_x"),
    )
    ui.set_component_placement_value(
        None,
        "mount",
        (engine.id, "parent_node"),
    )

    assert engine.placement.parent_id == tank.id
    assert engine.placement.offset == (0.75, 0.0, 0.0)
    assert engine.placement.parent_node == "mount"


def test_placement_editor_rejects_attachment_cycles(tmp_path):
    ui = SpacecraftDesignerUI(EventBus(), preset_path=tmp_path / "design.json")
    engine = next(c for c in ui.spacecraft.components if isinstance(c, Engine))
    tank = next(c for c in ui.spacecraft.components if isinstance(c, FuelTank))
    tank.placement = Placement(parent_id=engine.id)
    attach_label = f"Attach to {tank.name} [{tank.id[:8]}]"

    ui.set_component_placement_mode(
        None,
        attach_label,
        (engine.id, {attach_label: tank.id}),
    )

    assert engine.placement is None


def test_engine_throttle_range_is_editable_as_percent(tmp_path):
    ui = SpacecraftDesignerUI(EventBus(), preset_path=tmp_path / "design.json")
    engine = next(c for c in ui.spacecraft.components if isinstance(c, Engine))

    ui.update_component("sender", 10.0, (engine.id, "throttle_min_fraction"))
    ui.update_component("sender", 100.0, (engine.id, "throttle_max_fraction"))

    assert engine.throttle.min_fraction == 0.1
    assert engine.throttle.max_fraction == 1.0


def test_component_name_and_com_location_are_editable(tmp_path):
    ui = SpacecraftDesignerUI(EventBus(), preset_path=tmp_path / "design.json")
    engine = next(c for c in ui.spacecraft.components if isinstance(c, Engine))

    ui.rename_component("sender", "Main engine", engine.id)
    ui.set_component_com_defined("sender", True, engine.id)
    ui.set_component_com_value("sender", 1.25, (engine.id, "x"))

    assert engine.name == "Main engine"
    assert engine.com_m == (1.25, 0.0, 0.0)


def test_duplicate_copies_properties_with_a_new_id(tmp_path):
    ui = SpacecraftDesignerUI(EventBus(), preset_path=tmp_path / "design.json")
    original = next(c for c in ui.spacecraft.components if isinstance(c, Engine))
    count = len(ui.spacecraft.components)

    ui.duplicate_component(None, None, original.id)

    copy = ui.spacecraft.components[-1]
    assert len(ui.spacecraft.components) == count + 1
    assert copy.id != original.id
    assert (copy.thrust, copy.isp) == (original.thrust, original.isp)
    assert ui.selected_id == copy.id


def test_view_controls_publish_events():
    events = EventBus()
    seen = []
    events.subscribe("view.explode", lambda v: seen.append(("explode", v)))
    events.subscribe("view.grid", lambda v: seen.append(("grid", v)))
    events.subscribe("view.reset_camera", lambda: seen.append(("reset", None)))
    ui = SpacecraftDesignerUI(events)

    ui.set_explode(None, 0.5, None)
    ui.set_grid(None, False, None)
    ui.reset_camera()

    assert seen == [("explode", 0.5), ("grid", False), ("reset", None)]


def test_data_quality_and_source_edits_validate_provenance(tmp_path):
    ui = SpacecraftDesignerUI(EventBus(), preset_path=tmp_path / "design.json")
    engine = next(c for c in ui.spacecraft.components if isinstance(c, Engine))

    ui.set_data_quality(None, "published", engine.id)  # no source yet: rejected
    assert engine.provenance.quality != "published"

    ui.set_data_source(None, "Datasheet X rev B", engine.id)
    ui.set_data_quality(None, "published", engine.id)
    assert engine.provenance.quality == "published"
    assert engine.provenance.source == "Datasheet X rev B"


def test_stage_edit_updates_component(tmp_path):
    ui = SpacecraftDesignerUI(EventBus(), preset_path=tmp_path / "design.json")
    tank = next(c for c in ui.spacecraft.components if isinstance(c, FuelTank))

    ui.set_stage(None, 2, tank.id)

    assert tank.stage == 2


def test_residual_propellant_edit_changes_usable_propellant(tmp_path):
    ui = SpacecraftDesignerUI(EventBus(), preset_path=tmp_path / "design.json")
    tank = next(c for c in ui.spacecraft.components if isinstance(c, FuelTank))
    before = ui.analysis.fuel_mass

    ui.update_component("sender", 500.0, (tank.id, "residual_propellant"))

    assert tank.residual_propellant == 500.0
    assert ui.analysis.fuel_mass == before - 500.0


def test_new_subsystem_properties_can_be_edited_and_placement_reset(tmp_path):
    ui = SpacecraftDesignerUI(EventBus(), preset_path=tmp_path / "design.json")
    ui.clear()

    ui.add_component(None, None, "landing_leg")
    gear = ui.spacecraft.components[-1]
    ui.update_component("leg_count", 6, (gear.id, "leg_count"))
    ui.update_component("rated_load", 12_000.0, (gear.id, "rated_load_n"))
    ui.set_component_placement_value(
        "offset", 4.0, (gear.id, "offset_x")
    )
    assert gear.leg_count == 6
    assert gear.rated_load_n == 12_000.0
    assert gear.placement.offset[0] == 4.0

    ui.reset_component_placement(None, None, gear.id)

    assert gear.placement is None


def test_analysis_panel_reports_auxiliary_thrust_and_power_surplus():
    ui = SpacecraftDesignerUI(EventBus())
    ui.clear()
    ui.add_component(None, None, "rcs_thruster")
    ui.add_component(None, None, "solar_panel")
    ui.add_component(None, None, "avionics")
    ui.built = True
    designer_module.dpg.set_value.reset_mock()

    ui.refresh()

    values = {
        call.args[0]: call.args[1]
        for call in designer_module.dpg.set_value.call_args_list
    }
    assert values["spacecraft_rcs_thrust"].startswith("RCS thrust: 1,800.0 N")
    assert "+2.05 kW surplus" in values["spacecraft_power"]


def test_mirror_copy_reflects_placement_and_selects_the_copy(tmp_path):
    ui = SpacecraftDesignerUI(EventBus(), preset_path=tmp_path / "design.json")
    engine = next(part for part in ui.spacecraft.components if isinstance(part, Engine))
    engine.placement = Placement(
        offset=(2.0, 3.0, 4.0),
        rotation_deg=(10.0, 20.0, 30.0),
    )

    ui.mirror_component(None, None, (engine.id, "x"))

    copy = ui.spacecraft.components[-1]
    assert copy.id != engine.id
    assert copy.placement.offset == (-2.0, 3.0, 4.0)
    assert copy.placement.rotation_deg == engine.placement.rotation_deg
    assert copy.placement.symmetry_group == engine.id
    assert ui.selected_id == copy.id


def test_load_apollo_lm_replaces_design_without_changing_save_path(tmp_path):
    events = EventBus()
    selected = []
    events.subscribe("component.selected", selected.append)
    path = tmp_path / "design.json"
    ui = SpacecraftDesignerUI(events, preset_path=path)

    ui.load_apollo_lm()

    assert ui.spacecraft.name.startswith("Apollo Lunar Module")
    assert ui.preset_path == path
    assert ui.selected_id is None and selected == [None]
    assert ui.analysis.fuel_mass == 7_295.0
