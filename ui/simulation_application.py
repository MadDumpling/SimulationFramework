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
    OpenGLRenderer,
)

from .controls import SimulationUI
from .dpg_input_source import DpgInputSource
from .viewport_manager import (
    ViewportManager,
)


class SimulationApplication:

    def __init__(self):

        self.events = EventBus()

        #
        # Framework Metrics
        #

        self.metrics = MetricsManager()

        self.metrics.register("fps")
        self.metrics.register("frame_time")

        USE_OPENGL = True

        if USE_OPENGL:

            self.renderer = (
                OpenGLRenderer()
            )

        else:

            self.renderer = (
                DpgRenderer()
            )

        #
        # Viewport System
        #

        self.viewport = (
            ViewportManager(
                self.renderer
            )
        )

        #
        # Simulation Management
        #

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

        #
        # UI
        #

        self.ui = SimulationUI(
            self.manager,
            self.events,
        )

        #
        # Input
        #

        self.input_manager = (
            InputManager()
        )

        self.input_source = (
            DpgInputSource()
        )

        #
        # Performance
        #

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

        #
        # Force initial viewport sizing
        #

        self.viewport.update()

    def update(self):

        #
        # Viewport
        #

        self.viewport.update()

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
                f"FPS: {self.performance.fps:.1f}",
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

                if metric.graph:

                    series_tag = (
                        f"metric_series_{key}"
                    )

                    if (
                        dpg.does_item_exist(
                            series_tag
                        )
                        and len(
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

        print(
            "viewport_texture:",
            dpg.does_item_exist(
                "viewport_texture"
            )
        )

        print(
            "viewport_image:",
            dpg.does_item_exist(
                "viewport_image"
            )
        )

        print(
            "viewport_region:",
            dpg.does_item_exist(
                "viewport_region"
            )
        )

        simulation = self.manager.current

        print(
            "simulation loaded:",
            simulation is not None
        )

        if dpg.does_item_exist(
            "viewport_image"
        ):

            try:

                width = dpg.get_item_width(
                    "viewport_image"
                )

                height = dpg.get_item_height(
                    "viewport_image"
                )

                print(
                    "viewport_image size:",
                    width,
                    height,
                )

            except Exception as e:

                print(
                    "viewport image error:",
                    e,
                )

        if dpg.does_item_exist(
            "viewport_region"
        ):

            try:

                width = dpg.get_item_width(
                    "viewport_region"
                )

                height = dpg.get_item_height(
                    "viewport_region"
                )

                print(
                    "viewport_region size:",
                    width,
                    height,
                )

            except Exception as e:

                print(
                    "viewport region error:",
                    e,
                )

        self.renderer.begin_frame()

        if simulation:

            simulation.render(
                self.renderer,
                self.input_manager.camera,
            )

        self.renderer.end_frame()