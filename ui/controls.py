#controls.py
class SimulationUI:

    def __init__(self):
        self.paused = False

    def draw(self, window, simulation, camera):

        gui = window.get_gui()

        with gui.sub_window(
            "Controls",
            0.02,
            0.02,
            0.25,
            0.30,
        ):

            gui.text("Simulation Framework")

            if gui.button("Reset"):
                simulation.reset()
            if gui.button("Reset Camera"):
                camera.reset()
            self.paused = gui.checkbox(
                "Paused",
                self.paused,
            )
            for parameter in simulation.parameters.values():

                parameter.value = gui.slider_float(
                    parameter.name,
                    parameter.value,
                    parameter.min,
                    parameter.max,
                )
