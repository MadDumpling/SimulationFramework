import taichi as ti

from simulations import BouncingBalls
from ui import SimulationUI
from input import InputManager

def main():
    try:
        ti.init(arch=ti.gpu)
    except RuntimeError as error:
        print(f"GPU initialization failed ({error}). Falling back to CPU.")
        ti.init(arch=ti.cpu)

    window = ti.ui.Window(
        "Simulation Framework",
        (1920, 1080),
        vsync=True,
    )
    print(dir(window))
    canvas = window.get_canvas()

    simulation = BouncingBalls()
    ui = SimulationUI()

    input_manager = InputManager()

    while window.running:

        input_manager.update(window)

        ui.draw(window, simulation, input_manager.camera)

        if not ui.paused:
            simulation.step()

        canvas.set_background_color(
            (0.05, 0.05, 0.08)
        )

        simulation.render(
            canvas,
            input_manager.camera
        )

        window.show()


if __name__ == "__main__":
    main()