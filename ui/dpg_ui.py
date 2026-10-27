import dearpygui.dearpygui as dpg

from registry import SIMULATIONS


class SimulationUI:

    def __init__(self, simulation_manager):

        self.manager = simulation_manager
        self.paused = False

        dpg.create_context()

        with dpg.window(
            label="Controls",
            width=400,
            height=700,
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

            dpg.add_text("Parameters")

            dpg.add_group(
                tag="parameter_container"
            )

        dpg.create_viewport(
            title="Controls",
            width=400,
            height=700,
        )

        dpg.setup_dearpygui()
        dpg.show_viewport()

        self.rebuild_parameter_ui()

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
        self.manager.load(app_data)

        self.rebuild_parameter_ui()

    def reset_simulation(
        self,
        sender,
        app_data,
        user_data,
    ):
        self.manager.reset()

    def update_parameter(
        self,
        sender,
        app_data,
        parameter,
    ):
        parameter.value = app_data

    def rebuild_parameter_ui(self):

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

    def render(self):
        dpg.render_dearpygui_frame()

    def shutdown(self):
        dpg.destroy_context()