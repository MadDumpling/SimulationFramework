import taichi as ti

from plugin_loader import load_simulations

from ui import (
    Application,
    SimulationApplication,
)


def initialize_taichi():

    try:
        ti.init(
            arch=ti.gpu,
        )

    except RuntimeError as error:

        print(
            f"GPU initialization failed ({error}). "
            "Falling back to CPU."
        )

        ti.init(
            arch=ti.cpu,
        )


def main():

    initialize_taichi()

    load_simulations()

    app = Application()

    app.initialize()

    simulation_app = (
        SimulationApplication()
    )

    simulation_app.initialize()

    while (
        simulation_app.running
        and app.running()
    ):

        simulation_app.update()

        simulation_app.render()

        app.render()

    app.shutdown()


if __name__ == "__main__":
    main()