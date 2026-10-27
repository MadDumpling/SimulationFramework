#controls.py
class SimulationUI:

    def __init__(self):
        self.paused = False
        self.controls_x = 0.02
        self.controls_y = 0.02
        self.controls_width = 0.25
        self.controls_height = 0.30

    def is_mouse_over_gui(self, window):
        mouse_x, mouse_y = window.get_cursor_pos()

        if mouse_x > 1.0 or mouse_y > 1.0:
            window_width, window_height = window.get_window_shape()
            if window_width > 0 and window_height > 0:
                mouse_x /= window_width
                mouse_y /= window_height

        return (
            self.controls_x <= mouse_x <= self.controls_x + self.controls_width
            and self.controls_y <= mouse_y <= self.controls_y + self.controls_height
        )

    def draw(self, window, simulation, camera):

        gui = window.get_gui()

        with gui.sub_window(
            "Controls",
            self.controls_x,
            self.controls_y,
            self.controls_width,
            self.controls_height,
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
