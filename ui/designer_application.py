import dearpygui.dearpygui as dpg

import time

from core import EventBus
from core.performance import PerformanceMonitor
from rendering import OpenGLRenderer
from spacecraft.components import (
    Avionics,
    Battery,
    Engine,
    FuelTank,
    LandingLeg,
    RcsThruster,
    SolarPanel,
)
from viewport import SpacecraftViewport
from viewport import flight

from .dpg_input_source import DpgInputSource
from .audio_cues import AudioCues
from .layout import create_dockspace
from . import mission_outcome as outcome
from .spacecraft_designer import SpacecraftDesignerUI

CLICK_DRAG_TOLERANCE = 4.0  # pixels of movement still treated as a click


class DesignerApplication:
    """Wires the designer panel to the OpenGL spacecraft viewport."""

    def __init__(self):
        self.events = EventBus()
        self.renderer = OpenGLRenderer()
        self.performance = PerformanceMonitor()
        self.audio = AudioCues()
        self.designer = SpacecraftDesignerUI(self.events)
        self.viewport = SpacecraftViewport(lambda: self.designer.spacecraft)
        self.input_source = None
        self._mission_started_at = None
        self._banner_second = None
        self._held_banner = None  # verdict banner waiting for the animation to catch up

        self._drag = None
        self._drag_distance = 0.0

        self.events.subscribe("spacecraft.updated", self._on_spacecraft_updated)
        self.events.subscribe(
            "spacecraft.appearance_updated",
            self._on_spacecraft_appearance_updated,
        )
        self.events.subscribe("component.selected", self._on_component_selected)
        self.events.subscribe("view.explode", self._on_explode)
        self.events.subscribe("view.grid", self._on_grid)
        self.events.subscribe("view.reset_camera", self.viewport.reset_camera)
        self.events.subscribe("mission.started", self._on_mission_started)
        self.events.subscribe("mission.completed", self._on_mission_completed)
        self.events.subscribe("mission.failed", self._on_mission_failed)
        self.events.subscribe("mission.cancelled", self._reset_flight)
        self.events.subscribe("flight.reset", self._reset_flight)
        self.events.subscribe("audio.enabled", self._on_audio_enabled)
        self.designer.background_missions = True

    @property
    def running(self):
        return True

    def initialize(self):
        create_dockspace()
        self.designer.build()
        self._set_audio_status(self.audio.status_message)
        self.input_source = DpgInputSource()
        self.viewport.invalidate(reframe=True)

    def shutdown(self):
        self.audio.close()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _on_spacecraft_updated(self, spacecraft):
        if (
            self.viewport.selected_id is not None
            and spacecraft.get_component(self.viewport.selected_id) is None
        ):
            self.viewport.selected_id = None
        self._reset_flight()  # editing the design returns the vehicle to the pad
        self.viewport.invalidate()
        self._refresh_component_overlay()

    def _on_spacecraft_appearance_updated(self, spacecraft):
        self.viewport.invalidate()

    def _reset_flight(self):
        self._held_banner = None
        self.viewport.reset_flight()
        self.audio.stop()
        self._set_banner(" ", outcome.BLUE)

    def _set_audio_status(self, message):
        warning = message.startswith("Demo audio unavailable") or message.startswith(
            "Demo audio could not play"
        )
        self.designer.set_audio_status(message, warning=warning)

    def _play_audio(self, cue):
        error = self.audio.play(cue)
        if error is not None:
            self._set_audio_status(error)

    def _on_audio_enabled(self, enabled):
        self.audio.set_enabled(enabled)
        self._set_audio_status(self.audio.status_message)

    def _set_banner(self, text, color):
        if dpg.does_item_exist("mission_banner"):
            dpg.set_value("mission_banner", text)
            dpg.configure_item("mission_banner", color=color)

    def _on_mission_started(self, liftoff=True, has_thrust=True):
        self._held_banner = None
        self.viewport.start_flight(liftoff, has_thrust)
        if liftoff and has_thrust:
            self._play_audio("takeoff")
        self._mission_started_at = time.monotonic()
        self._banner_second = None
        if liftoff:
            self._set_banner(*outcome.running_banner(0.0))
        else:
            self._set_banner(*outcome.no_liftoff_banner(self.designer.analysis))

    def step_flight(self, dt):
        """Advance the mission: apply a finished run, tick banners, animate."""
        self.designer.poll_mission()
        self._update_progress_banner()
        self.viewport.update(dt)
        if self._held_banner is not None and not self.viewport.flight.pending:
            self._set_banner(*self._held_banner)  # the verdict is now on screen
            self._held_banner = None

    def _update_progress_banner(self):
        """Tick the elapsed time while the simulation is still running."""
        if not self.designer.mission_running or self._mission_started_at is None:
            return
        if self.viewport.flight.state != flight.ASCENDING:
            return
        elapsed = time.monotonic() - self._mission_started_at
        if int(elapsed) != self._banner_second:
            self._banner_second = int(elapsed)
            self._set_banner(*outcome.running_banner(elapsed))

    def _on_mission_completed(self, result):
        verdict = outcome.flight_outcome(result)
        self._play_audio("success" if verdict == flight.LAND else "failure")
        if self.viewport.flight.state == flight.NO_LIFTOFF:
            return  # the vehicle never left the pad; the banner already says why
        self.viewport.finish_flight(verdict)
        banner = outcome.verdict_banner(result, verdict)
        if self.viewport.flight.pending:
            self._held_banner = banner  # keep "in progress" until the ship has climbed
        else:
            self._set_banner(*banner)

    def _on_mission_failed(self, error):
        # An error is not a verdict on the vehicle: return to the pad and say so.
        self._held_banner = None
        self.viewport.reset_flight()
        self.audio.stop()
        self._set_banner(*outcome.error_banner(error))

    def _on_component_selected(self, component_id):
        self.viewport.selected_id = component_id
        self._refresh_component_overlay()

    def _refresh_component_overlay(self):
        component = self.designer.spacecraft.get_component(self.viewport.selected_id)
        if component is None:
            title = "No component selected"
            details = "Select a part to inspect its mass and modeled hardware ratings."
        else:
            title = component.name
            lines = [f"Dry mass: {component.dry_mass:,.1f} kg"]
            if isinstance(component, Engine):
                lines.extend(
                    (
                        f"Main-engine thrust: {component.thrust:,.1f} N",
                        f"Specific impulse: {component.isp:,.1f} s",
                        f"Propellant: {component.fuel_type}",
                    )
                )
            elif isinstance(component, FuelTank):
                lines.extend(
                    (
                        f"Loaded propellant: {component.fuel_mass:,.1f} / "
                        f"{component.capacity:,.1f} kg",
                        f"Propellant: {component.fuel_type}",
                    )
                )
            elif isinstance(component, LandingLeg):
                lines.append(
                    f"Landing legs: {component.leg_count} · "
                    f"footprint radius: {component.footprint_radius_m:.2f} m"
                )
            elif isinstance(component, RcsThruster):
                lines.append(
                    f"RCS: {component.thruster_count} × "
                    f"{component.thrust_n:,.1f} N · Isp {component.isp_s:.1f} s"
                )
            elif isinstance(component, SolarPanel):
                lines.append(
                    f"Solar array: {component.area_m2:.2f} m² · "
                    f"{component.generation_kw:.2f} kW rated"
                )
            elif isinstance(component, Battery):
                lines.append(
                    f"Battery: {component.capacity_kwh:.2f} kWh · "
                    f"charge {component.max_charge_kw:.2f} kW / "
                    f"discharge {component.max_discharge_kw:.2f} kW"
                )
            elif isinstance(component, Avionics):
                lines.append(
                    f"Avionics load: {component.power_draw_kw:.2f} kW · "
                    f"redundancy {component.redundancy}"
                )
            details = "  |  ".join(lines)
        for tag, value in (
            ("viewport_component_title", title),
            ("viewport_component_details", details),
        ):
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)

    def _on_explode(self, amount):
        self.viewport.explode = amount
        self.viewport.invalidate()

    def _on_grid(self, visible):
        self.viewport.show_grid = visible

    # ------------------------------------------------------------------
    # Frame loop
    # ------------------------------------------------------------------

    def update(self):
        self.performance.update()
        if dpg.does_item_exist("fps_text"):
            dpg.set_value(
                "fps_text",
                f"{self.performance.fps:.0f} FPS · "
                f"{self.performance.frame_time:.1f} ms · {self.renderer.name}",
            )
        self.step_flight(self.performance.frame_time / 1000.0)
        self._handle_input()

    def _handle_input(self):
        source = self.input_source
        over = source.is_cursor_over_viewport()
        dx, dy = source.mouse_delta()
        scroll = source.consume_scroll()
        camera = self.viewport.camera
        _, height = source.get_window_shape()

        if over and scroll:
            camera.zoom(scroll)

        if over and self._drag is None:
            for button in ("left", "right", "middle"):
                if source.is_clicked(button):
                    self._drag = button
                    self._drag_distance = 0.0
                    break

        if self._drag is not None:
            if source.is_down(self._drag):
                self._drag_distance += abs(dx) + abs(dy)
                if self._drag == "left":
                    camera.orbit(dx, dy)
                else:
                    camera.pan(dx, dy, height)
            else:
                if self._drag == "left" and self._drag_distance <= CLICK_DRAG_TOLERANCE:
                    x, y = source.get_cursor_pos()
                    self.designer.select_component(
                        self.viewport.pick(self.renderer, x, y)
                    )
                self._drag = None
        elif over and (dx or dy):
            x, y = source.get_cursor_pos()
            self.viewport.hovered_id = self.viewport.pick(self.renderer, x, y)
        elif not over:
            self.viewport.hovered_id = None

        if over and source.is_pressed("f"):
            self.viewport.invalidate(reframe=True)
        if over and source.is_pressed("r"):
            self.viewport.reset_camera()

    def render(self):
        self.renderer.begin_frame()
        self.viewport.render(self.renderer)
        self.renderer.end_frame()
