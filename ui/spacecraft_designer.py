"""DearPyGui spacecraft configurator panel for the 3D OpenGL viewport."""

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
from spacecraft.components import (
    Component,
    Engine,
    FuelTank,
    PowerSystem,
    component_from_catalog,
    component_from_dict,
    component_to_dict,
)
from spacecraft.mission import MissionSimulationResult, run_lunar_flyby_simulation
from spacecraft.apollo_lm import PRESET_PATH as APOLLO_LM_PRESET
from spacecraft.provenance import QUALITIES
from spacecraft.readiness import assess_definition
from spacecraft.presets import load_spacecraft, save_spacecraft
from spacecraft.vehicle import Spacecraft

DEFAULT_PRESET = (
    Path(__file__).resolve().parents[1]
    / "presets"
    / "spacecraft"
    / "spacecraft_mvp.json"
)


class SpacecraftDesignerUI:
    """Editable vehicle assembly, analysis, persistence, and mission launch UI."""

    SELECTED_COLOR = (255, 160, 40)
    NORMAL_COLOR = (255, 255, 255)

    def __init__(self, events, preset_path=DEFAULT_PRESET):
        self.events = events
        self.preset_path = Path(preset_path)
        self.spacecraft = self._load_starting_spacecraft()
        self.mission_id = "leo"
        self.analysis = analyze_spacecraft(self.spacecraft)
        self.mission_result: MissionSimulationResult | None = None
        self.selected_id: str | None = None
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
            width=640,
            height=900,
        ):
            dpg.add_text(
                "Ideal delta-v analysis · live 3D viewport",
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
                for label, catalog_id in (
                    ("Add Engine", "engine"),
                    ("Add Tank", "fuel_tank"),
                    ("Add Payload", "payload"),
                    ("Add Power", "power_system"),
                ):
                    dpg.add_button(
                        label=label,
                        callback=self.add_component,
                        user_data=catalog_id,
                    )
            with dpg.group(horizontal=True):
                dpg.add_button(label="Save Design", callback=self.save)
                dpg.add_button(label="Load Design", callback=self.load)
                dpg.add_button(label="Clear Assembly", callback=self.clear)
                dpg.add_button(label="Load Apollo LM", callback=self.load_apollo_lm)
            dpg.add_text("Viewport", bullet=True)
            dpg.add_slider_float(
                label="Exploded view",
                default_value=0.0,
                min_value=0.0,
                max_value=1.0,
                width=220,
                callback=self.set_explode,
            )
            with dpg.group(horizontal=True):
                dpg.add_checkbox(
                    label="Grid",
                    default_value=True,
                    callback=self.set_grid,
                )
                dpg.add_button(label="Reset Camera", callback=self.reset_camera)
            dpg.add_text(
                "Click a part in the 3D viewport to select it; F frames and R resets.",
                color=(175, 190, 210),
                wrap=560,
            )
            dpg.add_separator()
            dpg.add_text("Assembly Components (select in viewport)")
            dpg.add_group(tag="spacecraft_components_container")
            dpg.add_separator()
            dpg.add_combo(
                items=[profile.name for profile in MISSION_PROFILES.values()],
                default_value=MISSION_PROFILES[self.mission_id].name,
                label="Mission target",
                callback=self.select_mission,
                tag="spacecraft_mission_combo",
            )
            dpg.add_text("Analysis", bullet=True)
            dpg.add_text("Dry Mass: 0 kg", tag="spacecraft_dry_mass")
            dpg.add_text("Fuel Mass: 0 kg", tag="spacecraft_fuel_mass")
            dpg.add_text("Wet Mass: 0 kg", tag="spacecraft_wet_mass")
            dpg.add_text("Thrust: 0 kN", tag="spacecraft_thrust")
            dpg.add_text("Delta-v: 0 m/s", tag="spacecraft_delta_v")
            dpg.add_text("TWR: 0.00", tag="spacecraft_twr")
            dpg.add_text("Burn Time: 0 s", tag="spacecraft_burn_time")
            dpg.add_text(
                "Power: 0.00 kW generation / 0.00 kW load",
                tag="spacecraft_power",
            )
            dpg.add_text("Mission status", tag="spacecraft_mission_status")
            dpg.add_text("", tag="spacecraft_warnings", wrap=560)
            dpg.add_separator()
            dpg.add_text("Vehicle data readiness", bullet=True)
            dpg.add_text("", tag="spacecraft_data_readiness", wrap=560)
            dpg.add_text("", tag="spacecraft_data_message", wrap=560, color=(255, 120, 100))
            dpg.add_separator()
            dpg.add_text("Lunar mission screening · JPL DE440s", bullet=True)
            dpg.add_input_text(
                label="Departure date (UTC)",
                default_value=datetime.now(timezone.utc).date().isoformat(),
                callback=self._invalidate_mission_result,
                tag="lunar_departure_date",
                width=240,
            )
            dpg.add_input_float(
                label="Transfer time (days)",
                default_value=5.0,
                min_value=3.0,
                max_value=8.0,
                min_clamped=True,
                max_clamped=True,
                width=240,
                callback=self._invalidate_mission_result,
                tag="lunar_transfer_days",
            )
            dpg.add_button(
                label="Run Lunar Mission Simulation",
                callback=self.run_lunar_mission,
            )
            dpg.add_text(
                "Success currently means reaching the lunar sphere of influence; "
                "this is not capture or landing.",
                wrap=560,
                color=(175, 190, 210),
            )
            dpg.add_text("Not simulated", tag="lunar_reachability_status", wrap=560)
            dpg.add_text("", tag="lunar_reachability_details", wrap=560)

        self.built = True
        self._rebuild_component_controls()
        self.refresh()

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
        self._apply_selection_style()
        self.events.publish("component.selected", component_id)

    def select_component_callback(self, sender, app_data, user_data):
        self.select_component(user_data)

    def _apply_selection_style(self):
        if not self.built:
            return
        for component in self.spacecraft.components:
            tag = f"spacecraft_component_label_{component.id}"
            if dpg.does_item_exist(tag):
                dpg.configure_item(
                    tag,
                    color=(
                        self.SELECTED_COLOR
                        if component.id == self.selected_id
                        else self.NORMAL_COLOR
                    ),
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
                dpg.add_text(
                    component.name,
                    wrap=250,
                    tag=f"spacecraft_component_label_{component.id}",
                )
                dpg.add_text(
                    f"{component.dry_mass:,.0f} kg dry",
                    tag=f"spacecraft_component_mass_{component.id}",
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
            for field_name, label, minimum, maximum in self._editable_fields(component):
                options = {
                    "label": label,
                    "default_value": getattr(component, field_name) or 0.0,
                    "min_value": minimum,
                    "min_clamped": True,
                    "width": 220,
                    "parent": "spacecraft_components_container",
                    "callback": self.update_component,
                    "user_data": (component.id, field_name),
                    "on_enter": True,
                    "tag": f"spacecraft_{component.id}_{field_name}",
                }
                if maximum is not None:
                    options["max_value"] = maximum
                    options["max_clamped"] = True
                dpg.add_input_float(**options)
            self._add_definition_controls(component)
            dpg.add_separator(parent="spacecraft_components_container")
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
        return fields

    def _add_definition_controls(self, component):
        """Stage, data-quality, and source inputs for one component."""
        parent = "spacecraft_components_container"
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
            width=220,
            parent=parent,
            on_enter=True,
            callback=self.set_data_source,
            user_data=component.id,
            tag=f"spacecraft_{component.id}_source",
        )

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
        old_value = getattr(component, field_name)
        setattr(component, field_name, float(app_data))
        try:
            component.__post_init__()
        except ValueError:
            setattr(component, field_name, old_value)
            dpg.set_value(sender, old_value)
            return
        if field_name == "dry_mass":
            mass_tag = f"spacecraft_component_mass_{component.id}"
            if dpg.does_item_exist(mass_tag):
                dpg.set_value(mass_tag, f"{component.dry_mass:,.0f} kg dry")
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
        self.spacecraft = load_spacecraft(APOLLO_LM_PRESET)
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
        self._set_lunar_status(
            "Mission simulation running…",
            "Downloading/reading JPL ephemeris and integrating the trajectory.",
        )
        try:
            result = run_lunar_flyby_simulation(
                self.spacecraft,
                departure_date,
                transfer_time=float(transfer_days) * u.day,
            )
        except Exception as error:
            self.mission_result = None
            self._set_lunar_status(
                "Simulation could not run.",
                f"{error}\nCheck the date, network, and JPL DE440s access.",
            )
            return
        self.mission_result = result
        self.events.publish("mission.completed", result)
        self._display_mission_result(result)

    def _display_mission_result(self, result):
        if not result.simulated:
            title = "MISSION FAILED — vehicle/transfer constraints not met"
        elif result.success:
            title = "MISSION SUCCESS — propagated path reached the Moon"
            if result.surface_impact:
                title += " (surface impact predicted)"
        else:
            title = "MISSION FAILED — propagated path missed the Moon"
        closest = (
            f"{result.closest_approach.to_value('km'):,.0f} km"
            if result.closest_approach is not None
            else "not propagated"
        )
        details = (
            f"TLI required: {result.tli_delta_v.to_value('km/s'):.2f} km/s  |  "
            f"Delta-v remaining after Earth-ascent allowance: "
            f"{max(0.0, result.available_delta_v.to_value('km/s') - 9.4):.2f} km/s\n"
            f"Transfer: {result.transfer_time.to_value('day'):.2f} days  |  "
            f"Arrival: {result.arrival_time}\n"
            f"Closest approach: {closest}  |  "
            f"Lunar SOI: {result.lunar_sphere_of_influence.to_value('km'):,.0f} km\n"
            f"Ephemeris: {result.data_source}\n"
            + (
                "Surface intersection predicted; this is not a landing simulation.\n"
                if result.surface_impact
                else ""
            )
            + ("Reasons: " + " ".join(result.reasons) if result.reasons else "")
        )
        self._set_lunar_status(title, details)

    def _invalidate_mission_result(self, sender=None, app_data=None, user_data=None):
        if self.mission_result is not None:
            self.mission_result = None
            self._set_lunar_status(
                "Design changed — run the mission simulation again.",
                "Previous trajectory result discarded because the spacecraft changed.",
            )

    @staticmethod
    def _set_lunar_status(status, details):
        if dpg.does_item_exist("lunar_reachability_status"):
            dpg.set_value("lunar_reachability_status", status)
        if dpg.does_item_exist("lunar_reachability_details"):
            dpg.set_value("lunar_reachability_details", details)

    def refresh(self):
        self.analysis = analyze_spacecraft(self.spacecraft)
        if not self.built:
            return
        analysis = self.analysis
        mission = assess_mission(analysis, MISSION_PROFILES[self.mission_id])
        values = {
            "spacecraft_dry_mass": f"Dry Mass: {analysis.dry_mass:,.1f} kg",
            "spacecraft_fuel_mass": f"Fuel Mass: {analysis.fuel_mass:,.1f} kg",
            "spacecraft_wet_mass": f"Wet Mass: {analysis.wet_mass:,.1f} kg",
            "spacecraft_thrust": f"Thrust: {analysis.thrust / 1000:,.1f} kN",
            "spacecraft_delta_v": (
                f"Delta-v: {analysis.delta_v:,.0f} m/s · Isp {analysis.isp:.1f} s"
            ),
            "spacecraft_twr": f"TWR: {analysis.twr:.2f}",
            "spacecraft_burn_time": f"Burn Time: {analysis.burn_time:,.1f} s",
            "spacecraft_power": (
                f"Power: {analysis.power_generation_kw:.2f} kW generation / "
                f"{analysis.power_draw_kw:.2f} kW load · "
                f"{analysis.power_storage_kwh:.2f} kWh storage"
            ),
            "spacecraft_mission_status": self._mission_text(mission),
            "spacecraft_warnings": "\n".join(analysis.warnings),
            "spacecraft_data_readiness": assess_definition(self.spacecraft).summary(),
        }
        for tag, value in values.items():
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)
        if dpg.does_item_exist("spacecraft_name_input"):
            dpg.set_value("spacecraft_name_input", self.spacecraft.name)
        self.events.publish("analysis.updated", analysis, mission)

    @staticmethod
    def _mission_text(mission):
        if mission.achievable:
            return (
                f"{mission.mission.name}: IDEAL BUDGET MET "
                f"({mission.delta_v_margin:,.0f} m/s margin)"
            )
        return f"{mission.mission.name}: NOT MET · " + " ".join(mission.reasons)