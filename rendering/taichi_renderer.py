import taichi as ti

from .renderer import Renderer


class TaichiRenderer(Renderer):

    def __init__(self):

        self.window = ti.ui.Window(
            "Simulation Framework",
            (1920, 1080),
            vsync=True,
        )

        self.canvas = (
            self.window.get_canvas()
        )

    @property
    def running(self):
        return self.window.running

    def begin_frame(self):

        self.canvas.set_background_color(
            (0.05, 0.05, 0.08)
        )

    def draw_circles(
        self,
        positions,
        radius,
        color,
    ):
        self.canvas.circles(
            positions,
            radius=radius,
            color=color,
        )

    def end_frame(self):
        self.window.show()
