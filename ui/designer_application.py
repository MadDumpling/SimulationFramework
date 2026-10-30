import dearpygui.dearpygui as dpg

import time

from core import EventBus
from core.performance import PerformanceMonitor
from rendering import OpenGLRenderer
from viewport import SpacecraftViewport
from viewport import flight

from .dpg_input_source import DpgInputSource
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
        self.designer = SpacecraftDesignerUI(self.events)
        self.viewport = SpacecraftViewport(lambda: self.designer.spacecraft)
        self.input_source = None
        self._mission_started_at = None
        self._banner_second = None
        self._held_banner = None  # verdict banner waiting for the animation to catch up

        self._drag = None
        self._drag_distance = 0.0

        self.events.subscribe("spacecraft.updated", self._on_spacecraft_updated)
        self.events.subscribe("component.selected", self._on_component_selected)
        self.events.subscribe("view.explode", self._on_explode)
        self.events.subscribe("view.grid", self._on_grid)
        self.events.subscribe("view.reset_camera", self.viewport.reset_camera)
        self.events.subscribe("mission.started", self._on_mission_started)
        self.events.subscribe("mission.completed", self._on_mission_completed)
        self.events.subscribe("mission.failed", self._on_mission_failed)
        self.events.subscribe("mission.cancelled", self._reset_flight)
        self.events.subscribe("flight.reset", self._reset_flight)
        self.designer.background_missions = True

    @property
    def running(self):
        return True

    def initialize(self):
        create_dockspace()
        self.designer.build()
        self.input_source = DpgInputSource()
        self.viewport.invalidate(reframe=True)

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

    def _reset_flight(self):
        self._held_banner = None
        self.viewport.reset_flight()
        self._set_banner(" ", outcome.BLUE)

    def _set_banner(self, text, color):
        if dpg.does_item_exist("mission_banner"):
            dpg.set_value("mission_banner", text)
            dpg.configure_item("mission_banner", color=color)

    def _on_mission_started(self, liftoff=True, has_thrust=True):
        self._held_banner = None
        self.viewport.start_flight(liftoff, has_thrust)
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
        if self.viewport.flight.state == flight.NO_LIFTOFF:
            return  # the vehicle never left the pad; the banner already says why
        verdict = outcome.flight_outcome(result)
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
        self._set_banner(*outcome.error_banner(error))

    def _on_component_selected(self, component_id):
        self.viewport.selected_id = component_id

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
