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
    DpgRenderer,
)

from .controls import SimulationUI
from .dpg_input_source import DpgInputSource


class SimulationApplication:

    def __init__(self):

        self.events = EventBus()

        #
        # Framework Metrics
        #

        self.metrics = MetricsManager()

        self.metrics.register(
            "fps"
        )

        self.metrics.register(
            "frame_time"
        )

        self.renderer = (
            DpgRenderer()
        )

        self.manager = (
            SimulationManager()
        )

        #
        # Simulation Events
        #

        self.events.subscribe(
            "simulation.load",
            self.manager.load,
        )

        self.events.subscribe(
            "simulation.reset",
            self.manager.reset,
        )

        #
        # Preset Events
        #

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

        self.input_source = (
            DpgInputSource()
        )

        self.performance = (
            PerformanceMonitor()
        )

    @property
    def running(self):
        return True

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
        # Framework Graphs
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

        if (
            len(fps_values) > 1
            and dpg.does_item_exist(
                "fps_series"
            )
        ):

            dpg.set_value(
                "fps_series",
                [
                    list(
                        range(
                            len(
                                fps_values
                            )
                        )
                    ),
                    fps_values,
                ],
            )

        if (
            len(frame_values) > 1
            and dpg.does_item_exist(
                "frame_time_series"
            )
        ):

            dpg.set_value(
                "frame_time_series",
                [
                    list(
                        range(
                            len(
                                frame_values
                            )
                        )
                    ),
                    frame_values,
                ],
            )

        #
        # Framework Text
        #

        if dpg.does_item_exist(
            "fps_text"
        ):

            dpg.set_value(
                "fps_text",
                (
                    f"FPS: "
                    f"{self.performance.fps:.1f}"
                ),
            )

        if dpg.does_item_exist(
            "frame_time_text"
        ):

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
            self.input_source,
            disable_mouse_camera=(
                not self.input_source
                .is_cursor_over_viewport()
            ),
        )

        #
        # Simulation
        #

        if not self.ui.paused:

            self.manager.step()

        simulation = (
            self.manager.current
        )

        #
        # Simulation Metrics
        #

        if simulation:

            for (
                key,
                metric,
            ) in (
                simulation.metrics.items()
            ):

                #
                # Metric Labels
                #

                value_tag = (
                    f"metric_value_{key}"
                )

                if dpg.does_item_exist(
                    value_tag
                ):

                    dpg.set_value(
                        value_tag,
                        (
                            f"{metric.name}: "
                            f"{metric.value:.2f}"
                        ),
                    )

                #
                # Metric Graphs
                #

                if metric.graph:

                    series_tag = (
                        f"metric_series_{key}"
                    )

                    if (
                        dpg.does_item_exist(
                            series_tag
                        )
                        and
                        len(
                            metric.history
                        ) > 1
                    ):

                        values = list(
                            metric.history
                        )

                        x_values = list(
                            range(
                                len(
                                    values
                                )
                            )
                        )

                        dpg.set_value(
                            series_tag,
                            [
                                x_values,
                                values,
                            ],
                        )

    def render(self):

        self.renderer.begin_frame()

        simulation = self.manager.current

        if simulation:
            simulation.render(
                self.renderer,
                self.input_manager.camera,
            )

        self.renderer.end_frame()
