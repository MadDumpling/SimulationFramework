"""DearPyGui spacecraft configurator panel for the 3D OpenGL viewport."""

import threading
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import dearpygui.dearpygui as dpg
from astropy import units as u

from spacecraft.analysis import (
    MISSION_PROFILES,
    analyze_spacecraft,
    assess_mission,
)
from spacecraft.apollo_lm import PRESET_PATH as APOLLO_LM_PRESET
from spacecraft.components import (
    Avionics,
    Battery,
    Component,
    Engine,
    FuelTank,
    LandingLeg,
    PowerSystem,
    RcsThruster,
    SolarPanel,
    component_from_catalog,
    component_from_dict,
    component_to_dict,
)
from spacecraft.demo_designs import build_lunar_demo
from spacecraft.geometry import component_centers
from spacecraft.mass_properties import mass_properties
from spacecraft.mission import MissionSimulationResult, run_lunar_flyby_simulation
from spacecraft.placement import NODE_BOTTOM, NODE_NAMES, NODE_TOP, Placement
from spacecraft.presets import load_spacecraft, save_spacecraft
from spacecraft.provenance import QUALITIES
from spacecraft.readiness import assess_definition
from spacecraft.vehicle import Spacecraft

from .mission_outcome import (
    can_lift_off,
    apollo11_reference_report,
    apollo11_reference_summary,
    lunar_mission_report,
    lunar_prescreen,
    prescreen_text,
)
from .mission_timeline import mission_timeline

DEFAULT_PRESET = (
    Path(__file__).resolve().parents[1]
    / "presets"
    / "spacecraft"
    / "lunar_demo.json"
)
SHOWCASE_SCENARIOS = {
    "Lunar encounter — no surface impact": {
        "preset": "lunar_demo.json",
        "departure_date": "2026-10-30",
        "transfer_days": 6.0,
        "description": (
            "Reference encounter: the propagated path enters the lunar SOI without "
            "intersecting the mean-radius surface in this run."
        ),
    },
    "Lunar encounter — surface impact estimate": {
        "preset": "lunar_demo.json",
        "departure_date": "2026-10-30",
        "transfer_days": 5.0,
        "description": (
            "Same vehicle, different transfer time: this modeled path enters the lunar "
            "SOI and intersects the mean-radius surface. Impact is not a safe landing."
        ),
    },
    "Failure — insufficient lift-off thrust": {
        "preset": "lunar_low_thrust.json",
        "departure_date": "2026-10-30",
        "transfer_days": 5.0,
        "description": "Good ideal delta-v cannot compensate for TWR below 1.0.",
    },
    "Failure — insufficient Earth-ascent delta-v": {
        "preset": "lunar_ascent_shortfall.json",
        "departure_date": "2026-10-30",
        "transfer_days": 5.0,
        "description": "The design has thrust, but its ideal delta-v is below the 9.4 km/s ascent allowance.",
    },
    "Failure — insufficient TLI propellant": {
        "preset": "lunar_tli_shortfall.json",
        "departure_date": "2026-10-30",
        "transfer_days": 5.0,
        "description": "It clears the initial ascent check but cannot pay the date-specific lunar injection burn.",
    },
    "Failure — engine/tank propellant mismatch": {
        "preset": "lunar_propellant_mismatch.json",
        "departure_date": "2026-10-30",
        "transfer_days": 5.0,
        "description": "The tank is full, but none of its propellant is compatible with the engine.",
    },
}


class _MissionRun:
    """One background mission run; the worker stores ``outcome`` last when done."""

    def __init__(self, serial: int):
        self.serial = serial
        self.outcome = None  # (result, error) once finished


class SpacecraftDesignerUI:
    """Editable vehicle assembly, analysis, persistence, and mission launch UI."""

    SELECTED_COLOR = (255, 160, 40)

    def __init__(self, events, preset_path=DEFAULT_PRESET):
        self.events = events
        self.preset_path = Path(preset_path)
        self.spacecraft = self._load_starting_spacecraft()
        self.mission_id = "leo"
        self.analysis = analyze_spacecraft(self.spacecraft)
        self.mission_result: MissionSimulationResult | None = None
        self.selected_id: str | None = None
        # The app sets this so the viewport keeps animating during the (slow) run.
        self.background_missions = False
        self._mission_run: _MissionRun | None = None
        self._mission_serial = 0
        self.built = False

    def _load_starting_spacecraft(self):
        if self.preset_path.exists():
            return load_spacecraft(self.preset_path)
        craft = Spacecraft("Untitled spacecraft")
        for catalog_id in ("engine", "fuel_tank", "payload"):
            craft.add_component(component_from_catalog(catalog_id))
        return craft

    def build(self):
        with dpg.window(
            label="Spacecraft Designer",
            tag="spacecraft_designer_window",
            pos=(0, 28),
            width=520,
            height=1025,
        ):
            dpg.add_text(
                "SPACECRAFT CONFIGURATOR",
                color=(175, 190, 210),
            )
            dpg.add_input_text(
                label="Vehicle name",
                default_value=self.spacecraft.name,
                callback=self._rename_spacecraft,
                on_enter=True,
                tag="spacecraft_name_input",
            )
            with dpg.group(horizontal=True):
                dpg.add_button(label="Load Apollo LM", callback=self.load_apollo_lm)
                dpg.add_button(label="Save", callback=self.save)
                dpg.add_button(label="Load", callback=self.load)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Lunar Demo", callback=self.load_lunar_demo)
                dpg.add_button(label="Clear Assembly", callback=self.clear)

            with dpg.tab_bar(tag="designer_tabs"):
                with dpg.tab(label="Design"):
                    dpg.add_text("Add component")
                    with dpg.group(horizontal=True):
                        for label, catalog_id in (
                            ("Engine", "engine"),
                            ("Tank", "fuel_tank"),
                            ("Payload", "payload"),
                            ("Power", "power_system"),
                        ):
                            dpg.add_button(
                                label=f"+ {label}",
                                callback=self.add_component,
                                user_data=catalog_id,
                            )
                    dpg.add_text("Landing and spacecraft subsystems")
                    with dpg.group(horizontal=True):
                        for label, catalog_id in (
                            ("Landing gear", "landing_leg"),
                            ("RCS", "rcs_thruster"),
                            ("Solar panel", "solar_panel"),
                        ):
                            dpg.add_button(
                                label=f"+ {label}",
                                callback=self.add_component,
                                user_data=catalog_id,
                            )
                    with dpg.group(horizontal=True):
                        for label, catalog_id in (
                            ("Battery", "battery"),
                            ("Avionics", "avionics"),
                        ):
                            dpg.add_button(
                                label=f"+ {label}",
                                callback=self.add_component,
                                user_data=catalog_id,
                            )
                    dpg.add_text("Viewport controls", bullet=True)
                    dpg.add_slider_float(
                        label="Exploded view",
                        default_value=0.0,
                        min_value=0.0,
                        max_value=1.0,
                        width=440,
                        callback=self.set_explode,
                    )
                    with dpg.group(horizontal=True):
                        dpg.add_checkbox(
                            label="Grid",
                            default_value=True,
                            callback=self.set_grid,
                        )
                        dpg.add_button(label="Reset Camera", callback=self.reset_camera)
                        dpg.add_button(label="Reset Flight", callback=self.reset_flight)
                    dpg.add_text(
                        "Click a part in the viewport or select it below. "
                        "Position edits update the 3D view immediately.",
                        color=(175, 190, 210),
                        wrap=460,
                    )
                    dpg.add_separator()
                    dpg.add_text("Assembly")
                    dpg.add_group(tag="spacecraft_components_container")
                    dpg.add_separator()
                    dpg.add_text("Selected component inspector", bullet=True)
                    dpg.add_group(tag="spacecraft_component_inspector")
                    dpg.add_text(
                        "",
                        tag="spacecraft_data_message",
                        wrap=460,
                        color=(255, 120, 100),
                    )

                with dpg.tab(label="Analysis"):
                    dpg.add_text("Vehicle performance", bullet=True)
                    for label, tag in (
                        ("Dry mass: 0 kg", "spacecraft_dry_mass"),
                        ("Fuel mass: 0 kg", "spacecraft_fuel_mass"),
                        ("Wet mass: 0 kg", "spacecraft_wet_mass"),
                        ("Thrust: 0 kN", "spacecraft_thrust"),
                        ("RCS thrust: 0 N (auxiliary)", "spacecraft_rcs_thrust"),
                        ("Delta-v: 0 m/s", "spacecraft_delta_v"),
                        ("TWR: 0.00", "spacecraft_twr"),
                        ("Burn time: 0 s", "spacecraft_burn_time"),
                        ("Power: 0.00 kW generation / 0.00 kW load", "spacecraft_power"),
                    ):
                        dpg.add_text(label, tag=tag)
                    dpg.add_text("", tag="spacecraft_com", wrap=460)
                    dpg.add_text("", tag="spacecraft_tip_over", wrap=460)
                    dpg.add_text("", tag="spacecraft_stability_warning", wrap=460)
                    with dpg.plot(
                        label="Mass by component",
                        height=260,
                        width=-1,
                        tag="spacecraft_mass_plot",
                    ):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(
                            dpg.mvXAxis,
                            label="Component",
                            tag="spacecraft_mass_x_axis",
                        )
                        with dpg.plot_axis(
                            dpg.mvYAxis,
                            label="Mass (kg)",
                            tag="spacecraft_mass_y_axis",
                        ):
                            dpg.add_bar_series(
                                [0.0], [0.0], label="Dry mass", weight=0.36,
                                tag="spacecraft_mass_dry_series",
                            )
                            dpg.add_bar_series(
                                [0.4], [0.0], label="Propellant", weight=0.36,
                                tag="spacecraft_mass_fuel_series",
                            )
                    with dpg.plot(
                        label="Delta-v vs mission budget",
                        height=260,
                        width=-1,
                        tag="spacecraft_delta_v_plot",
                    ):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(
                            dpg.mvXAxis,
                            label="Mission",
                            tag="spacecraft_delta_v_x_axis",
                        )
                        with dpg.plot_axis(
                            dpg.mvYAxis,
                            label="Delta-v (m/s)",
                            tag="spacecraft_delta_v_y_axis",
                        ):
                            dpg.add_bar_series(
                                [-0.18], [0.0], label="Available", weight=0.36,
                                tag="spacecraft_delta_v_available_series",
                            )
                            dpg.add_bar_series(
                                [0.18], [0.0], label="Required", weight=0.36,
                                tag="spacecraft_delta_v_required_series",
                            )
                    dpg.add_text("Mission assessment", bullet=True)
                    dpg.add_text("", tag="spacecraft_mission_status", wrap=460)
                    dpg.add_text("", tag="spacecraft_warnings", wrap=460)
                    dpg.add_text("Lunar mission check (single-stage screening)", bullet=True)
                    dpg.add_text("", tag="spacecraft_lunar_check", wrap=460)
                    dpg.add_text("Vehicle data readiness", bullet=True)
                    dpg.add_text("", tag="spacecraft_data_readiness", wrap=460)
                with dpg.tab(label="Mission"):
                    dpg.add_text("Lunar mission screening · JPL DE440s", bullet=True)
                    dpg.add_text(
                        apollo11_reference_summary(),
                        color=(175, 190, 210),
                        tag="apollo11_reference_summary",
                    )
                    with dpg.collapsing_header(
                        label="Apollo 11 historical reference · AS-506",
                        default_open=False,
                    ):
                        dpg.add_text(
                            apollo11_reference_report(),
                            tag="apollo11_reference_report",
                            wrap=460,
                        )
                    dpg.add_separator()
                    dpg.add_combo(
                        items=list(SHOWCASE_SCENARIOS),
                        default_value=next(iter(SHOWCASE_SCENARIOS)),
                        label="Demo scenario",
                        width=440,
                        tag="lunar_demo_scenario",
                    )
                    dpg.add_button(
                        label="Load demo scenario",
                        callback=self.load_demo_scenario,
                    )
                    dpg.add_text(
                        "Loads a spacecraft preset and sets the example departure "
                        "date and transfer time.",
                        color=(175, 190, 210),
                        wrap=460,
                    )
                    dpg.add_combo(
                        items=[profile.name for profile in MISSION_PROFILES.values()],
                        default_value=MISSION_PROFILES[self.mission_id].name,
                        label="Mission target",
                        callback=self.select_mission,
                        tag="spacecraft_mission_combo",
                    )
                    dpg.add_input_text(
                        label="Departure date (UTC)",
                        default_value=datetime.now(timezone.utc).date().isoformat(),
                        callback=self._invalidate_mission_result,
                        tag="lunar_departure_date",
                        width=300,
                    )
                    dpg.add_input_float(
                        label="Transfer time (days)",
                        default_value=5.0,
                        min_value=3.0,
                        max_value=8.0,
                        min_clamped=True,
                        max_clamped=True,
                        width=300,
                        callback=self._invalidate_mission_result,
                        tag="lunar_transfer_days",
                    )
                    dpg.add_button(
                        label="Run Lunar Mission Simulation",
                        callback=self.run_lunar_mission,
                    )
                    dpg.add_text(
                        "A successful result means lunar sphere-of-influence entry, "
                        "not capture or landing.",
                        wrap=460,
                        color=(175, 190, 210),
                    )
                    dpg.add_text(
                        "READY",
                        tag="lunar_reachability_status",
                        wrap=460,
                    )
                    dpg.add_text(
                        "",
                        tag="lunar_reachability_details",
                        wrap=460,
                        color=(195, 205, 220),
                    )
                    dpg.add_separator()
                    dpg.add_text("Mission timeline", bullet=True)
                    dpg.add_group(tag="lunar_timeline_container")

        self.built = True
        self._rebuild_component_controls()
        self.refresh()
        self._refresh_mission_timeline()

    def add_component(self, sender, app_data, user_data):
        component = component_from_catalog(user_data)
        self.spacecraft.add_component(component)
        self.events.publish("component.added", component)
        self.events.publish("spacecraft.updated", self.spacecraft)
        self._invalidate_mission_result()
        self._rebuild_component_controls()
        self.select_component(component.id)
        self.refresh()

    def select_component(self, component_id):
        """Select a component and synchronize its viewport highlight."""
        if component_id is not None and self.spacecraft.get_component(component_id) is None:
            component_id = None
        if component_id == self.selected_id:
            return
        self.selected_id = component_id
        self._rebuild_component_controls()
        self.events.publish("component.selected", component_id)

    def select_component_callback(self, sender, app_data, user_data):
        self.select_component(user_data)

    def _apply_selection_style(self):
        if not self.built:
            return
        for component in self.spacecraft.components:
            tag = f"spacecraft_component_select_{component.id}"
            if dpg.does_item_exist(tag):
                dpg.configure_item(
                    tag,
                    default_value=component.id == self.selected_id,
                )

    def duplicate_component(self, sender, app_data, user_data):
        original = self.spacecraft.get_component(user_data)
        if original is None:
            return
        data = component_to_dict(original)
        data["id"] = str(uuid4())
        duplicate = component_from_dict(data)
        self.spacecraft.add_component(duplicate)
        self.events.publish("component.added", duplicate)
        self.events.publish("spacecraft.updated", self.spacecraft)
        self._invalidate_mission_result()
        self._rebuild_component_controls()
        self.select_component(duplicate.id)
        self.refresh()

    def set_explode(self, sender, app_data, user_data):
        self.events.publish("view.explode", float(app_data))

    def set_grid(self, sender, app_data, user_data):
        self.events.publish("view.grid", bool(app_data))

    def reset_camera(self, sender=None, app_data=None, user_data=None):
        self.events.publish("view.reset_camera")

    def reset_flight(self, sender=None, app_data=None, user_data=None):
        self._cancel_mission()
        self.events.publish("flight.reset")

    def remove_component(self, sender, app_data, user_data):
        if not self.spacecraft.remove_component(user_data):
            return
        if self.selected_id == user_data:
            self.select_component(None)
        self.events.publish("component.removed", user_data)
        self.events.publish("spacecraft.updated", self.spacecraft)
        self._invalidate_mission_result()
        self._rebuild_component_controls()
        self.refresh()

    def _rebuild_component_controls(self):
        if self.spacecraft.get_component(self.selected_id) is None:
            self.selected_id = None
        if not self.built:
            return
        dpg.delete_item("spacecraft_components_container", children_only=True)
        for component in self.spacecraft.components:
            with dpg.group(horizontal=True, parent="spacecraft_components_container"):
                dpg.add_selectable(
                    label=component.name,
                    default_value=component.id == self.selected_id,
                    callback=self.select_component_callback,
                    user_data=component.id,
                    tag=f"spacecraft_component_select_{component.id}",
                )
                dpg.add_text(
                    f"{component.dry_mass:,.1f} kg",
                )
                dpg.add_button(
                    label="Duplicate",
                    callback=self.duplicate_component,
                    user_data=component.id,
                    small=True,
                )
                dpg.add_button(
                    label="Remove",
                    callback=self.remove_component,
                    user_data=component.id,
                    small=True,
                )
        dpg.delete_item("spacecraft_component_inspector", children_only=True)
        component = self.spacecraft.get_component(self.selected_id)
        if component is None:
            dpg.add_text(
                "Select a component in the list or directly in the 3D viewport.",
                parent="spacecraft_component_inspector",
                color=(150, 165, 185),
                wrap=450,
            )
        else:
            dpg.add_text(
                component.name,
                parent="spacecraft_component_inspector",
                color=self.SELECTED_COLOR,
            )
            dpg.add_input_text(
                label="Component name",
                default_value=component.name,
                width=300,
                parent="spacecraft_component_inspector",
                callback=self.rename_component,
                on_enter=True,
                user_data=component.id,
            )
            for field_name, label, minimum, maximum in self._editable_fields(component):
                options = {
                    "label": label,
                    "default_value": getattr(component, field_name) or 0.0,
                    "min_value": minimum,
                    "min_clamped": True,
                    "width": 300,
                    "parent": "spacecraft_component_inspector",
                    "callback": self.update_component,
                    "user_data": (component.id, field_name),
                    "on_enter": True,
                    "tag": f"spacecraft_{component.id}_{field_name}",
                }
                if maximum is not None:
                    options["max_value"] = maximum
                    options["max_clamped"] = True
                dpg.add_input_float(**options)
            self._add_placement_controls(component)
            self._add_com_controls(component)
            self._add_definition_controls(component)
        self._apply_selection_style()

    @staticmethod
    def _editable_fields(component: Component):
        fields = [("dry_mass", "Dry mass (kg)", 0.0, None)]
        if isinstance(component, Engine):
            fields.extend(
                [
                    ("thrust", "Thrust (N)", 0.001, None),
                    ("isp", "Specific impulse (s)", 0.001, None),
                    ("power_draw_kw", "Power draw (kW)", 0.0, None),
                ]
            )
        elif isinstance(component, FuelTank):
            fields.extend(
                [
                    ("capacity", "Tank capacity (kg)", component.fuel_mass, None),
                    ("fuel_mass", "Loaded propellant (kg)", 0.0, component.capacity),
                    ("residual_propellant", "Residual propellant (kg)", 0.0, None),
                ]
            )
        elif isinstance(component, PowerSystem):
            fields.extend(
                [
                    ("generation_kw", "Power generation (kW)", 0.0, None),
                    ("storage_kwh", "Energy storage (kWh)", 0.0, None),
                ]
            )
        elif isinstance(component, LandingLeg):
            fields.extend(
                [
                    ("leg_length_m", "Leg length (m)", 0.001, None),
                    ("footprint_radius_m", "Footprint radius (m)", 0.001, None),
                    ("footpad_radius_m", "Footpad radius (m)", 0.001, None),
                    ("rated_load_n", "Rated load (N; 0 = unknown)", 0.0, None),
                ]
            )
        elif isinstance(component, RcsThruster):
            fields.extend(
                [
                    ("thrust_n", "Thrust per thruster (N)", 0.001, None),
                    ("isp_s", "Specific impulse (s)", 0.001, None),
                    (
                        "minimum_impulse_bit_ns",
                        "Minimum impulse bit (N·s; 0 = unknown)",
                        0.0,
                        None,
                    ),
                    ("power_draw_kw", "Power draw (kW)", 0.0, None),
                ]
            )
        elif isinstance(component, SolarPanel):
            fields.extend(
                [
                    ("area_m2", "Deployed area (m²)", 0.001, None),
                    ("generation_kw", "Rated generation (kW)", 0.0, None),
                ]
            )
        elif isinstance(component, Battery):
            fields.extend(
                [
                    ("capacity_kwh", "Energy capacity (kWh)", 0.0, None),
                    ("max_charge_kw", "Maximum charge power (kW)", 0.0, None),
                    ("max_discharge_kw", "Maximum discharge power (kW)", 0.0, None),
                ]
            )
        elif isinstance(component, Avionics):
            fields.append(("power_draw_kw", "Power draw (kW)", 0.0, None))
        return fields

    def _add_definition_controls(self, component):
        """Stage, data-quality, and source inputs for one component."""
        parent = "spacecraft_component_inspector"
        dpg.add_input_int(
            label="Stage",
            default_value=component.stage,
            min_value=1,
            min_clamped=True,
            width=120,
            parent=parent,
            callback=self.set_stage,
            user_data=component.id,
        )
        dpg.add_combo(
            items=list(QUALITIES),
            default_value=component.provenance.quality,
            label="Data quality",
            width=160,
            parent=parent,
            callback=self.set_data_quality,
            user_data=component.id,
            tag=f"spacecraft_{component.id}_quality",
        )
        dpg.add_input_text(
            label="Data source / revision",
            default_value=component.provenance.source,
            width=300,
            parent=parent,
            on_enter=True,
            callback=self.set_data_source,
            user_data=component.id,
            tag=f"spacecraft_{component.id}_source",
        )
        if isinstance(component, Engine):
            dpg.add_input_float(
                label="Minimum throttle (%)",
                default_value=(component.throttle.min_fraction or 0.0) * 100.0,
                min_value=0.0,
                min_clamped=True,
                width=300,
                parent=parent,
                callback=self.update_component,
                user_data=(component.id, "throttle_min_fraction"),
                tag=f"spacecraft_{component.id}_throttle_min",
            )
            dpg.add_input_float(
                label="Maximum throttle (%)",
                default_value=(component.throttle.max_fraction or 0.0) * 100.0,
                min_value=0.0,
                min_clamped=True,
                width=300,
                parent=parent,
                callback=self.update_component,
                user_data=(component.id, "throttle_max_fraction"),
                tag=f"spacecraft_{component.id}_throttle_max",
            )
        integer_fields = ()
        if isinstance(component, LandingLeg):
            integer_fields = (("leg_count", "Number of legs", 3, 12),)
        elif isinstance(component, RcsThruster):
            integer_fields = (("thruster_count", "Number of thrusters", 1, 32),)
        elif isinstance(component, Avionics):
            integer_fields = (("redundancy", "Redundant systems", 1, None),)
        for field_name, label, minimum, maximum in integer_fields:
            options = {
                "label": label,
                "default_value": getattr(component, field_name),
                "min_value": minimum,
                "min_clamped": True,
                "width": 220,
                "parent": parent,
                "callback": self.update_component,
                "user_data": (component.id, field_name),
            }
            if maximum is not None:
                options["max_value"] = maximum
                options["max_clamped"] = True
            dpg.add_input_int(**options)
    def _add_placement_controls(self, component):
        labels = {"auto": "Automatic layout", "root": "Free placement"}
        parent_by_label = {}
        for candidate in self.spacecraft.components:
            if candidate.id == component.id:
                continue
            label = f"Attach to {candidate.name} [{candidate.id[:8]}]"
            labels[candidate.id] = label
            parent_by_label[label] = candidate.id
        current = component.placement
        if current is None:
            default_mode = labels["auto"]
        elif current.parent_id is None:
            default_mode = labels["root"]
        else:
            default_mode = labels.get(current.parent_id, labels["auto"])
        label_to_mode = {
            labels["auto"]: "auto",
            labels["root"]: "root",
            **parent_by_label,
        }
        parent = "spacecraft_component_inspector"
        dpg.add_combo(
            items=list(label_to_mode),
            default_value=default_mode,
            label="Placement",
            width=300,
            parent=parent,
            callback=self.set_component_placement_mode,
            user_data=(component.id, label_to_mode),
            tag=f"spacecraft_{component.id}_placement_mode",
        )
        dpg.add_text(
            "XYZ offsets are metres in the vehicle frame for free parts, or the "
            "parent frame for attached parts. Rotations use local Euler XYZ degrees.",
            parent=parent,
            color=(150, 165, 185),
            wrap=450,
        )
        with dpg.group(horizontal=True, parent=parent):
            dpg.add_button(
                label="Return to automatic layout",
                callback=self.reset_component_placement,
                user_data=component.id,
            )
            dpg.add_button(
                label="Reset rotation",
                callback=self.reset_component_rotation,
                user_data=component.id,
            )
        position = (
            current.offset
            if current is not None
            else self._component_visual_center(component.id)
        )
        with dpg.group(horizontal=True, parent=parent):
            for axis, value in zip("xyz", position):
                dpg.add_input_float(
                    label=f"{axis.upper()} (m)",
                    default_value=value,
                    width=130,
                    parent=parent,
                    callback=self.set_component_placement_value,
                    user_data=(component.id, f"offset_{axis}"),
                    tag=f"spacecraft_{component.id}_position_{axis}",
                )
        rotation = current.rotation_deg if current is not None else (0.0, 0.0, 0.0)
        with dpg.group(horizontal=True, parent=parent):
            for axis, value in zip("xyz", rotation):
                dpg.add_input_float(
                    label=f"R{axis.upper()} (deg)",
                    default_value=value,
                    width=130,
                    parent=parent,
                    callback=self.set_component_placement_value,
                    user_data=(component.id, f"rotation_{axis}"),
                    tag=f"spacecraft_{component.id}_rotation_{axis}",
                )
        if current is not None and current.parent_id is not None:
            dpg.add_combo(
                items=list(NODE_NAMES),
                default_value=current.parent_node,
                label="Parent node",
                width=200,
                parent=parent,
                callback=self.set_component_placement_value,
                user_data=(component.id, "parent_node"),
            )
            dpg.add_combo(
                items=list(NODE_NAMES),
                default_value=current.node,
                label="Part node",
                width=200,
                parent=parent,
                callback=self.set_component_placement_value,
                user_data=(component.id, "node"),
            )
            dpg.add_input_float(
                label="Attachment angle (deg)",
                default_value=current.angle_deg,
                width=300,
                parent=parent,
                callback=self.set_component_placement_value,
                user_data=(component.id, "angle_deg"),
            )
        with dpg.group(horizontal=True, parent=parent):
            dpg.add_button(
                label="Mirror copy X",
                callback=self.mirror_component,
                user_data=(component.id, "x"),
            )
            dpg.add_button(
                label="Mirror copy Z",
                callback=self.mirror_component,
                user_data=(component.id, "z"),
            )

    def _add_com_controls(self, component):
        parent = "spacecraft_component_inspector"
        dpg.add_checkbox(
            label="COM position known",
            default_value=component.com_m is not None,
            parent=parent,
            callback=self.set_component_com_defined,
            user_data=component.id,
        )
        if component.com_m is None:
            dpg.add_text(
                "Unknown COM data is not estimated. Enable this only when you "
                "can provide the part's automatic-layout vehicle coordinates; "
                "enabling starts at (0, 0, 0). Known COM values follow placements.",
                parent=parent,
                color=(150, 165, 185),
                wrap=450,
            )
            return
        with dpg.group(horizontal=True, parent=parent):
            for axis, value in zip("xyz", component.com_m):
                dpg.add_input_float(
                    label=f"COM {axis.upper()} (m)",
                    default_value=value,
                    width=130,
                    callback=self.set_component_com_value,
                    user_data=(component.id, axis),
                    tag=f"spacecraft_{component.id}_com_{axis}",
                )

    def _component_visual_center(self, component_id):
        center = component_centers(self.spacecraft).get(component_id)
        if center is None:
            return (0.0, 0.0, 0.0)
        return tuple(float(value) for value in center)

    def set_component_placement_mode(self, sender, app_data, user_data):
        component_id, label_to_mode = user_data
        component = self.spacecraft.get_component(component_id)
        if component is None:
            return
        mode = label_to_mode.get(app_data)
        if mode == "auto":
            component.placement = None
        elif mode == "root":
            component.placement = Placement(
                offset=self._component_visual_center(component_id)
            )
        elif mode is not None:
            if self._would_create_attachment_cycle(component_id, mode):
                self._set_data_message("That attachment would create a placement cycle.")
                self._rebuild_component_controls()
                return
            component.placement = Placement(
                parent_id=mode,
                parent_node=NODE_TOP,
                node=NODE_BOTTOM,
            )
        else:
            return
        self._set_data_message("")
        self._placement_changed()
        self._rebuild_component_controls()

    def reset_component_placement(self, sender, app_data, user_data):
        component = self.spacecraft.get_component(user_data)
        if component is None:
            return
        component.placement = None
        self._placement_changed()
        self._rebuild_component_controls()

    def reset_component_rotation(self, sender, app_data, user_data):
        component = self.spacecraft.get_component(user_data)
        if component is None:
            return
        placement = component.placement or Placement(
            offset=self._component_visual_center(component.id)
        )
        component.placement = replace(placement, rotation_deg=(0.0, 0.0, 0.0))
        self._placement_changed()
        self._rebuild_component_controls()

    def mirror_component(self, sender, app_data, user_data):
        component_id, axis_name = user_data
        original = self.spacecraft.get_component(component_id)
        if original is None:
            return
        axis = "xyz".index(axis_name)
        data = component_to_dict(original)
        data["id"] = str(uuid4())
        duplicate = component_from_dict(data)
        placement = original.placement or Placement(
            offset=self._component_visual_center(component_id)
        )
        offset = list(placement.offset)
        offset[axis] *= -1.0
        angle = placement.angle_deg
        if axis_name == "x":
            angle = 180.0 - angle
        else:
            angle = -angle
        symmetry_group = placement.symmetry_group or original.id
        duplicate.placement = replace(
            placement,
            offset=tuple(offset),
            angle_deg=angle,
            symmetry_group=symmetry_group,
        )
        duplicate.name = f"{original.name} mirrored {axis_name.upper()}"
        self.spacecraft.add_component(duplicate)
        self.events.publish("component.added", duplicate)
        self.events.publish("spacecraft.updated", self.spacecraft)
        self._placement_changed()
        self.select_component(duplicate.id)

    def _would_create_attachment_cycle(self, component_id, parent_id):
        current_id = parent_id
        while current_id is not None:
            if current_id == component_id:
                return True
            current = self.spacecraft.get_component(current_id)
            if current is None or current.placement is None:
                return False
            current_id = current.placement.parent_id
        return False

    def set_component_placement_value(self, sender, app_data, user_data):
        component_id, field_name = user_data
        component = self.spacecraft.get_component(component_id)
        if component is None:
            return
        was_automatic = component.placement is None
        placement = component.placement or Placement(
            offset=self._component_visual_center(component_id)
        )
        changes = {}
        if field_name.startswith("offset_"):
            axis = "xyz".index(field_name[-1])
            offset = list(placement.offset)
            offset[axis] = float(app_data)
            changes["offset"] = tuple(offset)
        elif field_name.startswith("rotation_"):
            axis = "xyz".index(field_name[-1])
            rotation = list(placement.rotation_deg)
            rotation[axis] = float(app_data)
            changes["rotation_deg"] = tuple(rotation)
        else:
            changes[field_name] = app_data
        try:
            component.placement = replace(placement, **changes)
        except ValueError as error:
            self._set_data_message(str(error))
            self._rebuild_component_controls()
            return
        self._set_data_message("")
        self._placement_changed()
        if was_automatic:
            self._rebuild_component_controls()

    def set_component_com_defined(self, sender, app_data, user_data):
        component = self.spacecraft.get_component(user_data)
        if component is None:
            return
        component.com_m = (0.0, 0.0, 0.0) if app_data else None
        self._set_data_message("")
        self._placement_changed()
        self._rebuild_component_controls()

    def set_component_com_value(self, sender, app_data, user_data):
        component_id, axis_name = user_data
        component = self.spacecraft.get_component(component_id)
        if component is None or component.com_m is None:
            return
        axis = "xyz".index(axis_name)
        position = list(component.com_m)
        position[axis] = float(app_data)
        component.com_m = tuple(position)
        self._placement_changed()

    def rename_component(self, sender, app_data, user_data):
        component = self.spacecraft.get_component(user_data)
        if component is None:
            return
        name = str(app_data).strip()
        if not name:
            dpg.set_value(sender, component.name)
            return
        component.name = name
        self._placement_changed()
        self._rebuild_component_controls()

    def _placement_changed(self):
        self.events.publish("spacecraft.updated", self.spacecraft)
        self._invalidate_mission_result()
        self.refresh()

    def set_stage(self, sender, app_data, user_data):
        component = self.spacecraft.get_component(user_data)
        if component is None:
            return
        component.stage = max(1, int(app_data))
        self._invalidate_mission_result()
        self.refresh()

    def _update_provenance(self, component_id, **changes):
        component = self.spacecraft.get_component(component_id)
        if component is None:
            return
        try:
            component.provenance = replace(component.provenance, **changes)
        except ValueError as error:
            self._set_data_message(f"{component.name}: {error}")
            for key, tag in (
                ("quality", f"spacecraft_{component_id}_quality"),
                ("source", f"spacecraft_{component_id}_source"),
            ):
                if dpg.does_item_exist(tag):
                    dpg.set_value(tag, getattr(component.provenance, key))
            return
        self._set_data_message("")
        self.refresh()

    def set_data_quality(self, sender, app_data, user_data):
        self._update_provenance(user_data, quality=app_data)

    def set_data_source(self, sender, app_data, user_data):
        self._update_provenance(user_data, source=str(app_data).strip())

    @staticmethod
    def _set_data_message(message):
        if dpg.does_item_exist("spacecraft_data_message"):
            dpg.set_value("spacecraft_data_message", message)

    def update_component(self, sender, app_data, user_data):
        component_id, field_name = user_data
        component = self.spacecraft.get_component(component_id)
        if component is None:
            return
        if isinstance(component, Engine) and field_name in (
            "throttle_min_fraction",
            "throttle_max_fraction",
        ):
            throttle_field = field_name.removeprefix("throttle_")
            fraction = float(app_data) / 100.0 if float(app_data) > 0.0 else None
            old_fraction = getattr(component.throttle, throttle_field)
            try:
                component.throttle = replace(
                    component.throttle,
                    **{throttle_field: fraction},
                )
            except ValueError:
                dpg.set_value(sender, (old_fraction or 0.0) * 100.0)
                return
        else:
            old_value = getattr(component, field_name)
            integer_fields = {"leg_count", "thruster_count", "redundancy"}
            optional_fields = {"rated_load_n", "minimum_impulse_bit_ns"}
            entered_value = float(app_data)
            if field_name in optional_fields:
                new_value = entered_value if entered_value > 0.0 else None
            elif field_name in integer_fields:
                new_value = int(app_data)
            else:
                new_value = entered_value
            setattr(component, field_name, new_value)
            try:
                component.__post_init__()
            except (TypeError, ValueError):
                setattr(component, field_name, old_value)
                dpg.set_value(sender, old_value or 0.0)
                return
            if field_name in optional_fields and dpg.does_item_exist(sender):
                dpg.set_value(sender, new_value or 0.0)
        if field_name == "capacity":
            fuel_tag = f"spacecraft_{component.id}_fuel_mass"
            if dpg.does_item_exist(fuel_tag):
                dpg.configure_item(
                    fuel_tag,
                    max_value=component.capacity,
                    max_clamped=True,
                )
        self.events.publish("spacecraft.updated", self.spacecraft)
        self._invalidate_mission_result()
        self.refresh()

    def _rename_spacecraft(self, sender, app_data, user_data):
        name = str(app_data).strip()
        if not name:
            dpg.set_value(sender, self.spacecraft.name)
            return
        self.spacecraft.name = name
        self.events.publish("spacecraft.updated", self.spacecraft)
        self._invalidate_mission_result()
        self.refresh()

    def select_mission(self, sender, app_data, user_data):
        self.mission_id = next(
            (
                mission_id
                for mission_id, profile in MISSION_PROFILES.items()
                if profile.name == app_data
            ),
            "leo",
        )
        self.events.publish("mission.selected", MISSION_PROFILES[self.mission_id])
        self.refresh()

    def save(self, sender=None, app_data=None, user_data=None):
        save_spacecraft(self.spacecraft, self.preset_path)
        self.events.publish("spacecraft.saved", self.spacecraft, self.preset_path)

    def load(self, sender=None, app_data=None, user_data=None):
        if not self.preset_path.exists():
            return
        self.spacecraft = load_spacecraft(self.preset_path)
        self.select_component(None)
        self.events.publish("spacecraft.updated", self.spacecraft)
        self._rebuild_component_controls()
        self.refresh()

    def load_apollo_lm(self, sender=None, app_data=None, user_data=None):
        """Load the Apollo LM reference vehicle without changing the save path."""
        self._load_reference(load_spacecraft(APOLLO_LM_PRESET))

    def load_lunar_demo(self, sender=None, app_data=None, user_data=None):
        """Load an illustrative design that clears the lunar pre-screen."""
        self._load_reference(build_lunar_demo())

    def load_demo_scenario(self, sender=None, app_data=None, user_data=None):
        """Load a documented spacecraft and mission-input example."""
        scenario_name = str(app_data or dpg.get_value("lunar_demo_scenario"))
        scenario = SHOWCASE_SCENARIOS.get(scenario_name)
        if scenario is None:
            self._set_lunar_status(
                "Unknown demo scenario.",
                f"No showcase scenario is registered as {scenario_name!r}.",
            )
            return

        preset_path = DEFAULT_PRESET.parent / scenario["preset"]
        self._load_reference(load_spacecraft(preset_path))
        if dpg.does_item_exist("lunar_departure_date"):
            dpg.set_value("lunar_departure_date", scenario["departure_date"])
        if dpg.does_item_exist("lunar_transfer_days"):
            dpg.set_value("lunar_transfer_days", scenario["transfer_days"])
        self._set_lunar_status(
            f"DEMO SCENARIO READY — {scenario_name}",
            (
                f"{scenario['description']}\n"
                f"Preset: {preset_path.name} · "
                f"departure {scenario['departure_date']} · "
                f"transfer {scenario['transfer_days']:.1f} days.\n"
                "Select Run Lunar Mission Simulation to see the result."
            ),
        )

    def _load_reference(self, spacecraft):
        self.spacecraft = spacecraft
        self.selected_id = None
        self.events.publish("component.selected", None)
        self.events.publish("spacecraft.updated", self.spacecraft)
        self._invalidate_mission_result()
        self._rebuild_component_controls()
        self.refresh()
        self.events.publish("view.reset_camera")

    def clear(self, sender=None, app_data=None, user_data=None):
        self.spacecraft = Spacecraft(self.spacecraft.name)
        self.select_component(None)
        self.events.publish("spacecraft.updated", self.spacecraft)
        self._invalidate_mission_result()
        self._rebuild_component_controls()
        self.refresh()

    def run_lunar_mission(self, sender=None, app_data=None, user_data=None):
        departure_date = dpg.get_value("lunar_departure_date")
        transfer_days = dpg.get_value("lunar_transfer_days")
        if not str(departure_date).strip():
            self._set_lunar_status("Enter a departure date in UTC (YYYY-MM-DD).", "")
            return
        if self._mission_run is not None and self._mission_run.serial == self._mission_serial:
            return  # a run is already in progress
        self.mission_result = None  # a rerun starts clean; no stale result lingers
        self._set_lunar_status(
            "Mission simulation running…",
            "Downloading/reading JPL ephemeris and integrating the trajectory.",
        )
        liftoff, has_thrust = can_lift_off(self.analysis)
        self.events.publish("mission.started", liftoff, has_thrust)
        self._mission_serial += 1
        serial = self._mission_serial
        args = (self.spacecraft, departure_date, float(transfer_days))
        if not self.background_missions:
            self._finish_mission(serial, *self._compute_mission(*args))
            return

        run = _MissionRun(serial)

        self._refresh_mission_timeline(running=True)

        def work():
            try:
                outcome = self._compute_mission(*args)
            except BaseException as error:  # never leave the run unreported
                outcome = (None, error)
            run.outcome = outcome  # set last: marks completion

        self._mission_run = run
        threading.Thread(target=work, daemon=True).start()

    @staticmethod
    def _compute_mission(spacecraft, departure_date, transfer_days):
        """Run the simulation; returns (result, error). Safe to call off-thread."""
        try:
            return (
                run_lunar_flyby_simulation(
                    spacecraft,
                    departure_date,
                    transfer_time=transfer_days * u.day,
                ),
                None,
            )
        except Exception as error:
            return None, error

    @property
    def mission_running(self) -> bool:
        return self._mission_run is not None

    def poll_mission(self):
        """Apply a finished background run on the UI thread (call once per frame).

        Completion is signalled by the worker storing its outcome, not by thread
        liveness: a just-created thread reports not-alive until it has started.
        """
        run = self._mission_run
        if run is None or run.outcome is None:
            return
        self._mission_run = None
        self._finish_mission(run.serial, *run.outcome)

    def _cancel_mission(self):
        """Discard any run in progress; its result will never be applied."""
        self._mission_serial += 1
        if self._mission_run is not None:
            self._mission_run = None
            self._set_lunar_status(
                "Mission cancelled — run the simulation again.",
                "The run was stopped before it finished, so there is no result.",
            )
            self.events.publish("mission.cancelled")

    def _finish_mission(self, serial, result, error):
        if serial != self._mission_serial:
            # The design or inputs changed mid-run; the result no longer applies.
            self.events.publish("mission.cancelled")
            return
        if error is not None:
            self.mission_result = None
            self._set_lunar_status(
                "Simulation could not run.",
                f"{error}\nCheck the date, network, and JPL DE440s access.",
            )
            self.events.publish("mission.failed", error)
            return
        self.mission_result = result
        self.events.publish("mission.completed", result)
        self._display_mission_result(result)

    def _display_mission_result(self, result):
        if not result.simulated:
            title = "MISSION FAILED — vehicle/transfer constraints not met"
        elif result.success:
            title = "LUNAR ARRIVAL — propagated path reached the Moon"
            if result.surface_impact:
                title += " (surface impact predicted)"
        else:
            title = "MISSION FAILED — propagated path missed the Moon"
        self._set_lunar_status(title, lunar_mission_report(result, self.analysis))

    def _invalidate_mission_result(self, sender=None, app_data=None, user_data=None):
        self._cancel_mission()
        if self.mission_result is not None:
            self.mission_result = None
            self._set_lunar_status(
                "Design changed — run the mission simulation again.",
                "Previous trajectory result discarded because the spacecraft changed.",
            )

    def _set_lunar_status(self, status, details):
        if dpg.does_item_exist("lunar_reachability_status"):
            dpg.set_value("lunar_reachability_status", status)
        if dpg.does_item_exist("lunar_reachability_details"):
            dpg.set_value("lunar_reachability_details", details)
        self._refresh_mission_timeline()

    def _refresh_mission_timeline(self, running=False):
        container = "lunar_timeline_container"
        if not dpg.does_item_exist(container):
            return
        dpg.delete_item(container, children_only=True)
        colors = {
            "READY": (150, 165, 185),
            "PENDING": (120, 135, 155),
            "SCREENED": (100, 180, 255),
            "SIMULATING": (255, 190, 80),
            "REACHED": (100, 220, 150),
            "FAILED": (255, 105, 90),
        }
        for milestone in mission_timeline(
            self.mission_result,
            running=running or self.mission_running,
        ):
            dpg.add_text(
                f"{milestone.state:>10}   {milestone.label}"
                + (f" — {milestone.reason}" if milestone.reason else ""),
                parent=container,
                color=colors.get(milestone.state, (175, 190, 210)),
                wrap=460,
            )

    def _refresh_plots(self):
        components = self.spacecraft.components
        x = list(range(len(components)))
        labels = [component.name[:12] for component in components]
        dry_mass = [component.dry_mass for component in components]
        fuel_mass = [
            component.fuel_mass if isinstance(component, FuelTank) else 0.0
            for component in components
        ]
        if dpg.does_item_exist("spacecraft_mass_dry_series"):
            dpg.set_value(
                "spacecraft_mass_dry_series",
                [[value - 0.18 for value in x], dry_mass],
            )
            dpg.set_value(
                "spacecraft_mass_fuel_series",
                [[value + 0.18 for value in x], fuel_mass],
            )
            dpg.set_axis_ticks(
                "spacecraft_mass_x_axis",
                tuple((name, float(index)) for index, name in enumerate(labels)),
            )

        mission_x = list(range(len(MISSION_PROFILES)))
        mission_names = ["LEO", "GEO", "Moon", "Lunar orbit", "Mars"]
        available = [self.analysis.delta_v] * len(mission_x)
        required = [
            profile.required_delta_v for profile in MISSION_PROFILES.values()
        ]
        if dpg.does_item_exist("spacecraft_delta_v_available_series"):
            dpg.set_value(
                "spacecraft_delta_v_available_series",
                [[value - 0.18 for value in mission_x], available],
            )
            dpg.set_value(
                "spacecraft_delta_v_required_series",
                [[value + 0.18 for value in mission_x], required],
            )
            dpg.set_axis_ticks(
                "spacecraft_delta_v_x_axis",
                tuple(
                    (name, float(index))
                    for index, name in enumerate(mission_names)
                ),
            )

    def refresh(self):
        self.analysis = analyze_spacecraft(self.spacecraft)
        if not self.built:
            return
        analysis = self.analysis
        mission = assess_mission(analysis, MISSION_PROFILES[self.mission_id])
        properties = mass_properties(self.spacecraft)
        if properties.com_m is None:
            missing = ", ".join(properties.missing_com)
            com_text = (
                "Center of mass: unknown"
                + (f" · missing data: {missing}" if missing else "")
            )
        else:
            x, y, z = properties.com_m
            com_text = f"Center of mass: X {x:.2f} · Y {y:.2f} · Z {z:.2f} m"
        tip_over = self.spacecraft.tip_over_angle_deg()
        tip_text = (
            f"Static tip-over limit: {tip_over:.1f}°"
            if tip_over is not None
            else "Static tip-over limit: unavailable (gear or COM data incomplete)"
        )
        stability_warning = (
            "UNSTABLE LANDER — center of mass is outside the safe footprint."
            if tip_over is not None and tip_over <= 0.0
            else ""
        )
        values = {
            "spacecraft_dry_mass": f"Dry mass: {analysis.dry_mass:,.1f} kg",
            "spacecraft_fuel_mass": f"Fuel mass: {analysis.fuel_mass:,.1f} kg",
            "spacecraft_wet_mass": f"Wet mass: {analysis.wet_mass:,.1f} kg",
            "spacecraft_thrust": f"Thrust: {analysis.thrust / 1000:,.1f} kN",
            "spacecraft_rcs_thrust": (
                f"RCS thrust: {analysis.rcs_thrust_n:,.1f} N auxiliary "
                "(excluded from main-engine performance)"
            ),
            "spacecraft_delta_v": (
                f"Delta-v: {analysis.delta_v:,.0f} m/s · Isp {analysis.isp:.1f} s"
            ),
            "spacecraft_twr": f"TWR: {analysis.twr:.2f}",
            "spacecraft_burn_time": f"Burn time: {analysis.burn_time:,.1f} s",
            "spacecraft_power": (
                f"Power: {analysis.power_generation_kw:.2f} kW generation / "
                f"{analysis.power_draw_kw:.2f} kW load · "
                f"{analysis.power_surplus_kw:+.2f} kW surplus · "
                f"{analysis.power_storage_kwh:.2f} kWh storage · "
                f"+{analysis.power_max_charge_kw:.2f}/"
                f"-{analysis.power_max_discharge_kw:.2f} kW charge/discharge"
            ),
            "spacecraft_com": com_text,
            "spacecraft_tip_over": tip_text,
            "spacecraft_stability_warning": stability_warning,
            "spacecraft_mission_status": self._mission_text(mission),
            "spacecraft_warnings": "\n".join(analysis.warnings),
            "spacecraft_lunar_check": prescreen_text(lunar_prescreen(analysis)),
            "spacecraft_data_readiness": assess_definition(self.spacecraft).summary(),
        }
        for tag, value in values.items():
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)
        if dpg.does_item_exist("spacecraft_name_input"):
            dpg.set_value("spacecraft_name_input", self.spacecraft.name)
        if dpg.does_item_exist("spacecraft_mass_dry_series"):
            self._refresh_plots()
        self.events.publish("analysis.updated", analysis, mission)

    @staticmethod
    def _mission_text(mission):
        if mission.achievable:
            return (
                f"{mission.mission.name}: IDEAL BUDGET MET "
                f"({mission.delta_v_margin:,.0f} m/s margin)"
            )
        return f"{mission.mission.name}: NOT MET · " + " ".join(mission.reasons)