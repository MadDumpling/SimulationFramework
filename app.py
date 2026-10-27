import taichi as ti

from plugin_loader import load_simulations
from registry import SIMULATIONS

from ui import SimulationUI
from input import InputManager


def main():
    try:
        ti.init(arch=ti.gpu)
    except RuntimeError as error:
        print(
            f"GPU initialization failed ({error}). "
            "Falling back to CPU."
        )
        ti.init(arch=ti.cpu)

    # Discover all simulations
    load_simulations()

    print("Registered simulations:")
    print(SIMULATIONS)

    window = ti.ui.Window(
        "Simulation Framework",
        (1920, 1080),
        vsync=True,
    )

    canvas = window.get_canvas()

    # Create initial simulation from registry
    from simulation_manager import (
        SimulationManager
    )

    manager = SimulationManager()

    manager.load(
        "Bouncing Balls"
    )

    ui = SimulationUI()

    input_manager = InputManager()

    while window.running:

        mouse_over_gui = (
            ui.is_mouse_over_gui(window)
        )

        input_manager.update(
            window,
            disable_mouse_camera=mouse_over_gui,
        )

        ui.draw(
            window,
            manager.current,
            input_manager.camera,
        )

        if not ui.paused:
            manager.step()

        canvas.set_background_color(
            (0.05, 0.05, 0.08)
        )

        manager.render(
            canvas,
            input_manager.camera,
        )

        window.show()


if __name__ == "__main__":
    main()