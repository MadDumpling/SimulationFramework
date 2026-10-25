import taichi as ti


class SimulationUI:
    def __init__(self):
        self.paused = False

    def draw(self, window, simulation):
        gui = window.get_gui()

        with gui.sub_window(
            "Controls",
            0.02, 0.02,
            0.25, 0.3
        ):
            gui.text("Simulation Controls")

            if gui.button("Reset"):
                simulation.reset()

            self.paused = gui.checkbox(
                "Paused",
                self.paused
            )

            simulation.gravity = gui.slider_float(
                "Gravity",
                simulation.gravity,
                0.0,
                20.0
            )