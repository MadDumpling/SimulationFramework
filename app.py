import taichi as ti

from simulations.bouncing_balls import BouncingBalls

ti.init(arch=ti.gpu)

window = ti.ui.Window(
    "Simulation Framework",
    (1280, 720)
)

canvas = window.get_canvas()

simulation = BouncingBalls()

while window.running:

    simulation.step()

    canvas.set_background_color((0.05, 0.05, 0.08))
    simulation.render(canvas)

    window.show()
