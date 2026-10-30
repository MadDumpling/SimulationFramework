from ui import (
    Application,
    SimulationApplication,
)


def main():
    app = Application()

    app.initialize()

    simulation_app = (
        SimulationApplication()
    )

    try:
        simulation_app.initialize()

        while simulation_app.running and app.running():
            simulation_app.update()
            simulation_app.render()
            app.render()
    finally:
        app.shutdown()


if __name__ == "__main__":
    main()