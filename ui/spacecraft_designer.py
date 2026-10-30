"""DearPyGui editor panel for the initial spacecraft-design MVP."""

from datetime import datetime, timezone
from pathlib import Path

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
    Payload,
    PowerSystem,
    component_from_catalog,
)
from spacecraft.presets import load_spacecraft, save_spacecraft
from spacecraft.vehicle import Spacecraft
from spacecraft.mission import MissionSimulationResult, run_lunar_flyby_simulation

DEFAULT_PRESET = (
    Path(__file__).resolve().parents[1]
    / "presets"
    / "spacecraft"
    / "spacecraft_mvp.json"
)


class SpacecraftDesignerUI:
    """Editable component assembly, analysis, persistence, and schematic view."""

    def __init__(self, events, preset_path=DEFAULT_PRESET):
        self.events = events
        self.preset_path = Path(preset_path)
        self.spacecraft = self._load_starting_spacecraft()
        self.mission_id = "leo"
        self.analysis = analyze_spacecraft(self.spacecraft)
        self.mission_result: MissionSimulationResult | None = None
        self.built = False

    def _load_starting_spacecraft(self):
        if self.preset_path.exists():
            return load_spacecraft(self.preset_path)
        craft = Spacecraft("Untitled spacecraft")
        craft.add_component(component_from_catalog("engine"))
        craft.add_component(component_from_catalog("fuel_tank"))
        craft.add_component(component_from_catalog("payload"))
        return craft

    def build(self):
        with dpg.window(
            label="Spacecraft Designer",
            tag="spacecraft_designer_window",
            width=640,
            height=900,
        ):
            dpg.add_text(
                "Ideal vehicle delta-v estimate · lunar check uses JPL DE440s",
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
                dpg.add_button(
                    label="Add Engine",
                    callback=self.add_component,
                    user_data="engine",
                )
                dpg.add_button(
                    label="Add Tank",
                    callback=self.add_component,
                    user_data="fuel_tank",
                )
                dpg.add_button(
                    label="Add Payload",
                    callback=self.add_component,
                    user_data="payload",
                )
                dpg.add_button(
                    label="Add Power",
                    callback=self.add_component,
                    user_data="power_system",
                )
            with dpg.group(horizontal=True):
                dpg.add_button(label="Save Design", callback=self.save)
                dpg.add_button(label="Load Design", callback=self.load)
                dpg.add_button(label="Clear Assembly", callback=self.clear)
            dpg.add_separator()
            dpg.add_text("Assembly Components")
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
            dpg.add_text("Power: 0.00 kW generation / 0.00 kW load", tag="spacecraft_power")
            dpg.add_text("Mission status", tag="spacecraft_mission_status")
            dpg.add_text("", tag="spacecraft_warnings", wrap=560)
            dpg.add_separator()
            dpg.add_text("Moon Reachability · JPL DE440s ephemeris", bullet=True)
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
                "Shoots a Lambert transfer, then propagates Sun/Earth/Moon gravity "
                "against JPL DE440s. Success means entering the lunar sphere of influence; "
                "this does not simulate capture or landing.",
                wrap=560,
                color=(175, 190, 210),
            )
            dpg.add_text("Not simulated", tag="lunar_reachability_status", wrap=560)
            dpg.add_text("", tag="lunar_reachability_details", wrap=560)
            dpg.add_separator()
            dpg.add_text("Stack schematic (not to scale)")
            dpg.add_drawlist(
                width=560,
                height=300,
                tag="spacecraft_schematic",
            )

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
        self.refresh()

    def remove_component(self, sender, app_data, user_data):
        removed = self.spacecraft.remove_component(user_data)
        if removed:
            self.events.publish("component.removed", user_data)
            self.events.publish("spacecraft.updated", self.spacecraft)
            self._invalidate_mission_result()
            self._rebuild_component_controls()
            self.refresh()

    def _rebuild_component_controls(self):
        if not self.built:
            return
        dpg.delete_item("spacecraft_components_container", children_only=True)
        for component in self.spacecraft.components:
            with dpg.group(
                horizontal=True,
                parent="spacecraft_components_container",
            ):
                dpg.add_text(
                    f"{component.name} · {component.dry_mass:,.0f} kg dry",
                    wrap=250,
                    tag=f"spacecraft_component_label_{component.id}",
                )
                dpg.add_button(
                    label="Remove",
                    callback=self.remove_component,
                    user_data=component.id,
                    small=True,
                )
            for field_name, label, minimum, maximum in self._editable_fields(component):
                input_options = {
                    "label": label,
                    "default_value": getattr(component, field_name),
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
                    input_options["max_value"] = maximum
                    input_options["max_clamped"] = True
                dpg.add_input_float(**input_options)
            dpg.add_separator(parent="spacecraft_components_container")

    @staticmethod
    def _editable_fields(component):
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
            label_tag = f"spacecraft_component_label_{component.id}"
            if dpg.does_item_exist(label_tag):
                dpg.set_value(
                    label_tag,
                    f"{component.name} · {component.dry_mass:,.0f} kg dry",
                )
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
        if self.preset_path.exists():
            self.spacecraft = load_spacecraft(self.preset_path)
            self.events.publish("spacecraft.updated", self.spacecraft)
            self._rebuild_component_controls()
            self.refresh()

    def clear(self, sender=None, app_data=None, user_data=None):
        self.spacecraft = Spacecraft(self.spacecraft.name)
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
        details = (
            f"TLI required: {result.tli_delta_v.to_value('km/s'):.2f} km/s  |  "
            f"Delta-v remaining after Earth-ascent allowance: "
            f"{max(0.0, result.available_delta_v.to_value('km/s') - 9.4):.2f} km/s\n"
            f"Transfer: {result.transfer_time.to_value('day'):.2f} days  |  "
            f"Arrival: {result.arrival_time}\n"
            f"Closest approach: "
            + (
                f"{result.closest_approach.to_value('km'):,.0f} km  |  "
                if result.closest_approach is not None
                else "not propagated  |  "
            )
            + f"Lunar SOI: {result.lunar_sphere_of_influence.to_value('km'):,.0f} km\n"
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
        profile = MISSION_PROFILES[self.mission_id]
        mission = assess_mission(analysis, profile)
        values = {
            "spacecraft_dry_mass": f"Dry Mass: {analysis.dry_mass:,.1f} kg",
            "spacecraft_fuel_mass": f"Fuel Mass: {analysis.fuel_mass:,.1f} kg",
            "spacecraft_wet_mass": f"Wet Mass: {analysis.wet_mass:,.1f} kg",
            "spacecraft_thrust": f"Thrust: {analysis.thrust / 1000:,.1f} kN",
            "spacecraft_delta_v": f"Delta-v: {analysis.delta_v:,.0f} m/s · Isp {analysis.isp:.1f} s",
            "spacecraft_twr": f"TWR: {analysis.twr:.2f}",
            "spacecraft_burn_time": f"Burn Time: {analysis.burn_time:,.1f} s",
            "spacecraft_power": (
                f"Power: {analysis.power_generation_kw:.2f} kW generation / "
                f"{analysis.power_draw_kw:.2f} kW load · "
                f"{analysis.power_storage_kwh:.2f} kWh storage"
            ),
            "spacecraft_mission_status": self._mission_text(mission),
            "spacecraft_warnings": "\n".join(analysis.warnings),
        }
        for tag, value in values.items():
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)
        if dpg.does_item_exist("spacecraft_name_input"):
            dpg.set_value("spacecraft_name_input", self.spacecraft.name)
        self._draw_schematic()
        self.events.publish("analysis.updated", analysis, mission)

    @staticmethod
    def _mission_text(mission):
        if mission.achievable:
            return (
                f"{mission.mission.name}: IDEAL BUDGET MET "
                f"({mission.delta_v_margin:,.0f} m/s margin)"
            )
        return (
            f"{mission.mission.name}: NOT MET · "
            + " ".join(mission.reasons)
        )

    def _draw_schematic(self):
        dpg.delete_item("spacecraft_schematic", children_only=True)
        dpg.draw_rectangle(
            (0, 0),
            (560, 300),
            parent="spacecraft_schematic",
            fill=(20, 28, 40, 255),
            color=(55, 70, 90, 255),
        )
        dpg.draw_text(
            (16, 12),
            self.spacecraft.name,
            parent="spacecraft_schematic",
            color=(220, 230, 245, 255),
            size=16,
        )
        stack = sorted(
            self.spacecraft.components,
            key=self._stack_order,
        )
        if not stack:
            dpg.draw_text(
                (190, 145),
                "Add components to assemble a vehicle",
                parent="spacecraft_schematic",
                color=(160, 175, 195, 255),
            )
            return

        center_x = 280
        bottom_y = 270
        available_height = 220
        segment_height = min(50, available_height / len(stack))
        for index, component in enumerate(stack):
            y1 = bottom_y - index * segment_height
            y0 = y1 - segment_height + 2
            width = self._schematic_width(component)
            x0 = center_x - width / 2
            x1 = center_x + width / 2
            color = self._schematic_color(component)
            dpg.draw_rectangle(
                (x0, y0),
                (x1, y1),
                parent="spacecraft_schematic",
                fill=color,
                color=(220, 230, 245, 255),
                rounding=3,
            )
            label = f"{component.name} · {component.dry_mass:,.0f} kg"
            dpg.draw_text(
                (x1 + 12, y0 + 8),
                label,
                parent="spacecraft_schematic",
                color=(220, 230, 245, 255),
            )
        dpg.draw_line(
            (center_x, 44),
            (center_x, 52),
            parent="spacecraft_schematic",
            color=(120, 180, 240, 255),
            thickness=2,
        )
        dpg.draw_text(
            (16, 275),
            "Ideal single-stage model; schematic not to scale",
            parent="spacecraft_schematic",
            color=(150, 165, 185, 255),
            size=12,
        )

    @staticmethod
    def _stack_order(component: Component):
        if isinstance(component, Engine):
            return 0
        if isinstance(component, FuelTank):
            return 1
        if isinstance(component, PowerSystem):
            return 2
        if isinstance(component, Payload):
            return 3
        return 4

    @staticmethod
    def _schematic_width(component: Component):
        if isinstance(component, Engine):
            return 56
        if isinstance(component, FuelTank):
            return 94
        if isinstance(component, Payload):
            return 68
        if isinstance(component, PowerSystem):
            return 112
        return 70

    @staticmethod
    def _schematic_color(component: Component):
        if isinstance(component, Engine):
            return (185, 95, 55, 255)
        if isinstance(component, FuelTank):
            return (95, 125, 165, 255)
        if isinstance(component, Payload):
            return (125, 155, 110, 255)
        if isinstance(component, PowerSystem):
            return (130, 105, 175, 255)
        return (110, 120, 130, 255)
