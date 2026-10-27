#ui.py
class SimulationUI:
    def __init__(self):
        self.paused = False
        self.selected_simualation = None

    def draw(self, window, simulation, camera):
        gui = window.get_gui()
        gui.text("Simulation")

        selected = gui.combo(
            "Simulation",
            self.available_simulations,
        )

        with gui.sub_window(
            "Controls",
            0.02,
            0.02,
            0.25,
            0.45,
        ):
            gui.text("Simulation Framework")

            if gui.button("Reset Simulation"):
                simulation.reset()
            if gui.button("Reset Camera"):
                camera.reset()
            self.paused = gui.checkbox(
                "Paused",
                self.paused,
            )

            gui.separator()
            gui.text(
        f"Parameters: {len(simulation.parameters)}"
        )
            for parameter in simulation.parameters.values():

                parameter.value = gui.slider_float(
                    parameter.name,
                    parameter.value,
                    parameter.min,
                    parameter.max,
                )