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

    def build(self):

        create_dockspace()

        self.build_controls()

        self.rebuild_parameter_ui()

    def build_controls(self):

        with dpg.window(
            label="Controls",
            tag="controls_window",
        ):

            dpg.add_text(
                "Simulation Framework"
            )

            dpg.add_separator()

            dpg.add_text(
                "Simulation"
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
                "Parameters"
            )

            dpg.add_group(
                tag="parameter_container"
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

    def reset_simulation(
        self,
        sender,
        app_data,
        user_data,
    ):

        self.events.publish(
            "simulation.reset"
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
            "parameter_container"
        ):
            return

        dpg.delete_item(
            "parameter_container",
            children_only=True,
        )

        simulation = self.manager.current

        if simulation is None:
            return

        for parameter in simulation.parameters.values():

            dpg.add_slider_float(
                label=parameter.name,
                default_value=parameter.value,
                min_value=parameter.min,
                max_value=parameter.max,
                callback=self.update_parameter,
                user_data=parameter,
                parent="parameter_container",
            )
