#ui.py
from registry import SIMULATIONS


class SimulationUI:
    def __init__(self):

        self.paused = False

        self.available_simulations = list(
            SIMULATIONS.keys()
        )

        self.selected_simulation = (
            self.available_simulations[0]
            if self.available_simulations
            else ""
        )

    def draw(
        self,
        window,
        simulation_manager,
        camera,
    ):
        gui = window.get_gui()

        with gui.sub_window(
            "Controls",
            0.02,
            0.02,
            0.25,
            0.45,
        ):

            gui.text("Simulation Framework")

            gui.separator()

            gui.text("Simulation")

            selected = gui.combo(
                "Type",
                self.available_simulations,
            )

            if (
                selected != ""
                and
                selected != self.selected_simulation
            ):
                self.selected_simulation = selected

                simulation_manager.load(
                    selected
                )

            simulation = (
                simulation_manager.current
            )

            if gui.button(
                "Reset Simulation"
            ):
                simulation.reset()

            if gui.button(
                "Reset Camera"
            ):
                camera.reset()

            self.paused = gui.checkbox(
                "Paused",
                self.paused,
            )

            gui.separator()

            gui.text(
                f"Parameters: "
                f"{len(simulation.parameters)}"
            )

            for parameter in (
                simulation.parameters.values()
            ):

                parameter.value = (
                    gui.slider_float(
                        parameter.name,
                        parameter.value,
                        parameter.min,
                        parameter.max,
                    )
                )