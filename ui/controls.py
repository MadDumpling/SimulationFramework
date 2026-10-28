import dearpygui.dearpygui as dpg

from registry import SIMULATIONS
from .layout import create_dockspace


class SimulationUI:

    def __init__(
        self,
        simulation_manager,
        events,
    ):

        self.manager = simulation_manager
        self.events = events

        self.paused = False

    def save_preset(
        self,
        sender,
        app_data,
        user_data,
    ):

        self.events.publish(
            "preset.save",
            "presets/test.json",
        )

    def load_preset(
        self,
        sender,
        app_data,
        user_data,
    ):

        self.events.publish(
            "preset.load",
            "presets/test.json",
        )

        self.rebuild_parameter_ui()

    def build(self):

        create_dockspace()

        self.build_controls()

        self.build_metrics()

        self.rebuild_parameter_ui()

    def build_controls(self):

        with dpg.window(
            label="Controls",
            tag="controls_window",
        ):

            dpg.add_text(
                "Simulation Framework",
            )

            dpg.add_text(
                "FPS: 0",
                tag="fps_text",
            )

            dpg.add_text(
                "Frame Time: 0.00 ms",
                tag="frame_time_text",
            )

            dpg.add_separator()

            dpg.add_button(
                label="Save Preset",
                callback=self.save_preset,
            )

            dpg.add_button(
                label="Load Preset",
                callback=self.load_preset,
            )

            dpg.add_separator()

            dpg.add_text(
                "Simulation",
            )

            dpg.add_combo(
                items=list(
                    SIMULATIONS.keys()
                ),
                default_value="Bouncing Balls",
                callback=self.change_simulation,
            )

            dpg.add_separator()

            dpg.add_button(
                label="Reset Simulation",
                callback=self.reset_simulation,
            )

            dpg.add_checkbox(
                label="Paused",
                default_value=False,
                callback=self.toggle_pause,
            )

            dpg.add_separator()

            dpg.add_text(
                "Parameters",
            )

            dpg.add_group(
                tag="parameter_container",
            )

    def build_metrics(self):

        with dpg.window(
            label="Metrics",
            tag="metrics_window",
        ):

            with dpg.plot(
                label="FPS",
                height=200,
                width=-1,
            ):

                dpg.add_plot_axis(
                    dpg.mvXAxis,
                    label="Frame",
                )

                with dpg.plot_axis(
                    dpg.mvYAxis,
                    label="FPS",
                ):

                    dpg.add_line_series(
                        [0],
                        [0],
                        tag="fps_series",
                    )

            with dpg.plot(
                label="Frame Time",
                height=200,
                width=-1,
            ):

                dpg.add_plot_axis(
                    dpg.mvXAxis,
                    label="Frame",
                )

                with dpg.plot_axis(
                    dpg.mvYAxis,
                    label="ms",
                ):

                    dpg.add_line_series(
                        [0],
                        [0],
                        tag="frame_time_series",
                    )
            dpg.add_separator()

            dpg.add_text(
                "Simulation Metrics"
            )

            dpg.add_group(
                tag="simulation_metrics_container"
            )

    def rebuild_metrics_ui(self):

        if not dpg.does_item_exist(
            "simulation_metrics_container"
        ):
            return

        dpg.delete_item(
            "simulation_metrics_container",
            children_only=True,
        )

        simulation = self.manager.current

        if simulation is None:
            return

        for metric in (
            simulation.metrics.values()
        ):

            dpg.add_text(
                f"{metric.name}: {metric.value}",
                tag=f"metric_{metric.name}",
                parent="simulation_metrics_container",
            )

    def toggle_pause(
        self,
        sender,
        app_data,
        user_data,
    ):

        self.paused = app_data
    
    def change_simulation(
        self,
        sender,
        app_data,
        user_data,
    ):

        self.events.publish(
            "simulation.load",
            app_data,
        )

        self.rebuild_parameter_ui()

        self.rebuild_metrics_ui()

        self.events.publish(
            "simulation.load",
            app_data,
        )

        self.rebuild_parameter_ui()

    def reset_simulation(
        self,
        sender,
        app_data,
        user_data,
    ):

        self.events.publish(
            "simulation.reset",
        )

    def update_parameter(
        self,
        sender,
        app_data,
        parameter,
    ):

        parameter.value = app_data

    def rebuild_parameter_ui(self):

        if not dpg.does_item_exist(
            "parameter_container",
        ):
            return

        dpg.delete_item(
            "parameter_container",
            children_only=True,
        )

        simulation = self.manager.current

        if simulation is None:
            return

        for parameter in (
            simulation.parameters.values()
        ):

            dpg.add_slider_float(
                label=parameter.name,
                default_value=parameter.value,
                min_value=parameter.min,
                max_value=parameter.max,
                callback=self.update_parameter,
                user_data=parameter,
                parent="parameter_container",
            )