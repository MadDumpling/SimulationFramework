import taichi as ti

from simulations import BouncingBalls
from ui import SimulationUI


def main():
    ti.init(arch=ti.gpu)

    window = ti.ui.Window(
        "Simulation Framework",
        (1920, 1080),
        vsync=True,
    )

    canvas = window.get_canvas()

    simulation = BouncingBalls()
    ui = SimulationUI()

    while window.running:

        ui.draw(window, simulation)

        if not ui.paused:
            simulation.step()

        canvas.set_background_color(
            (0.05, 0.05, 0.08)
        )

        simulation.render(canvas)

        window.show()


if __name__ == "__main__":
    main()