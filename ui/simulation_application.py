import dearpygui.dearpygui as dpg

from input import InputManager

from core import EventBus

from core.performance import (
    PerformanceMonitor,
)

from core.metrics import (
    MetricsManager,
)

from simulation_manager import (
    SimulationManager,
)

from rendering import (
    TaichiRenderer,
)

from .controls import SimulationUI


class SimulationApplication:

    def __init__(self):

        self.events = EventBus()

        self.metrics = MetricsManager()

        self.metrics.register(
            "fps"
        )

        self.metrics.register(
            "frame_time"
        )

        self.renderer = (
            TaichiRenderer()
        )

        self.manager = (
            SimulationManager()
        )

        # Simulation Events

        self.events.subscribe(
            "simulation.load",
            self.manager.load,
        )

        self.events.subscribe(
            "simulation.reset",
            self.manager.reset,
        )

        # Preset Events

        self.events.subscribe(
            "preset.save",
            self.manager.save_preset,
        )

        self.events.subscribe(
            "preset.load",
            self.manager.load_preset,
        )

        self.ui = SimulationUI(
            self.manager,
            self.events,
        )

        self.input_manager = (
            InputManager()
        )

        self.performance = (
            PerformanceMonitor()
        )

    @property
    def running(self):
        return self.renderer.running

    def initialize(self):

        self.manager.load(
            "Bouncing Balls"
        )

        self.ui.build()

    def update(self):

        #
        # Performance
        #

        self.performance.update()

        self.metrics.record(
            "fps",
            self.performance.fps,
        )

        self.metrics.record(
            "frame_time",
            self.performance.frame_time,
        )

        #
        # Graph Data
        #

        fps_values = (
            self.metrics.get(
                "fps"
            )
        )

        frame_values = (
            self.metrics.get(
                "frame_time"
            )
        )

        if len(fps_values) > 1:

            fps_x = list(
                range(
                    len(fps_values)
                )
            )

            dpg.set_value(
                "fps_series",
                [
                    fps_x,
                    fps_values,
                ],
            )

        if len(frame_values) > 1:

            frame_x = list(
                range(
                    len(frame_values)
                )
            )

            dpg.set_value(
                "frame_time_series",
                [
                    frame_x,
                    frame_values,
                ],
            )

        #
        # Metrics Text
        #

        dpg.set_value(
            "fps_text",
            (
                f"FPS: "
                f"{self.performance.fps:.1f}"
            ),
        )

        dpg.set_value(
            "frame_time_text",
            (
                f"Frame Time: "
                f"{self.performance.frame_time:.2f} ms"
            ),
        )

        #
        # Input
        #

        self.input_manager.update(
            self.renderer.window,
            disable_mouse_camera=False,
        )

        #
        # Simulation
        #

        if not self.ui.paused:

            self.manager.step()
            simulation = self.manager.current

            if simulation:

                for metric in (
                    simulation.metrics.values()
                ):

                    tag = (
                        f"metric_{metric.name}"
                    )

                    if dpg.does_item_exist(
                        tag
                    ):

                        dpg.set_value(
                            tag,
                            (
                                f"{metric.name}: "
                                f"{metric.value:.2f}"
                            ),
                        )
    def render(self):

        self.renderer.begin_frame()

        self.renderer.render(
            self.manager.current,
            self.input_manager.camera,
        )

        self.renderer.end_frame()