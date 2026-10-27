import taichi as ti

from plugin_loader import load_simulations
from registry import SIMULATIONS

from ui import SimulationUI
from input import InputManager
from simulation_manager import (
    SimulationManager
)


def main():

    try:
        ti.init(arch=ti.gpu)
    except RuntimeError as error:
        print(
            f"GPU initialization failed ({error}). "
            "Falling back to CPU."
        )
        ti.init(arch=ti.cpu)

    load_simulations()

    print("Registered simulations:")
    print(SIMULATIONS)

    window = ti.ui.Window(
        "Simulation Framework",
        (1920, 1080),
        vsync=True,
    )

    canvas = window.get_canvas()

    manager = SimulationManager()

    manager.load(
        "Bouncing Balls"
    )

    ui = SimulationUI(manager)
    ui.build()
    input_manager = InputManager()

    while window.running:

        # Render DearPyGui frame
        ui.render()

        # Camera input
        input_manager.update(
            window,
            disable_mouse_camera=False,
        )

        # Update simulation
        if not ui.paused:
            manager.step()

        # Render simulation
        canvas.set_background_color(
            (0.05, 0.05, 0.08)
        )

        manager.render(
            canvas,
            input_manager.camera,
        )

        window.show()

    ui.shutdown()


if __name__ == "__main__":
    main()